#!/usr/bin/env python3
"""Run the dial-nestedness probe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from experiments.dial_nestedness.core import evaluate_benchmark
else:
    from .core import evaluate_benchmark

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "results" / "dial_nestedness_summary.json"


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
                "rates": ranking["rates"],
                "rate_monotone": ranking["rate_monotone"],
                "all_nested": ranking["all_nested"],
                "chain_exists": ranking["chain_exists"],
            },
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
