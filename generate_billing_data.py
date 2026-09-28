from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Configuration
# ============================================================

SEED = 42

START_DATE = "2026-01-01"
END_DATE = "2026-09-30"

RESOURCES_PER_ACCOUNT = 25

OUTPUT_DIR = Path(__file__).resolve().parent / "data"

CSV_OUTPUT = OUTPUT_DIR / "raw_billing_data.csv"
EXCEL_OUTPUT = OUTPUT_DIR / "raw_billing_data.xlsx"


# ============================================================
# Reference Data
# ============================================================

PROVIDERS = {
    "AWS": {
        "accounts": [
            "aws-prod-001",
            "aws-dev-001",
        ],
        "services": [
            "EC2",
            "S3",
            "RDS",
            "Lambda",
            "EBS",
            "CloudFront",
        ],
        "regions": [
            "ap-south-1",
            "us-east-1",
            "eu-west-1",
        ],
    },

    "Azure": {
        "accounts": [
            "azure-prod-001",
            "azure-dev-001",
        ],
        "services": [
            "Virtual Machines",
            "Blob Storage",
            "Azure SQL",
            "Functions",
            "Managed Disks",
        ],
        "regions": [
            "Central India",
            "East US",
            "West Europe",
        ],
    },

    "GCP": {
        "accounts": [
            "gcp-prod-001",
            "gcp-dev-001",
        ],
        "services": [
            "Compute Engine",
            "Cloud Storage",
            "BigQuery",
            "Cloud Functions",
        ],
        "regions": [
            "asia-south1",
            "us-central1",
            "europe-west1",
        ],
    },
}


TEAMS = [
    "Data Engineering",
    "Java",
    "DBA",
    "DevOps",
    "Analytics",
    "QA",
]


ENVIRONMENTS = [
    "Development",
    "Testing",
    "Staging",
    "Production",
]


# ============================================================
# Service Configuration
# ============================================================

SERVICE_CONFIG = {
    "EC2": {
        "unit": "hours",
        "base_usage": (100, 700),
        "rate": 0.08,
    },

    "S3": {
        "unit": "GB-month",
        "base_usage": (50, 2000),
        "rate": 0.025,
    },

    "RDS": {
        "unit": "hours",
        "base_usage": (100, 700),
        "rate": 0.12,
    },

    "Lambda": {
        "unit": "requests",
        "base_usage": (10_000, 2_000_000),
        "rate": 0.00002,
    },

    "EBS": {
        "unit": "GB-month",
        "base_usage": (50, 2000),
        "rate": 0.08,
    },

    "CloudFront": {
        "unit": "GB",
        "base_usage": (100, 10_000),
        "rate": 0.09,
    },

    "Virtual Machines": {
        "unit": "hours",
        "base_usage": (100, 700),
        "rate": 0.08,
    },

    "Blob Storage": {
        "unit": "GB-month",
        "base_usage": (50, 2000),
        "rate": 0.024,
    },

    "Azure SQL": {
        "unit": "hours",
        "base_usage": (100, 700),
        "rate": 0.13,
    },

    "Functions": {
        "unit": "requests",
        "base_usage": (10_000, 2_000_000),
        "rate": 0.00002,
    },

    "Managed Disks": {
        "unit": "GB-month",
        "base_usage": (50, 2000),
        "rate": 0.075,
    },

    "Compute Engine": {
        "unit": "hours",
        "base_usage": (100, 700),
        "rate": 0.075,
    },

    "Cloud Storage": {
        "unit": "GB-month",
        "base_usage": (50, 2000),
        "rate": 0.022,
    },

    "BigQuery": {
        "unit": "TB",
        "base_usage": (0.1, 20),
        "rate": 5.0,
    },

    "Cloud Functions": {
        "unit": "requests",
        "base_usage": (10_000, 2_000_000),
        "rate": 0.00002,
    },
}


# ============================================================
# Helper Functions
# ============================================================

def generate_resource_id(provider, service, number):
    """Generate a unique resource ID."""

    provider_prefix = {
        "AWS": "aws",
        "Azure": "az",
        "GCP": "gcp",
    }

    service_code = (
        service.lower()
        .replace(" ", "-")
    )

    return (
        f"{provider_prefix[provider]}"
        f"-{service_code}"
        f"-{number:06d}"
    )


def generate_resource_name(
    service,
    team,
    environment,
    number,
):
    """Generate a readable resource name."""

    service_code = (
        service.lower()
        .replace(" ", "-")
    )

    team_code = (
        team.lower()
        .replace(" ", "-")
    )

    environment_code = environment.lower()

    return (
        f"{service_code}-"
        f"{team_code}-"
        f"{environment_code}-"
        f"{number:04d}"
    )


def generate_resource_inventory(rng):
    """
    Create a fixed resource inventory.

    Resources are created once and reused across
    all billing dates.
    """

    resources = []

    resource_counter = 1

    for provider, provider_data in PROVIDERS.items():

        for account in provider_data["accounts"]:

            for _ in range(RESOURCES_PER_ACCOUNT):

                service = rng.choice(
                    provider_data["services"]
                )

                region = rng.choice(
                    provider_data["regions"]
                )

                team = rng.choice(TEAMS)

                environment = rng.choice(
                    ENVIRONMENTS,
                    p=[
                        0.20,
                        0.20,
                        0.15,
                        0.45,
                    ],
                )

                resource_id = generate_resource_id(
                    provider,
                    service,
                    resource_counter,
                )

                resource_name = generate_resource_name(
                    service,
                    team,
                    environment,
                    resource_counter,
                )

                resources.append(
                    {
                        "provider": provider,
                        "account_id": account,
                        "service": service,
                        "region": region,
                        "resource_id": resource_id,
                        "resource_name": resource_name,
                        "team": team,
                        "environment": environment,
                    }
                )

                resource_counter += 1

    return pd.DataFrame(resources)


def generate_daily_usage(
    service,
    environment,
    rng,
):
    """Generate daily usage for a resource."""

    config = SERVICE_CONFIG[service]

    minimum, maximum = config["base_usage"]

    base_usage = rng.uniform(
        minimum,
        maximum,
    )

    environment_multiplier = {
        "Development": 0.60,
        "Testing": 0.80,
        "Staging": 1.00,
        "Production": 1.80,
    }

    multiplier = environment_multiplier[
        environment
    ]

    daily_variation = rng.uniform(
        0.85,
        1.15,
    )

    usage = (
        base_usage
        * multiplier
        * daily_variation
    )

    return round(
        usage,
        2,
    )


def generate_daily_cost(
    service,
    usage,
    rng,
):
    """Calculate daily cost from usage."""

    rate = SERVICE_CONFIG[
        service
    ]["rate"]

    pricing_variation = rng.uniform(
        0.90,
        1.10,
    )

    cost = (
        usage
        * rate
        * pricing_variation
    )

    return round(
        cost,
        2,
    )


# ============================================================
# Generate Billing Data
# ============================================================

def generate_billing_data():

    rng = np.random.default_rng(
        SEED
    )

    dates = pd.date_range(
        start=START_DATE,
        end=END_DATE,
        freq="D",
    )

    resources = generate_resource_inventory(
        rng
    )

    records = []

    for date in dates:

        for _, resource in resources.iterrows():

            usage = generate_daily_usage(
                resource["service"],
                resource["environment"],
                rng,
            )

            cost = generate_daily_cost(
                resource["service"],
                usage,
                rng,
            )

            record = {
                "billing_date": date,
                "provider": resource["provider"],
                "account_id": resource["account_id"],
                "service": resource["service"],
                "region": resource["region"],
                "resource_id": resource["resource_id"],
                "resource_name": resource["resource_name"],
                "team": resource["team"],
                "environment": resource["environment"],
                "usage_quantity": usage,
                "usage_unit": SERVICE_CONFIG[
                    resource["service"]
                ]["unit"],
                "cost": cost,
                "currency": "USD",
            }

            records.append(record)

    return pd.DataFrame(records)


# ============================================================
# Inject Synthetic Anomalies
# ============================================================

def inject_anomalies(df):

    rng = np.random.default_rng(
        SEED
    )

    anomaly_count = max(
        1,
        int(len(df) * 0.01),
    )

    anomaly_indices = rng.choice(
        df.index,
        size=anomaly_count,
        replace=False,
    )

    anomaly_multiplier = rng.uniform(
        4,
        10,
        size=anomaly_count,
    )

    df.loc[
        anomaly_indices,
        "cost",
    ] *= anomaly_multiplier

    df.loc[
        anomaly_indices,
        "cost",
    ] = df.loc[
        anomaly_indices,
        "cost",
    ].round(2)

    return df


# ============================================================
# Validation
# ============================================================

def validate_generated_data(
    df,
    resource_inventory,
):

    required_columns = [
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
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError(
            "Generated dataset is empty."
        )

    if df["cost"].isna().any():
        raise ValueError(
            "Missing cost values found."
        )

    if (df["cost"] < 0).any():
        raise ValueError(
            "Negative costs found."
        )

    if df["resource_id"].isna().any():
        raise ValueError(
            "Missing resource IDs found."
        )

    expected_resource_count = len(
        resource_inventory
    )

    actual_resource_count = df[
        "resource_id"
    ].nunique()

    if actual_resource_count != expected_resource_count:
        raise ValueError(
            "Resource count mismatch."
        )

    print("\nValidation successful.")

    print(
        f"Billing records : {len(df):,}"
    )

    print(
        f"Unique resources: "
        f"{actual_resource_count:,}"
    )

    print(
        f"Date range      : "
        f"{df['billing_date'].min().date()} "
        f"to "
        f"{df['billing_date'].max().date()}"
    )

    print(
        f"Providers       : "
        f"{df['provider'].nunique()}"
    )

    print(
        f"Services        : "
        f"{df['service'].nunique()}"
    )

    print(
        f"Teams           : "
        f"{df['team'].nunique()}"
    )

    print(
        f"Environments    : "
        f"{df['environment'].nunique()}"
    )

    print(
        f"Total Cost      : "
        f"${df['cost'].sum():,.2f}"
    )


# ============================================================
# Save Data
# ============================================================

def save_data(df):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        CSV_OUTPUT,
        index=False,
    )

    df.to_excel(
        EXCEL_OUTPUT,
        index=False,
    )

    print("\nData generation completed.")

    print(
        f"CSV file   : {CSV_OUTPUT}"
    )

    print(
        f"Excel file : {EXCEL_OUTPUT}"
    )


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    billing_df = generate_billing_data()

    resource_inventory = (
        billing_df[
            [
                "provider",
                "account_id",
                "service",
                "region",
                "resource_id",
                "resource_name",
                "team",
                "environment",
            ]
        ]
        .drop_duplicates(
            subset=["resource_id"]
        )
        .reset_index(drop=True)
    )

    billing_df = inject_anomalies(
        billing_df
    )

    validate_generated_data(
        billing_df,
        resource_inventory,
    )

    save_data(
        billing_df
    )

    print("\nSample records:")

    print(
        billing_df.head(10).to_string(
            index=False
        )
    )