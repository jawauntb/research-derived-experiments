"""Tests for the Wave 1b Zhang-Levin epiplexity module.

Five regressions per the Wave 1b task brief for epiplexity:

(a) :class:`SharedQREpiplexity` agrees with the frozen L0 pilot
    :class:`ReservoirEpiplexity` to ``max_diff < 1e-6`` on a fixed toy
    candidate set with shared ``X_tilde``.
(b) :meth:`SharedQREpiplexity.assert_shared_design` raises
    :class:`SharedDesignError` when a per-candidate reservoir state
    disagrees with the cached ``X_tilde``.
(c) The determinant identity ``det(I_m + eta W W^T) = det(I_D + eta W^T W)``
    is used correctly — the ``D == 1`` branch matches
    ``0.5 * log2(1 + eta * ||w||^2)`` byte-for-byte.
(d) :meth:`SharedQREpiplexity.score_batch` is deterministic — repeated
    calls with the same futures return byte-identical arrays, and
    per-candidate :meth:`score` calls match the batched output.
(e) :class:`IndependentSolveEpiplexity` is the correct fallback when
    ``X_tilde`` changes per candidate; it agrees with the frozen L0
    pilot on the changed-design toy.
"""

from __future__ import annotations

from math import sqrt

import numpy as np
import pytest

from experiments.concern_gated_retrieval.epiplexity import ReservoirEpiplexity
from experiments.concern_gated_retrieval_e2.wave1b.epiplexity import (
    IndependentSolveEpiplexity,
    SharedDesignError,
    SharedQREpiplexity,
)
from experiments.concern_gated_retrieval_e2.wave1b.epiplexity_validation import (
    cross_validate_against_full,
    cross_validate_independent,
)


# --------------------------------------------------------------------------- #
# (a) Shared-QR vs frozen L0 pilot on shared X_tilde                          #
# --------------------------------------------------------------------------- #


def test_shared_qr_matches_reservoir_epiplexity_on_shared_design() -> None:
    receipt = cross_validate_against_full(sample_size=32)
    assert receipt["sample_size"] == 32
    assert receipt["max_diff"] < 1e-6
    # We expect exact-equivalence under float64 QR, not merely
    # regression-tolerance; check a much tighter bound too so the test
    # would trip on any algorithmic drift, not just gross bugs.
    assert receipt["max_diff"] < 1e-10
    assert receipt["rank_correlation"] == pytest.approx(1.0)


# --------------------------------------------------------------------------- #
# (b) Refuse the shared-QR trick when X_tilde changes per candidate           #
# --------------------------------------------------------------------------- #


def test_assert_shared_design_raises_when_reservoir_state_differs() -> None:
    rng = np.random.default_rng(20260724)
    state = rng.normal(size=(16, 8))
    shared = SharedQREpiplexity(reservoir_state=state, ridge_lambda=1.0, eta=1.0)

    # Identical state — no raise.
    shared.assert_shared_design(np.stack([state, state, state]))

    # Perturb one candidate — must raise.
    perturbed = np.stack([state, state.copy(), state])
    perturbed[1, 0, 0] += 1e-9
    with pytest.raises(SharedDesignError):
        shared.assert_shared_design(perturbed)

    # Wrong shape — also raises SharedDesignError.
    with pytest.raises(SharedDesignError):
        shared.assert_shared_design(rng.normal(size=(3, 16, 7)))


# --------------------------------------------------------------------------- #
# (c) Determinant identity — D == 1 branch matches the closed form            #
# --------------------------------------------------------------------------- #


def test_determinant_identity_scalar_output_matches_closed_form() -> None:
    """For ``D == 1`` the identity collapses to ``0.5 log2 (1 + eta * ||w||^2)``.

    We compute ``S^phi`` two ways for the same shared design + scalar
    future:

    * via :meth:`SharedQREpiplexity.score` (which internally uses the
      D == 1 branch);
    * via the explicit paper-side formula
      ``0.5 * log2 (1 + eta * ||w||^2)`` where ``w`` is solved from
      the same augmented QR.

    They must agree exactly (float64), and both must agree with the
    generic ``slogdet(I_D + eta W^T W)`` fallback with ``D = 1``.
    """

    rng = np.random.default_rng(20260724 + 1)
    trajectory_length = 20
    m = 6
    ridge_lambda = 0.7
    eta = 1.3

    state = rng.normal(size=(trajectory_length, m))
    future = rng.normal(size=(trajectory_length, 1))

    shared = SharedQREpiplexity(
        reservoir_state=state,
        ridge_lambda=ridge_lambda,
        eta=eta,
    )
    branch_score = shared.score(future)

    # Explicit W via augmented QR (mirrors the module internals, but
    # written out inline so an algorithmic drift in the module code
    # would not silently pass this test).
    augmented = np.vstack(
        (state, sqrt(ridge_lambda) * np.eye(m, dtype=np.float64))
    )
    q, r = np.linalg.qr(augmented, mode="reduced")
    rhs = np.vstack((future, np.zeros((m, 1), dtype=np.float64)))
    w = np.linalg.solve(r, q.T @ rhs)  # shape [m, 1]
    closed_form = 0.5 * np.log2(1.0 + eta * float(np.dot(w[:, 0], w[:, 0])))
    assert branch_score == pytest.approx(closed_form, rel=0, abs=1e-14)

    # And the generic slogdet(I_D + eta W^T W) with D == 1 — must also
    # match. This is the sanity check that the identity is correct.
    gram_output = np.eye(1) + eta * (w.T @ w)
    sign, log_det = np.linalg.slogdet(gram_output)
    assert sign == 1.0
    generic_score = float(0.5 * log_det / np.log(2.0))
    assert branch_score == pytest.approx(generic_score, rel=0, abs=1e-13)

    # For completeness: the paper's original m x m form must also agree.
    gram_input = np.eye(m) + eta * (w @ w.T)
    sign_in, log_det_in = np.linalg.slogdet(gram_input)
    assert sign_in == 1.0
    input_side_score = float(0.5 * log_det_in / np.log(2.0))
    assert branch_score == pytest.approx(input_side_score, rel=0, abs=1e-12)


# --------------------------------------------------------------------------- #
# (d) score_batch is deterministic and matches per-candidate score            #
# --------------------------------------------------------------------------- #


def test_score_batch_is_deterministic_and_matches_per_candidate_score() -> None:
    rng = np.random.default_rng(20260724 + 2)
    trajectory_length = 24
    m = 8
    n = 12
    d = 1

    state = rng.normal(size=(trajectory_length, m))
    futures = rng.normal(size=(n, trajectory_length, d))

    shared = SharedQREpiplexity(reservoir_state=state, ridge_lambda=1.0, eta=1.0)

    # Determinism — byte-identical outputs across calls.
    first = shared.score_batch(futures)
    second = shared.score_batch(futures)
    np.testing.assert_array_equal(first, second)
    assert first.shape == (n,)
    assert first.dtype == np.float64

    # Batched output equals per-candidate scoring.
    per_candidate = np.array(
        [shared.score(futures[i]) for i in range(n)], dtype=np.float64
    )
    np.testing.assert_allclose(first, per_candidate, rtol=0, atol=1e-13)

    # Also validate the multi-D branch runs deterministically and matches
    # per-candidate score on D > 1 futures (a genuinely different code
    # path than the D == 1 fast branch).
    futures_multi = rng.normal(size=(n, trajectory_length, 3))
    batch_multi_first = shared.score_batch(futures_multi)
    batch_multi_second = shared.score_batch(futures_multi)
    np.testing.assert_array_equal(batch_multi_first, batch_multi_second)
    per_candidate_multi = np.array(
        [shared.score(futures_multi[i]) for i in range(n)],
        dtype=np.float64,
    )
    np.testing.assert_allclose(
        batch_multi_first, per_candidate_multi, rtol=0, atol=1e-12
    )


# --------------------------------------------------------------------------- #
# (e) Independent-QR fallback when X_tilde changes per candidate              #
# --------------------------------------------------------------------------- #


def test_independent_solve_matches_reservoir_epiplexity_when_x_tilde_varies() -> None:
    receipt = cross_validate_independent(sample_size=8)
    assert receipt["sample_size"] == 8
    assert receipt["max_diff"] < 1e-6
    assert receipt["max_diff"] < 1e-10  # exact equivalence in float64

    # Direct end-to-end check: build a change-of-design case, run the
    # frozen L0 pilot per candidate, and confirm
    # IndependentSolveEpiplexity.score_batch reproduces every value.
    rng = np.random.default_rng(20260724 + 3)
    reservoir = ReservoirEpiplexity(input_dimension=4, width=10, ridge=1.0, eta=1.0)
    n = 5
    T = 20
    features = np.empty((n, T, 10), dtype=np.float64)
    futures = np.empty((n, T, 1), dtype=np.float64)
    ref = np.empty(n, dtype=np.float64)
    for i in range(n):
        inputs = rng.normal(size=(T, 4))
        y = rng.normal(size=(T,))
        # Re-derive the L0 pilot's internal standardised design so we
        # feed the SAME (X, Y) into both implementations.
        proj_rng = np.random.default_rng(reservoir.seed)
        projection = proj_rng.normal(
            0.0, 1 / sqrt(reservoir.input_dimension), size=(4, 10)
        )
        bias = proj_rng.normal(0.0, 0.35, size=(10,))
        raw = np.tanh(inputs @ projection + bias)
        centred = raw - raw.mean(axis=0, keepdims=True)
        scale = centred.std(axis=0, keepdims=True)
        scale = np.where(scale > 1e-12, scale, 1.0)
        features[i] = centred / (scale * sqrt(10))
        futures[i, :, 0] = (y - y.mean()) / reservoir.target_scale
        ref[i] = reservoir.score(inputs, y)

    independent = IndependentSolveEpiplexity(ridge_lambda=1.0, eta=1.0)
    got = independent.score_batch(features, futures)
    np.testing.assert_allclose(got, ref, rtol=0, atol=1e-10)
