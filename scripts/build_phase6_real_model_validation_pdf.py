#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Build the Phase 6 real-model validation paper PDF from a suite payload."""

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
        figure_dir / "fig1_phase6_gate_passes.png",
        labels,
        values,
        title="Phase 6 real-model validation gate status",
        xlabel="pass = 1, fail = 0",
        vmin=0,
        vmax=1.1,
        value_fmt="{:.0f}",
        figsize=(6.4, 2.4),
    )


def _gate_table(summary: dict[str, Any]) -> list[list[str]]:
    gates = summary["gates"]
    lm = gates.get("open_lm_action_coupling", {})
    enc = gates.get("frozen_encoder_metric_deformation", {})
    rows = [["Track", "Status", "Primary result", "Allowed claim"]]
    if lm:
        rows.append([
            "Open LMs",
            _fmt(lm["pass"]),
            f"models={_fmt(lm['ok_models'], 0)}; r={_fmt(lm['geometry_action_r'])}; lift={_fmt(lm['label_margin_lift'])}; AUC={_fmt(lm['margin_auc'])}",
            "LM text signal",
        ])
    if enc:
        rows.append([
            "Frozen encoders",
            _fmt(enc["pass"]),
            f"margin lift={_fmt(enc['deformed_margin_lift'])}; random={_fmt(enc['random_margin_lift'])}; AUC={_fmt(enc['template_transfer_auc'])}",
            "metric margin",
        ])
    return rows


def _short_name(condition: str) -> str:
    names = {
        "all_minilm_l6_v2": "MiniLM-L6",
        "bge_small_en_v1_5": "BGE-small",
        "distilgpt2": "DistilGPT2",
        "pythia_70m": "Pythia-70M",
        "qwen2_0_5b_instruct": "Qwen2.5-0.5B",
    }
    return names.get(condition, condition)


def _metric(cdata: dict[str, Any], metric: str) -> str:
    if metric not in cdata["metrics"]:
        return "n/a"
    return _fmt(cdata["metrics"][metric]["mean"])


def _lm_rows(summary: dict[str, Any]) -> list[list[str]]:
    rows = [["LM", "r", "gap", "lift", "AUC", "cue"]]
    for condition, cdata in summary["by_track"].get("open_lm_action_coupling", {}).get("conditions", {}).items():
        rows.append([
            _short_name(condition),
            _metric(cdata, "geometry_action_r"),
            _metric(cdata, "label_geometry_gap"),
            _metric(cdata, "label_margin_lift"),
            _metric(cdata, "margin_auc"),
            _metric(cdata, "cue_specificity"),
        ])
    return rows


def _encoder_rows(summary: dict[str, Any]) -> list[list[str]]:
    rows = [["Encoder", "raw P", "def P", "m-lift", "rand", "AUC", "drift"]]
    for condition, cdata in summary["by_track"].get("frozen_encoder_metric_deformation", {}).get("conditions", {}).items():
        rows.append([
            _short_name(condition),
            _metric(cdata, "raw_neighbor_precision"),
            _metric(cdata, "deformed_neighbor_precision"),
            _metric(cdata, "deformed_margin_lift"),
            _metric(cdata, "random_margin_lift"),
            _metric(cdata, "template_transfer_auc"),
            _metric(cdata, "off_target_drift"),
        ])
    return rows


def build(payload_path: Path, out: Path, figure_dir: Path, copy_to_metaphysics: bool = True) -> None:
    payload = json.loads(payload_path.read_text())
    summary = payload["summary"]
    manifest = payload.get("manifest", {})
    figure_dir.mkdir(parents=True, exist_ok=True)
    fig_gate = _gate_chart(payload, figure_dir)
    gates = summary["gates"]

    p = pk.Paper(str(out), str(figure_dir))
    p.title("From Proxy Transport to Open Models")
    p.authors("Jawaun Brown")
    p.authors("Phase 6 actual-model validation for the Metric Stack of Concern")
    p.authors("Research-Derived Experiments - budgeted Modal L4 sweep")
    p.rule()
    p.abstract(
        "Phase 5 used proxy harnesses to decide whether expensive validation was warranted. "
        "Phase 6 runs that heavier tier directly: public decoder language models are scored by "
        "hidden-state geometry and action logprob margins, while public frozen sentence encoders "
        "are tested with a post-hoc value-weighted metric deformation. The result is deliberately "
        "bounded. It is actual open-model evidence, not human behavioral evidence or foundation-"
        "model finetuning evidence."
    )

    p.h1("1. Question")
    p.para(
        "The question is whether the Phase 5 proxy transport signals survive contact with actual "
        "open LMs and frozen encoders. For language, the validation asks whether a hidden concern "
        "axis predicts held-out help-versus-wait logprob margins and whether concern cues move "
        "those margins more than matched controls. For encoders, it asks whether a value direction "
        "trained from template-A text improves held-out value-neighbor retrieval without random-"
        "label lift or off-target collapse."
    )
    p.table(
        [
            ["preset", str(manifest.get("preset", "n/a"))],
            ["models", f"{len(manifest.get('models', []))} public HF models"],
            ["gpu", str(manifest.get("gpu", "local"))],
            ["rows", str(summary.get("n_rows", "n/a"))],
            ["claim level", str(manifest.get("claim_level", "actual open-model validation result"))],
        ],
        caption="Table 1. Suite manifest.",
        col_widths=[100, 380],
    )

    p.h1("2. Real-Model Gates")
    p.figure(fig_gate, "Figure 1. Pass/fail status for Phase 6 real-model validation gates.", width_in=6.0)
    p.table(
        _gate_table(summary),
        caption="Table 2. Phase 6 validation gates and allowed claims.",
        col_widths=[95, 55, 250, 100],
    )

    p.h1("3. Open Language Models")
    p.para(
        "Each decoder LM is treated as a frozen measurement instrument. The suite builds a concern "
        "axis from train prompts, evaluates held-out prompts, and scores the average logprob margin "
        "between help and wait continuations. This tests text-model coupling only: a positive result "
        "means the open LM's hidden states and next-token distribution carry the measured concern "
        "signal, not that the model would act in the world."
    )
    p.table(
        _lm_rows(summary),
        caption="Table 3. Public decoder-LM hidden geometry and logprob results.",
        col_widths=[115, 55, 55, 55, 55, 55],
    )

    p.h1("4. Frozen Encoders")
    p.para(
        "Each sentence encoder is frozen. The suite estimates a value direction from training "
        "phrases, then deforms held-out retrieval with a positive value-kernel term. The control is "
        "the same deformation after randomizing value scores. This isolates whether the metric "
        "story survives real encoder embeddings, not whether the encoder learned concern."
    )
    p.table(
        _encoder_rows(summary),
        caption="Table 4. Public frozen-encoder metric deformation results.",
        col_widths=[115, 55, 55, 55, 55, 55, 55],
    )

    p.h1("5. Interpretation")
    p.para(
        "The strictest interpretation is operational. Passing gates promote the relevant mechanism "
        "from proxy-compatible to actual-model-compatible. Failing or weak gates demote that path "
        "back to hypothesis status while preserving the exact model rows as future baselines."
    )
    p.small(
        "Gate snapshot: "
        f"language pass={_fmt(gates.get('open_lm_action_coupling', {}).get('pass', False))}; "
        f"encoder pass={_fmt(gates.get('frozen_encoder_metric_deformation', {}).get('pass', False))}; "
        f"overall={_fmt(gates.get('all_pass', False))}."
    )

    p.h1("6. Discovery-Regime Audit")
    p.para(
        "Old regime: Phase 5 proxy transport. Transition: public model weights replace proxy "
        "weights while preserving predeclared controls, budget caps, and archiveable artifacts. "
        "Promoted evidence is restricted to actual open-model logprob/hidden-state measurements "
        "and frozen-encoder metric deformation. Rejected alternatives remain explicit: random "
        "deformation, weak cue specificity, off-target drift, and model-loading failures."
    )
    p.references(
        [
            "Brown, J. From Controlled Concern Geometry to Foundation Models. Research-Derived Experiments, 2026.",
            "Brown, J. Learning the Missing Conditions. Research-Derived Experiments, 2026.",
            "Hugging Face model cards for distilgpt2, EleutherAI/pythia-70m-deduped, Qwen/Qwen2.5-0.5B-Instruct, all-MiniLM-L6-v2, and BAAI/bge-small-en-v1.5.",
        ]
    )
    p.build()
    print(f"Wrote {out}")

    if copy_to_metaphysics:
        target_dir = Path("/Users/jawaun/Metaphysics of Intelligence")
        if target_dir.exists():
            target = target_dir / "34_From_Proxy_Transport_to_Open_Models_Phase6_2026_07_06.pdf"
            shutil.copy2(out, target)
            print(f"Copied {target}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("papers/phase6_real_model_validation/from_proxy_transport_to_open_models.pdf"))
    parser.add_argument("--figure-dir", type=Path, default=Path("papers/phase6_real_model_validation/figures"))
    parser.add_argument("--no-copy-to-metaphysics", action="store_true")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    build(args.input, args.out, args.figure_dir, copy_to_metaphysics=not args.no_copy_to_metaphysics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
