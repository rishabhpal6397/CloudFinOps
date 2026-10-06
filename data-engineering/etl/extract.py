"""
CloudFinOps – ETL: Extract stage
================================

Reads raw billing data from CSV or Excel files.

The extract stage intentionally does NOT validate or transform data — its only
job is to load the file into a pandas DataFrame. Structural issues (missing
columns, wrong types) are the responsibility of the validate stage.

Supported formats: .csv, .xlsx, .xls
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def extract(input_path: str | Path) -> pd.DataFrame:
    """
    Read a billing data file into a DataFrame.

    Parameters
    ----------
    input_path : str | Path
        Path to a .csv, .xlsx, or .xls file.

    Returns
    -------
    pd.DataFrame
        The raw data as read from the file, unchanged.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file extension is not supported.
    """
    path = Path(input_path)

    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file extension '{suffix}'. "
            f"Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    logger.info("Extracting from %s", path)

    if suffix == ".csv":
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)

    logger.info("Extracted %s rows x %s columns", f"{len(df):,}", df.shape[1])
    return df