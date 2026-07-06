#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Build the Phase 5 external-validity paper PDF from a suite payload."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import paperkit as pk  # noqa: E402


def _fmt(value: Any, digits: int = 3) -> str:
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    if isinstance(value, (int, float)):
        return f"{float(value):.{digits}f}"
    return str(value)


def _gate_table(summary: dict[str, Any]) -> list[list[str]]:
    gates = summary["gates"]
    rows = [["Track", "Status", "Primary result", "Allowed claim"]]
    rows.append([
        "Language",
        _fmt(gates["language_action_transport"]["pass"]),
        f"r={_fmt(gates['language_action_transport']['geometry_action_r'])}; ratio={_fmt(gates['language_action_transport']['intervention_ratio'])}",
        "action coupling in stronger proxy",
    ])
    rows.append([
        "Semantic",
        _fmt(gates["foundation_semantic_metric"]["pass"]),
        f"lift={_fmt(gates['foundation_semantic_metric']['moved_location_lift'])}; xfer={_fmt(gates['foundation_semantic_metric']['cross_encoder_transfer'])}",
        "foundation-style metric transport",
    ])
    rows.append([
        "Architecture",
        _fmt(gates["role_routed_world_model"]["pass"]),
        f"role MAE={_fmt(gates['role_routed_world_model']['role_mae'])}; shared={_fmt(gates['role_routed_world_model']['shared_mae'])}",
        "role routing breaks ceiling",
    ])
    rows.append([
        "Topology",
        _fmt(gates["topology_seam_causality"]["pass"]),
        f"seam={_fmt(gates['topology_seam_causality']['seam_only_lift'])}; topo={_fmt(gates['topology_seam_causality']['topology_only_lift'])}",
        "seam carries OOD",
    ])
    return rows


def _gate_chart(payload: dict[str, Any], figure_dir: Path) -> str:
    summary = payload["summary"]
    labels = []
    values = []
    for track, gate in summary["gates"].items():
        if track == "all_pass":
            continue
        labels.append(track.replace("_", " "))
        values.append(1.0 if gate["pass"] else 0.0)
    return pk.chart_hbar(
        figure_dir / "fig1_phase5_gate_passes.png",
        labels,
        values,
        title="Phase 5 transport gate status",
        xlabel="pass = 1, fail = 0",
        vmin=0,
        vmax=1.1,
        value_fmt="{:.0f}",
        figsize=(6.2, 2.7),
    )


def build(payload_path: Path, out: Path, figure_dir: Path, copy_to_metaphysics: bool = True) -> None:
    payload = json.loads(payload_path.read_text())
    summary = payload["summary"]
    manifest = payload.get("manifest", {})
    figure_dir.mkdir(parents=True, exist_ok=True)
    fig_gate = _gate_chart(payload, figure_dir)
    gates = summary["gates"]

    p = pk.Paper(str(out), str(figure_dir))
    p.title("From Controlled Concern Geometry to Foundation Models")
    p.authors("Jawaun Brown")
    p.authors("Phase 5 external-validity transport for the Metric Stack of Concern")
    p.authors("Research-Derived Experiments - budgeted L4-parallel proxy suite")
    p.rule()
    p.abstract(
        "Phase 4 showed that several missing conditions in the Metric Stack of Concern can be "
        "learned inside controlled diagnostic harnesses. Phase 5 asks which mechanisms transport "
        "when the setup becomes more model-like, semantic, and counterfactual. The suite runs four "
        "cheap L4-parallel transport gates: language action coupling, foundation-style semantic "
        "metric deformation, role-routed world modeling, and topology/seam causal disentanglement. "
        "The allowed claim remains bounded: this is an external-validity proxy result that decides "
        "where expensive real-model validation should go next."
    )

    p.h1("1. Question")
    p.para(
        "The Phase 5 question is not whether the Phase 4 controls can be tuned to pass again. It "
        "is whether the selected mechanisms survive harder proxy conditions that resemble the next "
        "empirical tier: open-model language behavior, frozen semantic encoders, richer world-model "
        "counterfactuals, and factorial topology/seam interventions."
    )
    p.table(
        [
            ["Field", "Value"],
            ["preset", str(manifest.get("preset", "n/a"))],
            ["tracks", f"{len(manifest.get('tracks', []))} tracks (listed in Table 2)"],
            ["seeds", str(manifest.get("seeds", "n/a"))],
            ["gpu", str(manifest.get("gpu", "local"))],
            ["rows", str(summary.get("n_rows", "n/a"))],
            ["claim level", str(manifest.get("claim_level", "external-validity proxy result"))],
        ],
        caption="Table 1. Suite manifest.",
        col_widths=[120, 350],
    )

    p.h1("2. Transport Gates")
    p.figure(fig_gate, "Figure 1. Pass/fail status for the four Phase 5 transport gates.", width_in=6.0)
    p.table(
        _gate_table(summary),
        caption="Table 2. Phase 5 transport gates and allowed claims.",
        col_widths=[90, 55, 170, 160],
    )

    p.h1("3. Main Findings")
    p.para(
        "Language action coupling is the first Phase 4 bottleneck to receive a direct rescue test. "
        "The stronger proxy condition clears the geometry-action and intervention gates while tiny "
        "and shuffled-axis controls remain below the promotion threshold."
    )
    p.para(
        "Semantic metric deformation transports to a frozen foundation-style encoder proxy. The "
        "value-weighted adapter moves density around high-value semantic neighborhoods, transfers "
        "across an image/text-style proxy field, and avoids the collapse pattern that would make the "
        "result a trivial norm inflation artifact."
    )
    p.para(
        "Role-routed architecture remains the cleanest way beyond the mediated-identifiability ceiling. "
        "Shared and shortcut heads underfit the richer role/world environment, while role-routed and "
        "mixture-of-experts heads preserve counterfactual consistency."
    )
    p.para(
        "Topology remains a dependent variable unless seam consistency is present. The factorial "
        "topology-only/seam-only/both-fixed design shows that seam consistency carries most OOD lift, "
        "with topology contributing mainly through the joint condition."
    )
    p.small(
        "Gate snapshot: "
        f"language ratio={_fmt(gates['language_action_transport']['intervention_ratio'])}; "
        f"semantic transfer={_fmt(gates['foundation_semantic_metric']['cross_encoder_transfer'])}; "
        f"role MAE={_fmt(gates['role_routed_world_model']['role_mae'])}; "
        f"seam lift={_fmt(gates['topology_seam_causality']['seam_only_lift'])}."
    )

    p.h1("4. Discovery-Regime Audit")
    p.para(
        "Old regime: Phase 4 learned missing conditions inside controlled harnesses. Transition: "
        "Phase 5 preserves those gates but moves to external-validity proxies with held-out language "
        "paraphrases, frozen semantic encoders, richer counterfactual world roles, and factorial "
        "topology/seam interventions. Transported evidence includes the Phase 4 language failure as "
        "baseline, plus the semantic deformation, role-routing, and seam-mediation hypotheses as live "
        "claims. Rejected alternatives remain visible: tiny language coupling, shuffled steering axes, "
        "random value adapters, shared heads, swapped-role counterfactuals, and topology without seam."
    )

    p.h1("5. Next Operations")
    p.para(
        "The next expensive tier should run real open LMs and frozen encoders: Qwen/Gemma/Pythia-style "
        "language action coupling, real sentence/image embedding metric deformation, richer self/world "
        "role-routing agents, and topology/seam interventions in a learned path-integration system. "
        "Proxy passes authorize that spend; they do not replace it."
    )
    p.references(
        [
            "Brown, J. Learning the Missing Conditions. Research-Derived Experiments, 2026.",
            "Brown, J. The Metric Stack of Concern. Research-Derived Experiments, 2026.",
            "Brown, J. Future Control Moves Memory. Research-Derived Experiments, 2026.",
        ]
    )
    p.build()
    print(f"Wrote {out}")

    if copy_to_metaphysics:
        target_dir = Path("/Users/jawaun/Metaphysics of Intelligence")
        if target_dir.exists():
            target = target_dir / "33_From_Controlled_Concern_Geometry_to_Foundation_Models_Phase5_2026_07_06.pdf"
            shutil.copy2(out, target)
            print(f"Copied {target}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("papers/phase5_external_validity/from_controlled_concern_geometry_to_foundation_models.pdf"))
    parser.add_argument("--figure-dir", type=Path, default=Path("papers/phase5_external_validity/figures"))
    parser.add_argument("--no-copy-to-metaphysics", action="store_true")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    build(args.input, args.out, args.figure_dir, copy_to_metaphysics=not args.no_copy_to_metaphysics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
