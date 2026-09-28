from pathlib import Path

import pandas as pd


CLOUD_FINOPS_COLUMNS = [
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


AWS_REQUIRED_COLUMNS = [
    "line_item_usage_start_date",
    "line_item_usage_account_id",
    "line_item_usage_amount",
    "line_item_unblended_cost",
    "line_item_currency_code",
]


def validate_aws_cur_schema(df: pd.DataFrame) -> None:
    """
    Validate that the AWS CUR input contains
    the minimum columns required by CloudFinOps.
    """

    missing_columns = [
        column
        for column in AWS_REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required AWS CUR columns: {missing_columns}"
        )


def transform_aws_cur_data(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Transform AWS CUR data into the
    CloudFinOps canonical billing schema.
    """

    validate_aws_cur_schema(df)

    result = pd.DataFrame()

    result["billing_date"] = pd.to_datetime(
        df["line_item_usage_start_date"],
        errors="coerce",
        utc=True,
    ).dt.date

    result["provider"] = "AWS"

    result["account_id"] = (
        df["line_item_usage_account_id"]
        .astype("string")
        .str.strip()
    )

    # CUR 2.0 may expose the service/product information
    # differently depending on the selected export columns.
    if "product_product_name" in df.columns:
        result["service"] = (
            df["product_product_name"]
            .astype("string")
            .str.strip()
        )
    elif "line_item_product_code" in df.columns:
        result["service"] = (
            df["line_item_product_code"]
            .astype("string")
            .str.strip()
        )
    else:
        result["service"] = "Unknown"

    if "product_region_code" in df.columns:
        result["region"] = (
            df["product_region_code"]
            .astype("string")
            .str.strip()
        )
    else:
        result["region"] = "Unknown"

    if "line_item_resource_id" in df.columns:
        result["resource_id"] = (
            df["line_item_resource_id"]
            .astype("string")
            .str.strip()
        )
    else:
        result["resource_id"] = pd.NA

    # Until we have a separate resource metadata lookup,
    # use resource_id as the resource name.
    result["resource_name"] = result["resource_id"]

    # These will be populated from AWS tags later.
    result["team"] = "Unknown"
    result["environment"] = "Unknown"

    result["usage_quantity"] = pd.to_numeric(
        df["line_item_usage_amount"],
        errors="coerce",
    )

    if "pricing_unit" in df.columns:
        result["usage_unit"] = (
            df["pricing_unit"]
            .astype("string")
            .str.strip()
        )
    elif "product_pricing_unit" in df.columns:
        result["usage_unit"] = (
            df["product_pricing_unit"]
            .astype("string")
            .str.strip()
        )
    else:
        result["usage_unit"] = "Unknown"

    result["cost"] = pd.to_numeric(
        df["line_item_unblended_cost"],
        errors="coerce",
    )

    result["currency"] = (
        df["line_item_currency_code"]
        .astype("string")
        .str.strip()
    )

    return result[CLOUD_FINOPS_COLUMNS]


def load_aws_cur(
    input_file: str | Path,
) -> pd.DataFrame:
    """
    Load an AWS CUR CSV file and convert it
    into the CloudFinOps canonical schema.
    """

    input_file = Path(input_file)

    if not input_file.exists():
        raise FileNotFoundError(
            f"AWS CUR file not found: {input_file}"
        )

    df = pd.read_csv(
        input_file,
        low_memory=False,
    )

    print(f"AWS CUR file : {input_file}")
    print(f"Input records: {len(df):,}")

    transformed_df = transform_aws_cur_data(df)

    print(
        f"CloudFinOps records: "
        f"{len(transformed_df):,}"
    )

    print(
        f"CloudFinOps columns: "
        f"{len(transformed_df.columns)}"
    )

    return transformed_df