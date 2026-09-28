from pathlib import Path

from clean_billing_data import clean_billing_data


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "test_invalid_billing_data.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "test_cleaned_billing_data.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "data"
    / "test_cleaning_report.csv"
)


def main() -> None:

    print("Testing cleaner with intentionally invalid data...\n")

    clean_billing_data(
        input_file=INPUT_FILE,
        output_file=OUTPUT_FILE,
        report_file=REPORT_FILE,
    )


if __name__ == "__main__":
    main()