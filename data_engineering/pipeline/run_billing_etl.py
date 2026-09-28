from pathlib import Path
import sys
import time

import pandas as pd


# --------------------------------------------------
# Project root
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(PROJECT_ROOT))


# --------------------------------------------------
# Import pipeline functions
# --------------------------------------------------
from data_engineering.utils.logger import get_logger

from data_engineering.ingestion.load_billing_data import (
    load_billing_data,
    validate_schema,
    validate_data_quality,
)

from data_engineering.cleaning.clean_billing_data import (
    clean_text_columns,
    convert_data_types,
    remove_duplicates,
    identify_invalid_records,
)

from data_engineering.transformation.transform_billing_data import (
    add_date_attributes,
    add_cost_metrics,
    add_normalized_dimensions,
    add_cost_category,
)


# --------------------------------------------------
# File paths
# --------------------------------------------------

RAW_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw_billing_data.csv"
)

CLEANED_FILE = (
    PROJECT_ROOT
    / "data"
    / "cleaned_billing_data.csv"
)

INVALID_FILE = (
    PROJECT_ROOT
    / "data"
    / "cleaning_report.csv"
)

TRANSFORMED_FILE = (
    PROJECT_ROOT
    / "data"
    / "transformed_billing_data.csv"
)


# --------------------------------------------------
# Logging
# --------------------------------------------------

logger = get_logger()


def log(message: str) -> None:
    logger.info(message)


# --------------------------------------------------
# Main pipeline
# --------------------------------------------------

def run_pipeline() -> None:

    start_time = time.perf_counter()

    log("Starting billing ETL pipeline")

    # ==================================================
    # EXTRACT
    # ==================================================

    log("Stage 1/4 - Extract")

    df = load_billing_data(RAW_FILE)

    records_read = len(df)

    # ==================================================
    # VALIDATE
    # ==================================================

    log("Stage 2/4 - Validate")

    validate_schema(df)
    validate_data_quality(df)

    # ==================================================
    # CLEAN
    # ==================================================

    log("Stage 3/4 - Clean")

    original_count = len(df)

    df = convert_data_types(df)

    df = clean_text_columns(df)

    df, duplicates_removed = remove_duplicates(df)

    cleaned_df, invalid_df = identify_invalid_records(df)

    cleaned_df.to_csv(
        CLEANED_FILE,
        index=False
    )

    invalid_df.to_csv(
        INVALID_FILE,
        index=False
    )

    # ==================================================
    # TRANSFORM
    # ==================================================

    log("Stage 4/4 - Transform")

    transformed_df = cleaned_df.copy()

    transformed_df = add_date_attributes(
        transformed_df
    )

    transformed_df = add_cost_metrics(
        transformed_df
    )

    transformed_df = add_normalized_dimensions(
        transformed_df
    )

    transformed_df = add_cost_category(
        transformed_df
    )

    transformed_df.to_csv(
        TRANSFORMED_FILE,
        index=False
    )

    # ==================================================
    # Metrics
    # ==================================================

    execution_time = (
        time.perf_counter() - start_time
    )

    logger.info(
    "ETL completed successfully | "
    f"records_read={records_read} | "
    f"duplicates_removed={duplicates_removed} | "
    f"invalid_records={len(invalid_df)} | "
    f"valid_records={len(cleaned_df)} | "
    f"transformed_records={len(transformed_df)} | "
    f"execution_time={execution_time:.3f}s"
)


# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":
    run_pipeline()