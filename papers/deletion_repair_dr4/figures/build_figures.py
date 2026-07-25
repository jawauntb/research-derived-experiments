#!/usr/bin/env python3
"""DR4 figures. Numbers hardcoded from results/dr4_verdict.json (2026-07-25)."""

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
    """The ceiling was the instrument, not the nominator."""
    fig, ax = _prep(th)
    labels = ["DR3 CT\n191/1350 load-bearing", "DR4 CT4\n1/1350 load-bearing"]
    ceiling = [7.0, 675.5]
    achieved = [7.0, 675.5]
    x = np.arange(len(labels), dtype=float)
    w = 0.36
    ax.bar(x - w / 2, ceiling, w, label="ceiling = E[random] (base rate alone)",
           color=PAL[0], edgecolor=th.fg, hatch=HATCH[3], alpha=0.92)
    ax.bar(x + w / 2, achieved, w, label="achieved by best nominator",
           color=PAL[5], edgecolor=th.fg, hatch=HATCH[2], alpha=0.92)
    ax.axhline(10.0, color=PAL[6], linestyle="--", linewidth=1.6)
    ax.text(0.5, 12.0, "H4 gate = 10x", color=PAL[6], fontsize=8.5,
            weight="bold", ha="center")
    ax.set_yscale("log")
    ax.set_ylim(1, 3000)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("speedup vs random ordering (log)")
    ax.annotate("gate unreachable\nby construction", xy=(-0.18, 7.2),
                xytext=(-0.42, 90), color=PAL[6], fontsize=8.5, weight="bold",
                arrowprops=dict(arrowstyle="->", color=PAL[6], lw=1.5))
    ax.text(1.18, 850, "675.5x", ha="center", color=PAL[5],
            fontsize=11, weight="bold")
    leg = ax.legend(frameon=True, facecolor=th.bg, edgecolor=th.fg,
                    labelcolor=th.fg, fontsize=8, loc="upper left")
    for t in leg.get_texts():
        t.set_fontfamily("monospace")
    ax.set_title("DR4 - THE CEILING WAS THE TOY, NOT THE NOMINATOR",
                 color=th.fg, fontsize=10.5, loc="left", pad=18)
    ax.text(0.0, 1.015,
            "speedup <= E[random]; both bars touch the ceiling in both experiments",
            transform=ax.transAxes, color=th.muted, fontsize=8, va="bottom")
    fig.text(0.01, 0.01,
             "threshold carried over unchanged; only the base rate was repaired",
             color=th.muted, fontsize=7)
    fig.tight_layout()
    return _save(fig, "fig1_dr4_ceiling", th)


def fig2(th: Theme) -> str:
    """Complementarity survives the recalibration."""
    fig, (a1, a2) = _prep(th, 2)
    noms = ["weakness", "cost", "minrank", "sum", "max", "size_only", "random"]
    rk = [1, 689, 1, 1, 1, 263, 989]
    ct = [996, 1, 1, 1, 1, 352, 989]
    for ax, vals, title in (
        (a1, rk, "restrictive_kinematics"),
        (a2, ct, "calibrated_costly_transduction"),
    ):
        y = np.arange(len(noms), dtype=float)
        cols = [PAL[5] if v == 1 else (PAL[6] if v > 100 else PAL[1]) for v in vals]
        ax.barh(y, vals, color=cols, edgecolor=th.fg, hatch=HATCH[0], alpha=0.92)
        ax.set_yticks(list(y))
        ax.set_yticklabels(noms, fontsize=7)
        ax.invert_yaxis()
        ax.set_xscale("log")
        ax.set_xlim(0.7, 4000)
        ax.set_xlabel("verifications to first hit (log)", fontsize=8)
        ax.axvline(675.5, color=PAL[1], linestyle="--", linewidth=1.3)
        for yi, v in zip(y, vals):
            ax.text(v * 1.3, yi, str(v), va="center", color=th.fg, fontsize=7)
        ax.set_title(title.upper(), color=th.fg, fontsize=8.5, loc="left", pad=14)
    fig.text(0.01, 0.955, "EACH NOMINATOR STILL SILENT ON THE OTHER'S TOY",
             color=th.fg, fontsize=12, weight="bold")
    fig.text(0.01, 0.915,
             "dashed line = E[random] = 675.5; both toys now share one base rate",
             color=th.muted, fontsize=8)
    fig.text(0.01, 0.01,
             "H2 GO, H3 GO -- all three combiners reach 1 verification on both toys",
             color=th.muted, fontsize=7)
    fig.tight_layout(rect=(0, 0.03, 1, 0.89))
    return _save(fig, "fig2_dr4_complementarity", th)


def main() -> None:
    for th in (DARK, LIGHT):
        for f in (fig1, fig2):
            print(f"  - {f(th)}")


if __name__ == "__main__":
    main()
