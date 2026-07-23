"""Build dither-kit-styled figures for the Wave 0 report.

This script emits six figures (fig1..fig6) as PNG pairs (_dark.png, _light.png)
into the same directory it lives in.  When
``experiments/concern_gated_retrieval_e2/wave0/results/calibration_summary.json``
is present, fig6 uses its per-family variance rows; when it is absent, all
figures render against in-file synthetic placeholder data and stamp a
"placeholder" watermark.

Aesthetic: matplotlib emulation of https://www.tripwire.sh/dither-kit — an
ordered, retro palette with hatch-fill overlays, monospace typography, and
letter-spaced uppercase titles.  Dither Kit itself is a React library, so this
script does not use it directly; instead it re-implements the look in
matplotlib primitives so the same asset ships in both light and dark mode.

The script is deterministic and safe to re-invoke; each call overwrites the
existing PNG pair.  Wave 0 style discipline applies: no figure describes the
mechanism as learned memory, concern recovery, meaning, or selfhood; every
figure title labels itself as a Wave 0 calibration scaffolding artifact.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle


# ---------------------------------------------------------------------------
# Dither-kit inspired palette + typography
# ---------------------------------------------------------------------------

DITHER_PALETTE: list[str] = [
    "#111827",  # near-black ink
    "#F97316",  # orange
    "#22D3EE",  # cyan
    "#A78BFA",  # violet
    "#F5F5F4",  # bone-white
    "#84CC16",  # lime
    "#EF4444",  # red (used sparingly for alarms / X marks)
]

HATCHES: list[str] = ["///", "\\\\\\", "xxx", "...", "ooo", "|||", "---"]

DARK_BG = "#0E0E0F"
DARK_FG = "#F5F5F4"
DARK_MUTED = "#4B5563"

LIGHT_BG = "#FAF7F0"
LIGHT_FG = "#0E0E0F"
LIGHT_MUTED = "#9CA3AF"

FIG_SIZE = (8, 5)
FIG_DPI = 200


def _title_case(text: str) -> str:
    """UPPERCASE with single-space letter-spacing — a matplotlib-safe
    approximation of an 8-bit typographic feel (Dither Kit uses real
    letter-spacing CSS).  Real spaces in the source string collapse to
    " / " so word boundaries remain readable.
    """
    upper = text.upper()
    out_chars: list[str] = []
    for i, ch in enumerate(upper):
        if ch == " ":
            out_chars.append(" / ")
        else:
            out_chars.append(ch)
            # single space between adjacent non-space glyphs
            if i + 1 < len(upper) and upper[i + 1] != " ":
                out_chars.append(" ")
    return "".join(out_chars).rstrip()


def _set_font_defaults() -> None:
    plt.rcParams["font.family"] = "monospace"
    plt.rcParams["font.monospace"] = [
        "Menlo",
        "Consolas",
        "DejaVu Sans Mono",
        "Courier New",
        "monospace",
    ]
    plt.rcParams["axes.titleweight"] = "bold"
    plt.rcParams["axes.labelweight"] = "bold"
    plt.rcParams["axes.spines.top"] = False
    plt.rcParams["axes.spines.right"] = False


@dataclass(frozen=True)
class Theme:
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
    ax.set_title(
        _title_case(title),
        color=theme.fg,
        fontsize=12,
        loc="left",
        pad=18,
    )
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


def _stamp_placeholder(fig: Figure, theme: Theme, note: str = "placeholder") -> None:
    del theme
    fig.text(
        0.5,
        0.5,
        _title_case(note),
        color=DITHER_PALETTE[1],  # orange, low alpha
        alpha=0.18,
        fontsize=40,
        ha="center",
        va="center",
        rotation=20,
        family="monospace",
        weight="bold",
    )


def _stamp_footer(fig: Figure, text: str, theme: Theme) -> None:
    fig.text(
        0.01,
        0.01,
        text,
        color=theme.muted,
        fontsize=7,
        ha="left",
        va="bottom",
        family="monospace",
    )


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def _find_repo_root(start: Path) -> Path:
    """Walk up until we find the repo root (contains ``experiments/``)."""
    cur = start.resolve()
    for _ in range(8):
        if (cur / "experiments").is_dir() and (cur / "papers").is_dir():
            return cur
        cur = cur.parent
    # Fall back to the script's grandparent's grandparent.
    return start.resolve().parents[3]


def _load_calibration(repo_root: Path) -> dict[str, Any] | None:
    path = (
        repo_root
        / "experiments"
        / "concern_gated_retrieval_e2"
        / "wave0"
        / "results"
        / "calibration_summary.json"
    )
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Figure 1 — pipeline
# ---------------------------------------------------------------------------


PIPELINE_STAGES = [
    ("CONTEXT", "active"),
    ("CARE", "wrong prior"),
    ("NOMINATE", "r_ctx AND r_care"),
    ("RARITY", "/ r_freq^beta"),
    ("VERIFIER", "SealedEnv"),
    ("OUTCOME", "scalar"),
]


def _draw_pipeline(theme: Theme, path: Path, has_data: bool) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    _apply_theme(fig, ax, theme)
    for spine in ax.spines.values():
        spine.set_visible(False)

    n = len(PIPELINE_STAGES)
    box_w = 0.128
    gap = (1.0 - n * box_w) / (n + 1)
    y_center = 0.5
    box_h = 0.30

    label_plate_h = 0.10  # solid label plate so text sits above the hatch

    for i, (label, sublabel) in enumerate(PIPELINE_STAGES):
        x = gap + i * (box_w + gap)
        color = DITHER_PALETTE[i % (len(DITHER_PALETTE) - 1) + 1]
        hatch = HATCHES[i % len(HATCHES)]

        # base fill
        box = FancyBboxPatch(
            (x, y_center - box_h / 2),
            box_w,
            box_h,
            boxstyle="round,pad=0.006,rounding_size=0.012",
            linewidth=1.2,
            edgecolor=theme.fg,
            facecolor=color,
            alpha=0.85,
        )
        ax.add_patch(box)
        # ordered-dither approximation: hatched overlay
        overlay = FancyBboxPatch(
            (x, y_center - box_h / 2),
            box_w,
            box_h,
            boxstyle="round,pad=0.006,rounding_size=0.012",
            linewidth=0.0,
            edgecolor="none",
            facecolor="none",
            hatch=hatch,
        )
        overlay.set_edgecolor(theme.bg)
        ax.add_patch(overlay)

        # solid label plate that sits ABOVE the hatch so the label reads clean
        plate = FancyBboxPatch(
            (x + 0.004, y_center - label_plate_h / 2),
            box_w - 0.008,
            label_plate_h,
            boxstyle="round,pad=0.002,rounding_size=0.008",
            linewidth=0.8,
            edgecolor=theme.fg,
            facecolor=theme.bg,
            alpha=0.92,
        )
        ax.add_patch(plate)

        ax.text(
            x + box_w / 2,
            y_center,
            label,
            ha="center",
            va="center",
            fontsize=8.5,
            color=theme.fg,
            weight="bold",
            family="monospace",
        )
        ax.text(
            x + box_w / 2,
            y_center - box_h / 2 - 0.04,
            sublabel,
            ha="center",
            va="top",
            fontsize=7.0,
            color=theme.muted,
            family="monospace",
        )

        # arrow to the next stage
        if i < n - 1:
            arrow = FancyArrowPatch(
                (x + box_w, y_center),
                (x + box_w + gap, y_center),
                arrowstyle="->",
                mutation_scale=14,
                color=theme.fg,
                linewidth=1.4,
            )
            ax.add_patch(arrow)

    _stamp_title(
        ax,
        "Fig 1 — calibration pipeline",
        "context AND care -> rarity correction -> sealed verifier -> outcome",
        theme,
    )
    _stamp_footer(
        fig,
        "cogr-wave0 // calibration scaffolding // not a mechanism claim",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder")
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2 — wrong prior vs oracle
# ---------------------------------------------------------------------------


PRIOR_REGIONS = [
    "alarm\n(inflated)",
    "commit_A\n(suppressed)",
    "commit_B\n(neutral)",
    "distractor_A",
    "distractor_B",
    "neutral_bg",
]

# From §5 of the preregistration: alarm=1.0, suppressed commitment=0.05,
# other true commitment left at uniform ~0.2 for a 5-region prior, etc.
WRONG_PRIOR = np.array([1.00, 0.05, 0.20, 0.20, 0.20, 0.20])
ORACLE_PRIOR = np.array([0.05, 0.55, 0.30, 0.05, 0.05, 0.05])


def _draw_wrong_prior(theme: Theme, path: Path, has_data: bool) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    _apply_theme(fig, ax, theme)

    x = np.arange(len(PRIOR_REGIONS))
    width = 0.36

    wrong_color = DITHER_PALETTE[6]  # red — the wrong prior
    oracle_color = DITHER_PALETTE[5]  # lime — the oracle

    ax.bar(
        x - width / 2,
        WRONG_PRIOR,
        width,
        color=wrong_color,
        edgecolor=theme.fg,
        linewidth=1.0,
        hatch=HATCHES[0],
        alpha=0.90,
        label="wrong prior",
    )
    ax.bar(
        x + width / 2,
        ORACLE_PRIOR,
        width,
        color=oracle_color,
        edgecolor=theme.fg,
        linewidth=1.0,
        hatch=HATCHES[2],
        alpha=0.90,
        label="oracle prior",
    )

    ax.set_xticks(x)
    ax.set_xticklabels(PRIOR_REGIONS, fontsize=8, color=theme.fg)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("concern weight (unitless)", color=theme.fg, fontsize=9)

    # annotate the two adversarial regions
    ax.annotate(
        "over-weighted\nalarm  w = 1.00",
        xy=(0 - width / 2, WRONG_PRIOR[0]),
        xytext=(0.35, 1.02),
        color=DITHER_PALETTE[6],
        fontsize=8,
        arrowprops=dict(arrowstyle="->", color=DITHER_PALETTE[6], lw=1.2),
        family="monospace",
        weight="bold",
    )
    ax.annotate(
        "under-weighted\ncommitment  w = 0.05",
        xy=(1 - width / 2, WRONG_PRIOR[1]),
        xytext=(1.55, 0.72),
        color=DITHER_PALETTE[1],
        fontsize=8,
        arrowprops=dict(arrowstyle="->", color=DITHER_PALETTE[1], lw=1.2),
        family="monospace",
        weight="bold",
    )

    leg = ax.legend(
        loc="upper right",
        frameon=True,
        facecolor=theme.bg,
        edgecolor=theme.fg,
        labelcolor=theme.fg,
        fontsize=8,
    )
    for txt in leg.get_texts():
        txt.set_fontfamily("monospace")

    _stamp_title(
        ax,
        "Fig 2 — wrong prior vs oracle",
        "§5 of PREREGISTRATION.md — wave 0 never updates this prior",
        theme,
    )
    _stamp_footer(
        fig,
        "over-weight alarm + suppress at least one true commitment (§5)",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder")
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3 — family x property matrix
# ---------------------------------------------------------------------------


FAMILIES = ["delayed_commitments", "maintenance_fault", "resource_constrained"]
PROPERTIES = [
    "off-context\nload",
    "chronic\nalarm",
    "paraphrase\nholdout",
    "family\nholdout",
    "sealed\noutcome",
    "wrong-prior\nadversarial",
]

# All three families exercise all six properties (that is the design).
# The intensity encodes the family-specific salience per property so the
# grid still reads as a matrix rather than a solid block.
FAMILY_PROPERTY_INTENSITY = np.array(
    [
        # off-ctx  alarm  paraph  fam-out  sealed  wrong-prior
        [1.00, 0.85, 0.70, 0.90, 1.00, 1.00],  # delayed_commitments
        [0.95, 1.00, 0.65, 0.90, 1.00, 1.00],  # maintenance_fault
        [0.90, 0.80, 0.75, 0.90, 1.00, 1.00],  # resource_constrained
    ]
)


def _draw_family_matrix(theme: Theme, path: Path, has_data: bool) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    _apply_theme(fig, ax, theme)

    grid = FAMILY_PROPERTY_INTENSITY
    n_rows, n_cols = grid.shape

    # Build a discrete quantized palette so the heatmap has an ordered-dither
    # feel rather than a continuous gradient.
    palette_cells = [
        DITHER_PALETTE[3],  # violet — low
        DITHER_PALETTE[2],  # cyan
        DITHER_PALETTE[5],  # lime
        DITHER_PALETTE[1],  # orange — high
    ]
    thresholds = [0.5, 0.75, 0.9, 1.01]

    for r in range(n_rows):
        for c in range(n_cols):
            v = grid[r, c]
            for i, t in enumerate(thresholds):
                if v <= t:
                    color = palette_cells[i]
                    hatch = HATCHES[i % len(HATCHES)]
                    break
            else:
                color = palette_cells[-1]
                hatch = HATCHES[0]
            rect = Rectangle(
                (c, n_rows - 1 - r),
                1,
                1,
                facecolor=color,
                edgecolor=theme.bg,
                linewidth=1.6,
                alpha=0.92,
            )
            ax.add_patch(rect)
            overlay = Rectangle(
                (c, n_rows - 1 - r),
                1,
                1,
                facecolor="none",
                edgecolor=theme.bg,
                hatch=hatch,
                linewidth=0.0,
            )
            ax.add_patch(overlay)
            ax.text(
                c + 0.5,
                n_rows - 1 - r + 0.5,
                f"{v:0.2f}",
                ha="center",
                va="center",
                fontsize=8.5,
                color=DARK_BG,
                weight="bold",
                family="monospace",
                bbox=dict(
                    boxstyle="round,pad=0.20",
                    facecolor="#F5F5F4",
                    edgecolor="none",
                    alpha=0.85,
                ),
            )

    ax.set_xlim(0, n_cols)
    ax.set_ylim(0, n_rows)
    ax.set_xticks(np.arange(n_cols) + 0.5)
    ax.set_yticks(np.arange(n_rows) + 0.5)
    ax.set_xticklabels(PROPERTIES, fontsize=8, color=theme.fg)
    ax.set_yticklabels(list(reversed(FAMILIES)), fontsize=8.5, color=theme.fg)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)

    _stamp_title(
        ax,
        "Fig 3 — families x properties",
        "three procedurally distinct calibration families, disjoint from confirmatory",
        theme,
    )
    _stamp_footer(
        fig,
        "intensity = calibration salience per property (not a metric).",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder")
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 4 — baseline slate
# ---------------------------------------------------------------------------


BASELINE_SLATE = [
    ("no_retrieval", "floor"),
    ("random", "chance floor"),
    ("freq_only", "unconditional freq"),
    ("context_only", "PPR from ctx"),
    ("care_only", "PPR from wrong prior"),
    ("additive", "r_ctx + r_care"),
    ("multiplicative", "candidate mechanism"),
    ("embedding_sim", "modern embed baseline"),
    ("learned_one_stage", "matched-cap learned ranker"),
    ("info_matched", "value / priority / recency"),
    ("wrong_agent", "must-not-help control"),
    ("oracle_ceiling", "diagnostic only"),
]


def _draw_baseline_slate(
    theme: Theme, path: Path, has_data: bool, calib: dict | None
) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    _apply_theme(fig, ax, theme)

    names = [row[0] for row in BASELINE_SLATE]
    # Value axis: number of matched-budget dimensions each baseline exercises.
    # This is a Wave 0 scaffolding view; it is NOT a performance chart.
    budget_dims = np.array(
        [
            0,  # no_retrieval — not budget-comparable
            1,  # random — budget only
            1,  # freq_only
            2,  # context_only — budget + graph
            2,  # care_only — budget + graph
            3,  # additive — budget + graph + fusion
            3,  # multiplicative
            3,  # embedding_sim — budget + embed + compute
            4,  # learned_one_stage — budget + params + compute + gradient
            3,  # info_matched
            2,  # wrong_agent
            5,  # oracle_ceiling — ceiling only
        ]
    )

    # If we have calibration data, tint each bar by whether the summary
    # mentions the baseline explicitly — a scaffold check, not a metric.
    is_scored = np.zeros(len(names), dtype=bool)
    if calib is not None:
        try:
            fam_summary = calib["summary"]["families"]
            observed = set()
            for fam in fam_summary.values():
                for bl in fam.get("baselines", {}).keys():
                    observed.add(bl)
            key_alias = {
                "context_only": "context_only_ppr",
                "care_only": "care_only_ppr",
                "additive": "additive_ppr",
                "multiplicative": "multiplicative_ppr",
                "embedding_sim": "embedding_similarity",
                "info_matched": "info_matched_recency",
                "wrong_agent": "wrong_agent_concern",
                "learned_one_stage": "learned_one_stage",
                "oracle_ceiling": "oracle_ceiling",
                "random": "random",
                "freq_only": "freq_only",
                "no_retrieval": "no_retrieval",
            }
            for i, name in enumerate(names):
                if key_alias.get(name, name) in observed:
                    is_scored[i] = True
        except Exception:
            pass

    colors = []
    hatches = []
    for i, (name, _) in enumerate(BASELINE_SLATE):
        if name == "oracle_ceiling":
            colors.append(DITHER_PALETTE[6])  # red — do not promote
            hatches.append(HATCHES[2])
        elif name == "multiplicative":
            colors.append(DITHER_PALETTE[1])  # orange — candidate mechanism
            hatches.append(HATCHES[0])
        elif name == "no_retrieval":
            colors.append(DITHER_PALETTE[3])
            hatches.append(HATCHES[3])
        else:
            colors.append(DITHER_PALETTE[2 + (i % 3)])
            hatches.append(HATCHES[i % len(HATCHES)])

    y_pos = np.arange(len(names))
    bars = ax.barh(
        y_pos,
        budget_dims,
        color=colors,
        edgecolor=theme.fg,
        linewidth=1.0,
        alpha=0.90,
    )
    for b, hatch in zip(bars, hatches):
        b.set_hatch(hatch)

    for i, (n_dim, scored) in enumerate(zip(budget_dims, is_scored)):
        marker = "  [scored]" if scored else ""
        ax.text(
            n_dim + 0.1,
            i,
            f"{BASELINE_SLATE[i][1]}{marker}",
            va="center",
            ha="left",
            color=theme.fg,
            fontsize=7.5,
            family="monospace",
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=8.5, color=theme.fg)
    ax.set_xlim(0, 8.0)
    ax.set_xticks(range(0, 6))
    ax.set_xlabel(
        "matched-budget dimensions (Wave 0 scaffolding, not a metric)",
        color=theme.fg,
        fontsize=9,
    )
    ax.invert_yaxis()

    _stamp_title(
        ax,
        "Fig 4 — baseline slate",
        "§7 of PREREGISTRATION.md — every baseline is scored on every calibration row",
        theme,
    )
    _stamp_footer(
        fig,
        "oracle_ceiling is diagnostic only — never a promotable claim.",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder")
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 5 — leakage barriers
# ---------------------------------------------------------------------------


EVALUATOR_ONLY_FIELDS = [
    "role_label",
    "answer_key",
    "future_utility",
    "oracle_concern",
    "wrong_agent_id",
    "template_family_split",
    "paraphrase_family",
    "epiplexity_future_target",
]

POLICY_VISIBLE_FIELDS = [
    "history (t <= t_decide)",
    "active_context",
    "concern_prior (§5)",
    "graph.WeightedGraph",
]


def _draw_leakage_barriers(theme: Theme, path: Path, has_data: bool) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    _apply_theme(fig, ax, theme)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Left column — POLICY-VISIBLE
    left_box = FancyBboxPatch(
        (0.03, 0.20),
        0.34,
        0.62,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        linewidth=1.5,
        edgecolor=DITHER_PALETTE[5],  # lime
        facecolor=DITHER_PALETTE[5],
        alpha=0.16,
    )
    ax.add_patch(left_box)
    ax.text(
        0.20,
        0.84,
        _title_case("policy-visible"),
        ha="center",
        va="bottom",
        color=DITHER_PALETTE[5],
        fontsize=9.5,
        weight="bold",
        family="monospace",
    )
    for i, name in enumerate(POLICY_VISIBLE_FIELDS):
        y = 0.75 - i * 0.10
        ax.text(
            0.06,
            y,
            f"[OK]  {name}",
            color=theme.fg,
            fontsize=8.5,
            family="monospace",
            va="center",
        )

    # Right column — EVALUATOR-ONLY with red X marks
    right_box = FancyBboxPatch(
        (0.55, 0.06),
        0.42,
        0.78,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        linewidth=1.5,
        edgecolor=DITHER_PALETTE[6],  # red
        facecolor=DITHER_PALETTE[6],
        alpha=0.14,
    )
    ax.add_patch(right_box)
    ax.text(
        0.76,
        0.86,
        _title_case("evaluator-only"),
        ha="center",
        va="bottom",
        color=DITHER_PALETTE[6],
        fontsize=9.5,
        weight="bold",
        family="monospace",
    )
    for i, name in enumerate(EVALUATOR_ONLY_FIELDS):
        y = 0.78 - i * 0.085
        ax.text(
            0.58,
            y,
            "X",
            color=DITHER_PALETTE[6],
            fontsize=13,
            weight="bold",
            family="monospace",
            va="center",
        )
        ax.text(
            0.62,
            y,
            name,
            color=theme.fg,
            fontsize=8.5,
            family="monospace",
            va="center",
        )

    # Middle: sealed env barrier
    barrier_x = 0.44
    ax.plot(
        [barrier_x, barrier_x],
        [0.05, 0.86],
        color=DITHER_PALETTE[1],
        linewidth=2.6,
        linestyle="--",
    )
    ax.text(
        barrier_x,
        0.03,
        _title_case("sealedenv.observe_outcome"),
        ha="center",
        va="bottom",
        color=DITHER_PALETTE[1],
        fontsize=7.5,
        family="monospace",
        weight="bold",
    )

    # decision -> outcome arrow across the barrier
    ax.add_patch(
        FancyArrowPatch(
            (0.37, 0.50),
            (0.55, 0.50),
            arrowstyle="->",
            mutation_scale=16,
            color=DITHER_PALETTE[1],
            linewidth=1.6,
        )
    )
    ax.text(
        0.46,
        0.53,
        "decision",
        ha="center",
        va="bottom",
        color=DITHER_PALETTE[1],
        fontsize=7.5,
        family="monospace",
    )
    ax.add_patch(
        FancyArrowPatch(
            (0.55, 0.40),
            (0.37, 0.40),
            arrowstyle="->",
            mutation_scale=16,
            color=DITHER_PALETTE[2],
            linewidth=1.6,
        )
    )
    ax.text(
        0.46,
        0.36,
        "RealizedOutcome",
        ha="center",
        va="top",
        color=DITHER_PALETTE[2],
        fontsize=7.5,
        family="monospace",
    )

    _stamp_title(
        ax,
        "Fig 5 — leakage barriers",
        "policy-visible vs evaluator-only fields, sealed env as the sole channel",
        theme,
    )
    _stamp_footer(
        fig,
        "any confirmatory row reaching a calibration path = fatal integrity failure (§9.1).",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder")
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 6 — calibration grid (epsilon, budget) with variance
# ---------------------------------------------------------------------------


def _extract_grid(
    calib: dict[str, Any] | None,
) -> tuple[list[str], list[int], np.ndarray, np.ndarray, bool]:
    """Return (families, budgets, sigma_grid, exploration_grid, has_data).

    The JSON schema in practice records a single epsilon (0.05) and a
    per-family variance rather than a per-cell variance.  We render as a
    (family, budget) grid annotated with the per-family sigma, and shade
    intensity by the per-cell exploration fraction.
    """
    if calib is None:
        # placeholder synthetic scaffold
        return (
            ["delayed_commitments", "maintenance_fault", "resource_constrained"],
            [1, 2],
            np.array([[0.20, 0.21], [0.15, 0.15], [0.29, 0.29]]),
            np.array([[0.08, 0.08], [0.06, 0.06], [0.09, 0.09]]),
            False,
        )
    try:
        fam_summary = calib["summary"]["families"]
        families = list(fam_summary.keys())
        budgets = [1, 2]
        sigma_grid = np.zeros((len(families), len(budgets)))
        expl_grid = np.zeros((len(families), len(budgets)))
        # sigma is per-family in the summary; we replicate across budgets
        for i, fam in enumerate(families):
            sig = float(fam_summary[fam].get("sigma_hat_multiplicative", 0.0))
            sigma_grid[i, :] = sig
        # exploration fraction per (family, budget) is aggregated from cells
        cell_by_key: dict[tuple[str, int], list[float]] = {}
        for row in calib.get("cells", []):
            cell = row["cell"]
            fam = cell["family"]
            budget = int(cell["budget"])
            expl = float(row.get("coverage", {}).get("exploration_fraction", 0.0))
            cell_by_key.setdefault((fam, budget), []).append(expl)
        for i, fam in enumerate(families):
            for j, b in enumerate(budgets):
                vals = cell_by_key.get((fam, b), [])
                expl_grid[i, j] = float(np.mean(vals)) if vals else 0.0
        return families, budgets, sigma_grid, expl_grid, True
    except Exception:
        return (
            ["delayed_commitments", "maintenance_fault", "resource_constrained"],
            [1, 2],
            np.array([[0.20, 0.21], [0.15, 0.15], [0.29, 0.29]]),
            np.array([[0.08, 0.08], [0.06, 0.06], [0.09, 0.09]]),
            False,
        )


def _draw_calibration_grid(
    theme: Theme, path: Path, has_data: bool, calib: dict | None
) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    _apply_theme(fig, ax, theme)

    families, budgets, sigma_grid, expl_grid, _ = _extract_grid(calib)
    n_rows, n_cols = sigma_grid.shape

    # colour intensity by exploration_fraction; annotation shows sigma
    palette_cells = [
        DITHER_PALETTE[3],  # violet — low exploration
        DITHER_PALETTE[2],  # cyan
        DITHER_PALETTE[5],  # lime
        DITHER_PALETTE[1],  # orange — high exploration
    ]
    thresholds = [0.02, 0.08, 0.15, 1.0]

    for r in range(n_rows):
        for c in range(n_cols):
            v = float(expl_grid[r, c])
            for i, t in enumerate(thresholds):
                if v <= t:
                    color = palette_cells[i]
                    hatch = HATCHES[i % len(HATCHES)]
                    break
            else:
                color = palette_cells[-1]
                hatch = HATCHES[0]
            rect = Rectangle(
                (c, n_rows - 1 - r),
                1,
                1,
                facecolor=color,
                edgecolor=theme.bg,
                linewidth=1.6,
                alpha=0.90,
            )
            ax.add_patch(rect)
            overlay = Rectangle(
                (c, n_rows - 1 - r),
                1,
                1,
                facecolor="none",
                edgecolor=theme.bg,
                hatch=hatch,
                linewidth=0.0,
            )
            ax.add_patch(overlay)
            ax.text(
                c + 0.5,
                n_rows - 1 - r + 0.62,
                f"sigma = {sigma_grid[r, c]:0.3f}",
                ha="center",
                va="center",
                fontsize=9,
                color=DARK_BG,
                weight="bold",
                family="monospace",
                bbox=dict(
                    boxstyle="round,pad=0.25",
                    facecolor="#F5F5F4",
                    edgecolor="none",
                    alpha=0.90,
                ),
            )
            ax.text(
                c + 0.5,
                n_rows - 1 - r + 0.32,
                f"expl = {v:0.2f}",
                ha="center",
                va="center",
                fontsize=8,
                color=DARK_BG,
                family="monospace",
                bbox=dict(
                    boxstyle="round,pad=0.20",
                    facecolor="#F5F5F4",
                    edgecolor="none",
                    alpha=0.85,
                ),
            )

    ax.set_xlim(0, n_cols)
    ax.set_ylim(0, n_rows)
    ax.set_xticks(np.arange(n_cols) + 0.5)
    ax.set_yticks(np.arange(n_rows) + 0.5)
    ax.set_xticklabels(
        [f"budget = {b}" for b in budgets], fontsize=8.5, color=theme.fg
    )
    ax.set_yticklabels(list(reversed(families)), fontsize=8, color=theme.fg)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)

    _stamp_title(
        ax,
        "Fig 6 — calibration grid",
        "sigma_hat_multiplicative per family, exploration_fraction per (family, budget)",
        theme,
    )
    _stamp_footer(
        fig,
        "epsilon fixed at 0.05 in this run — Wave 1 will sweep.",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder — replaced by Modal run")
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


FIG_NAMES = [
    "fig1_pipeline",
    "fig2_wrong_prior",
    "fig3_family_matrix",
    "fig4_baseline_slate",
    "fig5_leakage_barriers",
    "fig6_calibration_grid",
]


def build_all(out_dir: Path, calib: dict | None) -> list[Path]:
    _set_font_defaults()
    out_dir.mkdir(parents=True, exist_ok=True)
    has_data = calib is not None
    written: list[Path] = []

    for theme in (DARK, LIGHT):
        # fig1
        p = out_dir / f"fig1_pipeline_{theme.name}.png"
        _draw_pipeline(theme, p, has_data)
        written.append(p)
        # fig2
        p = out_dir / f"fig2_wrong_prior_{theme.name}.png"
        _draw_wrong_prior(theme, p, has_data)
        written.append(p)
        # fig3
        p = out_dir / f"fig3_family_matrix_{theme.name}.png"
        _draw_family_matrix(theme, p, has_data)
        written.append(p)
        # fig4
        p = out_dir / f"fig4_baseline_slate_{theme.name}.png"
        _draw_baseline_slate(theme, p, has_data, calib)
        written.append(p)
        # fig5
        p = out_dir / f"fig5_leakage_barriers_{theme.name}.png"
        _draw_leakage_barriers(theme, p, has_data)
        written.append(p)
        # fig6
        p = out_dir / f"fig6_calibration_grid_{theme.name}.png"
        _draw_calibration_grid(theme, p, has_data, calib)
        written.append(p)

    return written


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    repo_root = _find_repo_root(script_dir)
    calib = _load_calibration(repo_root)
    written = build_all(script_dir, calib)
    print(f"[cogr-wave0] wrote {len(written)} figures to {script_dir}")
    for p in written:
        print(f"  - {p.name}")
    if calib is None:
        print(
            "[cogr-wave0] calibration_summary.json not found — figures include "
            "placeholder watermark."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
