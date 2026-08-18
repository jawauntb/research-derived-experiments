#!/usr/bin/env python3
"""Run Gate 2's silence gate at the kernel: the zero-leakage instrument."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from experiments.silent_substitution.core import evaluate_benchmark
else:
    from .core import evaluate_benchmark

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "results" / "silent_substitution_summary.json"


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
                "record_constant_both_arms": ranking["record_constant_both_arms"],
                "misaligned_reward_rises": ranking["misaligned_reward_rises"],
                "misaligned_principal_falls": ranking["misaligned_principal_falls"],
                "aligned_principal_rises": ranking["aligned_principal_rises"],
                "limit_mass": ranking["limit_mass"],
            },
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
