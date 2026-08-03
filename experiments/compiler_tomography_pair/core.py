"""Exact witness of Theorems CT-1 (MDL identification) and CT-2 (ecology
monotone reward) from the companion paper *Compiler Tomography*
(``papers/compiler_tomography/paper.md``).

Setup (matches paper section 4, 4-bit Boolean world of Instrument 4):

- ``S`` = 4 specification classes = ``Z``, with ``q(x) = (x_0 XOR x_1, x_2 XOR x_3)``.
- ``X`` = 16 realizations = ``{0, 1}^4``.
- Base compiler ``K*(x | s)`` is uniform on the 4-element fiber ``q^{-1}(s)``.
- Hypothesis family (for CT-1): concern-parameterised compilers
  ``K_theta(x | s) proportional to K*(x | s) * exp(theta_1 T_1(x) + theta_2 T_2(x))``,
  where ``T(x) = (2 x_0 - 1, 2 x_2 - 1) in {-1, +1}^2``. Grid
  ``theta in {-1, -0.5, 0, 0.5, 1}^2`` = 25 candidates; true ``theta* = (0, 0)``.
- Reward for CT-2: ``r(x) = x_0 + x_2 in {0, 1, 2}``.

CT-1: exact simulation. For each ``N in {50, 100, 200, 500, 1000, 2000}``
draw N (s, x) pairs with s uniform on S (deterministic seeded PRNG), then
compute the MDL score for every grid candidate and pick the argmin. Repeat
for 100 seeds; report recovery rate ``Pr[theta_hat = theta*]``.

CT-2: exact iteration. Starting from K_0 = K* on every fiber, apply the
Boltzmann update K_{t+1}(x|s) proportional to K_t(x|s) * exp(beta * r(x))
for 20 steps at beta in {0.1, 1.0, 4.0}, and verify per-fiber expected
reward is non-decreasing.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from itertools import product

World = tuple[int, int, int, int]


def all_worlds() -> list[World]:
    return [(b0, b1, b2, b3) for b0, b1, b2, b3 in product((0, 1), repeat=4)]


def latent_z(w: World) -> tuple[int, int]:
    return (w[0] ^ w[1], w[2] ^ w[3])


def concern_stat(w: World) -> tuple[int, int]:
    return (2 * w[0] - 1, 2 * w[2] - 1)


def fiber_of(worlds: Sequence[World], z: tuple[int, int]) -> list[World]:
    return [w for w in worlds if latent_z(w) == z]


def uniform_kernel(worlds: Sequence[World]) -> dict[tuple[int, int], dict[World, float]]:
    """K*(x | s) = uniform on q^{-1}(s)."""

    out: dict[tuple[int, int], dict[World, float]] = {}
    for z in {latent_z(w) for w in worlds}:
        fiber = fiber_of(worlds, z)
        p = 1.0 / len(fiber)
        out[z] = {w: p for w in fiber}
    return out


def concern_kernel(
    base: dict[tuple[int, int], dict[World, float]], theta: tuple[float, float]
) -> dict[tuple[int, int], dict[World, float]]:
    out = {}
    for z, base_probs in base.items():
        weights = {}
        for w, p_base in base_probs.items():
            t = concern_stat(w)
            weights[w] = p_base * math.exp(theta[0] * t[0] + theta[1] * t[1])
        total = sum(weights.values())
        out[z] = {w: v / total for w, v in weights.items()}
    return out


# -------- deterministic seeded PRNG (Mulberry32) --------


def _mulberry32(seed: int) -> Callable[[], float]:
    state = [seed & 0xFFFFFFFF]

    def rng() -> float:
        state[0] = (state[0] + 0x6D2B79F5) & 0xFFFFFFFF
        t = state[0]
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0

    return rng


def sample_pairs(
    kernel: dict[tuple[int, int], dict[World, float]],
    n_pairs: int,
    seed: int,
) -> list[tuple[tuple[int, int], World]]:
    """Draw N i.i.d. (s, x) pairs with s uniform on {q^-1 keys} and x ~ K(.|s)."""

    rng = _mulberry32(seed)
    ss = sorted(kernel.keys())
    pairs = []
    for _ in range(n_pairs):
        u = rng()
        s_idx = min(int(u * len(ss)), len(ss) - 1)
        s = ss[s_idx]
        # Now draw x from K(.|s) via inverse CDF.
        v = rng()
        cum = 0.0
        chosen = None
        for w, p in kernel[s].items():
            cum += p
            if v <= cum:
                chosen = w
                break
        if chosen is None:
            chosen = list(kernel[s].keys())[-1]
        pairs.append((s, chosen))
    return pairs


# -------- CT-1: MDL identification --------


THETA_GRID: tuple[tuple[float, float], ...] = tuple(
    (t1, t2)
    for t1 in (-1.0, -0.5, 0.0, 0.5, 1.0)
    for t2 in (-1.0, -0.5, 0.0, 0.5, 1.0)
)
TRUE_THETA: tuple[float, float] = (0.0, 0.0)
N_VALUES: tuple[int, ...] = (50, 100, 200, 500, 1000, 2000)
N_SEEDS: int = 100


def mdl_score(
    pairs: Sequence[tuple[tuple[int, int], World]],
    kernel: dict[tuple[int, int], dict[World, float]],
    description_bits: float,
) -> float:
    """MDL = L(theta) + L(data | K_theta), in bits.

    L(data | K_theta) = -sum_i log2 K_theta(x_i | s_i). We add a tiny
    epsilon guard against log(0), but in practice base_prob > 0 always
    (the reweight is a positive scalar times a positive base).
    """

    neg_ll = 0.0
    for s, x in pairs:
        p = kernel[s].get(x, 1e-300)
        neg_ll += -math.log2(max(p, 1e-300))
    return description_bits + neg_ll


def mdl_recover(
    pairs: Sequence[tuple[tuple[int, int], World]],
) -> tuple[float, float]:
    """MDL argmin over THETA_GRID, uniform prior (description = log2(25))."""

    worlds = all_worlds()
    base = uniform_kernel(worlds)
    description_bits = math.log2(len(THETA_GRID))
    best_score = math.inf
    best_theta = THETA_GRID[0]
    for theta in THETA_GRID:
        k = concern_kernel(base, theta)
        s = mdl_score(pairs, k, description_bits)
        if s < best_score:
            best_score = s
            best_theta = theta
    return best_theta


def evaluate_ct1() -> dict:
    worlds = all_worlds()
    base = uniform_kernel(worlds)
    true_kernel = concern_kernel(base, TRUE_THETA)
    per_n = []
    for n in N_VALUES:
        n_recover = 0
        for seed in range(N_SEEDS):
            pairs = sample_pairs(true_kernel, n, seed=seed + 1)
            theta_hat = mdl_recover(pairs)
            if theta_hat == TRUE_THETA:
                n_recover += 1
        rate = n_recover / N_SEEDS
        per_n.append(
            {
                "N": n,
                "recovery_rate": rate,
                "n_seeds": N_SEEDS,
                "meets_0p95": rate >= 0.95,
            }
        )
    # At the largest N, insist recovery >= 0.95. At the smallest N, expect
    # recovery is not yet at 1 (the estimator is only asymptotically
    # consistent) — but recovery should still be monotone across N.
    largest_meets = per_n[-1]["meets_0p95"]
    monotone = all(
        p1["recovery_rate"] <= p2["recovery_rate"] + 0.15
        for p1, p2 in zip(per_n, per_n[1:])
    )
    return {
        "per_N": per_n,
        "largest_N_recovery_meets_target": largest_meets,
        "recovery_rate_broadly_monotone": monotone,
        "N_grid": list(N_VALUES),
        "n_theta_candidates": len(THETA_GRID),
    }


# -------- CT-2: ecology monotone-reward --------


def reward(w: World) -> float:
    return float(w[0] + w[2])


BETA_VALUES: tuple[float, ...] = (0.1, 1.0, 4.0)
N_STEPS: int = 20


def ecology_step(
    kernel: dict[tuple[int, int], dict[World, float]], beta: float
) -> dict[tuple[int, int], dict[World, float]]:
    out = {}
    for z, probs in kernel.items():
        weighted = {w: p * math.exp(beta * reward(w)) for w, p in probs.items()}
        total = sum(weighted.values())
        out[z] = {w: v / total for w, v in weighted.items()}
    return out


def fiber_expected_reward(
    kernel: dict[tuple[int, int], dict[World, float]], z: tuple[int, int]
) -> float:
    return sum(p * reward(w) for w, p in kernel[z].items())


def evaluate_ct2() -> dict:
    worlds = all_worlds()
    base = uniform_kernel(worlds)
    per_beta = []
    for beta in BETA_VALUES:
        k = base
        # Store trajectory as parallel lists (typed) to keep ty happy.
        trajectory_rewards: list[dict[str, float]] = []
        monotone_at_all_z = True
        for t in range(N_STEPS + 1):
            per_fiber: dict[str, float] = {
                f"z{z[0]}{z[1]}": round(fiber_expected_reward(k, z), 6)
                for z in sorted(k.keys())
            }
            trajectory_rewards.append(per_fiber)
            if t > 0:
                prev_fibers = trajectory_rewards[-2]
                curr_fibers = trajectory_rewards[-1]
                for z in sorted(k.keys()):
                    key = f"z{z[0]}{z[1]}"
                    if curr_fibers[key] < prev_fibers[key] - 1e-12:
                        monotone_at_all_z = False
            k = ecology_step(k, beta)
        final_fiber_reward: dict[str, float] = trajectory_rewards[-1]
        max_fiber_reward: dict[str, float] = {
            f"z{z[0]}{z[1]}": max(reward(w) for w in fiber_of(worlds, z))
            for z in sorted(base.keys())
        }
        converged_to_argmax_at_large_beta = beta >= 3.0 and all(
            abs(final_fiber_reward[k_name] - max_fiber_reward[k_name]) < 0.05
            for k_name in max_fiber_reward
        )
        per_beta.append(
            {
                "beta": beta,
                "monotone_at_all_z": monotone_at_all_z,
                "final_expected_reward": final_fiber_reward,
                "max_possible_reward_per_fiber": max_fiber_reward,
                "converged_to_argmax_if_large_beta": (
                    converged_to_argmax_at_large_beta if beta >= 3.0 else None
                ),
                "trajectory": [
                    {"t": i, "expected_reward_per_fiber": row}
                    for i, row in enumerate(trajectory_rewards)
                ],
            }
        )
    all_monotone = all(entry["monotone_at_all_z"] for entry in per_beta)
    large_beta_converged = all(
        entry["converged_to_argmax_if_large_beta"] is not False for entry in per_beta
    )
    return {
        "per_beta": per_beta,
        "monotone_at_every_beta": all_monotone,
        "large_beta_converges_to_argmax": large_beta_converged,
        "beta_grid": list(BETA_VALUES),
        "n_steps": N_STEPS,
    }


def evaluate_benchmark() -> dict:
    ct1 = evaluate_ct1()
    ct2 = evaluate_ct2()
    gates = {
        "ct1_largest_N_recovers_true_theta_at_0p95": ct1[
            "largest_N_recovery_meets_target"
        ],
        "ct1_recovery_broadly_monotone_in_N": ct1["recovery_rate_broadly_monotone"],
        "ct2_expected_reward_monotone_at_every_beta": ct2["monotone_at_every_beta"],
        "ct2_large_beta_converges_to_fiber_argmax": ct2[
            "large_beta_converges_to_argmax"
        ],
    }
    status = "pass" if all(gates.values()) else "fail"
    return {
        "status": status,
        "gates": gates,
        "ct1": ct1,
        "ct2": ct2,
    }
