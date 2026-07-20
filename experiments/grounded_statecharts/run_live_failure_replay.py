"""Render one paired live D2 failure replay from an artifact rows file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.grounded_statecharts.live_replay import (
    DEFAULT_OUTPUT,
    DEFAULT_PUBLIC_OUTPUT,
    DEFAULT_ROWS,
    generate_replay,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, default=DEFAULT_ROWS)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument(
        "--publish-public",
        action="store_true",
        help="Write a public stub only when every input row is sanitized public schema.",
    )
    args = parser.parse_args(argv)
    output_dir = args.out_dir or (
        DEFAULT_PUBLIC_OUTPUT if args.publish_public else DEFAULT_OUTPUT
    )
    summary = generate_replay(
        args.rows, output_dir, publish_public=args.publish_public
    )
    print(json.dumps({"out_dir": str(output_dir), **summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
