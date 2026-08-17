#!/usr/bin/env python3
"""Run the EML constant-grammar fiber-spectrum enumerator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from experiments.eml_fiber_spectrum.core import evaluate_benchmark
else:
    from .core import evaluate_benchmark


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "results" / "eml_fiber_spectrum_summary.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = evaluate_benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    closed = payload["closed_spectrum"]
    optional = payload["optional_gates"]["EFS_CROSS_SIZE_COLLISION"]
    print(
        json.dumps(
            {
                "status": payload["status"],
                "gates": payload["gates"],
                "n_trees": payload["n_trees"],
                "n_numerical_fibers": closed["n_numerical_fibers"],
                "n_undefined": closed["n_undefined"],
                "cross_size_status": optional["status"],
                "us4_prime": "untested",
            },
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
