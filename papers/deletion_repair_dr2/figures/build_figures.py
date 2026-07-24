#!/usr/bin/env python3
"""DR2 figures. Numbers hardcoded from results/dr2_verdict.json (2026-07-24)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

PAL = ["#111827", "#F97316", "#22D3EE", "#A78BFA", "#F5F5F4", "#84CC16", "#EF4444"]
HATCH = ["///", "\\\\\\", "xxx", "...", "ooo"]
FIG, DPI = (8, 5), 200
OUT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str
    fg: str
    muted: str


DARK = Theme("dark", "#0E0E0F", "#F5F5F4", "#4B5563")
LIGHT = Theme("light", "#FAF7F0", "#0E0E0F", "#9CA3AF")


def _prep(th: Theme, n: int = 1):
    plt.rcParams["font.family"] = "monospace"
    fig, axes = plt.subplots(1, n, figsize=FIG)
    fig.patch.set_facecolor(th.bg)
    for ax in (axes if n > 1 else [axes]):
        ax.set_facecolor(th.bg)
        for sp in ax.spines.values():
            sp.set_edgecolor(th.fg)
        ax.tick_params(colors=th.fg, labelsize=8)
        ax.yaxis.label.set_color(th.fg)
        ax.xaxis.label.set_color(th.fg)
    return fig, axes


def _save(fig, stem: str, th: Theme) -> str:
    name = f"{stem}_{th.name}.png"
    fig.savefig(OUT / name, dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    return name


NOMS = ["weakness", "minrank_disj", "sum_disj", "max_disj", "cost", "size_only", "random"]
SK = [1, 1, 1, 1, 689, 263, 989]
ST = [1, 1, 1, 3, 3, 21, 247]


def fig1(th: Theme) -> str:
    fig, (a1, a2) = _prep(th, 2)
    for ax, vals, title, exp in (
        (a1, SK, "scaled_kinematics", 675.5),
        (a2, ST, "scaled_transduction", 67.5),
    ):
        y = np.arange(len(NOMS), dtype=float)
        cols = [PAL[5] if v <= 3 else (PAL[6] if v > 100 else PAL[1]) for v in vals]
        ax.barh(y, vals, color=cols, edgecolor=th.fg, hatch=HATCH[0], alpha=0.92)
        ax.set_yticks(list(y))
        ax.set_yticklabels(NOMS, fontsize=7)
        ax.invert_yaxis()
        ax.set_xscale("log")
        ax.set_xlim(0.7, 2000)
        ax.set_xlabel("verifications to first hit (log)", fontsize=8)
        ax.axvline(exp, color=PAL[1], linestyle="--", linewidth=1.3)
        ax.text(exp * 1.1, len(NOMS) - 0.4, f"random\n{exp:.0f}", color=PAL[1], fontsize=7)
        for yi, v in zip(y, vals):
            ax.text(v * 1.25, yi, str(v), va="center", color=th.fg, fontsize=7)
        ax.set_title(title.upper(), color=th.fg, fontsize=10, loc="left", pad=14)
    fig.suptitle("")
    fig.text(0.01, 0.955, "DR2 - THE NOMINATOR EARNS ITS KEEP", color=th.fg,
             fontsize=12, weight="bold")
    fig.text(0.01, 0.915, "675x and 68x fewer expensive verifications than random ordering",
             color=th.muted, fontsize=8)
    fig.text(0.01, 0.01, "H3' GO | 1350 candidates each | base rates 0.07% and 1.41%",
             color=th.muted, fontsize=7)
    fig.tight_layout(rect=(0, 0.03, 1, 0.89))
    return _save(fig, "fig1_dr2_speedup", th)


def fig2(th: Theme) -> str:
    fig, ax = _prep(th)
    cats = ["cost>0\nweakness>0", "cost>0\nweakness=0", "cost=0\nweakness>0"]
    sk = [0, 0, 1]
    st = [191, 0, 172]
    x = np.arange(len(cats), dtype=float)
    w = 0.36
    ax.bar(x - w / 2, sk, w, label="scaled_kinematics", color=PAL[2],
           edgecolor=th.fg, hatch=HATCH[0], alpha=0.92)
    ax.bar(x + w / 2, st, w, label="scaled_transduction", color=PAL[3],
           edgecolor=th.fg, hatch=HATCH[2], alpha=0.92)
    ax.set_xticks(list(x))
    ax.set_xticklabels(cats, fontsize=8)
    ax.set_ylabel("candidate deletions")
    ax.set_ylim(0, 220)
    ax.annotate("EMPTY -- and provably so", xy=(1.0, 6), xytext=(1.0, 120),
                ha="center", color=PAL[6], fontsize=10, weight="bold",
                arrowprops=dict(arrowstyle="->", color=PAL[6], lw=1.6))
    leg = ax.legend(frameon=True, facecolor=th.bg, edgecolor=th.fg,
                    labelcolor=th.fg, fontsize=8)
    for t in leg.get_texts():
        t.set_fontfamily("monospace")
    ax.set_title("COST CANNOT FIRE WHERE WEAKNESS IS SILENT", color=th.fg,
                 fontsize=11, loc="left", pad=18)
    ax.text(0.0, 1.015,
            "ext(R) subset of ext(R\\D)  =>  a min over the extension improves only if it GREW",
            transform=ax.transAxes, color=th.muted, fontsize=8, va="bottom")
    fig.text(0.01, 0.01, "2700 candidates across both toys | H1' is unreachable, not merely unsupported",
             color=th.muted, fontsize=7)
    fig.tight_layout()
    return _save(fig, "fig2_dr2_theorem", th)


def main() -> None:
    for th in (DARK, LIGHT):
        for f in (fig1, fig2):
            print(f"  - {f(th)}")


if __name__ == "__main__":
    main()
