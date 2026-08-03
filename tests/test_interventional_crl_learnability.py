from __future__ import annotations

import unittest

import numpy as np

from experiments.interventional_crl_learnability.core import (
    BASE_SEED,
    D_Z_VALUES,
    FINAL_AMARI_TARGET,
    INTERVENTION_MU_MAX,
    INTERVENTION_MU_MIN,
    INTERVENTION_SIGMA,
    MONOTONE_TOL,
    N_PER_ENV_VALUES,
    NONLINEAR_ACTIVATION_SCALE,
    POLY_AMARI_TARGET,
    POLY_EXPONENT_MAX,
    SPLIT_HELPS_TOL,
    TRIALS,
    _run_trial,
    align_via_intervention_shift,
    amari_index,
    evaluate_benchmark,
    is_monotone_within_tolerance,
    mlp_mixing,
    polynomial_exponent,
    sample_environment_latents,
    sample_intervention_offsets,
    sample_orthogonal,
    smallest_n_reaching_target,
)


class InterventionalCrlLearnabilityTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_amari_of_identity_and_signed_permutation_is_zero(self) -> None:
        for d in (2, 3, 4):
            self.assertAlmostEqual(amari_index(np.eye(d)), 0.0, places=12)
        rng = np.random.default_rng(0)
        for d in (2, 3, 4, 5):
            perm = rng.permutation(d)
            signs = rng.choice([-1.0, 1.0], size=d)
            matrix = np.zeros((d, d))
            for i, j in enumerate(perm):
                matrix[i, j] = signs[i] * rng.uniform(0.5, 2.5)
            self.assertAlmostEqual(amari_index(matrix), 0.0, places=12)

    def test_amari_of_uniform_mixture_is_positive(self) -> None:
        for d in (2, 3, 4):
            self.assertGreater(amari_index(np.ones((d, d))), 0.5)

    def test_sample_orthogonal_is_orthogonal_and_deterministic(self) -> None:
        for d in (2, 3, 4, 5):
            rng_a = np.random.default_rng(42)
            rng_b = np.random.default_rng(42)
            q_a = sample_orthogonal(d, rng_a)
            q_b = sample_orthogonal(d, rng_b)
            np.testing.assert_array_equal(q_a, q_b)
            np.testing.assert_allclose(q_a @ q_a.T, np.eye(d), atol=1e-10)

    def test_intervention_offsets_are_bounded_and_reproducible(self) -> None:
        rng_a = np.random.default_rng(np.random.SeedSequence([BASE_SEED, 3, 1]))
        rng_b = np.random.default_rng(np.random.SeedSequence([BASE_SEED, 3, 1]))
        mus_a = sample_intervention_offsets(3, rng_a)
        mus_b = sample_intervention_offsets(3, rng_b)
        np.testing.assert_array_equal(mus_a, mus_b)
        self.assertTrue(bool(np.all(mus_a >= INTERVENTION_MU_MIN)))
        self.assertTrue(bool(np.all(mus_a <= INTERVENTION_MU_MAX)))

    def test_mlp_mixing_is_linear_at_zero_input(self) -> None:
        # d/dz [W2 tanh(alpha W1 z)]|z=0 = alpha W2 W1, so a tiny input
        # should be approximately alpha * (W2 @ W1) @ z. Verifies the
        # A_linear = W2 @ W1 identity used in the Amari calibration is
        # correct in the limit z -> 0.
        rng = np.random.default_rng(7)
        for d in (2, 3, 4):
            w1 = sample_orthogonal(d, rng)
            w2 = sample_orthogonal(d, rng)
            z = 1e-6 * rng.standard_normal((5, d))
            x = mlp_mixing(z, w1, w2)
            expected = NONLINEAR_ACTIVATION_SCALE * z @ w1.T @ w2.T
            np.testing.assert_allclose(x, expected, atol=1e-14, rtol=1e-8)

    def test_sample_environment_latents_shapes_and_intervention_effect(self) -> None:
        rng = np.random.default_rng(np.random.SeedSequence([BASE_SEED, 3, 0]))
        mus = np.array([1.5, -1.0, 2.0])
        latents, labels = sample_environment_latents(2000, 3, mus, rng)
        self.assertEqual(labels, [0, 1, 2, 3])
        self.assertEqual(len(latents), 4)
        for z in latents:
            self.assertEqual(z.shape, (2000, 3))
        # Environment 0 is observational: every component has mean near 0.
        for k in range(3):
            self.assertLess(abs(latents[0][:, k].mean()), 0.3)
        # Environment i > 0 intervenes on Z_i: that component's sample
        # mean should be closer to mus[i - 1] than to 0, and the other
        # components' means should still be near 0.
        for i in range(1, 4):
            intervened = latents[i][:, i - 1]
            self.assertLess(
                abs(intervened.mean() - mus[i - 1]),
                abs(intervened.mean()) + 0.3,
            )
            for k in range(3):
                if k == i - 1:
                    continue
                self.assertLess(abs(latents[i][:, k].mean()), 0.3)

    def test_align_via_intervention_shift_picks_the_shifted_row(self) -> None:
        # A hand-crafted case with d_z = 2: three environments (obs +
        # intervention on Z_0 + intervention on Z_1). Each intervention
        # environment shifts a different X column and the alignment must
        # pick the corresponding row of the identity unmixing.
        d = 2
        w_hats = [np.eye(d), np.eye(d), np.eye(d)]
        x0 = np.zeros((10, d))
        x1 = np.array([[3.0, 0.0]] * 10)  # env 1 shifts column 0.
        x2 = np.array([[0.0, -2.5]] * 10)  # env 2 shifts column 1.
        aligned = align_via_intervention_shift(w_hats, [x0, x1, x2], d)
        self.assertEqual(aligned.shape, (d, d))
        # Row 0 must match column-0-picking row of I: [1, 0].
        np.testing.assert_array_equal(aligned[0], np.array([1.0, 0.0]))
        # Row 1 must match column-1-picking row of I: [0, 1].
        np.testing.assert_array_equal(aligned[1], np.array([0.0, 1.0]))

    def test_run_trial_is_reproducible(self) -> None:
        first_split, first_pool = _run_trial(d_z=3, trial=1, n_per_env=1000)
        second_split, second_pool = _run_trial(d_z=3, trial=1, n_per_env=1000)
        self.assertEqual(first_split, second_split)
        self.assertEqual(first_pool, second_pool)

    def test_public_constants_hold_expected_shape(self) -> None:
        self.assertEqual(BASE_SEED, 0)
        self.assertEqual(tuple(D_Z_VALUES), (2, 3, 4))
        self.assertEqual(tuple(N_PER_ENV_VALUES), (500, 1000, 2000, 5000, 10000))
        self.assertEqual(TRIALS, 4)
        self.assertEqual(FINAL_AMARI_TARGET, 0.20)
        self.assertEqual(POLY_AMARI_TARGET, 0.30)
        self.assertEqual(POLY_EXPONENT_MAX, 5.0)
        self.assertEqual(MONOTONE_TOL, 0.03)
        self.assertEqual(SPLIT_HELPS_TOL, 0.005)
        self.assertEqual(INTERVENTION_SIGMA, 0.5)
        self.assertEqual(INTERVENTION_MU_MIN, -2.0)
        self.assertEqual(INTERVENTION_MU_MAX, 2.0)
        self.assertEqual(NONLINEAR_ACTIVATION_SCALE, 0.5)

    def test_committed_summary_supports_analysis_helpers(self) -> None:
        import json
        from pathlib import Path

        from experiments.interventional_crl_learnability.core import SweepPoint

        summary_path = (
            Path(__file__).resolve().parents[1]
            / "experiments"
            / "interventional_crl_learnability"
            / "results"
            / "interventional_crl_learnability_summary.json"
        )
        summary = json.loads(summary_path.read_text())

        points = [
            SweepPoint(
                d_z=int(pt["d_z"]),
                n_per_env=int(pt["n_per_env"]),
                split_amari_mean=float(pt["split_amari_mean"]),
                split_amari_trials=tuple(float(v) for v in pt["split_amari_trials"]),
                pool_amari_mean=float(pt["pool_amari_mean"]),
                pool_amari_trials=tuple(float(v) for v in pt["pool_amari_trials"]),
            )
            for pt in summary["sweep_points"]
        ]
        for d_z in D_Z_VALUES:
            self.assertTrue(
                is_monotone_within_tolerance(points, d_z, MONOTONE_TOL),
                msg=f"monotonicity failed at d_Z={d_z}",
            )
            self.assertIsNotNone(
                smallest_n_reaching_target(points, d_z, POLY_AMARI_TARGET)
            )
        slope, _ = polynomial_exponent(points, POLY_AMARI_TARGET)
        self.assertLessEqual(slope, POLY_EXPONENT_MAX)

    def test_split_helps_gate_is_witnessed_by_committed_summary(self) -> None:
        import json
        from pathlib import Path

        summary = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "experiments"
                / "interventional_crl_learnability"
                / "results"
                / "interventional_crl_learnability_summary.json"
            ).read_text()
        )
        deltas = summary["split_vs_pool_delta_at_N_max"]
        self.assertEqual(set(deltas.keys()), {str(d) for d in D_Z_VALUES})
        for d in D_Z_VALUES:
            self.assertLess(
                float(deltas[str(d)]),
                -SPLIT_HELPS_TOL,
                msg=f"environment-split gate violated at d_Z = {d}",
            )


if __name__ == "__main__":
    unittest.main()
