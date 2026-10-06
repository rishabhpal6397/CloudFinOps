"""
CloudFinOps – Validation report writer
======================================

Persists a ValidationReport to CSV (row-level issues) and JSON (summary).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from etl.validate import ValidationReport

logger = logging.getLogger(__name__)


def write_report(
    report: ValidationReport,
    output_dir: str | Path,
    prefix: str = "validation_report",
) -> dict[str, Path]:
    """Write the report to CSV + JSON. Returns artifact paths."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Row-level issues (capped by MAX_ISSUE_RECORDS in validate.py)
    issues_df = report.issues_dataframe()
    csv_path = output_dir / f"{prefix}.csv"
    issues_df.to_csv(csv_path, index=False)

    # Summary JSON — always accurate totals, independent of the cap
    summary = {
        "total_rows": report.total_rows,
        "total_columns": report.total_columns,
        "missing_columns": report.missing_columns,
        "extra_columns": report.extra_columns,
        "error_count": report.error_count,
        "warning_count": report.warning_count,
        "issue_counts_by_check": report.counts,
        "structurally_valid": report.is_structurally_valid,
    }
    json_path = output_dir / f"{prefix}_summary.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info("Wrote validation report: %s, %s", csv_path, json_path)
    return {"issues_csv": csv_path, "summary_json": json_path}