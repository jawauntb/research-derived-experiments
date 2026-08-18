#!/usr/bin/env python3
"""Run the door-2 (q, K)-reduction audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from experiments.delete_repair_reduction.core import evaluate_benchmark
else:
    from .core import evaluate_benchmark

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "results" / "delete_repair_reduction_summary.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = evaluate_benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    ranking = payload["ranking"]
    print(
        json.dumps(
            {
                "status": payload["status"],
                "verdict": ranking["verdict"],
                "screens_all_invariant": ranking["screens_all_invariant"],
                "access_changed": ranking["access_changed"],
                "min_size_x4": (
                    f"base {ranking['min_size_x4_base']}, "
                    f"ext {ranking['min_size_x4_ext']}"
                ),
                "mass_x4": (
                    f"base {ranking['mass_x4_base']}, ext {ranking['mass_x4_ext']}"
                ),
                "round_trip_identity": ranking["round_trip_identity"],
            },
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
