from pathlib import Path

import pandas as pd


# --------------------------------------------------
# Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "data" / "raw_billing_data.csv"


# --------------------------------------------------
# Expected schema
# --------------------------------------------------

REQUIRED_COLUMNS = [
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


# --------------------------------------------------
# Load data
# --------------------------------------------------

def load_billing_data(file_path: Path) -> pd.DataFrame:
    """
    Load raw billing data from CSV.
    """

    if not file_path.exists():
        raise FileNotFoundError(
            f"Billing data file not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    print(f"Loaded file : {file_path}")
    print(f"Records     : {len(df):,}")
    print(f"Columns     : {len(df.columns)}")

    return df


# --------------------------------------------------
# Schema validation
# --------------------------------------------------

def validate_schema(df: pd.DataFrame) -> None:
    """
    Validate that all required columns exist.
    """

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    print("Schema validation : PASSED")


# --------------------------------------------------
# Data-quality validation
# --------------------------------------------------

def validate_data_quality(df: pd.DataFrame) -> None:
    """
    Perform basic data-quality checks.
    """

    errors = []

    # Empty dataset
    if df.empty:
        errors.append("Dataset is empty.")

    # Null checks
    null_counts = df[REQUIRED_COLUMNS].isnull().sum()

    null_columns = null_counts[null_counts > 0]

    if not null_columns.empty:
        errors.append(
            f"Null values found: {null_columns.to_dict()}"
        )

    # Cost validation
    if (df["cost"] < 0).any():
        errors.append("Negative cost values found.")

    # Usage validation
    if (df["usage_quantity"] < 0).any():
        errors.append("Negative usage quantities found.")

    # Date validation
    invalid_dates = pd.to_datetime(
        df["billing_date"],
        errors="coerce"
    ).isna()

    if invalid_dates.any():
        errors.append(
            f"Invalid billing dates found: {invalid_dates.sum()}"
        )

    # Resource ID validation
    if df["resource_id"].astype(str).str.strip().eq("").any():
        errors.append("Empty resource IDs found.")

    # Currency validation
    if not df["currency"].isin(["USD"]).all():
        errors.append("Unexpected currency values found.")

    if errors:
        print("\nData-quality validation : FAILED")

        for error in errors:
            print(f"  - {error}")

        raise ValueError(
            "Data-quality validation failed."
        )

    print("Data-quality validation : PASSED")


# --------------------------------------------------
# Summary
# --------------------------------------------------

def print_summary(df: pd.DataFrame) -> None:
    """
    Print useful information about the dataset.
    """

    dates = pd.to_datetime(df["billing_date"])

    print("\n========== BILLING DATA SUMMARY ==========")

    print(f"Records          : {len(df):,}")
    print(f"Unique resources : {df['resource_id'].nunique():,}")
    print(f"Date range       : {dates.min().date()} to {dates.max().date()}")
    print(f"Providers        : {df['provider'].nunique()}")
    print(f"Accounts         : {df['account_id'].nunique()}")
    print(f"Services         : {df['service'].nunique()}")
    print(f"Regions          : {df['region'].nunique()}")
    print(f"Teams            : {df['team'].nunique()}")
    print(f"Environments     : {df['environment'].nunique()}")
    print(f"Total cost       : ${df['cost'].sum():,.2f}")

    print("\nProvider distribution:")

    print(
        df["provider"]
        .value_counts()
        .to_string()
    )

    print("\nTop 5 services by cost:")

    service_cost = (
        df.groupby("service")["cost"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )

    print(service_cost.to_string())


# --------------------------------------------------
# Main pipeline
# --------------------------------------------------

def main() -> None:

    print("Starting billing data ingestion...\n")

    df = load_billing_data(INPUT_FILE)

    validate_schema(df)

    validate_data_quality(df)

    print_summary(df)

    print("\nBilling data ingestion completed successfully.")


if __name__ == "__main__":
    main()