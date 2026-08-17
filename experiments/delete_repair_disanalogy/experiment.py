#!/usr/bin/env python3
"""Run the Paper D shared-diagram disanalogy probe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from experiments.delete_repair_disanalogy.core import evaluate_benchmark
else:
    from .core import evaluate_benchmark

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "results" / "delete_repair_disanalogy_summary.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = evaluate_benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    ranking = payload["ranking"]
    lorentz = payload["lorentz_lamport"]
    print(
        json.dumps(
            {
                "status": payload["status"],
                "verdict": ranking["verdict"],
                "n_diamond": lorentz["n_diamond"],
                "distinct_s2": lorentz["distinct_s2"],
                "pe_quotient_fails": ranking["pe_quotient_fails"],
                "pe_typed_works": ranking["pe_typed_works"],
            },
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
