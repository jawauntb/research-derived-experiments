#!/usr/bin/env python3
"""Summarize a Phase 6 real-model validation payload."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from experiments.phase6_real_model_validation.core import summarize_rows  # noqa: E402


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
    lines.append("# Phase 6 Real-Model Validation L4 Suite")
    lines.append("")
    lines.append("## Discovery-Regime Audit")
    lines.append("")
    lines.append("Question: Do the Phase 5 proxy transport signals survive contact with actual open LMs and frozen text encoders?")
    lines.append("")
    lines.append("Current regime:")
    lines.append("- Artifact types: JSON model payloads, gate summaries, markdown report, paper PDF, and archived copy.")
    lines.append("- Operations: L4-parallel Hugging Face decoder-LM logprob/hidden-state cells and frozen-encoder metric cells.")
    lines.append("- Gates/verifiers: predeclared signal thresholds, failed-model rows retained, budget guard, lint/type/test checks, PDF render inspection.")
    lines.append("- Known limitations: LM logprob margins are model text behavior, not human action; frozen-encoder metric deformation is post-hoc, not finetuning.")
    lines.append("")
    lines.append("Action class:")
    lines.append("- Validation tier: replaces Phase 5 proxy weights with public open-model/frozen-encoder measurements.")
    lines.append("")
    lines.append("Gate:")
    lines.append("- Acceptance rule: actual models must run and clear weak positive transport thresholds with controls below the promoted effect.")
    lines.append("- Withheld/rejected rule: failed downloads, weak LM coupling, random-label deformation, and cue leakage remain explicit rows.")
    lines.append("")
    lines.append("## Manifest")
    lines.append("")
    manifest = payload.get("manifest", {})
    for key in ["preset", "tracks", "models", "gpu", "claim_level"]:
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
    lines.append("## Model Rows")
    lines.append("")
    for track, data in summary["by_track"].items():
        lines.append(f"### {track}")
        lines.append("")
        lines.append("| Condition | Model | Status | Primary metrics |")
        lines.append("| --- | --- | --- | --- |")
        for condition, cdata in data["conditions"].items():
            metrics = []
            for name, stat in cdata["metrics"].items():
                if name in {
                    "geometry_action_r",
                    "label_geometry_gap",
                    "label_margin_lift",
                    "margin_auc",
                    "cue_specificity",
                    "raw_neighbor_precision",
                    "deformed_neighbor_precision",
                    "raw_value_margin",
                    "deformed_value_margin",
                    "deformed_precision_lift",
                    "random_precision_lift",
                    "deformed_margin_lift",
                    "random_margin_lift",
                    "template_transfer_auc",
                    "off_target_drift",
                    "collapse_index",
                    "elapsed_seconds",
                }:
                    metrics.append(f"{name}={_fmt(stat['mean'])}")
            status = "ok" if cdata.get("ok") else f"failed: {cdata.get('error', 'unknown')}"
            lines.append(f"| `{condition}` | `{cdata.get('model_id')}` | {status} | {'; '.join(metrics)} |")
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
