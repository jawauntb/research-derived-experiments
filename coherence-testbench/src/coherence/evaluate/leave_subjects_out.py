"""Leave-subjects-out cross-validation for the cross-subject gate.

Metrics reported (both required by the kill-criterion):

    * balanced accuracy (per fold + pooled)
    * bits/sec of mutual information at the epoch rate

The train-subject sweep produces the generalization curve — perf as a function
of the number of subjects the target decoder trained on. That curve is the
single most useful figure for arguing 'we haven't saturated; more data will
push it up' vs 'we've plateaued below the threshold; it's dead.'
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from sklearn.metrics import balanced_accuracy_score


@dataclass(frozen=True)
class LSOFoldResult:
    seed: int
    n_train_subjects: int
    held_out_subjects: tuple[str, ...]
    balanced_accuracy: float
    bits_per_second: float
    n_test_epochs: int


@dataclass
class LeaveSubjectsOut:
    epoch_seconds: float
    n_lso_seeds: int = 5
    held_out_fraction: float = 0.2
    train_subject_sweep: tuple[int, ...] = (8, 16, 32, 64, 128)
    rng: np.random.Generator = field(default_factory=lambda: np.random.default_rng(0))

    def run(
        self,
        by_subject: dict[str, tuple[np.ndarray, np.ndarray]],
        decoder_factory: Callable[[], object],
    ) -> list[LSOFoldResult]:
        """Fit ``decoder_factory()`` at each (seed, n_train) point.

        ``by_subject`` maps subject_id -> (X, y) arrays. ``decoder_factory``
        returns a fresh cross-subject decoder each call — this is how the eval
        enforces train-only fitting.
        """
        subjects = sorted(by_subject.keys())
        results: list[LSOFoldResult] = []

        for seed in range(self.n_lso_seeds):
            rng = np.random.default_rng(seed)
            shuffled = list(subjects)
            rng.shuffle(shuffled)
            n_test = max(1, int(len(shuffled) * self.held_out_fraction))
            test_subjects = tuple(shuffled[:n_test])
            train_pool = shuffled[n_test:]

            for n_train in self.train_subject_sweep:
                if n_train > len(train_pool):
                    continue
                train_subjects = train_pool[:n_train]
                X_tr, y_tr, s_tr = _concat(by_subject, train_subjects, subject_index=True)
                X_te, y_te, _ = _concat(by_subject, test_subjects, subject_index=False)

                if len(y_te) == 0 or len(np.unique(y_tr)) < 2:
                    continue

                dec = decoder_factory()
                dec.fit(X_tr, y_tr, s_tr)  # type: ignore[attr-defined]
                pred = dec.predict(X_te)   # type: ignore[attr-defined]

                bacc = balanced_accuracy_score(y_te, pred)
                bps = bits_per_second(
                    y_te, pred, epoch_seconds=self.epoch_seconds
                )
                results.append(
                    LSOFoldResult(
                        seed=seed,
                        n_train_subjects=int(n_train),
                        held_out_subjects=test_subjects,
                        balanced_accuracy=float(bacc),
                        bits_per_second=float(bps),
                        n_test_epochs=int(len(y_te)),
                    )
                )
        return results


def _concat(
    by_subject: dict[str, tuple[np.ndarray, np.ndarray]],
    ids: list[str] | tuple[str, ...],
    subject_index: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    Xs, ys, subs = [], [], []
    for i, sub in enumerate(ids):
        X, y = by_subject[sub]
        Xs.append(X)
        ys.append(y)
        if subject_index:
            subs.append(np.full(len(y), i, dtype=np.int64))
    if not Xs:
        return (
            np.zeros((0,), dtype=np.float32),
            np.zeros((0,), dtype=np.int64),
            np.zeros((0,), dtype=np.int64),
        )
    return (
        np.concatenate(Xs, axis=0),
        np.concatenate(ys, axis=0),
        np.concatenate(subs, axis=0) if subs else np.zeros((0,), dtype=np.int64),
    )


def balanced_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(balanced_accuracy_score(y_true, y_pred))


def bits_per_second(y_true: np.ndarray, y_pred: np.ndarray, epoch_seconds: float) -> float:
    """Empirical mutual information between predictions and truth, in bits/sec.

    Uses the confusion-matrix estimator I(Y;Y_hat) = H(Y) - H(Y|Y_hat), which
    is the tight lower-bound on the channel that would be needed to transmit
    the (binary) label at the epoch rate. This is the plan's 'bandwidth as
    bits/second of MI' metric.
    """
    if len(y_true) == 0:
        return 0.0
    labels = np.unique(np.concatenate([y_true, y_pred]))
    joint = np.zeros((len(labels), len(labels)), dtype=np.float64)
    idx = {int(v): i for i, v in enumerate(labels)}
    for t, p in zip(y_true, y_pred):
        joint[idx[int(t)], idx[int(p)]] += 1.0
    joint /= joint.sum()
    py = joint.sum(axis=1, keepdims=True)
    pyhat = joint.sum(axis=0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(joint > 0, joint / (py @ pyhat), 1.0)
        info_bits = float(np.sum(joint * np.log2(np.where(ratio > 0, ratio, 1.0))))
    return info_bits / max(epoch_seconds, 1e-9) if not math.isnan(info_bits) else 0.0
