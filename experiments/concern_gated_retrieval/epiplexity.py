"""Closed-form reservoir/ridge estimator of epiplexity.

This implements equations (7)-(9) of Zhang and Levin (2026),
"Intelligence from Learnable Novelty", for a fixed random feature map.
The estimator is used only as a bounded-observer diagnostic in this package.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class ReservoirEpiplexity:
    """A frozen random reservoir with a closed-form ridge readout."""

    input_dimension: int
    width: int = 16
    ridge: float = 1.0
    eta: float = 1.0
    target_scale: float = 1.0
    seed: int = 20260723

    def __post_init__(self) -> None:
        if self.input_dimension < 1 or self.width < 1:
            raise ValueError("input dimension and width must be positive")
        for name, value in (
            ("ridge", self.ridge),
            ("eta", self.eta),
            ("target_scale", self.target_scale),
        ):
            if not isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")

    def _reservoir(self, inputs: FloatArray) -> FloatArray:
        rng = np.random.default_rng(self.seed)
        projection = rng.normal(
            0.0,
            1 / sqrt(self.input_dimension),
            size=(self.input_dimension, self.width),
        )
        bias = rng.normal(0.0, 0.35, size=(self.width,))
        return np.tanh(inputs @ projection + bias)

    def readout(self, inputs: FloatArray, targets: FloatArray) -> FloatArray:
        """Return the stable least-squares form of the ridge readout."""

        inputs = np.asarray(inputs, dtype=np.float64)
        targets = np.asarray(targets, dtype=np.float64)
        if inputs.ndim != 2 or inputs.shape[1] != self.input_dimension:
            raise ValueError("inputs must be a 2D array with the configured width")
        if targets.ndim == 1:
            targets = targets[:, None]
        if targets.ndim != 2 or targets.shape[0] != inputs.shape[0]:
            raise ValueError("targets must be 1D/2D and row-aligned with inputs")
        if not np.isfinite(inputs).all() or not np.isfinite(targets).all():
            raise ValueError("inputs and targets must be finite")

        features = self._reservoir(inputs)
        centered_features = features - features.mean(axis=0, keepdims=True)
        feature_scale = centered_features.std(axis=0, keepdims=True)
        feature_scale = np.where(feature_scale > 1e-12, feature_scale, 1.0)
        standardized = centered_features / (feature_scale * sqrt(self.width))

        standardized_targets = (
            targets - targets.mean(axis=0, keepdims=True)
        ) / self.target_scale
        regularizer = sqrt(self.ridge) * np.eye(self.width, dtype=np.float64)
        augmented_features = np.vstack((standardized, regularizer))
        augmented_targets = np.vstack(
            (
                standardized_targets,
                np.zeros((self.width, standardized_targets.shape[1])),
            )
        )
        readout, *_ = np.linalg.lstsq(
            augmented_features,
            augmented_targets,
            rcond=None,
        )
        return readout

    def score(self, inputs: FloatArray, targets: FloatArray) -> float:
        """Return ``0.5 log2 det(I + eta W W^T)`` in bits."""

        readout = self.readout(inputs, targets)
        priced = np.eye(self.width, dtype=np.float64) + self.eta * (
            readout @ readout.T
        )
        sign, log_determinant = np.linalg.slogdet(priced)
        if sign <= 0:
            raise RuntimeError("epiplexity price matrix is not positive definite")
        return float(0.5 * log_determinant / np.log(2.0))
