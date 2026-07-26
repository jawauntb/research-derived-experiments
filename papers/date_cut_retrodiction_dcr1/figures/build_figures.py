#!/usr/bin/env python3
"""DCR1 figures, read from results/dcr1_verdict.json rather than hardcoded."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib
import matplotlib.colors

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

PAL = ["#111827", "#F97316", "#22D3EE", "#A78BFA", "#F5F5F4", "#84CC16", "#EF4444"]
HATCH = ["///", "\\\\\\", "xxx", "...", "ooo"]
FIG, DPI = (8, 5), 200
OUT = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
VERDICT = ROOT / "experiments" / "date_cut_retrodiction" / "results" / "dcr1_verdict.json"

FACET_LABEL = {
    "T1_absolute_simultaneity": "T1\nabsolute\nsimultaneity",
    "T2_privileged_frame": "T2\nprivileged\nframe",
    "T3_local_time_artifice": "T3\nlocal time\nas artifice",
}
CUT_ORDER = [1880, 1897, 1904]
CUT_LABEL = {
    1880: "1880\ndeep placebo",
    1897: "1897\nnear placebo",
    1904: "1904\ntarget",
}


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


def _load() -> dict:
    return json.loads(VERDICT.read_text())


def fig1(th: Theme, data: dict) -> str:
    """The emergence profile: which facets appear at which cut."""
    fig, ax = _prep(th)
    facets = list(FACET_LABEL)
    grid = np.zeros((len(facets), len(CUT_ORDER)))
    for j, year in enumerate(CUT_ORDER):
        present = set(data["cuts"][f"{year}_all"]["facets_present"])
        for i, facet in enumerate(facets):
            grid[i, j] = 1.0 if facet in present else 0.0

    ax.imshow(
        grid,
        cmap=matplotlib.colors.ListedColormap([th.bg, PAL[5]]),
        vmin=0,
        vmax=1,
        aspect="auto",
    )
    for i in range(len(facets)):
        for j in range(len(CUT_ORDER)):
            ax.text(
                j,
                i,
                "PRESENT" if grid[i, j] else "absent",
                ha="center",
                va="center",
                color=th.bg if grid[i, j] else th.muted,
                fontsize=9,
                weight="bold" if grid[i, j] else "normal",
            )
    ax.set_xticks(range(len(CUT_ORDER)))
    ax.set_xticklabels([CUT_LABEL[y] for y in CUT_ORDER], fontsize=8)
    ax.set_yticks(range(len(facets)))
    ax.set_yticklabels([FACET_LABEL[f] for f in facets], fontsize=7.5)
    ax.set_xticks(np.arange(-0.5, len(CUT_ORDER), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(facets), 1), minor=True)
    ax.grid(which="minor", color=th.fg, linewidth=1.2)
    ax.tick_params(which="minor", length=0)

    ax.set_title(
        "DCR1 - DOES THE TARGET FAMILY APPEAR ONLY WHERE THE CORPUS SUPPORTS IT?",
        color=th.fg,
        fontsize=9.5,
        loc="left",
        pad=18,
    )
    ax.text(
        0.0,
        1.02,
        "extraction is cut-blind: each document extracted once, cuts composed afterwards",
        transform=ax.transAxes,
        color=th.muted,
        fontsize=7.5,
        va="bottom",
    )
    g3 = data["G3_deep_placebo_silent"]["decision"]
    g4 = data["G4_target_cut_not_silent"]["decision"]
    fig.text(
        0.01,
        0.01,
        f"G3 deep placebo silent: {g3}   |   G4 target cut not silent: {g4}",
        color=th.muted,
        fontsize=7,
    )
    fig.tight_layout()
    return _save(fig, "fig1_dcr1_emergence", th)


def fig2(th: Theme, data: dict) -> str:
    """Corpus growth vs propositions vs residue."""
    fig, (a1, a2) = _prep(th, 2)

    docs = [data["cuts"][f"{y}_all"]["n_documents"] for y in CUT_ORDER]
    props = [data["cuts"][f"{y}_all"]["n_propositions"] for y in CUT_ORDER]
    x = np.arange(len(CUT_ORDER), dtype=float)
    w = 0.36
    a1.bar(x - w / 2, docs, w, label="documents", color=PAL[2],
           edgecolor=th.fg, hatch=HATCH[0], alpha=0.92)
    a1.bar(x + w / 2, props, w, label="propositions", color=PAL[3],
           edgecolor=th.fg, hatch=HATCH[2], alpha=0.92)
    for xi, (d, p) in enumerate(zip(docs, props)):
        a1.text(xi - w / 2, d + 3, str(d), ha="center", color=th.fg, fontsize=7)
        a1.text(xi + w / 2, p + 3, str(p), ha="center", color=th.fg, fontsize=7)
    a1.set_xticks(list(x))
    a1.set_xticklabels([CUT_LABEL[y] for y in CUT_ORDER], fontsize=7.5)
    a1.set_ylabel("count")
    leg = a1.legend(frameon=True, facecolor=th.bg, edgecolor=th.fg,
                    labelcolor=th.fg, fontsize=7.5, loc="upper left")
    for t in leg.get_texts():
        t.set_fontfamily("monospace")
    a1.set_title("CORPUS AND EXTRACTION SIZE", color=th.fg, fontsize=9, loc="left", pad=12)

    residue = [100.0 * data["cuts"][f"{y}_all"]["residue_rate"] for y in CUT_ORDER]
    gate = 100.0 * data["G2_vocabulary_residue"]["threshold"]
    cols = [PAL[5] if r < gate else PAL[6] for r in residue]
    a2.bar(x, residue, 0.5, color=cols, edgecolor=th.fg, hatch=HATCH[3], alpha=0.92)
    a2.axhline(gate, color=PAL[6], linestyle="--", linewidth=1.4)
    a2.text(len(CUT_ORDER) - 0.5, gate * 1.08, f"G2 gate = {gate:.0f}%",
            color=PAL[6], fontsize=7.5, ha="right", weight="bold")
    for xi, r in zip(x, residue):
        a2.text(xi, r + gate * 0.05, f"{r:.1f}%", ha="center", color=th.fg, fontsize=7.5)
    a2.set_xticks(list(x))
    a2.set_xticklabels([CUT_LABEL[y] for y in CUT_ORDER], fontsize=7.5)
    a2.set_ylabel("vocabulary residue (% of output types)")
    a2.set_ylim(0, max(gate * 1.6, max(residue) * 1.35 if residue else gate))
    a2.set_title("RESIDUE: WORDS THE CORPUS DID NOT HAVE",
                 color=th.fg, fontsize=9, loc="left", pad=12)

    fidelity = 100.0 * data["quote_audit"]["fidelity"]
    fig.text(0.01, 0.01,
             f"quote fidelity {fidelity:.1f}% of "
             f"{data['quote_audit']['n_total']} propositions "
             f"(G1 gate 90%)   |   residue is relational, not a blocklist",
             color=th.muted, fontsize=7)
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    return _save(fig, "fig2_dcr1_corpus_residue", th)


def main() -> None:
    data = _load()
    for th in (DARK, LIGHT):
        for f in (fig1, fig2):
            print(f"  - {f(th, data)}")


if __name__ == "__main__":
    main()
