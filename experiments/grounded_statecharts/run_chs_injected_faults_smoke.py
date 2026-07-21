"""Generate the credential-free injected-fault CHS seal bundle under results/.

Seals context/tools/generation/orchestration/memory/output labels from the
committed single-fault fixtures in `fixtures/counterfactual_faults.json`,
independently of the live paired-contrast tier (`chs_adjudication.py`'s
`seal_from_paired_contrasts`) and independently of the live heuristic harvest
(`chs_from_live.py`). See CHS_SEALED_PREREGISTRATION.md for the claim
boundary: this tier alone is not six-surface CHS1.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.grounded_statecharts.chs_adjudication import (
    DEFAULT_INJECTED_CASES,
    DEFAULT_INJECTED_OUTPUT,
    generate_injected_results,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_INJECTED_CASES)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_INJECTED_OUTPUT)
    args = parser.parse_args(argv)
    summary = generate_injected_results(cases_path=args.cases, output_dir=args.out_dir)
    print(json.dumps({"out_dir": str(args.out_dir), **summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
