from pathlib import Path

import pandas as pd


# --------------------------------------------------
# Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "cleaned_billing_data.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "transformed_billing_data.csv"
)


# --------------------------------------------------
# Load
# --------------------------------------------------

def load_cleaned_data() -> pd.DataFrame:
    """Load cleaned billing data."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Cleaned data not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print(f"Input file    : {INPUT_FILE}")
    print(f"Input records : {len(df):,}")

    return df


# --------------------------------------------------
# Date transformation
# --------------------------------------------------

def add_date_attributes(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Add useful calendar attributes."""

    df["billing_date"] = pd.to_datetime(
        df["billing_date"]
    )

    df["year"] = df["billing_date"].dt.year

    df["month"] = df["billing_date"].dt.month

    df["month_name"] = (
        df["billing_date"]
        .dt.strftime("%B")
    )

    df["quarter"] = (
        "Q"
        + df["billing_date"]
        .dt.quarter
        .astype(str)
    )

    df["day_of_month"] = (
        df["billing_date"].dt.day
    )

    df["day_of_week"] = (
        df["billing_date"]
        .dt.day_name()
    )

    df["is_weekend"] = (
        df["billing_date"]
        .dt.dayofweek >= 5
    )

    return df


# --------------------------------------------------
# Cost metrics
# --------------------------------------------------

def add_cost_metrics(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate derived cost metrics."""

    df["cost_per_unit"] = (
        df["cost"]
        / df["usage_quantity"]
        .replace(0, pd.NA)
    )

    df["cost_per_unit"] = (
        df["cost_per_unit"]
        .fillna(0)
    )

    return df


# --------------------------------------------------
# Normalized dimensions
# --------------------------------------------------

def add_normalized_dimensions(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Create normalized dimension keys."""

    df["provider_key"] = (
        df["provider"]
        .str.strip()
        .str.upper()
    )

    df["service_key"] = (
        df["service"]
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    df["environment_key"] = (
        df["environment"]
        .str.strip()
        .str.lower()
    )

    df["team_key"] = (
        df["team"]
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    return df


# --------------------------------------------------
# Cost categories
# --------------------------------------------------

def add_cost_category(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Classify records into simple cost categories."""

    service_categories = {

        "EC2": "Compute",
        "Virtual Machines": "Compute",
        "Compute Engine": "Compute",

        "S3": "Storage",
        "EBS": "Storage",
        "Blob Storage": "Storage",
        "Managed Disks": "Storage",
        "Cloud Storage": "Storage",

        "RDS": "Database",
        "Azure SQL": "Database",
        "BigQuery": "Database",

        "Lambda": "Serverless",
        "Functions": "Serverless",
        "Cloud Functions": "Serverless",

        "CloudFront": "Networking",
    }

    df["cost_category"] = (
        df["service"]
        .map(service_categories)
        .fillna("Other")
    )

    return df


# --------------------------------------------------
# Main transformation pipeline
# --------------------------------------------------

def transform_billing_data() -> None:

    print("\nStarting billing data transformation...\n")

    df = load_cleaned_data()

    df = add_date_attributes(df)

    df = add_cost_metrics(df)

    df = add_normalized_dimensions(df)

    df = add_cost_category(df)

    # Save transformed dataset
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n========== TRANSFORMATION SUMMARY ==========")

    print(
        f"Input records     : {len(df):,}"
    )

    print(
        f"Output records    : {len(df):,}"
    )

    print(
        f"Output columns    : {len(df.columns)}"
    )

    print(
        f"Output file       : {OUTPUT_FILE}"
    )

    print("\nCost categories:")

    print(
        df["cost_category"]
        .value_counts()
        .to_string()
    )

    print("\nTransformation completed.")


# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":
    transform_billing_data()