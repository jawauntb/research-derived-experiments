"""Generate the credential-free equal-budget repair-search bundle under results/.

Re-runs the equal-budget counterfactual repair/placebo search
(`counterfactual_search.CounterfactualHarnessPilot`, unchanged) fresh against
the six committed single-fault fixtures and scores it against the
independently adjudicated injected-fault seal tier
(`results/chs_injected_faults/labels.jsonl`) and the hand-authored sealed-label
fixture (`fixtures/chs_sealed_labels.json`). See `chs_repair_search.py` for the
claim boundary: this is not CHS1 on naturalistic live failures.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.grounded_statecharts.chs_repair_search import (
    DEFAULT_CASES,
    DEFAULT_FIXTURE_LABELS,
    DEFAULT_OUTPUT,
    DEFAULT_SEALED_LABELS,
    generate_results,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sealed-labels", type=Path, default=DEFAULT_SEALED_LABELS)
    parser.add_argument("--fixture-labels", type=Path, default=DEFAULT_FIXTURE_LABELS)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    summary = generate_results(
        sealed_labels_path=args.sealed_labels,
        fixture_labels_path=args.fixture_labels,
        cases_path=args.cases,
        output_dir=args.out_dir,
    )
    print(
        json.dumps(
            {
                "out_dir": str(args.out_dir),
                "gates": summary["gates"],
                "metrics": summary["metrics"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
