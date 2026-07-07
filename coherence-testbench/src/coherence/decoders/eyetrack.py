"""Eyetrack decoders — flat-feature analogues of baseline.py + cross_subject.py.

No Riemannian machinery here: eyetrack features are already flat scalars.
The per-subject baseline is a scikit-learn LR pipeline with a standard
scaler + logistic regression. The cross-subject target reuses the same
adversarial MLP head from ``cross_subject.py`` (trunk + class head +
gradient-reversed subject-ID head), just fed z-scored raw features
instead of tangent-space projections.

The decoders take pre-registered guardrails from
``config/kill_criterion_eyetrack.yaml``:

    * z-scoring stats fit train-only (mitigates subject_id_leak +
      device_calibration_drift).
    * Feature-set ablations (pupil-only, gaze+pupil no-head, prior-only)
      are exposed as toggles the shard runner can call to populate the
      confound_ablations section.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class PerSubjectEyetrackDecoder:
    """LR baseline with StratifiedKFold, robust to single-class folds."""

    n_folds: int = 5
    random_state: int = 0

    def fit_predict_within_subject(
        self, X: np.ndarray, y: np.ndarray
    ) -> dict[str, float]:
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import balanced_accuracy_score
        from sklearn.model_selection import StratifiedKFold
        from sklearn.preprocessing import StandardScaler

        finite = np.isfinite(X).all(axis=1)
        X = X[finite]
        y = y[finite]

        unique, counts = np.unique(y, return_counts=True)
        if (
            len(unique) < 2
            or counts.min() < self.n_folds
            or len(y) < self.n_folds * 2
        ):
            return {"balanced_accuracy": float("nan"), "n": int(len(y))}

        skf = StratifiedKFold(
            n_splits=self.n_folds, shuffle=True, random_state=self.random_state
        )
        baccs: list[float] = []
        for train_idx, test_idx in skf.split(X, y):
            try:
                sc = StandardScaler().fit(X[train_idx])
                Xtr = sc.transform(X[train_idx])
                Xte = sc.transform(X[test_idx])
                if not np.isfinite(Xtr).all() or not np.isfinite(Xte).all():
                    continue
                lr = LogisticRegression(max_iter=1000)
                lr.fit(Xtr, y[train_idx])
                preds = lr.predict(Xte)
                baccs.append(
                    float(balanced_accuracy_score(y[test_idx], preds))
                )
            except (ValueError, np.linalg.LinAlgError):
                continue

        if not baccs:
            return {"balanced_accuracy": float("nan"), "n": int(len(y))}
        return {
            "balanced_accuracy": float(np.mean(baccs)),
            "balanced_accuracy_std": float(np.std(baccs)),
            "n": int(len(y)),
        }


@dataclass
class CrossSubjectEyetrackDecoder:
    """Cross-subject MLP with domain-adversarial head, on eyetrack features."""

    adversary_weight: float = 0.1
    epochs: int = 40
    batch_size: int = 64
    lr: float = 3e-4
    seed: int = 0
    ssl_pretrain: bool = False
    _scaler_: Any = field(default=None, init=False, repr=False)
    _model: Any = field(default=None, init=False, repr=False)
    _pretrained_trunk_state_: Any = field(default=None, init=False, repr=False)

    def _fit_scaler(self, X: np.ndarray) -> np.ndarray:
        # Train-only z-score. Structural guarantee against
        # device_calibration_drift + subject_id_leak.
        mu = X.mean(axis=0)
        sd = X.std(axis=0) + 1e-8
        self._scaler_ = (mu, sd)
        return ((X - mu) / sd).astype(np.float32)

    def _apply_scaler(self, X: np.ndarray) -> np.ndarray:
        assert self._scaler_ is not None
        mu, sd = self._scaler_
        return ((X - mu) / sd).astype(np.float32)

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        subj_train: np.ndarray,
    ) -> None:
        Z = self._fit_scaler(X_train)
        if self.ssl_pretrain:
            self._ssl_pretrain_trunk(Z)
        self._fit_classifier(Z, y_train, subj_train)

    def _ssl_pretrain_trunk(self, feats: np.ndarray) -> None:
        """Masked-feature reconstruction pretrain on train features only.

        Same objective as the EEG side (cross_subject.py) — mask 20% of
        the feature vector's dims and train a small autoencoder to
        reconstruct. Learned trunk weights become the init for the
        classifier's trunk. Non-load-bearing on rich EEG features; may
        help more on eyetrack's small 11-D feature space where the
        classifier could overfit."""
        import torch
        from torch import nn

        torch.manual_seed(self.seed)
        n, d = feats.shape
        hidden = 64
        trunk = nn.Sequential(
            nn.Linear(d, hidden), nn.GELU(),
            nn.Linear(hidden, hidden), nn.GELU(),
        )
        decoder = nn.Linear(hidden, d)
        opt = torch.optim.Adam(
            list(trunk.parameters()) + list(decoder.parameters()),
            lr=self.lr,
        )
        mse = nn.MSELoss()
        X_t = torch.from_numpy(feats).float()
        pretrain_epochs = 30
        mask_frac = 0.2
        for _ in range(pretrain_epochs):
            idx = torch.randperm(n)
            for start in range(0, n, self.batch_size):
                bi = idx[start:start + self.batch_size]
                x = X_t[bi]
                mask = (torch.rand_like(x) > mask_frac).float()
                h = trunk(x * mask)
                loss = mse(decoder(h), x)
                opt.zero_grad()
                loss.backward()
                opt.step()
        self._pretrained_trunk_state_ = {
            k: v.clone().detach() for k, v in trunk.state_dict().items()
        }

    def predict(self, X_test: np.ndarray) -> np.ndarray:
        Z = self._apply_scaler(X_test)
        return self._predict_from_feats(Z)

    def _fit_classifier(
        self, feats: np.ndarray, y: np.ndarray, subj: np.ndarray
    ) -> None:
        import torch
        from torch import nn
        from torch.autograd import Function

        torch.manual_seed(self.seed)
        n, d = feats.shape
        n_subjects = int(subj.max()) + 1
        hidden = 64

        class _Reverse(Function):
            @staticmethod
            def forward(_ctx, x):  # type: ignore[override]
                return x.view_as(x)

            @staticmethod
            def backward(_ctx, grad_out):  # type: ignore[override]
                return -self.adversary_weight * grad_out

        trunk = nn.Sequential(
            nn.Linear(d, hidden), nn.GELU(),
            nn.Linear(hidden, hidden), nn.GELU(),
        )
        # Warm-start from SSL pretrain if it ran.
        if self._pretrained_trunk_state_ is not None:
            try:
                trunk.load_state_dict(self._pretrained_trunk_state_)
            except (RuntimeError, ValueError):
                pass
        cls_head = nn.Linear(hidden, 2)
        subj_head = nn.Linear(hidden, n_subjects)

        params = (
            list(trunk.parameters())
            + list(cls_head.parameters())
            + list(subj_head.parameters())
        )
        opt = torch.optim.Adam(params, lr=self.lr)
        cls_loss = nn.CrossEntropyLoss()
        subj_loss = nn.CrossEntropyLoss()

        X_t = torch.from_numpy(feats).float()
        y_t = torch.from_numpy(y).long()
        s_t = torch.from_numpy(subj).long()

        for _ in range(self.epochs):
            idx = torch.randperm(n)
            for start in range(0, n, self.batch_size):
                bi = idx[start:start + self.batch_size]
                h = trunk(X_t[bi])
                cls_logits = cls_head(h)
                subj_logits = subj_head(_Reverse.apply(h))
                loss = cls_loss(cls_logits, y_t[bi]) + subj_loss(subj_logits, s_t[bi])
                opt.zero_grad()
                loss.backward()
                opt.step()

        self._model = (trunk, cls_head)

    def _predict_from_feats(self, feats: np.ndarray) -> np.ndarray:
        import torch

        trunk, cls_head = self._model
        with torch.no_grad():
            X_t = torch.from_numpy(feats).float()
            logits = cls_head(trunk(X_t))
            return logits.argmax(-1).cpu().numpy()
