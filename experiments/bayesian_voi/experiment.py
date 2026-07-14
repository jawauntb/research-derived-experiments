#!/usr/bin/env python3
"""Run the exact deterministic Bayesian VOI benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in (None, ""):  # Support the README's direct command.
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from experiments.bayesian_voi.core import evaluate_benchmark
else:  # ``python -m experiments.bayesian_voi.experiment``.
    from .core import evaluate_benchmark


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "results" / "bayesian_voi_summary.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = evaluate_benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": payload["status"], "scenarios": len(payload["scenarios"])}, sort_keys=True))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
