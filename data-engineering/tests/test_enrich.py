"""Tests for the enrich stage."""

from __future__ import annotations

from etl import enrich


def test_service_category_added(sample_df):
    out = enrich.enrich(sample_df)
    assert "service_category" in out.columns
    assert out.loc[out["service"] == "EC2", "service_category"].iloc[0] == "Compute"


def test_provider_display_name(sample_df):
    out = enrich.enrich(sample_df)
    aws_row = out.loc[out["provider"] == "AWS", "provider_display_name"].iloc[0]
    assert aws_row == "Amazon Web Services"


def test_tag_parsing(sample_df):
    out = enrich.enrich(sample_df)
    assert "tag_env" in out.columns
    assert out.loc[0, "tag_env"] == "production"
    assert out.loc[0, "tag_team"] == "platform"


def test_invalid_json_tags_do_not_crash(sample_df):
    df = sample_df.copy()
    df.loc[0, "tags"] = "not json"
    out = enrich.enrich(df)
    assert out.loc[0, "tag_env"] is None or out.loc[0, "tag_env"] != out.loc[0, "tag_env"]