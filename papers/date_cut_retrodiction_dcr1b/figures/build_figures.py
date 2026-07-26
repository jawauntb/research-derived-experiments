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


def fig1(th: Theme, verdict: dict, calib: dict) -> str:
    """Residue: what the repaired measure changes, and where the gate sits."""
    fig, ax = _prep(th)
    v1 = [100 * calib["cuts"][f"{y}_all"]["residue_rate_v1"] for y in CUT_ORDER]
    v2 = [100 * calib["cuts"][f"{y}_all"]["residue_rate_v2"] for y in CUT_ORDER]
    gate = 100 * verdict["H2_vocabulary_residue_v2"]["threshold"]

    x = np.arange(len(CUT_ORDER), dtype=float)
    w = 0.36
    ax.bar(x - w / 2, v1, w, label="v1 measure (DCR1, failed)", color=PAL[6],
           edgecolor=th.fg, hatch=HATCH[0], alpha=0.92)
    ax.bar(x + w / 2, v2, w, label="v2 measure (accent+stem+possessive)",
           color=PAL[5], edgecolor=th.fg, hatch=HATCH[2], alpha=0.92)
    ax.axhline(gate, color=PAL[1], linestyle="--", linewidth=1.6)
    ax.text(len(CUT_ORDER) - 0.62, gate + 0.12, f"gate {gate:.0f}% (unchanged)",
            color=PAL[1], fontsize=8, weight="bold", ha="right")
    for xi, (a, b) in enumerate(zip(v1, v2)):
        ax.text(xi - w / 2, a + 0.1, f"{a:.2f}", ha="center", color=th.fg, fontsize=7)
        ax.text(xi + w / 2, b + 0.1, f"{b:.2f}", ha="center", color=th.fg, fontsize=7)
    ax.set_xticks(list(x))
    ax.set_xticklabels([CUT_LABEL[y] for y in CUT_ORDER], fontsize=8)
    ax.set_ylabel("vocabulary residue (% of output types)")
    ax.set_ylim(0, max(max(v1), gate) * 1.35)
    leg = ax.legend(frameon=True, facecolor=th.bg, edgecolor=th.fg,
                    labelcolor=th.fg, fontsize=8, loc="upper right")
    for t in leg.get_texts():
        t.set_fontfamily("monospace")
    ax.set_title("DCR1b - INSTRUMENT REPAIRED, THRESHOLD CARRIED OVER",
                 color=th.fg, fontsize=10.5, loc="left", pad=18)
    ax.text(0.0, 1.015,
            "most of DCR1's residue was inflection and accents, not imported concepts",
            transform=ax.transAxes, color=th.muted, fontsize=8, va="bottom")
    fig.text(0.01, 0.01, "H2 GO | tightest cut 4.34% against a 5% gate -- reachable, not trivial",
             color=th.muted, fontsize=7)
    fig.tight_layout()
    return _save(fig, "fig1_dcr1b_residue", th)


def fig2(th: Theme, verdict: dict, _calib: dict) -> str:
    """Robustness (H6) and matcher soundness (H5) side by side."""
    fig, (a1, a2) = _prep(th, 2)

    # H6 -- facet count per cut for each pass and the consensus.
    series = dict(verdict["per_pass_facets"])
    series["consensus"] = verdict["consensus_facets"]
    labels = {"extractions_blind": "pass 2", "extractions_pass3": "pass 3",
              "consensus": "consensus"}
    x = np.arange(len(CUT_ORDER), dtype=float)
    width = 0.26
    for i, (key, rows) in enumerate(series.items()):
        counts = [len(rows[str(y)]) for y in CUT_ORDER]
        a1.bar(x + (i - 1) * width, counts, width, label=labels.get(key, key),
               color=PAL[[2, 3, 5][i]], edgecolor=th.fg, hatch=HATCH[i], alpha=0.92)
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
    adjudication = json.loads((RESULTS / "dcr1b_facet_adjudication.json").read_text())
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
    a2.set_ylabel("consensus propositions matched")
    leg = a2.legend(frameon=True, facecolor=th.bg, edgecolor=th.fg,
                    labelcolor=th.fg, fontsize=7.5, loc="upper right")
    for t in leg.get_texts():
        t.set_fontfamily("monospace")
    a2.set_title("H5 - NO_GO, ANY FALSE POSITIVE FAILS", color=th.fg,
                 fontsize=9, loc="left", pad=12)

    fig.text(0.01, 0.955, "FIVE GATES PASS, ONE FAILS",
             color=th.fg, fontsize=12, weight="bold")
    fig.text(0.01, 0.915,
             "the placebo holds under every extraction; the matcher still cannot read polarity",
             color=th.muted, fontsize=7.5)
    fig.text(0.01, 0.01,
             "DCR2 remains blocked -- the reason moved from a measurement artifact to a real defect",
             color=th.muted, fontsize=7)
    fig.tight_layout(rect=(0, 0.03, 1, 0.89))
    return _save(fig, "fig2_dcr1b_gates", th)


def main() -> None:
    verdict = json.loads((RESULTS / "dcr1b_verdict.json").read_text())
    calib = json.loads((RESULTS / "dcr1b_calibration.json").read_text())
    for th in (DARK, LIGHT):
        for f in (fig1, fig2):
            print(f"  - {f(th, verdict, calib)}")


if __name__ == "__main__":
    main()
