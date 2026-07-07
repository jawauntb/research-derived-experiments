#!/usr/bin/env python3
"""Write a markdown report for the Gauge-Fixed Concern Transport suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TRACK_LABELS = {
    "concern_weighted_ood": "Concern-weighted OOD",
    "causal_gauge_fixing": "Causal gauge fixing",
    "mechanistic_commitment": "Mechanistic commitment",
    "reafference_null": "Reafference/null",
    "moved_bottleneck": "Moved bottleneck",
}


PRIMARY_METRICS = {
    "concern_weighted_ood": ["weighted_error_gain", "concern_selector_is_shape"],
    "causal_gauge_fixing": ["alignment_lift", "commitment_effect_lift"],
    "mechanistic_commitment": [
        "patch_effect_ratio",
        "distractor_probe_auc",
        "distractor_patch_effect",
    ],
    "reafference_null": [
        "attribution_lift",
        "correction_error_reduction",
        "null_intervention_auc",
    ],
    "moved_bottleneck": [
        "active_vs_early_gain",
        "active_inactive_ratio",
        "localized_active_bottleneck",
    ],
}


def _fmt(value: Any, digits: int = 3) -> str:
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    if isinstance(value, (int, float)):
        return f"{float(value):.{digits}f}"
    return str(value)


def write_report(payload: dict[str, Any], out: Path) -> None:
    summary = payload["summary"]
    manifest = payload.get("manifest", {})
    lines = [
        "# Gauge-Fixed Concern Transport L4 Suite",
        "",
        f"- Overall: **{_fmt(summary['gates']['all_pass'])}**",
        f"- Claim level: `{manifest.get('claim_level', 'unknown')}`",
        f"- Preset: `{manifest.get('preset', 'unknown')}`",
        f"- Tracks: `{', '.join(manifest.get('tracks', []))}`",
        f"- Seeds: `{manifest.get('seeds', 'unknown')}`",
        f"- Rows: `{summary.get('n_rows', 'unknown')}`",
    ]
    budget = manifest.get("budget_estimate")
    if budget:
        lines.extend(
            [
                f"- GPU: `{budget.get('gpu')}`",
                "- Budget estimate: "
                f"{budget.get('cells')} L4 cells, conservative timeout cost "
                f"${float(budget.get('conservative_cost_usd', 0.0)):.2f} / "
                f"${float(budget.get('budget_usd', 0.0)):.2f}",
            ]
        )
    lines.extend(["", "## Gates", "", "| Track | Status | Primary metrics |", "| --- | --- | --- |"])
    for track in summary["tracks"]:
        gate = summary["gates"][track]
        metric_parts = []
        for metric in PRIMARY_METRICS[track]:
            value = summary["by_track"][track]["metrics"][metric]["mean"]
            metric_parts.append(f"`{metric}`={_fmt(value)}")
        lines.append(
            f"| {TRACK_LABELS.get(track, track)} | {_fmt(gate['pass'])} | "
            f"{'; '.join(metric_parts)} |"
        )
    lines.extend(
        [
            "",
            "## Discovery-Regime Audit",
            "",
            "- **Old regime:** proof-focused theorem paper with proposed demos.",
            "- **Transition:** Modal L4 synthetic cells with raw rows, gates, controls, and figures.",
            "- **Preserved gates:** concern weighting, gauge separation, commitment effect, null controls, and moved-bottleneck localization.",
            "- **Allowed claim:** synthetic L4 empirical validation only.",
            "- **Residual bottleneck:** human, neural, biological, and foundation-model validation remain future work.",
            "",
            "## Raw Payload",
            "",
            f"`{payload.get('payload_path', 'artifact path recorded by caller')}`",
            "",
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.in_path.read_text())
    payload["payload_path"] = str(args.in_path)
    write_report(payload, args.out)
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
