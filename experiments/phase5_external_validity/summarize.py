#!/usr/bin/env python3
"""Summarize a Phase 5 external-validity suite payload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from experiments.phase5_external_validity.core import summarize_rows


def _fmt(value: Any, digits: int = 3) -> str:
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    if isinstance(value, (int, float)):
        return f"{float(value):.{digits}f}"
    return str(value)


def write_report(payload: dict[str, Any], out: Path) -> None:
    summary = payload.get("summary") or summarize_rows(payload["rows"])
    gates = summary["gates"]
    lines: list[str] = []
    lines.append("# Phase 5 External Validity L4 Suite")
    lines.append("")
    lines.append("## Discovery-Regime Audit")
    lines.append("")
    lines.append("Question: Which Phase 4 mechanisms transport when the setup becomes model-like, semantic, or counterfactual?")
    lines.append("")
    lines.append("Current regime:")
    lines.append("- Artifact types: JSON suite payloads, gate summaries, result reports, paper PDFs.")
    lines.append("- Operations: cheap L4-parallel transport cells across four external-validity proxy harnesses.")
    lines.append("- Gates/verifiers: predeclared pass/fail criteria, controls that should fail, lint/type/test checks, PDF render inspection.")
    lines.append("- Known limitations: proxy transport result; real open-model runs remain the next heavier validation tier.")
    lines.append("")
    lines.append("Action class:")
    lines.append("- Search/discovery: discovery only where a Phase 4 mechanism survives a harder transport gate and controls fail.")
    lines.append("")
    lines.append("Gate:")
    lines.append("- Acceptance rule: each transport track must clear its track-specific gate before the mechanism is promoted.")
    lines.append("- Withheld/rejected rule: failed controls and bounded negatives remain in the report as future baselines.")
    lines.append("")
    lines.append("## Manifest")
    lines.append("")
    manifest = payload.get("manifest", {})
    for key in ["preset", "tracks", "seeds", "gpu", "claim_level"]:
        if key in manifest:
            lines.append(f"- {key}: `{manifest[key]}`")
    if "budget_estimate" in manifest:
        est = manifest["budget_estimate"]
        lines.append(
            "- budget estimate: "
            f"{est.get('cells')} L4 cells, conservative timeout cost "
            f"${float(est.get('conservative_cost_usd', 0.0)):.2f} / "
            f"${float(est.get('budget_usd', 0.0)):.2f}"
        )
    lines.append(f"- rows: `{summary['n_rows']}`")
    lines.append("")
    lines.append("## Gate Summary")
    lines.append("")
    lines.append("| Track | Status | Criteria | Key metrics | Claim |")
    lines.append("| --- | --- | --- | --- | --- |")
    for track, gate in gates.items():
        if track == "all_pass":
            continue
        metric_bits = []
        for key, value in gate.items():
            if key in {"pass", "criteria", "claim"}:
                continue
            metric_bits.append(f"{key}={_fmt(value)}")
        lines.append(
            f"| `{track}` | {_fmt(gate['pass'])} | {gate['criteria']} | "
            f"{'; '.join(metric_bits)} | {gate['claim']} |"
        )
    lines.append("")
    lines.append(f"Overall: **{_fmt(gates['all_pass'])}**")
    lines.append("")
    lines.append("## Condition Means")
    lines.append("")
    for track, data in summary["by_track"].items():
        lines.append(f"### {track}")
        lines.append("")
        lines.append("| Condition | n | Primary metrics |")
        lines.append("| --- | ---: | --- |")
        for condition, cdata in data["conditions"].items():
            metrics = []
            for name, stat in cdata["metrics"].items():
                if name in {
                    "geometry_action_r",
                    "heldout_transfer_r",
                    "intervention_ratio",
                    "moved_location_lift",
                    "specificity",
                    "cross_encoder_transfer",
                    "mediated_mae",
                    "counterfactual_consistency",
                    "ood_return",
                    "mean_ood",
                    "seam_only_lift",
                    "topology_only_lift",
                    "joint_interaction",
                    "seam_partial_with_topology",
                }:
                    metrics.append(f"{name}={_fmt(stat['mean'])}")
            lines.append(f"| `{condition}` | {cdata['n']} | {'; '.join(metrics)} |")
        lines.append("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text())
    write_report(payload, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
