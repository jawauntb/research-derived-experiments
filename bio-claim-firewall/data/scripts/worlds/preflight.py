#!/usr/bin/env python3
"""Run no-network source-contract preflights for one or all ranked worlds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _common import preflight_contract

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "data" / "manifests" / "worlds"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world", help="world_id to inspect; default is every contract")
    args = parser.parse_args()
    paths = sorted(CONTRACTS.glob("*.json"))
    if args.world:
        paths = [path for path in paths if path.stem == args.world]
    if not paths:
        parser.error("no matching world contract")
    print(json.dumps([preflight_contract(path) for path in paths], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
