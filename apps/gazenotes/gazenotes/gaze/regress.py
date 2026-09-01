"""A small dependency-free ridge regression, used to map eye features → screen.

Degree-2 polynomial features over a 10-dimensional feature vector give 66
terms; the normal equations are a 66x66 symmetric solve done once at
calibration time, so pure Python is comfortably fast and keeps the calibration
model loadable (and testable) without NumPy.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "poly2",
    "solve_spd",
    "RidgeModel",
    "save_calibration",
    "load_calibration",
    "load_calibration_entry",
]


def poly2(features: Sequence[float]) -> list[float]:
    """``[1, x_i, x_i*x_j]`` — bias, linear terms, then all quadratic pairs."""
    xs = list(map(float, features))
    out = [1.0]
    out.extend(xs)
    for i in range(len(xs)):
        for j in range(i, len(xs)):
            out.append(xs[i] * xs[j])
    return out


def solve_spd(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    """Solve ``A x = b`` for symmetric positive-definite ``A`` by Gaussian
    elimination with partial pivoting.

    Ridge makes ``A`` positive definite, but pivoting is kept anyway: a
    degenerate calibration (user never moved their eyes) should raise rather
    than silently return garbage.
    """
    n = len(rhs)
    aug = [list(map(float, row)) + [float(rhs[i])] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-12:
            raise ValueError("singular normal equations; calibration data is degenerate")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        pivot_row = aug[col]
        inv = 1.0 / pivot_row[col]
        for row_index in range(col + 1, n):
            row = aug[row_index]
            factor = row[col] * inv
            if factor == 0.0:
                continue
            for k in range(col, n + 1):
                row[k] -= factor * pivot_row[k]
    solution = [0.0] * n
    for col in range(n - 1, -1, -1):
        row = aug[col]
        total = row[n] - sum(row[k] * solution[k] for k in range(col + 1, n))
        solution[col] = total / row[col]
    return solution


@dataclass
class RidgeModel:
    """Two independent ridge fits (one per screen axis) over ``poly2`` features."""

    coef_x: list[float]
    coef_y: list[float]
    feature_names: list[str]
    residual_px: float = 0.0
    """Median Euclidean residual in logical points over the calibration set."""

    @classmethod
    def fit(
        cls,
        features: Sequence[Sequence[float]],
        targets: Sequence[tuple[float, float]],
        *,
        alpha: float = 1e-3,
        feature_names: Sequence[str] | None = None,
    ) -> RidgeModel:
        """Fit ``targets`` (screen x, y) from ``features``.

        ``alpha`` regularises every term except the bias, so a constant offset
        is never shrunk toward zero.
        """
        if len(features) != len(targets):
            raise ValueError("features and targets must be the same length")
        if not features:
            raise ValueError("no calibration samples")
        design = [poly2(row) for row in features]
        width = len(design[0])
        if len(design) < width:
            # Under-determined: ridge still solves it, but warn the caller by
            # requiring a stronger prior rather than pretending it is a fit.
            alpha = max(alpha, 1e-2)

        gram = [[0.0] * width for _ in range(width)]
        bx = [0.0] * width
        by = [0.0] * width
        for row, (tx, ty) in zip(design, targets, strict=True):
            for i in range(width):
                ri = row[i]
                if ri == 0.0:
                    continue
                gram_i = gram[i]
                for j in range(i, width):
                    gram_i[j] += ri * row[j]
                bx[i] += ri * tx
                by[i] += ri * ty
        for i in range(width):
            for j in range(i + 1, width):
                gram[j][i] = gram[i][j]
            if i > 0:
                gram[i][i] += alpha * len(design)

        coef_x = solve_spd([row[:] for row in gram], bx)
        coef_y = solve_spd([row[:] for row in gram], by)
        names = list(feature_names or [])
        model = cls(coef_x=coef_x, coef_y=coef_y, feature_names=names)
        model.residual_px = model.median_residual(features, targets)
        return model

    def predict(self, features: Sequence[float]) -> tuple[float, float]:
        row = poly2(features)
        px = sum(c * v for c, v in zip(self.coef_x, row, strict=True))
        py = sum(c * v for c, v in zip(self.coef_y, row, strict=True))
        return px, py

    def median_residual(
        self,
        features: Sequence[Sequence[float]],
        targets: Sequence[tuple[float, float]],
    ) -> float:
        errors = []
        for row, (tx, ty) in zip(features, targets, strict=True):
            px, py = self.predict(row)
            errors.append(((px - tx) ** 2 + (py - ty) ** 2) ** 0.5)
        errors.sort()
        if not errors:
            return float("inf")
        mid = len(errors) // 2
        if len(errors) % 2:
            return errors[mid]
        return 0.5 * (errors[mid - 1] + errors[mid])

    # -- persistence ----------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "coef_x": self.coef_x,
            "coef_y": self.coef_y,
            "feature_names": self.feature_names,
            "residual_px": self.residual_px,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RidgeModel:
        return cls(
            coef_x=list(data["coef_x"]),
            coef_y=list(data["coef_y"]),
            feature_names=list(data.get("feature_names", [])),
            residual_px=float(data.get("residual_px", 0.0)),
        )


def save_calibration(path: Path | str, key: str, model: RidgeModel, meta: dict | None = None) -> Path:
    """Merge one display's model into ``calibration.json`` without dropping others."""
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    store: dict = {}
    if path.exists():
        try:
            store = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            store = {}
    entry = model.to_dict()
    entry.update(meta or {})
    store[key] = entry
    path.write_text(json.dumps(store, indent=2) + "\n", encoding="utf-8")
    return path


def load_calibration_entry(path: Path | str, key: str) -> dict | None:
    """The stored record for one display: model coefficients plus its metadata."""
    path = Path(path).expanduser()
    if not path.is_file():
        return None
    try:
        store = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    data = store.get(key)
    if not isinstance(data, dict) or "coef_x" not in data:
        return None
    return data


def load_calibration(path: Path | str, key: str) -> RidgeModel | None:
    """Load one display's model, or ``None`` if this display is uncalibrated."""
    data = load_calibration_entry(path, key)
    return RidgeModel.from_dict(data) if data is not None else None
