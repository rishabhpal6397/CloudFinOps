"""
CloudFinOps – ETL: Validate stage
=================================

Performs structural and semantic validation on the raw billing DataFrame.

The validator never drops or modifies rows — it only reports problems. The
clean stage is responsible for actually removing or repairing invalid data.

Validation categories
---------------------
1. Structural  – required columns present, extra columns flagged
2. Type        – values parse to expected types (dates, numbers)
3. Domain      – values fall within allowed sets (providers, environments, currency)
4. Quality     – nulls in critical columns, duplicate rows, negative values

Every issue is recorded with a check name, column, row index, message, and
severity. The report is written to disk by validation/validation_report.py.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REQUIRED_COLUMNS = [
    "billing_date", "provider", "account_id", "service", "region",
    "resource_id", "resource_name", "team", "environment",
    "usage_quantity", "usage_unit", "cost", "currency", "tags",
]

CRITICAL_COLUMNS = [
    "billing_date", "provider", "account_id", "service", "region",
    "resource_id", "team", "environment",
    "usage_quantity", "usage_unit", "cost", "currency",
]

VALID_PROVIDERS = {"AWS", "Azure", "GCP"}
VALID_ENVIRONMENTS = {"production", "staging", "development"}
VALID_CURRENCY = "USD"

# Cap individual issue records so a catastrophically bad file doesn't write
# gigabytes of report. Totals are still counted accurately.
MAX_ISSUE_RECORDS = 500


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class ValidationIssue:
    check: str          # e.g. "null_check", "domain_check"
    column: str
    row_index: int      # -1 for file-level issues
    message: str
    severity: str       # "error" | "warning"


@dataclass
class ValidationReport:
    total_rows: int
    total_columns: int
    missing_columns: list[str] = field(default_factory=list)
    extra_columns: list[str] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    @property
    def is_structurally_valid(self) -> bool:
        return not self.missing_columns

    @property
    def is_row_level_valid(self) -> bool:
        return self.error_count == 0

    def add_issue(self, issue: ValidationIssue, count: int = 1) -> None:
        """Record an issue; increment total counter even if we stop storing."""
        self.counts[issue.check] = self.counts.get(issue.check, 0) + count
        if len(self.issues) < MAX_ISSUE_RECORDS * len(REQUIRED_COLUMNS):
            self.issues.append(issue)

    def issues_dataframe(self) -> pd.DataFrame:
        if not self.issues:
            return pd.DataFrame(
                columns=["check", "column", "row_index", "message", "severity"]
            )
        return pd.DataFrame([vars(i) for i in self.issues])

    def summary(self) -> str:
        lines = [
            f"Rows: {self.total_rows:,}   Columns: {self.total_columns}",
            f"Missing columns: {self.missing_columns or 'none'}",
            f"Extra columns  : {self.extra_columns or 'none'}",
            f"Errors  : {self.error_count}",
            f"Warnings: {self.warning_count}",
        ]
        if self.counts:
            lines.append("Issue counts by check:")
            for k, v in sorted(self.counts.items()):
                lines.append(f"  - {k}: {v:,}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def validate(df: pd.DataFrame) -> ValidationReport:
    """Run all validation checks. Returns a ValidationReport."""
    report = ValidationReport(total_rows=len(df), total_columns=df.shape[1])

    _check_columns(df, report)
    if not report.is_structurally_valid:
        logger.warning("Skipping row-level validation — missing required columns")
        return report

    _check_nulls(df, report)
    _check_types(df, report)
    _check_domains(df, report)
    _check_value_ranges(df, report)
    _check_duplicates(df, report)

    return report


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------
def _check_columns(df: pd.DataFrame, report: ValidationReport) -> None:
    cols = set(df.columns)
    report.missing_columns = [c for c in REQUIRED_COLUMNS if c not in cols]
    report.extra_columns = [c for c in df.columns if c not in REQUIRED_COLUMNS]

    for col in report.missing_columns:
        report.add_issue(ValidationIssue(
            check="missing_column",
            column=col,
            row_index=-1,
            message=f"Required column '{col}' is missing",
            severity="error",
        ))


def _check_nulls(df: pd.DataFrame, report: ValidationReport) -> None:
    for col in CRITICAL_COLUMNS:
        count = int(df[col].isna().sum())
        if count == 0:
            continue
        report.add_issue(
            ValidationIssue(
                check="null_check",
                column=col,
                row_index=-1,
                message=f"{count:,} rows have null {col}",
                severity="error",
            ),
            count=count,
        )


def _check_types(df: pd.DataFrame, report: ValidationReport) -> None:
    # billing_date must parse as a date
    parsed = pd.to_datetime(df["billing_date"], errors="coerce")
    bad_dates = parsed.isna() & df["billing_date"].notna()
    count = int(bad_dates.sum())
    if count:
        for idx in df.index[bad_dates][:10]:
            report.add_issue(ValidationIssue(
                check="type_check",
                column="billing_date",
                row_index=int(idx),
                message=f"Unparseable date: {df.at[idx, 'billing_date']!r}",
                severity="error",
            ))
        report.counts["type_check"] = report.counts.get("type_check", 0) + count

    for col in ("cost", "usage_quantity"):
        num = pd.to_numeric(df[col], errors="coerce")
        bad = num.isna() & df[col].notna()
        count = int(bad.sum())
        if count:
            report.add_issue(
                ValidationIssue(
                    check="type_check",
                    column=col,
                    row_index=-1,
                    message=f"{count:,} rows have non-numeric {col}",
                    severity="error",
                ),
                count=count,
            )


def _check_domains(df: pd.DataFrame, report: ValidationReport) -> None:
    checks = [
        ("provider", VALID_PROVIDERS, "error", "unexpected provider"),
        ("environment", VALID_ENVIRONMENTS, "warning", "unexpected environment"),
    ]
    for col, valid_set, severity, label in checks:
        bad = ~df[col].isin(valid_set)
        count = int(bad.sum())
        if count:
            report.add_issue(
                ValidationIssue(
                    check="domain_check",
                    column=col,
                    row_index=-1,
                    message=f"{count:,} rows have {label}",
                    severity=severity,
                ),
                count=count,
            )

    bad = df["currency"] != VALID_CURRENCY
    count = int(bad.sum())
    if count:
        report.add_issue(
            ValidationIssue(
                check="domain_check",
                column="currency",
                row_index=-1,
                message=f"{count:,} rows have currency other than {VALID_CURRENCY}",
                severity="warning",
            ),
            count=count,
        )


def _check_value_ranges(df: pd.DataFrame, report: ValidationReport) -> None:
    cost = pd.to_numeric(df["cost"], errors="coerce")
    count = int((cost < 0).sum())
    if count:
        report.add_issue(
            ValidationIssue(
                check="range_check",
                column="cost",
                row_index=-1,
                message=f"{count:,} rows have negative cost",
                severity="error",
            ),
            count=count,
        )

    usage = pd.to_numeric(df["usage_quantity"], errors="coerce")
    count = int((usage < 0).sum())
    if count:
        report.add_issue(
            ValidationIssue(
                check="range_check",
                column="usage_quantity",
                row_index=-1,
                message=f"{count:,} rows have negative usage_quantity",
                severity="error",
            ),
            count=count,
        )


def _check_duplicates(df: pd.DataFrame, report: ValidationReport) -> None:
    subset = ["billing_date", "provider", "account_id", "resource_id", "service"]
    count = int(df.duplicated(subset=subset, keep=False).sum())
    if count:
        report.add_issue(
            ValidationIssue(
                check="duplicate_check",
                column=",".join(subset),
                row_index=-1,
                message=f"{count:,} rows are duplicates on {subset}",
                severity="warning",
            ),
            count=count,
        )