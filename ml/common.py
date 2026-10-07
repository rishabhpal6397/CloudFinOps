"""
CloudFinOps – Shared ML helpers
===============================

DB access, config, and small utilities used by anomaly detection,
forecasting, and recommendations.
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import date
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import bindparam, text
from sqlalchemy.engine import Engine

# ---------------------------------------------------------------------------
# Ensure data-engineering/ is importable so we can reuse etl.db.get_engine()
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DE_DIR = _REPO_ROOT / "data-engineering"
if str(_DE_DIR) not in sys.path:
    sys.path.insert(0, str(_DE_DIR))

from etl.db import get_engine, test_connection  # noqa: E402


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )


def get_db() -> Engine:
    """Return a live SQLAlchemy engine, raising if MySQL is down."""
    load_dotenv()
    engine = get_engine()
    if not test_connection(engine):
        raise RuntimeError("MySQL is not reachable. Start it with `sudo service mysql start`.")
    return engine


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_daily_service_cost(engine: Engine) -> pd.DataFrame:
    """
    Return a DataFrame of daily cost per service.

    Columns: service_key, service_name, full_date, daily_cost, record_count
    """
    sql = text("""
        SELECT
            s.service_key,
            s.service_name,
            s.service_category,
            d.full_date,
            ROUND(SUM(f.cost), 4) AS daily_cost,
            COUNT(*)              AS record_count
        FROM fact_cost f
        JOIN dim_date    d ON f.date_key    = d.date_key
        JOIN dim_service s ON f.service_key = s.service_key
        GROUP BY s.service_key, s.service_name, s.service_category, d.full_date
        ORDER BY s.service_name, d.full_date
    """)
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn)
    df["full_date"] = pd.to_datetime(df["full_date"]).dt.date
    return df


def load_daily_resource_cost(engine: Engine, top_n: int = 100) -> pd.DataFrame:
    """
    Return daily cost for the top N resources by total cost.

    Columns: resource_key, resource_id, resource_name, service_key,
             full_date, daily_cost
    """
    sql_top = text("""
        SELECT resource_key
        FROM fact_cost
        GROUP BY resource_key
        ORDER BY SUM(cost) DESC
        LIMIT :n
    """)
    with engine.connect() as conn:
        top_keys: list[int] = [int(row[0]) for row in conn.execute(sql_top, {"n": top_n})]

    if not top_keys:
        return pd.DataFrame()

    sql = text("""
        SELECT
            r.resource_key,
            r.resource_id,
            r.resource_name,
            f.service_key,
            d.full_date,
            ROUND(SUM(f.cost), 4) AS daily_cost
        FROM fact_cost f
        JOIN dim_date     d ON f.date_key     = d.date_key
        JOIN dim_resource r ON f.resource_key = r.resource_key
        WHERE f.resource_key IN :keys
        GROUP BY r.resource_key, r.resource_id, r.resource_name,
                 f.service_key, d.full_date
        ORDER BY r.resource_id, d.full_date
    """).bindparams(bindparam("keys", expanding=True))

    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params={"keys": top_keys})

    df["full_date"] = pd.to_datetime(df["full_date"]).dt.date
    return df


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def write_anomalies(engine: Engine, df: pd.DataFrame, method: str) -> int:
    """
    Replace all anomalies for a given method with the new set.

    Idempotent: DELETE WHERE detection_method = :method, then batch INSERT.
    Returns the number of rows inserted.
    """
    if df.empty:
        logger = logging.getLogger(__name__)
        logger.warning("No anomalies to write for method '%s'", method)
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM cost_anomalies WHERE detection_method = :m"),
                {"m": method},
            )
        return 0

    insert_sql = text("""
        INSERT INTO cost_anomalies (
            anomaly_date, service_key, resource_key,
            expected_cost, actual_cost, deviation, anomaly_score,
            severity, detection_method, details
        ) VALUES (
            :anomaly_date, :service_key, :resource_key,
            :expected_cost, :actual_cost, :deviation, :anomaly_score,
            :severity, :detection_method, :details
        )
    """)

    rows = []
    for r in df.itertuples(index=False):
        rows.append({
            "anomaly_date":     r.anomaly_date,
            "service_key":      int(r.service_key) if r.service_key is not None and not pd.isna(r.service_key) else None,
            "resource_key":     int(r.resource_key) if r.resource_key is not None and not pd.isna(r.resource_key) else None,
            "expected_cost":    float(r.expected_cost) if r.expected_cost is not None else None,
            "actual_cost":      float(r.actual_cost),
            "deviation":        float(r.deviation),
            "anomaly_score":    float(r.anomaly_score),
            "severity":         r.severity,
            "detection_method": r.detection_method,
            "details":          r.details,
        })

    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM cost_anomalies WHERE detection_method = :m"),
            {"m": method},
        )
        BATCH = 1000
        inserted = 0
        for start in range(0, len(rows), BATCH):
            conn.execute(insert_sql, rows[start:start + BATCH])
            inserted += len(rows[start:start + BATCH])

    logging.getLogger(__name__).info(
        "Wrote %s anomalies for method '%s'", f"{inserted:,}", method
    )
    return inserted