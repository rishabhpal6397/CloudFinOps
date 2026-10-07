"""
CloudFinOps – Apply SQL views
=============================

Loads every .sql file in database/views/ and executes it.
Views use CREATE OR REPLACE, so this is idempotent.

Usage (from repo root):
    python data-engineering/apply_views.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from sqlalchemy import text

from etl.db import get_engine, test_connection

logger = logging.getLogger("apply_views")

VIEWS_DIR = Path(__file__).resolve().parent.parent / "database" / "views"


def _strip_sql_comments(sql: str) -> str:
    out_lines: list[str] = []
    for line in sql.splitlines():
        if line.lstrip().startswith("--"):
            continue
        idx = line.find("--")
        if idx >= 0:
            line = line[:idx].rstrip()
        out_lines.append(line)
    return "\n".join(out_lines)


def _iter_statements(sql: str):
    for stmt in sql.split(";"):
        s = stmt.strip()
        if s:
            yield s


def apply_views() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    engine = get_engine()
    if not test_connection(engine):
        raise RuntimeError("Cannot connect to MySQL.")

    sql_files = sorted(VIEWS_DIR.glob("*.sql"))
    if not sql_files:
        logger.warning("No .sql files found in %s", VIEWS_DIR)
        return

    for path in sql_files:
        logger.info("Applying %s", path.name)
        cleaned = _strip_sql_comments(path.read_text(encoding="utf-8"))
        with engine.begin() as conn:
            for stmt in _iter_statements(cleaned):
                conn.execute(text(stmt))

    logger.info("✔ All views applied successfully.")


if __name__ == "__main__":
    try:
        apply_views()
    except Exception as exc:
        logger.exception("Views application failed: %s", exc)
        sys.exit(1)