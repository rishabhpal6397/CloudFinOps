"""
CloudFinOps – Top-level anomaly detection runner
================================================

Run from the repo root:

    python ml/run_anomaly_detection.py
    python ml/run_anomaly_detection.py --window 30 --z-threshold 3.0 --contamination 0.02
    python ml/run_anomaly_detection.py --include-resources --top-n-resources 100
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Make repo root importable so `ml.*` resolves
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ml.common import configure_logging       # noqa: E402
from ml.anomaly_detection import detector     # noqa: E402


def _cli() -> int:
    p = argparse.ArgumentParser(description="CloudFinOps anomaly detection")
    p.add_argument("--window", type=int, default=30, help="Rolling window (days)")
    p.add_argument("--z-threshold", type=float, default=3.0, help="Z-score cutoff")
    p.add_argument("--contamination", type=float, default=0.02,
                   help="IsolationForest expected anomaly fraction")
    p.add_argument("--include-resources", action="store_true",
                   help="Also run per-resource statistical detection")
    p.add_argument("--top-n-resources", type=int, default=100,
                   help="How many top resources to include")
    p.add_argument("--log-level", default="INFO")
    args = p.parse_args()

    configure_logging(args.log_level)

    try:
        summary = detector.run(
            window=args.window,
            z_threshold=args.z_threshold,
            contamination=args.contamination,
            include_resources=args.include_resources,
            top_n_resources=args.top_n_resources,
        )
    except Exception as exc:
        logging.getLogger("run_anomaly_detection").exception("Failed: %s", exc)
        return 1

    print()
    print("=" * 60)
    print("Anomaly detection summary")
    print("=" * 60)
    for section, data in summary.items():
        print(f"  {section}:")
        for k, v in data.items():
            print(f"    {k}: {v}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(_cli())