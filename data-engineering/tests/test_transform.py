"""Tests for the transform stage."""

from __future__ import annotations

from etl import transform


def test_transform_adds_derived_columns(sample_df):
    out = transform.transform(sample_df)
    for col in transform.DERIVED_COLUMNS:
        assert col in out.columns


def test_year_month_format(sample_df):
    out = transform.transform(sample_df)
    assert out.loc[0, "billing_year_month"] == "2025-10"


def test_is_weekend(sample_df):
    df = sample_df.copy()
    df.loc[0, "billing_date"] = "2025-10-04"   # Saturday
    out = transform.transform(df)
    assert bool(out.loc[0, "is_weekend"]) is True


def test_cost_per_unit(sample_df):
    out = transform.transform(sample_df)
    # cost 100.50 / usage 10.0 = 10.05
    assert abs(out.loc[0, "cost_per_unit"] - 10.05) < 1e-6