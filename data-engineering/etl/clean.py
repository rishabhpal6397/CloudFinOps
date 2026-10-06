"""
CloudFinOps – ETL: Clean stage
==============================

Normalises and repairs a validated DataFrame.

Cleaning philosophy
-------------------
* Only strict failures are dropped (unparseable dates, nulls in critical columns).
* Fixable issues are repaired (whitespace, case, aliases, type coercion).
* Every action is counted and returned as `stats` so the caller can log or
  persist it.

Idempotent: running clean() twice produces the same output.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Normalisation maps
# ---------------------------------------------------------------------------
PROVIDER_ALIASES: dict[str, str] = {
    "aws": "AWS", "amazon": "AWS", "amazon web services": "AWS",
    "azure": "Azure", "microsoft azure": "Azure", "microsoft": "Azure",
    "gcp": "GCP", "google": "GCP", "google cloud": "GCP",
    "google cloud platform": "GCP",
}

ENVIRONMENT_ALIASES: dict[str, str] = {
    "prod": "production", "prd": "production",
    "stg": "staging", "stage": "staging",
    "dev": "development", "develop": "development",
}

CRITICAL_FOR_DROP = [
    "billing_date", "provider", "account_id", "service", "region",
    "resource_id", "team", "environment",
    "usage_quantity", "usage_unit", "cost", "currency",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Normalise and repair a validated DataFrame.

    Returns
    -------
    (cleaned_df, stats)
        cleaned_df : pd.DataFrame with rows dropped where necessary
        stats      : dict of counters describing what was changed/dropped
    """
    stats: dict[str, Any] = {"rows_in": len(df)}
    df = df.copy()

    df = _strip_whitespace(df, stats)
    df = _normalise_provider(df, stats)
    df = _normalise_environment(df, stats)
    df = _coerce_types(df, stats)
    df = _fill_resource_name(df, stats)
    df = _drop_nulls_in_critical(df, stats)
    df = _deduplicate(df, stats)

    stats["rows_out"] = len(df)
    stats["rows_dropped_total"] = stats["rows_in"] - stats["rows_out"]

    logger.info(
        "Cleaned: %s → %s rows (dropped %s)",
        f"{stats['rows_in']:,}",
        f"{stats['rows_out']:,}",
        f"{stats['rows_dropped_total']:,}",
    )
    return df.reset_index(drop=True), stats


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------
def _strip_whitespace(df: pd.DataFrame, stats: dict) -> pd.DataFrame:
    obj_cols = df.select_dtypes(include="object").columns
    touched = 0
    for col in obj_cols:
        mask = df[col].notna()
        df.loc[mask, col] = df.loc[mask, col].astype(str).str.strip()
        # Treat empty strings as null
        empty = df[col] == ""
        touched += int(empty.sum())
        df.loc[empty, col] = None
    stats["whitespace_cleaned"] = touched
    return df


def _normalise_provider(df: pd.DataFrame, stats: dict) -> pd.DataFrame:
    def _map(value):
        if not isinstance(value, str):
            return value
        return PROVIDER_ALIASES.get(value.lower().strip(), value)

    before = df["provider"].copy()
    df["provider"] = df["provider"].map(_map)
    stats["provider_normalised"] = int((before != df["provider"]).sum())
    return df


def _normalise_environment(df: pd.DataFrame, stats: dict) -> pd.DataFrame:
    def _map(value):
        if not isinstance(value, str):
            return value
        lowered = value.lower().strip()
        return ENVIRONMENT_ALIASES.get(lowered, lowered)

    before = df["environment"].copy()
    df["environment"] = df["environment"].map(_map)
    stats["environment_normalised"] = int((before != df["environment"]).sum())
    return df


def _coerce_types(df: pd.DataFrame, stats: dict) -> pd.DataFrame:
    # billing_date → Python date
    before = int(df["billing_date"].notna().sum())
    df["billing_date"] = pd.to_datetime(df["billing_date"], errors="coerce").dt.date
    after = int(df["billing_date"].notna().sum())
    stats["billing_date_parse_failures"] = before - after

    # cost → float, rounded to 2 decimals
    before = int(df["cost"].notna().sum())
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce").round(2)
    stats["cost_parse_failures"] = before - int(df["cost"].notna().sum())

    # usage_quantity → float, rounded to 4 decimals
    before = int(df["usage_quantity"].notna().sum())
    df["usage_quantity"] = pd.to_numeric(df["usage_quantity"], errors="coerce").round(4)
    stats["usage_quantity_parse_failures"] = before - int(df["usage_quantity"].notna().sum())

    return df


def _fill_resource_name(df: pd.DataFrame, stats: dict) -> pd.DataFrame:
    mask = df["resource_name"].isna()
    count = int(mask.sum())
    df.loc[mask, "resource_name"] = df.loc[mask, "resource_id"]
    stats["resource_name_filled"] = count
    return df


def _drop_nulls_in_critical(df: pd.DataFrame, stats: dict) -> pd.DataFrame:
    mask = df[CRITICAL_FOR_DROP].isna().any(axis=1)
    dropped = int(mask.sum())
    stats["dropped_null_critical"] = dropped
    return df.loc[~mask].copy()


def _deduplicate(df: pd.DataFrame, stats: dict) -> pd.DataFrame:
    subset = ["billing_date", "provider", "account_id", "resource_id", "service"]
    before = len(df)
    df = df.drop_duplicates(subset=subset, keep="first")
    stats["dropped_duplicates"] = before - len(df)
    return df