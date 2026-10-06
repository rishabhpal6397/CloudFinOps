"""
CloudFinOps – Database connection helpers
=========================================

Reads configuration from environment variables (see .env.example).

All DB access flows through `get_engine()` so credentials live in exactly one
place. `pymysql` is used because it is a pure-Python MySQL driver — no
compilation, works everywhere Codespaces runs.
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def get_engine(echo: bool = False) -> Engine:
    """
    Build a SQLAlchemy engine from environment variables.

    Requires: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
    """
    load_dotenv()

    user = os.getenv("DB_USER", "finops")
    password = os.getenv("DB_PASSWORD", "finops_dev_password")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "cloudfinops")

    url = (
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
        f"?charset=utf8mb4"
    )

    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
        echo=echo,
    )
    logger.info("Engine created for %s@%s:%s/%s", user, host, port, name)
    return engine


def test_connection(engine: Engine) -> bool:
    """Return True if the engine can execute a trivial query."""
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("DB connection test failed: %s", exc)
        return False