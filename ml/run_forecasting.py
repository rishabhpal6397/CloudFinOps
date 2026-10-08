"""
CloudFinOps – Top-level forecasting runner
==========================================

Run from the repo root:

    python ml/run_forecasting.py
    python ml/run_forecasting.py --no-backtest
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
from ml.forecasting import forecaster          # noqa: E402


def _cli() -> int:
    p = argparse.ArgumentParser(description="CloudFinOps forecasting")
    p.add_argument("--no-backtest", action="store_true",
                   help="Skip train/test evaluation (faster)")
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args()

    configure_logging(args.log_level)

    try:
        summary = forecaster.run(backtest=not args.no_backtest)
    except Exception as exc:
        logging.getLogger("run_forecasting").exception("Failed: %s", exc)
        return 1

    print()
    print("=" * 60)
    print("Forecasting summary")
    print("=" * 60)
    for k, v in summary.items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for kk, vv in v.items():
                if isinstance(vv, dict):
                    print(f"    {kk}:")
                    for kkk, vvv in vv.items():
                        print(f"      {kkk}: {vvv}")
                else:
                    print(f"    {kk}: {vv}")
        else:
            print(f"  {k}: {v}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(_cli())