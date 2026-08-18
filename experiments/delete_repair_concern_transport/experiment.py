#!/usr/bin/env python3
"""Run the door-3 concern-transport probe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from experiments.delete_repair_concern_transport.core import evaluate_benchmark
else:
    from .core import evaluate_benchmark

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "results" / "delete_repair_concern_transport_summary.json"


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
                "base_boundary": ranking["base_boundary"],
                "ext_boundary": ranking["ext_boundary"],
                "boundary_menu_relative": ranking["boundary_menu_relative"],
                "reversal_natural_both_menus": ranking["reversal_natural_both_menus"],
                "candidates": (
                    f"base {len(ranking['base_candidates'])}, "
                    f"ext {len(ranking['ext_candidates'])}"
                ),
            },
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
