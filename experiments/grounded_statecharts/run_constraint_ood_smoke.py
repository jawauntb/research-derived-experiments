"""Generate the credential-free Constraint Transport OOD probe stub bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.grounded_statecharts.constraint_ood import DEFAULT_OUTPUT, generate_results


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
