#!/usr/bin/env python3
"""Run the door-1 menu-variation probe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from experiments.delete_repair_menu_blind.core import evaluate_benchmark
else:
    from .core import evaluate_benchmark

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "results" / "delete_repair_menu_blind_summary.json"


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
                "n_flips": ranking["n_flips"],
                "flip_case_ids": ranking["flip_case_ids"],
                "cheap_hits": (
                    f"base {ranking['cheap_hits_base']}/17, "
                    f"ext {ranking['cheap_hits_ext']}/17"
                ),
                "cheap_collisions": (
                    f"base {ranking['cheap_collisions_base']}, "
                    f"ext {ranking['cheap_collisions_ext']}"
                ),
                "screen": f"{ranking['screen_hits']}/{ranking['screen_n']}",
                "relabel_action_natural": ranking["relabel_action_natural"],
                "tie_break_screen_natural": ranking["tie_break_screen_natural"],
            },
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
