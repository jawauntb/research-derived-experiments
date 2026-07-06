#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Build the Phase 4 Metaphysics paper PDF from a suite payload."""

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
    rows = [["Track", "Status", "Primary result", "Claim level"]]
    rows.append([
        "Language",
        _fmt(gates["language_scale"]["pass"]),
        f"r={_fmt(gates['language_scale']['post_logprob_r'])}; ratio={_fmt(gates['language_scale']['intervention_ratio'])}",
        "mixed: predictive, not 3x causal",
    ])
    rows.append([
        "Symmetry",
        _fmt(gates["neural_symmetry"]["pass"]),
        f"F1={_fmt(gates['neural_symmetry']['closure_f1'])}; raw={_fmt(gates['neural_symmetry']['raw_f1'])}",
        "closure-constrained generator",
    ])
    rows.append([
        "Regimes",
        _fmt(gates["learned_regimes"]["pass"]),
        f"boundary={_fmt(gates['learned_regimes']['learned_boundary_accuracy'])}",
        "learned hard partition",
    ])
    rows.append([
        "Probe value",
        _fmt(gates["probe_value"]["pass"]),
        f"VOI red={_fmt(gates['probe_value']['learned_voi_reduction'])}",
        "marginal value beats error",
    ])
    rows.append([
        "Ceiling",
        _fmt(gates["beyond_ceiling"]["pass"]),
        f"role MAE={_fmt(gates['beyond_ceiling']['role_mae'])}",
        "role routing beats shared head",
    ])
    rows.append([
        "Metric",
        _fmt(gates["semantic_metric"]["pass"]),
        f"spec={_fmt(gates['semantic_metric']['specificity'])}",
        "controlled semantic deformation",
    ])
    rows.append([
        "Topology",
        _fmt(gates["topology_mediation"]["pass"]),
        f"seam r={_fmt(gates['topology_mediation']['seam_partial_with_topology'])}",
        "seam carries mediation",
    ])
    return rows


def _condition_chart(payload: dict[str, Any], figure_dir: Path) -> str:
    summary = payload["summary"]
    labels = []
    values = []
    for track, gate in summary["gates"].items():
        if track == "all_pass":
            continue
        labels.append(track.replace("_", " "))
        values.append(1.0 if gate["pass"] else 0.0)
    return pk.chart_hbar(
        figure_dir / "fig1_gate_passes.png",
        labels,
        values,
        title="Phase 4 gate status by track",
        xlabel="pass = 1, fail = 0",
        vmin=0,
        vmax=1.1,
        value_fmt="{:.0f}",
        figsize=(6.2, 3.4),
    )


def build(payload_path: Path, out: Path, figure_dir: Path, copy_to_metaphysics: bool = True) -> None:
    payload = json.loads(payload_path.read_text())
    summary = payload["summary"]
    manifest = payload.get("manifest", {})
    figure_dir.mkdir(parents=True, exist_ok=True)
    fig_gate = _condition_chart(payload, figure_dir)

    p = pk.Paper(str(out), str(figure_dir))
    p.title("Learning the Missing Conditions")
    p.authors("Jawaun Brown")
    p.authors("Phase 4 diagnostics for the Metric Stack of Concern")
    p.authors("Research-Derived Experiments - controlled L4-parallel harnesses")
    p.rule()
    p.abstract(
        "Phase 3 identified several open bottlenecks in the Metric Stack of Concern: "
        "language scale, non-enumerative symmetry discovery, learned regime variables, "
        "probe value, architecture beyond the mediated-identifiability ceiling, "
        "foundation-model-style metric deformation, and topology mediation. This paper "
        "reports a controlled Phase 4 diagnostic suite that turns those bottlenecks into "
        "seven cheap L4-parallel gates. The allowed claim is bounded: these experiments "
        "resolve mechanism choices inside controlled harnesses and identify which claims "
        "deserve heavier external validation."
    )

    p.h1("1. Question")
    p.para(
        "The Phase 4 question is whether the missing conditions from the prior arc can be "
        "learned rather than handed to the agent: regime partitions, marginal probe value, "
        "role-specific mediated structure, semantic metric allocation, and topology/seam "
        "factors. The suite is not a foundation-model claim; it is a mechanism-selection "
        "filter for the next, more expensive tier."
    )
    p.table(
        [
            ["Field", "Value"],
            ["preset", str(manifest.get("preset", "n/a"))],
            ["tracks", f"{len(manifest.get('tracks', []))} tracks (listed in Table 2)"],
            ["seeds", str(manifest.get("seeds", "n/a"))],
            ["gpu", str(manifest.get("gpu", "local"))],
            ["rows", str(summary.get("n_rows", "n/a"))],
            ["claim level", str(manifest.get("claim_level", "diagnostic controlled-harness result"))],
        ],
        caption="Table 1. Suite manifest.",
        col_widths=[120, 350],
    )

    p.h1("2. Gate Results")
    p.figure(fig_gate, "Figure 1. Pass/fail status for the seven Phase 4 gates.", width_in=6.0)
    p.table(
        _gate_table(summary),
        caption="Table 2. Phase 4 gates and allowed claims.",
        col_widths=[85, 55, 150, 180],
    )

    p.h1("3. Main Findings")
    gates = summary["gates"]
    p.para(
        "Language-scale diagnostics are mixed. Hidden paraphrase geometry predicts "
        "log-probability consistency in the large post-coupling condition, but the causal "
        "intervention ratio reaches only 2.36x against a 3x gate. The result supports a "
        "predictive scale signal while withholding the stronger causal-controller claim."
    )
    p.para(
        "Non-enumerative symmetry discovery improves when the generator is constrained by "
        "group closure. Raw neural proposal is not enough; closure and top-K selection are "
        "the load-bearing additions."
    )
    p.para(
        "The learned-regime gate confirms the Phase 3 diagnosis: smooth approximators can "
        "fail at singular boundaries, while a learned hard partition can close most of the "
        "oracle gap."
    )
    p.para(
        "The probe-value track separates current error from marginal information gain. A "
        "learned VOI score beats matched-random and current-error allocation, which is the "
        "mechanism needed for re-engagement without anxiety."
    )
    p.para(
        "The role-specific architecture track supports the architectural-ceiling reading: "
        "shared mediated heads fail, while disjoint per-role and mixture-style routing "
        "recover the mediated coefficients and wrong-history controls fail as they should."
    )
    p.para(
        "Semantic metric deformation and topology mediation both remain bounded. Value fields "
        "move metric density in the controlled semantic harness; topology mediates OOD only "
        "through seam consistency, so topology alone is not the causal story."
    )

    p.h1("4. Discovery-Regime Audit")
    p.para(
        "Old regime: Phase 3 could measure concern-like structure in minimal agents but left "
        "several variables oracle-specified or architecturally capped. Transition: Phase 4 "
        "adds learned regime gates, marginal probe-value targets, role-routed mediated heads, "
        "semantic-style metric deformation, and seam-aware topology mediation. Transported "
        "evidence: the null-anchor, current-replay, habituation, role-specific ceiling, and "
        "metric-deformation claims are preserved as baselines. Rejected alternatives remain "
        "visible: raw neural symmetry proposal, current-error probe value, smooth boundary "
        "heads, shared mediated heads, and topology without seam consistency."
    )

    p.h1("5. Next Operations")
    p.para(
        "The next tier should spend expensive compute only on tracks that passed these gates: "
        "larger real language models for paraphrase action coupling, learned closure-constrained "
        "transform generators, learned regime variables in richer homeostatic environments, "
        "true VOI probes under regime shifts, role-routed self/world heads, and foundation-model "
        "semantic metric deformation. Failed or bounded tracks should be carried forward as "
        "controls, not erased."
    )
    p.references(
        [
            "Brown, J. The Metric Stack of Concern. Research-Derived Experiments, 2026.",
            "Brown, J. Weakness, Not Compression. Research-Derived Experiments, 2026.",
            "Brown, J. Future Control Moves Memory. Research-Derived Experiments, 2026.",
        ]
    )
    p.build()
    print(f"Wrote {out}")

    if copy_to_metaphysics:
        target_dir = Path("/Users/jawaun/Metaphysics of Intelligence")
        if target_dir.exists():
            target = target_dir / "32_Learning_the_Missing_Conditions_Phase4_2026_07_06.pdf"
            shutil.copy2(out, target)
            print(f"Copied {target}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("papers/phase4_metaphysics/learning_missing_conditions.pdf"))
    parser.add_argument("--figure-dir", type=Path, default=Path("papers/phase4_metaphysics/figures"))
    parser.add_argument("--no-copy-to-metaphysics", action="store_true")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    build(args.input, args.out, args.figure_dir, copy_to_metaphysics=not args.no_copy_to_metaphysics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
