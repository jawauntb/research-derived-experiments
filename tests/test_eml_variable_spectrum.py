from __future__ import annotations

import math
import unittest

from experiments.eml_variable_spectrum.core import (
    MAX_INTERNAL,
    catalan,
    enumerate_trees,
    eval_at,
    evaluate_benchmark,
    labeled_count,
    parse_var,
)


class EmlVariableSpectrumTest(unittest.TestCase):
    def test_benchmark_passes_fatal_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["EVS_ENUMERATION_COMPLETE"])
        self.assertTrue(payload["gates"]["EVS_SIZE_NOT_FUNCTION"])
        self.assertTrue(payload["gates"]["EVS_CONSTANT_EMBEDDING"])
        self.assertTrue(payload["gates"]["EVS_US4_PRIME_WITHHELD"])
        self.assertIn("untested", payload["untested"]["US-4_prime"])

    def test_labeled_catalan_counts_through_five(self) -> None:
        expected = [2, 4, 16, 80, 448, 2688]
        for k, count in enumerate(expected):
            self.assertEqual(labeled_count(k), count)
            self.assertEqual(labeled_count(k), catalan(k) * (2 ** (k + 1)))
        payload = evaluate_benchmark()
        self.assertEqual(payload["n_trees"], sum(expected))
        for k, count in enumerate(expected):
            self.assertEqual(payload["tree_counts_by_size"][str(k)], count)

    def test_size_one_is_not_a_function(self) -> None:
        left = parse_var("eml(x,1)")
        right = parse_var("eml(1,x)")
        self.assertEqual(left.n_internal, 1)
        self.assertEqual(right.n_internal, 1)
        self.assertAlmostEqual(eval_at(left, 2.0), math.exp(2.0), places=12)
        self.assertAlmostEqual(eval_at(right, 2.0), math.e - math.log(2.0), places=12)
        self.assertNotAlmostEqual(eval_at(left, 2.0), eval_at(right, 2.0), places=8)
        self.assertAlmostEqual(eval_at(left, 1.0), math.e, places=12)
        self.assertAlmostEqual(eval_at(right, 1.0), math.e, places=12)

    def test_constant_embedding_recovers_the_size_two_split(self) -> None:
        left = parse_var("eml(1,eml(1,1))")
        right = parse_var("eml(eml(1,1),1)")
        self.assertTrue(left.all_ones())
        self.assertTrue(right.all_ones())
        self.assertAlmostEqual(eval_at(left, 0.5), math.e - 1.0, places=12)
        self.assertAlmostEqual(eval_at(right, 4.0), math.exp(math.e), places=10)

    def test_enumeration_matches_the_recurrence(self) -> None:
        by_size = enumerate_trees(MAX_INTERNAL)
        self.assertEqual(len(by_size[0]), 2)
        self.assertEqual({tree.pretty() for tree in by_size[0]}, {"1", "x"})
        self.assertEqual(sum(len(trees) for trees in by_size.values()), 3238)

    def test_us4_prime_cannot_pass(self) -> None:
        payload = evaluate_benchmark()
        self.assertIn("not identity of functions", payload["grid_disclosure"])
        self.assertFalse(payload["spectrum"]["size_is_function_invariant"])
