"""Build dither-kit-styled figures for the Concern-Gated Retrieval SYNTHESIS.

Five figures rendered as PNG pairs (``_dark.png``, ``_light.png``) into the
directory this script lives in.  All numbers are hardcoded from the program's
real ledger (L0 pilot -> Wave 0 -> Wave 1a -> Wave 1b); there is no JSON
dependency.

Aesthetic: matplotlib emulation of the Dither Kit look — an ordered retro
palette, hatch-fill overlays, monospace typography, letter-spaced uppercase
titles, dark + light pairs at 8x5 @ 200 dpi.  The palette and Theme helpers are
imported from the Wave 0 figure module when reachable; otherwise a compact copy
of the same palette / theme block is used so this script stands alone.

Figures:
  fig1_arc_timeline          -- L0 -> Wave0 -> 1a -> 1b horizontal arc, each
                                step's verdict + one headline number.
  fig2_correction_ladder     -- what each step corrected in the prior step.
  fig3_wave1a_recency_oracle -- info_matched_recency AT the oracle ceiling on
                                all 3 families (the covert oracle).
  fig4_wave1b_learned_vs_random -- the decisive L1 KILL: learned vs random
                                geometry (~equal), mean_delta ~0 vs the
                                delta_thresh_L1 requirement far above.
  fig5_two_circularities     -- candidate-selection + verifier circularity and
                                where each was addressed.

Style discipline: no figure describes the mechanism as learned memory, concern
recovery, meaning, or selfhood.  Every figure labels the honest verdict.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


# ---------------------------------------------------------------------------
# Palette + Theme — import from Wave 0 module if reachable, else local copy
# ---------------------------------------------------------------------------

_WAVE0_FIGS = (
    Path(__file__).resolve().parents[2]
    / "concern_gated_retrieval_wave0"
    / "figures"
    / "build_figures.py"
)


def _try_import_wave0():
    if not _WAVE0_FIGS.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location("_cogr_wave0_figs", _WAVE0_FIGS)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_cogr_wave0_figs"] = mod
        spec.loader.exec_module(mod)
        # sanity: it must expose the pieces we reuse
        for name in ("DITHER_PALETTE", "HATCHES", "Theme", "DARK", "LIGHT"):
            if not hasattr(mod, name):
                return None
        return mod
    except Exception:
        return None


_W0 = _try_import_wave0()

if _W0 is not None:
    DITHER_PALETTE = _W0.DITHER_PALETTE
    HATCHES = _W0.HATCHES
    DARK_BG, DARK_FG, DARK_MUTED = _W0.DARK_BG, _W0.DARK_FG, _W0.DARK_MUTED
    LIGHT_BG, LIGHT_FG, LIGHT_MUTED = _W0.LIGHT_BG, _W0.LIGHT_FG, _W0.LIGHT_MUTED
    FIG_SIZE, FIG_DPI = _W0.FIG_SIZE, _W0.FIG_DPI
    Theme = _W0.Theme
    DARK, LIGHT = _W0.DARK, _W0.LIGHT
    _title_case = _W0._title_case
    _set_font_defaults = _W0._set_font_defaults
    _apply_theme = _W0._apply_theme
    _stamp_title = _W0._stamp_title
    _stamp_footer = _W0._stamp_footer
    _IMPORT_SOURCE = "imported wave0 palette/theme"
else:
    # -- compact copy of the Wave 0 palette + theme block --------------------
    DITHER_PALETTE = [
        "#111827",  # near-black ink
        "#F97316",  # orange
        "#22D3EE",  # cyan
        "#A78BFA",  # violet
        "#F5F5F4",  # bone-white
        "#84CC16",  # lime
        "#EF4444",  # red (alarms / X marks)
    ]
    HATCHES = ["///", "\\\\\\", "xxx", "...", "ooo", "|||", "---"]

    DARK_BG, DARK_FG, DARK_MUTED = "#0E0E0F", "#F5F5F4", "#4B5563"
    LIGHT_BG, LIGHT_FG, LIGHT_MUTED = "#FAF7F0", "#0E0E0F", "#9CA3AF"

    FIG_SIZE = (8, 5)
    FIG_DPI = 200

    def _title_case(text: str) -> str:
        upper = text.upper()
        out: list[str] = []
        for i, ch in enumerate(upper):
            if ch == " ":
                out.append(" / ")
            else:
                out.append(ch)
                if i + 1 < len(upper) and upper[i + 1] != " ":
                    out.append(" ")
        return "".join(out).rstrip()

    def _set_font_defaults() -> None:
        plt.rcParams["font.family"] = "monospace"
        plt.rcParams["font.monospace"] = [
            "Menlo", "Consolas", "DejaVu Sans Mono", "Courier New", "monospace",
        ]
        plt.rcParams["axes.titleweight"] = "bold"
        plt.rcParams["axes.labelweight"] = "bold"
        plt.rcParams["axes.spines.top"] = False
        plt.rcParams["axes.spines.right"] = False

    @dataclass(frozen=True)
    class Theme:  # type: ignore[no-redef]
        name: str
        bg: str
        fg: str
        muted: str

    DARK = Theme(name="dark", bg=DARK_BG, fg=DARK_FG, muted=DARK_MUTED)
    LIGHT = Theme(name="light", bg=LIGHT_BG, fg=LIGHT_FG, muted=LIGHT_MUTED)

    def _apply_theme(fig: Figure, ax: Axes, theme: Theme) -> None:
        fig.patch.set_facecolor(theme.bg)
        ax.set_facecolor(theme.bg)
        for spine in ax.spines.values():
            spine.set_edgecolor(theme.fg)
            spine.set_linewidth(1.0)
        ax.tick_params(colors=theme.fg, labelsize=9)
        ax.xaxis.label.set_color(theme.fg)
        ax.yaxis.label.set_color(theme.fg)
        if ax.title:
            ax.title.set_color(theme.fg)

    def _stamp_title(ax: Axes, title: str, subtitle: str | None, theme: Theme) -> None:
        ax.set_title(_title_case(title), color=theme.fg, fontsize=12, loc="left", pad=18)
        if subtitle:
            ax.text(0.0, 1.015, subtitle, transform=ax.transAxes, color=theme.muted,
                    fontsize=8, va="bottom", ha="left", family="monospace")

    def _stamp_footer(fig: Figure, text: str, theme: Theme) -> None:
        fig.text(0.01, 0.01, text, color=theme.muted, fontsize=7, ha="left",
                 va="bottom", family="monospace")


# Semantic palette shortcuts
INK = DITHER_PALETTE[0]
ORANGE = DITHER_PALETTE[1]
CYAN = DITHER_PALETTE[2]
VIOLET = DITHER_PALETTE[3]
BONE = DITHER_PALETTE[4]
LIME = DITHER_PALETTE[5]
RED = DITHER_PALETTE[6]

FAMILIES = ["delayed_commitments", "maintenance_fault", "resource_constrained"]
FAM_SHORT = ["delayed_\ncommitments", "maintenance_\nfault", "resource_\nconstrained"]

FOOTER = "concern-gated retrieval / synthesis  -  hardcoded ledger, no JSON dependency"


def _save(fig: Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 1 — arc timeline
# ---------------------------------------------------------------------------

ARC_STEPS = [
    {
        "id": "L0",
        "name": "L0 PILOT",
        "verdict": "DIAGNOSTIC",
        "headline": "hit@1 1.000\nvs 0.0052 one-sided",
        "color": CYAN,
        "vcolor": CYAN,
    },
    {
        "id": "WAVE 0",
        "name": "WAVE 0",
        "verdict": "FREEZE",
        "headline": "mu_mult 0.055\nvs mu_best 0.531 (~10x below)",
        "color": VIOLET,
        "vcolor": VIOLET,
    },
    {
        "id": "WAVE 1a",
        "name": "WAVE 1a",
        "verdict": "KILL",
        "headline": "recency = oracle\nceiling 0.5315 (covert)",
        "color": ORANGE,
        "vcolor": RED,
    },
    {
        "id": "WAVE 1b",
        "name": "WAVE 1b",
        "verdict": "KILL",
        "headline": "learned-vs-random\nmean_delta -0.022 (~0)",
        "color": ORANGE,
        "vcolor": RED,
    },
]


def _draw_arc_timeline(theme: Theme, path: Path) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    _apply_theme(fig, ax, theme)
    for spine in ax.spines.values():
        spine.set_visible(False)

    n = len(ARC_STEPS)
    box_w = 0.19
    y_center = 0.58
    box_h = 0.30
    xs = np.linspace(0.5 / n, 1 - 0.5 / n, n)

    # connecting spine
    ax.plot([xs[0], xs[-1]], [y_center, y_center], color=theme.muted,
            lw=1.2, zorder=0, ls=(0, (3, 3)))

    for i, step in enumerate(ARC_STEPS):
        x = xs[i]
        color = step["color"]
        hatch = HATCHES[i % len(HATCHES)]
        # base plate
        box = FancyBboxPatch(
            (x - box_w / 2, y_center - box_h / 2), box_w, box_h,
            boxstyle="round,pad=0.006,rounding_size=0.012",
            linewidth=1.3, edgecolor=theme.fg, facecolor=color, alpha=0.85, zorder=2,
        )
        ax.add_patch(box)
        overlay = FancyBboxPatch(
            (x - box_w / 2, y_center - box_h / 2), box_w, box_h,
            boxstyle="round,pad=0.006,rounding_size=0.012",
            linewidth=0.0, edgecolor=theme.fg, facecolor="none",
            hatch=hatch, alpha=0.30, zorder=3,
        )
        overlay.set_edgecolor(theme.fg)
        ax.add_patch(overlay)

        # step name (solid plate for legibility over hatch)
        ax.text(x, y_center + 0.075, step["name"], ha="center", va="center",
                color=INK, fontsize=10, family="monospace", weight="bold", zorder=4)

        # verdict pill
        vcolor = step["vcolor"]
        pill_w = box_w * 0.86
        pill = FancyBboxPatch(
            (x - pill_w / 2, y_center - 0.11), pill_w, 0.08,
            boxstyle="round,pad=0.004,rounding_size=0.02",
            linewidth=1.0, edgecolor=theme.fg, facecolor=vcolor, alpha=0.95, zorder=4,
        )
        ax.add_patch(pill)
        ax.text(x, y_center - 0.07, step["verdict"], ha="center", va="center",
                color=INK, fontsize=9, family="monospace", weight="bold", zorder=5)

        # headline number below
        ax.text(x, y_center - box_h / 2 - 0.07, step["headline"], ha="center",
                va="top", color=theme.fg, fontsize=7.5, family="monospace", zorder=4)

        # arrow to next
        if i < n - 1:
            arr = FancyArrowPatch(
                (x + box_w / 2 + 0.005, y_center),
                (xs[i + 1] - box_w / 2 - 0.005, y_center),
                arrowstyle="-|>", mutation_scale=16, lw=1.6,
                color=theme.fg, zorder=1,
            )
            ax.add_patch(arr)

    # top-of-arc "claim boundary" annotation
    ax.text(xs[0], y_center + box_h / 2 + 0.10,
            "graph ENCODES answer\n-> not learned relevance",
            ha="center", va="bottom", color=CYAN, fontsize=7,
            family="monospace", style="italic")
    ax.text((xs[-2] + xs[-1]) / 2, y_center + box_h / 2 + 0.10,
            "sealed eval:\ntwo-flashlight op. does NOT survive",
            ha="center", va="bottom", color=RED, fontsize=7,
            family="monospace", style="italic")

    _stamp_title(ax, "Program arc", "L0 diagnostic  ->  Wave 0 freeze  ->  Wave 1a KILL  ->  Wave 1b KILL", theme)
    _stamp_footer(fig, FOOTER, theme)
    _save(fig, path)


# ---------------------------------------------------------------------------
# Figure 2 — correction ladder
# ---------------------------------------------------------------------------

LADDER_RUNGS = [
    {
        "step": "WAVE 0  corrects  L0",
        "removed": "ceiling initialization",
        "detail": "L0 saturated hit@1 1.000 in every care condition; ceiling init\n"
                  "masked the mechanism's sensitivity to WRONG care weights.",
        "color": VIOLET,
    },
    {
        "step": "WAVE 1a  corrects  WAVE 0",
        "removed": "assumed care-recovery adjudicability",
        "detail": "Concern-recovery screen exposed a COVERT ORACLE: the load-bearing\n"
                  "memory was systematically most-recent, so recency reproduced the\n"
                  "oracle ceiling byte-for-byte; G3 specificity could not adjudicate.",
        "color": ORANGE,
    },
    {
        "step": "WAVE 1b  corrects  WAVE 1a",
        "removed": "recency / load-bearing coupling",
        "detail": "Fixture decouples recency from load-bearing role; leakage audits PASS\n"
                  "(label-perm p 0.594/0.366/0.515). Clean L1 falsification now possible.",
        "color": LIME,
    },
]


def _draw_correction_ladder(theme: Theme, path: Path) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    _apply_theme(fig, ax, theme)
    for spine in ax.spines.values():
        spine.set_visible(False)

    n = len(LADDER_RUNGS)
    top = 0.80
    bottom = 0.10
    rung_h = 0.175
    ys = np.linspace(top, bottom + rung_h, n)

    for i, rung in enumerate(LADDER_RUNGS):
        y = ys[i]
        color = rung["color"]
        hatch = HATCHES[i % len(HATCHES)]
        # rung plate
        box = FancyBboxPatch(
            (0.06, y - rung_h / 2), 0.88, rung_h,
            boxstyle="round,pad=0.006,rounding_size=0.01",
            linewidth=1.3, edgecolor=theme.fg, facecolor=theme.bg, alpha=1.0, zorder=2,
        )
        ax.add_patch(box)
        # left colour tab with hatch
        tab = FancyBboxPatch(
            (0.06, y - rung_h / 2), 0.035, rung_h,
            boxstyle="round,pad=0.001,rounding_size=0.006",
            linewidth=1.0, edgecolor=theme.fg, facecolor=color, alpha=0.9,
            hatch=hatch, zorder=3,
        )
        ax.add_patch(tab)

        # step label
        ax.text(0.115, y + rung_h / 2 - 0.035, rung["step"], ha="left", va="center",
                color=color, fontsize=10, family="monospace", weight="bold", zorder=4)
        # "removed:" line with strike-through feel
        ax.text(0.115, y + rung_h / 2 - 0.083, "removed crutch:  ", ha="left",
                va="center", color=theme.muted, fontsize=8, family="monospace", zorder=4)
        ax.text(0.315, y + rung_h / 2 - 0.083, rung["removed"], ha="left",
                va="center", color=RED, fontsize=8.5, family="monospace",
                weight="bold", zorder=4)
        # detail
        ax.text(0.115, y - rung_h / 2 + 0.045, rung["detail"], ha="left", va="center",
                color=theme.fg, fontsize=7.3, family="monospace", zorder=4)

        # down arrow between rungs
        if i < n - 1:
            ax.add_patch(FancyArrowPatch(
                (0.5, y - rung_h / 2 - 0.002),
                (0.5, ys[i + 1] + rung_h / 2 + 0.002),
                arrowstyle="-|>", mutation_scale=15, lw=1.6, color=theme.fg, zorder=1,
            ))

    _stamp_title(ax, "Correction ladder", "each step removes the crutch that let the prior step over-claim", theme)
    _stamp_footer(fig, FOOTER, theme)
    _save(fig, path)


# ---------------------------------------------------------------------------
# Figure 3 — Wave 1a recency covert oracle
# ---------------------------------------------------------------------------

RECENCY_VALS = [0.5315, 0.4772, 0.6000]   # info_matched_recency
ORACLE_VALS = [0.5315, 0.4772, 0.6000]    # oracle ceiling (identical -> covert oracle)


def _draw_recency_oracle(theme: Theme, path: Path) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    _apply_theme(fig, ax, theme)

    x = np.arange(len(FAMILIES))
    bar_w = 0.5

    # recency bars
    bars = ax.bar(x, RECENCY_VALS, bar_w, color=ORANGE, edgecolor=theme.fg,
                  linewidth=1.3, hatch="///", alpha=0.9, zorder=3,
                  label="info_matched_recency")

    # oracle ceiling markers sitting exactly on top of each bar
    for xi, ov in zip(x, ORACLE_VALS):
        ax.plot([xi - bar_w / 2 - 0.06, xi + bar_w / 2 + 0.06], [ov, ov],
                color=RED, lw=2.2, zorder=4)
    # single legend proxy for the ceiling line
    ax.plot([], [], color=RED, lw=2.2, label="oracle ceiling (identical)")

    for xi, rv in zip(x, RECENCY_VALS):
        ax.text(xi, rv + 0.018, f"{rv:.4f}", ha="center", va="bottom",
                color=theme.fg, fontsize=9, family="monospace", weight="bold", zorder=5)
        ax.text(xi, rv / 2, "= ceiling", ha="center", va="center",
                color=INK, fontsize=8, family="monospace", weight="bold",
                rotation=90, zorder=5)

    ax.set_xticks(x)
    ax.set_xticklabels(FAM_SHORT, fontsize=8)
    ax.set_ylim(0, 0.72)
    ax.set_ylabel("SET-level recovery", color=theme.fg, fontsize=9)
    ax.axhline(0, color=theme.fg, lw=1.0)

    leg = ax.legend(loc="upper right", fontsize=8, frameon=True)
    leg.get_frame().set_facecolor(theme.bg)
    leg.get_frame().set_edgecolor(theme.fg)
    for txt in leg.get_texts():
        txt.set_color(theme.fg)

    _stamp_title(ax, "Wave 1a covert oracle",
                 "recency reproduces the oracle ceiling byte-for-byte -> G3 cannot adjudicate  [KILL]", theme)
    _stamp_footer(fig, FOOTER, theme)
    _save(fig, path)


# ---------------------------------------------------------------------------
# Figure 4 — Wave 1b learned vs random  (the decisive L1 KILL)
# ---------------------------------------------------------------------------

MEAN_DELTA = [-0.022, -0.005, -0.003]          # learned - random geometry
LB_2SIGMA = [-0.432, -0.421, -0.359]           # 2-sigma lower bounds
DELTA_THRESH_L1 = [0.0484, 0.0534, 0.0500]     # frozen per-family requirement
HEADROOM = [0.539, 0.520, 0.572]               # non-ceiling headroom (context)


def _draw_learned_vs_random(theme: Theme, path: Path) -> None:
    fig, (axL, axR) = plt.subplots(
        1, 2, figsize=FIG_SIZE, dpi=FIG_DPI, gridspec_kw={"width_ratios": [1.0, 1.25]}
    )
    _apply_theme(fig, axL, theme)
    _apply_theme(fig, axR, theme)

    x = np.arange(len(FAMILIES))

    # -- Left panel: learned vs random geometry, essentially equal ----------
    bw = 0.34
    learned = HEADROOM
    random_g = [h - d for h, d in zip(HEADROOM, MEAN_DELTA)]  # random = learned - delta
    axL.bar(x - bw / 2, learned, bw, color=CYAN, edgecolor=theme.fg, linewidth=1.2,
            hatch="///", alpha=0.9, zorder=3, label="learned geometry")
    axL.bar(x + bw / 2, random_g, bw, color=VIOLET, edgecolor=theme.fg, linewidth=1.2,
            hatch="xxx", alpha=0.9, zorder=3, label="degree-matched random")
    axL.set_xticks(x)
    axL.set_xticklabels(FAM_SHORT, fontsize=7)
    axL.set_ylim(0, 0.72)
    axL.set_ylabel("non-ceiling recovery", color=theme.fg, fontsize=9)
    axL.set_title(_title_case("learned == random"), color=theme.fg, fontsize=9.5, loc="left", pad=8)
    legL = axL.legend(loc="upper right", fontsize=6.8, frameon=True)
    legL.get_frame().set_facecolor(theme.bg)
    legL.get_frame().set_edgecolor(theme.fg)
    for t in legL.get_texts():
        t.set_color(theme.fg)

    # -- Right panel: mean_delta ~0 vs delta_thresh_L1 far above ------------
    yerr_low = [md - lb for md, lb in zip(MEAN_DELTA, LB_2SIGMA)]  # extend down to LB
    yerr = np.array([yerr_low, [0.0, 0.0, 0.0]])
    axR.bar(x, MEAN_DELTA, 0.5, color=ORANGE, edgecolor=theme.fg, linewidth=1.3,
            hatch="...", alpha=0.9, zorder=3, label="mean_delta (learned - random)")
    axR.errorbar(x, MEAN_DELTA, yerr=yerr, fmt="none", ecolor=theme.fg, elinewidth=1.3,
                 capsize=5, capthick=1.3, zorder=4)

    # per-family threshold ticks + a representative band label
    for xi, th in zip(x, DELTA_THRESH_L1):
        axR.plot([xi - 0.28, xi + 0.28], [th, th], color=LIME, lw=2.4, zorder=5)
    axR.plot([], [], color=LIME, lw=2.4, label="delta_thresh_L1 (required)")

    axR.axhline(0, color=theme.fg, lw=1.0, zorder=2)

    for xi, md, lb in zip(x, MEAN_DELTA, LB_2SIGMA):
        axR.text(xi, 0.06, f"{md:+.3f}", ha="center", va="bottom", color=theme.fg,
                 fontsize=8, family="monospace", weight="bold", zorder=6)
        axR.text(xi, lb - 0.015, f"2s LB\n{lb:.3f}", ha="center", va="top",
                 color=theme.muted, fontsize=6.5, family="monospace", zorder=6)

    axR.set_xticks(x)
    axR.set_xticklabels(FAM_SHORT, fontsize=7)
    axR.set_ylim(-0.50, 0.16)
    axR.set_ylabel("learned - random  delta", color=theme.fg, fontsize=9)
    axR.set_title(_title_case("delta << required"), color=theme.fg, fontsize=8.5, loc="left", pad=8)
    legR = axR.legend(loc="center left", fontsize=6.6, frameon=True)
    legR.get_frame().set_facecolor(theme.bg)
    legR.get_frame().set_edgecolor(theme.fg)
    for t in legR.get_texts():
        t.set_color(theme.fg)

    fig.suptitle(_title_case("Wave 1b  L1 KILL"), color=theme.fg, fontsize=13,
                 x=0.012, ha="left", weight="bold")
    fig.text(0.012, 0.915, "learned geometry does NOT beat a degree-matched random null at matched budget",
             color=theme.muted, fontsize=7.5, ha="left", family="monospace")
    _stamp_footer(fig, FOOTER, theme)
    fig.tight_layout(rect=(0, 0.02, 1, 0.90))
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 5 — the two circularities
# ---------------------------------------------------------------------------


def _draw_two_circularities(theme: Theme, path: Path) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    _apply_theme(fig, ax, theme)
    for spine in ax.spines.values():
        spine.set_visible(False)

    def node(cx, cy, w, h, label, color, hatch, fs=8):
        b = FancyBboxPatch(
            (cx - w / 2, cy - h / 2), w, h,
            boxstyle="round,pad=0.006,rounding_size=0.012",
            linewidth=1.3, edgecolor=theme.fg, facecolor=color, alpha=0.88, zorder=3,
        )
        ax.add_patch(b)
        ov = FancyBboxPatch(
            (cx - w / 2, cy - h / 2), w, h,
            boxstyle="round,pad=0.006,rounding_size=0.012",
            linewidth=0.0, facecolor="none", edgecolor=theme.fg, hatch=hatch,
            alpha=0.28, zorder=4,
        )
        ax.add_patch(ov)
        ax.text(cx, cy, label, ha="center", va="center", color=INK, fontsize=fs,
                family="monospace", weight="bold", zorder=5)

    def cyc_arrow(p0, p1, color, rad):
        ax.add_patch(FancyArrowPatch(
            p0, p1, arrowstyle="-|>", mutation_scale=14, lw=1.7, color=color,
            connectionstyle=f"arc3,rad={rad}", zorder=2,
        ))

    # ---- Left loop: candidate-selection circularity ----
    lx = 0.27
    ax.text(lx, 0.93, _title_case("candidate-selection"), ha="center", va="center",
            color=ORANGE, fontsize=9.5, family="monospace", weight="bold")
    ax.text(lx, 0.885, "circularity", ha="center", va="center",
            color=ORANGE, fontsize=8.5, family="monospace")
    node(lx, 0.74, 0.30, 0.11, "care weights\npick candidates", ORANGE, "///")
    node(lx, 0.44, 0.30, 0.11, "candidates confirm\nthe care weights", ORANGE, "\\\\\\")
    cyc_arrow((lx + 0.13, 0.70), (lx + 0.13, 0.49), ORANGE, -0.55)
    cyc_arrow((lx - 0.13, 0.49), (lx - 0.13, 0.70), ORANGE, -0.55)

    # ---- Right loop: verifier circularity ----
    rx = 0.73
    ax.text(rx, 0.93, _title_case("verifier"), ha="center", va="center",
            color=CYAN, fontsize=9.5, family="monospace", weight="bold")
    ax.text(rx, 0.885, "circularity", ha="center", va="center",
            color=CYAN, fontsize=8.5, family="monospace")
    node(rx, 0.74, 0.30, 0.11, "verifier trained\non same signal", CYAN, "xxx")
    node(rx, 0.44, 0.30, 0.11, "scores the signal\nas success", CYAN, "...")
    cyc_arrow((rx + 0.13, 0.70), (rx + 0.13, 0.49), CYAN, -0.55)
    cyc_arrow((rx - 0.13, 0.49), (rx - 0.13, 0.70), CYAN, -0.55)

    # Spencer echo-chamber banner between the loops
    ax.text(0.5, 0.59, "Spencer\necho-chamber\nobjection", ha="center", va="center",
            color=theme.muted, fontsize=7.5, family="monospace", style="italic")

    # ---- Where each was addressed (bottom band) ----
    band_y = 0.19
    band = FancyBboxPatch(
        (0.06, band_y - 0.115), 0.88, 0.23,
        boxstyle="round,pad=0.006,rounding_size=0.01",
        linewidth=1.3, edgecolor=theme.fg, facecolor=theme.bg, zorder=2,
    )
    ax.add_patch(band)
    ax.text(0.5, band_y + 0.075, _title_case("where each was addressed"), ha="center",
            va="center", color=theme.fg, fontsize=9, family="monospace", weight="bold")

    # left address
    ax.add_patch(FancyArrowPatch((lx, 0.38), (lx, band_y + 0.115),
                 arrowstyle="-|>", mutation_scale=13, lw=1.5, color=ORANGE, zorder=3))
    ax.text(lx, band_y + 0.005,
            "Wave 1b fixture:\ndecouple recency from\nload-bearing role\n"
            "-> KILL, delta ~ 0",
            ha="center", va="center", color=theme.fg, fontsize=7,
            family="monospace", zorder=4)

    # right address
    ax.add_patch(FancyArrowPatch((rx, 0.38), (rx, band_y + 0.115),
                 arrowstyle="-|>", mutation_scale=13, lw=1.5, color=CYAN, zorder=3))
    ax.text(rx, band_y + 0.005,
            "leakage audits PASS\n(label-perm p 0.594/\n0.366/0.515)  +  future:\ncare-INDEPENDENT prior",
            ha="center", va="center", color=theme.fg, fontsize=7,
            family="monospace", zorder=4)

    _stamp_title(ax, "Two circularities",
                 "candidate-selection + verifier loops Spencer named, and where the arc attacked each", theme)
    _stamp_footer(fig, FOOTER, theme)
    _save(fig, path)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

FIG_BUILDERS = [
    ("fig1_arc_timeline", _draw_arc_timeline),
    ("fig2_correction_ladder", _draw_correction_ladder),
    ("fig3_wave1a_recency_oracle", _draw_recency_oracle),
    ("fig4_wave1b_learned_vs_random", _draw_learned_vs_random),
    ("fig5_two_circularities", _draw_two_circularities),
]


def build_all(out_dir: Path) -> list[Path]:
    _set_font_defaults()
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for theme in (DARK, LIGHT):
        for stem, fn in FIG_BUILDERS:
            p = out_dir / f"{stem}_{theme.name}.png"
            fn(theme, p)
            written.append(p)
    return written


def main() -> int:
    out_dir = Path(__file__).resolve().parent
    written = build_all(out_dir)
    print(f"[cogr-synthesis] {_IMPORT_SOURCE if _W0 is not None else 'local palette copy'}")
    print(f"[cogr-synthesis] wrote {len(written)} figures to {out_dir}")
    for p in written:
        print(f"  - {p.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
