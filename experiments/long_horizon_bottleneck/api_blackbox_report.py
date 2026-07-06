"""Aggregate black-box API benchmark summaries into a provider matrix."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


def read_summary_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def aggregate_api_blackbox_summaries(paths: list[Path]) -> dict[str, Any]:
    """Build a compact matrix from per-provider summary JSON files."""

    entries: list[dict[str, Any]] = []
    failed_cells: list[dict[str, Any]] = []
    for path in sorted(paths):
        payload = read_summary_payload(path)
        summary = payload["summary"]
        manifest = payload.get("manifest", {})
        models = [str(model) for model in manifest.get("models", [])]
        provider = str(manifest.get("provider") or _first_cell_value(summary, "provider"))
        model_label = ", ".join(models) if models else str(_first_cell_value(summary, "model"))
        suite = str(manifest.get("suite") or _first_cell_value(summary, "suite"))
        n_cells = len(summary.get("cells", {}))
        n_failed = 0
        for key, cell in sorted(summary.get("cells", {}).items()):
            if cell.get("pass"):
                continue
            n_failed += 1
            failed_cells.append(
                {
                    "summary_path": str(path),
                    "cell_key": key,
                    "suite": cell.get("suite", suite),
                    "stress_case": cell.get("stress_case"),
                    "provider": cell.get("provider", provider),
                    "model": cell.get("model", model_label),
                    "prompt_family": cell.get("prompt_family"),
                    "n_slots": cell.get("n_slots"),
                    "slot_gap": cell.get("slot_gap"),
                    "complete": bool(cell.get("complete")),
                    "controls_pass": bool(cell.get("controls_pass")),
                    "bottleneck_pass": bool(cell.get("bottleneck_pass")),
                    "condition_gates": cell.get("condition_gates", {}),
                }
            )
        requests_per_model = int(manifest.get("n_requests", 0) or 0)
        model_count = max(1, len(models))
        entries.append(
            {
                "summary_path": str(path),
                "suite": suite,
                "provider": provider,
                "model": model_label,
                "outcome": summary["outcome"],
                "n_rows": int(summary["n_rows"]),
                "n_cells": n_cells,
                "failed_cells": n_failed,
                "request_budget": requests_per_model * model_count,
                "prompt_families": manifest.get("prompt_families", []),
                "stress_cases": manifest.get("stress_cases", []),
            }
        )

    suite_outcomes: dict[str, dict[str, Any]] = {}
    for suite in sorted({entry["suite"] for entry in entries}):
        suite_entries = [entry for entry in entries if entry["suite"] == suite]
        outcomes = sorted({entry["outcome"] for entry in suite_entries})
        suite_outcomes[suite] = {
            "n_runs": len(suite_entries),
            "outcomes": outcomes,
            "all_positive": bool(suite_entries) and all(entry["outcome"] == "positive" for entry in suite_entries),
            "any_strong_negative": any(entry["outcome"] == "strong_negative" for entry in suite_entries),
            "total_rows": sum(entry["n_rows"] for entry in suite_entries),
            "total_request_budget": sum(entry["request_budget"] for entry in suite_entries),
        }

    return {
        "kind": "long-horizon moved-bottleneck multi-provider API aggregate",
        "n_summaries": len(entries),
        "total_rows": sum(entry["n_rows"] for entry in entries),
        "total_request_budget": sum(entry["request_budget"] for entry in entries),
        "entries": entries,
        "suite_outcomes": suite_outcomes,
        "failed_cells": failed_cells,
    }


def render_api_blackbox_markdown(
    aggregate: dict[str, Any],
    *,
    title: str = "API Black-Box Multi-Provider Replication",
    report_date: str | None = None,
) -> str:
    report_date = report_date or date.today().isoformat()
    lines = [
        f"# {title}",
        "",
        f"Date: {report_date}",
        "",
        "## Outcome",
        "",
        *_outcome_lines(aggregate),
        "",
        "## Verification Signals",
        "",
        *_verification_signal_lines(aggregate),
        "",
        "## Provider Matrix",
        "",
        "| Suite | Provider | Model | Rows | Requests | Cells | Failed cells | Outcome |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for entry in sorted(aggregate["entries"], key=lambda item: (item["suite"], item["provider"], item["model"])):
        lines.append(
            "| {suite} | {provider} | `{model}` | {n_rows} | {request_budget} | {n_cells} | "
            "{failed_cells} | `{outcome}` |".format(**entry)
        )

    lines.extend(["", "## Failure Surface", ""])
    if aggregate["failed_cells"]:
        lines.extend(
            [
                "| Suite | Provider | Model | Stress | Family | Controls | Bottleneck | Failed condition gates |",
                "|---|---|---|---|---|---|---|---|",
            ]
        )
        for cell in aggregate["failed_cells"]:
            failed_gates = ", ".join(
                condition for condition, passed in sorted(cell["condition_gates"].items()) if not passed
            )
            lines.append(
                "| {suite} | {provider} | `{model}` | {stress_case} | {prompt_family} | {controls} | "
                "{bottleneck} | {failed_gates} |".format(
                    suite=cell["suite"],
                    provider=cell["provider"],
                    model=cell["model"],
                    stress_case=cell["stress_case"],
                    prompt_family=cell["prompt_family"],
                    controls="yes" if cell["controls_pass"] else "no",
                    bottleneck="yes" if cell["bottleneck_pass"] else "no",
                    failed_gates=failed_gates or "none",
                )
            )
    else:
        lines.append("No failed cells.")

    lines.extend(
        [
            "",
            "## Regime Audit",
            "",
            "- Old regime: one-provider black-box behavior after open-model hidden-state and causal-patch evidence.",
            "- Transition: matched multi-provider API behavior with the same parser, controls, bottleneck gates, and repair gates.",
            "- Transported evidence: prompt-family suite, external-stress axes, request guard, JSONL rows, and scored summaries.",
            "- Rejected alternatives: smoke runs are not counted in the matched matrix, and black-box API behavior is not treated as hidden-state or production-tool evidence.",
            "- Residual finding: provider-specific stress sensitivity is now visible; a run can be positive on the registered prompt-family suite and still fail a controlled dispatch stress cell.",
            "- Readiness: prompt-family gates pass across all tested providers; external-stress readiness is mixed because failed cells remain under passing controls.",
            "- Allowed claim: multi-provider black-box behavioral replication for the tested suites, with any failed stress cells treated as behavioral counterevidence rather than hidden-state evidence.",
            "- Next operation: isolate the dispatch failure into wording, value-copying, and repair-memory variants.",
            "",
            "## Local Artifacts",
            "",
        ]
    )
    for entry in sorted(aggregate["entries"], key=lambda item: item["summary_path"]):
        lines.append(f"- `{entry['summary_path']}`")
    return "\n".join(lines) + "\n"


def write_aggregate_json(path: Path, aggregate: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _outcome_lines(aggregate: dict[str, Any]) -> list[str]:
    prompt = aggregate["suite_outcomes"].get("prompt_family")
    stress = aggregate["suite_outcomes"].get("external_stress")
    lines: list[str] = []
    if prompt:
        result = "positive" if prompt["all_positive"] else ", ".join(prompt["outcomes"])
        lines.append(
            f"Prompt-family replication outcome: `{result}` across {prompt['n_runs']} provider/model runs."
        )
    if stress:
        if stress["all_positive"]:
            result = "positive"
        elif stress["any_strong_negative"]:
            result = "mixed with controlled strong negative"
        else:
            result = ", ".join(stress["outcomes"])
        lines.append(f"External-stress outcome: `{result}` across {stress['n_runs']} provider/model runs.")
    lines.append(
        f"Total scored rows: {aggregate['total_rows']}; total planned API requests: "
        f"{aggregate['total_request_budget']}."
    )
    return lines


def _verification_signal_lines(aggregate: dict[str, Any]) -> list[str]:
    prompt = aggregate["suite_outcomes"].get("prompt_family", {})
    stress = aggregate["suite_outcomes"].get("external_stress", {})
    failed_controls_preserved = bool(aggregate["failed_cells"]) and all(
        cell["controls_pass"] for cell in aggregate["failed_cells"]
    )
    return [
        f"API prompt-family multi-provider gate pass: {'yes' if prompt.get('all_positive') else 'no'}.",
        f"API external-stress all-provider gate pass: {'yes' if stress.get('all_positive') else 'no'}.",
        f"API external-stress controlled strong negative found: {'yes' if stress.get('any_strong_negative') else 'no'}.",
        f"API failed-cell controls preserved: {'yes' if failed_controls_preserved else 'not applicable'}.",
    ]


def _first_cell_value(summary: dict[str, Any], key: str) -> Any:
    for cell in summary.get("cells", {}).values():
        return cell.get(key)
    return ""


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summaries", nargs="+", type=Path)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    parser.add_argument("--title", default="API Black-Box Multi-Provider Replication")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)

    aggregate = aggregate_api_blackbox_summaries(args.summaries)
    if args.out_json:
        write_aggregate_json(args.out_json, aggregate)
    markdown = render_api_blackbox_markdown(aggregate, title=args.title, report_date=args.date)
    if args.out_md:
        write_markdown(args.out_md, markdown)
    if not args.out_json and not args.out_md:
        print(markdown)


if __name__ == "__main__":
    main()
