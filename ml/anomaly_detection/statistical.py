"""
CloudFinOps – Statistical anomaly detection
===========================================

Z-score over a rolling window per service (and optionally per resource).

Algorithm
---------
For each series (e.g. service X's daily cost):
  1. Compute rolling mean μ_t and std σ_t over the trailing `window` days.
  2. Compute z_t = (cost_t − μ_t) / σ_t.
  3. Flag as anomaly when |z_t| ≥ z_threshold.
  4. Convert |z| to severity: LOW / MEDIUM / HIGH / CRITICAL.

Graceful failure
----------------
* Window rows with insufficient history (< min_periods) are skipped.
* σ = 0 (constant series) produces z = 0 → no anomalies.
* NaN z-scores are dropped.
"""

from __future__ import annotations

import json
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_WINDOW = 30
DEFAULT_MIN_PERIODS = 15
DEFAULT_Z_THRESHOLD = 3.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def detect_anomalies(
    df: pd.DataFrame,
    entity_col: str = "service_name",
    value_col: str = "daily_cost",
    date_col: str = "full_date",
    window: int = DEFAULT_WINDOW,
    min_periods: int = DEFAULT_MIN_PERIODS,
    z_threshold: float = DEFAULT_Z_THRESHOLD,
) -> pd.DataFrame:
    """
    Detect anomalies across all entity series.

    Parameters
    ----------
    df : DataFrame with columns [entity_col, service_key, date_col, value_col]
        (resource_key optional).
    entity_col : str
        Column to group by (e.g. 'service_name' or 'resource_id').
    """
    if df.empty:
        return _empty_result()

    required = {entity_col, date_col, value_col, "service_key"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    has_resource = "resource_key" in df.columns

    results: list[dict] = []
    for entity, group in df.groupby(entity_col):
        group = group.sort_values(date_col).reset_index(drop=True)

        if len(group) < min_periods + 1:
            continue  # not enough history

        rolling = group[value_col].rolling(window=window, min_periods=min_periods)
        group["expected"] = rolling.mean()
        group["std"] = rolling.std()

        # Avoid division by zero
        std = group["std"].replace(0, np.nan)
        group["z_score"] = (group[value_col] - group["expected"]) / std

        flagged = group[group["z_score"].abs() >= z_threshold].copy()
        flagged = flagged.dropna(subset=["z_score", "expected"])

        for r in flagged.itertuples(index=False):
            z_abs = abs(float(r.z_score))
            results.append({
                "anomaly_date":     getattr(r, date_col),
                "service_key":      getattr(r, "service_key"),
                "resource_key":     getattr(r, "resource_key") if has_resource else None,
                "expected_cost":    round(float(r.expected), 4),
                "actual_cost":      round(float(getattr(r, value_col)), 4),
                "deviation":        round(float(getattr(r, value_col) - r.expected), 4),
                "anomaly_score":    round(float(r.z_score), 4),
                "severity":         _severity_from_z(z_abs),
                "detection_method": f"zscore_rolling_{window}d",
                "details": json.dumps({
                    "window_days":  window,
                    "min_periods":  min_periods,
                    "z_threshold":  z_threshold,
                    "rolling_mean": round(float(r.expected), 4),
                    "rolling_std":  round(float(r.std), 4),
                    "z_abs":        round(z_abs, 4),
                    "direction":    "spike" if r.z_score > 0 else "drop",
                }),
            })

    if not results:
        return _empty_result()

    out = pd.DataFrame(results).sort_values("anomaly_score", key=lambda s: s.abs(), ascending=False)
    logger.info(
        "Statistical detector: %s anomalies across %s entities",
        f"{len(out):,}", df[entity_col].nunique(),
    )
    return out.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _severity_from_z(z_abs: float) -> str:
    if z_abs >= 6.0:
        return "CRITICAL"
    if z_abs >= 5.0:
        return "HIGH"
    if z_abs >= 4.0:
        return "MEDIUM"
    return "LOW"


def _empty_result() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "anomaly_date", "service_key", "resource_key",
        "expected_cost", "actual_cost", "deviation", "anomaly_score",
        "severity", "detection_method", "details",
    ])