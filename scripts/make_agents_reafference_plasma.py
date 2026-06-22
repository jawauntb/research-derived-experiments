#!/usr/bin/env python3
"""Generate a plasma-style concept figure for first-order self/reafference."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle


ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "papers" / "first_order_self" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Source:
    """A point source in the standing-wave field."""

    x: float
    y: float
    weight: float
    phase: float


@dataclass(frozen=True)
class Agent:
    """A visual agent with a first-order self loop."""

    name: str
    x: float
    y: float
    phase: float


AGENTS = (
    Agent("agent A", 0.26, 0.31, 0.15),
    Agent("agent B", 0.64, 0.54, 1.95),
    Agent("agent C", 0.78, 0.74, 3.35),
)

WORLD_SOURCES = (
    Source(0.18, 0.78, 0.95, 2.40),
    Source(0.86, 0.23, 0.80, 5.40),
)


def ramp(values: np.ndarray) -> np.ndarray:
    """Map normalized amplitudes in [-1, 1] onto the plasma color ramp."""

    stops = np.array([0.00, 0.34, 0.55, 0.78, 1.00])
    colors = np.array(
        [
            [5, 8, 34],
            [36, 101, 196],
            [72, 218, 226],
            [255, 179, 73],
            [255, 249, 236],
        ],
        dtype=float,
    )
    u = np.clip((values + 1.0) * 0.5, 0.0, 1.0)
    channels = [np.interp(u, stops, colors[:, i]) for i in range(3)]
    return np.stack(channels, axis=-1) / 255.0


def make_field(n: int = 84) -> np.ndarray:
    """Build a coarse standing-wave field like the objet d'art plasma page."""

    xs = np.linspace(0.0, 1.0, n)
    ys = np.linspace(0.0, 1.0, n)
    xx, yy = np.meshgrid(xs, ys)

    agent_sources = tuple(
        Source(agent.x, agent.y, 1.05, agent.phase) for agent in AGENTS
    )
    sources = agent_sources + WORLD_SOURCES

    amplitude = np.zeros_like(xx)
    for source in sources:
        distance = np.hypot(xx - source.x, yy - source.y)
        attenuation = 1.0 / np.sqrt(1.0 + distance * 7.0)
        wave = np.sin(distance * 45.0 + source.phase)
        amplitude += source.weight * wave * attenuation

    # Add a slow diagonal bias so the field reads as alive rather than radial.
    shear = 0.18 * np.sin((xx * 1.9 - yy * 1.4) * np.pi + 0.55)
    amplitude = (amplitude + shear) / 3.6
    return ramp(np.clip(amplitude, -1.0, 1.0))


def add_text(
    ax: plt.Axes,
    x: float,
    y: float,
    text: str,
    *,
    size: int = 10,
    color: str = "#f4eee3",
    ha: str = "center",
    va: str = "center",
    weight: str = "normal",
) -> None:
    """Draw legible label text on the plasma field."""

    ax.text(
        x,
        y,
        text,
        color=color,
        fontsize=size,
        ha=ha,
        va=va,
        weight=weight,
        family="DejaVu Sans Mono",
        path_effects=[pe.withStroke(linewidth=3, foreground="#030718", alpha=0.82)],
    )


def add_arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str,
    rad: float,
    linestyle: str = "-",
    alpha: float = 0.82,
    linewidth: float = 1.8,
) -> None:
    """Draw a curved process arrow."""

    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12,
        connectionstyle=f"arc3,rad={rad}",
        linewidth=linewidth,
        linestyle=linestyle,
        color=color,
        alpha=alpha,
        zorder=9,
    )
    ax.add_patch(arrow)


def add_agent(ax: plt.Axes, agent: Agent, *, annotate: bool) -> None:
    """Draw an agent as source, nested heads, and reafference loop."""

    x, y = agent.x, agent.y
    for radius, alpha in ((0.086, 0.09), (0.060, 0.16), (0.040, 0.24)):
        ax.add_patch(
            Circle((x, y), radius, facecolor="#f6f0df", edgecolor="none", alpha=alpha, zorder=6)
        )
    ax.add_patch(
        Circle(
            (x, y),
            0.052,
            facecolor=(0.95, 0.98, 1.0, 0.06),
            edgecolor=(0.96, 0.98, 1.0, 0.58),
            linewidth=1.2,
            zorder=7,
        )
    )
    ax.add_patch(Circle((x, y), 0.016, facecolor="#fffdf4", edgecolor="none", zorder=10))

    self_pos = (x - 0.040, y + 0.040)
    world_pos = (x + 0.040, y + 0.038)
    for end, color in ((self_pos, "#62eaf0"), (world_pos, "#ffbd61")):
        ax.plot([x, end[0]], [y, end[1]], color=color, alpha=0.44, linewidth=1.0, zorder=8)
        ax.add_patch(Circle(end, 0.010, facecolor=color, edgecolor="#f9f5e8", linewidth=0.4, zorder=10))

    add_arrow(
        ax,
        (x - 0.073, y - 0.012),
        (x + 0.073, y + 0.012),
        color="#66f0f2",
        rad=0.48,
        alpha=0.72,
        linewidth=1.45,
    )
    add_arrow(
        ax,
        (x + 0.070, y + 0.020),
        (x - 0.063, y - 0.020),
        color="#f8f0dc",
        rad=0.42,
        alpha=0.58,
        linewidth=1.25,
    )

    if annotate:
        add_text(ax, x + 0.092, y + 0.108, agent.name, size=8, ha="left", weight="bold")
    else:
        label_y = y - 0.086 if y > 0.38 else y + 0.090
        add_text(ax, x, label_y, agent.name, size=8, weight="bold")

    if annotate:
        add_text(ax, x - 0.165, y + 0.076, "efference copy", size=7, ha="left", color="#93fbff")
        add_text(ax, x + 0.070, y - 0.098, "reafference", size=7, ha="left", color="#fff2d4")
        add_text(ax, self_pos[0] - 0.042, self_pos[1] + 0.020, "self dE", size=7, ha="right", color="#93fbff")
        add_text(ax, world_pos[0] + 0.038, world_pos[1] + 0.010, "world dE", size=7, ha="left", color="#ffc875")


def main() -> int:
    field = make_field()

    fig, ax = plt.subplots(figsize=(8.4, 10.0), facecolor="#060a1e")
    ax.set_facecolor("#060a1e")

    # Soft bloom under the coarse cells.
    ax.imshow(field, extent=(0, 1, 0, 1), origin="lower", interpolation="bilinear", alpha=0.45)
    ax.imshow(field, extent=(0, 1, 0, 1), origin="lower", interpolation="nearest", alpha=0.96)

    # Dark glass edge like the plasma reference page.
    ax.add_patch(
        Rectangle(
            (0, 0),
            1,
            1,
            fill=False,
            edgecolor=(0.83, 0.92, 1.0, 0.35),
            linewidth=1.2,
            zorder=12,
        )
    )

    for source in WORLD_SOURCES:
        for radius, alpha in ((0.058, 0.16), (0.036, 0.25)):
            ax.add_patch(
                Circle((source.x, source.y), radius, facecolor="#ffb85a", edgecolor="none", alpha=alpha, zorder=5)
            )
        ax.add_patch(Circle((source.x, source.y), 0.012, facecolor="#ffd99a", edgecolor="#fff7e4", linewidth=0.6, zorder=10))
        add_text(ax, source.x, source.y + 0.080, "world shock", size=7, color="#ffd99a")

    for idx, agent in enumerate(AGENTS):
        add_agent(ax, agent, annotate=idx == 0)

    for source in WORLD_SOURCES:
        for agent in AGENTS:
            add_arrow(
                ax,
                (source.x, source.y),
                (agent.x, agent.y),
                color="#ffb861",
                rad=0.16 if source.x < agent.x else -0.16,
                linestyle=(0, (2.0, 3.0)),
                alpha=0.34,
                linewidth=1.1,
            )

    # Shared correction channel: agents do not just sense, they update a boundary.
    add_arrow(
        ax,
        (AGENTS[0].x + 0.055, AGENTS[0].y + 0.090),
        (AGENTS[1].x - 0.070, AGENTS[1].y - 0.055),
        color="#e9fff9",
        rad=-0.24,
        alpha=0.44,
        linewidth=1.25,
    )
    add_arrow(
        ax,
        (AGENTS[1].x + 0.072, AGENTS[1].y + 0.060),
        (AGENTS[2].x - 0.065, AGENTS[2].y - 0.065),
        color="#e9fff9",
        rad=0.20,
        alpha=0.44,
        linewidth=1.25,
    )
    add_text(ax, 0.49, 0.435, "prediction error", size=7, color="#e9fff9")

    add_text(
        ax,
        0.5,
        1.073,
        "first-order selves in a reafferent plasma",
        size=15,
        weight="bold",
    )
    add_text(
        ax,
        0.5,
        1.030,
        "self-caused loops and world-caused shocks occupy the same field",
        size=8,
        color="#c9c2b8",
    )
    add_text(
        ax,
        0.5,
        -0.044,
        "waves meet, sources move, attribution has to break the gauge",
        size=8,
        color="#c9c2b8",
    )

    ax.set_xlim(-0.035, 1.035)
    ax.set_ylim(-0.065, 1.095)
    ax.set_aspect("equal")
    ax.axis("off")

    out = FIG_DIR / "fig4_agents_reafference_plasma.png"
    fig.savefig(out, dpi=260, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
