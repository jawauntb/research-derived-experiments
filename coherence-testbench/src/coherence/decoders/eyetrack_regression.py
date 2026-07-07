"""Cross-subject regression head over aggregated eyetrack features.

For quiz-score regression: each recording's per-epoch features are
aggregated to a single fixed-length vector (mean + std across epochs),
then a train-only-standardized MLP predicts the quiz score. LSO metric
is Spearman rank correlation on held-out subjects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np


def aggregate_epochs(X: np.ndarray) -> np.ndarray:
    """(n_epochs, n_features) -> (2*n_features,) mean concat std vector."""
    if len(X) == 0:
        return np.zeros((0,), dtype=np.float32)
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    return np.concatenate([mu, sd]).astype(np.float32)


@dataclass
class CrossSubjectEyetrackRegressor:
    ssl_pretrain: bool = False
    epochs: int = 60
    batch_size: int = 64
    lr: float = 3e-4
    seed: int = 0
    _scaler_: Any = field(default=None, init=False, repr=False)
    _model: Any = field(default=None, init=False, repr=False)

    def _fit_scaler(self, X: np.ndarray) -> np.ndarray:
        mu = X.mean(axis=0)
        sd = X.std(axis=0) + 1e-8
        self._scaler_ = (mu, sd)
        return ((X - mu) / sd).astype(np.float32)

    def _apply_scaler(self, X: np.ndarray) -> np.ndarray:
        assert self._scaler_ is not None
        mu, sd = self._scaler_
        return ((X - mu) / sd).astype(np.float32)

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        import torch
        from torch import nn

        torch.manual_seed(self.seed)
        Z = self._fit_scaler(X_train)
        n, d = Z.shape
        hidden = 64

        trunk = nn.Sequential(
            nn.Linear(d, hidden), nn.GELU(),
            nn.Linear(hidden, hidden), nn.GELU(),
        )
        head = nn.Linear(hidden, 1)

        # Optional SSL pretrain: masked feature reconstruction.
        if self.ssl_pretrain:
            decoder = nn.Linear(hidden, d)
            opt = torch.optim.Adam(
                list(trunk.parameters()) + list(decoder.parameters()),
                lr=self.lr,
            )
            X_t = torch.from_numpy(Z).float()
            for _ in range(20):
                idx = torch.randperm(n)
                for start in range(0, n, self.batch_size):
                    bi = idx[start:start + self.batch_size]
                    x = X_t[bi]
                    mask = (torch.rand_like(x) > 0.2).float()
                    h = trunk(x * mask)
                    loss = nn.functional.mse_loss(decoder(h), x)
                    opt.zero_grad()
                    loss.backward()
                    opt.step()

        params = list(trunk.parameters()) + list(head.parameters())
        opt = torch.optim.Adam(params, lr=self.lr)
        mse = nn.MSELoss()
        X_t = torch.from_numpy(Z).float()
        y_t = torch.from_numpy(y_train.astype(np.float32)).float().unsqueeze(1)
        for _ in range(self.epochs):
            idx = torch.randperm(n)
            for start in range(0, n, self.batch_size):
                bi = idx[start:start + self.batch_size]
                pred = head(trunk(X_t[bi]))
                loss = mse(pred, y_t[bi])
                opt.zero_grad()
                loss.backward()
                opt.step()
        self._model = (trunk, head)

    def predict(self, X: np.ndarray) -> np.ndarray:
        import torch

        trunk, head = self._model
        Z = self._apply_scaler(X)
        with torch.no_grad():
            X_t = torch.from_numpy(Z).float()
            return head(trunk(X_t)).squeeze(-1).cpu().numpy()


def spearman_r(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Spearman rank correlation. Returns 0.0 on degenerate inputs."""
    if len(y_true) < 2:
        return 0.0
    yt = np.asarray(y_true, dtype=np.float64)
    yp = np.asarray(y_pred, dtype=np.float64)
    if np.all(yt == yt[0]) or np.all(yp == yp[0]):
        return 0.0
    # Compute Spearman as Pearson on ranks; avoids scipy dependency.
    rt = np.argsort(np.argsort(yt))
    rp = np.argsort(np.argsort(yp))
    return float(np.corrcoef(rt, rp)[0, 1])


def lso_regression(
    by_subject: dict[str, tuple[np.ndarray, np.ndarray]],
    factory: Callable[[], "CrossSubjectEyetrackRegressor"],
    n_seeds: int = 5,
    train_subject_sweep: tuple[int, ...] = (8, 16, 24, 32),
    held_out_fraction: float = 0.2,
) -> list[dict[str, Any]]:
    """Leave-subjects-out for a regression target.

    ``by_subject`` maps subject_id -> (X_records, y_records) where
    X_records is (n_records, n_features) and y_records is (n_records,).
    Returns per-fold summary dicts with Spearman ρ.
    """
    subjects = sorted(by_subject.keys())
    results: list[dict[str, Any]] = []
    for seed in range(n_seeds):
        rng = np.random.default_rng(seed)
        shuffled = list(subjects)
        rng.shuffle(shuffled)
        n_test = max(1, int(len(shuffled) * held_out_fraction))
        test_subjects = tuple(shuffled[:n_test])
        train_pool = shuffled[n_test:]
        for n_train in train_subject_sweep:
            if n_train > len(train_pool):
                continue
            train_subjects = train_pool[:n_train]
            X_tr = np.concatenate([by_subject[s][0] for s in train_subjects], axis=0)
            y_tr = np.concatenate([by_subject[s][1] for s in train_subjects], axis=0)
            X_te = np.concatenate([by_subject[s][0] for s in test_subjects], axis=0)
            y_te = np.concatenate([by_subject[s][1] for s in test_subjects], axis=0)
            if len(y_tr) < 4 or len(y_te) < 4:
                continue
            dec = factory()
            dec.fit(X_tr, y_tr)
            preds = dec.predict(X_te)
            rho = spearman_r(y_te, preds)
            results.append({
                "seed": int(seed),
                "n_train_subjects": int(n_train),
                "held_out_subjects": list(test_subjects),
                "spearman_r": float(rho),
                "n_test_records": int(len(y_te)),
            })
    return results
