#!/usr/bin/env python3
"""Generate figures for the Gauge-Fixed Concern Transport paper."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


LABELS = {
    "concern_weighted_ood": "Concern-weighted\nOOD",
    "causal_gauge_fixing": "Gauge\nfixing",
    "mechanistic_commitment": "Mechanistic\ncommitment",
    "reafference_null": "Reafference\nnull",
    "moved_bottleneck": "Moved\nbottleneck",
}


def _metric(summary: dict[str, Any], track: str, metric: str) -> float:
    return float(summary["by_track"][track]["metrics"][metric]["mean"])


def _save(fig: Any, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight", facecolor="white", dpi=220)
    plt.close(fig)
    return out


def _setup() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.edgecolor": "#374151",
            "axes.linewidth": 0.8,
            "xtick.color": "#374151",
            "ytick.color": "#374151",
            "axes.grid": True,
            "grid.color": "#e5e7eb",
            "grid.linewidth": 0.8,
        }
    )


def gate_status(summary: dict[str, Any], out: Path) -> Path:
    tracks = [track for track in summary["tracks"] if track in LABELS]
    vals = [1.0 if summary["gates"][track]["pass"] else 0.0 for track in tracks]
    fig, ax = plt.subplots(figsize=(6.6, 2.7))
    ax.barh([LABELS[t] for t in tracks], vals, color="#2b6cb0", height=0.64)
    ax.set_xlim(0, 1.1)
    ax.set_xlabel("pass = 1")
    ax.set_title("Modal L4 gate status across theorem obligations", weight="bold")
    ax.invert_yaxis()
    for i, value in enumerate(vals):
        ax.text(value + 0.03, i, "PASS" if value else "FAIL", va="center", fontsize=8)
    return _save(fig, out / "fig5_l4_gate_status.png")


def concern_ood(summary: dict[str, Any], out: Path) -> Path:
    raw = _metric(summary, "concern_weighted_ood", "raw_selector_weighted_error")
    concern = _metric(summary, "concern_weighted_ood", "concern_selector_weighted_error")
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    bars = ax.bar(["validation\nselector", "concern-weighted\nselector"], [raw, concern], color=["#9ca3af", "#2f9e44"])
    ax.set_ylabel("concern-weighted deployment error")
    ax.set_title("Concern weighting changes the selected hypothesis", weight="bold")
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.015, f"{bar.get_height():.3f}", ha="center", fontsize=8)
    return _save(fig, out / "fig6_concern_weighted_ood.png")


def gauge_fixing(summary: dict[str, Any], out: Path) -> Path:
    ungauge_align = _metric(summary, "causal_gauge_fixing", "ungauge_alignment")
    fixed_align = _metric(summary, "causal_gauge_fixing", "gauge_fixed_alignment")
    ungauge_ce = _metric(summary, "causal_gauge_fixing", "ungauge_commitment_effect")
    fixed_ce = _metric(summary, "causal_gauge_fixing", "gauge_fixed_commitment_effect")
    fig, ax = plt.subplots(figsize=(5.3, 3.0))
    x = [0, 1]
    width = 0.35
    ax.bar([v - width / 2 for v in x], [ungauge_align, ungauge_ce], width, label="ungauge-fixed", color="#9ca3af")
    ax.bar([v + width / 2 for v in x], [fixed_align, fixed_ce], width, label="gauge-fixed", color="#2b6cb0")
    ax.set_xticks(x)
    ax.set_xticklabels(["factor alignment", "commitment effect"])
    ax.set_ylim(0, 1.05)
    ax.set_title("Interventions fix the latent gauge", weight="bold")
    ax.legend(fontsize=8)
    return _save(fig, out / "fig7_gauge_fixing.png")


def probe_patch(summary: dict[str, Any], out: Path) -> Path:
    causal_auc = _metric(summary, "mechanistic_commitment", "causal_probe_auc")
    distractor_auc = _metric(summary, "mechanistic_commitment", "distractor_probe_auc")
    causal_effect = _metric(summary, "mechanistic_commitment", "causal_patch_effect")
    distractor_effect = _metric(summary, "mechanistic_commitment", "distractor_patch_effect")
    fig, ax1 = plt.subplots(figsize=(5.4, 3.1))
    ax2 = ax1.twinx()
    x = [0, 1]
    ax1.bar([v - 0.17 for v in x], [causal_auc, distractor_auc], 0.32, color="#60a5fa", label="probe AUC")
    ax2.bar([v + 0.17 for v in x], [causal_effect, distractor_effect], 0.32, color="#ef4444", label="patch effect")
    ax1.set_xticks(x)
    ax1.set_xticklabels(["causal feature", "decodable distractor"])
    ax1.set_ylim(0, 1.05)
    ax2.set_ylim(0, max(causal_effect, distractor_effect) * 1.25)
    ax1.set_ylabel("probe AUC")
    ax2.set_ylabel("commitment effect")
    ax1.set_title("Decodability and commitment effect diverge", weight="bold")
    ax1.grid(axis="y", visible=False)
    return _save(fig, out / "fig8_probe_vs_patch.png")


def reafference_bottleneck(summary: dict[str, Any], out: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.0))
    no_eff = _metric(summary, "reafference_null", "no_efference_auc")
    with_eff = _metric(summary, "reafference_null", "with_efference_auc")
    axes[0].bar(["no\nefference", "with\nefference"], [no_eff, with_eff], color=["#9ca3af", "#2b6cb0"])
    axes[0].set_ylim(0.5, 1.0)
    axes[0].set_ylabel("source-attribution AUC")
    axes[0].set_title("Self/world gauge fixing")

    early = _metric(summary, "moved_bottleneck", "early_patch_effect")
    active = _metric(summary, "moved_bottleneck", "active_bottleneck_patch_effect")
    inactive = _metric(summary, "moved_bottleneck", "inactive_bottleneck_patch_effect")
    axes[1].bar(["early", "active\nbottleneck", "inactive\ncontrol"], [early, active, inactive], color=["#9ca3af", "#2f9e44", "#ef4444"])
    axes[1].set_ylabel("commitment change")
    axes[1].set_title("Commitment locates memory")
    fig.subplots_adjust(top=0.84, wspace=0.35)
    return _save(fig, out / "fig9_reafference_and_bottleneck.png")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("papers/gauge_fixed_concern_transport/figures"))
    args = parser.parse_args()
    _setup()
    payload = json.loads(args.in_path.read_text())
    summary = payload["summary"]
    paths = [
        gate_status(summary, args.out_dir),
        concern_ood(summary, args.out_dir),
        gauge_fixing(summary, args.out_dir),
        probe_patch(summary, args.out_dir),
        reafference_bottleneck(summary, args.out_dir),
    ]
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
