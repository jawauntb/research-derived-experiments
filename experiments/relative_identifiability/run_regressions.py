#!/usr/bin/env python3
"""Run the versioned MIDAS regression fixtures and write public receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from experiments.relative_identifiability.fixtures import load_regression_suite


PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[1]
DEFAULT_FIXTURE = PACKAGE / "fixtures" / "midas_regressions.json"
DEFAULT_JSON = PACKAGE / "results" / "summary.json"
DEFAULT_MARKDOWN = PACKAGE / "results" / "summary.md"


def render_markdown(receipt: dict[str, Any]) -> str:
    verdict = "PASS" if receipt["all_passed"] else "FAIL"
    lines = [
        "# Relative Identifiability Regression Summary",
        "",
        f"**Python fixture verdict:** `{verdict}`",
        "",
        f"**Fixture SHA-256:** `{receipt['fixture']['sha256']}`",
        "",
        "## Target-identification cases",
        "",
        "| Case | Expected | Observed | Pass |",
        "|---|---|---|---|",
    ]
    for case in receipt["cases"]:
        lines.append(
            "| {id} | {expected} | {observed} | {passed} |".format(
                id=case["id"],
                expected=case["expected"]["status"],
                observed=case["observed"]["status"],
                passed="yes" if case["passed"] else "no",
            )
        )
    lines.extend(
        [
            "",
            "## Experiment-family refinements",
            "",
            "| Case | Expected strict | Observed strict | Pass |",
            "|---|---:|---:|---|",
        ]
    )
    for case in receipt["refinements"]:
        lines.append(
            "| {id} | {expected} | {observed} | {passed} |".format(
                id=case["id"],
                expected=str(case["expected"]["strict"]).lower(),
                observed=str(case["observed"]["strict"]).lower(),
                passed="yes" if case["passed"] else "no",
            )
        )
    lines.extend(
        [
            "",
            "The external-only mechanism and coordinate cases are expected",
            "obstructions. Their `PASS` status means the engine produced the",
            "registered counterexample; it does not mean those targets were",
            "identified.",
            "",
        ]
    )
    return "\n".join(lines)


def run(
    fixture_path: Path = DEFAULT_FIXTURE,
    json_path: Path | None = None,
    markdown_path: Path | None = None,
) -> dict[str, Any]:
    fixture_path = fixture_path.resolve()
    if fixture_path != DEFAULT_FIXTURE.resolve() and (
        json_path is None or markdown_path is None
    ):
        raise ValueError(
            "custom fixtures require explicit JSON and Markdown output paths"
        )
    json_path = DEFAULT_JSON if json_path is None else json_path
    markdown_path = DEFAULT_MARKDOWN if markdown_path is None else markdown_path
    suite = load_regression_suite(fixture_path)
    receipt = suite.run()
    try:
        fixture_label = str(fixture_path.relative_to(ROOT))
    except ValueError:
        fixture_label = str(fixture_path)
    receipt["fixture"] = {
        "path": fixture_label,
        "sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
    }
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(receipt), encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args()
    try:
        receipt = run(args.fixture, args.json_out, args.markdown_out)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["all_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
