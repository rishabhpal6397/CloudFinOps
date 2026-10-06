"""Shared pytest fixtures for the ETL test suite."""

from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """A small, valid billing DataFrame."""
    return pd.DataFrame({
        "billing_date":   ["2025-10-01", "2025-10-01", "2025-10-02", "2025-10-02"],
        "provider":       ["AWS",        "Azure",      "AWS",        "GCP"],
        "account_id":     ["a1",         "a2",         "a1",         "a3"],
        "service":        ["EC2",        "VirtualMachines", "S3",   "BigQuery"],
        "region":         ["us-east-1",  "eastus",     "us-east-1",  "us-central1"],
        "resource_id":    ["r1",         "r2",         "r3",         "r4"],
        "resource_name":  ["res1",       "res2",       "res3",       "res4"],
        "team":           ["platform",   "backend",    "platform",   "ml"],
        "environment":    ["production", "staging",    "production", "development"],
        "usage_quantity": [10.0,         20.0,         5.0,          100.0],
        "usage_unit":     ["hours",      "hours",      "GB-Month",   "TB-scanned"],
        "cost":           [100.50,       200.75,       30.00,        500.00],
        "currency":       ["USD",        "USD",        "USD",        "USD"],
        "tags":           ['{"env":"production","team":"platform"}'] * 4,
    })