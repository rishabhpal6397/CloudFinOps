"""
CloudFinOps – ETL: Enrich stage
===============================

Adds reference data and parses semi-structured columns.

Reference data
--------------
* service_category       – map service → category (Compute, Storage, Database, …)
* provider_display_name  – canonical long-form provider name

Tag extraction
--------------
* tag_env, tag_team, tag_cost_center, tag_owner  – parsed from the `tags` JSON
"""

from __future__ import annotations

import json
import logging

import pandas as pd

logger = logging.getLogger(__name__)

SERVICE_CATEGORY_MAP: dict[str, str] = {
    # AWS
    "EC2": "Compute", "Lambda": "Compute",
    "S3": "Storage", "EBS": "Storage",
    "RDS": "Database", "DynamoDB": "Database",
    "CloudFront": "Network", "ELB": "Network",
    "SNS": "Integration", "SQS": "Integration",
    # Azure
    "VirtualMachines": "Compute", "Functions": "Compute",
    "BlobStorage": "Storage", "DiskStorage": "Storage",
    "SQLDatabase": "Database", "CosmosDB": "Database",
    "CDN": "Network", "LoadBalancer": "Network",
    "ServiceBus": "Integration", "EventGrid": "Integration",
    # GCP
    "ComputeEngine": "Compute", "CloudFunctions": "Compute",
    "CloudStorage": "Storage", "PersistentDisk": "Storage",
    "CloudSQL": "Database", "BigQuery": "Database",
    "CloudCDN": "Network", "CloudLoadBalancing": "Network",
    "CloudDNS": "Network",
    "PubSub": "Integration",
}

PROVIDER_DISPLAY: dict[str, str] = {
    "AWS": "Amazon Web Services",
    "Azure": "Microsoft Azure",
    "GCP": "Google Cloud Platform",
}

TAG_FIELDS = {
    "tag_env": "env",
    "tag_team": "team",
    "tag_cost_center": "cost_center",
    "tag_owner": "owner",
}


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Add reference columns and flatten the `tags` JSON column."""
    df = df.copy()

    df["service_category"] = df["service"].map(SERVICE_CATEGORY_MAP).fillna("Other")
    df["provider_display_name"] = (
        df["provider"].map(PROVIDER_DISPLAY).fillna(df["provider"])
    )

    tags_df = _parse_tags(df["tags"])
    df = pd.concat([df, tags_df], axis=1)

    logger.info(
        "Enriched: added service_category, provider_display_name, and %d tag_* columns",
        len(TAG_FIELDS),
    )
    return df


def _parse_tags(series: pd.Series) -> pd.DataFrame:
    """Parse the `tags` JSON column into flat tag_* columns."""
    buckets: dict[str, list] = {col: [] for col in TAG_FIELDS}

    for value in series:
        parsed = _parse_one(value)
        for out_col, json_key in TAG_FIELDS.items():
            buckets[out_col].append(parsed.get(json_key))

    return pd.DataFrame(buckets, index=series.index)


def _parse_one(value) -> dict:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return {}
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}