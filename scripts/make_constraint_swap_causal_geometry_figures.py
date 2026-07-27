#!/usr/bin/env python3
"""Build registered paper figures from the committed summary payload."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = (
    ROOT
    / "experiments"
    / "constraint_swap_causal_geometry"
    / "results"
    / "summary.json"
)
FIG_DIR = ROOT / "papers" / "constraint_swap_causal_geometry" / "figures"


def _setup() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 180,
            "savefig.dpi": 220,
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "axes.edgecolor": "#475569",
            "axes.grid": True,
            "grid.color": "#e2e8f0",
            "grid.linewidth": 0.7,
            "axes.axisbelow": True,
        }
    )


def _save(fig: Any, name: str) -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / name
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def figure_chain() -> Path:
    _setup()
    fig, ax = plt.subplots(figsize=(7.1, 2.7))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    boxes = [
        (0.03, 0.38, 0.22, "Hidden constraint\nA or B", "#dbeafe"),
        (0.39, 0.38, 0.22, "Reachability-aligned\nhidden geometry", "#ede9fe"),
        (0.75, 0.38, 0.22, "Constraint-consistent\nbehavior", "#dcfce7"),
    ]
    for x, y, width, text, color in boxes:
        patch = FancyBboxPatch(
            (x, y),
            width,
            0.28,
            boxstyle="round,pad=0.018",
            facecolor=color,
            edgecolor="#334155",
            linewidth=1.0,
        )
        ax.add_patch(patch)
        ax.text(x + width / 2, y + 0.14, text, ha="center", va="center", weight="bold")
    for start, end in ((0.25, 0.39), (0.61, 0.75)):
        ax.annotate(
            "",
            xy=(end, 0.52),
            xytext=(start, 0.52),
            arrowprops={"arrowstyle": "->", "lw": 1.8, "color": "#334155"},
        )
    ax.text(
        0.50,
        0.84,
        "Registered chain: both arrows had to pass",
        ha="center",
        va="center",
        fontsize=12,
        weight="bold",
        color="#0f172a",
    )
    ax.text(
        0.50,
        0.15,
        "Observed: behavior = 1.000, but active reachability geometry and targeted transport both failed",
        ha="center",
        va="center",
        color="#b91c1c",
        weight="bold",
    )
    return _save(fig, "fig1_registered_chain.png")


def _interval(summary: dict[str, Any], scope: str, metric: str) -> tuple[float, float, float]:
    row = summary[f"{scope}_intervals"][metric]
    return float(row["mean"]), float(row["lower"]), float(row["upper"])


def figure_geometry_swap(summary: dict[str, Any]) -> Path:
    _setup()
    metrics = [
        ("geometry_A_specific", "A geometry"),
        ("geometry_B_specific", "B geometry"),
        ("swap_tau_AB", "A->B swap"),
        ("swap_tau_BA", "B->A swap"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.25), sharey=True)
    for ax, scope, title in zip(
        axes,
        ("primary", "transfer"),
        ("6x6 torus", "Untouched 7x7 cylinder"),
        strict=True,
    ):
        means = []
        lower = []
        upper = []
        labels = []
        for metric, label in metrics:
            mean, lo, hi = _interval(summary, scope, metric)
            means.append(mean)
            lower.append(mean - lo)
            upper.append(hi - mean)
            labels.append(label)
        y = range(len(labels))
        ax.errorbar(
            means,
            list(y),
            xerr=[lower, upper],
            fmt="o",
            color="#b91c1c",
            ecolor="#ef4444",
            capsize=3,
            markersize=5,
        )
        ax.axvline(0, color="#334155", linewidth=1)
        ax.axvline(0.05, color="#2563eb", linewidth=1, linestyle="--", label="gate > .05")
        ax.set_yticks(list(y), labels)
        ax.invert_yaxis()
        ax.set_title(title)
        ax.set_xlabel("registered effect (90% bootstrap interval)")
        ax.set_xlim(-0.72, 0.18)
    axes[1].legend(loc="lower right", fontsize=7.5)
    fig.suptitle("Constraint-specific geometry and swap tracking had the wrong sign")
    return _save(fig, "fig2_geometry_swap.png")


def figure_interventions(summary: dict[str, Any]) -> Path:
    _setup()
    metrics = [
        ("undo_B_specific_harm", "Undo B"),
        ("undo_A_specific_harm", "Undo A"),
        ("rescue_B_specific_gain", "Impose B"),
        ("rescue_A_specific_gain", "Impose A"),
    ]
    fig, ax = plt.subplots(figsize=(6.8, 3.3))
    x = range(len(metrics))
    width = 0.36
    for offset, scope, color, label in (
        (-width / 2, "primary", "#2563eb", "torus"),
        (width / 2, "transfer", "#7c3aed", "cylinder"),
    ):
        means = [_interval(summary, scope, metric)[0] for metric, _ in metrics]
        lower = [
            means[index] - _interval(summary, scope, metric)[1]
            for index, (metric, _) in enumerate(metrics)
        ]
        upper = [
            _interval(summary, scope, metric)[2] - means[index]
            for index, (metric, _) in enumerate(metrics)
        ]
        ax.bar(
            [value + offset for value in x],
            means,
            width,
            color=color,
            label=label,
            yerr=[lower, upper],
            capsize=3,
        )
    ax.axhline(0, color="#334155", linewidth=1)
    ax.axhline(0.10, color="#16a34a", linewidth=1, linestyle="--", label="gate > .10")
    ax.set_xticks(list(x), [label for _, label in metrics])
    ax.set_ylabel("specific effect over strongest matched control")
    ax.set_title("Targeted latent transports did not beat matched controls")
    ax.legend(ncol=3, fontsize=7.8)
    return _save(fig, "fig3_interventions.png")


def figure_gates(summary: dict[str, Any]) -> Path:
    _setup()
    gates = summary["verdict"]["gates"]
    labels = list(gates)
    passed = [bool(gates[label]["pass"]) for label in labels]
    colors = ["#16a34a" if value else "#dc2626" for value in passed]
    fig, ax = plt.subplots(figsize=(7.0, 3.1))
    y = range(len(labels))
    ax.barh(list(y), [1] * len(labels), color=colors, height=0.64)
    ax.set_yticks(list(y), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.grid(False)
    for index, value in enumerate(passed):
        ax.text(
            0.5,
            index,
            "PASS" if value else "FAIL",
            ha="center",
            va="center",
            color="white",
            weight="bold",
        )
    ax.set_title("Noncompensatory verdict: upstream geometry failed")
    return _save(fig, "fig4_gates.png")


def main() -> int:
    payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    summary = payload["summary"]
    outputs = [
        figure_chain(),
        figure_geometry_swap(summary),
        figure_interventions(summary),
        figure_gates(summary),
    ]
    for output in outputs:
        print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
