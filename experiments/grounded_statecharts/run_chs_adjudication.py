"""Seal CHS labels from paired public-row contrasts into artifacts/.

With `--with-injected`, also seal the injected/deterministic fault tier
(context/tools/generation/orchestration/memory/output) under results/ and
print combined, tier-labeled surface coverage. Neither tier, alone or
combined, is a six-surface CHS1 claim; see CHS_SEALED_PREREGISTRATION.md.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.grounded_statecharts.chs_adjudication import (
    DEFAULT_INJECTED_CASES,
    DEFAULT_INJECTED_OUTPUT,
    DEFAULT_OUTPUT,
    generate_injected_results,
    generate_results,
    summarize_combined_coverage,
)
from experiments.grounded_statecharts.live_replay import DEFAULT_ROWS


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, default=DEFAULT_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--with-injected",
        action="store_true",
        help="also seal the injected-fault tier and report combined coverage",
    )
    parser.add_argument("--injected-cases", type=Path, default=DEFAULT_INJECTED_CASES)
    parser.add_argument("--injected-output-dir", type=Path, default=DEFAULT_INJECTED_OUTPUT)
    args = parser.parse_args()
    summary = generate_results(rows_path=args.rows, output_dir=args.output_dir)
    if not args.with_injected:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return
    injected_summary = generate_injected_results(
        cases_path=args.injected_cases, output_dir=args.injected_output_dir
    )
    combined_coverage = summarize_combined_coverage(
        _read_jsonl(args.output_dir / "labels.jsonl"),
        _read_jsonl(args.injected_output_dir / "labels.jsonl"),
    )
    print(
        json.dumps(
            {
                "live_paired_contrast": summary,
                "injected_fault_seal": injected_summary,
                "combined_coverage": combined_coverage,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
