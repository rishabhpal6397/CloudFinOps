"""
CloudFinOps – Synthetic Cloud Billing Data Generator
=====================================================

Generates realistic multi-cloud (AWS / Azure / GCP) billing data suitable for
demonstrating FinOps analytics, anomaly detection, and forecasting.

Output: data/raw/synthetic_billing_data.csv  (~120,000 records, 12 months)

Intentional patterns injected so downstream ML modules have signal to learn:
  * Weekly seasonality ........... weekends ~35% lower than weekdays
  * Month-over-month growth ...... +2% compounding on the base cost
  * Seasonal swing ............... Nov/Dec +30-35%, Jan -20%
  * Daily noise .................. ±15% random jitter
  * Random spike days ............ 15% of days have 1-3 resources inflated 3-6x
  * Sustained anomalies .......... 5 "problem" resources with a 60-day overrun
  * Sustained under-utilization .. 4 resources with a 90-day cost collapse
"""

from __future__ import annotations

import json
import os
import random
import sys
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from faker import Faker
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()

SEED = int(os.getenv("GEN_SEED", "42"))
random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


START_DATE = _parse_date(os.getenv("GEN_START_DATE", "2024-10-01"))
END_DATE = _parse_date(os.getenv("GEN_END_DATE", "2025-09-30"))
TOTAL_DAYS = (END_DATE - START_DATE).days + 1

TARGET_RECORDS = int(os.getenv("GEN_TARGET_RECORDS", "120000"))
AVG_RECORDS_PER_DAY = TARGET_RECORDS // TOTAL_DAYS  # ≈ 328

OUTPUT_DIR = os.getenv("GEN_OUTPUT_DIR", "data/raw")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "synthetic_billing_data.csv")

TEAMS = [
    "platform", "backend", "frontend", "data-engineering",
    "devops", "qa", "security", "ml", "infrastructure",
]
ENVIRONMENTS = ["production", "staging", "development"]

# Currency — all costs in USD
CURRENCY = "USD"

# ---------------------------------------------------------------------------
# Provider configuration
# ---------------------------------------------------------------------------
PROVIDERS_CONFIG: dict[str, dict] = {
    "AWS": {
        "services": {
            "EC2":        {"category": "Compute",     "unit": "hours",       "cost_range": (80, 800)},
            "S3":         {"category": "Storage",     "unit": "GB-Month",    "cost_range": (20, 300)},
            "RDS":        {"category": "Database",    "unit": "hours",       "cost_range": (150, 1200)},
            "Lambda":     {"category": "Compute",     "unit": "invocations", "cost_range": (5, 120)},
            "CloudFront": {"category": "Network",     "unit": "GB",          "cost_range": (30, 250)},
            "DynamoDB":   {"category": "Database",    "unit": "RCU/WCU",     "cost_range": (40, 400)},
            "EBS":        {"category": "Storage",     "unit": "GB-Month",    "cost_range": (15, 200)},
            "ELB":        {"category": "Network",     "unit": "hours",       "cost_range": (20, 150)},
            "SNS":        {"category": "Integration", "unit": "requests",    "cost_range": (2, 50)},
            "SQS":        {"category": "Integration", "unit": "requests",    "cost_range": (2, 60)},
        },
        "regions": ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1", "ap-southeast-1"],
        "accounts": ["aws-prod-001", "aws-staging-001", "aws-dev-001"],
    },
    "Azure": {
        "services": {
            "VirtualMachines": {"category": "Compute",     "unit": "hours",    "cost_range": (70, 900)},
            "BlobStorage":     {"category": "Storage",     "unit": "GB-Month", "cost_range": (15, 250)},
            "SQLDatabase":     {"category": "Database",    "unit": "hours",    "cost_range": (120, 1400)},
            "Functions":       {"category": "Compute",     "unit": "executions","cost_range": (5, 130)},
            "CDN":             {"category": "Network",     "unit": "GB",       "cost_range": (25, 220)},
            "CosmosDB":        {"category": "Database",    "unit": "RU/s",     "cost_range": (50, 500)},
            "DiskStorage":     {"category": "Storage",     "unit": "GB-Month", "cost_range": (12, 180)},
            "LoadBalancer":    {"category": "Network",     "unit": "hours",    "cost_range": (18, 140)},
            "ServiceBus":      {"category": "Integration", "unit": "messages", "cost_range": (3, 55)},
            "EventGrid":       {"category": "Integration", "unit": "events",   "cost_range": (2, 45)},
        },
        "regions": ["eastus", "westus2", "westeurope", "centralindia", "southeastasia"],
        "accounts": ["azure-prod-001", "azure-staging-001", "azure-dev-001"],
    },
    "GCP": {
        "services": {
            "ComputeEngine": {"category": "Compute",     "unit": "hours",       "cost_range": (60, 850)},
            "CloudStorage":  {"category": "Storage",     "unit": "GB-Month",    "cost_range": (18, 260)},
            "CloudSQL":      {"category": "Database",    "unit": "hours",       "cost_range": (130, 1150)},
            "CloudFunctions":{"category": "Compute",     "unit": "invocations", "cost_range": (4, 110)},
            "CloudCDN":      {"category": "Network",     "unit": "GB",          "cost_range": (22, 200)},
            "BigQuery":      {"category": "Database",    "unit": "TB-scanned",  "cost_range": (60, 900)},
            "PersistentDisk":{"category": "Storage",     "unit": "GB-Month",    "cost_range": (14, 190)},
            "CloudLoadBalancing": {"category": "Network","unit": "hours",       "cost_range": (16, 130)},
            "PubSub":        {"category": "Integration", "unit": "messages",    "cost_range": (3, 60)},
            "CloudDNS":      {"category": "Network",     "unit": "queries",     "cost_range": (2, 40)},
        },
        "regions": ["us-central1", "us-east1", "europe-west1", "asia-south1", "asia-southeast1"],
        "accounts": ["gcp-prod-001", "gcp-staging-001", "gcp-dev-001"],
    },
}


# ---------------------------------------------------------------------------
# Step 1 — Build the resource catalog
# ---------------------------------------------------------------------------
def build_resource_catalog() -> pd.DataFrame:
    """
    Build a static catalog of unique cloud resources.

    Produces ~540 resources across 3 providers × 3 accounts × ~60 per account.
    Each resource carries a base cost, a team owner, an environment, a region,
    a service, a usage unit, and a JSON-encoded tags blob.
    """
    resources: list[dict] = []

    for provider, config in PROVIDERS_CONFIG.items():
        for account_id in config["accounts"]:
            if "prod" in account_id:
                env = "production"
            elif "staging" in account_id:
                env = "staging"
            else:
                env = "development"

            n_resources = random.randint(55, 65)

            for _ in range(n_resources):
                service = random.choice(list(config["services"].keys()))
                svc = config["services"][service]
                region = random.choice(config["regions"])
                team = random.choice(TEAMS)
                base_cost = round(random.uniform(*svc["cost_range"]), 2)

                # Resource identifiers per provider conventions
                if provider == "AWS":
                    if service == "EC2":
                        resource_id = f"i-{fake.hexify(text='0^^^^^^^^^^^^^^^')}"
                    elif service == "S3":
                        resource_id = f"arn:aws:s3:::{fake.slug()}-{random.randint(100, 999)}"
                    elif service == "RDS":
                        resource_id = f"db-{fake.slug()}-{random.randint(10, 99)}"
                    else:
                        resource_id = f"{service.lower()}-{fake.hexify(text='^^^^^^^^^^')}"
                elif provider == "Azure":
                    resource_id = (
                        f"/subscriptions/{str(fake.uuid4())[:8]}-{str(fake.uuid4())[:4]}"
                        f"/resourceGroups/{fake.slug()}/providers/"
                        f"Microsoft.{service}/{fake.slug()}-{random.randint(1, 99)}"
                    )
                else:  # GCP
                    resource_id = (
                        f"projects/{fake.slug()}/zones/{region}/"
                        f"{service.lower()}/{fake.slug()}-{random.randint(1, 99)}"
                    )

                resource_name = f"{team}-{service.lower()}-{fake.word()}-{random.randint(1, 99)}"

                tags = {
                    "env": env,
                    "team": team,
                    "cost_center": f"CC-{random.randint(1000, 9999)}",
                    "owner": fake.user_name(),
                }

                resources.append({
                    "resource_id": resource_id,
                    "resource_name": resource_name,
                    "provider": provider,
                    "account_id": account_id,
                    "service": service,
                    "service_category": svc["category"],
                    "region": region,
                    "team": team,
                    "environment": env,
                    "usage_unit": svc["unit"],
                    "base_cost": base_cost,
                    "tags": json.dumps(tags),
                })

    df = pd.DataFrame(resources)
    # Deduplicate resource_ids if any collision occurred
    df = df.drop_duplicates(subset=["resource_id"]).reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Step 2 — Seasonal / trend multipliers
# ---------------------------------------------------------------------------
def _seasonal_multiplier(d: date) -> float:
    """Nov/Dec higher (holiday traffic), Jan lower, other months neutral."""
    return {11: 1.30, 12: 1.35, 1: 0.80, 2: 0.90}.get(d.month, 1.0)


def _weekend_multiplier(d: date) -> float:
    """Saturday / Sunday reduction."""
    return 0.65 if d.weekday() >= 5 else 1.0


# ---------------------------------------------------------------------------
# Step 3 — Inject controlled anomalies for downstream ML
# ---------------------------------------------------------------------------
def _pick_anomaly_resources(catalog: pd.DataFrame) -> dict[str, dict]:
    """
    Choose resources for injected anomaly patterns that overlap the LAST
    90 days of the data window, so downstream detectors can find them.
    """
    sampled = catalog.sample(n=16, random_state=SEED).reset_index(drop=True)

    # --- Time anchors (all relative to END_DATE so patterns are "recent") ---
    overrun_start    = END_DATE - timedelta(days=75)
    overrun_end      = END_DATE                    # 75-day overrun hits today

    collapse_start   = END_DATE - timedelta(days=60)
    collapse_end     = END_DATE                    # still collapsing

    dormant_start    = END_DATE - timedelta(days=120)   # 4 months dormant
    dormant_end      = END_DATE

    growth_start     = END_DATE - timedelta(days=120)   # 4 months of growth
    growth_end       = END_DATE

    # --- Overlapping-window "collapse" (triggers recent_collapse) ---
    # Move a slice of the sampled set to the present-window collapse.
    overrides: dict[str, dict] = {}

    # 5 overruns (still ongoing)
    for i in range(5):
        rid = sampled.iloc[i]["resource_id"]
        overrides[rid] = {
            "kind": "overrun",
            "start": overrun_start,
            "end": overrun_end,
            "multiplier_range": (3.0, 6.0),
        }

    # 3 recent collapses (currently low, will trigger recent_collapse)
    for i in range(5, 8):
        rid = sampled.iloc[i]["resource_id"]
        overrides[rid] = {
            "kind": "collapse",
            "start": collapse_start,
            "end": collapse_end,
            "multiplier_range": (0.05, 0.15),
        }

    # 3 dormant resources (near-zero for 4 months — triggers near_zero_cost)
    for i in range(8, 11):
        rid = sampled.iloc[i]["resource_id"]
        overrides[rid] = {
            "kind": "dormant",
            "start": dormant_start,
            "end": dormant_end,
            "multiplier_range": (0.001, 0.005),   # ~$0.05-$0.50/day
        }

    # 3 storage-growth resources (steady +35%/month — triggers storage_growth)
    for i in range(11, 14):
        rid = sampled.iloc[i]["resource_id"]
        overrides[rid] = {
            "kind": "growth",
            "start": growth_start,
            "end": growth_end,
            "monthly_growth_rate": 0.35,
        }

    # 2 oversized-per-unit resources (triggers oversized_by_unit_cost)
    for i in range(14, 16):
        rid = sampled.iloc[i]["resource_id"]
        overrides[rid] = {
            "kind": "oversized_unit",
            "start": START_DATE,
            "end": END_DATE,
            "unit_price_multiplier": 8.0,   # 8× the normal implied unit price
        }

    return overrides


# ---------------------------------------------------------------------------
# Step 4 — Generate daily billing records
# ---------------------------------------------------------------------------
def generate_records(catalog: pd.DataFrame) -> pd.DataFrame:
    """
    Iterate over every day in the range and emit ~AVG_RECORDS_PER_DAY rows.
    Vectorised per day for speed.
    """
    overrides = _pick_anomaly_resources(catalog)
    catalog_idx = catalog.set_index("resource_id", drop=False)

    daily_frames: list[pd.DataFrame] = []
    days = pd.date_range(START_DATE, END_DATE, freq="D")

    for day_idx, ts in enumerate(tqdm(days, desc="Generating daily records")):
        current_date = ts.date()

        # Target count for today: ±12% around average for natural variance
        low = int(AVG_RECORDS_PER_DAY * 0.88)
        high = int(AVG_RECORDS_PER_DAY * 1.12)
        n_today = random.randint(low, high)

        # Sample resources for today
        sampled = catalog.sample(n=n_today, replace=False).copy()

        # Base cost scaled by trend, seasonality, weekly pattern, and noise
        month_idx = day_idx / 30.0
        trend_mult = 1.0 + 0.02 * month_idx
        season_mult = _seasonal_multiplier(current_date)
        weekend_mult = _weekend_multiplier(current_date)
        noise = np.random.uniform(0.85, 1.15, size=n_today)

        cost = (
            sampled["base_cost"].to_numpy()
            * trend_mult
            * season_mult
            * weekend_mult
            * noise
        )

        # Apply anomaly overrides
        for rid, override in overrides.items():
            mask = sampled["resource_id"] == rid
            if not mask.any():
                continue

            mask_np = mask.to_numpy()
            kind = override["kind"]
            in_window = override["start"] <= current_date <= override["end"]

            if not in_window:
                continue

            if kind in ("overrun", "collapse", "dormant"):
                mult = np.random.uniform(*override["multiplier_range"])
                cost[mask_np] = cost[mask_np] * mult

            elif kind == "growth":
                # Compute months elapsed since growth_start
                days_in = (current_date - override["start"]).days
                months = days_in / 30.0
                growth = (1.0 + override["monthly_growth_rate"]) ** months
                cost[mask_np] = cost[mask_np] * growth

            elif kind == "oversized_unit":
                # Don't change cost — change implied unit price so that
                # cost_per_unit = cost / usage_quantity becomes 8× larger.
                # We handle this below by scaling usage_quantity down.
                pass

        # Random one-off spikes on ~15% of days
        if random.random() < 0.15:
            n_spikes = random.randint(1, 3)
            spike_idx = np.random.choice(n_today, size=n_spikes, replace=False)
            cost[spike_idx] *= np.random.uniform(3.0, 6.0, size=n_spikes)

        sampled["billing_date"] = current_date
        sampled["cost"] = np.round(np.clip(cost, 0.01, None), 2)
        sampled["currency"] = CURRENCY

        # Derive usage_quantity from cost / implied unit price
        # Implied unit price is between 0.01 and 1.0 USD per unit
        implied_unit_price = np.random.uniform(0.01, 1.0, size=n_today)

        # Apply oversized_unit override: scale implied price up 8× for those rows
        for rid, override in overrides.items():
            if override["kind"] != "oversized_unit":
                continue
            if not (override["start"] <= current_date <= override["end"]):
                continue
            mask = sampled["resource_id"].to_numpy() == rid
            if mask.any():
                implied_unit_price[mask] *= override["unit_price_multiplier"]
        sampled["usage_quantity"] = np.round(
            sampled["cost"].to_numpy() / implied_unit_price, 4
        )

        daily_frames.append(sampled)

    df = pd.concat(daily_frames, ignore_index=True)

    # Final column order matching the required schema
    df = df[[
        "billing_date",
        "provider",
        "account_id",
        "service",
        "region",
        "resource_id",
        "resource_name",
        "team",
        "environment",
        "usage_quantity",
        "usage_unit",
        "cost",
        "currency",
        "tags",
    ]]
    return df


# ---------------------------------------------------------------------------
# Step 5 — Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 60)
    print("CloudFinOps – Synthetic Cloud Billing Data Generator")
    print("=" * 60)
    print(f"  Date range      : {START_DATE} → {END_DATE}  ({TOTAL_DAYS} days)")
    print(f"  Target records  : ~{TARGET_RECORDS:,}")
    print(f"  Output          : {OUTPUT_FILE}")
    print(f"  Random seed     : {SEED}")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("▶ Building resource catalog...")
    catalog = build_resource_catalog()
    print(f"  ✔ {len(catalog):,} unique resources across "
          f"{catalog['provider'].nunique()} providers, "
          f"{catalog['account_id'].nunique()} accounts, "
          f"{catalog['service'].nunique()} services")

    print("▶ Generating daily billing records...")
    df = generate_records(catalog)

    print(f"  ✔ Generated {len(df):,} records")

    # Quick sanity checks
    assert (df["cost"] > 0).all(), "Negative or zero cost detected"
    assert df["currency"].eq(CURRENCY).all(), "Unexpected currency"
    assert df["billing_date"].notna().all(), "Missing billing dates"

    print("▶ Writing CSV...")
    df.to_csv(OUTPUT_FILE, index=False)
    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"  ✔ Wrote {OUTPUT_FILE}  ({size_mb:.1f} MB)")

    # Summary
    print()
    print("── Summary ───────────────────────────────────────────")
    print(f"  Total cost (USD)   : ${df['cost'].sum():,.2f}")
    print(f"  Average daily cost : ${df.groupby('billing_date')['cost'].sum().mean():,.2f}")
    print(f"  Min / Max cost     : ${df['cost'].min():,.2f} / ${df['cost'].max():,.2f}")
    print(f"  Providers          : {sorted(df['provider'].unique())}")
    print(f"  Teams              : {sorted(df['team'].unique())}")
    print(f"  Environments       : {sorted(df['environment'].unique())}")
    print("──────────────────────────────────────────────────────")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"✖ Generator failed: {exc}", file=sys.stderr)
        raise