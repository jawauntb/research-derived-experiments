from __future__ import annotations

import math
import unittest

from experiments.cross_task_learnability_continuous.core import (
    AMBIENT_SIDE,
    EPS_REL,
    D_Z_VALUES,
    R_VALUES,
    evaluate_benchmark,
    evaluate_scaling_point,
    exact_recovery_probability_balanced,
    theorem_bound,
)


class CrossTaskLearnabilityContinuousTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_theorem_bound_formula(self) -> None:
        self.assertEqual(theorem_bound(m=4, c=1.0, eps_rel=0.05), math.ceil(4 * math.log(80)))
        self.assertEqual(
            theorem_bound(m=256, c=1.0, eps_rel=0.05),
            math.ceil(256 * math.log(256 / 0.05)),
        )

    def test_balanced_recovery_is_zero_below_M(self) -> None:
        for m in (4, 16, 64, 256):
            for n in range(m):
                self.assertEqual(exact_recovery_probability_balanced(m, n), 0.0)

    def test_balanced_recovery_matches_small_M_formula(self) -> None:
        # For M = 4 balanced, use the closed form
        # P = 1 - 4*(3/4)^N + 6*(1/2)^N - 4*(1/4)^N.
        for n in (4, 6, 10, 18, 30):
            expected = (
                1
                - 4 * (3 / 4) ** n
                + 6 * (1 / 2) ** n
                - 4 * (1 / 4) ** n
            )
            actual = exact_recovery_probability_balanced(4, n)
            self.assertAlmostEqual(actual, expected, places=10)

    def test_balanced_recovery_is_monotone(self) -> None:
        # Spot check monotonicity for a middling M.
        prev = -0.001
        for n in range(0, 200, 5):
            current = exact_recovery_probability_balanced(64, n)
            self.assertGreaterEqual(current + 1e-12, prev)
            prev = current

    def test_ambient_side_divides_all_r_values(self) -> None:
        for r in R_VALUES:
            self.assertEqual(AMBIENT_SIDE % r, 0)

    def test_theorem_bound_meets_target_at_every_grid_point(self) -> None:
        for d_z in D_Z_VALUES:
            for r in R_VALUES:
                pt = evaluate_scaling_point(d_z=d_z, r=r)
                self.assertTrue(
                    pt.meets_target,
                    msg=f"(d_Z={d_z}, r={r}) failed: P={pt.exact_recovery_at_bound}",
                )
                self.assertGreaterEqual(pt.exact_recovery_at_bound, 1.0 - EPS_REL)

    def test_exponential_in_d_Z_scaling(self) -> None:
        # For fixed r, N_bound(d_Z=2, r) should exceed N_bound(d_Z=1, r) by
        # a factor at least r/2 (a loose lower bound that still catches
        # any accidental collapse to polynomial scaling).
        for r in R_VALUES:
            pt1 = evaluate_scaling_point(d_z=1, r=r)
            pt2 = evaluate_scaling_point(d_z=2, r=r)
            self.assertGreater(pt2.N_bound / pt1.N_bound, r / 2)


if __name__ == "__main__":
    unittest.main()
