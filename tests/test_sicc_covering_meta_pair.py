from __future__ import annotations

import math
import unittest

from experiments.sicc_covering_meta_pair.core import (
    DELTA,
    K_VALUES,
    STABILITY_TOL_PCT,
    evaluate_benchmark,
    exact_recovery_probability,
    meta_theorem_bound_at_c,
    smallest_N_for_recovery,
)


class SICCCoveringMetaPairTests(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_recovery_probability_is_zero_below_pigeonhole(self) -> None:
        for K in K_VALUES:
            self.assertEqual(exact_recovery_probability(K, K - 1), 0.0)

    def test_recovery_probability_monotone_in_N(self) -> None:
        # Coupling: adding samples never uncollects a cell. Verify at K = 8
        # across a broad N range.
        prev = 0.0
        for N in range(0, 200):
            p = exact_recovery_probability(8, N)
            self.assertGreaterEqual(p + 1e-15, prev)
            prev = p

    def test_recovery_probability_bounded_in_zero_one(self) -> None:
        for K in K_VALUES:
            for N in (K, 2 * K, 10 * K):
                p = exact_recovery_probability(K, N)
                self.assertGreaterEqual(p, 0.0)
                self.assertLessEqual(p, 1.0)

    def test_smallest_N_meets_target_and_is_tight(self) -> None:
        for K in K_VALUES:
            n = smallest_N_for_recovery(K, DELTA)
            self.assertGreaterEqual(exact_recovery_probability(K, n), 1.0 - DELTA)
            self.assertLess(exact_recovery_probability(K, n - 1), 1.0 - DELTA)

    def test_meta_theorem_bound_matches_formula(self) -> None:
        for K in K_VALUES:
            expected = 1.0 * K * math.log(K / DELTA)
            self.assertAlmostEqual(
                meta_theorem_bound_at_c(K, DELTA, 1.0), expected, places=12
            )

    def test_fitted_c_span_matches_stability_gate(self) -> None:
        payload = evaluate_benchmark()
        span = payload["c_fitted"]["span_over_mean"]
        self.assertLessEqual(span, STABILITY_TOL_PCT)

    def test_fitted_c_approaches_one_from_below_with_K(self) -> None:
        # The K · log(K/δ) upper bound is slightly loose at small K because
        # of the coupon-collector `K · γ` correction; the loose factor shrinks
        # as K grows, so c_fitted(K) is monotone increasing toward 1.
        payload = evaluate_benchmark()
        cs = [row["c_fitted"] for row in payload["rows"]]
        for a, b in zip(cs, cs[1:]):
            self.assertLess(a, b)
        # Every empirical c is at most 1 (coupon collector cannot exceed the
        # meta-theorem's constant here).
        for c in cs:
            self.assertLessEqual(c, 1.0)


if __name__ == "__main__":
    unittest.main()
