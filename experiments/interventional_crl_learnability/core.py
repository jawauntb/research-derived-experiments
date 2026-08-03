"""Fourth partial positive resolution of SIC-C-c (uniform polynomial-in-d_Z
learnability) --- this time for the *interventional causal representation
learning* inductive-bias class (Ahuja--Mahajan--Wang--Bengio 2022,
"Interventional Causal Representation Learning"; Squires et al. 2023).

Paper section 2.5c notes that after linear ICA (instrument 8), sparse ICA /
IMA (instrument 9), and iVAE (instrument 10), "other inductive-bias classes
... have their own analogues, each with its own sample-complexity theorem.
A full SIC-C-c programme would add one more instrument per class." This is
the interventional-CRL sibling: a numerical witness that access to
single-node-intervention environments provides the auxiliary information
needed to lift Theorem 6's exponential-in-d_Z bound to uniform polynomial
sample complexity.

Setup (single-node interventional CRL, simplified).
---------------------------------------------------
- Latent ``Z`` in ``R^{d_Z}`` with independent Laplace(0, 1) marginals under
  the "observational" distribution (environment label ``E = 0``).
- For each intervention target ``i in {1, ..., d_Z}``, environment ``E = i``
  is defined by drawing ``Z_i`` from ``Laplace(mu_i, 0.5)`` (a shifted,
  tighter distribution than the observational one) while every other
  ``Z_j`` (``j != i``) remains ``Laplace(0, 1)``. The per-component
  intervention offset ``mu_i`` is drawn once per (seed, d_Z) uniformly on
  ``[INTERVENTION_MU_MIN, INTERVENTION_MU_MAX]`` and then fixed across
  every trial, so the intervention is a *single-node do-style* shift on
  ``Z_i`` --- exactly the setting of Ahuja 2022 Theorem 4.4.
- Nonlinear mixing ``X = MLP(Z)`` with a 2-layer network:
      ``h = tanh(alpha * W1 @ Z)`` (per-sample; ``alpha =
      NONLINEAR_ACTIVATION_SCALE`` in ``(0, 1]`` controls how far tanh
      strays from linear; ``alpha = 0.5`` is a mild nonlinearity that
      keeps FastICA's linear-approximation model workable but is provably
      nonlinear beyond the linear-ICA class);
      ``X = W2 @ h``.
  ``W1, W2`` are square (``d_Z x d_Z``) Haar-orthogonal matrices via
  signed QR, drawn once per (seed, d_Z) and shared across every
  environment and trial for that (seed, d_Z). ``A_linear = W2 @ W1`` is
  the Jacobian of the MLP at ``Z = 0``; because tanh's derivative at 0 is
  1 and Amari is invariant to nonzero row/column scaling, the constant
  ``alpha`` factor drops out of the Amari calculation.
- Observation: for each ``E in {0, 1, ..., d_Z}`` we draw
  ``N / (d_Z + 1)`` samples of ``(X, E)``.

Algorithm (simplified interventional CRL).
------------------------------------------
Ahuja 2022 Theorem 4.4 says: given a set of single-node interventions on
each latent component, the mixing function ``f`` is identifiable up to
component-wise transformations. The full algorithm involves fitting an
inverse (e.g. via a normalising flow); the simplified witness here is:

1. Fit ``FastICA(n_components = d_Z)`` on ``X | E = e`` for every
   ``e in {0, 1, ..., d_Z}``. Call the recovered unmixing matrices
   ``W_hat[e] in R^{d_Z x d_Z}``.
2. For each intervention environment ``i in {1, ..., d_Z}``, identify
   which row of ``W_hat[i]`` corresponds to ``Z_i`` using the mean-shift
   heuristic: compute the per-component mean shift of ``W_hat[i] @ X_i``
   vs ``W_hat[i] @ X_0`` and pick the row with the largest absolute mean
   shift. That row is the ``i``-th row of ``W_aligned``.
3. Aggregate: after stacking the ``d_Z`` per-intervention rows into a
   ``d_Z x d_Z`` matrix ``W_aligned``, score by the Amari performance
   index of ``P = W_aligned @ A_linear`` (identical formula to
   instruments 8 and 9; ``P`` is a signed permutation iff ``W_aligned``
   recovers ``A_linear^{-1}`` up to permutation and sign).

Pooled control (no environment split).
--------------------------------------
As a control, we also compute the pooled-Amari: fit
``FastICA(n_components = d_Z)`` on the pooled ``X`` across all
environments (ignoring ``E``) and score ``Amari(W_pool @ A_linear)``.
Because Amari is invariant to permutation and sign, no alignment is
needed for the pooled control. The interventional-CRL claim is that
splitting by environment *helps* identifiability, so the environment-
split Amari should be smaller than the pooled control.

Sample-complexity sweep.
------------------------
``(d_Z, N_per_env) in {2, 3, 4} x {500, 1000, 2000, 5000, 10000}``.
(``d_Z = 4`` means 5 environments, 25k total samples at
``N_per_env = 5000``; keeps runtime bounded.) Each of the 15 grid
points is averaged over ``TRIALS = 4`` independent draws. Randomness is
derived from ``BASE_SEED = 0`` via
``np.random.SeedSequence([BASE_SEED, d_Z, trial])`` and sklearn's
``random_state = trial``, making the run fully deterministic.

Pre-registered gates (SIC-C-c interventional-CRL witness).
----------------------------------------------------------
- ``ICRL_CONVERGES_AT_LARGEST_N``: at ``N_per_env = N_PER_ENV_MAX``, the
  environment-consistency Amari averaged over trials is
  ``<= FINAL_AMARI_TARGET = 0.20`` for every ``d_Z``. (Looser than the
  linear/sparse-ICA / iVAE instruments because environment splitting is
  data-hungry, the alignment heuristic is imperfect, and the underlying
  mixing is nonlinear.)
- ``ICRL_ENVIRONMENT_SPLIT_HELPS``: at ``N_per_env = N_PER_ENV_MAX``, the
  environment-split Amari is strictly less than the pooled-control Amari
  (``split - pool < -SPLIT_HELPS_TOL``, with a small ``0.005`` tolerance
  so a numerical tie doesn't count as help) for every ``d_Z``.
- ``ICRL_MONOTONE_IN_N_AT_EVERY_D_Z``: for every ``d_Z`` the averaged
  environment-split Amari curve is nonincreasing in ``N_per_env`` modulo
  ``MONOTONE_TOL = 0.03`` (a wider wobble than instruments 8/9 because
  the intervention-shift alignment adds finite-sample noise).
- ``ICRL_POLYNOMIAL_IN_D_Z``: fit ``log(N_needed(d_Z)) = a + b log(d_Z)``
  with ``N_needed`` the smallest ``N_per_env`` in the sweep reaching
  averaged environment-split Amari ``<= POLY_AMARI_TARGET = 0.30``. Gate:
  ``b <= POLY_EXPONENT_MAX = 5.0`` (very generous; interventions do
  incur a real per-dimension cost because we run one FastICA fit per
  environment).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.decomposition import FastICA


BASE_SEED = 0
D_Z_VALUES: tuple[int, ...] = (2, 3, 4)
N_PER_ENV_VALUES: tuple[int, ...] = (500, 1000, 2000, 5000, 10000)
TRIALS = 4

# Interventional-CRL setup.
INTERVENTION_SIGMA = 0.5  # Laplace scale of the intervened Z_i (vs 1.0 obs).
INTERVENTION_MU_MIN = -2.0
INTERVENTION_MU_MAX = 2.0
NONLINEAR_ACTIVATION_SCALE = 0.5

# Gate thresholds (see docstring for rationale; realism-budget calibrated).
FINAL_AMARI_TARGET = 0.20
POLY_AMARI_TARGET = 0.30
POLY_EXPONENT_MAX = 5.0
MONOTONE_TOL = 0.03
SPLIT_HELPS_TOL = 0.005


def sample_orthogonal(d: int, rng: np.random.Generator) -> np.ndarray:
    """Random orthogonal ``d x d`` matrix via signed QR of a Gaussian.

    Identical to ``experiments/linear_ica_learnability/core.py``. The
    ``q * sign(diag(r))`` correction fixes QR's sign ambiguity so the
    output distribution is exactly Haar on ``O(d)``, keeping this call
    reproducible under a fixed ``rng``.
    """

    g = rng.standard_normal((d, d))
    q, r = np.linalg.qr(g)
    q = q * np.sign(np.diag(r))
    return q


def amari_index(matrix: np.ndarray) -> float:
    """Amari performance index of ``P = W_aligned @ A_linear``.

    ``amari(P)`` is in ``[0, 1]``: 0 iff ``P`` is a signed permutation
    (perfect recovery up to the identifiability class) and approaches 1
    as ``P`` becomes uniformly dense. Formula (identical to
    instruments 8 and 9):

        amari(P) = (1 / (2 * d * (d - 1))) * (
            sum_i (sum_j |P_ij| / max_j |P_ij| - 1)
            + sum_j (sum_i |P_ij| / max_i |P_ij| - 1)
        )
    """

    abs_p = np.abs(matrix)
    d = abs_p.shape[0]
    if d < 2:
        raise ValueError("Amari index is undefined for d < 2")
    row_max = abs_p.max(axis=1, keepdims=True)
    col_max = abs_p.max(axis=0, keepdims=True)
    row_scale = np.where(row_max == 0, 1.0, row_max)
    col_scale = np.where(col_max == 0, 1.0, col_max)
    row_term = (abs_p / row_scale).sum(axis=1) - 1.0
    col_term = (abs_p / col_scale).sum(axis=0) - 1.0
    return float((row_term.sum() + col_term.sum()) / (2 * d * (d - 1)))


def mlp_mixing(z: np.ndarray, w1: np.ndarray, w2: np.ndarray) -> np.ndarray:
    """Apply the 2-layer tanh mixing ``x = W2 @ tanh(alpha * W1 @ z)``.

    ``z`` has shape ``(n_samples, d_Z)`` and the returned ``x`` also has
    shape ``(n_samples, d_Z)`` (square mixing, ``d_out = d_Z``). Layer
    weights ``W1, W2`` are ``d_Z x d_Z``; the activation scale
    ``NONLINEAR_ACTIVATION_SCALE`` keeps tanh in a mildly nonlinear
    regime.
    """

    hidden = np.tanh(NONLINEAR_ACTIVATION_SCALE * z @ w1.T)
    return hidden @ w2.T


def sample_intervention_offsets(
    d_z: int, rng: np.random.Generator
) -> np.ndarray:
    """Draw per-component intervention means ``mu_i`` in ``[MIN, MAX]``."""

    return rng.uniform(INTERVENTION_MU_MIN, INTERVENTION_MU_MAX, size=d_z)


def sample_environment_latents(
    n_per_env: int,
    d_z: int,
    mus: np.ndarray,
    rng: np.random.Generator,
) -> tuple[list[np.ndarray], list[int]]:
    """Draw ``d_z + 1`` blocks of latent samples, one per environment.

    - Environment 0 is observational: every ``Z_j`` is ``Laplace(0, 1)``.
    - Environment ``i`` (for ``i in {1, ..., d_z}``) intervenes on
      ``Z_i``: ``Z_i`` is drawn as ``Laplace(mus[i - 1],
      INTERVENTION_SIGMA)`` and every other ``Z_j`` remains
      ``Laplace(0, 1)``.

    Returns a list of latent arrays (one per environment, in order
    ``E = 0, 1, ..., d_z``) and the matching list of environment labels
    (identical order); the size of each array is ``(n_per_env, d_z)``.
    """

    latents_by_env: list[np.ndarray] = []
    env_labels: list[int] = []

    obs = rng.laplace(0.0, 1.0, size=(n_per_env, d_z))
    latents_by_env.append(obs)
    env_labels.append(0)

    for i in range(d_z):
        z = rng.laplace(0.0, 1.0, size=(n_per_env, d_z))
        z[:, i] = rng.laplace(mus[i], INTERVENTION_SIGMA, size=n_per_env)
        latents_by_env.append(z)
        env_labels.append(i + 1)

    return latents_by_env, env_labels


def _fit_fastica(x: np.ndarray, d_z: int, trial: int) -> np.ndarray:
    """Wrap sklearn FastICA with the same knobs as instruments 8 and 9."""

    ica = FastICA(
        n_components=d_z,
        algorithm="parallel",
        whiten="unit-variance",
        fun="logcosh",
        max_iter=2000,
        tol=1e-6,
        random_state=trial,
    )
    ica.fit(x)
    return np.asarray(ica.components_)


def align_via_intervention_shift(
    w_hats: list[np.ndarray],
    xs: list[np.ndarray],
    d_z: int,
) -> np.ndarray:
    """Pick, for each intervention environment, the ``W_hat`` row whose mean
    shifts most between the observational and interventional data.

    ``w_hats[e]`` and ``xs[e]`` are the per-environment unmixing and data
    arrays for ``e in {0, 1, ..., d_z}`` (the observational entry is
    ``e = 0``); returns a stacked ``d_z x d_z`` matrix whose ``i``-th row
    is the mean-shift-max row of ``w_hats[i]`` (the ``i``-th intervention
    environment's unmixing, ``i = 1, ..., d_z``).
    """

    x_obs = xs[0]
    aligned = np.empty((d_z, d_z))
    for i in range(1, d_z + 1):
        w_i = w_hats[i]
        x_i = xs[i]
        obs_projections = x_obs @ w_i.T
        int_projections = x_i @ w_i.T
        shifts = np.abs(int_projections.mean(axis=0) - obs_projections.mean(axis=0))
        row_index = int(np.argmax(shifts))
        aligned[i - 1] = w_i[row_index]
    return aligned


def _trial_seed(d_z: int, trial: int) -> np.random.SeedSequence:
    """Deterministic (BASE_SEED, d_Z, trial)-keyed SeedSequence."""

    return np.random.SeedSequence([BASE_SEED, int(d_z), int(trial)])


def _run_trial(
    d_z: int, trial: int, n_per_env: int
) -> tuple[float, float]:
    """One trial at ``(d_z, trial, n_per_env)``: return (split_amari, pool_amari).

    All randomness is derived from the ``(BASE_SEED, d_z, trial)`` seed so
    that mixing weights, intervention offsets, and per-environment
    samples are byte-identical under repeated calls with the same
    triple; different ``n_per_env`` values at the same triple use the
    same underlying random stream (so smaller ``n_per_env`` samples are
    exactly the first ``n_per_env`` rows of the ``N_PER_ENV_MAX`` draw
    per environment).
    """

    rng = np.random.default_rng(_trial_seed(d_z, trial))
    w1 = sample_orthogonal(d_z, rng)
    w2 = sample_orthogonal(d_z, rng)
    a_linear = w2 @ w1

    mus = sample_intervention_offsets(d_z, rng)

    n_max = max(N_PER_ENV_VALUES)
    latents_by_env, _labels = sample_environment_latents(n_max, d_z, mus, rng)
    xs_full = [mlp_mixing(z, w1, w2) for z in latents_by_env]

    xs = [x[:n_per_env] for x in xs_full]

    # Environment-split: one FastICA per environment.
    w_hats = [_fit_fastica(x, d_z, trial) for x in xs]
    w_aligned = align_via_intervention_shift(w_hats, xs, d_z)
    split_amari = amari_index(w_aligned @ a_linear)

    # Pooled control: single FastICA on all environments together.
    x_pool = np.concatenate(xs, axis=0)
    w_pool = _fit_fastica(x_pool, d_z, trial)
    pool_amari = amari_index(w_pool @ a_linear)

    return split_amari, pool_amari


@dataclass(frozen=True)
class SweepPoint:
    d_z: int
    n_per_env: int
    split_amari_mean: float
    split_amari_trials: tuple[float, ...]
    pool_amari_mean: float
    pool_amari_trials: tuple[float, ...]


def sweep_amari() -> list[SweepPoint]:
    """Compute averaged split-Amari and pool-Amari at every grid point."""

    points: list[SweepPoint] = []
    for d_z in D_Z_VALUES:
        for n_per_env in N_PER_ENV_VALUES:
            splits: list[float] = []
            pools: list[float] = []
            for trial in range(TRIALS):
                split_amari, pool_amari = _run_trial(d_z, trial, n_per_env)
                splits.append(split_amari)
                pools.append(pool_amari)
            points.append(
                SweepPoint(
                    d_z=d_z,
                    n_per_env=n_per_env,
                    split_amari_mean=float(np.mean(splits)),
                    split_amari_trials=tuple(splits),
                    pool_amari_mean=float(np.mean(pools)),
                    pool_amari_trials=tuple(pools),
                )
            )
    return points


def smallest_n_reaching_target(
    points: list[SweepPoint], d_z: int, target: float
) -> int | None:
    """Smallest ``N_per_env`` with averaged split-Amari at ``d_z`` <= ``target``."""

    curve = sorted(
        (pt for pt in points if pt.d_z == d_z), key=lambda pt: pt.n_per_env
    )
    for pt in curve:
        if pt.split_amari_mean <= target:
            return pt.n_per_env
    return None


def polynomial_exponent(
    points: list[SweepPoint], target: float
) -> tuple[float, dict[int, int]]:
    """Fit ``log(N_needed(d_Z)) = a + b log(d_Z)``; return ``(b, {d_z: N_needed})``."""

    n_needed: dict[int, int] = {}
    for d_z in D_Z_VALUES:
        smallest = smallest_n_reaching_target(points, d_z, target)
        if smallest is None:
            raise ValueError(
                f"target amari {target} unreachable at d_z = {d_z} in swept N range"
            )
        n_needed[d_z] = smallest
    xs = np.log(np.array(sorted(n_needed.keys()), dtype=float))
    ys = np.log(np.array([n_needed[d] for d in sorted(n_needed.keys())], dtype=float))
    x_mean = xs.mean()
    y_mean = ys.mean()
    denom = float(((xs - x_mean) ** 2).sum())
    if denom == 0.0:
        return 0.0, n_needed
    slope = float(((xs - x_mean) * (ys - y_mean)).sum() / denom)
    return slope, n_needed


def is_monotone_within_tolerance(
    points: list[SweepPoint], d_z: int, tol: float
) -> bool:
    """Averaged split-Amari at ``d_z`` is nonincreasing in ``N_per_env`` modulo ``tol``."""

    curve = sorted(
        (pt for pt in points if pt.d_z == d_z), key=lambda pt: pt.n_per_env
    )
    values = [pt.split_amari_mean for pt in curve]
    return all(b <= a + tol for a, b in zip(values[:-1], values[1:], strict=True))


def evaluate_benchmark() -> dict:
    points = sweep_amari()
    indexed: dict[tuple[int, int], SweepPoint] = {
        (pt.d_z, pt.n_per_env): pt for pt in points
    }

    n_max = max(N_PER_ENV_VALUES)

    converges_at_largest_n = all(
        indexed[(d_z, n_max)].split_amari_mean <= FINAL_AMARI_TARGET
        for d_z in D_Z_VALUES
    )

    split_vs_pool_deltas: dict[int, float] = {}
    split_helps = True
    for d_z in D_Z_VALUES:
        pt = indexed[(d_z, n_max)]
        delta = pt.split_amari_mean - pt.pool_amari_mean
        split_vs_pool_deltas[d_z] = delta
        if delta >= -SPLIT_HELPS_TOL:
            split_helps = False

    monotone_gate = all(
        is_monotone_within_tolerance(points, d_z, MONOTONE_TOL)
        for d_z in D_Z_VALUES
    )

    slope, n_needed_poly = polynomial_exponent(points, POLY_AMARI_TARGET)
    poly_gate = slope <= POLY_EXPONENT_MAX

    gates = {
        "ICRL_CONVERGES_AT_LARGEST_N": bool(converges_at_largest_n),
        "ICRL_ENVIRONMENT_SPLIT_HELPS": bool(split_helps),
        "ICRL_MONOTONE_IN_N_AT_EVERY_D_Z": bool(monotone_gate),
        "ICRL_POLYNOMIAL_IN_D_Z": bool(poly_gate),
    }
    status = "pass" if all(gates.values()) else "fail"

    return {
        "status": status,
        "gates": gates,
        "base_seed": BASE_SEED,
        "trials_per_grid_point": TRIALS,
        "d_Z_values": list(D_Z_VALUES),
        "N_per_env_values": list(N_PER_ENV_VALUES),
        "intervention": {
            "sigma": INTERVENTION_SIGMA,
            "mu_min": INTERVENTION_MU_MIN,
            "mu_max": INTERVENTION_MU_MAX,
        },
        "nonlinear_activation_scale": NONLINEAR_ACTIVATION_SCALE,
        "amari_thresholds": {
            "final_amari_target": FINAL_AMARI_TARGET,
            "poly_amari_target": POLY_AMARI_TARGET,
            "split_helps_tol": SPLIT_HELPS_TOL,
        },
        "split_vs_pool_delta_at_N_max": {
            str(d_z): round(delta, 6) for d_z, delta in split_vs_pool_deltas.items()
        },
        "monotone_tolerance": MONOTONE_TOL,
        "poly_exponent_gate": {
            "target_amari": POLY_AMARI_TARGET,
            "N_needed_per_d_Z": {
                str(d): int(n) for d, n in n_needed_poly.items()
            },
            "fitted_exponent_b": round(slope, 6),
            "exponent_gate_max": POLY_EXPONENT_MAX,
        },
        "sweep_points": [
            {
                "d_z": pt.d_z,
                "n_per_env": pt.n_per_env,
                "split_amari_mean": round(pt.split_amari_mean, 6),
                "split_amari_trials": [round(v, 6) for v in pt.split_amari_trials],
                "pool_amari_mean": round(pt.pool_amari_mean, 6),
                "pool_amari_trials": [round(v, 6) for v in pt.pool_amari_trials],
            }
            for pt in points
        ],
    }
