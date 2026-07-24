"""Wave 1b Zhang-Levin epiplexity with the one legitimate shared-QR speedup.

Read the operator's memory entry ``reference-zhang-levin-epiplexity`` before
touching this module. The Zhang & Levin (2026) score is

    S^phi_c = (1/2) log_2 det( I_m + eta * W_c W_c^T )

where ``W_c`` is the ridge-regression readout mapping a frozen reservoir
state ``X_tilde`` onto a candidate-conditioned future ``Y_c``. The paper
solves ``W_c`` via QR on the augmented design

    A = [ X_tilde ; sqrt(lambda) * I_m ] = Q R
    W_c = R^{-1} Q^T [ Y_c ; 0 ]

NOT by forming and inverting a Gram matrix, and NOT via the scalar quadratic
form ``y^T (K + lambda I)^{-1} y`` (which only agrees with the general
estimator in the scalar-output reduction).

There is ONE — and only one — legitimate exact speedup:

1. Compute the augmented QR of ``A`` **once**, before iterating over
   candidates. This is valid iff every candidate shares the same
   reservoir state ``X_tilde`` (the trick refuses otherwise).
2. Solve every ``W_c`` as multiple right-hand sides against the same ``R``
   by triangular back-substitution — a single batched solve, no per-
   candidate QR.
3. Apply the determinant identity
       det( I_m + eta * W W^T ) = det( I_D + eta * W^T W )
   so the ``m x m`` log-determinant collapses to ``D x D`` where ``D`` is
   the output-future dimensionality. For scalar output (``D == 1``) this
   reduces to ``S^phi_c = (1/2) log_2 (1 + eta * ||w_c||^2)`` — the
   dedicated ``D == 1`` code path below evaluates that formula directly
   instead of a length-1 slogdet.

Critical condition. The shared-QR trick works ONLY when the candidate
protocol shares ``X_tilde``. If loading candidate ``c`` changes the
agent's state, then the trajectory changes, and therefore both ``X_c``
and ``Y_c`` change per candidate: there is no single QR to reuse.
:class:`SharedQREpiplexity.assert_shared_design` refuses that regime, and
:class:`IndependentSolveEpiplexity` is the fallback — batched independent
QR per candidate, *not* a shared-factorization win.

Design invariants
-----------------

* No Rademacher-complexity, Nystrom / random-feature, MMD, or LZ
  "approximation" of epiplexity is provided. No theorem connects those
  quantities to ``log det (I + eta W W^T)``; they would be *alternative
  bounded observers* and require a separate empirical validation study.
* No unqualified "20-30x speedup" claim appears in this module or in any
  Wave 1b receipt. Speedups are measured and reported, never projected.
* All linear algebra runs in float64 for exact-equivalence regression
  against the frozen L0 pilot :class:`ReservoirEpiplexity`.
"""

from __future__ import annotations

from math import isfinite, log, sqrt

import numpy as np
import scipy.linalg
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]


_LN2 = log(2.0)


class SharedDesignError(RuntimeError):
    """Raised when a batch of candidates does not share ``X_tilde``.

    The shared-QR speedup is only valid when every candidate observes the
    same reservoir state matrix. If per-candidate reservoir states differ
    even by a single ulp, :meth:`SharedQREpiplexity.assert_shared_design`
    raises this error and the caller must fall back to
    :class:`IndependentSolveEpiplexity`.
    """


class SharedQREpiplexity:
    """Exact Zhang-Levin score for a batch of candidates whose input
    design ``X_tilde`` is SHARED across the batch.

    The augmented QR of ``A = [X_tilde ; sqrt(lambda) I]`` is computed
    exactly once at construction. Each subsequent :meth:`score` or
    :meth:`score_batch` call solves the ridge readout ``W_c`` via
    triangular back-substitution against the cached ``R`` and returns
    ``S^phi_c`` via the ``det(I_m + eta W W^T) = det(I_D + eta W^T W)``
    identity in output space.

    If the candidate protocol changes ``X_tilde`` per candidate, this
    class refuses via :meth:`assert_shared_design` and the caller must
    use :class:`IndependentSolveEpiplexity` instead. No
    shared-factorization speedup is claimed in that regime.
    """

    def __init__(
        self,
        reservoir_state: FloatArray,
        ridge_lambda: float,
        eta: float,
    ) -> None:
        state = np.asarray(reservoir_state, dtype=np.float64)
        if state.ndim != 2:
            raise ValueError(
                "reservoir_state must be a 2D [T, m] array; got "
                f"shape {state.shape}"
            )
        if state.shape[0] < 1 or state.shape[1] < 1:
            raise ValueError("reservoir_state must have T >= 1 and m >= 1")
        if not np.isfinite(state).all():
            raise ValueError("reservoir_state must be finite")
        for name, value in (("ridge_lambda", ridge_lambda), ("eta", eta)):
            if not isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")

        self._reservoir_state: FloatArray = state
        self._T: int = int(state.shape[0])
        self._m: int = int(state.shape[1])
        self._ridge_lambda: float = float(ridge_lambda)
        self._eta: float = float(eta)

        # Augmented design A = [ X_tilde ; sqrt(lambda) I_m ] with shape
        # [T + m, m]. Reduced QR yields Q shape [T + m, m], R shape
        # [m, m] upper-triangular. The Gram matrix X^T X + lambda I is
        # positive definite for lambda > 0, so R is nonsingular and the
        # back-substitution is well-posed.
        regulariser = sqrt(self._ridge_lambda) * np.eye(self._m, dtype=np.float64)
        augmented = np.vstack((state, regulariser))
        self._Q: FloatArray
        self._R: FloatArray
        self._Q, self._R = np.linalg.qr(augmented, mode="reduced")

    # ------------------------------------------------------------------
    # Introspection helpers (used by validation harness + tests)
    # ------------------------------------------------------------------
    @property
    def reservoir_state(self) -> FloatArray:
        """Return a read-only view of the cached ``X_tilde``."""

        view = self._reservoir_state.view()
        view.flags.writeable = False
        return view

    @property
    def R(self) -> FloatArray:  # noqa: N802 — matches the paper's symbol
        """Return a read-only view of the upper-triangular ``R`` factor."""

        view = self._R.view()
        view.flags.writeable = False
        return view

    @property
    def Q(self) -> FloatArray:  # noqa: N802 — matches the paper's symbol
        """Return a read-only view of the orthonormal ``Q`` factor."""

        view = self._Q.view()
        view.flags.writeable = False
        return view

    @property
    def T(self) -> int:  # noqa: N802 — matches the paper's symbol
        return self._T

    @property
    def m(self) -> int:
        return self._m

    @property
    def ridge_lambda(self) -> float:
        return self._ridge_lambda

    @property
    def eta(self) -> float:
        return self._eta

    # ------------------------------------------------------------------
    # Core scoring
    # ------------------------------------------------------------------
    def _solve_readout(self, candidate_future: FloatArray) -> FloatArray:
        """Solve ``W_c = R^{-1} Q^T [candidate_future ; 0]`` (back-sub)."""

        rhs_top = candidate_future
        rhs = np.vstack(
            (
                rhs_top,
                np.zeros((self._m, rhs_top.shape[1]), dtype=np.float64),
            )
        )
        qt_rhs = self._Q.T @ rhs  # shape [m, D]
        # ``R`` is upper triangular; triangular back-substitution is
        # numerically preferred to a general solve here.
        return scipy.linalg.solve_triangular(
            self._R,
            qt_rhs,
            lower=False,
            check_finite=False,
        )

    def _score_from_readout(self, readout: FloatArray) -> float:
        """Return ``0.5 log2 det(I_D + eta W^T W)`` in bits.

        For ``D == 1`` this reduces to ``0.5 log2 (1 + eta * ||w||^2)``.
        """

        d = readout.shape[1]
        if d == 1:
            # Dedicated scalar-output branch — see docstring header. This
            # is the D == 1 collapse of the determinant identity, not a
            # separate algorithm.
            w_norm_sq = float(np.dot(readout[:, 0], readout[:, 0]))
            return 0.5 * np.log2(1.0 + self._eta * w_norm_sq)
        gram = np.eye(d, dtype=np.float64) + self._eta * (readout.T @ readout)
        sign, log_determinant = np.linalg.slogdet(gram)
        if sign <= 0:
            raise RuntimeError(
                "epiplexity output-space Gram is not positive definite"
            )
        return float(0.5 * log_determinant / _LN2)

    def score(self, candidate_future: FloatArray) -> float:
        """Return ``S^phi_c`` for a single candidate future.

        ``candidate_future`` has shape ``[T, D]``. If a 1D array of length
        ``T`` is supplied it is treated as ``D == 1``.
        """

        cf = np.asarray(candidate_future, dtype=np.float64)
        if cf.ndim == 1:
            cf = cf[:, None]
        if cf.ndim != 2 or cf.shape[0] != self._T:
            raise ValueError(
                "candidate_future must have shape [T, D] with the same T "
                f"as the reservoir state ({self._T}); got shape {cf.shape}"
            )
        if not np.isfinite(cf).all():
            raise ValueError("candidate_future must be finite")
        readout = self._solve_readout(cf)
        return self._score_from_readout(readout)

    def score_batch(self, futures: FloatArray) -> FloatArray:
        """Return ``S^phi_c`` for every candidate in ``futures``.

        ``futures`` has shape ``[N, T, D]``. All candidates share the
        cached ``X_tilde``; this is the whole point of :class:`SharedQREpiplexity`.
        The implementation stacks all ``N`` right-hand sides into a
        single matrix ``[T + m, N * D]`` and calls the triangular solver
        once, so the QR is amortised across the batch.
        """

        arr = np.asarray(futures, dtype=np.float64)
        if arr.ndim == 2:
            # Interpret as [N, T] scalar-output batch and broadcast to
            # [N, T, 1] so the fast D == 1 branch below fires uniformly.
            arr = arr[:, :, None]
        if arr.ndim != 3:
            raise ValueError(
                "futures must have shape [N, T, D]; got shape "
                f"{arr.shape}"
            )
        n_candidates, t_axis, d_axis = arr.shape
        if t_axis != self._T:
            raise ValueError(
                "futures T axis must match the reservoir state "
                f"({self._T}); got {t_axis}"
            )
        if not np.isfinite(arr).all():
            raise ValueError("futures must be finite")

        # Stack all right-hand sides. The zero-augmentation is the
        # bottom [m, N * D] block; np.zeros is cheap even for D * N
        # large because we only pay it once per batch.
        rhs = np.zeros(
            (self._T + self._m, n_candidates * d_axis),
            dtype=np.float64,
        )
        # Fill the top block with each candidate future in column order.
        # candidate i occupies columns [i * d_axis, (i + 1) * d_axis).
        for i in range(n_candidates):
            rhs[: self._T, i * d_axis : (i + 1) * d_axis] = arr[i]
        qt_rhs = self._Q.T @ rhs  # shape [m, N * D]
        readouts = scipy.linalg.solve_triangular(
            self._R,
            qt_rhs,
            lower=False,
            check_finite=False,
        )  # shape [m, N * D]

        scores = np.empty(n_candidates, dtype=np.float64)
        if d_axis == 1:
            # D == 1 collapse — vectorised across the batch.
            # readouts.shape = [m, N], per-candidate ||w||^2 = column norm^2.
            column_norm_sq = np.einsum("ij,ij->j", readouts, readouts)
            scores[:] = 0.5 * np.log2(1.0 + self._eta * column_norm_sq)
            return scores
        for i in range(n_candidates):
            w_c = readouts[:, i * d_axis : (i + 1) * d_axis]
            scores[i] = self._score_from_readout(w_c)
        return scores

    # ------------------------------------------------------------------
    # Shared-design gate
    # ------------------------------------------------------------------
    def assert_shared_design(
        self,
        reservoir_state_per_candidate: FloatArray,
    ) -> None:
        """Refuse the shared-QR trick if candidates do not share ``X_tilde``.

        Accepts an ``[N, T, m]`` (or ``[T, m]`` for a single candidate)
        array of per-candidate reservoir states. Raises
        :class:`SharedDesignError` if any candidate's state disagrees
        byte-for-byte with the cached ``X_tilde``. This is the gate the
        Wave 1b crossed-runner MUST call before using
        :meth:`score_batch`; if it fires, the runner has to fall back to
        :class:`IndependentSolveEpiplexity`.
        """

        arr = np.asarray(reservoir_state_per_candidate, dtype=np.float64)
        if arr.ndim == 2:
            arr = arr[None, :, :]
        if arr.ndim != 3:
            raise ValueError(
                "reservoir_state_per_candidate must have shape "
                f"[N, T, m]; got shape {arr.shape}"
            )
        if arr.shape[1] != self._T or arr.shape[2] != self._m:
            raise SharedDesignError(
                "candidate reservoir states have shape "
                f"{arr.shape[1:]}; expected ({self._T}, {self._m})"
            )
        for i in range(arr.shape[0]):
            if not np.array_equal(arr[i], self._reservoir_state):
                raise SharedDesignError(
                    "candidate reservoir state does not match the "
                    f"shared design at index {i}; the shared-QR "
                    "speedup does not apply — use "
                    "IndependentSolveEpiplexity"
                )


class IndependentSolveEpiplexity:
    """Exact Zhang-Levin score when ``X_tilde`` changes per candidate.

    If loading candidate ``c`` changes the agent's state, then both
    ``X_c`` (the reservoir state) and ``Y_c`` (the candidate-conditioned
    future) differ per candidate: there is no single ``R`` to reuse and
    the shared-QR trick does not apply. This class runs an independent
    augmented QR + triangular solve per candidate. Batching is possible
    on GPU (candidates are independent) but that is NOT a
    shared-factorization speedup — this class exists precisely so no
    misleading "20-30x" claim can attach to a per-candidate protocol.
    """

    def __init__(self, ridge_lambda: float, eta: float) -> None:
        for name, value in (("ridge_lambda", ridge_lambda), ("eta", eta)):
            if not isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        self._ridge_lambda = float(ridge_lambda)
        self._eta = float(eta)

    @property
    def ridge_lambda(self) -> float:
        return self._ridge_lambda

    @property
    def eta(self) -> float:
        return self._eta

    def _score_one(
        self,
        features: FloatArray,
        future: FloatArray,
    ) -> float:
        # Per-candidate augmented QR — no reuse across candidates.
        m = features.shape[1]
        regulariser = sqrt(self._ridge_lambda) * np.eye(m, dtype=np.float64)
        augmented_features = np.vstack((features, regulariser))
        rhs = np.vstack((future, np.zeros((m, future.shape[1]), dtype=np.float64)))
        q, r = np.linalg.qr(augmented_features, mode="reduced")
        qt_rhs = q.T @ rhs
        readout = scipy.linalg.solve_triangular(
            r,
            qt_rhs,
            lower=False,
            check_finite=False,
        )
        d = readout.shape[1]
        if d == 1:
            w_norm_sq = float(np.dot(readout[:, 0], readout[:, 0]))
            return 0.5 * np.log2(1.0 + self._eta * w_norm_sq)
        gram = np.eye(d, dtype=np.float64) + self._eta * (readout.T @ readout)
        sign, log_determinant = np.linalg.slogdet(gram)
        if sign <= 0:
            raise RuntimeError(
                "epiplexity output-space Gram is not positive definite"
            )
        return float(0.5 * log_determinant / _LN2)

    def score_batch(
        self,
        features_per_candidate: FloatArray,
        futures_per_candidate: FloatArray,
    ) -> FloatArray:
        """Return ``S^phi_c`` per candidate under independent QRs.

        ``features_per_candidate`` has shape ``[N, T, m]``; each slice is
        the reservoir state ``X_c`` for candidate ``c``.
        ``futures_per_candidate`` has shape ``[N, T, D]``; each slice is
        the future ``Y_c``. ``T`` may vary across the caller's outer
        loop but must be consistent within a single batch.
        """

        feats = np.asarray(features_per_candidate, dtype=np.float64)
        futs = np.asarray(futures_per_candidate, dtype=np.float64)
        if feats.ndim == 2:
            feats = feats[None, :, :]
        if futs.ndim == 2:
            futs = futs[None, :, :] if futs.shape[0] == feats.shape[1] else futs[:, :, None]
        if feats.ndim != 3:
            raise ValueError(
                "features_per_candidate must have shape [N, T, m]; got "
                f"{feats.shape}"
            )
        if futs.ndim != 3:
            raise ValueError(
                "futures_per_candidate must have shape [N, T, D]; got "
                f"{futs.shape}"
            )
        if feats.shape[0] != futs.shape[0]:
            raise ValueError(
                "features and futures must share candidate count N; got "
                f"{feats.shape[0]} vs {futs.shape[0]}"
            )
        if feats.shape[1] != futs.shape[1]:
            raise ValueError(
                "features and futures must share T; got "
                f"{feats.shape[1]} vs {futs.shape[1]}"
            )
        if not np.isfinite(feats).all() or not np.isfinite(futs).all():
            raise ValueError("features and futures must be finite")

        n = feats.shape[0]
        scores = np.empty(n, dtype=np.float64)
        for i in range(n):
            scores[i] = self._score_one(feats[i], futs[i])
        return scores


__all__ = [
    "SharedDesignError",
    "SharedQREpiplexity",
    "IndependentSolveEpiplexity",
]
