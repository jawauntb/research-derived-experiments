"""Generate the withheld-at-score-time equal-budget repair-search bundle.

Two-step CLI: first writes the withheld-seal label store (public-safe,
synthetic fixture bank) under `results/chs_withheld_seals/`, then re-runs the
equal-budget counterfactual repair/placebo search over a case/result
representation with no `responsible_component` attribute at all
(`BlindCounterfactualHarnessPilot`) and scores it against that separate
store, loaded only at score time via `--sealed-labels`. See
`chs_repair_search.py` and `CHS_SEALED_PREREGISTRATION.md` for the claim
boundary: this is a CHS1-bridge, not author-blind human adjudication CHS1.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.grounded_statecharts.chs_repair_search import (
    DEFAULT_CASES,
    DEFAULT_WITHHELD_SEAL_OUTPUT,
    DEFAULT_WITHHELD_SEALED_LABELS,
    DEFAULT_WITHHELD_SEARCH_OUTPUT,
    generate_withheld_results,
    generate_withheld_seals,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--seal-output-dir", type=Path, default=DEFAULT_WITHHELD_SEAL_OUTPUT)
    parser.add_argument("--sealed-labels", type=Path, default=DEFAULT_WITHHELD_SEALED_LABELS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_WITHHELD_SEARCH_OUTPUT)
    args = parser.parse_args(argv)

    seal_summary = generate_withheld_seals(cases_path=args.cases, output_dir=args.seal_output_dir)
    search_summary = generate_withheld_results(
        sealed_labels_path=args.sealed_labels,
        cases_path=args.cases,
        output_dir=args.out_dir,
    )
    print(
        json.dumps(
            {
                "seal_output_dir": str(args.seal_output_dir),
                "search_out_dir": str(args.out_dir),
                "seal_gates": seal_summary["gates"],
                "search_gates": search_summary["gates"],
                "search_metrics": search_summary["metrics"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
