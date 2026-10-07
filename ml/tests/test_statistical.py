"""Tests for the statistical anomaly detector."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from ml.anomaly_detection import statistical


def _make_series(service: str = "EC2", days: int = 60, spike_day: int = 40,
                 spike_mult: float = 10.0) -> pd.DataFrame:
    base = date(2026, 1, 1)
    rows = []
    for i in range(days):
        cost = 100.0
        if i == spike_day:
            cost *= spike_mult
        rows.append({
            "service_key":  1,
            "service_name": service,
            "full_date":    base + timedelta(days=i),
            "daily_cost":   cost,
        })
    return pd.DataFrame(rows)


def test_spike_is_detected():
    df = _make_series()
    out = statistical.detect_anomalies(df, window=20, min_periods=10, z_threshold=3.0)
    assert len(out) >= 1
    spike_row = out.iloc[0]
    assert spike_row["anomaly_date"] == date(2026, 2, 10)  # day 40
    assert spike_row["actual_cost"] == 1000.0
    assert spike_row["severity"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert spike_row["detection_method"] == "zscore_rolling_20d"


def test_constant_series_produces_no_anomalies():
    base = date(2026, 1, 1)
    df = pd.DataFrame([{
        "service_key":  1,
        "service_name": "Constant",
        "full_date":    base + timedelta(days=i),
        "daily_cost":   50.0,
    } for i in range(60)])
    out = statistical.detect_anomalies(df, window=20, min_periods=10, z_threshold=3.0)
    assert out.empty


def test_short_series_is_skipped():
    df = _make_series(days=5, spike_day=3)
    out = statistical.detect_anomalies(df, window=20, min_periods=10, z_threshold=3.0)
    assert out.empty


def test_drop_is_detected():
    base = date(2026, 1, 1)
    rows = []
    for i in range(60):
        cost = 100.0 if i != 40 else 1.0
        rows.append({
            "service_key":  1,
            "service_name": "DropTest",
            "full_date":    base + timedelta(days=i),
            "daily_cost":   cost,
        })
    df = pd.DataFrame(rows)
    out = statistical.detect_anomalies(df, window=20, min_periods=10, z_threshold=3.0)
    assert len(out) >= 1
    assert (out["anomaly_score"] < 0).any()