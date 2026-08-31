"""`python -m eval.mutation` -- run the full (or a limited) mutation pass.

Invoke from `bio-claim-firewall/` (or with `bio-claim-firewall/` on
`PYTHONPATH`), matching how `bio-claim-firewall/conftest.py` itself
bootstraps `sys.path`:

    cd bio-claim-firewall
    python -m eval.mutation --limit 5 --report eval/mutation/reports/latest.md

or from the workspace root:

    PYTHONPATH=bio-claim-firewall uv run --no-sync python -m eval.mutation \\
        --limit 5 --report bio-claim-firewall/eval/mutation/reports/latest.md

`--report` (like any relative CLI path) resolves against the current
working directory, same as `pytest`'s own path arguments.

Exit code is 0 iff every mutant was killed; 1 if at least one survived
(the guardrail's failure signal for CI); 2 on a framework-level problem
(e.g. discovery failed).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .report import summarize, surviving_sites, write_report
from .runner import MUTATION_KINDS, MutationError, MutationRunner


def _default_workspace_root() -> Path:
    # This file: bio-claim-firewall/eval/mutation/cli.py
    # parents[0]=mutation, [1]=eval, [2]=bio-claim-firewall, [3]=workspace root.
    return Path(__file__).resolve().parents[3]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m eval.mutation", description=__doc__)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only run the first N mutation POINTS (each still gets all mutation kinds).",
    )
    parser.add_argument(
        "--kinds",
        nargs="+",
        default=None,
        choices=list(MUTATION_KINDS),
        help="Restrict to specific mutation kinds (default: all three).",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("eval/mutation/reports/latest.md"),
        help="Markdown report path (a sibling .json is also written). Resolved against the CWD.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Per-subprocess pytest timeout, in seconds (default: 60).",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Directory containing bio-claim-firewall/ and its conftest.py (default: auto-detected).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    workspace_root = args.workspace_root or _default_workspace_root()
    runner = MutationRunner(workspace_root=workspace_root, timeout_s=args.timeout)

    try:
        points = runner.discover()
    except MutationError as exc:
        print(f"discovery failed: {exc}", file=sys.stderr)
        return 2
    print(f"Discovered {len(points)} MUTATION-POINT site(s) in src/rules/sections/.")

    baseline = runner.baseline_failed_tests()
    if baseline:
        print(f"WARNING: {len(baseline)} test(s) already fail on the unmutated tree; excluded from kill detection.")

    kinds = tuple(args.kinds) if args.kinds else MUTATION_KINDS
    reports = []
    for i, report in enumerate(runner.run(points, kinds=kinds, limit=args.limit), start=1):
        reports.append(report)
        print(f"[{i}] {report.site_id} :: {report.mutation_kind} -> {report.status}")

    json_path = write_report(reports, args.report)
    print(f"\nWrote {args.report} and {json_path}")

    summary = summarize(reports)
    print(f"killed={summary['killed']} survived={summary['survived']} skipped={summary['skipped']} total={summary['total']}")

    survivors = surviving_sites(reports)
    if survivors:
        print(f"\n{len(survivors)} mutant(s) SURVIVED -- untested rule site(s):")
        for r in survivors:
            print(f"  - {r.site_id} ({', '.join(r.rule_ids) or '?'}) [{r.mutation_kind}]")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
