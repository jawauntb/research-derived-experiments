#!/usr/bin/env python3
"""IDENT local-CPU entrypoint: generate splits (if needed) and run baselines.

Prefer: python3 -m experiments.ident.experiment
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow `python experiments/ident/experiment.py` without shadowing the package.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments.ident.eval.reports import markdown_summary  # noqa: E402
from experiments.ident.eval.runner import run_local_baseline_suite  # noqa: E402
from experiments.ident.generation import DATA_DIR, build_default_dataset  # noqa: E402

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="IDENT one-shot benchmark runner")
    parser.add_argument("--seed", type=int, default=20260727)
    parser.add_argument("--split", default="test", choices=["train", "dev", "test"])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--skip-generate", action="store_true")
    parser.add_argument(
        "--force-generate",
        action="store_true",
        help="Regenerate train/dev/test even if present",
    )
    args = parser.parse_args(argv)

    need = args.force_generate or not (DATA_DIR / "test.jsonl").exists()
    if need and not args.skip_generate:
        build_default_dataset(seed=args.seed)

    summary = run_local_baseline_suite(
        split=args.split,
        seed=0,
        limit=args.limit,
        out_dir=RESULTS,
    )
    md = markdown_summary(summary)
    (RESULTS / "baseline_summary.md").write_text(md, encoding="utf-8")
    print(json.dumps({"status": summary["status"], "gates": summary["gates"]}, indent=2))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
