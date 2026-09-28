from pathlib import Path

import pandas as pd


# --------------------------------------------------
# Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw_billing_data.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "cleaned_billing_data.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "data"
    / "cleaning_report.csv"
)


# --------------------------------------------------
# Columns
# --------------------------------------------------

TEXT_COLUMNS = [
    "provider",
    "account_id",
    "service",
    "region",
    "resource_id",
    "resource_name",
    "team",
    "environment",
    "usage_unit",
    "currency",
]

NUMERIC_COLUMNS = [
    "usage_quantity",
    "cost",
]


# --------------------------------------------------
# Load
# --------------------------------------------------

def load_data(input_file: Path) -> pd.DataFrame:
    """Load billing data from a CSV file."""

    if not input_file.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_file}"
        )

    df = pd.read_csv(input_file)

    print(f"Input file    : {input_file}")
    print(f"Input records : {len(df):,}")

    return df


# --------------------------------------------------
# Clean text
# --------------------------------------------------

def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove unnecessary whitespace from text columns."""

    for column in TEXT_COLUMNS:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    return df


# --------------------------------------------------
# Convert data types
# --------------------------------------------------

def convert_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """Convert columns to appropriate data types."""

    df["billing_date"] = pd.to_datetime(
        df["billing_date"],
        errors="coerce"
    )

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    return df


# --------------------------------------------------
# Duplicate detection
# --------------------------------------------------

def remove_duplicates(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, int]:
    """Remove exact duplicate records."""

    before = len(df)

    df = df.drop_duplicates().copy()

    removed = before - len(df)

    return df, removed


# --------------------------------------------------
# Invalid record detection
# --------------------------------------------------

def identify_invalid_records(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Separate valid and invalid records.

    Each invalid record receives an 'error_reason'
    describing why it was rejected.
    """

    invalid_conditions = pd.DataFrame(
        index=df.index
    )

    invalid_conditions["invalid_date"] = (
        df["billing_date"].isna()
    )

    invalid_conditions["missing_provider"] = (
        df["provider"].isna()
    )

    invalid_conditions["missing_resource_id"] = (
        df["resource_id"].isna()
        | df["resource_id"].astype("string").str.strip().eq("")
    )

    invalid_conditions["invalid_usage"] = (
        df["usage_quantity"].isna()
        | (df["usage_quantity"] < 0)
    )

    invalid_conditions["invalid_cost"] = (
        df["cost"].isna()
        | (df["cost"] < 0)
    )

    invalid_conditions["invalid_currency"] = (
        ~df["currency"].isin(["USD"])
    )

    invalid_mask = invalid_conditions.any(axis=1)

    invalid_records = df[invalid_mask].copy()
    valid_records = df[~invalid_mask].copy()

    # Build a readable reason for each invalid record
    def build_reason(row):
        reasons = [
            column
            for column, is_invalid in row.items()
            if is_invalid
        ]

        return ", ".join(reasons)

    if not invalid_records.empty:
        invalid_records["error_reason"] = (
            invalid_conditions.loc[
                invalid_records.index
            ]
            .apply(build_reason, axis=1)
        )

    return valid_records, invalid_records



def print_cleaning_statistics(
    original_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    invalid_df: pd.DataFrame,
    duplicates_removed: int,
) -> None:
    """Print detailed cleaning statistics."""

    print("\n========== CLEANING STATISTICS ==========")

    print(
        f"Original records   : {len(original_df):,}"
    )

    print(
        f"Duplicates removed : {duplicates_removed:,}"
    )

    print(
        f"Invalid records    : {len(invalid_df):,}"
    )

    print(
        f"Valid records      : {len(cleaned_df):,}"
    )

    print(
        f"Records accounted  : "
        f"{len(cleaned_df) + len(invalid_df) + duplicates_removed:,}"
    )

    if not invalid_df.empty:

        print("\nInvalid records by reason:")

        reasons = (
            invalid_df["error_reason"]
            .str.split(", ")
            .explode()
            .value_counts()
        )

        print(
            reasons.to_string()
        )
# --------------------------------------------------
# Main cleaning pipeline
# --------------------------------------------------

def clean_billing_data(
    input_file: Path,
    output_file: Path,
    report_file: Path,
) -> None:

    print("\nStarting billing data cleaning...\n")

    # Extract
    df = load_data(input_file)

    original_count = len(df)

    # Transform data types
    df = convert_data_types(df)

    # Clean text
    df = clean_text_columns(df)

    # Remove exact duplicates
    df, duplicates_removed = remove_duplicates(df)

    # Identify invalid records
    valid_df, invalid_df = identify_invalid_records(df)

    # Save valid records
    valid_df.to_csv(
        output_file,
        index=False
    )

    # Save invalid records
    invalid_df.to_csv(
        report_file,
        index=False
    )

    # --------------------------------------------------
    # Report
    # --------------------------------------------------

    print_cleaning_statistics(
    original_df=df,
    cleaned_df=valid_df,
    invalid_df=invalid_df,
    duplicates_removed=duplicates_removed,
    )

    print(f"\nCleaned data         : {output_file}")
    print(f"Invalid record report: {report_file}")

    print("\nCleaning completed.")


# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":

    clean_billing_data(
        input_file=INPUT_FILE,
        output_file=OUTPUT_FILE,
        report_file=REPORT_FILE,
    )