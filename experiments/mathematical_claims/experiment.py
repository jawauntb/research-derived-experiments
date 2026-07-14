#!/usr/bin/env python3
"""Run the deterministic M-201 assumption-example suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in (None, ""):  # Support the README's direct command.
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from experiments.mathematical_claims.core import evaluate_all
else:  # ``python -m experiments.mathematical_claims.experiment``.
    from .core import evaluate_all


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "results" / "mathematical_claims_summary.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    results = evaluate_all()
    payload = {
        "experiment_id": "mathematical_claims",
        "status": "pass" if all(
            result["example_satisfies_assumption"] and result["failure_case_detected"]
            for result in results
        ) else "fail",
        "n_assumptions": len(results),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {"status": payload["status"], "n_assumptions": payload["n_assumptions"]},
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
