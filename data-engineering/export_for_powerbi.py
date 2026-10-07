"""
CloudFinOps – Export all reporting views to CSV for Power BI
============================================================

Power BI Desktop cannot run inside the Codespaces Linux container. This script
exports every reporting view to CSV so a Power BI user on Windows can:

  1. Connect to the CSVs directly (Power BI Desktop → Get Data → Folder/Web)
  2. Publish them via GitHub (raw URLs) and use Power BI Service dataflows
  3. Refresh from CSV on demand

Usage (from repo root):
    python data-engineering/export_for_powerbi.py

Output:
    data/powerbi/<view_name>.csv   (one file per view)
    data/powerbi/_manifest.json    (row counts + timestamps for verification)
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from etl.db import get_engine, test_connection

logger = logging.getLogger("export_powerbi")

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "powerbi"

# Views to export (all 20). Add more here if new views are created.
VIEWS = [
    # Trends
    "vw_daily_cost",
    "vw_monthly_cost",
    "vw_provider_monthly",
    "vw_service_monthly",
    "vw_team_monthly",
    "vw_environment_monthly",
    # Dimension totals
    "vw_cost_by_provider",
    "vw_cost_by_service",
    "vw_cost_by_team",
    "vw_cost_by_environment",
    "vw_cost_by_region",
    "vw_cost_by_account",
    "vw_cost_by_resource",
    "vw_cost_by_dimension_long",
    # Detail
    "vw_cost_detail",
    # KPI
    "vw_kpi_summary",
    # FinOps (may be empty until Phase 6+)
    "vw_anomalies",
    "vw_forecasts",
    "vw_optimization_savings",
    "vw_budget_vs_actual",
]


def export_all(output_dir: Path = OUTPUT_DIR) -> dict:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    engine = get_engine()
    if not test_connection(engine):
        raise RuntimeError("Cannot connect to MySQL.")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "views": {},
    }

    for view in VIEWS:
        try:
            with engine.connect() as conn:
                df = pd.read_sql(text(f"SELECT * FROM `{view}`"), conn)
        except Exception as exc:
            logger.warning("Skipping %s: %s", view, exc)
            manifest["views"][view] = {"error": str(exc)}
            continue

        csv_path = output_dir / f"{view}.csv"
        df.to_csv(csv_path, index=False)
        size_kb = csv_path.stat().st_size / 1024
        logger.info(
            "  ✔ %-30s %8s rows  %7.1f KB",
            view, f"{len(df):,}", size_kb,
        )
        manifest["views"][view] = {
            "rows": int(len(df)),
            "columns": list(df.columns),
            "size_kb": round(size_kb, 1),
        }

    manifest_path = output_dir / "_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)
    logger.info("Wrote manifest: %s", manifest_path)

    total_rows = sum(v.get("rows", 0) for v in manifest["views"].values())
    logger.info(
        "✔ Exported %d views, %s total rows to %s",
        len(manifest["views"]), f"{total_rows:,}", output_dir,
    )
    return manifest


if __name__ == "__main__":
    try:
        export_all()
    except Exception as exc:
        logging.getLogger("export_powerbi").exception("Export failed: %s", exc)
        sys.exit(1)