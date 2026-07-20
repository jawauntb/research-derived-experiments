"""Harvest provisional CHS candidates from sanitized live D2 artifact rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.grounded_statecharts.chs_from_live import (
    DEFAULT_OUTPUT,
    DEFAULT_ROWS,
    generate_results,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, default=DEFAULT_ROWS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    summary = generate_results(args.rows, args.out_dir)
    print(json.dumps({"out_dir": str(args.out_dir), **summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
