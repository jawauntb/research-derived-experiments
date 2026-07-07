"""Per-subject calibrated baseline — the LSO upper bound.

Riemannian tangent-space projection of covariance matrices + logistic
classifier. This is the workhorse from the MOABB benchmarks; it is not the
target, it is the ceiling we compare the cross-subject target against.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class PerSubjectRiemannDecoder:
    """Fit + evaluate per subject; return the mean within-subject balanced acc."""

    n_folds: int = 5
    random_state: int = 0

    def fit_predict_within_subject(self, X: np.ndarray, y: np.ndarray) -> dict[str, float]:
        """K-fold within a single subject; returns balanced accuracy stats."""
        from pyriemann.estimation import Covariances
        from pyriemann.tangentspace import TangentSpace
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import balanced_accuracy_score
        from sklearn.model_selection import StratifiedKFold
        from sklearn.pipeline import make_pipeline

        if len(np.unique(y)) < 2 or len(y) < self.n_folds * 2:
            return {"balanced_accuracy": float("nan"), "n": int(len(y))}

        skf = StratifiedKFold(n_splits=self.n_folds, shuffle=True,
                              random_state=self.random_state)
        baccs: list[float] = []
        for train_idx, test_idx in skf.split(X, y):
            clf = make_pipeline(
                Covariances(estimator="oas"),
                TangentSpace(),
                LogisticRegression(max_iter=1000),
            )
            clf.fit(X[train_idx], y[train_idx])
            preds = clf.predict(X[test_idx])
            baccs.append(balanced_accuracy_score(y[test_idx], preds))
        return {
            "balanced_accuracy": float(np.mean(baccs)),
            "balanced_accuracy_std": float(np.std(baccs)),
            "n": int(len(y)),
        }
