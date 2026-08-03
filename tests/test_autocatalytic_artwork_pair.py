from __future__ import annotations

import math
import unittest

from experiments.autocatalytic_artwork_pair.core import (
    BAYES_BOLTZMANN_TOLERANCE,
    BOLTZMANN_BETA,
    COMPILERS,
    DIAGONAL_PROB,
    E_ALPHABET,
    MONOTONICITY_TOLERANCE,
    N_RUNS,
    N_STEPS,
    OFF_DIAGONAL_PROB,
    POSTERIOR_CONCENTRATION_TARGET,
    S_ALPHABET,
    TRUE_COMPILER,
    UNIFORM_BASELINE_GAP,
    UNIFORM_PRIOR,
    analytical_expected_ll,
    bayes_update,
    boltzmann_update,
    compiler_kernel_matrix,
    compiler_prob,
    compiler_rows_are_probability_distributions,
    evaluate_benchmark,
    mixture_predictive_prob,
    run_one_trajectory,
    sample_trajectory,
)


class AutocatalyticArtworkPairTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_compilers_are_probability_kernels(self) -> None:
        self.assertTrue(compiler_rows_are_probability_distributions())
        for theta in COMPILERS:
            matrix = compiler_kernel_matrix(theta)
            for row in matrix:
                self.assertAlmostEqual(sum(row), 1.0, places=12)
                for p in row:
                    self.assertGreaterEqual(p, 0.0)

    def test_compiler_definitions_match_paper(self) -> None:
        # K_a diagonal 0.85/0.05
        for s in S_ALPHABET:
            for e in E_ALPHABET:
                expected = DIAGONAL_PROB if e == s else OFF_DIAGONAL_PROB
                self.assertAlmostEqual(compiler_prob("a", e, s), expected, places=12)
        # K_b shifted 0.85/0.05 with cycle (s -> (s + 1) mod 4)
        for s in S_ALPHABET:
            for e in E_ALPHABET:
                expected = DIAGONAL_PROB if e == ((s + 1) % 4) else OFF_DIAGONAL_PROB
                self.assertAlmostEqual(compiler_prob("b", e, s), expected, places=12)
        # K_c uniform on |E|
        for s in S_ALPHABET:
            for e in E_ALPHABET:
                self.assertAlmostEqual(compiler_prob("c", e, s), 0.25, places=12)

    def test_true_compiler_is_in_candidate_family(self) -> None:
        self.assertIn(TRUE_COMPILER, COMPILERS)

    def test_prior_is_uniform_and_sums_to_one(self) -> None:
        self.assertAlmostEqual(sum(UNIFORM_PRIOR), 1.0, places=12)
        for p in UNIFORM_PRIOR:
            self.assertAlmostEqual(p, 1.0 / len(COMPILERS), places=12)

    def test_bayes_update_normalises_to_one(self) -> None:
        mu = UNIFORM_PRIOR
        for s in S_ALPHABET:
            for e in E_ALPHABET:
                new_mu = bayes_update(mu, s, e)
                self.assertAlmostEqual(sum(new_mu), 1.0, places=12)
                for p in new_mu:
                    self.assertGreaterEqual(p, 0.0)

    def test_boltzmann_update_normalises_to_one(self) -> None:
        mu = UNIFORM_PRIOR
        for s in S_ALPHABET:
            for e in E_ALPHABET:
                new_mu = boltzmann_update(mu, s, e, beta=BOLTZMANN_BETA)
                self.assertAlmostEqual(sum(new_mu), 1.0, places=12)
                for p in new_mu:
                    self.assertGreaterEqual(p, 0.0)

    def test_bayes_equals_boltzmann_at_beta_one_on_every_observation(self) -> None:
        # Theorem AA-2: Bayes IS Boltzmann with beta=1 and reward = log-likelihood.
        mu = (0.4, 0.35, 0.25)
        for s in S_ALPHABET:
            for e in E_ALPHABET:
                bayes_mu = bayes_update(mu, s, e)
                boltz_mu = boltzmann_update(mu, s, e, beta=1.0)
                for a, b in zip(bayes_mu, boltz_mu, strict=True):
                    self.assertAlmostEqual(a, b, places=12)

    def test_predictive_probability_is_mixture(self) -> None:
        # K̄_μ(e | s) = sum_theta mu(theta) K_theta(e | s).
        mu = (0.5, 0.3, 0.2)
        for s in S_ALPHABET:
            for e in E_ALPHABET:
                actual = mixture_predictive_prob(mu, e, s)
                expected = sum(
                    mu[i] * compiler_prob(COMPILERS[i], e, s)
                    for i in range(len(COMPILERS))
                )
                self.assertAlmostEqual(actual, expected, places=12)

    def test_sample_trajectory_is_deterministic_under_seed(self) -> None:
        traj_a = sample_trajectory(seed=42, n_steps=N_STEPS)
        traj_b = sample_trajectory(seed=42, n_steps=N_STEPS)
        self.assertEqual(traj_a, traj_b)
        self.assertEqual(len(traj_a), N_STEPS + 1)
        for s, e in traj_a:
            self.assertIn(s, S_ALPHABET)
            self.assertIn(e, E_ALPHABET)

    def test_analytical_expected_ll_at_uniform_prior_matches_closed_form(self) -> None:
        # E_{s, e ~ K_a}[log K̄_uniform(e | s)] with K̄_uniform =
        # (1/3)(K_a + K_b + K_c). For s = 0: mixture is 1.15/3 = 0.3833 for
        # e in {0, 1}, and 0.35/3 = 0.1167 for e in {2, 3}. E[log K̄] under
        # K_a(. | 0) is 0.85 log(1.15/3) + 0.05 log(1.15/3) + 0.05 log(0.35/3)
        # + 0.05 log(0.35/3) = 0.9 log(1.15/3) + 0.1 log(0.35/3). Averaged
        # over uniform s (by symmetry over s) this equals the same value.
        expected = 0.9 * math.log(1.15 / 3.0) + 0.1 * math.log(0.35 / 3.0)
        actual = analytical_expected_ll(UNIFORM_PRIOR)
        self.assertAlmostEqual(actual, expected, places=10)

    def test_analytical_expected_ll_at_true_compiler_equals_negative_entropy(
        self,
    ) -> None:
        # When mu concentrates on K_a, K̄_mu = K_a and E[log K_a(e|s)] under
        # (s, e) ~ P_S x K_a is -H(K_a(. | s)) averaged over s (which is the
        # same value for every s by symmetry).
        delta_a = (1.0, 0.0, 0.0)
        actual = analytical_expected_ll(delta_a)
        neg_entropy = 0.85 * math.log(0.85) + 3 * 0.05 * math.log(0.05)
        self.assertAlmostEqual(actual, neg_entropy, places=10)

    def test_analytical_expected_ll_monotone_in_run_trajectory(self) -> None:
        # For a single seeded trajectory, the per-posterior analytical LL is
        # provably non-decreasing under the Bayesian update by Theorem AA-1
        # (a per-step application of Jensen/mixture-DPI). This test checks the
        # per-trajectory non-decreasing property against a single seed.
        run = run_one_trajectory(seed=7)
        lls = run["analytical_expected_ll_per_t"]
        for i in range(len(lls) - 1):
            self.assertGreaterEqual(lls[i + 1] + 1e-12, lls[i])

    def test_run_one_trajectory_bayes_boltzmann_agreement(self) -> None:
        run = run_one_trajectory(seed=101)
        for gap in run["bayes_boltzmann_max_gap_per_t"]:
            self.assertLessEqual(gap, BAYES_BOLTZMANN_TOLERANCE)

    def test_aa1_monotone_gate_holds_in_expectation(self) -> None:
        payload = evaluate_benchmark()
        ll_seq = payload["mean_analytical_expected_ll_per_t"]
        self.assertEqual(len(ll_seq), N_STEPS + 1)
        for i in range(len(ll_seq) - 1):
            self.assertGreaterEqual(
                ll_seq[i + 1] + MONOTONICITY_TOLERANCE, ll_seq[i]
            )

    def test_aa1_posterior_concentration_gate_holds(self) -> None:
        payload = evaluate_benchmark()
        final_true_mass = payload["mean_posterior_true_compiler_per_t"][N_STEPS]
        self.assertGreaterEqual(final_true_mass, POSTERIOR_CONCENTRATION_TARGET)

    def test_aa2_bayes_boltzmann_agreement_gate_holds(self) -> None:
        payload = evaluate_benchmark()
        self.assertLessEqual(
            payload["global_max_bayes_vs_boltzmann_posterior_gap"],
            BAYES_BOLTZMANN_TOLERANCE,
        )

    def test_beats_uniform_baseline(self) -> None:
        payload = evaluate_benchmark()
        gap = payload["predictive_ll_gain_over_uniform_baseline_at_final_t"]
        self.assertGreaterEqual(gap, UNIFORM_BASELINE_GAP)

    def test_n_runs_and_n_steps_are_pre_registered(self) -> None:
        self.assertEqual(N_RUNS, 200)
        self.assertEqual(N_STEPS, 6)


if __name__ == "__main__":
    unittest.main()
