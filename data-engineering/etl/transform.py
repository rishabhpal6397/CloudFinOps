"""
CloudFinOps – ETL: Transform stage
==================================

Derives analytical columns that downstream layers (SQL views, ML models,
Power BI) depend on. All original columns are preserved.

Derived columns
---------------
* billing_year, billing_month, billing_quarter, billing_day
* day_of_week (0=Mon … 6=Sun), is_weekend
* billing_year_month (\"YYYY-MM\")
* cost_per_unit (safe division)
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DERIVED_COLUMNS = [
    "billing_year", "billing_month", "billing_quarter", "billing_day",
    "day_of_week", "is_weekend", "billing_year_month", "cost_per_unit",
]


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived date and ratio columns.

    Assumes `billing_date` is already a Python `date` object (post-clean).
    """
    df = df.copy()
    d = pd.to_datetime(df["billing_date"])

    df["billing_year"] = d.dt.year.astype("int32")
    df["billing_month"] = d.dt.month.astype("int8")
    df["billing_quarter"] = d.dt.quarter.astype("int8")
    df["billing_day"] = d.dt.day.astype("int8")
    df["day_of_week"] = d.dt.dayofweek.astype("int8")
    df["is_weekend"] = df["day_of_week"] >= 5
    df["billing_year_month"] = d.dt.strftime("%Y-%m")

    with np.errstate(divide="ignore", invalid="ignore"):
        cpu = df["cost"] / df["usage_quantity"].replace(0, np.nan)
    df["cost_per_unit"] = cpu.round(6)

    logger.info("Transformed: added %d derived columns", len(DERIVED_COLUMNS))
    return df