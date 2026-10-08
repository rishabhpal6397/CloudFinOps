"""Tests for the optimization rule engine."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from ml.optimization import rules


def _make_resource_series(
    resource_key: int = 1,
    days: int = 180,
    base_cost: float = 100.0,
    collapse_from_day: int | None = None,
    collapse_factor: float = 0.1,
) -> pd.DataFrame:
    base = date(2026, 1, 1)
    rows = []
    for i in range(days):
        cost = base_cost
        if collapse_from_day is not None and i >= collapse_from_day:
            cost *= collapse_factor
        rows.append({
            "resource_key":    resource_key,
            "resource_id":     f"r{resource_key}",
            "resource_name":   f"res{resource_key}",
            "service_name":    "EC2",
            "service_category":"Compute",
            "full_date":       base + timedelta(days=i),
            "daily_cost":      cost,
            "cost_per_unit":   0.5,
        })
    return pd.DataFrame(rows)


def test_recent_collapse_detected():
    df = _make_resource_series(collapse_from_day=150)
    out = rules.rule_recent_collapse(df, recent_days=30, baseline_days=90)
    assert len(out) >= 1
    assert out[0]["category"] == "UNDERUTILIZED"
    assert out[0]["estimated_monthly_saving"] > 0


def test_no_collapse_returns_empty():
    df = _make_resource_series()
    out = rules.rule_recent_collapse(df)
    assert out == []


def test_near_zero_cost_detected():
    df = _make_resource_series(base_cost=0.05)
    out = rules.rule_near_zero_cost(df, window_days=60, daily_threshold=1.0)
    assert len(out) >= 1
    assert out[0]["category"] == "UNUSED"


def test_oversized_detected():
    # Build a realistic peer group: 5 normal resources at 0.5, one outlier at 5.0.
    # Median across 6 resources = 0.5, so the 5.0 outlier is 10× the median and
    # clearly exceeds the 2× threshold.
    frames = [_make_resource_series(resource_key=1, base_cost=100.0)]
    frames[0]["cost_per_unit"] = 0.5

    for key in (3, 4, 5, 6):  # 4 more normal peers
        peer = _make_resource_series(resource_key=key, base_cost=100.0)
        peer["cost_per_unit"] = 0.5
        frames.append(peer)

    outlier = _make_resource_series(resource_key=2, base_cost=100.0)
    outlier["cost_per_unit"] = 5.0
    frames.append(outlier)

    df = pd.concat(frames, ignore_index=True)
    out = rules.rule_oversized_by_unit_cost(df, multiplier=2.0, min_observations=30)
    flagged_keys = {r["resource_key"] for r in out}
    assert 2 in flagged_keys, f"Expected resource 2 to be flagged, got {flagged_keys}"
    assert 1 not in flagged_keys