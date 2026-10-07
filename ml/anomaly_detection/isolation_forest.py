"""
CloudFinOps – Isolation Forest anomaly detection
================================================

Multivariate approach that considers the *context* around a cost point:
rolling means, lags, and calendar features. Useful when a cost spike is only
anomalous in combination with other signals (e.g. a weekend spike that's
unusual for that service).

Feature vector per (entity, day):
    daily_cost
    rolling_mean_7
    rolling_mean_30
    rolling_std_30
    lag_1
    lag_7
    day_of_week
    is_weekend
    month

Model
-----
sklearn.ensemble.IsolationForest with contamination=contamination.
Anomaly score = -score_samples (higher = more anomalous).
Severity derived from percentiles of the anomaly-score distribution.
"""

from __future__ import annotations

import json
import logging

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

DEFAULT_CONTAMINATION = 0.02
DEFAULT_N_ESTIMATORS = 200
DEFAULT_RANDOM_STATE = 42


def detect_anomalies(
    df: pd.DataFrame,
    entity_col: str = "service_name",
    value_col: str = "daily_cost",
    date_col: str = "full_date",
    contamination: float = DEFAULT_CONTAMINATION,
    n_estimators: int = DEFAULT_N_ESTIMATORS,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> pd.DataFrame:
    """
    Run IsolationForest per entity series. Returns the same schema as the
    statistical detector so both write to cost_anomalies uniformly.
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
        if len(group) < 30:
            continue

        feats = _build_features(group, value_col, date_col)
        valid_mask = feats.notna().all(axis=1) & (group[value_col].notna())

        # Require at least 20 usable rows to fit the forest
        if valid_mask.sum() < 20:
            continue

        # Both frames must be aligned on the same boolean mask, then reset
        # the index so positional indexing into them is safe.
        X_df = feats.loc[valid_mask].reset_index(drop=True)
        y_df = group.loc[valid_mask].reset_index(drop=True)

        X = X_df.to_numpy(dtype=float)

        model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1,
        )
        model.fit(X)

        predictions = model.predict(X)                 # -1 = anomaly, 1 = normal
        scores = -model.score_samples(X)               # higher = more anomalous

        anomaly_idx = np.where(predictions == -1)[0]
        if len(anomaly_idx) == 0:
            continue

        # Severity thresholds by percentile within this entity's anomaly set
        anomaly_scores = scores[anomaly_idx]
        p50 = float(np.percentile(anomaly_scores, 50))
        p75 = float(np.percentile(anomaly_scores, 75))
        p90 = float(np.percentile(anomaly_scores, 90))

        for idx in anomaly_idx:
            row = y_df.iloc[idx]
            feat_row = X_df.iloc[idx]

            cost = float(row[value_col])
            expected = float(feat_row["rolling_mean_30"])
            score = float(scores[idx])

            results.append({
                "anomaly_date":     row[date_col],
                "service_key":      row["service_key"],
                "resource_key":     row["resource_key"] if has_resource else None,
                "expected_cost":    round(expected, 4),
                "actual_cost":      round(cost, 4),
                "deviation":        round(cost - expected, 4),
                "anomaly_score":    round(score, 4),
                "severity":         _severity_from_percentile(
                    score, p50, p75, p90
                ),
                "detection_method": "isolation_forest",
                "details": json.dumps({
                    "contamination":   contamination,
                    "n_estimators":    n_estimators,
                    "rolling_mean_30": round(float(feat_row["rolling_mean_30"]), 4),
                    "rolling_std_30":  round(float(feat_row["rolling_std_30"]), 4),
                    "feature_row":     _features_to_dict(feat_row),
                }),
            })

    if not results:
        return _empty_result()

    out = pd.DataFrame(results).sort_values("anomaly_score", ascending=False)
    logger.info(
        "IsolationForest: %s anomalies across %s entities",
        f"{len(out):,}", df[entity_col].nunique(),
    )
    return out.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------
def _build_features(group: pd.DataFrame, value_col: str, date_col: str) -> pd.DataFrame:
    cost = group[value_col].astype(float)
    d = pd.to_datetime(group[date_col])

    feats = pd.DataFrame({
        "daily_cost":      cost,
        "rolling_mean_7":  cost.rolling(7,  min_periods=3).mean(),
        "rolling_mean_30": cost.rolling(30, min_periods=10).mean(),
        "rolling_std_30":  cost.rolling(30, min_periods=10).std(),
        "lag_1":           cost.shift(1),
        "lag_7":           cost.shift(7),
        "day_of_week":     d.dt.dayofweek.astype(float),
        "is_weekend":      (d.dt.dayofweek >= 5).astype(float),
        "month":           d.dt.month.astype(float),
    })
    # Fill rolling_std_30 NaN with 0 (constant series)
    feats["rolling_std_30"] = feats["rolling_std_30"].fillna(0.0)
    return feats


def _features_to_dict(row: pd.Series) -> dict:
    return {k: (round(float(v), 4) if pd.notna(v) else None) for k, v in row.items()}


def _severity_from_percentile(
    score: float, p50: float, p75: float, p90: float
) -> str:
    if score >= p90:
        return "CRITICAL"
    if score >= p75:
        return "HIGH"
    if score >= p50:
        return "MEDIUM"
    return "LOW"


def _empty_result() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "anomaly_date", "service_key", "resource_key",
        "expected_cost", "actual_cost", "deviation", "anomaly_score",
        "severity", "detection_method", "details",
    ])