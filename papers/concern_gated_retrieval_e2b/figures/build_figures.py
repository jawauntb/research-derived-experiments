"""Build dither-kit-styled figures for the Wave 1b (COGR-E2b) report.

Emits seven figures (fig1..fig7) as PNG pairs (_dark.png, _light.png) into
the same directory it lives in.  When
``experiments/concern_gated_retrieval_e2/wave1b/results/verdict.json`` is
present the figures consume its per-family aggregates; otherwise every
figure renders against in-file synthetic placeholder data and stamps a
"placeholder" watermark.

Aesthetic: identical to Wave 0 / Wave 1a — dither-kit inspired palette,
monospace typography, letter-spaced uppercase titles, hatch-fill overlays.
The palette + Theme dataclass are imported from the Wave 0 build script so
the three papers render as one system.  If the import fails for any reason
(script executed with a stripped PYTHONPATH, sibling paper renamed) the
local fallback block reproduces the same constants byte-for-byte.

Wave 1b style discipline:
  * L1 and L2 verdicts are issued separately; both figures 2 and 3 render
    even when one is a KILL — no aggregate hides a per-family reversal.
  * oracle_ceiling arms are tagged as diagnostic-only and never promotable.
  * no figure describes the mechanism as "learned memory", "meaning",
    or "selfhood" — every title labels itself as a Wave 1b crossed-design
    scaffolding artifact.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle


# ---------------------------------------------------------------------------
# Palette + Theme — import from Wave 0 if reachable, else local fallback
# ---------------------------------------------------------------------------

_WAVE0_FIG_DIR = (
    Path(__file__).resolve().parents[2]
    / "concern_gated_retrieval_wave0"
    / "figures"
)

try:
    if str(_WAVE0_FIG_DIR) not in sys.path:
        sys.path.insert(0, str(_WAVE0_FIG_DIR))
    from build_figures import (  # type: ignore[import-not-found]
        DITHER_PALETTE,
        HATCHES,
        DARK_BG,
        DARK_FG,
        DARK_MUTED,
        LIGHT_BG,
        LIGHT_FG,
        LIGHT_MUTED,
        FIG_SIZE,
        FIG_DPI,
        Theme,
        DARK,
        LIGHT,
        _apply_theme,
        _stamp_title,
        _stamp_placeholder,
        _stamp_footer,
        _set_font_defaults,
        _title_case,
    )
except Exception:  # pragma: no cover — pure-fallback branch
    DITHER_PALETTE: list[str] = [
        "#111827",
        "#F97316",
        "#22D3EE",
        "#A78BFA",
        "#F5F5F4",
        "#84CC16",
        "#EF4444",
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

    def _stamp_title(
        ax: Axes, title: str, subtitle: str | None, theme: Theme
    ) -> None:
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

    def _stamp_placeholder(
        fig: Figure, theme: Theme, note: str = "placeholder"
    ) -> None:
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
    cur = start.resolve()
    for _ in range(8):
        if (cur / "experiments").is_dir() and (cur / "papers").is_dir():
            return cur
        cur = cur.parent
    return start.resolve().parents[3]


def _load_verdict(repo_root: Path) -> dict[str, Any] | None:
    path = (
        repo_root
        / "experiments"
        / "concern_gated_retrieval_e2"
        / "wave1b"
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
# Preregistered constants (frozen at Wave 1b signature time)
# ---------------------------------------------------------------------------

FAMILIES: list[str] = [
    "delayed_commitments",
    "maintenance_fault",
    "resource_constrained",
]

FAMILY_SHORT: dict[str, str] = {
    "delayed_commitments": "DC",
    "maintenance_fault": "MF",
    "resource_constrained": "RC",
}

# Copied from PREREGISTRATION.md §11 — frozen at signature time; duplicated
# here so the figures do not need to import the harness at build time.
FROZEN_THRESHOLDS: dict[str, dict[str, float]] = {
    "delayed_commitments": {
        "mu_best": 0.5314,
        "sigma_best": 0.0218,
        "headroom": 0.4845,
        "delta_thresh_L1": 0.0484,
    },
    "maintenance_fault": {
        "mu_best": 0.5029,
        "sigma_best": 0.0267,
        "headroom": 0.4548,
        "delta_thresh_L1": 0.0534,
    },
    "resource_constrained": {
        "mu_best": 0.5750,
        "sigma_best": 0.0250,
        "headroom": 0.4291,
        "delta_thresh_L1": 0.0500,
    },
}

# E2b crossed factorial (PREREGISTRATION.md §5).
GEOMETRIES: list[str] = ["LEARNED", "FREQ_MATCHED_RANDOM", "ORACLE_WITHHELD"]
GEOMETRIES_LABEL: dict[str, str] = {
    "LEARNED": "learned",
    "FREQ_MATCHED_RANDOM": "freq-matched\nrandom",
    "ORACLE_WITHHELD": "oracle-withheld\n(ceiling)",
}

CONCERNS: list[str] = ["FROZEN_WRONG", "ONLINE_LEARNED", "ORACLE"]
CONCERNS_LABEL: dict[str, str] = {
    "FROZEN_WRONG": "frozen-wrong",
    "ONLINE_LEARNED": "online-learned\n(ips + dr)",
    "ORACLE": "oracle\n(ceiling)",
}

# L1 gate rows use frozen-wrong concern crossed with the three geometries
# (representation-contribution test).
L1_GATE_LABELS: list[str] = [
    "G0 integrity",
    "G1 L1_behavior",
    "G2 L1_representation",
    "G5 non_ceiling",
    "G6 bundle_awareness",
    "G8 robustness",
    "G9 leakage_audit",
]
L1_GATE_IDS: list[str] = [
    "G0_INTEGRITY",
    "G1_L1_BEHAVIOR",
    "G2_L1_REPRESENTATION",
    "G5_NON_CEILING",
    "G6_BUNDLE_AWARENESS",
    "G8_ROBUSTNESS",
    "G9_LEAKAGE_AUDIT",
]

# L2 gate rows use online-learned concern crossed with LEARNED geometry
# (recovery + specificity).
L2_GATE_LABELS: list[str] = [
    "G0 integrity",
    "G3 L2_recovery",
    "G4 L2_specificity",
    "G5 non_ceiling",
    "G6 bundle_awareness",
    "G7 adversarial",
    "G8 robustness",
]
L2_GATE_IDS: list[str] = [
    "G0_INTEGRITY",
    "G3_L2_RECOVERY",
    "G4_L2_SPECIFICITY",
    "G5_NON_CEILING",
    "G6_BUNDLE_AWARENESS",
    "G7_ADVERSARIAL",
    "G8_ROBUSTNESS",
]


# ---------------------------------------------------------------------------
# Figure 1 — 3x3 crossed-design grid
# ---------------------------------------------------------------------------


def _cell_kind(geometry: str, concern: str) -> str:
    """Classify a (geometry, concern) cell into one of five kinds.

    * ``l1``      — L1 gate row (frozen-wrong x non-ceiling geometry)
    * ``l2``      — L2 gate row (online-learned x LEARNED)
    * ``geom_c``  — geometry ceiling only (oracle-withheld, non-L2 concern)
    * ``conc_c``  — concern ceiling only (oracle concern, non-oracle geometry)
    * ``both_c``  — both ceilings (oracle x oracle)
    * ``diag``    — everything else (diagnostic-only cross)
    """
    if concern == "ORACLE" and geometry == "ORACLE_WITHHELD":
        return "both_c"
    if concern == "ORACLE":
        return "conc_c"
    if geometry == "ORACLE_WITHHELD":
        return "geom_c"
    if concern == "FROZEN_WRONG":
        return "l1"
    if concern == "ONLINE_LEARNED" and geometry == "LEARNED":
        return "l2"
    return "diag"


def _draw_crossed_design(theme: Theme, path: Path, has_data: bool) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    _apply_theme(fig, ax, theme)
    for spine in ax.spines.values():
        spine.set_visible(False)

    kind_color = {
        "l1": DITHER_PALETTE[1],       # orange — L1 promotion path
        "l2": DITHER_PALETTE[2],       # cyan   — L2 promotion path
        "diag": DITHER_PALETTE[3],     # violet — diagnostic cross
        "geom_c": DITHER_PALETTE[6],   # red    — geometry ceiling only
        "conc_c": DITHER_PALETTE[6],   # red    — concern ceiling only
        "both_c": DITHER_PALETTE[6],   # red    — both ceilings
    }
    kind_hatch = {
        "l1": HATCHES[0],
        "l2": HATCHES[1],
        "diag": HATCHES[3],
        "geom_c": HATCHES[2],
        "conc_c": HATCHES[2],
        "both_c": HATCHES[2],
    }
    kind_glyph = {
        "l1": "L1",
        "l2": "L2",
        "diag": "diag",
        "geom_c": "geom-cap",
        "conc_c": "conc-cap",
        "both_c": "ceiling",
    }
    kind_promo = {
        "l1": "PROMOTABLE",
        "l2": "PROMOTABLE",
        "diag": "DIAGNOSTIC",
        "geom_c": "DIAGNOSTIC",
        "conc_c": "DIAGNOSTIC",
        "both_c": "DIAGNOSTIC",
    }

    # 3x3 layout with room on the left / bottom for axis labels.
    grid_left, grid_right = 0.20, 0.96
    grid_bottom, grid_top = 0.16, 0.78
    grid_w = grid_right - grid_left
    grid_h = grid_top - grid_bottom
    n = 3
    cell_w = grid_w / n
    cell_h = grid_h / n
    pad = 0.008

    # Axis labels: concerns (columns) across the top, geometries (rows) down
    # the side.  Rows go top-to-bottom in list order.
    for j, concern in enumerate(CONCERNS):
        cx = grid_left + (j + 0.5) * cell_w
        ax.text(
            cx,
            grid_top + 0.045,
            _title_case(CONCERNS_LABEL[concern]),
            ha="center",
            va="bottom",
            color=theme.fg,
            fontsize=7.5,
            weight="bold",
            family="monospace",
        )
    for i, geometry in enumerate(GEOMETRIES):
        cy = grid_top - (i + 0.5) * cell_h
        ax.text(
            grid_left - 0.02,
            cy,
            _title_case(GEOMETRIES_LABEL[geometry]),
            ha="right",
            va="center",
            color=theme.fg,
            fontsize=7.5,
            weight="bold",
            family="monospace",
        )

    # Column / row category headers
    ax.text(
        (grid_left + grid_right) / 2.0,
        grid_top + 0.10,
        _title_case("concern axis"),
        ha="center",
        va="bottom",
        color=theme.muted,
        fontsize=8,
        family="monospace",
    )
    ax.text(
        grid_left - 0.15,
        (grid_top + grid_bottom) / 2.0,
        _title_case("geometry axis"),
        ha="center",
        va="center",
        rotation=90,
        color=theme.muted,
        fontsize=8,
        family="monospace",
    )

    # Cell rectangles
    for i, geometry in enumerate(GEOMETRIES):
        for j, concern in enumerate(CONCERNS):
            kind = _cell_kind(geometry, concern)
            x = grid_left + j * cell_w + pad
            y = grid_top - (i + 1) * cell_h + pad
            w = cell_w - 2 * pad
            h = cell_h - 2 * pad

            base = FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.004,rounding_size=0.010",
                linewidth=1.1,
                edgecolor=theme.fg,
                facecolor=kind_color[kind],
                alpha=0.85,
            )
            ax.add_patch(base)
            overlay = FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.004,rounding_size=0.010",
                linewidth=0.0,
                edgecolor="none",
                facecolor="none",
                hatch=kind_hatch[kind],
            )
            overlay.set_edgecolor(theme.bg)
            ax.add_patch(overlay)

            # Solid inner plate so labels read cleanly above the hatch.
            plate_h = min(0.055, h * 0.45)
            plate = FancyBboxPatch(
                (x + 0.006, y + h - plate_h - 0.005),
                w - 0.012,
                plate_h,
                boxstyle="round,pad=0.002,rounding_size=0.006",
                linewidth=0.6,
                edgecolor=theme.fg,
                facecolor=theme.bg,
                alpha=0.90,
            )
            ax.add_patch(plate)
            ax.text(
                x + w / 2.0,
                y + h - plate_h / 2.0 - 0.005,
                kind_glyph[kind],
                ha="center",
                va="center",
                fontsize=8.5,
                color=theme.fg,
                weight="bold",
                family="monospace",
            )

            # N=300 sub-caption
            ax.text(
                x + w / 2.0,
                y + h / 2.0 - 0.010,
                "N = 300",
                ha="center",
                va="center",
                fontsize=7.0,
                color=theme.fg,
                family="monospace",
            )
            ax.text(
                x + w / 2.0,
                y + h / 2.0 - 0.036,
                "x 3 families",
                ha="center",
                va="center",
                fontsize=6.5,
                color=theme.fg,
                family="monospace",
            )

            # Promotion-eligibility flag at the bottom.
            promo = kind_promo[kind]
            flag_color = (
                DITHER_PALETTE[5] if promo == "PROMOTABLE" else DITHER_PALETTE[6]
            )
            flag_h = 0.030
            flag = FancyBboxPatch(
                (x + 0.010, y + 0.006),
                w - 0.020,
                flag_h,
                boxstyle="round,pad=0.001,rounding_size=0.004",
                linewidth=0.5,
                edgecolor=flag_color,
                facecolor=theme.bg,
                alpha=0.92,
            )
            ax.add_patch(flag)
            ax.text(
                x + w / 2.0,
                y + 0.006 + flag_h / 2.0,
                promo,
                ha="center",
                va="center",
                fontsize=6.0,
                color=flag_color,
                weight="bold",
                family="monospace",
            )

    # Legend at the bottom for the four cell kinds.
    legend_y = 0.08
    legend_items = [
        ("l1 promotion row", "l1"),
        ("l2 promotion row", "l2"),
        ("diagnostic cross", "diag"),
        ("ceiling cell", "both_c"),
    ]
    x0 = 0.06
    swatch_w = 0.03
    for label, kind in legend_items:
        rect = Rectangle(
            (x0, legend_y - 0.010),
            swatch_w,
            0.020,
            facecolor=kind_color[kind],
            edgecolor=theme.fg,
            linewidth=0.8,
            alpha=0.9,
        )
        ax.add_patch(rect)
        overlay = Rectangle(
            (x0, legend_y - 0.010),
            swatch_w,
            0.020,
            facecolor="none",
            edgecolor=theme.bg,
            hatch=kind_hatch[kind],
            linewidth=0.0,
        )
        ax.add_patch(overlay)
        ax.text(
            x0 + swatch_w + 0.006,
            legend_y,
            label,
            color=theme.fg,
            fontsize=7.5,
            va="center",
            family="monospace",
        )
        x0 += 0.235

    _stamp_title(
        ax,
        "Fig 1 — crossed design",
        "geometry x concern x family — 9 x 3 = 27 cells, N = 300 seeds each",
        theme,
    )
    _stamp_footer(
        fig,
        "L1 and L2 verdicts issued separately (§9); ceiling cells never promotable.",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder")
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figures 2 and 3 — L1 / L2 gate PASS / KILL heatmaps
# ---------------------------------------------------------------------------


def _gate_matrix(
    verdict: dict[str, Any] | None,
    verdict_key: str,
    gate_ids: list[str],
    placeholder: np.ndarray,
) -> tuple[np.ndarray, bool]:
    """Return (matrix, has_data).

    ``matrix[i, j]`` = 1.0 PASS, 0.0 FAIL, -1.0 not-scored (n/a).
    ``verdict_key`` is the top-level dict under ``verdict`` that holds the
    per-family, per-gate breakdown — either ``l1_per_family_verdicts`` or
    ``l2_per_family_verdicts``.
    """
    n_f, n_g = len(FAMILIES), len(gate_ids)
    matrix = np.full((n_f, n_g), -1.0)
    if verdict is not None:
        per_family = verdict.get(verdict_key, {})
        if isinstance(per_family, dict) and per_family:
            found = False
            for i, fam in enumerate(FAMILIES):
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
                return matrix, True
    return placeholder.copy(), False


def _draw_gate_grid(
    theme: Theme,
    path: Path,
    has_data: bool,
    matrix: np.ndarray,
    gate_labels: list[str],
    fig_index: int,
    verdict_label: str,
    subtitle: str,
    banner_key: str,
    verdict: dict[str, Any] | None,
) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    _apply_theme(fig, ax, theme)

    n_f, n_g = matrix.shape

    pass_color = DITHER_PALETTE[5]
    fail_color = DITHER_PALETTE[6]
    skip_color = DITHER_PALETTE[3]
    pass_hatch = HATCHES[3]
    fail_hatch = HATCHES[2]
    skip_hatch = HATCHES[4]

    for r in range(n_f):
        for c in range(n_g):
            v = matrix[r, c]
            if v > 0.5:
                color, hatch, glyph = pass_color, pass_hatch, "PASS"
            elif v > -0.5:
                color, hatch, glyph = fail_color, fail_hatch, "KILL"
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
    ax.set_xticklabels(
        gate_labels, fontsize=7.5, color=theme.fg, rotation=25, ha="right"
    )
    ax.set_yticklabels(list(reversed(FAMILIES)), fontsize=8.5, color=theme.fg)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)

    # Aggregate PROMOTE / KILL banner across the top.
    if has_data and verdict is not None:
        agg = verdict.get(banner_key, {})
        promoted = (
            bool(agg.get("promoted", False)) if isinstance(agg, dict) else False
        )
    else:
        # Placeholder aggregate is PROMOTE only when every scored gate passes
        # (n/a rows are ignored — they carry no evidence either way).
        scored = matrix >= -0.5
        pos = matrix > 0.5
        promoted = bool(np.all(pos[scored])) and bool(np.any(scored))
    banner_color = pass_color if promoted else fail_color
    banner_text = (
        f"{verdict_label}: PROMOTE" if promoted else f"{verdict_label}: KILL"
    )
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
        f"Fig {fig_index} — {verdict_label.lower()} verdict",
        subtitle,
        theme,
    )
    _stamp_footer(
        fig,
        "any KILL cell = non-compensatory failure; only §11 replayable knobs may be rerun.",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder")
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


def _draw_l1_verdict(
    theme: Theme, path: Path, has_data: bool, verdict: dict[str, Any] | None
) -> None:
    # Placeholder: near-passing pattern with one KILL cell so the branch is
    # visible.  Wave 1b's actual verdict replaces this at first Modal receipt.
    placeholder = np.array(
        [
            # G0   G1   G2   G5   G6   G8   G9
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],  # delayed_commitments
            [1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0],  # maintenance_fault (fail G6)
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],  # resource_constrained
        ]
    )
    matrix, real = _gate_matrix(
        verdict, "l1_per_family_verdicts", L1_GATE_IDS, placeholder
    )
    _draw_gate_grid(
        theme,
        path,
        has_data and real,
        matrix,
        L1_GATE_LABELS,
        2,
        "L1",
        "gate-by-gate KILL / PASS grid — non-compensatory (§9 L1)",
        "l1_aggregate",
        verdict,
    )


def _draw_l2_verdict(
    theme: Theme, path: Path, has_data: bool, verdict: dict[str, Any] | None
) -> None:
    # Placeholder: L2 leans harder into KILL — the family redesign passes
    # G0/G3, but specificity / bundle-awareness / adversarial each fail on at
    # least one family so the KILL branch reads.
    placeholder = np.array(
        [
            # G0   G3   G4   G5   G6   G7   G8
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],  # delayed_commitments
            [1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0],  # maintenance_fault (spec fail)
            [1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0],  # resource_constrained (bundle)
        ]
    )
    matrix, real = _gate_matrix(
        verdict, "l2_per_family_verdicts", L2_GATE_IDS, placeholder
    )
    _draw_gate_grid(
        theme,
        path,
        has_data and real,
        matrix,
        L2_GATE_LABELS,
        3,
        "L2",
        "gate-by-gate KILL / PASS grid — blocked if L1 KILLs (§9 L2)",
        "l2_aggregate",
        verdict,
    )


# ---------------------------------------------------------------------------
# Figure 4 — per-family outcome deltas
# ---------------------------------------------------------------------------


def _family_delta_data(
    verdict: dict[str, Any] | None,
) -> tuple[np.ndarray, np.ndarray, bool]:
    """Return (delta, se, has_data) shaped (n_families, n_geometries).

    Each cell is the paired-seed mean delta of the candidate mechanism
    (multiplicative_ppr) vs the best matched-budget baseline on that family,
    on the non-ceiling geometries (LEARNED, FREQ_MATCHED_RANDOM).  Oracle
    geometry is included as a diagnostic ceiling.
    """
    n_f, n_g = len(FAMILIES), len(GEOMETRIES)
    delta = np.zeros((n_f, n_g))
    se = np.zeros((n_f, n_g))
    if verdict is not None:
        eff = verdict.get("l1_family_effect", {})
        if isinstance(eff, dict) and eff:
            found = False
            for i, fam in enumerate(FAMILIES):
                fam_eff = eff.get(fam, {})
                for j, geom in enumerate(GEOMETRIES):
                    row = fam_eff.get(geom)
                    if isinstance(row, dict):
                        delta[i, j] = float(row.get("mean_delta", 0.0))
                        se[i, j] = float(row.get("cluster_robust_se", 0.0))
                        found = True
            if found:
                return delta, se, True

    per_family_thresh = np.array(
        [FROZEN_THRESHOLDS[f]["delta_thresh_L1"] for f in FAMILIES]
    )
    # LEARNED comfortably above threshold; FREQ_MATCHED_RANDOM sits just above
    # threshold on one family and just below on another so the KILL / PASS
    # boundary is visible; ORACLE_WITHHELD shown as a ceiling (large positive).
    delta[:, 0] = per_family_thresh * 1.75 + np.array([0.006, -0.002, 0.004])
    delta[:, 1] = np.array(
        [
            per_family_thresh[0] * 1.20,
            per_family_thresh[1] * 0.85,
            per_family_thresh[2] * 1.05,
        ]
    )
    delta[:, 2] = per_family_thresh * 2.45  # ceiling — diagnostic only
    se[:] = 0.010
    return delta, se, False


def _draw_family_reversal(
    theme: Theme, path: Path, has_data: bool, verdict: dict[str, Any] | None
) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    _apply_theme(fig, ax, theme)

    delta, se, real = _family_delta_data(verdict)
    has_data = has_data and real
    n_f, n_g = delta.shape

    x = np.arange(n_f)
    bar_w = 0.26

    geom_color = {
        "LEARNED": DITHER_PALETTE[1],              # orange — L1 candidate path
        "FREQ_MATCHED_RANDOM": DITHER_PALETTE[2],  # cyan   — control geometry
        "ORACLE_WITHHELD": DITHER_PALETTE[3],      # violet — ceiling
    }
    geom_hatch = {
        "LEARNED": HATCHES[0],
        "FREQ_MATCHED_RANDOM": HATCHES[1],
        "ORACLE_WITHHELD": HATCHES[2],
    }

    for j, geom in enumerate(GEOMETRIES):
        offsets = x + (j - (n_g - 1) / 2.0) * bar_w
        heights = delta[:, j]
        errs = se[:, j]
        color = geom_color[geom]
        hatch = geom_hatch[geom]
        bars = ax.bar(
            offsets,
            heights,
            bar_w * 0.94,
            yerr=errs,
            capsize=2.0,
            color=color,
            edgecolor=theme.fg,
            linewidth=0.9,
            alpha=0.90,
            hatch=hatch,
            label=geom.replace("_", " ").lower(),
            error_kw={"ecolor": theme.fg, "elinewidth": 0.9},
        )
        # tag ceiling geometry with a DIAGNOSTIC label per bar
        if geom == "ORACLE_WITHHELD":
            for xi, h in zip(offsets, heights):
                ax.text(
                    xi,
                    h + max(errs) + 0.005,
                    "DIAG",
                    ha="center",
                    va="bottom",
                    color=DITHER_PALETTE[3],
                    fontsize=6.5,
                    weight="bold",
                    family="monospace",
                )
        # star reversal cells on non-ceiling geometry
        if geom in ("LEARNED", "FREQ_MATCHED_RANDOM"):
            for i, bar in enumerate(bars):
                thr = FROZEN_THRESHOLDS[FAMILIES[i]]["delta_thresh_L1"]
                if heights[i] <= -thr:
                    bar.set_facecolor(DITHER_PALETTE[6])
                    bar.set_hatch(HATCHES[2])
                    bar.set_edgecolor(DITHER_PALETTE[6])
                    ax.text(
                        offsets[i],
                        heights[i] - errs[i] - 0.005,
                        "REVERSAL",
                        ha="center",
                        va="top",
                        color=DITHER_PALETTE[6],
                        fontsize=6.5,
                        weight="bold",
                        family="monospace",
                    )

    # per-family delta_thresh_L1 pass line (lime) + reversal line (red)
    for i, fam in enumerate(FAMILIES):
        thr = FROZEN_THRESHOLDS[fam]["delta_thresh_L1"]
        left, right = i - 0.5, i + 0.5
        ax.plot(
            [left, right],
            [thr, thr],
            color=DITHER_PALETTE[5],
            linestyle="--",
            linewidth=1.5,
        )
        ax.plot(
            [left, right],
            [-thr, -thr],
            color=DITHER_PALETTE[6],
            linestyle=":",
            linewidth=1.4,
        )
        ax.text(
            i,
            thr + 0.005,
            f"δ_L1 = {thr:0.4f}",
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
        "paired-seed Δ_task (candidate − best matched baseline)",
        color=theme.fg,
        fontsize=9,
    )

    leg = ax.legend(
        loc="upper left",
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
        "Fig 4 — family reversal check",
        "per-family Δ_task per geometry; aggregate never hides a reversal",
        theme,
    )
    _stamp_footer(
        fig,
        "lime = §9 G1 pass threshold; red dotted = reversal threshold; ceiling tagged DIAG.",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder")
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 5 — leakage audit control distributions
# ---------------------------------------------------------------------------


def _leakage_null_distributions(
    verdict: dict[str, Any] | None,
) -> tuple[np.ndarray, np.ndarray, float, float, bool]:
    """Return (perm_null, rand_null, observed_perm, observed_rand, has_data).

    ``perm_null`` and ``rand_null`` are 1-D arrays of the bootstrap statistic
    (learned-edge oracle_recall_at_k on non-load-bearing nodes) under the
    label-permutation and randomized-generator controls respectively.  The
    observed statistic is the same quantity on the real Wave 1b sweep.
    """
    if verdict is not None:
        audit = verdict.get("leakage_audit", {})
        if isinstance(audit, dict) and audit:
            try:
                perm_null = np.asarray(audit["label_permutation"]["null"], dtype=float)
                rand_null = np.asarray(
                    audit["randomized_generator"]["null"], dtype=float
                )
                observed_perm = float(audit["label_permutation"]["observed"])
                observed_rand = float(audit["randomized_generator"]["observed"])
                return perm_null, rand_null, observed_perm, observed_rand, True
            except Exception:
                pass

    rng = np.random.default_rng(20260724)
    # Null distributions: PPR restart on permuted / randomised inputs should
    # sit at chance for k = 3 out of ~20 candidates -> ~0.15.  Draw 2 000
    # bootstrap replicates centered there with mild spread.
    n = 2000
    perm_null = np.clip(rng.normal(0.15, 0.045, size=n), 0.0, 1.0)
    rand_null = np.clip(rng.normal(0.16, 0.050, size=n), 0.0, 1.0)
    # Observed: comfortably inside the null envelope -> pass.  A live-sweep
    # observation outside the 99th percentile would fire G9.
    observed_perm = 0.18
    observed_rand = 0.19
    return perm_null, rand_null, observed_perm, observed_rand, False


def _draw_leakage_audit(
    theme: Theme, path: Path, has_data: bool, verdict: dict[str, Any] | None
) -> None:
    fig, axes = plt.subplots(
        1, 2, figsize=(FIG_SIZE[0], FIG_SIZE[1] * 0.95), dpi=FIG_DPI, sharey=True
    )
    fig.patch.set_facecolor(theme.bg)

    perm_null, rand_null, observed_perm, observed_rand, real = (
        _leakage_null_distributions(verdict)
    )
    has_data = has_data and real

    panels = [
        (
            axes[0],
            perm_null,
            observed_perm,
            "label permutation",
            DITHER_PALETTE[2],  # cyan
            HATCHES[0],
        ),
        (
            axes[1],
            rand_null,
            observed_rand,
            "randomised generator",
            DITHER_PALETTE[3],  # violet
            HATCHES[1],
        ),
    ]

    global_max = max(float(perm_null.max()), float(rand_null.max()))
    global_min = min(float(perm_null.min()), float(rand_null.min()))
    span = max(0.05, global_max - global_min)
    x_lo = max(0.0, global_min - 0.10 * span)
    x_hi = min(1.0, global_max + 0.20 * span)

    for ax, null, observed, title, color, hatch in panels:
        _apply_theme(fig, ax, theme)
        counts, bin_edges = np.histogram(null, bins=32, range=(x_lo, x_hi))
        widths = np.diff(bin_edges)
        ax.bar(
            bin_edges[:-1],
            counts,
            widths,
            align="edge",
            color=color,
            edgecolor=theme.fg,
            linewidth=0.6,
            alpha=0.85,
            hatch=hatch,
        )

        # 99th-percentile fail line (upper tail — a large recall would mean
        # the learned edge has smuggled label information).
        p99 = float(np.quantile(null, 0.99))
        ax.axvline(
            p99,
            color=DITHER_PALETTE[6],
            linewidth=1.4,
            linestyle="--",
        )
        ax.text(
            p99,
            counts.max() * 1.02,
            f"p99 = {p99:0.3f}",
            ha="left",
            va="bottom",
            color=DITHER_PALETTE[6],
            fontsize=7,
            family="monospace",
            rotation=90,
        )

        # Observed statistic marker.
        in_fail = observed > p99
        obs_color = DITHER_PALETTE[6] if in_fail else DITHER_PALETTE[5]
        ax.axvline(
            observed,
            color=obs_color,
            linewidth=2.0,
            linestyle="-",
        )
        ax.text(
            observed,
            counts.max() * 0.95,
            f"observed\n= {observed:0.3f}\n{'FAIL' if in_fail else 'PASS'}",
            ha="left" if observed < (x_lo + x_hi) / 2.0 else "right",
            va="top",
            color=obs_color,
            fontsize=7.5,
            weight="bold",
            family="monospace",
        )

        ax.set_title(
            _title_case(title),
            color=theme.fg,
            fontsize=10,
            loc="left",
            pad=10,
        )
        ax.set_xlim(x_lo, x_hi)
        ax.set_xlabel(
            "learned-edge oracle_recall_at_k (control)",
            color=theme.fg,
            fontsize=8,
        )

    axes[0].set_ylabel(
        "bootstrap frequency (2 000 replicates)", color=theme.fg, fontsize=8
    )

    # Overall figure title placed above the two panels.
    fig.suptitle(
        _title_case("Fig 5 — leakage audit"),
        color=theme.fg,
        fontsize=12,
        x=0.02,
        ha="left",
        y=0.995,
        weight="bold",
        family="monospace",
    )
    fig.text(
        0.02,
        0.960,
        "permutation + randomised-generator controls with observed statistic",
        color=theme.muted,
        fontsize=8,
        ha="left",
        family="monospace",
    )

    _stamp_footer(
        fig,
        "observed > p99 on either control fires §9 G9 leakage_audit and KILLs L1.",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder")
    fig.tight_layout(rect=(0.0, 0.03, 1.0, 0.94))
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 6 — top-edge intervention: outcome delta
# ---------------------------------------------------------------------------


def _intervention_data(
    verdict: dict[str, Any] | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    """Return (baseline, ablated, se, has_data) shaped (n_families,).

    ``baseline[i]`` is mean Δ_task on family[i] with the intact learned graph;
    ``ablated[i]`` is mean Δ_task with the top-scoring learned edge removed
    (§9 G2).  The predicted direction is baseline > ablated.
    """
    n_f = len(FAMILIES)
    baseline = np.zeros(n_f)
    ablated = np.zeros(n_f)
    se = np.zeros(n_f)
    if verdict is not None:
        interv = verdict.get("intervention_top_edge", {})
        if isinstance(interv, dict) and interv:
            found = False
            for i, fam in enumerate(FAMILIES):
                row = interv.get(fam)
                if isinstance(row, dict):
                    baseline[i] = float(row.get("delta_baseline", 0.0))
                    ablated[i] = float(row.get("delta_ablated", 0.0))
                    se[i] = float(row.get("cluster_robust_se", 0.0))
                    found = True
            if found:
                return baseline, ablated, se, True

    per_family_thresh = np.array(
        [FROZEN_THRESHOLDS[f]["delta_thresh_L1"] for f in FAMILIES]
    )
    # baseline sits above delta_thresh_L1 on every family; ablation drops it
    # meaningfully so the G2 direction check passes on ≥ 70% of episodes.
    baseline[:] = per_family_thresh * 1.6
    ablated[:] = per_family_thresh * 0.5
    se[:] = 0.010
    return baseline, ablated, se, False


def _draw_intervention_edge(
    theme: Theme, path: Path, has_data: bool, verdict: dict[str, Any] | None
) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    _apply_theme(fig, ax, theme)

    baseline, ablated, se, real = _intervention_data(verdict)
    has_data = has_data and real
    n_f = len(FAMILIES)

    x = np.arange(n_f)
    bar_w = 0.34

    ax.bar(
        x - bar_w / 2.0,
        baseline,
        bar_w * 0.96,
        yerr=se,
        capsize=2.0,
        color=DITHER_PALETTE[1],
        edgecolor=theme.fg,
        linewidth=0.9,
        alpha=0.90,
        hatch=HATCHES[0],
        label="intact learned graph",
        error_kw={"ecolor": theme.fg, "elinewidth": 0.9},
    )
    ax.bar(
        x + bar_w / 2.0,
        ablated,
        bar_w * 0.96,
        yerr=se,
        capsize=2.0,
        color=DITHER_PALETTE[3],
        edgecolor=theme.fg,
        linewidth=0.9,
        alpha=0.90,
        hatch=HATCHES[3],
        label="top-edge ablated",
        error_kw={"ecolor": theme.fg, "elinewidth": 0.9},
    )

    # Arrow from baseline to ablated on each family so the direction reads.
    for i in range(n_f):
        y_high = baseline[i]
        y_low = ablated[i]
        color = DITHER_PALETTE[5] if y_high > y_low else DITHER_PALETTE[6]
        ax.add_patch(
            FancyArrowPatch(
                (i - bar_w / 2.0, y_high + se[i] + 0.008),
                (i + bar_w / 2.0, y_low + se[i] + 0.008),
                arrowstyle="->",
                mutation_scale=12,
                color=color,
                linewidth=1.4,
            )
        )
        drop = y_high - y_low
        ax.text(
            i,
            max(y_high, y_low) + max(se) + 0.020,
            f"Δ = {drop:+.4f}",
            ha="center",
            va="bottom",
            color=color,
            fontsize=7.5,
            weight="bold",
            family="monospace",
        )

    # per-family delta_thresh_L1 line as a passing reference
    for i, fam in enumerate(FAMILIES):
        thr = FROZEN_THRESHOLDS[fam]["delta_thresh_L1"]
        left, right = i - 0.5, i + 0.5
        ax.plot(
            [left, right],
            [thr, thr],
            color=DITHER_PALETTE[5],
            linestyle="--",
            linewidth=1.2,
        )

    ax.axhline(0.0, color=theme.muted, linewidth=0.6, linestyle=":")
    ax.set_xticks(x)
    ax.set_xticklabels(FAMILIES, fontsize=8.5, color=theme.fg)
    ax.set_ylabel("mean Δ_task per family", color=theme.fg, fontsize=9)

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
        "Fig 6 — top-edge intervention",
        "ablating the top-scoring learned edge — Δ_task drop is the G2 signal",
        theme,
    )
    _stamp_footer(
        fig,
        "§9 G2 passes iff the ablation drops Δ_task in the predicted direction on ≥ 70% of episodes.",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder")
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 7 — cost vs effect: matched-budget curve
# ---------------------------------------------------------------------------


def _cost_effect_data(
    verdict: dict[str, Any] | None,
) -> tuple[
    np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, bool
]:
    """Return (budgets, cand_mean, cand_se, ranker_mean, ranker_se, has_data).

    ``budgets`` are integer retrieval budgets k ∈ {1, 2, 3, 4, 5}.  Candidate
    is ``multiplicative_ppr``; ``ranker`` is ``learned_one_stage`` — the
    matched-parameter learned baseline that the §9 G1 gate compares against.
    Curves are averaged across families.
    """
    budgets = np.array([1, 2, 3, 4, 5], dtype=int)
    if verdict is not None:
        cost = verdict.get("cost_effect", {})
        if isinstance(cost, dict) and cost:
            try:
                cand = cost.get("multiplicative_ppr", {})
                rank = cost.get("learned_one_stage", {})
                cand_mean = np.array(
                    [float(cand["mean"][str(int(b))]) for b in budgets]
                )
                cand_se = np.array(
                    [float(cand["se"][str(int(b))]) for b in budgets]
                )
                ranker_mean = np.array(
                    [float(rank["mean"][str(int(b))]) for b in budgets]
                )
                ranker_se = np.array(
                    [float(rank["se"][str(int(b))]) for b in budgets]
                )
                return (
                    budgets,
                    cand_mean,
                    cand_se,
                    ranker_mean,
                    ranker_se,
                    True,
                )
            except Exception:
                pass

    # Placeholder shapes: both curves rise with budget; the candidate sits
    # above the learned ranker at the frozen k = 3 mark by roughly the mean
    # delta_thresh_L1 across families (≈ 0.05).
    mean_thr = float(
        np.mean([FROZEN_THRESHOLDS[f]["delta_thresh_L1"] for f in FAMILIES])
    )
    cand_base = np.array([0.28, 0.44, 0.55, 0.60, 0.62])
    ranker = cand_base - np.array(
        [0.02, 0.03, mean_thr * 1.10, 0.045, 0.040]
    )
    cand_se_arr = np.array([0.014, 0.013, 0.011, 0.011, 0.011])
    ranker_se = np.array([0.015, 0.014, 0.013, 0.012, 0.012])
    return budgets, cand_base, cand_se_arr, ranker, ranker_se, False


def _draw_cost_vs_effect(
    theme: Theme, path: Path, has_data: bool, verdict: dict[str, Any] | None
) -> None:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=FIG_DPI)
    _apply_theme(fig, ax, theme)

    budgets, cand_mean, cand_se, ranker_mean, ranker_se, real = (
        _cost_effect_data(verdict)
    )
    has_data = has_data and real

    # Candidate curve
    ax.errorbar(
        budgets,
        cand_mean,
        yerr=cand_se,
        color=DITHER_PALETTE[1],
        linestyle="-",
        linewidth=1.8,
        marker="o",
        markersize=6,
        markerfacecolor=theme.bg,
        markeredgecolor=DITHER_PALETTE[1],
        capsize=3.0,
        label="multiplicative_ppr (candidate)",
    )
    # Learned-one-stage ranker
    ax.errorbar(
        budgets,
        ranker_mean,
        yerr=ranker_se,
        color=DITHER_PALETTE[2],
        linestyle="--",
        linewidth=1.6,
        marker="s",
        markersize=5,
        markerfacecolor=theme.bg,
        markeredgecolor=DITHER_PALETTE[2],
        capsize=3.0,
        label="learned_one_stage (matched-param baseline)",
    )

    # Fill between the two curves so the effect gap reads at a glance.
    ax.fill_between(
        budgets,
        cand_mean,
        ranker_mean,
        where=(cand_mean >= ranker_mean),
        color=DITHER_PALETTE[1],
        alpha=0.14,
        interpolate=True,
        hatch=HATCHES[0],
        edgecolor=DITHER_PALETTE[1],
        linewidth=0.0,
    )
    ax.fill_between(
        budgets,
        cand_mean,
        ranker_mean,
        where=(cand_mean < ranker_mean),
        color=DITHER_PALETTE[6],
        alpha=0.18,
        interpolate=True,
        hatch=HATCHES[2],
        edgecolor=DITHER_PALETTE[6],
        linewidth=0.0,
    )

    # Frozen k = 3 vertical
    ax.axvline(3.0, color=theme.muted, linestyle=":", linewidth=1.0)
    ax.text(
        3.0,
        max(cand_mean.max(), ranker_mean.max()) * 1.02,
        "k = 3\n(frozen budget)",
        ha="center",
        va="bottom",
        color=theme.muted,
        fontsize=7.5,
        family="monospace",
    )

    # Annotate the effect gap at k = 3.
    k_idx = int(np.where(budgets == 3)[0][0])
    gap = cand_mean[k_idx] - ranker_mean[k_idx]
    gap_color = DITHER_PALETTE[5] if gap > 0 else DITHER_PALETTE[6]
    ax.annotate(
        f"gap @ k=3\n= {gap:+.4f}",
        xy=(3.0, (cand_mean[k_idx] + ranker_mean[k_idx]) / 2.0),
        xytext=(3.7, (cand_mean[k_idx] + ranker_mean[k_idx]) / 2.0),
        color=gap_color,
        fontsize=7.5,
        weight="bold",
        family="monospace",
        arrowprops=dict(arrowstyle="->", color=gap_color, lw=1.0),
    )

    ax.set_xlabel(
        "retrieval budget k (matched across policies)",
        color=theme.fg,
        fontsize=9,
    )
    ax.set_ylabel(
        "mean Δ_task (averaged across families)",
        color=theme.fg,
        fontsize=9,
    )
    ax.set_xticks(list(budgets))

    leg = ax.legend(
        loc="lower right",
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
        "Fig 7 — cost vs effect",
        "matched-budget curve: candidate mechanism vs learned one-stage ranker",
        theme,
    )
    _stamp_footer(
        fig,
        "positive gap at k = 3 required for §9 G1; oracle_pair_ranker refused by promotion harness.",
        theme,
    )
    if not has_data:
        _stamp_placeholder(fig, theme, "placeholder")
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


FIG_NAMES: list[str] = [
    "fig1_crossed_design",
    "fig2_l1_verdict",
    "fig3_l2_verdict",
    "fig4_family_reversal",
    "fig5_leakage_audit",
    "fig6_intervention_edge",
    "fig7_cost_vs_effect",
]


def build_all(out_dir: Path, verdict: dict | None) -> list[Path]:
    _set_font_defaults()
    out_dir.mkdir(parents=True, exist_ok=True)
    has_data = verdict is not None
    written: list[Path] = []

    for theme in (DARK, LIGHT):
        p = out_dir / f"fig1_crossed_design_{theme.name}.png"
        _draw_crossed_design(theme, p, has_data)
        written.append(p)

        p = out_dir / f"fig2_l1_verdict_{theme.name}.png"
        _draw_l1_verdict(theme, p, has_data, verdict)
        written.append(p)

        p = out_dir / f"fig3_l2_verdict_{theme.name}.png"
        _draw_l2_verdict(theme, p, has_data, verdict)
        written.append(p)

        p = out_dir / f"fig4_family_reversal_{theme.name}.png"
        _draw_family_reversal(theme, p, has_data, verdict)
        written.append(p)

        p = out_dir / f"fig5_leakage_audit_{theme.name}.png"
        _draw_leakage_audit(theme, p, has_data, verdict)
        written.append(p)

        p = out_dir / f"fig6_intervention_edge_{theme.name}.png"
        _draw_intervention_edge(theme, p, has_data, verdict)
        written.append(p)

        p = out_dir / f"fig7_cost_vs_effect_{theme.name}.png"
        _draw_cost_vs_effect(theme, p, has_data, verdict)
        written.append(p)

    return written


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    repo_root = _find_repo_root(script_dir)
    verdict = _load_verdict(repo_root)
    written = build_all(script_dir, verdict)
    print(f"[cogr-wave1b-e2b] wrote {len(written)} figures to {script_dir}")
    for p in written:
        print(f"  - {p.name}")
    if verdict is None:
        print(
            "[cogr-wave1b-e2b] verdict.json not found — figures include "
            "placeholder watermark."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
