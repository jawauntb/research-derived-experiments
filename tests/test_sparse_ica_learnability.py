from __future__ import annotations

import unittest

import numpy as np

from experiments.sparse_ica_learnability.core import (
    BASE_SEED,
    D_Z_VALUES,
    FINAL_AMARI_TARGET,
    MASK_RETRIES,
    MONOTONE_TOL,
    N_VALUES,
    POLY_AMARI_TARGET,
    POLY_EXPONENT_MAX,
    SPARSER_IMPROVES_TOL,
    SPARSITY_VALUES,
    _fit_amari_for_trial,
    amari_index,
    evaluate_benchmark,
    is_monotone_within_tolerance,
    polynomial_exponent,
    sample_orthogonal,
    sample_sparse_orthogonal,
    smallest_n_reaching_target,
)


class SparseIcaLearnabilityTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_amari_of_identity_and_signed_permutation_is_zero(self) -> None:
        for d in (2, 4, 6, 8):
            self.assertAlmostEqual(amari_index(np.eye(d)), 0.0, places=12)
        rng = np.random.default_rng(0)
        for d in (3, 5, 7):
            perm = rng.permutation(d)
            signs = rng.choice([-1.0, 1.0], size=d)
            matrix = np.zeros((d, d))
            for i, j in enumerate(perm):
                matrix[i, j] = signs[i] * rng.uniform(0.5, 2.5)
            self.assertAlmostEqual(amari_index(matrix), 0.0, places=12)

    def test_amari_of_uniform_mixture_is_positive(self) -> None:
        for d in (2, 4, 6):
            self.assertGreater(amari_index(np.ones((d, d))), 0.5)

    def test_sample_sparse_orthogonal_is_orthogonal_and_deterministic(self) -> None:
        for d in (2, 4, 6, 8):
            for s in SPARSITY_VALUES:
                rng_a = np.random.default_rng(np.random.SeedSequence([42, d, int(s * 1000)]))
                rng_b = np.random.default_rng(np.random.SeedSequence([42, d, int(s * 1000)]))
                a, scheme_a = sample_sparse_orthogonal(d, s, rng_a)
                b, scheme_b = sample_sparse_orthogonal(d, s, rng_b)
                np.testing.assert_array_equal(a, b)
                self.assertEqual(scheme_a, scheme_b)
                np.testing.assert_allclose(a @ a.T, np.eye(d), atol=1e-10)
                self.assertIn(scheme_a, {"full_mask", "keep_diag"})

    def test_sample_orthogonal_matches_i8_and_is_orthogonal(self) -> None:
        for d in (2, 5, 8):
            rng_a = np.random.default_rng(42)
            rng_b = np.random.default_rng(42)
            q_a = sample_orthogonal(d, rng_a)
            q_b = sample_orthogonal(d, rng_b)
            np.testing.assert_array_equal(q_a, q_b)
            np.testing.assert_allclose(q_a @ q_a.T, np.eye(d), atol=1e-10)

    def test_trial_seed_is_reproducible(self) -> None:
        # Byte-identical Amari values under repeated calls with the same
        # (d_z, trial, sparsity) triple.
        first, scheme_a = _fit_amari_for_trial(d_z=4, trial=2, sparsity=0.25)
        second, scheme_b = _fit_amari_for_trial(d_z=4, trial=2, sparsity=0.25)
        self.assertEqual(first, second)
        self.assertEqual(scheme_a, scheme_b)

    def test_public_constants_hold_expected_shape(self) -> None:
        self.assertEqual(BASE_SEED, 0)
        self.assertEqual(tuple(D_Z_VALUES), (2, 4, 6, 8))
        self.assertEqual(tuple(N_VALUES), (200, 500, 1000, 2000, 5000, 10000))
        self.assertEqual(tuple(SPARSITY_VALUES), (0.5, 0.25))
        self.assertEqual(FINAL_AMARI_TARGET, 0.02)
        self.assertEqual(POLY_AMARI_TARGET, 0.03)
        self.assertEqual(POLY_EXPONENT_MAX, 3.0)
        self.assertEqual(MONOTONE_TOL, 0.01)
        self.assertEqual(SPARSER_IMPROVES_TOL, 0.01)
        self.assertGreaterEqual(MASK_RETRIES, 1)

    def test_committed_summary_supports_analysis_helpers(self) -> None:
        import json
        from pathlib import Path

        from experiments.sparse_ica_learnability.core import SweepPoint

        summary_path = (
            Path(__file__).resolve().parents[1]
            / "experiments"
            / "sparse_ica_learnability"
            / "results"
            / "sparse_ica_learnability_summary.json"
        )
        summary = json.loads(summary_path.read_text())

        points = [
            SweepPoint(
                d_z=int(pt["d_z"]),
                n=int(pt["n"]),
                sparsity=float(pt["sparsity"]),
                amari_mean=float(pt["amari_mean"]),
                amari_trials=tuple(float(v) for v in pt["amari_trials"]),
                scheme_counts=tuple(sorted(pt["scheme_counts"].items())),
            )
            for pt in summary["sweep_points"]
        ]
        for d_z in D_Z_VALUES:
            for s in SPARSITY_VALUES:
                self.assertTrue(
                    is_monotone_within_tolerance(points, d_z, s, MONOTONE_TOL),
                    msg=f"monotonicity failed at (d_Z={d_z}, s={s})",
                )
                self.assertIsNotNone(
                    smallest_n_reaching_target(points, d_z, s, POLY_AMARI_TARGET)
                )
        for s in SPARSITY_VALUES:
            slope, _ = polynomial_exponent(points, s, POLY_AMARI_TARGET)
            self.assertLessEqual(slope, POLY_EXPONENT_MAX)

    def test_sparser_vs_denser_gate_is_witnessed_by_committed_summary(self) -> None:
        import json
        from pathlib import Path

        summary = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "experiments"
                / "sparse_ica_learnability"
                / "results"
                / "sparse_ica_learnability_summary.json"
            ).read_text()
        )
        # sparser_delta_at_N_max[d_Z] = amari(s=0.25) - amari(s=0.5); gate
        # requires this <= SPARSER_IMPROVES_TOL for every d_Z.
        deltas = summary["sparser_delta_at_N_max"]
        self.assertEqual(set(deltas.keys()), {str(d) for d in D_Z_VALUES})
        for d in D_Z_VALUES:
            self.assertLessEqual(
                float(deltas[str(d)]),
                SPARSER_IMPROVES_TOL,
                msg=f"sparser-mixing gate violated at d_Z = {d}",
            )


if __name__ == "__main__":
    unittest.main()
