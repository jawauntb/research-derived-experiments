#!/usr/bin/env python3
"""Generate Phase / Arc 2 Step 4 figures.

The figures are intentionally compact: they show gate margins rather than only
raw scores, so a reader can see exactly why the accepted agent/body passes and
why each control fails.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
CONCERNED_FIG_DIR = ROOT / "papers" / "concerned_syntax" / "figures"
BODIES_FIG_DIR = ROOT / "papers" / "viable_computational_bodies" / "figures"


def _metric_margins(
    rows: list[tuple[str, dict[str, float]]],
    metrics: list[tuple[str, str, str, float]],
) -> tuple[list[list[float]], list[list[str]]]:
    margins: list[list[float]] = []
    labels: list[list[str]] = []
    for _, values in rows:
        margin_row: list[float] = []
        label_row: list[str] = []
        for key, _, direction, threshold in metrics:
            value = values[key]
            margin = value - threshold if direction == "min" else threshold - value
            margin_row.append(margin)
            label_row.append(f"{value:.3f}")
        margins.append(margin_row)
        labels.append(label_row)
    return margins, labels


def _heatmap(
    *,
    rows: list[tuple[str, dict[str, float]]],
    metrics: list[tuple[str, str, str, float]],
    title: str,
    subtitle: str,
    out: Path,
) -> None:
    margins, labels = _metric_margins(rows, metrics)
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    image = ax.imshow(margins, cmap="RdYlGn", vmin=-0.35, vmax=0.35)
    ax.set_xticks(range(len(metrics)), [metric[1] for metric in metrics])
    ax.set_yticks(range(len(rows)), [row[0] for row in rows])
    ax.tick_params(axis="x", labelrotation=24, labelsize=10)
    ax.tick_params(axis="y", labelsize=10)
    ax.set_title(title, loc="left", fontsize=14, fontweight="bold", pad=18)
    ax.text(
        0.0,
        1.03,
        subtitle,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=10,
        color="#444444",
    )
    for row_idx, label_row in enumerate(labels):
        for col_idx, label in enumerate(label_row):
            margin = margins[row_idx][col_idx]
            text_color = "white" if abs(margin) > 0.22 else "#111111"
            ax.text(
                col_idx,
                row_idx,
                label,
                ha="center",
                va="center",
                color=text_color,
                fontsize=9.5,
                fontweight="bold",
            )
    ax.set_xlabel("Raw metric value; color shows margin to gate", fontsize=10)
    ax.set_frame_on(False)
    cbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.03)
    cbar.set_label("Gate margin", rotation=90)
    cbar.outline.set_visible(False)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)


def make_concerned_syntax_gate() -> None:
    rows = [
        (
            "concerned vector",
            {
                "parse_high": 1.000,
                "action": 1.000,
                "subtree": 0.804,
                "high_probe": 1.000,
                "low_probe": 0.189,
            },
        ),
        (
            "passive vector",
            {
                "parse_high": 0.492,
                "action": 0.873,
                "subtree": 0.500,
                "high_probe": 0.000,
                "low_probe": 0.000,
            },
        ),
        (
            "restless vector",
            {
                "parse_high": 1.000,
                "action": 1.000,
                "subtree": 1.000,
                "high_probe": 1.000,
                "low_probe": 1.000,
            },
        ),
        (
            "surface shortcut",
            {
                "parse_high": 0.492,
                "action": 0.876,
                "subtree": 0.500,
                "high_probe": 0.000,
                "low_probe": 0.000,
            },
        ),
    ]
    metrics = [
        ("parse_high", "parse high", "min", 0.75),
        ("action", "action", "min", 0.85),
        ("subtree", "subtree", "min", 0.75),
        ("high_probe", "high probe", "min", 0.70),
        ("low_probe", "low probe", "max", 0.25),
    ]
    _heatmap(
        rows=rows,
        metrics=metrics,
        title="Vector concerned-syntax gate margins",
        subtitle="Green cells clear the gate; red cells identify the anti-cheat failure.",
        out=CONCERNED_FIG_DIR / "fig1_vector_gate_margins.png",
    )


def make_module_body_gate() -> None:
    rows = [
        (
            "modular concerned",
            {
                "parse_high": 1.000,
                "action": 1.000,
                "low_probe": 0.189,
                "formal": 1.000,
                "modules": 0.950,
                "anti_cheat": 0.950,
            },
        ),
        (
            "passive vector",
            {
                "parse_high": 0.492,
                "action": 0.873,
                "low_probe": 0.000,
                "formal": 1.000,
                "modules": 0.450,
                "anti_cheat": 0.550,
            },
        ),
        (
            "restless vector",
            {
                "parse_high": 1.000,
                "action": 1.000,
                "low_probe": 1.000,
                "formal": 0.000,
                "modules": 0.800,
                "anti_cheat": 0.550,
            },
        ),
        (
            "surface reward",
            {
                "parse_high": 0.492,
                "action": 0.876,
                "low_probe": 0.000,
                "formal": 1.000,
                "modules": 0.250,
                "anti_cheat": 0.350,
            },
        ),
    ]
    metrics = [
        ("parse_high", "parse high", "min", 0.75),
        ("action", "action", "min", 0.85),
        ("low_probe", "low probe", "max", 0.25),
        ("formal", "formal", "min", 1.00),
        ("modules", "modules", "min", 0.80),
        ("anti_cheat", "anti-cheat", "min", 0.70),
    ]
    _heatmap(
        rows=rows,
        metrics=metrics,
        title="Vector module-body gate margins",
        subtitle="The accepted body is the only one that clears behavior, formal, module, and anti-cheat gates.",
        out=BODIES_FIG_DIR / "fig1_vector_module_gate_margins.png",
    )


def make_haskell_verdicts() -> None:
    bodies = ["guarded syntax", "restless tree", "modular concerned"]
    costs = [12, 12, 8]
    valid = [True, False, True]
    colors = ["#287c5f" if flag else "#b94b4b" for flag in valid]
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    bars = ax.barh(bodies, costs, color=colors, alpha=0.92)
    ax.axvline(12, color="#333333", linestyle="--", linewidth=1.1)
    ax.text(12.15, 2.35, "budget cap", fontsize=9, color="#333333")
    for bar, flag in zip(bars, valid):
        label = "valid" if flag else "missing calibration guard"
        ax.text(
            bar.get_width() + 0.25,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            ha="left",
            fontsize=10,
            color="#111111",
        )
    ax.set_title("Haskell typed-ontology verdicts", loc="left", fontsize=14, fontweight="bold")
    ax.set_xlabel("Resource cost")
    ax.set_xlim(0, 15.5)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", alpha=0.18)
    fig.tight_layout()
    out = BODIES_FIG_DIR / "fig2_haskell_ontology_verdicts.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    make_concerned_syntax_gate()
    make_module_body_gate()
    make_haskell_verdicts()
    print(f"Wrote {CONCERNED_FIG_DIR / 'fig1_vector_gate_margins.png'}")
    print(f"Wrote {BODIES_FIG_DIR / 'fig1_vector_module_gate_margins.png'}")
    print(f"Wrote {BODIES_FIG_DIR / 'fig2_haskell_ontology_verdicts.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
