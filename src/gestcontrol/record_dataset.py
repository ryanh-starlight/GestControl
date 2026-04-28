"""Training-data recorder for the future ML classifier upgrade.

Hold a gesture, press the labelled key, and 21-landmark snapshots are
appended to data/samples.csv.  This is NOT wired into the v1 runtime.

Usage (future):
    python -m gestcontrol.record_dataset --gesture pinch --frames 200

CSV schema:
    label, lm0_x, lm0_y, lm0_z, lm1_x, ..., lm20_z
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

# TODO: import LandmarkExtractor and implement frame capture loop
# TODO: integrate with scikit-learn training pipeline in record_dataset_ml.py


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Record labeled gesture samples")
    parser.add_argument("--gesture", required=True, help="Label for samples")
    parser.add_argument("--frames",  type=int, default=100)
    parser.add_argument("--output",  default="data/samples.csv")
    parser.add_argument("--source",  choices=["opencv", "spout"], default="opencv")
    args = parser.parse_args()

    print(
        f"[record_dataset] STUB — not yet implemented.\n"
        f"Planned: capture {args.frames} frames labelled '{args.gesture}' "
        f"into {args.output}"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
