from __future__ import annotations

import unittest

import numpy as np

from experiments.linear_ica_learnability.core import (
    BASE_SEED,
    D_Z_VALUES,
    FINAL_AMARI_TARGET,
    MONOTONE_TOL,
    N_VALUES,
    POLY_AMARI_TARGET,
    POLY_EXPONENT_MAX,
    ESCAPE_FACTOR_MIN,
    _fit_amari_for_trial,
    amari_index,
    evaluate_benchmark,
    is_monotone_within_tolerance,
    polynomial_exponent,
    sample_orthogonal,
    smallest_n_reaching_target,
    theorem6_bound,
)


class LinearIcaLearnabilityTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_amari_of_identity_is_zero(self) -> None:
        for d in (2, 4, 6, 8):
            self.assertAlmostEqual(amari_index(np.eye(d)), 0.0, places=12)

    def test_amari_of_signed_permutation_is_zero(self) -> None:
        rng = np.random.default_rng(0)
        for d in (3, 5, 7):
            perm = rng.permutation(d)
            signs = rng.choice([-1.0, 1.0], size=d)
            matrix = np.zeros((d, d))
            for i, j in enumerate(perm):
                matrix[i, j] = signs[i] * (rng.uniform(0.5, 2.5))
            self.assertAlmostEqual(amari_index(matrix), 0.0, places=12)

    def test_amari_of_uniform_mixture_is_positive(self) -> None:
        for d in (2, 4, 6):
            matrix = np.ones((d, d))
            self.assertGreater(amari_index(matrix), 0.5)

    def test_sample_orthogonal_is_orthogonal_and_deterministic(self) -> None:
        for d in (2, 5, 8):
            rng_a = np.random.default_rng(42)
            rng_b = np.random.default_rng(42)
            q_a = sample_orthogonal(d, rng_a)
            q_b = sample_orthogonal(d, rng_b)
            np.testing.assert_array_equal(q_a, q_b)
            np.testing.assert_allclose(q_a @ q_a.T, np.eye(d), atol=1e-10)

    def test_trial_seed_is_reproducible(self) -> None:
        # Repeated calls to _fit_amari_for_trial with the same (d_z, trial)
        # must produce byte-identical Amari values.
        first = _fit_amari_for_trial(d_z=4, trial=2)
        second = _fit_amari_for_trial(d_z=4, trial=2)
        self.assertEqual(first, second)

    def test_theorem6_bound_matches_closed_form(self) -> None:
        # (D_Z / eps)^{d_Z} = 4^{d_Z} with the default (D_Z=1, eps=0.25, eps_rel=0.05).
        for d_z in (2, 4, 6, 8):
            expected = int(
                np.ceil(4.0**d_z * (d_z * np.log(4.0) + np.log(1.0 / 0.05)))
            )
            self.assertEqual(theorem6_bound(d_z), expected)

    def test_public_constants_hold_expected_shape(self) -> None:
        self.assertEqual(BASE_SEED, 0)
        self.assertEqual(tuple(D_Z_VALUES), (2, 4, 6, 8))
        self.assertEqual(tuple(N_VALUES), (200, 500, 1000, 2000, 5000, 10000))
        self.assertEqual(FINAL_AMARI_TARGET, 0.02)
        self.assertEqual(POLY_AMARI_TARGET, 0.03)
        self.assertEqual(POLY_EXPONENT_MAX, 3.0)
        self.assertEqual(MONOTONE_TOL, 0.01)
        self.assertEqual(ESCAPE_FACTOR_MIN, 20.0)

    def test_committed_summary_supports_analysis_helpers(self) -> None:
        # Read the committed run artifact to check the helper functions do
        # what the gate names claim (monotone + polynomial + smallest-N).
        import json
        from pathlib import Path

        summary_path = (
            Path(__file__).resolve().parents[1]
            / "experiments"
            / "linear_ica_learnability"
            / "results"
            / "linear_ica_learnability_summary.json"
        )
        summary = json.loads(summary_path.read_text())

        # Rebuild the SweepPoint list from the JSON so helpers can run offline.
        from experiments.linear_ica_learnability.core import SweepPoint

        points = [
            SweepPoint(
                d_z=int(pt["d_z"]),
                n=int(pt["n"]),
                amari_mean=float(pt["amari_mean"]),
                amari_trials=tuple(float(v) for v in pt["amari_trials"]),
            )
            for pt in summary["sweep_points"]
        ]
        for d_z in D_Z_VALUES:
            self.assertTrue(
                is_monotone_within_tolerance(points, d_z, MONOTONE_TOL),
                msg=f"monotonicity failed at d_Z = {d_z}",
            )
            n_needed = smallest_n_reaching_target(points, d_z, POLY_AMARI_TARGET)
            self.assertIsNotNone(n_needed)
        slope, _ = polynomial_exponent(points, POLY_AMARI_TARGET)
        self.assertLessEqual(slope, POLY_EXPONENT_MAX)


if __name__ == "__main__":
    unittest.main()
