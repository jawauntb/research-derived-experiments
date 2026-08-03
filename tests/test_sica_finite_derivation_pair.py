from __future__ import annotations

import unittest
from fractions import Fraction

from experiments.sica_finite_derivation_pair.core import (
    THETA_0,
    all_thetas,
    all_worlds,
    build_q,
    evaluate_benchmark,
    fibre_of,
    image_of_q,
    joint_parity,
    known_joint_parity_partition,
    p_all,
    p_smoothed,
    uniform_fibre_kernel,
)


class SICAFiniteDerivationPairTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_theta_set_is_the_four_joint_parities(self) -> None:
        self.assertEqual(set(all_thetas()), {(0, 0), (0, 1), (1, 0), (1, 1)})
        self.assertEqual(THETA_0, (0, 0))

    def test_smoothed_pmf_is_strictly_positive_on_every_world(self) -> None:
        worlds = all_worlds()
        for theta in all_thetas():
            for x in worlds:
                self.assertGreater(p_smoothed(theta, x), 0)

    def test_smoothed_pmf_normalises_on_every_theta(self) -> None:
        worlds = all_worlds()
        for theta in all_thetas():
            total = sum(
                (p_smoothed(theta, x) for x in worlds), Fraction(0)
            )
            self.assertEqual(total, Fraction(1))

    def test_smoothed_pmf_takes_the_two_expected_values(self) -> None:
        # After +1/16 smoothing and /2 normalisation:
        #   worlds with joint_parity(x) == theta  ->  P = 5/32
        #   worlds with joint_parity(x) != theta  ->  P = 1/32
        worlds = all_worlds()
        for theta in all_thetas():
            for x in worlds:
                p = p_smoothed(theta, x)
                if joint_parity(x) == theta:
                    self.assertEqual(p, Fraction(5, 32))
                else:
                    self.assertEqual(p, Fraction(1, 32))

    def test_lr_vector_is_reflexive_at_pivot(self) -> None:
        worlds = all_worlds()
        thetas = all_thetas()
        p_table = p_all(worlds, thetas)
        q = build_q(worlds, thetas, p_table)
        # Coordinate of the LR-vector at theta_0 is 1 (P(theta_0, x) / P(theta_0, x)).
        idx0 = thetas.index(THETA_0)
        for x in worlds:
            self.assertEqual(q[x][idx0], Fraction(1))

    def test_uniform_fibre_kernel_normalises_on_every_fibre(self) -> None:
        worlds = all_worlds()
        thetas = all_thetas()
        p_table = p_all(worlds, thetas)
        q = build_q(worlds, thetas, p_table)
        Z = image_of_q(q)
        for z in Z:
            total = sum(
                (uniform_fibre_kernel(q, z, x) for x in worlds), Fraction(0)
            )
            self.assertEqual(total, Fraction(1))

    def test_uniform_fibre_kernel_is_fibre_supported(self) -> None:
        worlds = all_worlds()
        thetas = all_thetas()
        p_table = p_all(worlds, thetas)
        q = build_q(worlds, thetas, p_table)
        Z = image_of_q(q)
        for z in Z:
            for x in worlds:
                k_val = uniform_fibre_kernel(q, z, x)
                if q[x] != z:
                    self.assertEqual(k_val, Fraction(0))
                else:
                    self.assertGreater(k_val, 0)

    def test_fibre_partition_covers_x_disjointly(self) -> None:
        worlds = all_worlds()
        thetas = all_thetas()
        p_table = p_all(worlds, thetas)
        q = build_q(worlds, thetas, p_table)
        Z = image_of_q(q)
        # Every world lives in the fibre of its q-value.
        for x in worlds:
            self.assertIn(x, fibre_of(q, q[x]))
        # Fibres partition X (disjoint and cover).
        seen: set[tuple[int, int, int, int]] = set()
        for z in Z:
            for w in fibre_of(q, z):
                self.assertNotIn(w, seen)
                seen.add(w)
        self.assertEqual(len(seen), len(worlds))

    def test_lr_partition_equals_joint_parity_partition(self) -> None:
        payload = evaluate_benchmark()
        agreement = payload["partition_agreement"]
        self.assertTrue(agreement["partitions_equal"])
        self.assertEqual(agreement["n_cells_q"], 4)
        self.assertEqual(agreement["n_cells_reference"], 4)
        self.assertEqual(agreement["cell_sizes_q"], [4, 4, 4, 4])

    def test_reference_partition_has_four_size_four_cells(self) -> None:
        worlds = all_worlds()
        part = known_joint_parity_partition(worlds)
        self.assertEqual(len(part), 4)
        for cell in part:
            self.assertEqual(len(cell), 4)

    def test_t1_biconditional_has_no_disagreements(self) -> None:
        payload = evaluate_benchmark()
        t1 = payload["t1_characterisation"]
        self.assertEqual(t1["n_disagreements"], 0)
        self.assertEqual(t1["matched_pairs"], t1["total_pairs"])

    def test_fibration_biconditional_has_no_disagreements(self) -> None:
        payload = evaluate_benchmark()
        fib = payload["fibration_structure"]
        self.assertEqual(fib["n_disagreements"], 0)


if __name__ == "__main__":
    unittest.main()
