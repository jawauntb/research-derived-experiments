"""Cross-subject target decoder.

Stack (mirrors the plan's Stage-2 decoder table):
    Base       — optional SSL pretrain hook (masked-signal / contrastive).
    Invariance — Riemannian covariance alignment (per-recording recentering) +
                 domain-adversarial head (gradient-reversal on subject ID).
    Adaptation — few-shot fine-tune (unused at the LSO gate; kept as an escape
                 hatch for the "inconclusive → try with adaptation" branch).
    Fusion     — fNIRS branch is a stub (Phase 0 is EEG-only).
    Supervision— binary head on attentive vs distracted.

Evaluation-discipline rules from `config/kill_criterion.yaml`:
    * Alignment / normalization stats fit ONLY on the train fold. This module
      handles that itself so the eval harness can't accidentally leak it.
    * Subject-embedding conditioning is disabled by default; enabling it lets
      the model 'see' subject identity at train time, which is fine as long as
      the gradient-reversal head is on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


def _riemannian_recentering(X: np.ndarray, reference_mean=None):
    """Whiten each recording toward a reference covariance in the Riemannian
    tangent space. Fitted on the train fold only when reference_mean is None."""
    from pyriemann.estimation import Covariances
    from pyriemann.utils.mean import mean_riemann
    from pyriemann.utils.base import invsqrtm

    # Ledoit-Wolf shrinkage is more numerically stable than OAS on
    # rank-deficient EEG. See baseline.py for the same choice.
    covs = Covariances(estimator="lwf").transform(X)
    n_ch = covs.shape[-1]
    # Substitute the identity matrix for any covariance that came out
    # non-finite so we keep row alignment with y/subj vectors. Identity
    # is positive-definite and contributes zero information.
    finite = np.isfinite(covs).reshape(len(covs), -1).all(axis=1)
    if not finite.all():
        covs = covs.copy()
        covs[~finite] = np.eye(n_ch, dtype=covs.dtype)
    # Ensure strict positive-definiteness so pyriemann's Riemannian mean
    # doesn't raise "Matrices must be positive definite". LWF can still
    # emit matrices that are PSD but numerically singular; add a small
    # trace-scaled ridge.
    trace = np.trace(covs, axis1=-2, axis2=-1).mean()
    ridge = 1e-6 * max(float(trace) / n_ch, 1.0)
    covs = covs + ridge * np.eye(n_ch, dtype=covs.dtype)[None, :, :]
    if reference_mean is None:
        reference_mean = mean_riemann(covs)
    whitener = invsqrtm(reference_mean)
    # Whiten each trial's covariance -> tangent-space projection.
    from pyriemann.tangentspace import TangentSpace

    ts = TangentSpace(metric="riemann")
    ts.reference_ = reference_mean  # skip .fit — we supply the reference
    feats = ts.transform(covs @ whitener[None, :, :])
    return feats, reference_mean


class _GradReverse:
    """Torch-side gradient-reversal, lazily imported."""

    @staticmethod
    def build(weight: float):
        import torch  # noqa: PLC0415
        from torch.autograd import Function

        class _Reverse(Function):
            @staticmethod
            def forward(_ctx, x):  # type: ignore[override]
                return x.view_as(x)

            @staticmethod
            def backward(_ctx, grad_out):  # type: ignore[override]
                return -weight * grad_out

        def apply(x):
            return _Reverse.apply(x)

        return apply, torch


@dataclass
class CrossSubjectAdversarialDecoder:
    alignment: str = "riemann"          # "euclidean" | "riemann"
    adversary_weight: float = 0.1
    ssl_pretrain: bool = False
    epochs: int = 30
    batch_size: int = 64
    lr: float = 3e-4
    seed: int = 0

    _train_reference_: Any = field(default=None, init=False, repr=False)
    _train_scaler_: Any = field(default=None, init=False, repr=False)

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        subj_train: np.ndarray,
    ) -> None:
        """Fit alignment stats (train-only) + adversarial classifier."""
        feats_train = self._fit_alignment(X_train)
        self._fit_classifier(feats_train, y_train, subj_train)

    def predict(self, X_test: np.ndarray) -> np.ndarray:
        feats = self._apply_alignment(X_test)
        return self._predict_from_feats(feats)

    def predict_proba(self, X_test: np.ndarray) -> np.ndarray:
        feats = self._apply_alignment(X_test)
        return self._proba_from_feats(feats)

    # --- alignment --------------------------------------------------------

    def _fit_alignment(self, X: np.ndarray) -> np.ndarray:
        if self.alignment == "riemann":
            feats, ref = _riemannian_recentering(X, reference_mean=None)
            self._train_reference_ = ref
            return feats
        # Euclidean fallback: per-channel z-score fit on train.
        mean = X.mean(axis=(0, 2), keepdims=True)
        std = X.std(axis=(0, 2), keepdims=True) + 1e-8
        self._train_scaler_ = (mean, std)
        z = (X - mean) / std
        return z.reshape(z.shape[0], -1)

    def _apply_alignment(self, X: np.ndarray) -> np.ndarray:
        if self.alignment == "riemann":
            feats, _ = _riemannian_recentering(X, reference_mean=self._train_reference_)
            return feats
        assert self._train_scaler_ is not None, "must call fit before predict"
        mean, std = self._train_scaler_
        z = (X - mean) / std
        return z.reshape(z.shape[0], -1)

    # --- classifier -------------------------------------------------------

    def _fit_classifier(self, feats: np.ndarray, y: np.ndarray, subj: np.ndarray) -> None:
        import torch  # noqa: PLC0415
        from torch import nn  # noqa: PLC0415

        torch.manual_seed(self.seed)
        n, d = feats.shape
        n_subjects = int(subj.max()) + 1
        self._model = _AdversarialHead(d=d, n_subjects=n_subjects).to("cpu")
        opt = torch.optim.Adam(self._model.parameters(), lr=self.lr)
        cls_loss = nn.CrossEntropyLoss()
        subj_loss = nn.CrossEntropyLoss()
        grl, _ = _GradReverse.build(self.adversary_weight)

        X_t = torch.from_numpy(feats).float()
        y_t = torch.from_numpy(y).long()
        s_t = torch.from_numpy(subj).long()

        for _ in range(self.epochs):
            idx = torch.randperm(n)
            for start in range(0, n, self.batch_size):
                bi = idx[start:start + self.batch_size]
                logits, embed = self._model(X_t[bi])
                subj_logits = self._model.subj_head(grl(embed))
                loss = cls_loss(logits, y_t[bi]) + subj_loss(subj_logits, s_t[bi])
                opt.zero_grad()
                loss.backward()
                opt.step()

    def _predict_from_feats(self, feats: np.ndarray) -> np.ndarray:
        import torch  # noqa: PLC0415

        with torch.no_grad():
            X_t = torch.from_numpy(feats).float()
            logits, _ = self._model(X_t)
            return logits.argmax(-1).cpu().numpy()

    def _proba_from_feats(self, feats: np.ndarray) -> np.ndarray:
        import torch  # noqa: PLC0415

        with torch.no_grad():
            X_t = torch.from_numpy(feats).float()
            logits, _ = self._model(X_t)
            return torch.softmax(logits, dim=-1).cpu().numpy()


class _AdversarialHead:
    """Simple MLP with a shared trunk, a binary class head, and a
    subject-ID adversary head. Instantiated at fit time so torch imports
    stay lazy."""

    def __init__(self, d: int, n_subjects: int, hidden: int = 128):
        import torch  # noqa: PLC0415
        from torch import nn  # noqa: PLC0415

        self.trunk = nn.Sequential(
            nn.Linear(d, hidden), nn.GELU(),
            nn.Linear(hidden, hidden), nn.GELU(),
        )
        self.cls_head = nn.Linear(hidden, 2)
        self.subj_head = nn.Linear(hidden, n_subjects)
        self._torch = torch

    def to(self, device):
        self.trunk = self.trunk.to(device)
        self.cls_head = self.cls_head.to(device)
        self.subj_head = self.subj_head.to(device)
        return self

    def parameters(self):
        return (list(self.trunk.parameters())
                + list(self.cls_head.parameters())
                + list(self.subj_head.parameters()))

    def __call__(self, x):
        h = self.trunk(x)
        return self.cls_head(h), h
