from pathlib import Path
import sys

import pandas as pd


# --------------------------------------------------
# Add project root to Python import path
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(PROJECT_ROOT))


from data_engineering.ingestion.load_billing_data import (
    INPUT_FILE,
    validate_data_quality,
    validate_schema,
)


# --------------------------------------------------
# Test file
# --------------------------------------------------

TEST_FILE = (
    PROJECT_ROOT
    / "data"
    / "test_invalid_billing_data.csv"
)


# --------------------------------------------------
# Create invalid dataset
# --------------------------------------------------

def create_invalid_dataset() -> pd.DataFrame:
    """
    Create a corrupted copy of the original billing dataset.

    The original dataset is never modified.
    """

    df = pd.read_csv(INPUT_FILE)

    # 1. Negative cost
    df.loc[0, "cost"] = -100

    # 2. Negative usage
    df.loc[1, "usage_quantity"] = -50

    # 3. Missing resource ID
    df.loc[2, "resource_id"] = None

    # 4. Invalid date
    df.loc[3, "billing_date"] = "INVALID_DATE"

    # 5. Invalid currency
    df.loc[4, "currency"] = "EUR"

    # 6. Duplicate record
    duplicate = df.iloc[[5]].copy()

    df = pd.concat(
        [df, duplicate],
        ignore_index=True
    )

    return df


# --------------------------------------------------
# Main
# --------------------------------------------------

def main() -> None:

    print("Creating invalid test dataset...\n")

    df = create_invalid_dataset()

    df.to_csv(
        TEST_FILE,
        index=False
    )

    print(f"Test file created : {TEST_FILE}")
    print(f"Test records      : {len(df):,}")

    print("\nRunning schema validation...")

    try:

        validate_schema(df)

        print("Schema test : PASSED")

    except ValueError as error:

        print("Schema test : FAILED")
        print(error)

    print("\nRunning data-quality validation...")

    try:

        validate_data_quality(df)

        print(
            "ERROR: Invalid dataset was accepted."
        )

    except ValueError as error:

        print("Data-quality test : PASSED")

        print(
            "\nValidator correctly detected invalid data:"
        )

        print(error)

    print("\nValidation testing completed.")


if __name__ == "__main__":
    main()