"""
CloudFinOps – ETL pipeline orchestrator
=======================================

Runs: extract → validate → clean → transform → enrich → save

Usage (from repo root)
----------------------
    python data-engineering/run_etl.py \\
        --input   data/raw/synthetic_billing_data.csv \\
        --output  data/processed \\
        --reports data/reports
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from etl import clean, enrich, extract, load, transform, validate
from validation import validation_report

logger = logging.getLogger("etl.pipeline")


def run_pipeline(
    input_path: str | Path,
    output_dir: str | Path = "data/processed",
    reports_dir: str | Path = "data/reports",
    log_level: str = "INFO",
    load_to_db: bool = False,
) -> dict:
    """Run the full ETL pipeline. Optionally load into MySQL."""
    _configure_logging(log_level)

    started = time.time()
    summary: dict = {"input": str(input_path)}

    # -- 1. Extract ----------------------------------------------------
    raw = extract.extract(input_path)
    summary["rows_extracted"] = len(raw)

    # -- 2. Validate ---------------------------------------------------
    report = validate.validate(raw)
    validation_report.write_report(report, reports_dir)
    summary["validation"] = {
        "errors": report.error_count,
        "warnings": report.warning_count,
        "missing_columns": report.missing_columns,
        "issue_counts": report.counts,
    }
    if not report.is_structurally_valid:
        logger.error("Structural validation failed — aborting pipeline.")
        return summary

    # -- 3. Clean ------------------------------------------------------
    cleaned, clean_stats = clean.clean(raw)
    summary["rows_after_clean"] = len(cleaned)
    summary["cleaning_stats"] = clean_stats

    # -- 4. Transform --------------------------------------------------
    transformed = transform.transform(cleaned)

    # -- 5. Enrich -----------------------------------------------------
    enriched = enrich.enrich(transformed)

    # -- 6. Load: CSV --------------------------------------------------
    artifacts = load.save_processed(enriched, output_dir)
    load.save_stats(clean_stats, output_dir)
    summary["artifacts"] = {k: str(v) for k, v in artifacts.items()}

    # -- 7. Load: MySQL (optional) ------------------------------------
    if load_to_db:
        from etl.db import get_engine, test_connection
        engine = get_engine()
        if not test_connection(engine):
            raise RuntimeError("DB connection test failed")
        db_stats = load.load_to_mysql(
            enriched,
            engine,
            source_file=str(input_path),
            reset_facts=True,
        )
        summary["db_load"] = db_stats

    summary["duration_seconds"] = round(time.time() - started, 2)
    logger.info(
        "Pipeline complete in %.1fs. %s → %s rows.",
        summary["duration_seconds"],
        f"{summary['rows_extracted']:,}",
        f"{summary['rows_after_clean']:,}",
    )
    return summary


def _configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )


def _cli() -> int:
    parser = argparse.ArgumentParser(description="CloudFinOps ETL pipeline")
    parser.add_argument("--input", required=True, help="Path to raw billing file")
    parser.add_argument("--output", default="data/processed", help="Output directory")
    parser.add_argument("--reports", default="data/reports", help="Reports directory")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    parser.add_argument(
        "--load-db", action="store_true",
        help="After saving CSV, load into MySQL star schema",
    )
    args = parser.parse_args()

    try:
        summary = run_pipeline(args.input, args.output, args.reports, args.log_level, load_to_db=args.load_db)
    except Exception as exc:
        logging.getLogger("etl.pipeline").exception("Pipeline failed: %s", exc)
        return 1

    print()
    print("=" * 60)
    print("ETL pipeline summary")
    print("=" * 60)
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(_cli())