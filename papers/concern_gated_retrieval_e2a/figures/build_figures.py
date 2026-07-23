"""Build dither-kit-styled figures for the Wave 1a (COGR-E2a) report.

This script emits six figures (fig1..fig6) as PNG pairs (_dark.png, _light.png)
into the same directory it lives in.  When
``experiments/concern_gated_retrieval_e2/wave1a/results/verdict.json`` is
present, the figures consume its per-family aggregates; when it is absent, all
figures render against in-file synthetic placeholder data and stamp a
"placeholder" watermark.

Aesthetic: identical to the Wave 0 build script — dither-kit inspired palette,
monospace typography, letter-spaced uppercase titles, hatch-fill overlays for
an ordered-dither feel.  Dither Kit itself is a React library, so this script
reimplements the look in matplotlib primitives.

The script is deterministic and safe to re-invoke; each call overwrites the
existing PNG pair.  Wave 1a style discipline: no figure describes the
mechanism as learned memory, meaning, or selfhood; every figure title labels
itself as a Wave 1a concern-recovery-screen artifact.  Oracle-ceiling arms
are always tagged as diagnostic-only and never promotable.
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
from matplotlib.patches import FancyBboxPatch, Rectangle


# ---------------------------------------------------------------------------
# Dither-kit inspired palette + typography (identical to Wave 0)
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
    """UPPERCASE with single-space letter-spacing.

    Matches the Wave 0 build script byte-for-byte: real spaces in the source
    string collapse to " / " so word boundaries remain readable at 8-bit-ish
    letter spacing.
    """
    upper = text.upper()
    out_chars: list[str] = []
    for i, ch in enumerate(upper):
        if ch == " ":
            out_chars.append(" / ")
        else:
            out_chars.append(ch)
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
        color=DITHER_PALETTE[1],
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
    return start.resolve().parents[3]


def _load_verdict(repo_root: Path) -> dict[str, Any] | None:
    """Load ``experiments/.../wave1a/results/verdict.json`` if present.

    The verdict schema is populated by the Wave 1a promotion harness once the
    confirmatory Modal sweep completes.  Before that point the figures render
    against synthetic placeholder data with a "placeholder" watermark.
    """
    path = (
        repo_root
        / "experiments"
        / "concern_gated_retrieval_e2"
        / "wave1a"
        / "results"
        / "verdict.json"
    )
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Preregistered constants (frozen at Wave 1a signature time)
# ---------------------------------------------------------------------------

# Copied from experiments/.../wave1a/promotion_harness.py :: WAVE1A_PREREGISTERED_THRESHOLDS.
# Duplicated here so the figures do not need to import the harness at build
# time — the values are frozen at preregistration signature and cannot change
# without a redesign.
FROZEN_THRESHOLDS: dict[str, dict[str, float]] = {
    "delayed_commitments": {
        "sigma_hat_multiplicative": 0.2080,
        "sigma_hat_best_matched": 0.0218,
        "delta_thresh_E2a": 0.04845,
    },
    "maintenance_fault": {
        "sigma_hat_multiplicative": 0.1483,
        "sigma_hat_best_matched": 0.0267,
        "delta_thresh_E2a": 0.05340,
    },
    "resource_constrained": {
        "sigma_hat_multiplicative": 0.2905,
        "sigma_hat_best_matched": 0.0250,
        "delta_thresh_E2a": 0.05000,
    },
}

FAMILIES: list[str] = [
    "delayed_commitments",
    "maintenance_fault",
    "resource_constrained",
]

# Preregistered coverage floor (PREREGISTRATION.md §5.1).
COVERAGE_FLOOR: float = 0.01

# The five Wave 1a conditions + the diagnostic ceiling.  Order matches
# PREREGISTRATION.md §4.  ``promotion_eligible=False`` on the oracle only.
E2A_CONDITIONS: list[dict[str, Any]] = [
    {
        "code": "C1",
        "name": "frozen_wrong",
        "role": "baseline",
        "promotion_eligible": True,
        "ceiling": False,
        "note": "Wave 0 wrong prior",
    },
    {
        "code": "C2a",
        "name": "online_learned_ips",
        "role": "candidate",
        "promotion_eligible": True,
        "ceiling": False,
        "note": "update_concern(ips)",
    },
    {
        "code": "C2b",
        "name": "online_learned_dr",
        "role": "candidate",
        "promotion_eligible": True,
        "ceiling": False,
        "note": "update_concern(dr)",
    },
    {
        "code": "C3",
        "name": "oracle",
        "role": "ceiling",
        "promotion_eligible": False,
        "ceiling": True,
        "note": "diagnostic only",
    },
    {
        "code": "C4",
        "name": "shuffled",
        "role": "control",
        "promotion_eligible": True,
        "ceiling": False,
        "note": "specificity control",
    },
    {
        "code": "C5",
        "name": "wrong_agent",
        "role": "control",
        "promotion_eligible": True,
        "ceiling": False,
        "note": "specificity control",
    },
]

VARIANTS: list[str] = ["online_learned_ips", "online_learned_dr"]

# Info-matched generic-signal comparators (PREREGISTRATION.md §5.3).
INFO_MATCHED_COMPARATORS: list[str] = [
    "info_matched_value",
    "info_matched_priority",
    "info_matched_recency",
]

# Gate identifiers (must match promotion_harness constants).
GATE_IDS: list[str] = [
    "G1_COVERAGE",
    "G2_PROPENSITY",
    "G3_SPECIFICITY_GENERIC",
    "G3_SPECIFICITY_WRONG_AGENT",
    "G4_PER_FAMILY_EFFECT",
    "G4_NO_FAMILY_REVERSAL",
]


# ---------------------------------------------------------------------------
# Figure 1 — E2a five-condition diagram
# ---------------------------------------------------------------------------


def _draw_conditions(theme: Theme, path: Path, has_data: bool) -> None:
    """Cards for the five Wave 1a conditions plus the oracle ceiling.

    Each card carries a role tag (baseline / candidate / control /
    ceiling) and a promotion-eligibility flag; the oracle card carries a
    "DIAGNOSTIC" flag because C3 is never a promotable claim.
    """
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    _apply_theme(fig, ax, theme)
    for spine in ax.spines.values():
        spine.set_visible(False)

    role_color = {
        "baseline": DITHER_PALETTE[3],  # violet
        "candidate": DITHER_PALETTE[1],  # orange
        "control": DITHER_PALETTE[2],  # cyan
        "ceiling": DITHER_PALETTE[6],  # red
    }
    role_hatch = {
        "baseline": HATCHES[3],
        "candidate": HATCHES[0],
        "control": HATCHES[1],
        "ceiling": HATCHES[2],
    }

    n = len(E2A_CONDITIONS)
    box_w = 0.135
    gap = (1.0 - n * box_w) / (n + 1)
    y_center = 0.52
    box_h = 0.42
    label_plate_h = 0.11

    for i, cond in enumerate(E2A_CONDITIONS):
        x = gap + i * (box_w + gap)
        color = role_color[cond["role"]]
        hatch = role_hatch[cond["role"]]

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
        # ordered-dither overlay
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

        # solid label plate for the condition code
        plate = FancyBboxPatch(
            (x + 0.004, y_center + box_h / 2 - label_plate_h - 0.01),
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
            y_center + box_h / 2 - label_plate_h / 2 - 0.01,
            cond["code"],
            ha="center",
            va="center",
            fontsize=10,
            color=theme.fg,
            weight="bold",
            family="monospace",
        )

        # solid inner plate so the condition name reads cleanly over the
        # hatched fill (matches the label-plate trick from Wave 0 Fig 1)
        inner_plate = FancyBboxPatch(
            (x + 0.006, y_center - 0.09),
            box_w - 0.012,
            0.16,
            boxstyle="round,pad=0.002,rounding_size=0.008",
            linewidth=0.6,
            edgecolor=theme.fg,
            facecolor=theme.bg,
            alpha=0.88,
        )
        ax.add_patch(inner_plate)

        # condition name centered in the body — auto-shrink for the long
        # online_learned_* labels so they fit inside the plate.
        name_fs = 7.5 if len(cond["name"]) <= 12 else 6.4
        ax.text(
            x + box_w / 2,
            y_center + 0.02,
            cond["name"],
            ha="center",
            va="center",
            fontsize=name_fs,
            color=theme.fg,
            weight="bold",
            family="monospace",
        )

        # role tag inside the box
        ax.text(
            x + box_w / 2,
            y_center - 0.05,
            cond["role"].upper(),
            ha="center",
            va="center",
            fontsize=7.0,
            color=color,
            weight="bold",
            family="monospace",
        )

        # promotion-eligibility flag on its own plate
        if cond["promotion_eligible"]:
            flag = "PROMOTABLE"
            flag_color = DITHER_PALETTE[5]  # lime
        else:
            flag = "DIAGNOSTIC"
            flag_color = DITHER_PALETTE[6]  # red
        flag_plate = FancyBboxPatch(
            (x + 0.010, y_center - box_h / 2 + 0.015),
            box_w - 0.020,
            0.055,
            boxstyle="round,pad=0.002,rounding_size=0.006",
            linewidth=0.6,
            edgecolor=flag_color,
            facecolor=theme.bg,
            alpha=0.90,
        )
        ax.add_patch(flag_plate)
        ax.text(
            x + box_w / 2,
            y_center - box_h / 2 + 0.043,
            flag,
            ha="center",
            va="center",
            fontsize=6.5,
            color=flag_color,
            weight="bold",
            family="monospace",
        )

        # sublabel under the card
        ax.text(
            x + box_w / 2,
            y_center - box_h / 2 - 0.04,
            cond["note"],
            ha="center",
            va="top",
            fontsize=7.0,
            color=theme.muted,
            family="monospace",
        )

    # Legend across the bottom explaining the role colours.
    legend_y = 0.10
    legend_items = [
        ("baseline", role_color["baseline"], role_hatch["baseline"]),
        ("candidate", role_color["candidate"], role_hatch["candidate"]),
        ("control", role_color["control"], role_hatch["control"]),
        ("ceiling", role_color["ceiling"], role_hatch["ceiling"]),
    ]
    x0 = 0.06
    swatch_w = 0.03
    for label, color, hatch in legend_items:
        rect = Rectangle(
            (x0, legend_y - 0.012),
            swatch_w,
            0.024,
            facecolor=color,
            edgecolor=theme.fg,
            linewidth=0.8,
            alpha=0.9,
        )
        ax.add_patch(rect)
        overlay = Rectangle(
            (x0, legend_y - 0.012),
            swatch_w,
            0.024,
            facecolor="none",
            edgecolor=theme.bg,
            hatch=hatch,
            linewidth=0.0,
        )
        ax.add_patch(overlay)
        ax.text(
            x0 + swatch_w + 0.006,
            legend_y,
            label,
            color=theme.fg,
            fontsize=8,
            va="center",
            family="monospace",
        )
        x0 += 0.20

    _stamp_title(
        ax,
        "Fig 1 — e2a conditions",
        "wave 1a §4 — one baseline, two candidates, one ceiling, two controls",
        theme,
    )
    _stamp_footer(
        fig,
        "oracle ceiling is diagnostic only — never a promotable claim.",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder")
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2 — oracle-distance trajectory per condition
# ---------------------------------------------------------------------------


def _distance_trajectories(
    verdict: dict[str, Any] | None,
) -> tuple[np.ndarray, dict[str, np.ndarray], bool]:
    """Return (episodes, per_condition_distance_curves, has_data).

    Distance is ``mu_hat(oracle, f) - mu_hat(condition, f)`` averaged across
    families and running-cumulative over the confirmatory seed order — a
    coarse diagnostic view of concern recovery over the 300-seed cell.

    When ``verdict`` supplies per-condition trajectory arrays the figure
    consumes them directly.  Otherwise it renders a placeholder that shows
    the expected shape without claiming a result: frozen-wrong stays flat,
    online-learned pulls down toward oracle, shuffled/wrong-agent wander,
    oracle is the y = 0 floor.
    """
    n = 300
    x = np.arange(n)
    curves: dict[str, np.ndarray] = {}
    has_data = False
    if verdict is not None:
        traj = verdict.get("trajectories", {})
        if isinstance(traj, dict) and traj:
            for cond in ("frozen_wrong", "online_learned_ips",
                         "online_learned_dr", "oracle", "shuffled",
                         "wrong_agent"):
                if cond in traj:
                    arr = np.asarray(traj[cond], dtype=float)
                    curves[cond] = arr
            if curves:
                has_data = True
                first_len = next(iter(curves.values())).shape[0]
                x = np.arange(first_len)
                return x, curves, has_data

    # Placeholder shapes (never claim a real result — just illustrate the
    # axes so the paper can be laid out before the sweep finishes).
    rng = np.random.default_rng(20260723)
    def _noise(scale: float) -> np.ndarray:
        return rng.normal(0.0, scale, size=n).cumsum() / (np.arange(1, n + 1))

    curves["oracle"] = np.zeros(n)  # by construction
    curves["frozen_wrong"] = 0.48 * np.ones(n) + _noise(0.02)
    curves["online_learned_ips"] = 0.48 * np.exp(-x / 90.0) + 0.10 + _noise(0.02)
    curves["online_learned_dr"] = 0.48 * np.exp(-x / 75.0) + 0.08 + _noise(0.02)
    curves["shuffled"] = 0.45 * np.ones(n) + _noise(0.03)
    curves["wrong_agent"] = 0.44 * np.ones(n) + _noise(0.03)
    return x, curves, has_data


def _draw_wrong_prior_trajectory(
    theme: Theme, path: Path, has_data: bool, verdict: dict[str, Any] | None
) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    _apply_theme(fig, ax, theme)

    x, curves, real = _distance_trajectories(verdict)
    has_data = has_data and real

    # Condition -> (colour, linestyle, hatch-marker).
    style: dict[str, tuple[str, str, str]] = {
        "oracle": (DITHER_PALETTE[5], "--", "o"),  # lime, ceiling
        "frozen_wrong": (DITHER_PALETTE[6], "-", "s"),  # red, baseline
        "online_learned_ips": (DITHER_PALETTE[1], "-", "^"),  # orange
        "online_learned_dr": (DITHER_PALETTE[2], "-", "D"),  # cyan
        "shuffled": (DITHER_PALETTE[3], ":", "x"),  # violet, control
        "wrong_agent": (DITHER_PALETTE[3], "-.", "P"),  # violet, control
    }

    # Plot in a specific z-order so candidates sit above controls but below
    # the ceiling reference line.
    order = [
        "shuffled",
        "wrong_agent",
        "frozen_wrong",
        "online_learned_dr",
        "online_learned_ips",
        "oracle",
    ]
    for cond in order:
        if cond not in curves:
            continue
        color, linestyle, _marker = style[cond]
        y = curves[cond]
        # decimate markers so the line reads as a line, not a scatter
        markevery = max(1, len(y) // 8)
        ax.plot(
            x,
            y,
            color=color,
            linestyle=linestyle,
            linewidth=1.6,
            marker=_marker,
            markersize=4,
            markevery=markevery,
            markerfacecolor=theme.bg,
            markeredgecolor=color,
            label=cond,
            alpha=0.95,
        )

    ax.axhline(
        0.0,
        color=theme.muted,
        linewidth=0.8,
        linestyle=":",
    )

    ax.set_xlabel("episode index (300 per family, aggregated)", color=theme.fg, fontsize=9)
    ax.set_ylabel(
        "oracle - condition mean reward (lower = closer to ceiling)",
        color=theme.fg,
        fontsize=9,
    )
    ax.set_xlim(0, x[-1] if len(x) > 0 else 300)

    leg = ax.legend(
        loc="upper right",
        frameon=True,
        facecolor=theme.bg,
        edgecolor=theme.fg,
        labelcolor=theme.fg,
        fontsize=7.5,
        ncol=2,
    )
    for txt in leg.get_texts():
        txt.set_fontfamily("monospace")

    _stamp_title(
        ax,
        "Fig 2 — wrong-prior trajectory",
        "distance to oracle per condition, averaged across families",
        theme,
    )
    _stamp_footer(
        fig,
        "oracle diagnostic only; frozen_wrong is the promotion baseline.",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder")
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3 — coverage audit with floor line
# ---------------------------------------------------------------------------


def _coverage_grid(
    verdict: dict[str, Any] | None,
) -> tuple[list[str], list[str], np.ndarray, bool]:
    """Return (families, receipt-producing-conditions, coverage_matrix, has_data).

    coverage_matrix[i, j] is the propensity-weighted coverage of the true
    commitment region for family[i] under condition[j].  Only receipt-
    producing conditions (§5.1: C2a, C2b, C4, C5) are audited.
    """
    receipt_conds = [
        "online_learned_ips",
        "online_learned_dr",
        "shuffled",
        "wrong_agent",
    ]
    families = list(FAMILIES)
    n_f, n_c = len(families), len(receipt_conds)
    if verdict is not None:
        cov = verdict.get("coverage", {})
        if isinstance(cov, dict) and cov:
            grid = np.zeros((n_f, n_c))
            found_any = False
            for i, fam in enumerate(families):
                fam_cov = cov.get(fam, {})
                for j, cond in enumerate(receipt_conds):
                    v = fam_cov.get(cond)
                    if v is not None:
                        grid[i, j] = float(v)
                        found_any = True
            if found_any:
                return families, receipt_conds, grid, True

    # Placeholder — every cell sits comfortably above the 0.01 floor to
    # illustrate the expected pass state, with a couple of near-floor
    # cells so the layout exercises the failure-tint branch.
    grid = np.array(
        [
            # ips    dr    shuf   wrong
            [0.048, 0.052, 0.031, 0.028],  # delayed_commitments
            [0.061, 0.058, 0.024, 0.019],  # maintenance_fault
            [0.045, 0.042, 0.014, 0.012],  # resource_constrained
        ]
    )
    return families, receipt_conds, grid, False


def _draw_coverage_audit(
    theme: Theme, path: Path, has_data: bool, verdict: dict[str, Any] | None
) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    _apply_theme(fig, ax, theme)

    families, conditions, grid, real = _coverage_grid(verdict)
    has_data = has_data and real

    n_f, n_c = grid.shape
    x = np.arange(n_c)
    group_gap = 0.18
    group_w = 1.0 - group_gap  # per-family total bar-cluster width
    bar_w = group_w / n_f

    family_color = {
        "delayed_commitments": DITHER_PALETTE[3],  # violet
        "maintenance_fault": DITHER_PALETTE[2],    # cyan
        "resource_constrained": DITHER_PALETTE[1],  # orange
    }
    family_hatch = {
        "delayed_commitments": HATCHES[3],
        "maintenance_fault": HATCHES[2],
        "resource_constrained": HATCHES[0],
    }

    y_max = max(float(grid.max()) * 1.35, COVERAGE_FLOOR * 6.0, 0.08)

    for i, fam in enumerate(families):
        offsets = x + (i - (n_f - 1) / 2.0) * bar_w
        values = grid[i, :]
        color = family_color.get(fam, DITHER_PALETTE[2])
        hatch = family_hatch.get(fam, HATCHES[0])

        bars = ax.bar(
            offsets,
            values,
            bar_w * 0.94,
            color=color,
            edgecolor=theme.fg,
            linewidth=0.9,
            alpha=0.90,
            hatch=hatch,
            label=fam,
        )
        # tint any below-floor cell red as a fail signal
        for bar, v in zip(bars, values):
            if v < COVERAGE_FLOOR:
                bar.set_facecolor(DITHER_PALETTE[6])  # red
                bar.set_hatch(HATCHES[2])
        # annotate the numeric coverage above every bar
        for xi, v in zip(offsets, values):
            ax.text(
                xi,
                v + y_max * 0.02,
                f"{v:0.3f}",
                ha="center",
                va="bottom",
                color=theme.fg,
                fontsize=7,
                family="monospace",
            )

    # Preregistered floor line.
    ax.axhline(
        COVERAGE_FLOOR,
        color=DITHER_PALETTE[6],  # red — the floor is a fail line
        linewidth=1.6,
        linestyle="--",
        label=f"floor = {COVERAGE_FLOOR:0.2f} (§5.1)",
    )

    ax.set_xticks(x)
    ax.set_xticklabels(conditions, fontsize=8, color=theme.fg, rotation=15, ha="right")
    ax.set_ylabel(
        "propensity-weighted coverage of TCR(f)",
        color=theme.fg,
        fontsize=9,
    )
    ax.set_ylim(0, y_max)

    leg = ax.legend(
        loc="upper right",
        frameon=True,
        facecolor=theme.bg,
        edgecolor=theme.fg,
        labelcolor=theme.fg,
        fontsize=7.5,
    )
    for txt in leg.get_texts():
        txt.set_fontfamily("monospace")

    _stamp_title(
        ax,
        "Fig 3 — coverage audit",
        "propensity-weighted coverage per (family, receipt-producing condition)",
        theme,
    )
    _stamp_footer(
        fig,
        "any cell below floor = pre-analysis rejection; >5% cell rejection = KILL.",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder")
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 4 — specificity contrast: online-learned vs generic signals
# ---------------------------------------------------------------------------


def _specificity_data(
    verdict: dict[str, Any] | None,
) -> tuple[np.ndarray, np.ndarray, bool]:
    """Return (grid, err_grid, has_data).

    grid[i, j, k] is the paired-seed mean delta for variant[k] vs comparator[j]
    on family[i]; err_grid is the cluster-robust SE for each cell.  Wave 1a
    reports every (variant, comparator, family) combination through the
    promotion harness.
    """
    n_f = len(FAMILIES)
    n_c = len(INFO_MATCHED_COMPARATORS)
    n_v = len(VARIANTS)

    grid = np.zeros((n_f, n_c, n_v))
    err = np.zeros((n_f, n_c, n_v))
    if verdict is not None:
        spec = verdict.get("specificity", {})
        if isinstance(spec, dict) and spec:
            found_any = False
            for i, fam in enumerate(FAMILIES):
                fam_spec = spec.get(fam, {})
                for j, comp in enumerate(INFO_MATCHED_COMPARATORS):
                    comp_spec = fam_spec.get(comp, {})
                    for k, var in enumerate(VARIANTS):
                        cell = comp_spec.get(var)
                        if isinstance(cell, dict):
                            grid[i, j, k] = float(cell.get("mean_delta", 0.0))
                            err[i, j, k] = float(cell.get("cluster_robust_se", 0.0))
                            found_any = True
            if found_any:
                return grid, err, True

    # Placeholder — every variant beats every info-matched comparator by a
    # small positive margin, with SE about 0.008 per cell.  Values chosen
    # to hover near, and mostly above, the per-family sigma_hat_best_matched
    # threshold so the layout exercises the near-threshold read.
    thresholds = np.array(
        [FROZEN_THRESHOLDS[fam]["sigma_hat_best_matched"] for fam in FAMILIES]
    )
    # per-family base delta with mild variant / comparator wobble
    for i, fam in enumerate(FAMILIES):
        base = thresholds[i] * 1.6
        for j, _comp in enumerate(INFO_MATCHED_COMPARATORS):
            for k, _var in enumerate(VARIANTS):
                jitter = 0.005 * ((j - 1) + 0.6 * (k - 0.5))
                grid[i, j, k] = base + jitter
                err[i, j, k] = 0.0085
    return grid, err, False


def _draw_specificity_contrast(
    theme: Theme, path: Path, has_data: bool, verdict: dict[str, Any] | None
) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    _apply_theme(fig, ax, theme)

    grid, err, real = _specificity_data(verdict)
    has_data = has_data and real
    n_f, n_c, n_v = grid.shape

    variant_color = {
        "online_learned_ips": DITHER_PALETTE[1],  # orange
        "online_learned_dr": DITHER_PALETTE[2],   # cyan
    }
    variant_hatch = {
        "online_learned_ips": HATCHES[0],
        "online_learned_dr": HATCHES[1],
    }

    # Grouping: x-axis = (family, comparator); bar clusters = variant.
    labels: list[str] = []
    for fam in FAMILIES:
        fam_short = {
            "delayed_commitments": "DC",
            "maintenance_fault": "MF",
            "resource_constrained": "RC",
        }.get(fam, fam[:2].upper())
        for comp in INFO_MATCHED_COMPARATORS:
            comp_short = comp.replace("info_matched_", "")
            labels.append(f"{fam_short}·{comp_short}")

    n_cells = n_f * n_c
    x = np.arange(n_cells)
    bar_w = 0.36

    for k, var in enumerate(VARIANTS):
        heights = []
        errs = []
        for i in range(n_f):
            for j in range(n_c):
                heights.append(grid[i, j, k])
                errs.append(err[i, j, k])
        offsets = x + (k - (n_v - 1) / 2.0) * bar_w
        ax.bar(
            offsets,
            heights,
            bar_w * 0.94,
            yerr=errs,
            capsize=2.0,
            color=variant_color[var],
            edgecolor=theme.fg,
            linewidth=0.9,
            alpha=0.90,
            hatch=variant_hatch[var],
            label=var,
            error_kw={"ecolor": theme.fg, "elinewidth": 0.9},
        )

    # per-family threshold overlays: draw a short horizontal segment across
    # each family's three-comparator span so the passing threshold is visible
    # in-place.  Threshold is sigma_hat_best_matched (§5.3, info-matched leg).
    for i, fam in enumerate(FAMILIES):
        thr = FROZEN_THRESHOLDS[fam]["sigma_hat_best_matched"]
        left = i * n_c - 0.5
        right = (i + 1) * n_c - 0.5
        ax.plot(
            [left, right],
            [thr, thr],
            color=DITHER_PALETTE[6],  # red
            linestyle="--",
            linewidth=1.4,
        )
        ax.text(
            (left + right) / 2.0,
            thr + 0.002,
            f"σ_best({fam[:2].upper()}) = {thr:0.4f}",
            ha="center",
            va="bottom",
            color=DITHER_PALETTE[6],
            fontsize=6.5,
            family="monospace",
        )

    ax.axhline(0.0, color=theme.muted, linewidth=0.6, linestyle=":")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7, color=theme.fg, rotation=45, ha="right")
    ax.set_ylabel(
        "paired-seed mean delta (variant - comparator)",
        color=theme.fg,
        fontsize=9,
    )

    leg = ax.legend(
        loc="upper right",
        frameon=True,
        facecolor=theme.bg,
        edgecolor=theme.fg,
        labelcolor=theme.fg,
        fontsize=7.5,
    )
    for txt in leg.get_texts():
        txt.set_fontfamily("monospace")

    _stamp_title(
        ax,
        "Fig 4 — specificity contrast",
        "online-learned variants vs value / priority / recency (§5.3)",
        theme,
    )
    _stamp_footer(
        fig,
        "bar - 2·SE must clear σ_best_matched on every (family, comparator) cell.",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder")
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 5 — per-family reversal check (variant vs frozen-wrong)
# ---------------------------------------------------------------------------


def _reversal_data(
    verdict: dict[str, Any] | None,
) -> tuple[np.ndarray, np.ndarray, bool]:
    """Return (delta, se, has_data) shaped (n_families, n_variants).

    Each cell is the paired-seed mean delta of variant vs frozen_wrong and its
    cluster-robust SE — the same quantity the family-effect gate scores.
    """
    n_f = len(FAMILIES)
    n_v = len(VARIANTS)
    delta = np.zeros((n_f, n_v))
    se = np.zeros((n_f, n_v))
    if verdict is not None:
        eff = verdict.get("family_effect", {})
        if isinstance(eff, dict) and eff:
            found = False
            for i, fam in enumerate(FAMILIES):
                fam_eff = eff.get(fam, {})
                for k, var in enumerate(VARIANTS):
                    row = fam_eff.get(var)
                    if isinstance(row, dict):
                        delta[i, k] = float(row.get("mean_delta", 0.0))
                        se[i, k] = float(row.get("cluster_robust_se", 0.0))
                        found = True
            if found:
                return delta, se, True

    # Placeholder — one variant clears the threshold on every family, the
    # other clears on two out of three (a shape that would trigger the
    # variant-level FAIL described in §6.3).  No family is in reversal.
    per_family_thresh = np.array(
        [FROZEN_THRESHOLDS[fam]["delta_thresh_E2a"] for fam in FAMILIES]
    )
    # IPS: comfortably above threshold on all families.
    delta[:, 0] = per_family_thresh * 1.55 + np.array([0.005, -0.003, 0.007])
    # DR: above on families 0 and 2, below on family 1.
    delta[:, 1] = np.array(
        [
            per_family_thresh[0] * 1.35,
            per_family_thresh[1] * 0.72,
            per_family_thresh[2] * 1.20,
        ]
    )
    se[:] = 0.012
    return delta, se, False


def _draw_family_reversal(
    theme: Theme, path: Path, has_data: bool, verdict: dict[str, Any] | None
) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    _apply_theme(fig, ax, theme)

    delta, se, real = _reversal_data(verdict)
    has_data = has_data and real
    n_f, n_v = delta.shape

    x = np.arange(n_f)
    bar_w = 0.36

    variant_color = {
        "online_learned_ips": DITHER_PALETTE[1],
        "online_learned_dr": DITHER_PALETTE[2],
    }
    variant_hatch = {
        "online_learned_ips": HATCHES[0],
        "online_learned_dr": HATCHES[1],
    }

    for k, var in enumerate(VARIANTS):
        offsets = x + (k - (n_v - 1) / 2.0) * bar_w
        heights = delta[:, k]
        errs = se[:, k]
        bars = ax.bar(
            offsets,
            heights,
            bar_w * 0.94,
            yerr=errs,
            capsize=2.5,
            color=variant_color[var],
            edgecolor=theme.fg,
            linewidth=0.9,
            alpha=0.90,
            hatch=variant_hatch[var],
            label=var,
            error_kw={"ecolor": theme.fg, "elinewidth": 0.9},
        )
        # highlight reversals (heights <= -threshold on that family)
        for i, bar in enumerate(bars):
            thr = FROZEN_THRESHOLDS[FAMILIES[i]]["delta_thresh_E2a"]
            if heights[i] <= -thr:
                bar.set_facecolor(DITHER_PALETTE[6])  # red
                bar.set_hatch(HATCHES[2])
                bar.set_edgecolor(DITHER_PALETTE[6])
                # star the reversal cell
                ax.text(
                    offsets[i],
                    heights[i] - errs[i] - 0.005,
                    "REVERSAL",
                    ha="center",
                    va="top",
                    color=DITHER_PALETTE[6],
                    fontsize=7,
                    weight="bold",
                    family="monospace",
                )

    # per-family delta_thresh_E2a line + zero line
    for i, fam in enumerate(FAMILIES):
        thr = FROZEN_THRESHOLDS[fam]["delta_thresh_E2a"]
        left, right = i - 0.5, i + 0.5
        ax.plot(
            [left, right],
            [thr, thr],
            color=DITHER_PALETTE[5],  # lime — the pass threshold
            linestyle="--",
            linewidth=1.5,
        )
        ax.plot(
            [left, right],
            [-thr, -thr],
            color=DITHER_PALETTE[6],  # red — the reversal threshold
            linestyle=":",
            linewidth=1.4,
        )
        ax.text(
            i,
            thr + 0.005,
            f"δ_thresh = {thr:0.4f}",
            ha="center",
            va="bottom",
            color=DITHER_PALETTE[5],
            fontsize=6.5,
            family="monospace",
        )

    ax.axhline(0.0, color=theme.muted, linewidth=0.7, linestyle=":")
    ax.set_xticks(x)
    ax.set_xticklabels(FAMILIES, fontsize=8.5, color=theme.fg)
    ax.set_ylabel(
        "paired-seed mean delta vs frozen_wrong",
        color=theme.fg,
        fontsize=9,
    )

    leg = ax.legend(
        loc="upper left",
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
        "Fig 5 — family reversal check",
        "per-family paired-seed delta; aggregate never hides a reversal",
        theme,
    )
    _stamp_footer(
        fig,
        "lime = §6.3 pass threshold; red dotted = §5.4 reversal threshold.",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder")
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 6 — promotion verdict: gate-by-gate KILL/PASS grid
# ---------------------------------------------------------------------------


def _verdict_grid(
    verdict: dict[str, Any] | None,
) -> tuple[list[str], list[str], np.ndarray, bool]:
    """Return (families, gate_labels, pass_matrix, has_data).

    pass_matrix[i, j] is 1.0 for PASS, 0.0 for FAIL, and -1.0 for NOT-SCORED
    (a gate that Wave 1a scores outside the family-scoped harness).
    """
    gate_labels = [
        "G1 coverage",
        "G2 propensity",
        "G3 spec / generic",
        "G3 spec / wrong-agent",
        "G4 per-family effect",
        "G4 no reversal",
    ]
    gate_ids = list(GATE_IDS)
    families = list(FAMILIES)
    n_f, n_g = len(families), len(gate_labels)
    matrix = np.full((n_f, n_g), -1.0)  # -1 sentinel: unscored
    if verdict is not None:
        per_family = verdict.get("per_family_verdicts", {})
        if isinstance(per_family, dict) and per_family:
            found = False
            for i, fam in enumerate(families):
                fam_v = per_family.get(fam)
                if not isinstance(fam_v, dict):
                    continue
                gates = fam_v.get("gates", {})
                if not isinstance(gates, dict):
                    continue
                for j, gid in enumerate(gate_ids):
                    row = gates.get(gid)
                    if isinstance(row, dict) and "passed" in row:
                        matrix[i, j] = 1.0 if bool(row["passed"]) else 0.0
                        found = True
                    elif isinstance(row, bool):
                        matrix[i, j] = 1.0 if row else 0.0
                        found = True
            if found:
                return families, gate_labels, matrix, True

    # Placeholder — a plausibly-passing pattern that still has one FAIL cell
    # so the KILL/PASS branch is visible.  Wave 1a's actual verdict replaces
    # this at first Modal-sweep receipt.
    matrix = np.array(
        [
            # G1   G2   G3g  G3w  G4e  G4r
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],  # delayed_commitments
            [1.0, 1.0, 1.0, 1.0, 0.0, 1.0],  # maintenance_fault: FAIL
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],  # resource_constrained
        ]
    )
    return families, gate_labels, matrix, False


def _draw_promotion_verdict(
    theme: Theme, path: Path, has_data: bool, verdict: dict[str, Any] | None
) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    _apply_theme(fig, ax, theme)

    families, gate_labels, matrix, real = _verdict_grid(verdict)
    has_data = has_data and real
    n_f, n_g = matrix.shape

    pass_color = DITHER_PALETTE[5]  # lime
    fail_color = DITHER_PALETTE[6]  # red
    skip_color = DITHER_PALETTE[3]  # violet
    pass_hatch = HATCHES[3]  # ...
    fail_hatch = HATCHES[2]  # xxx
    skip_hatch = HATCHES[4]  # ooo

    for r in range(n_f):
        for c in range(n_g):
            v = matrix[r, c]
            if v > 0.5:
                color, hatch, glyph = pass_color, pass_hatch, "PASS"
            elif v > -0.5:
                color, hatch, glyph = fail_color, fail_hatch, "FAIL"
            else:
                color, hatch, glyph = skip_color, skip_hatch, "n/a"
            rect = Rectangle(
                (c, n_f - 1 - r),
                1,
                1,
                facecolor=color,
                edgecolor=theme.bg,
                linewidth=1.6,
                alpha=0.90,
            )
            ax.add_patch(rect)
            overlay = Rectangle(
                (c, n_f - 1 - r),
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
                n_f - 1 - r + 0.5,
                glyph,
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

    ax.set_xlim(0, n_g)
    ax.set_ylim(0, n_f)
    ax.set_xticks(np.arange(n_g) + 0.5)
    ax.set_yticks(np.arange(n_f) + 0.5)
    ax.set_xticklabels(gate_labels, fontsize=8, color=theme.fg, rotation=20, ha="right")
    ax.set_yticklabels(list(reversed(families)), fontsize=8.5, color=theme.fg)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)

    # aggregate verdict banner across the top
    if has_data and verdict is not None:
        agg = verdict.get("aggregate", {})
        promoted = bool(agg.get("promoted", False)) if isinstance(agg, dict) else False
    else:
        # placeholder aggregate: KILL because one fail cell is present
        promoted = bool(np.all(matrix > 0.5))
    banner_color = pass_color if promoted else fail_color
    banner_text = "AGGREGATE: PROMOTE" if promoted else "AGGREGATE: KILL"
    ax.text(
        n_g / 2.0,
        n_f + 0.35,
        _title_case(banner_text),
        ha="center",
        va="bottom",
        color=banner_color,
        fontsize=11,
        weight="bold",
        family="monospace",
    )

    _stamp_title(
        ax,
        "Fig 6 — promotion verdict",
        "gate-by-gate KILL / PASS grid — non-compensatory (§5)",
        theme,
    )
    _stamp_footer(
        fig,
        "any FAIL cell = WAVE 1A KILL; only §7 replayable knobs may be rerun.",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder — replaced by Modal verdict")
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


FIG_NAMES = [
    "fig1_e2a_conditions",
    "fig2_wrong_prior_trajectory",
    "fig3_coverage_audit",
    "fig4_specificity_contrast",
    "fig5_family_reversal_check",
    "fig6_promotion_verdict",
]


def build_all(out_dir: Path, verdict: dict | None) -> list[Path]:
    _set_font_defaults()
    out_dir.mkdir(parents=True, exist_ok=True)
    has_data = verdict is not None
    written: list[Path] = []

    for theme in (DARK, LIGHT):
        p = out_dir / f"fig1_e2a_conditions_{theme.name}.png"
        _draw_conditions(theme, p, has_data)
        written.append(p)

        p = out_dir / f"fig2_wrong_prior_trajectory_{theme.name}.png"
        _draw_wrong_prior_trajectory(theme, p, has_data, verdict)
        written.append(p)

        p = out_dir / f"fig3_coverage_audit_{theme.name}.png"
        _draw_coverage_audit(theme, p, has_data, verdict)
        written.append(p)

        p = out_dir / f"fig4_specificity_contrast_{theme.name}.png"
        _draw_specificity_contrast(theme, p, has_data, verdict)
        written.append(p)

        p = out_dir / f"fig5_family_reversal_check_{theme.name}.png"
        _draw_family_reversal(theme, p, has_data, verdict)
        written.append(p)

        p = out_dir / f"fig6_promotion_verdict_{theme.name}.png"
        _draw_promotion_verdict(theme, p, has_data, verdict)
        written.append(p)

    return written


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    repo_root = _find_repo_root(script_dir)
    verdict = _load_verdict(repo_root)
    written = build_all(script_dir, verdict)
    print(f"[cogr-wave1a-e2a] wrote {len(written)} figures to {script_dir}")
    for p in written:
        print(f"  - {p.name}")
    if verdict is None:
        print(
            "[cogr-wave1a-e2a] verdict.json not found — figures include "
            "placeholder watermark."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
