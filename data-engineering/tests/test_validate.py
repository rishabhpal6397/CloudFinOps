"""Tests for the validate stage."""

from __future__ import annotations

import pandas as pd

from etl import validate


def test_valid_dataframe_passes(sample_df):
    report = validate.validate(sample_df)
    assert report.is_structurally_valid
    assert report.error_count == 0


def test_missing_column_detected(sample_df):
    df = sample_df.drop(columns=["cost"])
    report = validate.validate(df)
    assert "cost" in report.missing_columns
    assert not report.is_structurally_valid


def test_null_critical_column_detected(sample_df):
    df = sample_df.copy()
    df.loc[0, "provider"] = None
    report = validate.validate(df)
    assert report.counts.get("null_check", 0) >= 1


def test_negative_cost_detected(sample_df):
    df = sample_df.copy()
    df.loc[0, "cost"] = -10
    report = validate.validate(df)
    assert report.counts.get("range_check", 0) >= 1


def test_invalid_provider_detected(sample_df):
    df = sample_df.copy()
    df.loc[0, "provider"] = "Oracle"
    report = validate.validate(df)
    assert report.counts.get("domain_check", 0) >= 1


def test_duplicate_rows_warned(sample_df):
    df = pd.concat([sample_df, sample_df.iloc[[0]]], ignore_index=True)
    report = validate.validate(df)
    assert report.counts.get("duplicate_check", 0) >= 1