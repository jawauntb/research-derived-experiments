"""Seal CHS labels from paired public-row contrasts into artifacts/."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.grounded_statecharts.chs_adjudication import (
    DEFAULT_OUTPUT,
    generate_results,
)
from experiments.grounded_statecharts.live_replay import DEFAULT_ROWS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, default=DEFAULT_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = generate_results(rows_path=args.rows, output_dir=args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
