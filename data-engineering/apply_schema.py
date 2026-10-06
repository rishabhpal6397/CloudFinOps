"""
CloudFinOps – Apply MySQL schema
================================

Runs the DDL files in database/schema/ in order.
Idempotent: uses CREATE TABLE IF NOT EXISTS.

Usage (from repo root):
    python data-engineering/apply_schema.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from sqlalchemy import text

from etl.db import get_engine, test_connection

logger = logging.getLogger("apply_schema")

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "database" / "schema"
SCHEMA_FILES = [
    "00_create_database.sql",
    "01_dimensions.sql",
    "02_facts.sql",
    "03_finops.sql",
]


def _strip_sql_comments(sql: str) -> str:
    """
    Remove both full-line and inline `--` comments.

    Safe for our DDL because no `--` sequence appears inside a string literal.
    """
    out_lines: list[str] = []
    for line in sql.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("--"):
            continue
        idx = line.find("--")
        if idx >= 0:
            line = line[:idx].rstrip()
        out_lines.append(line)
    return "\n".join(out_lines)


def _iter_statements(sql: str):
    """Yield individual SQL statements split on `;`, skipping empties."""
    for stmt in sql.split(";"):
        s = stmt.strip()
        if s:
            yield s


def apply_schema(verbose: bool = True) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    engine = get_engine()
    if not test_connection(engine):
        raise RuntimeError("Cannot connect to MySQL. Is it running?")

    for fname in SCHEMA_FILES:
        path = SCHEMA_DIR / fname
        if not path.exists():
            logger.warning("Schema file missing, skipping: %s", path)
            continue

        logger.info("Applying %s", fname)
        raw_sql = path.read_text(encoding="utf-8")
        cleaned = _strip_sql_comments(raw_sql)

        with engine.begin() as conn:
            for stmt in _iter_statements(cleaned):
                if verbose:
                    logger.debug("  → %s", stmt[:80].replace("\n", " "))
                conn.execute(text(stmt))

    logger.info("✔ Schema applied successfully.")


if __name__ == "__main__":
    try:
        apply_schema()
    except Exception as exc:
        logger.exception("Schema application failed: %s", exc)
        sys.exit(1)