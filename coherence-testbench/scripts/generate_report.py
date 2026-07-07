#!/usr/bin/env python3
"""Regenerate the GO/KILL report from a saved run without rerunning the sweep.

Reads `manifest.json` + `run.jsonl` from an artifact directory and re-emits
`report.md` + `report.json`. Useful if the kill-criterion or the report
template changes; the underlying fold results are frozen.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from coherence.config import load_kill_criterion  # noqa: E402
from coherence.evaluate import LSOFoldResult  # noqa: E402
from coherence.report import build_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True,
                        help="Directory containing manifest.json + run.jsonl")
    parser.add_argument("--kill-criterion", default="config/kill_criterion.yaml")
    parser.add_argument("--out", default=None,
                        help="Output directory (defaults to --results)")
    args = parser.parse_args()

    results_dir = Path(args.results)
    out_dir = Path(args.out) if args.out else results_dir
    manifest = json.loads((results_dir / "manifest.json").read_text())

    fold_results: list[LSOFoldResult] = []
    with (results_dir / "run.jsonl").open() as jl:
        for line in jl:
            row = json.loads(line)
            fold_results.append(LSOFoldResult(
                seed=row["seed"],
                n_train_subjects=row["n_train_subjects"],
                held_out_subjects=tuple(row["held_out_subjects"]),
                balanced_accuracy=row["balanced_accuracy"],
                bits_per_second=row["bits_per_second"],
                n_test_epochs=row["n_test_epochs"],
            ))

    kc = load_kill_criterion(args.kill_criterion)
    build_report(
        kc=kc,
        fold_results=fold_results,
        per_subject_baseline_bacc=float(manifest.get(
            "per_subject_baseline_balanced_accuracy", 0.5)),
        confound_ablations={},
        out_dir=out_dir,
    )
    print(f"Wrote {out_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
