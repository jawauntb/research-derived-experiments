#!/usr/bin/env python3
"""Dither-styled figures for the MX1 de-risk probe paper.

Numbers are hardcoded from ``mx1_repair_prior/results/mx1_verdict.json`` (600
episodes, 2026-07-24) so the figure build never silently drifts from the
receipt. Emits dark/light PNG pairs at 8x5in @ 200dpi, matching the palette
used by the Wave 0/1a/1b/synthesis figure scripts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402


DITHER_PALETTE: list[str] = [
    "#111827",
    "#F97316",
    "#22D3EE",
    "#A78BFA",
    "#F5F5F4",
    "#84CC16",
    "#EF4444",
]
HATCHES: list[str] = ["///", "\\\\\\", "xxx", "...", "ooo", "|||", "---"]

DARK_BG, DARK_FG, DARK_MUTED = "#0E0E0F", "#F5F5F4", "#4B5563"
LIGHT_BG, LIGHT_FG, LIGHT_MUTED = "#FAF7F0", "#0E0E0F", "#9CA3AF"
FIG_SIZE, FIG_DPI = (8, 5), 200

OUT_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str
    fg: str
    muted: str


DARK = Theme("dark", DARK_BG, DARK_FG, DARK_MUTED)
LIGHT = Theme("light", LIGHT_BG, LIGHT_FG, LIGHT_MUTED)


def _set_font_defaults() -> None:
    plt.rcParams["font.family"] = "monospace"


def _title_case(text: str) -> str:
    return text.upper()


def _apply_theme(fig: Figure, ax: Axes, theme: Theme) -> None:
    fig.patch.set_facecolor(theme.bg)
    ax.set_facecolor(theme.bg)
    for spine in ax.spines.values():
        spine.set_edgecolor(theme.fg)
        spine.set_linewidth(1.0)
    ax.tick_params(colors=theme.fg, labelsize=9)
    ax.xaxis.label.set_color(theme.fg)
    ax.yaxis.label.set_color(theme.fg)


def _stamp_title(ax: Axes, title: str, subtitle: str | None, theme: Theme) -> None:
    ax.set_title(_title_case(title), color=theme.fg, fontsize=12, loc="left", pad=18)
    if subtitle:
        ax.text(
            0.0,
            1.015,
            subtitle,
            transform=ax.transAxes,
            color=theme.muted,
            fontsize=8,
            va="bottom",
            ha="left",
            family="monospace",
        )


def _footer(fig: Figure, text: str, theme: Theme) -> None:
    fig.text(0.01, 0.01, text, color=theme.muted, fontsize=7, ha="left", va="bottom")


def _save(fig: Figure, stem: str, theme: Theme) -> str:
    name = f"{stem}_{theme.name}.png"
    fig.savefig(OUT_DIR / name, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    return name


# --------------------------------------------------------------------------- #
# fig1 - design and verdicts
# --------------------------------------------------------------------------- #


def fig1(theme: Theme) -> str:
    fig, ax = plt.subplots(figsize=FIG_SIZE)
    _apply_theme(fig, ax, theme)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    panels = [
        (
            0.3,
            "PART A\nrepair-guided\nexploration",
            "retain a failed pick,\nre-pair it",
            "NO_GO",
            DITHER_PALETTE[6],
        ),
        (
            5.2,
            "PART B\nverifier-fault\nsplit",
            "decline when the marginal\nmodel is out of competence",
            "GO",
            DITHER_PALETTE[5],
        ),
    ]
    for x, head, body, verdict, colour in panels:
        ax.add_patch(
            FancyBboxPatch(
                (x, 1.2),
                4.5,
                3.6,
                boxstyle="round,pad=0.12",
                facecolor=theme.bg,
                edgecolor=colour,
                linewidth=2.0,
            )
        )
        ax.text(x + 2.25, 4.25, head, ha="center", va="center", color=theme.fg, fontsize=11, weight="bold")
        ax.text(x + 2.25, 2.95, body, ha="center", va="center", color=theme.muted, fontsize=8)
        ax.text(x + 2.25, 1.75, verdict, ha="center", va="center", color=colour, fontsize=20, weight="bold")

    ax.text(
        5.0,
        0.55,
        "overall: PARTIAL_GO_B_ONLY  ->  licenses verifier redesign only",
        ha="center",
        color=theme.fg,
        fontsize=9,
    )
    _stamp_title(ax, "MX1 - two transfers, tested separately", "600 episodes | delayed_commitments_v2 | local CPU | $0", theme)
    _footer(fig, "COGR MX1 de-risk probe | frozen preregistration | 2026-07-24", theme)
    fig.tight_layout()
    return _save(fig, "fig1_mx1_design", theme)


# --------------------------------------------------------------------------- #
# fig2 - Part A
# --------------------------------------------------------------------------- #


def fig2(theme: Theme) -> str:
    fig, ax = plt.subplots(figsize=FIG_SIZE)
    _apply_theme(fig, ax, theme)

    groups = ["all 600", "with pair (109)", "without pair (491)"]
    concern = [2.933, 2.862, 2.949]
    random_ = [2.975, 2.991, 2.971]
    repair = [3.218, 3.101, 3.244]

    x = np.arange(len(groups), dtype=float)
    w = 0.26
    ax.bar(x - w, concern, w, label="concern_sequential", color=DITHER_PALETTE[2],
           edgecolor=theme.fg, hatch=HATCHES[0], alpha=0.9)
    ax.bar(x, random_, w, label="random_sequential", color=DITHER_PALETTE[3],
           edgecolor=theme.fg, hatch=HATCHES[2], alpha=0.9)
    ax.bar(x + w, repair, w, label="repair_guided", color=DITHER_PALETTE[6],
           edgecolor=theme.fg, hatch=HATCHES[1], alpha=0.9)

    ax.set_xticks(list(x))
    ax.set_xticklabels(groups)
    ax.set_ylabel("mean attempts to success (lower is better)")
    ax.set_ylim(2.5, 3.45)
    leg = ax.legend(frameon=True, facecolor=theme.bg, edgecolor=theme.fg,
                    labelcolor=theme.fg, fontsize=8, loc="upper left")
    for txt in leg.get_texts():
        txt.set_fontfamily("monospace")

    ax.text(1.0, 3.40, "repair_guided loses EVEN where the pair exists",
            ha="center", color=DITHER_PALETTE[6], fontsize=9, weight="bold")

    _stamp_title(ax, "Part A - NO_GO", "both CIs exclude 0 in the wrong direction: +0.285 vs concern, +0.243 vs random", theme)
    _footer(fig, "diagnostic split reported, not used to move the frozen verdict", theme)
    fig.tight_layout()
    return _save(fig, "fig2_part_a_results", theme)


# --------------------------------------------------------------------------- #
# fig3 - Part B
# --------------------------------------------------------------------------- #


def fig3(theme: Theme) -> str:
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=FIG_SIZE)
    for a in (ax, ax2):
        _apply_theme(fig, a, theme)

    ax.bar(["marginal", "split"], [109, 0], color=[DITHER_PALETTE[6], DITHER_PALETTE[5]],
           edgecolor=theme.fg, hatch=HATCHES[0], alpha=0.9)
    ax.set_ylabel("useful pairs mislabeled useless")
    ax.set_ylim(0, 125)
    ax.text(0, 112, "109 / 109", ha="center", color=DITHER_PALETTE[6], fontsize=11, weight="bold")
    ax.text(1, 8, "0", ha="center", color=DITHER_PALETTE[5], fontsize=11, weight="bold")
    _stamp_title(ax, "mislabeling", "lower is better", theme)

    ax2.bar(["false declines"], [0], color=DITHER_PALETTE[5], edgecolor=theme.fg,
            hatch=HATCHES[2], alpha=0.9)
    ax2.set_ylim(0, 10)
    ax2.set_ylabel("false VERIFIER_FAULT")
    ax2.text(0, 4.5, "0 / 6920\nprecision 1.0", ha="center", color=DITHER_PALETTE[5],
             fontsize=11, weight="bold")
    _stamp_title(ax2, "singleton controls", "the split never over-declines", theme)

    _footer(fig, "Part B - GO | both frozen conditions met", theme)
    fig.tight_layout()
    return _save(fig, "fig3_part_b_results", theme)


def main() -> None:
    _set_font_defaults()
    written: list[str] = []
    for theme in (DARK, LIGHT):
        written.append(fig1(theme))
        written.append(fig2(theme))
        written.append(fig3(theme))
    print(f"[cogr-mx1] wrote {len(written)} figures to {OUT_DIR}")
    for name in written:
        print(f"  - {name}")


if __name__ == "__main__":
    main()
