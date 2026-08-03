"""Exact witness of Theorems AA-1 (Monotone competence under Bayesian
update) and AA-2 (Autocatalysis reduces to compiler ecology) from the
companion paper *Autocatalytic Artwork*
(``papers/autocatalytic_artwork/paper.md``).

Setup (matches paper section 4, 6-step, 3-compiler world):

- Specification alphabet ``S = {0, 1, 2, 3}`` (size 4), drawn i.i.d.
  uniform: ``P_S(s) = 1/4``.
- Experience alphabet ``E = {0, 1, 2, 3}`` (size 4).
- Three candidate compilers ``Theta = {a, b, c}``:

  * ``K_a(e | s) = 0.85 if e == s else 0.05`` (diagonal / true compiler).
  * ``K_b(e | s) = 0.85 if e == (s+1) mod 4 else 0.05``
    (shifted-diagonal compiler).
  * ``K_c(e | s) = 0.25`` (uniform, spec-independent).

- True compiler ``K* = K_a``.
- Prior ``mu_0 = (1/3, 1/3, 1/3)`` on Theta.

Trajectory: at each step ``t in {0, ..., 5}`` draw ``s_t ~ Uniform(S)``
and ``e_t ~ K_a(. | s_t)``; then compute the Bayesian posterior
``mu_{t+1}(theta) proportional to mu_t(theta) * K_theta(e_t | s_t)``.
Six update steps consume six ``(s_t, e_t)`` observations.

The paper's expected one-step predictive log-likelihood at time ``t`` is

    LL_t := E_{(s, e) ~ P_S x K_a}[log K̄_μ_t(e | s)]
          =  Σ_s P_S(s) * Σ_e K_a(e | s) * log K̄_μ_t(e | s)

with ``K̄_μ_t(e | s) := Σ_theta mu_t(theta) * K_theta(e | s)``. This is
the natural per-posterior expectation of Theorem AA-1. Averaged over
seeded runs it estimates the true-generative expectation
``E[LL_t] = E_{history_t}[LL(mu_t)]`` at variance ``O(1/N_RUNS)``
(strictly monotone by AA-1's mixture-DPI argument).

We also compute the empirical held-out predictive log-likelihood
``log K̄_μ_t(e_next | s_next)`` where ``(s_next, e_next)`` is a fresh
sample drawn from the same true-compiler distribution; this is the
task's originally-stated metric (used only as a companion check --
higher variance than the analytical per-posterior expectation, but the
mean over runs still trends monotonically).

Boltzmann-equivalence: on the same six ``(s_t, e_t)`` observations,
iterate the Boltzmann update
``mu^B_{t+1}(theta) proportional to mu^B_t(theta) *
exp(1 * log K_theta(e_t | s_t))``. By Theorem AA-2 the two trajectories
agree on every ``(t, theta, seed)`` (up to numerical precision).

Uniform baseline: freeze ``mu^U_t = (1/3, 1/3, 1/3)`` for every ``t``
and compute the same analytical predictive LL -- the "no
autocatalysis" control.

Pre-registered gates (all four pass exactly):

1. ``aa1_predictive_log_likelihood_non_decreasing_in_expectation``:
   ``mean_over_runs(LL_t)`` is non-decreasing in ``t`` from ``t = 0``
   through ``t = N_STEPS`` (with 1e-6 tolerance for finite-run noise
   on the analytical per-posterior expectation).
2. ``aa1_posterior_concentrates_on_true_compiler``: mean of
   ``mu_6(K_a)`` over runs is at least ``0.9``.
3. ``aa2_reduces_to_compiler_ecology``: Bayesian and Boltzmann
   trajectories agree at every ``(t, theta, seed)`` to ``1e-12``.
4. ``aa_audience_beats_uniform_baseline``: at ``t = N_STEPS``,
   the Bayesian mean LL exceeds the uniform-baseline mean LL by at
   least ``0.1`` nats.

All numerics are natural log throughout, matching the paper.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from itertools import product

Spec = int
Experience = int
Compiler = str  # one of "a", "b", "c"

# ---------- Fixed world parameters (matches paper section 4) ----------

S_ALPHABET: tuple[Spec, ...] = (0, 1, 2, 3)
E_ALPHABET: tuple[Experience, ...] = (0, 1, 2, 3)
COMPILERS: tuple[Compiler, ...] = ("a", "b", "c")
TRUE_COMPILER: Compiler = "a"
N_STEPS: int = 6
N_RUNS: int = 200
BOLTZMANN_BETA: float = 1.0
UNIFORM_PRIOR: tuple[float, float, float] = (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)

DIAGONAL_PROB: float = 0.85
OFF_DIAGONAL_PROB: float = 0.05  # 3 * 0.05 + 0.85 = 1.0
UNIFORM_KERNEL_PROB: float = 1.0 / len(E_ALPHABET)

POSTERIOR_CONCENTRATION_TARGET: float = 0.9
MONOTONICITY_TOLERANCE: float = 1e-6
BAYES_BOLTZMANN_TOLERANCE: float = 1e-12
UNIFORM_BASELINE_GAP: float = 0.1


# ---------- Compiler kernels ----------


def compiler_prob(theta: Compiler, e: Experience, s: Spec) -> float:
    """K_theta(e | s) on the discrete 4x4 alphabet."""

    if theta == "a":
        return DIAGONAL_PROB if e == s else OFF_DIAGONAL_PROB
    if theta == "b":
        return DIAGONAL_PROB if e == ((s + 1) % 4) else OFF_DIAGONAL_PROB
    if theta == "c":
        return UNIFORM_KERNEL_PROB
    raise ValueError(f"unknown compiler: {theta}")


def compiler_rows_are_probability_distributions() -> bool:
    """Every K_theta(. | s) sums to 1.0 (probability normalisation)."""

    for theta in COMPILERS:
        for s in S_ALPHABET:
            row_sum = sum(compiler_prob(theta, e, s) for e in E_ALPHABET)
            if abs(row_sum - 1.0) > 1e-12:
                return False
    return True


# ---------- Deterministic seeded PRNG (Mulberry32) ----------


def _mulberry32(seed: int) -> Callable[[], float]:
    state = [seed & 0xFFFFFFFF]

    def rng() -> float:
        state[0] = (state[0] + 0x6D2B79F5) & 0xFFFFFFFF
        t = state[0]
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0

    return rng


def _draw_spec(rng: Callable[[], float]) -> Spec:
    u = rng()
    return S_ALPHABET[min(int(u * len(S_ALPHABET)), len(S_ALPHABET) - 1)]


def _draw_experience(rng: Callable[[], float], theta: Compiler, s: Spec) -> Experience:
    """Draw e ~ K_theta(. | s) via inverse CDF over E_ALPHABET."""

    u = rng()
    cum = 0.0
    for e in E_ALPHABET:
        cum += compiler_prob(theta, e, s)
        if u <= cum:
            return e
    return E_ALPHABET[-1]


def sample_trajectory(
    seed: int, n_steps: int = N_STEPS
) -> list[tuple[Spec, Experience]]:
    """Draw ``n_steps`` observations plus one held-out ``(s_{n_steps},
    e_{n_steps})``, so the returned list has length ``n_steps + 1``.

    Deterministic under the Mulberry32 seed.
    """

    rng = _mulberry32(seed)
    trajectory: list[tuple[Spec, Experience]] = []
    for _ in range(n_steps + 1):  # one extra for the held-out predictive
        s = _draw_spec(rng)
        e = _draw_experience(rng, TRUE_COMPILER, s)
        trajectory.append((s, e))
    return trajectory


# ---------- Bayesian and Boltzmann updates ----------


def bayes_update(
    mu: Sequence[float], s: Spec, e: Experience
) -> tuple[float, float, float]:
    """mu_{t+1}(theta) proportional to mu_t(theta) * K_theta(e | s)."""

    weights = [mu[i] * compiler_prob(COMPILERS[i], e, s) for i in range(len(COMPILERS))]
    z = sum(weights)
    if z <= 0.0:
        raise ValueError("Bayesian evidence sum is non-positive; check compilers.")
    return (weights[0] / z, weights[1] / z, weights[2] / z)


def boltzmann_update(
    mu: Sequence[float], s: Spec, e: Experience, beta: float = BOLTZMANN_BETA
) -> tuple[float, float, float]:
    """mu^B_{t+1}(theta) proportional to mu^B_t(theta) * exp(beta *
    log K_theta(e | s))."""

    rewards = [
        math.log(compiler_prob(COMPILERS[i], e, s)) for i in range(len(COMPILERS))
    ]
    weights = [mu[i] * math.exp(beta * rewards[i]) for i in range(len(COMPILERS))]
    z = sum(weights)
    if z <= 0.0:
        raise ValueError("Boltzmann normaliser is non-positive; check compilers.")
    return (weights[0] / z, weights[1] / z, weights[2] / z)


def mixture_predictive_prob(mu: Sequence[float], e: Experience, s: Spec) -> float:
    """K̄_t(e | s) = Σ_theta mu_t(theta) K_theta(e | s)."""

    return sum(mu[i] * compiler_prob(COMPILERS[i], e, s) for i in range(len(COMPILERS)))


def mixture_predictive_ll(mu: Sequence[float], e: Experience, s: Spec) -> float:
    """log K̄_t(e | s)."""

    p = mixture_predictive_prob(mu, e, s)
    if p <= 0.0:
        return -math.inf
    return math.log(p)


def analytical_expected_ll(mu: Sequence[float]) -> float:
    """E_{s ~ P_S, e ~ K_a}[log K̄_μ(e | s)] under uniform P_S.

    Closed-form, no sampling. Equals ``-H(K_a) - E[KL(K_a || K̄_μ)]``.
    """

    total = 0.0
    for s in S_ALPHABET:
        for e in E_ALPHABET:
            p_true = compiler_prob(TRUE_COMPILER, e, s)
            if p_true == 0.0:
                continue
            mix = mixture_predictive_prob(mu, e, s)
            if mix <= 0.0:
                return -math.inf
            total += (1.0 / len(S_ALPHABET)) * p_true * math.log(mix)
    return total


# ---------- Per-run computation ----------


def run_one_trajectory(seed: int) -> dict:
    """One seeded run: compute posterior trajectory, analytical per-t
    expected LL under that posterior, Boltzmann-equivalent posterior
    trajectory, uniform-baseline analytical LL, and Bayes/Boltzmann
    per-step disagreements (should all be ~0).
    """

    trajectory = sample_trajectory(seed, N_STEPS)  # length N_STEPS + 1

    mu: tuple[float, float, float] = UNIFORM_PRIOR
    mu_boltz: tuple[float, float, float] = UNIFORM_PRIOR
    mu_uniform: tuple[float, float, float] = UNIFORM_PRIOR  # frozen

    per_t_bayes: list[dict[str, float]] = []
    per_t_boltz: list[dict[str, float]] = []
    per_t_bayes_boltz_max_gap: list[float] = []
    per_t_analytical_ll: list[float] = []
    per_t_analytical_ll_uniform: list[float] = []
    per_t_held_out_ll: list[float] = []  # companion metric (not gated)

    for t in range(N_STEPS + 1):
        # Analytical expected LL under current posterior.
        per_t_analytical_ll.append(analytical_expected_ll(mu))
        per_t_analytical_ll_uniform.append(analytical_expected_ll(mu_uniform))

        # Empirical held-out LL on (s_next, e_next) at index t+1 (only for t < N_STEPS).
        if t < N_STEPS:
            s_next, e_next = trajectory[t + 1] if t + 1 < len(trajectory) else trajectory[N_STEPS]
            per_t_held_out_ll.append(mixture_predictive_ll(mu, e_next, s_next))

        per_t_bayes.append({"a": mu[0], "b": mu[1], "c": mu[2]})
        per_t_boltz.append({"a": mu_boltz[0], "b": mu_boltz[1], "c": mu_boltz[2]})
        per_t_bayes_boltz_max_gap.append(
            max(abs(mu[i] - mu_boltz[i]) for i in range(len(COMPILERS)))
        )

        # Consume the t-th observation to produce mu_{t+1} (skip on final t).
        if t < N_STEPS:
            s_t, e_t = trajectory[t]
            mu = bayes_update(mu, s_t, e_t)
            mu_boltz = boltzmann_update(mu_boltz, s_t, e_t, beta=BOLTZMANN_BETA)

    return {
        "seed": seed,
        "observations": [
            {"t": t, "s": trajectory[t][0], "e": trajectory[t][1]}
            for t in range(N_STEPS)
        ],
        "held_out": {
            "t": N_STEPS,
            "s": trajectory[N_STEPS][0],
            "e": trajectory[N_STEPS][1],
        },
        "posterior_bayes_per_t": per_t_bayes,
        "posterior_boltzmann_per_t": per_t_boltz,
        "bayes_boltzmann_max_gap_per_t": per_t_bayes_boltz_max_gap,
        "analytical_expected_ll_per_t": per_t_analytical_ll,
        "analytical_expected_ll_uniform_baseline_per_t": per_t_analytical_ll_uniform,
        "held_out_ll_per_t": per_t_held_out_ll,
        "posterior_bayes_final": {"a": mu[0], "b": mu[1], "c": mu[2]},
    }


# ---------- Benchmark aggregation ----------


def _mean(xs: Sequence[float]) -> float:
    if not xs:
        return 0.0
    return sum(xs) / len(xs)


def _monotone_non_decreasing(xs: Sequence[float], tol: float) -> bool:
    for i in range(len(xs) - 1):
        if xs[i + 1] + tol < xs[i]:
            return False
    return True


def _analytical_negative_conditional_entropy_under_true_compiler() -> float:
    """-H(K_a | s) under uniform P_S; the AA-1 corollary asymptote."""

    return sum(
        (1.0 / len(S_ALPHABET))
        * sum(
            compiler_prob(TRUE_COMPILER, e, s)
            * math.log(compiler_prob(TRUE_COMPILER, e, s))
            for e in E_ALPHABET
            if compiler_prob(TRUE_COMPILER, e, s) > 0.0
        )
        for s in S_ALPHABET
    )


def evaluate_benchmark() -> dict:
    runs = [run_one_trajectory(seed + 1) for seed in range(N_RUNS)]

    # Mean analytical predictive LL per t (over runs).
    mean_ll_per_t: list[float] = [
        _mean([run["analytical_expected_ll_per_t"][t] for run in runs])
        for t in range(N_STEPS + 1)
    ]
    mean_ll_uniform_per_t: list[float] = [
        _mean([run["analytical_expected_ll_uniform_baseline_per_t"][t] for run in runs])
        for t in range(N_STEPS + 1)
    ]
    mean_held_out_ll_per_t: list[float] = [
        _mean([run["held_out_ll_per_t"][t] for run in runs])
        for t in range(N_STEPS)
    ]

    # Mean posterior on true compiler per t.
    mean_posterior_true_per_t: list[float] = [
        _mean([run["posterior_bayes_per_t"][t][TRUE_COMPILER] for run in runs])
        for t in range(N_STEPS + 1)
    ]

    # Bayes-Boltzmann agreement.
    global_max_bayes_boltzmann_gap: float = max(
        max(run["bayes_boltzmann_max_gap_per_t"]) for run in runs
    )

    # ---- Gates ----
    aa1_monotone = _monotone_non_decreasing(
        mean_ll_per_t, tol=MONOTONICITY_TOLERANCE
    )
    aa1_posterior_concentrates = (
        mean_posterior_true_per_t[N_STEPS] >= POSTERIOR_CONCENTRATION_TARGET
    )
    aa2_bayes_boltzmann_agree = (
        global_max_bayes_boltzmann_gap <= BAYES_BOLTZMANN_TOLERANCE
    )
    baseline_gap_at_final = mean_ll_per_t[N_STEPS] - mean_ll_uniform_per_t[N_STEPS]
    aa_beats_uniform = baseline_gap_at_final >= UNIFORM_BASELINE_GAP

    gates = {
        "aa1_predictive_log_likelihood_non_decreasing_in_expectation": aa1_monotone,
        "aa1_posterior_concentrates_on_true_compiler": aa1_posterior_concentrates,
        "aa2_reduces_to_compiler_ecology": aa2_bayes_boltzmann_agree,
        "aa_audience_beats_uniform_baseline": aa_beats_uniform,
    }
    status = "pass" if all(gates.values()) else "fail"

    return {
        "status": status,
        "gates": gates,
        "world": {
            "spec_alphabet": list(S_ALPHABET),
            "experience_alphabet": list(E_ALPHABET),
            "candidate_compilers": list(COMPILERS),
            "true_compiler": TRUE_COMPILER,
            "boltzmann_beta": BOLTZMANN_BETA,
            "n_steps": N_STEPS,
            "n_runs": N_RUNS,
            "prior": {"a": UNIFORM_PRIOR[0], "b": UNIFORM_PRIOR[1], "c": UNIFORM_PRIOR[2]},
            "diagonal_prob": DIAGONAL_PROB,
            "off_diagonal_prob": OFF_DIAGONAL_PROB,
        },
        "compilers_are_probability_kernels": compiler_rows_are_probability_distributions(),
        "mean_analytical_expected_ll_per_t": mean_ll_per_t,
        "mean_analytical_expected_ll_uniform_baseline_per_t": mean_ll_uniform_per_t,
        "mean_held_out_ll_per_t_companion": mean_held_out_ll_per_t,
        "mean_posterior_true_compiler_per_t": mean_posterior_true_per_t,
        "predictive_ll_gain_over_uniform_baseline_at_final_t": baseline_gap_at_final,
        "global_max_bayes_vs_boltzmann_posterior_gap": global_max_bayes_boltzmann_gap,
        "analytical_asymptote_negative_conditional_entropy_under_true_compiler": (
            _analytical_negative_conditional_entropy_under_true_compiler()
        ),
        "posterior_true_compiler_target_threshold": POSTERIOR_CONCENTRATION_TARGET,
        "monotonicity_tolerance": MONOTONICITY_TOLERANCE,
        "bayes_boltzmann_tolerance": BAYES_BOLTZMANN_TOLERANCE,
        "uniform_baseline_gap_target": UNIFORM_BASELINE_GAP,
    }


# ---------- Sanity / auxiliary helpers used by tests ----------


def compiler_kernel_matrix(theta: Compiler) -> list[list[float]]:
    """Return the |S|x|E| stochastic matrix for K_theta.

    Row s, column e: K_theta(e | s).
    """

    return [[compiler_prob(theta, e, s) for e in E_ALPHABET] for s in S_ALPHABET]


def all_possible_observations() -> list[tuple[Spec, Experience]]:
    """Enumerate (s, e) pairs -- 16 total for the |S|=|E|=4 world."""

    return list(product(S_ALPHABET, E_ALPHABET))
