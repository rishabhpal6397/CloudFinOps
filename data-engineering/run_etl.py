"""
CloudFinOps – Top-level ETL runner
==================================

Convenience wrapper so the pipeline can be run from the repo root:

    python data-engineering/run_etl.py --input data/raw/synthetic_billing_data.csv
"""

import sys
from pathlib import Path

# Make `data-engineering/` importable when run from the repo root
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from etl.pipeline import _cli  # noqa: E402

if __name__ == "__main__":
    sys.exit(_cli())