from __future__ import annotations

import math
import unittest

from experiments.rate_distortion_pair.core import (
    D_GRID_BERNOULLI_P03,
    D_GRID_UNIFORM_N4,
    bernoulli_channel_test_mi,
    bernoulli_rd_curve,
    evaluate_benchmark,
    h_binary,
    rd_bernoulli_hamming,
    rd_uniform_hamming,
    uniform_channel_test_mi,
    uniform_rd_curve,
)


class RateDistortionPairTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_binary_entropy_boundaries(self) -> None:
        self.assertEqual(h_binary(0.0), 0.0)
        self.assertEqual(h_binary(1.0), 0.0)
        self.assertAlmostEqual(h_binary(0.5), 1.0, places=12)

    def test_rd_uniform_boundary_values(self) -> None:
        self.assertAlmostEqual(rd_uniform_hamming(4, 0.0), 2.0, places=12)
        self.assertAlmostEqual(rd_uniform_hamming(4, 0.75), 0.0, places=12)
        self.assertEqual(rd_uniform_hamming(4, 0.9), 0.0)
        self.assertAlmostEqual(
            rd_uniform_hamming(2, 0.0), 1.0, places=12  # binary source: H = 1 bit
        )
        self.assertAlmostEqual(rd_uniform_hamming(2, 0.5), 0.0, places=12)

    def test_rd_bernoulli_boundary_values(self) -> None:
        p = 0.3
        self.assertAlmostEqual(rd_bernoulli_hamming(p, 0.0), h_binary(p), places=12)
        self.assertAlmostEqual(rd_bernoulli_hamming(p, p), 0.0, places=12)
        self.assertEqual(rd_bernoulli_hamming(p, 0.5), 0.0)

    def test_test_channel_achieves_rate_at_all_grid_points_below_dmax(self) -> None:
        for d in D_GRID_UNIFORM_N4:
            if d >= 0.75:
                continue
            self.assertAlmostEqual(
                uniform_channel_test_mi(4, d), rd_uniform_hamming(4, d), places=12
            )
        for d in D_GRID_BERNOULLI_P03:
            if d >= 0.3:
                continue
            self.assertAlmostEqual(
                bernoulli_channel_test_mi(0.3, d),
                rd_bernoulli_hamming(0.3, d),
                places=12,
            )

    def test_rd_curves_are_monotone_and_convex(self) -> None:
        for n in (2, 3, 4, 8):
            grid = [i / 20 for i in range(20)]
            rates = [rd_uniform_hamming(n, d) for d in grid]
            for a, b in zip(rates, rates[1:]):
                self.assertGreaterEqual(a + 1e-9, b)
            # Convexity: midpoint <= average of endpoints on a uniform grid.
            for i in range(1, len(rates) - 1):
                chord = 0.5 * (rates[i - 1] + rates[i + 1])
                self.assertLessEqual(rates[i], chord + 1e-9)

    def test_r_at_zero_equals_source_entropy_and_matches_theorem1_case(self) -> None:
        # Theorem 1 anchor: at D = 0 the encoder is minimal-sufficient
        # (identity partition) and R(0) equals the source entropy.
        for n in (2, 3, 4, 5, 8):
            self.assertAlmostEqual(rd_uniform_hamming(n, 0.0), math.log2(n), places=12)
        for p in (0.1, 0.3, 0.5):
            self.assertAlmostEqual(rd_bernoulli_hamming(p, 0.0), h_binary(p), places=12)

    def test_rd_curves_grid_lengths_match_evaluated_payloads(self) -> None:
        u_curve = uniform_rd_curve(4, D_GRID_UNIFORM_N4)
        self.assertEqual(len(u_curve), len(D_GRID_UNIFORM_N4))
        b_curve = bernoulli_rd_curve(0.3, D_GRID_BERNOULLI_P03)
        self.assertEqual(len(b_curve), len(D_GRID_BERNOULLI_P03))


if __name__ == "__main__":
    unittest.main()
