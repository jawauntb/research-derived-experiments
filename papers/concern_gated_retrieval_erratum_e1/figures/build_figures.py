#!/usr/bin/env python3
"""Erratum E1 figure: the leak, and the repair that closes it.

Numbers hardcoded from ``erratum_e1/results/erratum_receipt.json`` (300
episodes per family, k=4, 2026-07-24).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

DITHER_PALETTE = ["#111827", "#F97316", "#22D3EE", "#A78BFA", "#F5F5F4", "#84CC16", "#EF4444"]
HATCHES = ["///", "\\\\\\", "xxx", "...", "ooo"]
FIG_SIZE, FIG_DPI = (8, 5), 200
OUT_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str
    fg: str
    muted: str


DARK = Theme("dark", "#0E0E0F", "#F5F5F4", "#4B5563")
LIGHT = Theme("light", "#FAF7F0", "#0E0E0F", "#9CA3AF")

FAMILIES = [
    "wave0/\ndelayed",
    "wave0/\nmaintenance",
    "wave1b/\ndelayed_v2",
    "wave1b/\nmaintenance_v2",
]
BEFORE = [1.0000, 1.0000, 1.0000, 1.0000]
AFTER = [0.0633, 0.1867, 0.3767, 0.3000]
THRESHOLD = 0.8


def build(theme: Theme) -> str:
    plt.rcParams["font.family"] = "monospace"
    fig, ax = plt.subplots(figsize=FIG_SIZE)
    fig.patch.set_facecolor(theme.bg)
    ax.set_facecolor(theme.bg)
    for spine in ax.spines.values():
        spine.set_edgecolor(theme.fg)
    ax.tick_params(colors=theme.fg, labelsize=8)
    ax.yaxis.label.set_color(theme.fg)

    x = np.arange(len(FAMILIES), dtype=float)
    w = 0.36
    ax.bar(x - w / 2, BEFORE, w, label="before (frozen fixture)",
           color=DITHER_PALETTE[6], edgecolor=theme.fg, hatch=HATCHES[0], alpha=0.92)
    ax.bar(x + w / 2, AFTER, w, label="after repair (k=4)",
           color=DITHER_PALETTE[5], edgecolor=theme.fg, hatch=HATCHES[2], alpha=0.92)

    ax.axhline(THRESHOLD, color=DITHER_PALETTE[1], linestyle="--", linewidth=1.4)
    ax.text(len(FAMILIES) - 0.5, THRESHOLD + 0.02, "leak threshold 0.80",
            color=DITHER_PALETTE[1], fontsize=8, ha="right")
    ax.axhline(0.25, color=theme.muted, linestyle=":", linewidth=1.0)
    ax.text(-0.45, 0.27, "ideal 1/k = 0.25", color=theme.muted, fontsize=7)

    for xi, v in zip(x, BEFORE):
        ax.text(xi - w / 2, v + 0.02, "1.000", ha="center", color=DITHER_PALETTE[6],
                fontsize=8, weight="bold")
    for xi, v in zip(x, AFTER):
        ax.text(xi + w / 2, v + 0.02, f"{v:.3f}", ha="center", color=DITHER_PALETTE[5],
                fontsize=8, weight="bold")

    ax.set_xticks(list(x))
    ax.set_xticklabels(FAMILIES, fontsize=8)
    ax.set_ylabel("hit@1 of ascending-concern (one-line policy)")
    ax.set_ylim(0, 1.15)
    leg = ax.legend(frameon=True, facecolor=theme.bg, edgecolor=theme.fg,
                    labelcolor=theme.fg, fontsize=8, loc="upper center")
    for t in leg.get_texts():
        t.set_fontfamily("monospace")

    ax.set_title("ERRATUM E1 - THE CONCERN PRIOR IS AN INVERTED ORACLE",
                 color=theme.fg, fontsize=11, loc="left", pad=18)
    ax.text(0.0, 1.015, "sorting candidates by ASCENDING care_anchors identified the answer every time",
            transform=ax.transAxes, color=theme.muted, fontsize=8, va="bottom")
    fig.text(0.01, 0.01, "300 episodes/family | frozen packages unedited | repair suppresses a set of k=4",
             color=theme.muted, fontsize=7)

    fig.tight_layout()
    name = f"fig1_erratum_leak_{theme.name}.png"
    fig.savefig(OUT_DIR / name, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    return name


def main() -> None:
    for theme in (DARK, LIGHT):
        print(f"  - {build(theme)}")


if __name__ == "__main__":
    main()
