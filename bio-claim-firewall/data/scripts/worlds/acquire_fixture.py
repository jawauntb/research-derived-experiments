#!/usr/bin/env python3
"""Create a tiny deterministic local acquisition fixture without network access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _common import fixture_manifest, sha256_bytes


ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world", required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    output = args.output or ROOT / "data" / "fixtures" / "worlds" / args.world
    output.mkdir(parents=True, exist_ok=True)
    payload = ("world_id=" + args.world + "\n").encode("utf-8")
    artifact = output / "sample.txt"
    artifact.write_bytes(payload)
    manifest = fixture_manifest(output)
    (output / "fixture-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"{args.world}: {sha256_bytes(payload)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
