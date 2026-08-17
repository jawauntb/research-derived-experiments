#!/usr/bin/env python3
"""Run the US-4′ unknown-skeleton recovery probe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from experiments.eml_us4_search.core import evaluate_benchmark
else:
    from .core import evaluate_benchmark


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "results" / "eml_us4_search_summary.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = evaluate_benchmark()
    slim = dict(payload)
    searches = []
    for search in payload["searches"]:
        row = dict(search)
        row["hits"] = [hit for hit in search["hits"] if hit["n_success"] or hit["exact"]]
        searches.append(row)
    slim["searches"] = searches
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(slim, indent=2, sort_keys=True) + "\n")
    ranking = payload["ranking"]
    print(
        json.dumps(
            {
                "status": payload["status"],
                "gates": payload["gates"],
                "verdict": ranking["verdict"],
                "zero_gd": ranking["zero_gd"],
                "thin_gd": ranking["thin_gd"],
                "zero_extra": ranking["zero_extra"],
                "thin_extra": ranking["thin_extra"],
            },
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
