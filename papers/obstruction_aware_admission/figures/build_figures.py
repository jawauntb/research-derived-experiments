#!/usr/bin/env python3
"""Build deterministic figures for the Obstruction-Aware Admission paper."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[3]
FIGURE_DIR = Path(__file__).resolve().parent
RESULTS = (
    ROOT
    / "experiments"
    / "obstruction_aware_admission"
    / "results"
    / "summary.json"
)

INK = "#18202a"
MUTED = "#5f6b76"
BLUE = "#2563eb"
TEAL = "#0f9d8a"
AMBER = "#d97706"
RED = "#c2413a"
PALE_BLUE = "#eaf1ff"
PALE_TEAL = "#e6f7f3"
PALE_AMBER = "#fff4df"
PALE_RED = "#fdecea"
GRID = "#d8dee8"


def _save(figure: plt.Figure, name: str) -> None:
    figure.savefig(
        FIGURE_DIR / name,
        dpi=220,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(figure)


def _box(
    axis: plt.Axes,
    *,
    center: tuple[float, float],
    size: tuple[float, float],
    text: str,
    face: str,
    edge: str,
    fontsize: float = 11,
) -> None:
    x, y = center
    width, height = size
    patch = FancyBboxPatch(
        (x - width / 2, y - height / 2),
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.025",
        facecolor=face,
        edgecolor=edge,
        linewidth=1.8,
    )
    axis.add_patch(patch)
    axis.text(
        x,
        y,
        text,
        ha="center",
        va="center",
        color=INK,
        fontsize=fontsize,
        weight="semibold",
        linespacing=1.25,
    )


def _arrow(
    axis: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = MUTED,
) -> None:
    axis.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=13,
            linewidth=1.5,
            color=color,
        )
    )


def build_contract() -> None:
    figure, axis = plt.subplots(figsize=(11.0, 7.2))
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")

    axis.text(
        0.5,
        0.965,
        "One control law, four typed outcomes",
        ha="center",
        va="top",
        fontsize=19,
        weight="bold",
        color=INK,
    )
    axis.text(
        0.5,
        0.92,
        "The selector never turns a budget limit into an impossibility claim.",
        ha="center",
        va="top",
        fontsize=10.5,
        color=MUTED,
    )

    _box(
        axis,
        center=(0.5, 0.82),
        size=(0.36, 0.10),
        text="Declared target, version space,\nexperiments, costs, budget",
        face=PALE_BLUE,
        edge=BLUE,
    )
    _box(
        axis,
        center=(0.5, 0.64),
        size=(0.34, 0.09),
        text="Is the target constant?",
        face="#f7f8fa",
        edge=INK,
    )
    _arrow(axis, (0.5, 0.77), (0.5, 0.69))

    _box(
        axis,
        center=(0.16, 0.64),
        size=(0.24, 0.09),
        text="RECOVERED\nreturn common target",
        face=PALE_TEAL,
        edge=TEAL,
        fontsize=10,
    )
    _arrow(axis, (0.33, 0.64), (0.285, 0.64), color=TEAL)
    axis.text(0.305, 0.665, "yes", color=TEAL, fontsize=9, ha="center")

    _box(
        axis,
        center=(0.5, 0.47),
        size=(0.34, 0.09),
        text="Is exact continuation cost infinite?",
        face="#f7f8fa",
        edge=INK,
    )
    _arrow(axis, (0.5, 0.595), (0.5, 0.52))
    axis.text(0.515, 0.555, "no", color=MUTED, fontsize=9)

    _box(
        axis,
        center=(0.84, 0.47),
        size=(0.25, 0.10),
        text="TERMINAL OBSTRUCTION\nreturn indistinguishable pair",
        face=PALE_RED,
        edge=RED,
        fontsize=9.5,
    )
    _arrow(axis, (0.67, 0.47), (0.705, 0.47), color=RED)
    axis.text(0.69, 0.495, "yes", color=RED, fontsize=9, ha="center")

    _box(
        axis,
        center=(0.5, 0.30),
        size=(0.34, 0.09),
        text="Does C* exceed remaining budget?",
        face="#f7f8fa",
        edge=INK,
    )
    _arrow(axis, (0.5, 0.425), (0.5, 0.35))
    axis.text(0.515, 0.385, "no", color=MUTED, fontsize=9)

    _box(
        axis,
        center=(0.16, 0.30),
        size=(0.25, 0.10),
        text="BUDGET INFEASIBLE\nreturn required cost",
        face=PALE_AMBER,
        edge=AMBER,
        fontsize=9.5,
    )
    _arrow(axis, (0.33, 0.30), (0.285, 0.30), color=AMBER)
    axis.text(0.305, 0.325, "yes", color=AMBER, fontsize=9, ha="center")

    _box(
        axis,
        center=(0.5, 0.12),
        size=(0.42, 0.10),
        text="ADMIT\nexperiment on a minimum worst-case-cost branch",
        face=PALE_BLUE,
        edge=BLUE,
        fontsize=10,
    )
    _arrow(axis, (0.5, 0.255), (0.5, 0.17), color=BLUE)
    axis.text(0.515, 0.215, "no", color=BLUE, fontsize=9)
    _save(figure, "fig1_control_contract.png")


def build_counterexample(receipt: dict[str, object]) -> None:
    screen = receipt["exhaustive_screen"]
    witness = screen["minimal_greedy_counterexample"]
    figure, axes = plt.subplots(1, 2, figsize=(11.2, 5.4))
    figure.suptitle(
        "The smallest strict counterexample to immediate pair-gain admission",
        fontsize=16,
        weight="bold",
        color=INK,
        y=0.985,
    )
    figure.text(
        0.5,
        0.91,
        (
            "Four worlds, two experiments, binary outcomes, target "
            "[1, 0, 0, 0], costs [1, 2]"
        ),
        ha="center",
        fontsize=10,
        color=MUTED,
    )
    figure.subplots_adjust(top=0.78, bottom=0.12, wspace=0.28)

    for axis, title, first, edge, pale in (
        (
            axes[0],
            "Greedy target-pair gain",
            "e0  (cost 1)",
            AMBER,
            PALE_AMBER,
        ),
        (
            axes[1],
            "Exact continuation cost",
            "e1  (cost 2)",
            BLUE,
            PALE_BLUE,
        ),
    ):
        axis.set_xlim(0, 1)
        axis.set_ylim(0, 1)
        axis.axis("off")
        axis.set_title(title, fontsize=13, weight="bold", color=edge, pad=14)
        _box(
            axis,
            center=(0.5, 0.75),
            size=(0.52, 0.12),
            text=first,
            face=pale,
            edge=edge,
            fontsize=12,
        )

    _box(
        axes[0],
        center=(0.26, 0.48),
        size=(0.34, 0.12),
        text="outcome 0\n{r2, r3} -> target 0",
        face=PALE_TEAL,
        edge=TEAL,
        fontsize=9.5,
    )
    _box(
        axes[0],
        center=(0.74, 0.48),
        size=(0.34, 0.12),
        text="outcome 1\n{r0, r1} unresolved",
        face=PALE_RED,
        edge=RED,
        fontsize=9.5,
    )
    _arrow(axes[0], (0.43, 0.69), (0.31, 0.55))
    _arrow(axes[0], (0.57, 0.69), (0.69, 0.55))
    _box(
        axes[0],
        center=(0.74, 0.24),
        size=(0.34, 0.11),
        text="must still run e1\nworst-case cost = 1 + 2 = 3",
        face=PALE_AMBER,
        edge=AMBER,
        fontsize=9.5,
    )
    _arrow(axes[0], (0.74, 0.42), (0.74, 0.30), color=AMBER)

    _box(
        axes[1],
        center=(0.26, 0.46),
        size=(0.34, 0.14),
        text="outcome 0\n{r1, r2, r3}\nall target 0",
        face=PALE_TEAL,
        edge=TEAL,
        fontsize=9.5,
    )
    _box(
        axes[1],
        center=(0.74, 0.46),
        size=(0.34, 0.14),
        text="outcome 1\n{r0}\ntarget 1",
        face=PALE_TEAL,
        edge=TEAL,
        fontsize=9.5,
    )
    _arrow(axes[1], (0.43, 0.69), (0.31, 0.54))
    _arrow(axes[1], (0.57, 0.69), (0.69, 0.54))
    axes[1].text(
        0.5,
        0.20,
        "worst-case cost = 2",
        ha="center",
        va="center",
        fontsize=12,
        color=BLUE,
        weight="bold",
    )
    figure.text(
        0.5,
        0.03,
        (
            f"Registered witness: {witness['problem_id']}. "
            "Immediate gain ignores the cost of the hard continuation branch."
        ),
        ha="center",
        fontsize=9,
        color=MUTED,
    )
    _save(figure, "fig2_minimal_counterexample.png")


def build_results(receipt: dict[str, object]) -> None:
    screen = receipt["exhaustive_screen"]
    counts = screen["counts"]
    recoverable = counts["recoverable_cases"]
    labels = [
        "Target-pair\ngreedy",
        "All-pair\ngreedy",
        "Fixed\norder",
    ]
    values = [
        100
        * counts["greedy_target_strict_counterexamples"]
        / recoverable,
        100 * counts["greedy_all_strict_counterexamples"] / recoverable,
        100 * counts["fixed_order_strict_counterexamples"] / recoverable,
    ]
    colors = [BLUE, AMBER, RED]
    figure, axis = plt.subplots(figsize=(9.6, 5.6))
    bars = axis.bar(labels, values, color=colors, width=0.62)
    axis.set_ylim(0, 52)
    axis.set_ylabel(
        "Recoverable systems with strictly higher worst-case cost (%)",
        color=INK,
    )
    axis.set_title(
        "Myopic admission is frequently, but not uniformly, suboptimal",
        fontsize=16,
        weight="bold",
        color=INK,
        pad=14,
    )
    axis.text(
        0.5,
        1.01,
        (
            f"{recoverable:,} recoverable systems inside the registered "
            "500,912-system boundary"
        ),
        transform=axis.transAxes,
        ha="center",
        va="bottom",
        fontsize=9.5,
        color=MUTED,
    )
    axis.grid(axis="y", color=GRID, linewidth=0.8)
    axis.set_axisbelow(True)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color(GRID)
    axis.spines["bottom"].set_color(GRID)
    axis.tick_params(colors=INK)
    for bar, value in zip(bars, values, strict=True):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.1,
            f"{value:.2f}%",
            ha="center",
            va="bottom",
            fontsize=11,
            weight="bold",
            color=INK,
        )
    axis.text(
        0.02,
        0.96,
        "Exact controller: 0 dominance failures",
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=9.5,
        color=TEAL,
        weight="bold",
    )
    _save(figure, "fig3_exhaustive_results.png")


def main() -> int:
    receipt = json.loads(RESULTS.read_text(encoding="utf-8"))
    build_contract()
    build_counterexample(receipt)
    build_results(receipt)
    for path in sorted(FIGURE_DIR.glob("fig*.png")):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
