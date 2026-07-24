#!/usr/bin/env python3
"""DR1 figures. Numbers hardcoded from results/dr1_verdict.json (2026-07-24)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

PAL = ["#111827", "#F97316", "#22D3EE", "#A78BFA", "#F5F5F4", "#84CC16", "#EF4444"]
HATCH = ["///", "\\\\\\", "xxx", "...", "ooo"]
FIG_SIZE, DPI = (8, 5), 200
OUT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str
    fg: str
    muted: str


DARK = Theme("dark", "#0E0E0F", "#F5F5F4", "#4B5563")
LIGHT = Theme("light", "#FAF7F0", "#0E0E0F", "#9CA3AF")


def _prep(th: Theme, ncols: int = 1):
    plt.rcParams["font.family"] = "monospace"
    fig, axes = plt.subplots(1, ncols, figsize=FIG_SIZE)
    fig.patch.set_facecolor(th.bg)
    for ax in (axes if ncols > 1 else [axes]):
        ax.set_facecolor(th.bg)
        for sp in ax.spines.values():
            sp.set_edgecolor(th.fg)
        ax.tick_params(colors=th.fg, labelsize=8)
        ax.yaxis.label.set_color(th.fg)
    return fig, axes


def _save(fig, stem: str, th: Theme) -> str:
    name = f"{stem}_{th.name}.png"
    fig.savefig(OUT / name, dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    return name


def fig1(th: Theme) -> str:
    fig, ax = _prep(th)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    panels = [
        (0.3, "TK - kinematics", "alpha cannot tell\nGalilean from Lorentz",
         "weakness 1.00\ncost 0.00 (SILENT)", PAL[2]),
        (5.2, "TT - transduction", "depth budget, not\nexpressivity",
         "cost 1.00\nweakness 0.67", PAL[5]),
    ]
    for x, head, body, res, col in panels:
        ax.add_patch(FancyBboxPatch((x, 1.2), 4.5, 3.6, boxstyle="round,pad=0.12",
                                    facecolor=th.bg, edgecolor=col, linewidth=2.0))
        ax.text(x + 2.25, 4.3, head, ha="center", color=th.fg, fontsize=12, weight="bold")
        ax.text(x + 2.25, 3.3, body, ha="center", color=th.muted, fontsize=8)
        ax.text(x + 2.25, 2.0, res, ha="center", color=col, fontsize=10, weight="bold")
    ax.text(5.0, 0.5, "each nominator wins on one toy and loses on the other",
            ha="center", color=th.fg, fontsize=9)
    ax.set_title("DR1 - TWO DISCOVERY SHAPES, ONE HARNESS", color=th.fg,
                 fontsize=12, loc="left", pad=18)
    ax.text(0.0, 1.015, "H1 and H2 both NO_GO | the graded claim survives, the binary one does not",
            transform=ax.transAxes, color=th.muted, fontsize=8, va="bottom")
    fig.tight_layout()
    return _save(fig, "fig1_dr1_design", th)


def fig2(th: Theme) -> str:
    fig, (a1, a2) = _prep(th, 2)
    noms = ["weakness", "cost", "disjunctive", "random", "size_only"]
    tk = [1.00, 0.00, 1.00, 0.00, 0.00]
    tt = [0.67, 1.00, 0.67, 0.67, 0.67]
    cols = [PAL[2], PAL[5], PAL[3], th.muted, th.muted]
    for ax, vals, title, sub in (
        (a1, tk, "toy_kinematics", "1 of 21 load-bearing"),
        (a2, tt, "toy_transduction", "4 of 10 -- weak test"),
    ):
        y = np.arange(len(noms), dtype=float)
        ax.barh(y, vals, color=cols, edgecolor=th.fg, hatch=HATCH[0], alpha=0.92)
        ax.set_yticks(list(y))
        ax.set_yticklabels(noms, fontsize=8)
        ax.invert_yaxis()
        ax.set_xlim(0, 1.15)
        ax.set_xlabel("recall@3", color=th.fg, fontsize=8)
        for yi, v in zip(y, vals):
            ax.text(v + 0.03, yi, f"{v:.2f}", va="center", color=th.fg, fontsize=8)
        ax.set_title(title.upper(), color=th.fg, fontsize=10, loc="left", pad=14)
        ax.text(0.0, 1.02, sub, transform=ax.transAxes, color=th.muted, fontsize=7)
    fig.text(0.01, 0.01, "controls in grey | only cost beats controls on TT",
             color=th.muted, fontsize=7)
    fig.tight_layout()
    return _save(fig, "fig2_dr1_results", th)


def fig3(th: Theme) -> str:
    fig, ax = _prep(th)
    labels = ["alphabetical\ntie-break", "seeded shuffle\n(corrected)"]
    vals = [1.00, 0.00]
    ax.bar(labels, vals, color=[PAL[6], PAL[5]], edgecolor=th.fg,
           hatch=HATCH[0], alpha=0.92, width=0.5)
    ax.set_ylim(0, 1.2)
    ax.set_ylabel("recall@3 of a SILENT nominator\n(cost on TK, tie_fraction = 1.00)")
    ax.text(0, 1.05, "1.00\nperfect score,\nzero information", ha="center",
            color=PAL[6], fontsize=9, weight="bold")
    ax.text(1, 0.10, "0.00\nchance,\nas it should be", ha="center",
            color=PAL[5], fontsize=9, weight="bold")
    ax.set_title("THE E1 GATE FIRED ON DR1'S OWN CONSTRUCTION", color=th.fg,
                 fontsize=11, loc="left", pad=18)
    ax.text(0.0, 1.015,
            "a nominator with no opinion scored perfectly, because 'a' sorts before 'p'",
            transform=ax.transAxes, color=th.muted, fontsize=8, va="bottom")
    fig.text(0.01, 0.01, "caught and fixed before freezing | pinned by a regression test",
             color=th.muted, fontsize=7)
    fig.tight_layout()
    return _save(fig, "fig3_dr1_tiebreak", th)


def main() -> None:
    for th in (DARK, LIGHT):
        for f in (fig1, fig2, fig3):
            print(f"  - {f(th)}")


if __name__ == "__main__":
    main()
