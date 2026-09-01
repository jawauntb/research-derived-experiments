"""Calibration: dwell on dots, fit a ridge model, refuse a bad fit.

The dot UI uses Tkinter (stdlib) so calibration needs no extra GUI dependency.
The scheduling and acceptance logic is separated from the UI so it can be
tested headlessly.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from ..geometry import Rect
from .regress import RidgeModel, save_calibration

__all__ = [
    "MAX_MEDIAN_RESIDUAL_PT",
    "CalibrationPlan",
    "CalibrationResult",
    "grid_targets",
    "fit_calibration",
    "collect_samples",
    "run_calibration",
]

MAX_MEDIAN_RESIDUAL_PT = 120.0
"""Refuse to save a fit worse than this: a model that cannot pick a screen
third is worse than no model, because it makes crops confidently wrong."""


def grid_targets(screen: Rect, points: int = 9, margin: float = 0.08) -> list[tuple[float, float]]:
    """Evenly spaced dot positions, inset from the edges, in boustrophedon order.

    ``points`` must be a perfect square (9 or 16). The inset matters: users
    cannot comfortably fixate the extreme corners of a laptop screen, and
    samples taken there drag the polynomial around. Alternating row direction
    keeps the eye's travel between dots short.
    """
    side = int(round(points**0.5))
    if side * side != points:
        raise ValueError("points must be a perfect square (9 or 16)")
    if side < 2:
        raise ValueError("need at least a 2x2 grid")
    xs = [screen.x + screen.w * (margin + (1 - 2 * margin) * i / (side - 1)) for i in range(side)]
    ys = [screen.y + screen.h * (margin + (1 - 2 * margin) * j / (side - 1)) for j in range(side)]
    return [(x, y) for j, y in enumerate(ys) for x in (xs if j % 2 == 0 else list(reversed(xs)))]


@dataclass
class CalibrationPlan:
    """Timing for one calibration run."""

    dwell_seconds: float = 1.5
    settle_seconds: float = 0.5
    """Discarded at the start of each dot, while the eyes are still moving."""
    samples_per_dot: int = 30
    points: int = 9


@dataclass
class CalibrationResult:
    """Outcome of a calibration attempt."""

    model: RidgeModel | None
    residual_px: float
    accepted: bool
    reason: str = ""
    samples: int = 0
    reference_features: list[float] = field(default_factory=list)


def fit_calibration(
    samples: Sequence[tuple[Sequence[float], tuple[float, float]]],
    *,
    max_residual: float = MAX_MEDIAN_RESIDUAL_PT,
    feature_names: Sequence[str] | None = None,
) -> CalibrationResult:
    """Fit and gate. A fit is accepted only if its median residual passes."""
    if len(samples) < 30:
        return CalibrationResult(None, float("inf"), False, "too few samples", len(samples))
    features = [list(f) for f, _ in samples]
    targets = [t for _, t in samples]
    try:
        model = RidgeModel.fit(features, targets, feature_names=feature_names)
    except ValueError as exc:
        return CalibrationResult(None, float("inf"), False, str(exc), len(samples))

    accepted = model.residual_px <= max_residual
    reason = (
        ""
        if accepted
        else f"median error {model.residual_px:.0f} pt exceeds {max_residual:.0f} pt"
    )
    reference = [
        sum(row[i] for row in features) / len(features) for i in range(len(features[0]))
    ]
    return CalibrationResult(
        model=model,
        residual_px=model.residual_px,
        accepted=accepted,
        reason=reason,
        samples=len(samples),
        reference_features=reference,
    )


def collect_samples(
    targets: Sequence[tuple[float, float]],
    read_features: Callable[[], Sequence[float] | None],
    plan: CalibrationPlan,
    *,
    show_dot: Callable[[tuple[float, float], int, int], None] | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> list[tuple[list[float], tuple[float, float]]]:
    """Dwell on each dot in turn, collecting feature vectors.

    ``read_features`` returns the current frame's feature vector, or ``None``
    when no face is visible; those frames are skipped rather than sampled.
    """
    collected: list[tuple[list[float], tuple[float, float]]] = []
    interval = max(1e-3, (plan.dwell_seconds - plan.settle_seconds) / plan.samples_per_dot)
    for index, target in enumerate(targets):
        if show_dot is not None:
            show_dot(target, index, len(targets))
        sleep(plan.settle_seconds)
        for _ in range(plan.samples_per_dot):
            vector = read_features()
            if vector is not None:
                collected.append((list(vector), target))
            sleep(interval)
    return collected


def run_calibration(
    screen: Rect,
    read_features: Callable[[], Sequence[float] | None],
    *,
    calibration_path: Path | str,
    display_key: str = "main",
    plan: CalibrationPlan | None = None,
    show_dot: Callable[[tuple[float, float], int, int], None] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    feature_names: Sequence[str] | None = None,
) -> CalibrationResult:
    """Full calibration: dwell, fit, gate, and save only on acceptance."""
    plan = plan or CalibrationPlan()
    targets = grid_targets(screen, plan.points)
    samples = collect_samples(targets, read_features, plan, show_dot=show_dot, sleep=sleep)
    result = fit_calibration(samples, feature_names=feature_names)
    if result.accepted and result.model is not None:
        save_calibration(
            calibration_path,
            display_key,
            result.model,
            meta={
                "screen": [screen.x, screen.y, screen.w, screen.h],
                "reference_features": result.reference_features,
                "samples": result.samples,
                "fitted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            },
        )
    return result


def show_calibration_ui(  # pragma: no cover - GUI
    screen: Rect,
    read_features: Callable[[], Sequence[float] | None],
    *,
    calibration_path: Path | str,
    display_key: str = "main",
    plan: CalibrationPlan | None = None,
) -> CalibrationResult:
    """Fullscreen Tkinter dot runner.

    Tk owns the main thread; sampling happens on the camera thread that is
    already running inside the gaze engine, so ``sleep`` here pumps the Tk
    event loop instead of blocking it.
    """
    import tkinter as tk

    plan = plan or CalibrationPlan()
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.configure(bg="#111111")
    canvas = tk.Canvas(root, bg="#111111", highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    label = canvas.create_text(
        screen.w / 2,
        40,
        fill="#888888",
        font=("Helvetica", 18),
        text="Look at each dot until it moves. Esc to cancel.",
    )
    dot = canvas.create_oval(0, 0, 0, 0, fill="#ffcc00", outline="")
    cancelled = {"value": False}

    def cancel(_event=None):
        cancelled["value"] = True

    root.bind("<Escape>", cancel)

    def show_dot(target, index, total):
        if cancelled["value"]:
            raise KeyboardInterrupt("calibration cancelled")
        x, y = target
        canvas.coords(dot, x - 14, y - 14, x + 14, y + 14)
        canvas.itemconfigure(label, text=f"Dot {index + 1} of {total}")
        root.update()

    def sleep(seconds: float) -> None:
        deadline = time.time() + seconds
        while time.time() < deadline:
            if cancelled["value"]:
                raise KeyboardInterrupt("calibration cancelled")
            root.update()
            time.sleep(0.005)

    try:
        return run_calibration(
            screen,
            read_features,
            calibration_path=calibration_path,
            display_key=display_key,
            plan=plan,
            show_dot=show_dot,
            sleep=sleep,
        )
    except KeyboardInterrupt:
        return CalibrationResult(None, float("inf"), False, "cancelled")
    finally:
        root.destroy()
