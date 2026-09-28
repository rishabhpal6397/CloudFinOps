import sys
import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


from data_engineering.ingestion.load_billing_data import (
    REQUIRED_COLUMNS,
    validate_schema,
    validate_data_quality,
)

from data_engineering.cleaning.clean_billing_data import (
    remove_duplicates,
    identify_invalid_records,
)

from data_engineering.transformation.transform_billing_data import (
    add_date_attributes,
    add_cost_metrics,
    add_normalized_dimensions,
    add_cost_category,
)


class TestBillingETL(unittest.TestCase):

    def setUp(self):

        self.df = pd.DataFrame({
            "billing_date": [
                "2026-01-01",
                "2026-01-02",
            ],
            "provider": [
                "AWS",
                "Azure",
            ],
            "account_id": [
                "aws-prod-001",
                "azure-prod-001",
            ],
            "service": [
                "EC2",
                "Virtual Machines",
            ],
            "region": [
                "ap-south-1",
                "Central India",
            ],
            "resource_id": [
                "aws-ec2-000001",
                "azure-vm-000001",
            ],
            "resource_name": [
                "test-resource-1",
                "test-resource-2",
            ],
            "team": [
                "DevOps",
                "Data Engineering",
            ],
            "environment": [
                "Production",
                "Development",
            ],
            "usage_quantity": [
                100.0,
                200.0,
            ],
            "usage_unit": [
                "hours",
                "hours",
            ],
            "cost": [
                10.0,
                20.0,
            ],
            "currency": [
                "USD",
                "USD",
            ],
        })

    # ----------------------------------------------
    # Schema
    # ----------------------------------------------

    def test_required_columns_exist(self):

        for column in REQUIRED_COLUMNS:
            self.assertIn(
                column,
                self.df.columns
            )

        validate_schema(self.df)

    # ----------------------------------------------
    # Data quality
    # ----------------------------------------------

    def test_valid_data_passes(self):

        validate_data_quality(self.df)

    def test_negative_cost_detected(self):

        df = self.df.copy()

        df.loc[0, "cost"] = -10

        with self.assertRaises(ValueError):
            validate_data_quality(df)

    # ----------------------------------------------
    # Duplicate handling
    # ----------------------------------------------

    def test_duplicate_removal(self):

        duplicate_df = pd.concat(
            [
                self.df,
                self.df.iloc[[0]]
            ],
            ignore_index=True
        )

        cleaned_df, removed = remove_duplicates(
            duplicate_df
        )

        self.assertEqual(
            removed,
            1
        )

        self.assertEqual(
            len(cleaned_df),
            2
        )

    # ----------------------------------------------
    # Invalid record detection
    # ----------------------------------------------

    def test_invalid_record_detection(self):

        df = self.df.copy()

        df.loc[0, "cost"] = -10

        valid_df, invalid_df = (
            identify_invalid_records(df)
        )

        self.assertEqual(
            len(valid_df),
            1
        )

        self.assertEqual(
            len(invalid_df),
            1
        )

        self.assertIn(
            "invalid_cost",
            invalid_df.iloc[0]["error_reason"]
        )

    # ----------------------------------------------
    # Transformation
    # ----------------------------------------------

    def test_date_attributes(self):

        df = add_date_attributes(
            self.df.copy()
        )

        self.assertEqual(
            df.loc[0, "year"],
            2026
        )

        self.assertEqual(
            df.loc[0, "month"],
            1
        )

        self.assertEqual(
            df.loc[0, "quarter"],
            "Q1"
        )

    def test_cost_metrics(self):

        df = add_cost_metrics(
            self.df.copy()
        )

        self.assertAlmostEqual(
            df.loc[0, "cost_per_unit"],
            0.1
        )

    def test_normalized_dimensions(self):

        df = add_normalized_dimensions(
            self.df.copy()
        )

        self.assertEqual(
            df.loc[0, "provider_key"],
            "AWS"
        )

        self.assertEqual(
            df.loc[0, "service_key"],
            "ec2"
        )

        self.assertEqual(
            df.loc[0, "team_key"],
            "devops"
        )

    def test_cost_categories(self):

        df = add_cost_category(
            self.df.copy()
        )

        self.assertEqual(
            df.loc[0, "cost_category"],
            "Compute"
        )

        self.assertEqual(
            df.loc[1, "cost_category"],
            "Compute"
        )


if __name__ == "__main__":
    unittest.main()