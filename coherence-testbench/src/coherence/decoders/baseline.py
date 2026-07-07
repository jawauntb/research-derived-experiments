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
        """K-fold within a single subject; returns balanced accuracy stats.

        Defensively skips folds where the Riemannian tangent-space features
        contain NaN/Inf (some EEG epochs slip past peak-to-peak rejection
        but still yield ill-conditioned covariances) and folds where any
        stage raises. A subject whose folds all fail returns NaN.
        """
        from pyriemann.estimation import Covariances
        from pyriemann.tangentspace import TangentSpace
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import balanced_accuracy_score
        from sklearn.model_selection import StratifiedKFold
        from sklearn.pipeline import make_pipeline

        # Also drop epochs whose raw values contain NaN/Inf before we even
        # try to compute covariance.
        finite_mask = np.isfinite(X).reshape(len(X), -1).all(axis=1)
        X = X[finite_mask]
        y = y[finite_mask]

        unique, counts = np.unique(y, return_counts=True)
        if (
            len(unique) < 2
            or counts.min() < self.n_folds
            or len(y) < self.n_folds * 2
        ):
            return {"balanced_accuracy": float("nan"), "n": int(len(y))}

        skf = StratifiedKFold(n_splits=self.n_folds, shuffle=True,
                              random_state=self.random_state)
        baccs: list[float] = []
        for train_idx, test_idx in skf.split(X, y):
            try:
                # Lwf (Ledoit-Wolf) is more numerically stable than OAS for
                # small samples with rank-deficient EEG.
                clf = make_pipeline(
                    Covariances(estimator="lwf"),
                    TangentSpace(),
                    LogisticRegression(max_iter=1000),
                )
                # Sanity-check post-transform features BEFORE fit — pyriemann
                # can silently emit NaN on bad covariances.
                cov = Covariances(estimator="lwf").fit_transform(X[train_idx])
                ts_feats = TangentSpace().fit_transform(cov)
                if not np.isfinite(ts_feats).all():
                    continue
                clf.fit(X[train_idx], y[train_idx])
                preds = clf.predict(X[test_idx])
                baccs.append(balanced_accuracy_score(y[test_idx], preds))
            except (ValueError, np.linalg.LinAlgError):
                continue

        if not baccs:
            return {"balanced_accuracy": float("nan"), "n": int(len(y))}
        return {
            "balanced_accuracy": float(np.mean(baccs)),
            "balanced_accuracy_std": float(np.std(baccs)),
            "n": int(len(y)),
        }
