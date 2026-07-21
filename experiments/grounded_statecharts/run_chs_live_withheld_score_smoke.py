"""Generate the live withheld-at-score-time harvest-vs-seal join under artifacts/.

Reads sanitized live D2 harness-v2 rows, seals paired-contrast labels and
harvests heuristic candidates independently, writes both to disk, then joins
them by result digest only after both have already returned. See
`chs_live_withheld_score.py` and `CHS_SEALED_PREREGISTRATION.md` for the
claim boundary.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.grounded_statecharts.chs_live_withheld_score import (
    DEFAULT_OUTPUT,
    DEFAULT_ROWS,
    generate_results,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, default=DEFAULT_ROWS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    summary = generate_results(rows_path=args.rows, output_dir=args.out_dir)
    print(json.dumps({"out_dir": str(args.out_dir), **summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
