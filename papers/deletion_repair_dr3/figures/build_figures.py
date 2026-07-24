#!/usr/bin/env python3
"""DR3 figures. Numbers hardcoded from results/dr3_verdict.json (2026-07-24)."""

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


def fig1(th: Theme) -> str:
    fig, ax = _prep(th)
    cats = ["cost>0\nweakness=0", "weakness>0\ncost=0", "both>0"]
    dr2 = [0, 173, 191]
    dr3 = [363, 1, 0]
    x = np.arange(len(cats), dtype=float)
    w = 0.36
    ax.bar(x - w / 2, dr2, w, label="DR2 (cost = min over extension)",
           color=PAL[6], edgecolor=th.fg, hatch=HATCH[0], alpha=0.92)
    ax.bar(x + w / 2, dr3, w, label="DR3 (cost on propositions)",
           color=PAL[5], edgecolor=th.fg, hatch=HATCH[2], alpha=0.92)
    ax.set_xticks(list(x))
    ax.set_xticklabels(cats, fontsize=8)
    ax.set_ylabel("candidate deletions (both toys)")
    ax.annotate("0 -- provably empty", xy=(-0.18, 8), xytext=(-0.35, 250),
                color=PAL[6], fontsize=9, weight="bold",
                arrowprops=dict(arrowstyle="->", color=PAL[6], lw=1.5))
    ax.text(0.18, 375, "363", ha="center", color=PAL[5], fontsize=11, weight="bold")
    leg = ax.legend(frameon=True, facecolor=th.bg, edgecolor=th.fg,
                    labelcolor=th.fg, fontsize=8)
    for t in leg.get_texts():
        t.set_fontfamily("monospace")
    ax.set_title("DR3 - MOVING COST OFF THE EXTENSION RESTORES INDEPENDENCE",
                 color=th.fg, fontsize=10.5, loc="left", pad=18)
    ax.text(0.0, 1.015,
            "the cell DR2 proved impossible is now populated",
            transform=ax.transAxes, color=th.muted, fontsize=8, va="bottom")
    fig.text(0.01, 0.01, "H1'' GO | cost_relief no longer reads the extension",
             color=th.muted, fontsize=7)
    fig.tight_layout()
    return _save(fig, "fig1_dr3_independence", th)


def fig2(th: Theme) -> str:
    fig, (a1, a2) = _prep(th, 2)
    noms = ["weakness", "cost", "minrank", "sum", "max", "size_only", "random"]
    rk = [1, 689, 1, 1, 1, 263, 989]
    ct = [9, 1, 1, 1, 1, 1, 7]
    for ax, vals, title, exp in (
        (a1, rk, "restrictive_kinematics", 675.5),
        (a2, ct, "costly_transduction", 7.0),
    ):
        y = np.arange(len(noms), dtype=float)
        cols = [PAL[5] if v == 1 else (PAL[6] if v > 100 else PAL[1]) for v in vals]
        ax.barh(y, vals, color=cols, edgecolor=th.fg, hatch=HATCH[0], alpha=0.92)
        ax.set_yticks(list(y))
        ax.set_yticklabels(noms, fontsize=7)
        ax.invert_yaxis()
        ax.set_xscale("log")
        ax.set_xlim(0.7, 2000)
        ax.set_xlabel("verifications to first hit (log)", fontsize=8)
        ax.axvline(exp, color=PAL[1], linestyle="--", linewidth=1.3)
        for yi, v in zip(y, vals):
            ax.text(v * 1.3, yi, str(v), va="center", color=th.fg, fontsize=7)
        ax.set_title(title.upper(), color=th.fg, fontsize=9.5, loc="left", pad=14)
    fig.text(0.01, 0.955, "EACH NOMINATOR IS SILENT ON THE OTHER'S TOY",
             color=th.fg, fontsize=12, weight="bold")
    fig.text(0.01, 0.915,
             "weakness wins RK and is silent on CT; cost wins CT and is silent on RK",
             color=th.muted, fontsize=8)
    fig.text(0.01, 0.01,
             "H2'' GO -- the two-nominator claim holds once cost is off the extension",
             color=th.muted, fontsize=7)
    fig.tight_layout(rect=(0, 0.03, 1, 0.89))
    return _save(fig, "fig2_dr3_complementarity", th)


def main() -> None:
    for th in (DARK, LIGHT):
        for f in (fig1, fig2):
            print(f"  - {f(th)}")


if __name__ == "__main__":
    main()
