from __future__ import annotations

import math
import unittest

from experiments.squaring_separation.core import (
    AMENDMENT,
    GIBBS_BASE,
    HEADLINE_N,
    N_VALUES,
    RUN1_UNNORMALISED_N4_BOUND,
    Z_MUL,
    Z_SQ,
    CircStep,
    alternative_circuits,
    catalan,
    circuit_degrees,
    circuit_invariant_holds,
    circuit_max_degree,
    count_mul_trees,
    count_sq_trees,
    evaluate_benchmark,
    evaluate_row,
    mul_tree_size,
    repeated_squaring,
    run1_unnormalised_bound,
    shortest_access_bound,
    sq_min_tree_size,
)


class SquaringSeparationTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))
        self.assertEqual(len(payload["gates"]), 6)

    def test_catalan_c15_is_the_n4_shell(self) -> None:
        self.assertEqual(catalan(15), 9_694_845)
        row = evaluate_row(4)
        self.assertEqual(row.mul_fiber_count, 9_694_845)
        self.assertEqual(row.mul_shell_count, 1)
        self.assertEqual(row.sq_shell_count, 27)

    def test_headline_masses_match_closed_forms(self) -> None:
        row = evaluate_row(4)
        self.assertAlmostEqual(row.p_mul, 7.8e-12, delta=1e-13)
        self.assertAlmostEqual(row.p_sq, 4.0e-3, delta=5e-5)
        self.assertAlmostEqual(row.log2_ratio, 28.92, places=2)
        self.assertAlmostEqual(row.shortest_bound, 28.28, places=2)
        self.assertGreater(row.log2_ratio, row.shortest_bound)

    def test_amended_bound_includes_partition_functions(self) -> None:
        n = 4
        delta = mul_tree_size(n) - sq_min_tree_size(n)
        expected = 2.0 * delta + math.log2(Z_MUL / Z_SQ) - math.log2(catalan(15))
        self.assertAlmostEqual(shortest_access_bound(n), expected, places=12)
        self.assertAlmostEqual(run1_unnormalised_bound(n), 2.0 * delta - math.log2(catalan(15)))
        self.assertGreater(RUN1_UNNORMALISED_N4_BOUND, shortest_access_bound(n))
        self.assertIn("SS_FIBER_MASS_EXCEEDS_SHORTEST_BOUND", AMENDMENT["gate_id"])

    def test_mul_dp_matches_catalan_on_each_registered_n(self) -> None:
        for n in N_VALUES:
            degree = 1 << n
            max_size = mul_tree_size(n)
            table = count_mul_trees(max_size, degree)
            self.assertEqual(table[max_size][degree], catalan(degree - 1))
            occupied = [size for size in range(1, max_size + 1) if table[size][degree]]
            self.assertEqual(occupied, [max_size])

    def test_sq_shells_fill_the_interval(self) -> None:
        for n in N_VALUES:
            row = evaluate_row(n)
            self.assertEqual(
                list(row.sq_shells),
                list(range(row.sq_min_tree_size, row.mul_tree_size + 1)),
            )

    def test_tree_sizes_are_exact(self) -> None:
        self.assertEqual([mul_tree_size(n) for n in N_VALUES], [3, 7, 15, 31])
        self.assertEqual([sq_min_tree_size(n) for n in N_VALUES], [2, 3, 4, 5])

    def test_repeated_squaring_is_exactly_n_steps(self) -> None:
        for n in N_VALUES:
            steps = repeated_squaring(n)
            self.assertEqual(len(steps), n)
            self.assertEqual(circuit_degrees(steps)[-1], 1 << n)
            self.assertTrue(circuit_invariant_holds(steps))
            self.assertLessEqual(circuit_max_degree(steps), 1 << n)

    def test_short_circuit_cannot_reach_pow2_degree(self) -> None:
        for n in (1, 2, 3, 4):
            short = repeated_squaring(n - 1) if n else ()
            self.assertLessEqual(circuit_max_degree(short), 1 << max(n - 1, 0))
            if n:
                self.assertLess(circuit_max_degree(short), 1 << n)

    def test_alternative_circuits_obey_the_degree_cap(self) -> None:
        for n in N_VALUES:
            for steps in alternative_circuits(n):
                self.assertTrue(circuit_invariant_holds(steps))

    def test_self_mul_is_sharing_square(self) -> None:
        steps = (CircStep("mul", 0, 0),)
        self.assertEqual(circuit_degrees(steps), [1, 2])

    def test_expressivity_every_degree_to_sixteen(self) -> None:
        mul = count_mul_trees(31, 16)
        sq = count_sq_trees(31, 16)
        for degree in range(1, 17):
            self.assertGreater(sum(row[degree] for row in mul), 0)
            self.assertGreater(sum(row[degree] for row in sq), 0)

    def test_partition_functions_are_the_generating_function_values(self) -> None:
        self.assertAlmostEqual(Z_MUL, 2.0 - math.sqrt(3.0), places=15)
        self.assertAlmostEqual(Z_SQ, (3.0 - math.sqrt(5.0)) / 2.0, places=15)
        self.assertEqual(GIBBS_BASE, 4)
        self.assertEqual(HEADLINE_N, 4)

    def test_us4_prime_is_flagged_untested(self) -> None:
        payload = evaluate_benchmark()
        self.assertIn("US-4_prime", payload["untested"])
        self.assertEqual(len(payload["citations_pending_verification"]), 2)
