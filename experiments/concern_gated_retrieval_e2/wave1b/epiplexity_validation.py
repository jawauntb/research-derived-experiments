"""Regression harness proving SharedQREpiplexity == ReservoirEpiplexity on
the shared-X_tilde case.

This is an EQUIVALENCE proof for the shared-design regime only. It is
NOT a claim that :class:`SharedQREpiplexity` always approximates the
frozen L0 pilot :class:`ReservoirEpiplexity` — the shared-QR speedup is
mathematically exact iff every candidate observes the same reservoir
state ``X_tilde``. When ``X_tilde`` changes per candidate the caller
must use :class:`IndependentSolveEpiplexity` instead, and that regime
has its own equivalence property (per-candidate QR equals the full
readout by construction).

The frozen L0 pilot lives at
``experiments/concern_gated_retrieval/epiplexity.py`` and its exact
standardisation (projection, tanh, per-column centring and scaling by
``std * sqrt(width)``, target centring by ``target_scale``) is
reproduced below so we can feed the *same* ``X_tilde`` and ``Y_c`` to
both implementations. If the L0 pilot's standardisation ever changes,
this helper — and the wave 1b regression test — will fail loudly, which
is the intended freeze behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any, Dict

import numpy as np
from numpy.typing import NDArray

from experiments.concern_gated_retrieval.epiplexity import ReservoirEpiplexity
from experiments.concern_gated_retrieval_e2.wave1b.epiplexity import (
    IndependentSolveEpiplexity,
    SharedQREpiplexity,
)


FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class _Standardisation:
    """The ``X_tilde``, ``Y_tilde`` the L0 pilot forms internally.

    Recomputing these once and handing them to SharedQREpiplexity is the
    ONLY way to prove exact equivalence without editing the frozen L0
    module.
    """

    features: FloatArray  # shape [T, width]
    targets: FloatArray   # shape [T, D]


def _l0_standardised(
    reservoir: ReservoirEpiplexity,
    inputs: FloatArray,
    targets: FloatArray,
) -> _Standardisation:
    """Recompute the L0 pilot's internal standardised design + targets.

    Byte-for-byte replica of the pre-``lstsq`` block in
    :meth:`experiments.concern_gated_retrieval.epiplexity.ReservoirEpiplexity.readout`.
    Any drift between this helper and the frozen L0 pilot must trip
    :func:`cross_validate_against_full` — that is the whole point of
    the regression harness.
    """

    inputs = np.asarray(inputs, dtype=np.float64)
    targets = np.asarray(targets, dtype=np.float64)
    if targets.ndim == 1:
        targets = targets[:, None]

    rng = np.random.default_rng(reservoir.seed)
    projection = rng.normal(
        0.0,
        1 / sqrt(reservoir.input_dimension),
        size=(reservoir.input_dimension, reservoir.width),
    )
    bias = rng.normal(0.0, 0.35, size=(reservoir.width,))
    features = np.tanh(inputs @ projection + bias)

    centred = features - features.mean(axis=0, keepdims=True)
    scale = centred.std(axis=0, keepdims=True)
    scale = np.where(scale > 1e-12, scale, 1.0)
    standardised = centred / (scale * sqrt(reservoir.width))

    standardised_targets = (
        targets - targets.mean(axis=0, keepdims=True)
    ) / reservoir.target_scale

    return _Standardisation(features=standardised, targets=standardised_targets)


def cross_validate_against_full(
    sample_size: int = 32,
    *,
    trajectory_length: int = 24,
    input_dimension: int = 5,
    width: int = 12,
    ridge: float = 1.0,
    eta: float = 1.0,
    seed: int = 20260724,
) -> Dict[str, Any]:
    """Compare SharedQREpiplexity vs the frozen L0 ReservoirEpiplexity.

    Draws a fixed ``sample_size`` toy candidate set with a single
    shared input matrix (the ``X_tilde`` case the shared-QR trick
    covers) and ``sample_size`` distinct scalar-output futures. Returns
    a receipt with ``max_diff``, ``mean_diff``, ``rank_correlation``
    (Spearman) between the two score vectors, and per-candidate values.
    Also asserts ``max_diff < 1e-6``.

    This is a REGRESSION test, not a proof that shared-QR always
    matches full: it is only valid because the toy candidate set is
    constructed to satisfy the shared-``X_tilde`` condition.
    """

    if sample_size < 2:
        raise ValueError("sample_size must be at least 2 for rank correlation")

    rng = np.random.default_rng(seed)
    inputs = rng.normal(size=(trajectory_length, input_dimension))
    futures = rng.normal(size=(sample_size, trajectory_length))

    reservoir = ReservoirEpiplexity(
        input_dimension=input_dimension,
        width=width,
        ridge=ridge,
        eta=eta,
    )

    # Frozen L0 pilot side — one call per candidate. The pilot has no
    # batched API, so this is the honest "full" baseline.
    full_scores = np.empty(sample_size, dtype=np.float64)
    standardised_features_reference: FloatArray | None = None
    standardised_futures = np.empty(
        (sample_size, trajectory_length, 1), dtype=np.float64
    )
    for i in range(sample_size):
        full_scores[i] = reservoir.score(inputs, futures[i])
        standardised = _l0_standardised(reservoir, inputs, futures[i])
        if standardised_features_reference is None:
            standardised_features_reference = standardised.features
        else:
            # Sanity — the shared-QR case must actually be shared.
            if not np.array_equal(
                standardised.features, standardised_features_reference
            ):
                raise AssertionError(
                    "L0 standardised features drifted between candidates "
                    "in what should be a shared-X_tilde toy; the "
                    "regression harness is misconfigured"
                )
        standardised_futures[i] = standardised.targets

    assert standardised_features_reference is not None  # for type-checkers
    shared = SharedQREpiplexity(
        reservoir_state=standardised_features_reference,
        ridge_lambda=ridge,
        eta=eta,
    )
    shared_scores = shared.score_batch(standardised_futures)

    diffs = np.abs(full_scores - shared_scores)
    max_diff = float(diffs.max())
    mean_diff = float(diffs.mean())

    # Rank correlation — deterministic Spearman via argsort-of-argsort.
    def _ranks(values: FloatArray) -> FloatArray:
        order = np.argsort(values, kind="stable")
        ranks = np.empty_like(order)
        ranks[order] = np.arange(values.size)
        return ranks.astype(np.float64)

    r_full = _ranks(full_scores)
    r_shared = _ranks(shared_scores)
    r_full_centred = r_full - r_full.mean()
    r_shared_centred = r_shared - r_shared.mean()
    denom = float(
        np.sqrt((r_full_centred**2).sum() * (r_shared_centred**2).sum())
    )
    rank_corr = float((r_full_centred * r_shared_centred).sum() / denom) if denom > 0 else 1.0

    if not (max_diff < 1e-6):
        raise AssertionError(
            f"SharedQREpiplexity disagrees with frozen L0 ReservoirEpiplexity "
            f"beyond regression tolerance: max_diff={max_diff:.3e} "
            f"mean_diff={mean_diff:.3e}"
        )

    return {
        "sample_size": int(sample_size),
        "max_diff": max_diff,
        "mean_diff": mean_diff,
        "rank_correlation": rank_corr,
        "full_scores": full_scores.tolist(),
        "shared_scores": shared_scores.tolist(),
        "ridge_lambda": float(ridge),
        "eta": float(eta),
        "input_dimension": int(input_dimension),
        "width": int(width),
        "trajectory_length": int(trajectory_length),
        "seed": int(seed),
    }


def cross_validate_independent(
    sample_size: int = 8,
    *,
    trajectory_length: int = 16,
    input_dimension: int = 4,
    width: int = 10,
    ridge: float = 1.0,
    eta: float = 1.0,
    seed: int = 20260724,
) -> Dict[str, Any]:
    """Independent-QR fallback equivalence receipt.

    Draws ``sample_size`` DIFFERENT input matrices — the changed-X_tilde
    regime — and confirms :class:`IndependentSolveEpiplexity` agrees
    with :class:`ReservoirEpiplexity` per candidate.
    """

    if sample_size < 2:
        raise ValueError("sample_size must be at least 2")

    rng = np.random.default_rng(seed)
    reservoir = ReservoirEpiplexity(
        input_dimension=input_dimension,
        width=width,
        ridge=ridge,
        eta=eta,
    )
    features_per_candidate = np.empty(
        (sample_size, trajectory_length, width), dtype=np.float64
    )
    futures_per_candidate = np.empty(
        (sample_size, trajectory_length, 1), dtype=np.float64
    )
    full_scores = np.empty(sample_size, dtype=np.float64)
    for i in range(sample_size):
        inputs = rng.normal(size=(trajectory_length, input_dimension))
        future = rng.normal(size=(trajectory_length,))
        standardised = _l0_standardised(reservoir, inputs, future)
        features_per_candidate[i] = standardised.features
        futures_per_candidate[i] = standardised.targets
        full_scores[i] = reservoir.score(inputs, future)

    independent = IndependentSolveEpiplexity(ridge_lambda=ridge, eta=eta)
    scores = independent.score_batch(
        features_per_candidate, futures_per_candidate
    )

    diffs = np.abs(full_scores - scores)
    max_diff = float(diffs.max())
    if not (max_diff < 1e-6):
        raise AssertionError(
            f"IndependentSolveEpiplexity disagrees with frozen L0 "
            f"ReservoirEpiplexity beyond tolerance: max_diff={max_diff:.3e}"
        )
    return {
        "sample_size": int(sample_size),
        "max_diff": max_diff,
        "mean_diff": float(diffs.mean()),
        "full_scores": full_scores.tolist(),
        "independent_scores": scores.tolist(),
        "ridge_lambda": float(ridge),
        "eta": float(eta),
    }


__all__ = [
    "cross_validate_against_full",
    "cross_validate_independent",
]
