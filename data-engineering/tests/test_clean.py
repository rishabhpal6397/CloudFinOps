"""Tests for the clean stage."""

from __future__ import annotations

import pandas as pd

from etl import clean


def test_provider_normalisation(sample_df):
    df = sample_df.copy()
    df.loc[0, "provider"] = "aws"
    out, stats = clean.clean(df)
    assert out.loc[0, "provider"] == "AWS"
    assert stats["provider_normalised"] >= 1


def test_environment_alias_normalised(sample_df):
    df = sample_df.copy()
    df.loc[0, "environment"] = "prod"
    out, _ = clean.clean(df)
    assert out.loc[0, "environment"] == "production"


def test_whitespace_stripped(sample_df):
    df = sample_df.copy()
    df.loc[0, "team"] = "  platform  "
    out, _ = clean.clean(df)
    assert out.loc[0, "team"] == "platform"


def test_duplicates_dropped(sample_df):
    df = pd.concat([sample_df, sample_df.iloc[[0]]], ignore_index=True)
    out, stats = clean.clean(df)
    assert stats["dropped_duplicates"] >= 1


def test_null_critical_rows_dropped(sample_df):
    df = sample_df.copy()
    df.loc[0, "cost"] = None
    out, stats = clean.clean(df)
    assert stats["dropped_null_critical"] >= 1


def test_resource_name_filled_from_id(sample_df):
    df = sample_df.copy()
    df.loc[0, "resource_name"] = None
    out, _ = clean.clean(df)
    assert out.loc[0, "resource_name"] == out.loc[0, "resource_id"]