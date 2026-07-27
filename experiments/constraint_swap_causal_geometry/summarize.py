#!/usr/bin/env python3
"""Human-readable registered report for Constraint-Swap results."""

from __future__ import annotations

from pathlib import Path
from typing import Any


METRIC_LABELS = {
    "accuracy_A": "Mature A accuracy",
    "accuracy_B": "Mature B accuracy",
    "accuracy_D": "Deterministic-control accuracy",
    "sham_accuracy": "Randomized-sham accuracy",
    "known_geometry_lift": "Injected-geometry recovery lift",
    "geometry_A_specific": "A-specific geometry",
    "geometry_B_specific": "B-specific geometry",
    "swap_tau_AB": "A-to-B swap tracking",
    "swap_tau_BA": "B-to-A swap tracking",
    "undo_B_specific_harm": "Undo B selective impairment",
    "undo_A_specific_harm": "Undo A selective impairment",
    "rescue_B_specific_gain": "Impose B selective rescue",
    "rescue_A_specific_gain": "Impose A selective rescue",
}


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    return f"{float(value):.3f}"


def write_summary(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    verdict = summary["verdict"]
    lines = [
        "# Constraint-Swap Causal Geometry - Registered Result",
        "",
        f"- **Decision:** `{verdict['decision']}`",
        f"- **All gates pass:** `{verdict['all_pass']}`",
        f"- **Independent confirmatory seeds:** `{summary['n_seeds']}`",
        f"- **Bootstrap resamples:** `{summary['bootstrap_samples']}`",
        "- **Claim scope:** frozen meta-GRU, registered parity constraints, "
        "query-surface rank-4 affine transports, one torus and one cylinder.",
        "",
        "## Noncompensatory Gates",
        "",
        "| Gate | Status | Registered rule / failure |",
        "| --- | --- | --- |",
    ]
    for gate, detail in verdict["gates"].items():
        explanation = detail.get("rule")
        if not explanation:
            failed = detail.get("failed_checks", [])
            explanation = ", ".join(failed) if failed else "registered component tests"
        lines.append(
            f"| `{gate}` | **{'PASS' if detail['pass'] else 'FAIL'}** | {explanation} |"
        )

    lines.extend(
        [
            "",
            "## Primary Topology Metrics",
            "",
            "| Metric | Mean | 90% bootstrap interval |",
            "| --- | ---: | ---: |",
        ]
    )
    for metric, label in METRIC_LABELS.items():
        interval = summary["primary_intervals"][metric]
        lines.append(
            f"| {label} | {_fmt(interval['mean'])} | "
            f"[{_fmt(interval['lower'])}, {_fmt(interval['upper'])}] |"
        )

    lines.extend(
        [
            "",
            "## Transfer Topology Metrics",
            "",
            "| Metric | Mean | 90% bootstrap interval |",
            "| --- | ---: | ---: |",
        ]
    )
    for metric, label in METRIC_LABELS.items():
        interval = summary["transfer_intervals"][metric]
        lines.append(
            f"| {label} | {_fmt(interval['mean'])} | "
            f"[{_fmt(interval['lower'])}, {_fmt(interval['upper'])}] |"
        )

    lines.extend(
        [
            "",
            "## Discovery-Regime Audit",
            "",
            "- **Accepted artifacts:** exact future-language enumerator, balanced "
            "constraint schedules, seed rows, nuisance audit, and positive-control "
            "measurement check where their gates pass.",
            "- **Rejected or withheld artifacts:** every failed gate remains visible; "
            "no pooled score rescues a failed direction or topology.",
            "- **Transported evidence:** prior task/context geometry and causal "
            "intervention literature motivated the controls but does not count as "
            "evidence that this run passed.",
            "- **Residual content:** the final paper states the strongest surviving "
            "descriptive, swap, causal, and topology claims separately.",
            "",
            "## Provenance",
            "",
            f"- Raw run: `{payload['raw_run_path']}`",
            f"- Public seed rows: `{payload['rows_path']}`",
            "- Frozen manifest: "
            "`experiments/constraint_swap_causal_geometry/experiment_manifest.json`",
            "- Preregistration: "
            "`experiments/constraint_swap_causal_geometry/PREREGISTRATION.md`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
