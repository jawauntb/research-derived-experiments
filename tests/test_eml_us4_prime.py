from __future__ import annotations

import math
import unittest

from experiments.eml_us4_prime.core import (
    HEADLINE_MIN_INTERNAL,
    MIN_SPLIT_RATIO,
    SINGLETON_CONSTANT,
    ZERO_LEFT,
    ZERO_RIGHT,
    evaluate_benchmark,
    tree_mass,
)
from experiments.eml_variable_spectrum.core import eval_at, parse_var, require_finite


class EmlUs4PrimeTest(unittest.TestCase):
    def test_benchmark_passes_fatal_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["US4P_ENUMERATION_INHERITED"])
        self.assertTrue(payload["gates"]["US4P_ZERO_IDENTITY"])
        self.assertTrue(payload["gates"]["US4P_SAME_MINSIZE_SPLIT"])
        self.assertTrue(payload["gates"]["US4P_SHORTEST_DOES_NOT_DETERMINE_P"])
        self.assertTrue(payload["gates"]["US4P_GRADIENT_WITHHELD"])
        self.assertIn("untested", payload["untested"]["gradient_recovery"])

    def test_zero_identity_is_algebraic(self) -> None:
        left = parse_var(ZERO_LEFT)
        right = parse_var(ZERO_RIGHT)
        self.assertEqual(left.n_internal, 3)
        self.assertEqual(right.n_internal, 3)
        for x_val in (0.25, 1.0, 2.0, math.e, 4.0):
            self.assertAlmostEqual(require_finite(eval_at(left, x_val), ZERO_LEFT), 0.0, places=12)
            self.assertAlmostEqual(require_finite(eval_at(right, x_val), ZERO_RIGHT), 0.0, places=12)

    def test_headline_split_is_min_shell_multiplicity(self) -> None:
        payload = evaluate_benchmark()
        split = payload["headline_split"]
        self.assertEqual(split["min_internal"], HEADLINE_MIN_INTERNAL)
        self.assertGreaterEqual(split["ratio"], MIN_SPLIT_RATIO)
        self.assertGreater(split["fat_n_min_shell"], split["thin_n_min_shell"])
        self.assertEqual(parse_var(SINGLETON_CONSTANT).n_internal, 3)

    def test_extra_shells_do_not_carry_the_split(self) -> None:
        payload = evaluate_benchmark()
        self.assertLess(payload["max_extra_shell_factor"], 1.05)
        self.assertEqual(payload["n_size_class_inversions"], 0)
        self.assertIn("min-shell multiplicity", payload["extra_shell_note"])

    def test_shortest_only_is_flat_at_equal_multiplicity(self) -> None:
        self.assertAlmostEqual(tree_mass(3), 4.0 ** (-7), places=15)
        self.assertAlmostEqual(2.0 * tree_mass(3) / tree_mass(3), 2.0, places=15)

    def test_gradient_cannot_pass(self) -> None:
        payload = evaluate_benchmark()
        self.assertIn("not identity of functions", payload["grid_disclosure"])
        self.assertIn("exact algebraic identity", payload["grid_disclosure"])
        self.assertTrue(payload["gates"]["US4P_GRADIENT_WITHHELD"])
