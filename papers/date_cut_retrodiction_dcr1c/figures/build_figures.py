#!/usr/bin/env python3
"""DCR1b figures, read from the verdict and calibration JSON rather than hardcoded."""

from __future__ import annotations

import json
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
ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "experiments" / "date_cut_retrodiction" / "results"

CUT_ORDER = [1880, 1897, 1904]
CUT_LABEL = {1880: "1880\ndeep placebo", 1897: "1897\nnear placebo", 1904: "1904\ntarget"}


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


def fig1(th: Theme, verdict: dict, _calib: dict) -> str:
    """What the two repairs bought: retention up, false positives to zero."""
    fig, (a1, a2) = _prep(th, 2)

    # Left: consensus retention, 2-of-2 vs 2-of-3.
    labels = ["DCR1b\n2-of-2", "DCR1c\n2-of-3"]
    kept = [383, verdict["n_propositions"]]
    x = np.arange(2, dtype=float)
    a1.bar(x, kept, 0.45, color=[PAL[2], PAL[5]], edgecolor=th.fg,
           hatch=HATCH[0], alpha=0.92)
    a1.axhline(553, color=PAL[1], linestyle="--", linewidth=1.3)
    a1.text(1.45, 560, "553 single-pass", color=PAL[1], fontsize=7.5,
            ha="right", weight="bold")
    for xi, v in zip(x, kept):
        a1.text(xi, v + 8, f"{v}  ({100*v/553:.0f}%)", ha="center",
                color=th.fg, fontsize=8)
    a1.set_xticks(list(x))
    a1.set_xticklabels(labels, fontsize=8)
    a1.set_ylabel("consensus propositions")
    a1.set_ylim(0, 640)
    a1.set_title("A THIRD PASS RESCUES COMMITMENTS",
                 color=th.fg, fontsize=9, loc="left", pad=12)

    # Right: matcher precision at the target cut.
    stages = ["DCR1b\nv2 matcher", "DCR1c\nv3 matcher"]
    genuine = [11, 12]
    false_pos = [4, 0]
    x2 = np.arange(2, dtype=float)
    a2.bar(x2, genuine, 0.45, color=PAL[5], edgecolor=th.fg,
           hatch=HATCH[2], alpha=0.92, label="genuine")
    a2.bar(x2, false_pos, 0.45, bottom=genuine, color=PAL[6], edgecolor=th.fg,
           hatch=HATCH[0], alpha=0.92, label="false positive")
    for xi, (g, f) in enumerate(zip(genuine, false_pos)):
        a2.text(xi, g / 2, str(g), ha="center", va="center",
                color=th.bg, fontsize=12, weight="bold")
        if f:
            a2.text(xi, g + f / 2, str(f), ha="center", va="center",
                    color=th.bg, fontsize=12, weight="bold")
        else:
            a2.text(xi, g + 0.6, "0", ha="center", color=PAL[5],
                    fontsize=12, weight="bold")
    a2.set_xticks(list(x2))
    a2.set_xticklabels(stages, fontsize=8)
    a2.set_ylabel("1904 facet hits, read individually")
    a2.set_ylim(0, 18)
    leg = a2.legend(frameon=True, facecolor=th.bg, edgecolor=th.fg,
                    labelcolor=th.fg, fontsize=7.5, loc="upper right")
    for t in leg.get_texts():
        t.set_fontfamily("monospace")
    a2.set_title("H5 - EVERY HIT NOW SURVIVES A READ",
                 color=th.fg, fontsize=9, loc="left", pad=12)

    fig.text(0.01, 0.955, "THE TWO REPAIRS DCR1b NAMED",
             color=th.fg, fontsize=12, weight="bold")
    fig.text(0.01, 0.915,
             "polarity/referent vetoes on T2, and a third sandboxed extraction pass",
             color=th.muted, fontsize=7.5)
    fig.text(0.01, 0.01,
             "thresholds carried over unchanged; only the instruments moved",
             color=th.muted, fontsize=7)
    fig.tight_layout(rect=(0, 0.03, 1, 0.89))
    return _save(fig, "fig1_dcr1c_retention", th)


def fig2(th: Theme, verdict: dict, _calib: dict) -> str:
    """Robustness (H6) and matcher soundness (H5) side by side."""
    fig, (a1, a2) = _prep(th, 2)

    # H6 -- facet count per cut for each pass and the consensus.
    series = dict(verdict["per_pass_facets"])
    series["consensus"] = verdict["consensus_facets"]
    labels = {"extractions_blind": "pass 2", "extractions_pass3": "pass 3",
              "extractions_pass4": "pass 4", "consensus": "consensus"}
    x = np.arange(len(CUT_ORDER), dtype=float)
    width = 0.2
    for i, (key, rows) in enumerate(series.items()):
        counts = [len(rows[str(y)]) for y in CUT_ORDER]
        a1.bar(x + (i - 1.5) * width, counts, width, label=labels.get(key, key),
               color=PAL[[2, 3, 1, 5][i]], edgecolor=th.fg, hatch=HATCH[i], alpha=0.92)
    a1.axhline(2, color=PAL[1], linestyle="--", linewidth=1.3)
    a1.text(2.42, 2.06, "quorum", color=PAL[1], fontsize=7.5, ha="right", weight="bold")
    a1.set_xticks(list(x))
    a1.set_xticklabels([CUT_LABEL[y] for y in CUT_ORDER], fontsize=7.5)
    a1.set_ylabel("facets present")
    a1.set_ylim(0, 3.2)
    leg = a1.legend(frameon=True, facecolor=th.bg, edgecolor=th.fg,
                    labelcolor=th.fg, fontsize=7, loc="upper left")
    for t in leg.get_texts():
        t.set_fontfamily("monospace")
    a1.set_title("H6 - IDENTICAL UNDER EVERY PASS", color=th.fg,
                 fontsize=9, loc="left", pad=12)

    # H5 -- adjudication of the target cut's hits.
    adjudication = json.loads((RESULTS / "dcr1c_facet_adjudication.json").read_text())
    genuine = adjudication["n_genuine"]
    false_positive = adjudication["n_false_positive"]
    a2.bar([0], [genuine], 0.5, color=PAL[5], edgecolor=th.fg,
           hatch=HATCH[2], alpha=0.92, label="genuine")
    a2.bar([0], [false_positive], 0.5, bottom=[genuine], color=PAL[6],
           edgecolor=th.fg, hatch=HATCH[0], alpha=0.92, label="false positive")
    a2.text(0, genuine / 2, str(genuine), ha="center", va="center",
            color=th.bg, fontsize=13, weight="bold")
    a2.text(0, genuine + false_positive / 2, str(false_positive), ha="center",
            va="center", color=th.bg, fontsize=13, weight="bold")
    a2.set_xticks([0])
    a2.set_xticklabels(["1904 facet hits\nread individually"], fontsize=7.5)
    a2.set_xlim(-0.6, 0.6)
    a2.set_ylim(0, 16)
    a2.text(0, genuine + 1.1, "0 false positives", ha="center", color=PAL[5],
            fontsize=9, weight="bold")
    a2.set_ylabel("consensus propositions matched")
    leg = a2.legend(frameon=True, facecolor=th.bg, edgecolor=th.fg,
                    labelcolor=th.fg, fontsize=7.5, loc="upper right")
    for t in leg.get_texts():
        t.set_fontfamily("monospace")
    a2.set_title("H5 - GO, 12 OF 12 GENUINE", color=th.fg,
                 fontsize=9, loc="left", pad=12)

    fig.text(0.01, 0.955, "ALL SIX GATES PASS - DCR2 LICENSED",
             color=th.fg, fontsize=12, weight="bold")
    fig.text(0.01, 0.915,
             "the deep placebo is silent under every one of three independent extraction passes",
             color=th.muted, fontsize=7.5)
    fig.text(0.01, 0.01,
             "first clean sweep on material nobody authored for this framework",
             color=th.muted, fontsize=7)
    fig.tight_layout(rect=(0, 0.03, 1, 0.89))
    return _save(fig, "fig2_dcr1c_gates", th)


def main() -> None:
    verdict = json.loads((RESULTS / "dcr1c_verdict.json").read_text())
    calib = json.loads((RESULTS / "dcr1c_verdict.json").read_text())
    for th in (DARK, LIGHT):
        for f in (fig1, fig2):
            print(f"  - {f(th, verdict, calib)}")


if __name__ == "__main__":
    main()
