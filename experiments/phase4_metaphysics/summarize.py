#!/usr/bin/env python3
"""Summarize a Phase 4 Metaphysics suite payload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from experiments.phase4_metaphysics.core import summarize_rows


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
    lines.append("# Phase 4 Metaphysics L4 Suite")
    lines.append("")
    lines.append("## Discovery-Regime Audit")
    lines.append("")
    lines.append("Question: Can the Metric Stack learn the missing conditions that Phase 3 had to hand-specify?")
    lines.append("")
    lines.append("Current regime:")
    lines.append("- Artifact types: JSON suite payloads, gate summaries, result reports, paper PDFs.")
    lines.append("- Operations: cheap L4-parallel diagnostic cells across seven controlled harnesses.")
    lines.append("- Gates/verifiers: predeclared pass/fail criteria per open question, negative controls, lint/type/test checks.")
    lines.append("- Known limitations: controlled synthetic/diagnostic harnesses; not yet foundation-model or biological generality.")
    lines.append("")
    lines.append("Action class:")
    lines.append("- Search/discovery: search inside known program schema, with discovery claim only where a new mechanism survives controls.")
    lines.append("")
    lines.append("Gate:")
    lines.append("- Acceptance rule: each track-specific gate must pass for a Phase 4 mechanism claim.")
    lines.append("- Withheld/rejected rule: any failed track remains a bounded negative and cannot be promoted into the synthesis claim.")
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
                    "weakness_logprob_r",
                    "intervention_effect",
                    "f1",
                    "ood_lift",
                    "boundary_accuracy",
                    "return_50",
                    "final_mae",
                    "mae_reduction_vs_random",
                    "voi_spearman",
                    "mediated_mae",
                    "specificity",
                    "moved_location_lift",
                    "mean_ood",
                    "topology_partial_loss_weakness",
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
