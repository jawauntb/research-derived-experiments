#!/usr/bin/env python3
"""Build Future-Commitment Quotient figures from the public exact summary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = (
    ROOT / "experiments" / "future_commitment_quotient" / "results" / "summary.json"
)
FIGURE_DIR = ROOT / "papers" / "future_commitment_quotient" / "figures"
CONDITION_GRID = (("RP_CP", "RP_CA"), ("RD_CP", "RD_CA"))


def _setup() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 180,
            "savefig.dpi": 220,
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "axes.edgecolor": "#475569",
            "axes.grid": True,
            "grid.color": "#e2e8f0",
            "grid.linewidth": 0.7,
            "axes.axisbelow": True,
        }
    )


def _save(figure: Any, name: str) -> Path:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURE_DIR / name
    figure.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return path


def _condition_matrix(
    cells: dict[str, Any],
    metric: str,
) -> np.ndarray:
    return np.asarray(
        [[cells[condition][metric] for condition in row] for row in CONDITION_GRID],
        dtype=np.float64,
    )


def figure_factorial(summary: dict[str, Any]) -> Path:
    _setup()
    cells = summary["condition_metrics"]
    matrix = _condition_matrix(
        cells,
        "behavioral_disagreement_mean",
    )
    quotient = _condition_matrix(
        cells,
        "quotient_agreement_mean",
    )
    figure, axis = plt.subplots(figsize=(6.8, 3.6))
    image = axis.imshow(matrix, vmin=0.0, vmax=1.0, cmap="RdYlGn_r")
    axis.set_xticks([0, 1], ["Constraint preserved", "Constraint altered"])
    axis.set_yticks([0, 1], ["Coordinates preserved", "Coordinates destroyed"])
    axis.set_title("Behavior follows the future quotient, not coordinate identity")
    for row in range(2):
        for column in range(2):
            axis.text(
                column,
                row,
                f"behavior diff = {matrix[row, column]:.3f}\n"
                f"quotient = {quotient[row, column]:.3f}",
                ha="center",
                va="center",
                color="#0f172a",
                weight="bold",
                fontsize=8.2,
            )
    colorbar = figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    colorbar.set_label("fraction of aligned states with a future witness")
    return _save(figure, "fig1_factorial.png")


def figure_predictors(summary: dict[str, Any]) -> Path:
    _setup()
    order = (
        "coordinate_geometry",
        "current_output_agreement",
        "depth_one_agreement",
        "quotient_agreement",
    )
    labels = (
        "Coordinate\ngeometry",
        "Current\noutput",
        "Depth-one\noutput",
        "Exact\nquotient",
    )
    values = [float(summary["predictors"][name]["balanced_accuracy"]) for name in order]
    colors = ["#94a3b8", "#94a3b8", "#94a3b8", "#2563eb"]
    figure, axis = plt.subplots(figsize=(6.8, 3.4))
    bars = axis.bar(range(len(values)), values, color=colors, width=0.62)
    axis.axhline(0.5, color="#b91c1c", linestyle="--", linewidth=1.2, label="chance")
    axis.set_xticks(range(len(values)), labels)
    axis.set_ylim(0.0, 1.08)
    axis.set_ylabel("leave-one-family-out balanced accuracy")
    axis.set_title("Only exhaustive quotient agreement separates the factorial")
    axis.legend(loc="upper left")
    for bar, value in zip(bars, values, strict=True):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.025,
            f"{value:.3f}",
            ha="center",
            va="bottom",
            weight="bold",
        )
    return _save(figure, "fig2_predictors.png")


def main() -> int:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    outputs = [figure_factorial(summary), figure_predictors(summary)]
    for output in outputs:
        print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
