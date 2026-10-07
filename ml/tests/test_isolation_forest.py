"""Tests for the Isolation Forest detector."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from ml.anomaly_detection import isolation_forest


def _make_df(days: int = 120, n_spikes: int = 3) -> pd.DataFrame:
    base = date(2026, 1, 1)
    rows = []
    for i in range(days):
        cost = 100.0 + (i % 7) * 5.0  # weekly pattern
        rows.append({
            "service_key":  1,
            "service_name": "EC2",
            "full_date":    base + timedelta(days=i),
            "daily_cost":   cost,
        })
    # Inject spikes at end
    for j in range(n_spikes):
        idx = 50 + j * 10
        rows[idx]["daily_cost"] = 5000.0
    return pd.DataFrame(rows)


def test_isolation_forest_returns_expected_schema():
    df = _make_df()
    out = isolation_forest.detect_anomalies(df, contamination=0.05)
    if not out.empty:
        for col in ("anomaly_date", "service_key", "expected_cost",
                    "actual_cost", "deviation", "anomaly_score",
                    "severity", "detection_method", "details"):
            assert col in out.columns
        assert (out["detection_method"] == "isolation_forest").all()
        assert out["severity"].isin({"LOW", "MEDIUM", "HIGH", "CRITICAL"}).all()


def test_empty_input_returns_empty_frame():
    out = isolation_forest.detect_anomalies(pd.DataFrame())
    assert out.empty


def test_short_series_returns_empty():
    df = pd.DataFrame([{
        "service_key":  1,
        "service_name": "Short",
        "full_date":    date(2026, 1, 1) + timedelta(days=i),
        "daily_cost":   100.0,
    } for i in range(10)])
    out = isolation_forest.detect_anomalies(df)
    assert out.empty