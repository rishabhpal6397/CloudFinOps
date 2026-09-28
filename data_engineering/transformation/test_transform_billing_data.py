from pathlib import Path

import pandas as pd


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


EXPECTED_NEW_COLUMNS = [
    "year",
    "month",
    "month_name",
    "quarter",
    "day_of_month",
    "day_of_week",
    "is_weekend",
    "cost_per_unit",
    "provider_key",
    "service_key",
    "environment_key",
    "team_key",
    "cost_category",
]


def validate_record_count(
    input_df: pd.DataFrame,
    output_df: pd.DataFrame,
) -> None:

    if len(input_df) != len(output_df):
        raise ValueError(
            "Record count changed during transformation."
        )

    print("Record count validation : PASSED")


def validate_columns(
    output_df: pd.DataFrame,
) -> None:

    missing_columns = [
        column
        for column in EXPECTED_NEW_COLUMNS
        if column not in output_df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing transformed columns: {missing_columns}"
        )

    print("Column validation       : PASSED")


def validate_dates(
    output_df: pd.DataFrame,
) -> None:

    dates = pd.to_datetime(
        output_df["billing_date"],
        errors="coerce"
    )

    if dates.isna().any():
        raise ValueError(
            "Invalid dates found."
        )

    invalid_year = (
        output_df["year"]
        != dates.dt.year
    ).any()

    invalid_month = (
        output_df["month"]
        != dates.dt.month
    ).any()

    if invalid_year or invalid_month:
        raise ValueError(
            "Derived date attributes are incorrect."
        )

    print("Date validation         : PASSED")


def validate_cost_metrics(
    output_df: pd.DataFrame,
) -> None:

    if output_df["cost_per_unit"].isna().any():
        raise ValueError(
            "Null cost_per_unit values found."
        )

    if (
        output_df["cost_per_unit"] < 0
    ).any():
        raise ValueError(
            "Negative cost_per_unit values found."
        )

    print("Cost metric validation  : PASSED")


def validate_categories(
    output_df: pd.DataFrame,
) -> None:

    if output_df["cost_category"].isna().any():
        raise ValueError(
            "Missing cost categories found."
        )

    if (
        output_df["cost_category"]
        .eq("Other")
        .any()
    ):
        raise ValueError(
            "Unmapped services found."
        )

    print("Category validation     : PASSED")


def validate_normalized_keys(
    output_df: pd.DataFrame,
) -> None:

    columns = [
        "provider_key",
        "service_key",
        "environment_key",
        "team_key",
    ]

    for column in columns:

        if output_df[column].isna().any():
            raise ValueError(
                f"Null values found in {column}."
            )

        if (
            output_df[column]
            .astype(str)
            .str.strip()
            .eq("")
            .any()
        ):
            raise ValueError(
                f"Empty values found in {column}."
            )

    print("Normalized keys validation : PASSED")


def main() -> None:

    print(
        "Starting transformation validation...\n"
    )

    input_df = pd.read_csv(INPUT_FILE)

    output_df = pd.read_csv(OUTPUT_FILE)

    print(
        f"Input records  : {len(input_df):,}"
    )

    print(
        f"Output records : {len(output_df):,}"
    )

    print()

    validate_record_count(
        input_df,
        output_df
    )

    validate_columns(
        output_df
    )

    validate_dates(
        output_df
    )

    validate_cost_metrics(
        output_df
    )

    validate_categories(
        output_df
    )

    validate_normalized_keys(
        output_df
    )

    print(
        "\nTransformation validation : PASSED"
    )


if __name__ == "__main__":
    main()