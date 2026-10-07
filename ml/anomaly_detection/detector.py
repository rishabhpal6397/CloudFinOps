"""
CloudFinOps – Anomaly detection orchestrator
============================================

Runs both detectors (statistical + IsolationForest), writes both result sets
into cost_anomalies, and prints a summary.

Usage (from repo root):
    python ml/run_anomaly_detection.py
    python ml/run_anomaly_detection.py --window 30 --z-threshold 3.0
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from ml.common import (
    get_db,
    load_daily_resource_cost,
    load_daily_service_cost,
    write_anomalies,
)
from ml.anomaly_detection import isolation_forest, statistical

logger = logging.getLogger(__name__)


def run(
    window: int = 30,
    z_threshold: float = 3.0,
    contamination: float = 0.02,
    include_resources: bool = False,
    top_n_resources: int = 100,
) -> dict[str, Any]:
    """Run both anomaly detection pipelines and persist results."""
    engine = get_db()
    summary: dict[str, Any] = {}

    # -- 1. Load data --------------------------------------------------
    logger.info("Loading daily service cost…")
    service_df = load_daily_service_cost(engine)
    logger.info(
        "Loaded %s service-days across %s services",
        f"{len(service_df):,}", service_df["service_name"].nunique(),
    )

    # -- 2. Statistical detector (service level) -----------------------
    logger.info("Running statistical detector (window=%d, z>=%.1f)…", window, z_threshold)
    stat_anomalies = statistical.detect_anomalies(
        service_df, window=window, z_threshold=z_threshold,
    )
    stat_method = f"zscore_rolling_{window}d"
    stat_count = write_anomalies(engine, stat_anomalies, method=stat_method)
    summary["statistical"] = {
        "method":  stat_method,
        "count":   stat_count,
        "by_severity": _count_by_severity(stat_anomalies),
    }

    # -- 3. IsolationForest (service level) ----------------------------
    logger.info("Running IsolationForest (contamination=%.3f)…", contamination)
    if_anomalies = isolation_forest.detect_anomalies(
        service_df, contamination=contamination,
    )
    if_count = write_anomalies(engine, if_anomalies, method="isolation_forest")
    summary["isolation_forest"] = {
        "method":  "isolation_forest",
        "count":   if_count,
        "by_severity": _count_by_severity(if_anomalies),
    }

    # -- 4. Optional resource-level statistical -----------------------
    if include_resources:
        logger.info("Loading top %d resources by cost…", top_n_resources)
        resource_df = load_daily_resource_cost(engine, top_n=top_n_resources)
        logger.info("Loaded %s resource-days", f"{len(resource_df):,}")

        res_anomalies = statistical.detect_anomalies(
            resource_df,
            entity_col="resource_id",
            window=window,
            z_threshold=z_threshold,
        )
        res_method = f"zscore_resource_rolling_{window}d"
        res_count = write_anomalies(engine, res_anomalies, method=res_method)
        summary["resource_level"] = {
            "method":  res_method,
            "count":   res_count,
            "by_severity": _count_by_severity(res_anomalies),
        }

    return summary


def _count_by_severity(df: pd.DataFrame) -> dict[str, int]:
    if df.empty:
        return {}
    return df["severity"].value_counts().to_dict()