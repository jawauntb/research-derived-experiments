from __future__ import annotations

import math
import unittest

from experiments.compiler_tomography_pair.core import (
    BETA_VALUES,
    N_STEPS,
    N_VALUES,
    THETA_GRID,
    TRUE_THETA,
    all_worlds,
    concern_kernel,
    ecology_step,
    evaluate_benchmark,
    evaluate_ct1,
    evaluate_ct2,
    fiber_expected_reward,
    fiber_of,
    latent_z,
    mdl_recover,
    mdl_score,
    reward,
    sample_pairs,
    uniform_kernel,
)


class CompilerTomographyPairTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_theta_grid_contains_true_theta(self) -> None:
        self.assertIn(TRUE_THETA, THETA_GRID)

    def test_uniform_kernel_sums_to_one_on_every_fiber(self) -> None:
        worlds = all_worlds()
        k = uniform_kernel(worlds)
        for z, probs in k.items():
            self.assertAlmostEqual(sum(probs.values()), 1.0, places=12)
            self.assertEqual(len(probs), 4)  # 4-bit world has 4-element fibers

    def test_concern_kernel_matches_true_at_zero_theta(self) -> None:
        worlds = all_worlds()
        base = uniform_kernel(worlds)
        tilted = concern_kernel(base, (0.0, 0.0))
        for z in base:
            for w in base[z]:
                self.assertAlmostEqual(tilted[z][w], base[z][w], places=12)

    def test_sample_pairs_returns_correct_count(self) -> None:
        worlds = all_worlds()
        base = uniform_kernel(worlds)
        pairs = sample_pairs(base, n_pairs=100, seed=42)
        self.assertEqual(len(pairs), 100)
        for s, x in pairs:
            self.assertEqual(latent_z(x), s)

    def test_mdl_recovers_theta_at_large_N(self) -> None:
        worlds = all_worlds()
        base = uniform_kernel(worlds)
        true_kernel = concern_kernel(base, TRUE_THETA)
        pairs = sample_pairs(true_kernel, n_pairs=2000, seed=7)
        theta_hat = mdl_recover(pairs)
        self.assertEqual(theta_hat, TRUE_THETA)

    def test_ct1_recovery_curve_ends_above_target(self) -> None:
        ct1 = evaluate_ct1()
        self.assertTrue(ct1["largest_N_recovery_meets_target"])
        self.assertGreaterEqual(ct1["per_N"][-1]["recovery_rate"], 0.95)

    def test_ecology_step_preserves_normalisation(self) -> None:
        worlds = all_worlds()
        k = uniform_kernel(worlds)
        for beta in BETA_VALUES:
            k = ecology_step(k, beta)
            for z, probs in k.items():
                self.assertAlmostEqual(sum(probs.values()), 1.0, places=12)

    def test_ecology_reward_monotone_at_every_beta(self) -> None:
        ct2 = evaluate_ct2()
        self.assertTrue(ct2["monotone_at_every_beta"])

    def test_large_beta_converges_to_argmax(self) -> None:
        # At beta = 4, T = 20 steps should get within 0.05 of the fiber argmax.
        worlds = all_worlds()
        k = uniform_kernel(worlds)
        for _ in range(N_STEPS):
            k = ecology_step(k, 4.0)
        for z in k:
            reward_here = fiber_expected_reward(k, z)
            max_here = max(reward(w) for w in fiber_of(worlds, z))
            self.assertLess(abs(reward_here - max_here), 0.05)

    def test_mdl_score_is_log2_neg_log_lik_plus_description(self) -> None:
        worlds = all_worlds()
        base = uniform_kernel(worlds)
        k = concern_kernel(base, (0.5, -0.5))
        pairs = [((0, 0), worlds[0])]  # single pair
        expected = math.log2(25) + (-math.log2(max(k[(0, 0)].get(worlds[0], 1e-300), 1e-300)))
        self.assertAlmostEqual(mdl_score(pairs, k, math.log2(25)), expected, places=12)

    def test_n_values_are_pre_registered(self) -> None:
        self.assertEqual(list(N_VALUES), [50, 100, 200, 500, 1000, 2000])


if __name__ == "__main__":
    unittest.main()
