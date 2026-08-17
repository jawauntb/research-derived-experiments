from __future__ import annotations

import math
import unittest

from experiments.eml_fiber_spectrum.core import (
    MAX_INTERNAL,
    EmlTree,
    catalan,
    enumerate_trees,
    eval_closed,
    evaluate_benchmark,
    parse_eml,
    require_finite,
)


class EmlFiberSpectrumTest(unittest.TestCase):
    def test_benchmark_passes_fatal_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["EFS_SIZE_NOT_DENOTATION"])
        self.assertTrue(payload["gates"]["EFS_ENUMERATION_COMPLETE"])
        self.assertTrue(payload["gates"]["EFS_US4_PRIME_WITHHELD"])
        self.assertIn("untested", payload["untested"]["US-4_prime"])

    def test_catalan_counts_through_six(self) -> None:
        expected = [1, 1, 2, 5, 14, 42, 132]
        for k, count in enumerate(expected):
            self.assertEqual(catalan(k), count)
        payload = evaluate_benchmark()
        self.assertEqual(payload["n_trees"], sum(expected))
        for k, count in enumerate(expected):
            self.assertEqual(payload["tree_counts_by_size"][str(k)], count)

    def test_k2_size_is_not_a_denotation(self) -> None:
        left = parse_eml("eml(1,eml(1,1))")
        right = parse_eml("eml(eml(1,1),1)")
        self.assertEqual(left.n_internal, 2)
        self.assertEqual(right.n_internal, 2)
        self.assertEqual(left.n_nodes, 5)
        self.assertNotEqual(eval_closed(left), eval_closed(right))
        self.assertAlmostEqual(require_finite(eval_closed(left), left.pretty()), math.e - 1, places=12)
        self.assertAlmostEqual(
            require_finite(eval_closed(right), right.pretty()),
            math.exp(math.e),
            places=10,
        )

    def test_hand_identities(self) -> None:
        self.assertEqual(eval_closed(EmlTree()), 1.0)
        self.assertAlmostEqual(
            require_finite(eval_closed(parse_eml("eml(1,1)")), "eml(1,1)"),
            math.e,
            places=12,
        )

    def test_enumeration_is_exactly_the_catalan_family(self) -> None:
        by_size = enumerate_trees(MAX_INTERNAL)
        self.assertEqual(sum(len(trees) for trees in by_size.values()), 197)
        self.assertEqual(len(by_size[0]), 1)
        self.assertTrue(by_size[0][0].is_leaf)

    def test_us4_prime_cannot_pass(self) -> None:
        payload = evaluate_benchmark()
        self.assertIn("untested", payload["untested"]["US-4_prime"])
        self.assertIn("not identity of functions", payload["grid_collision_disclosure"])
        self.assertTrue(payload["grid_collision_disclosed"])
