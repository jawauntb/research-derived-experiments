"""Generate the credential-free Harness Unlearning multi-shift draft bundle.

Runs the nine independently authored shift-instance fixtures in
`unlearning_multishift.py` against the deterministic memory ledger and
commitment harness. No network access, no live model calls; safe to run in
any clean clone. See `run_unlearning_multishift_live_smoke.py` for the
optional credentialed live-adapter mechanics smoke over a subset of this
bank.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.grounded_statecharts.unlearning_multishift import (
    DEFAULT_OUTPUT,
    generate_results,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    summary = generate_results(args.out_dir)
    print(
        json.dumps(
            {
                "run_id": summary["run_id"],
                "gates": summary["gates"],
                "out_dir": str(args.out_dir),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
