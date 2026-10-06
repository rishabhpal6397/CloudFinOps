"""
CloudFinOps – ETL: Load stage
=============================

Phase 2 writes processed data to disk. Phase 3 will extend this module with
a `load_to_mysql()` function that inserts the cleaned records into the star
schema.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def save_processed(df: pd.DataFrame, output_dir: str | Path) -> dict[str, Path]:
    """
    Persist the processed DataFrame as CSV.

    Returns a mapping of artifact name → path.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "billing_data_clean.csv"
    df.to_csv(csv_path, index=False)
    logger.info("Wrote processed CSV: %s (%s rows)", csv_path, f"{len(df):,}")

    return {"processed_csv": csv_path}


def save_stats(
    stats: dict,
    output_dir: str | Path,
    name: str = "cleaning_stats.json",
) -> Path:
    """Persist cleaning statistics as JSON."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / name
    with path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, default=str)
    logger.info("Wrote cleaning stats: %s", path)
    return path