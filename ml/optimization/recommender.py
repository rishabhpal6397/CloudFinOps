"""
CloudFinOps – Optimization recommendation orchestrator
======================================================

Runs all rules, deduplicates by (resource_key, category), writes to
optimization_recommendations, and returns a summary.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from ml.common import get_db
from ml.optimization import rules

logger = logging.getLogger(__name__)

def _to_int(value: Any) -> int:
    """Convert a value to a valid Python int."""
    if value is None or pd.isna(value):
        raise ValueError(
            f"Expected a numeric value, got: {value!r}"
        )

    numeric_value = pd.to_numeric(
        value,
        errors="coerce",
    )

    if pd.isna(numeric_value):
        raise ValueError(
            f"Expected a numeric value, got: {value!r}"
        )

    return int(numeric_value)

def _to_float(value: Any) -> float:
    """Convert a value to a valid Python float."""
    if value is None or pd.isna(value):
        raise ValueError(
            f"Expected a numeric value, got: {value!r}"
        )

    numeric_value = pd.to_numeric(
        value,
        errors="coerce",
    )

    if pd.isna(numeric_value):
        raise ValueError(
            f"Expected a numeric value, got: {value!r}"
        )

    return float(numeric_value)
# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def _load_resource_daily(engine: Engine) -> pd.DataFrame:
    """Daily cost per resource with service metadata."""
    sql = text("""
        SELECT
            r.resource_key,
            r.resource_id,
            r.resource_name,
            s.service_name,
            s.service_category,
            d.full_date,
            SUM(f.cost)                                AS daily_cost,
            AVG(NULLIF(f.cost_per_unit, 0))            AS cost_per_unit
        FROM fact_cost f
        JOIN dim_date     d ON f.date_key     = d.date_key
        JOIN dim_service  s ON f.service_key  = s.service_key
        JOIN dim_resource r ON f.resource_key = r.resource_key
        GROUP BY r.resource_key, r.resource_id, r.resource_name,
                 s.service_name, s.service_category, d.full_date
        ORDER BY r.resource_key, d.full_date
    """)
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn)
    df["full_date"] = pd.to_datetime(df["full_date"]).dt.date
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run() -> dict[str, Any]:
    engine = get_db()

    logger.info("Loading resource-level daily cost…")
    df = _load_resource_daily(engine)
    logger.info("Loaded %s resource-days across %s resources",
                f"{len(df):,}", df["resource_key"].nunique())

    all_recs: list[dict] = []
    all_recs += rules.rule_recent_collapse(df)
    all_recs += rules.rule_near_zero_cost(df)
    all_recs += rules.rule_oversized_by_unit_cost(df)
    all_recs += rules.rule_storage_growth(df)
    all_recs += rules.rule_database_spike(df)

    logger.info("Collected %d raw recommendations", len(all_recs))

    # Deduplicate: keep highest-saving recommendation per (resource_key, category)
    if all_recs:
        rec_df = pd.DataFrame(all_recs)
        rec_df = (
            rec_df.sort_values("estimated_monthly_saving", ascending=False)
                  .drop_duplicates(subset=["resource_key", "category"], keep="first")
                  .reset_index(drop=True)
        )
    else:
        rec_df = pd.DataFrame()

    logger.info("After dedup: %d recommendations", len(rec_df))

    written = _write_recommendations(engine, rec_df)

    summary = {
        "total_written": written,
        "by_category":   rec_df["category"].value_counts().to_dict() if not rec_df.empty else {},
        "by_priority":   rec_df["priority"].value_counts().to_dict() if not rec_df.empty else {},
        "total_estimated_monthly_saving": (
            round(float(rec_df["estimated_monthly_saving"].sum()), 2)
            if not rec_df.empty else 0.0
        ),
    }
    return summary


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def _write_recommendations(engine: Engine, df: pd.DataFrame) -> int:
    """
    Replace all rows (full refresh — recommendations are derived data).
    """
    sql = text("""
        INSERT INTO optimization_recommendations (
            resource_key, category, finding, recommendation,
            estimated_monthly_saving, priority, status
        ) VALUES (
            :resource_key, :category, :finding, :recommendation,
            :estimated_monthly_saving, :priority, 'OPEN'
        )
    """)

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM optimization_recommendations"))
        if df.empty:
            logger.warning("No recommendations to write")
            return 0

        rows = [
            {
                "resource_key":             _to_int(r.resource_key),
                "category":                 r.category,
                "finding":                  r.finding,
                "recommendation":           r.recommendation,
                "estimated_monthly_saving": _to_float(r.estimated_monthly_saving),
                "priority":                 r.priority,
            }
            for r in df.itertuples(index=False)
        ]
        conn.execute(sql, rows)

    logger.info("Wrote %d recommendations", len(rows))
    return len(rows)