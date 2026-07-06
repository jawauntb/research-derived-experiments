#!/usr/bin/env python3
"""Figures for the long-horizon moved-bottleneck paper."""

from __future__ import annotations

from pathlib import Path
from textwrap import fill

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "papers" / "long_horizon_bottleneck" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update(
    {
        "font.size": 10.5,
        "axes.titlesize": 12,
        "axes.labelsize": 10.5,
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "legend.fontsize": 9.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def fig1_commitment_surface_ladder() -> None:
    """Evidence ladder from final behavior to action-surface causal leverage."""
    rows = [
        (
            "Final behavior",
            "Delayed answer accuracy reaches 1.000 in synthetic L4 sweeps.",
            "necessary, weak",
            "#dbeafe",
        ),
        (
            "Moved memory metric",
            "Critical-slot hidden-state sensitivity moves with the registered slot.",
            "hidden transport",
            "#d1fae5",
        ),
        (
            "Tool commitment",
            "Slot/value commitments survive external handoff, repair, no-op, and aliases.",
            "action surface",
            "#fef3c7",
        ),
        (
            "Generated JSON",
            "Structured and autoregressive JSON actions preserve parser-scored behavior.",
            "interface hardening",
            "#fde68a",
        ),
        (
            "Hidden localization",
            "Generated-action and fixed-action sites pass; one prompt-final site fails.",
            "where it lives",
            "#dcfce7",
        ),
        (
            "Causal patch",
            "Value-prefix hidden states shift the next JSON value readout.",
            "causal leverage",
            "#bbf7d0",
        ),
        (
            "Black-box API",
            "Gemini Flash-Lite passes prompt-family and external-stress behavior.",
            "behavioral bridge",
            "#e9d5ff",
        ),
    ]

    fig, ax = plt.subplots(figsize=(13.5, 7.6))
    ax.set_xlim(0, 14)
    ax.set_ylim(-0.2, len(rows) + 1.55)
    ax.axis("off")

    ax.text(
        7,
        len(rows) + 1.15,
        "Figure 1. Commitment-surface evidence ladder",
        ha="center",
        fontsize=14,
        fontweight="bold",
    )
    ax.text(
        7,
        len(rows) + 0.78,
        "The claim strengthens as evidence moves from final behavior to memory transport, action commitment, and causal readout.",
        ha="center",
        fontsize=10,
        color="#444",
        style="italic",
    )

    x0, w0 = 0.35, 3.0
    x1, w1 = 3.75, 6.3
    x2, w2 = 10.55, 2.9
    for x, w, title, color in [
        (x0, w0, "Evidence surface", "#e5e7eb"),
        (x1, w1, "What passed or failed", "#e5e7eb"),
        (x2, w2, "Claim type", "#e5e7eb"),
    ]:
        box = FancyBboxPatch(
            (x, len(rows) + 0.1),
            w,
            0.44,
            boxstyle="round,pad=0.035",
            facecolor=color,
            edgecolor="#555",
            linewidth=0.9,
        )
        ax.add_patch(box)
        ax.text(x + w / 2, len(rows) + 0.32, title, ha="center", va="center", fontweight="bold")

    for idx, (surface, evidence, claim, color) in enumerate(rows):
        y = len(rows) - idx - 0.62
        stripe = "#ffffff" if idx % 2 == 0 else "#f8fafc"
        ax.add_patch(
            patches.Rectangle(
                (0.15, y - 0.39),
                13.65,
                0.78,
                facecolor=stripe,
                edgecolor="#e5e7eb",
                linewidth=0.6,
            )
        )
        ax.add_patch(
            FancyBboxPatch(
                (x0, y - 0.28),
                w0,
                0.56,
                boxstyle="round,pad=0.03",
                facecolor=color,
                edgecolor="#cbd5e1",
                linewidth=0.7,
            )
        )
        ax.add_patch(
            patches.Rectangle(
                (x1, y - 0.28),
                w1,
                0.56,
                facecolor="#f8fafc",
                edgecolor="#e5e7eb",
                linewidth=0.7,
            )
        )
        ax.add_patch(
            FancyBboxPatch(
                (x2, y - 0.28),
                w2,
                0.56,
                boxstyle="round,pad=0.03",
                facecolor="#f1f5f9",
                edgecolor="#cbd5e1",
                linewidth=0.7,
            )
        )
        ax.text(x0 + 0.18, y, fill(surface, 22), ha="left", va="center", fontweight="bold", color="#0f172a")
        ax.text(x1 + 0.18, y, fill(evidence, 64), ha="left", va="center", color="#1f2937")
        ax.text(x2 + w2 / 2, y, fill(claim, 18), ha="center", va="center", fontweight="bold", color="#334155")
        if idx < len(rows) - 1:
            ax.annotate(
                "",
                xy=(1.85, y - 0.45),
                xytext=(1.85, y - 0.29),
                arrowprops=dict(arrowstyle="->", color="#64748b", lw=1.0),
            )

    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig1_commitment_surface_ladder.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {FIG_DIR}/fig1_commitment_surface_ladder.png")


def main() -> None:
    fig1_commitment_surface_ladder()


if __name__ == "__main__":
    main()
