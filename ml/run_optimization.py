"""
CloudFinOps – Top-level optimization runner
============================================

Run from the repo root:

    python ml/run_optimization.py
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ml.common import configure_logging        # noqa: E402
from ml.optimization import recommender        # noqa: E402


def _cli() -> int:
    p = argparse.ArgumentParser(description="CloudFinOps optimization recommendations")
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args()
    configure_logging(args.log_level)

    try:
        summary = recommender.run()
    except Exception as exc:
        logging.getLogger("run_optimization").exception("Failed: %s", exc)
        return 1

    print()
    print("=" * 60)
    print("Optimization summary")
    print("=" * 60)
    print(f"  Total recommendations:  {summary['total_written']}")
    print(f"  Estimated monthly saving: ${summary['total_estimated_monthly_saving']:,.2f}")
    print(f"  By category: {summary['by_category']}")
    print(f"  By priority: {summary['by_priority']}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(_cli())