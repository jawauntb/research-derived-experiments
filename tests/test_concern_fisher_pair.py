from __future__ import annotations

import math
import unittest

from experiments.concern_fisher_pair.core import (
    BETA,
    CONCERN_GRID,
    EPSILON,
    LOOP_RECTANGLE,
    LOOP_TRIANGLE,
    all_worlds,
    alpha_prime,
    concern_kernel,
    concern_stat,
    evaluate_benchmark,
    fisher_matrix_at,
    holonomy_polygon,
    latent_z,
    predicted_fisher,
)


class ConcernFisherPairTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_concern_stat_is_pm_one_on_every_world(self) -> None:
        for w in all_worlds():
            t = concern_stat(w)
            self.assertIn(t[0], (-1, 1))
            self.assertIn(t[1], (-1, 1))

    def test_kernel_normalises_to_one_on_every_fiber(self) -> None:
        worlds = all_worlds()
        for z in {latent_z(w) for w in worlds}:
            for c in CONCERN_GRID:
                kernel = concern_kernel(worlds, z, c, BETA)
                self.assertAlmostEqual(sum(p for _x, p in kernel), 1.0, places=12)

    def test_fisher_matrix_is_diagonal_with_sech_squared(self) -> None:
        worlds = all_worlds()
        for z in {latent_z(w) for w in worlds}:
            for c in CONCERN_GRID:
                emp = fisher_matrix_at(worlds, z, c, BETA)
                pred = predicted_fisher(c, BETA)
                for i in range(2):
                    for j in range(2):
                        self.assertAlmostEqual(emp[i][j], pred[i][j], places=12)

    def test_predicted_fisher_at_zero_is_beta_squared_identity(self) -> None:
        pred = predicted_fisher((0.0, 0.0), BETA)
        self.assertAlmostEqual(pred[0][0], BETA * BETA, places=12)
        self.assertAlmostEqual(pred[1][1], BETA * BETA, places=12)
        self.assertEqual(pred[0][1], 0.0)

    def test_predicted_fisher_decays_at_extremes(self) -> None:
        # sech²(β c) → 0 as |c| → ∞.
        pred = predicted_fisher((5.0, 5.0), BETA)
        self.assertLess(pred[0][0], 1e-3)
        self.assertLess(pred[1][1], 1e-3)

    def test_holonomy_of_rectangle_matches_epsilon_times_area(self) -> None:
        worlds = all_worlds()
        h = holonomy_polygon(worlds, (1, 1), BETA, EPSILON, LOOP_RECTANGLE)
        self.assertAlmostEqual(h, EPSILON * 1.0, places=3)

    def test_holonomy_of_triangle_matches_half_epsilon(self) -> None:
        worlds = all_worlds()
        h = holonomy_polygon(worlds, (1, 1), BETA, EPSILON, LOOP_TRIANGLE)
        self.assertAlmostEqual(h, EPSILON * 0.5, places=3)

    def test_alpha_prime_has_expected_correction_at_c_zero(self) -> None:
        # At c = 0, alpha_mean_stat = 0, so alpha_prime = (- eps * c_2, 0) = (0, 0).
        worlds = all_worlds()
        a = alpha_prime(worlds, (1, 1), (0.0, 0.0), BETA, EPSILON)
        self.assertAlmostEqual(a[0], 0.0, places=12)
        self.assertAlmostEqual(a[1], 0.0, places=12)


class ConcernPaperNumbersMatchClosedForm(unittest.TestCase):
    def test_sech_squared_beta_c1_formula_matches_expectation(self) -> None:
        # Sanity: our closed form matches E[T_1^2] - (E[T_1])^2 by hand at c = 0.5, beta = 1.
        c = (0.5, -0.3)
        beta = 1.0
        m1 = math.tanh(beta * c[0])
        var1 = 1 - m1 * m1
        pred = predicted_fisher(c, beta)
        self.assertAlmostEqual(pred[0][0], beta * beta * var1, places=12)


if __name__ == "__main__":
    unittest.main()
