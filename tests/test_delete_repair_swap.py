from __future__ import annotations

import unittest

from experiments.delete_repair_swap.core import evaluate_benchmark
from experiments.delete_the_absolute.core import all_worlds, fiber_count, is_representable, q_id, q_perm, q_stab0


class DeleteRepairSwapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = evaluate_benchmark()

    def test_instrument_stays_valid_even_if_taxonomy_dies(self) -> None:
        payload = self.payload
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["SWAP_ENUMERATION"])
        self.assertTrue(payload["gates"]["SWAP_TYPED_OVER_REPRESENTABLE"])
        self.assertTrue(payload["gates"]["SWAP_TYPED_UNDER_REPRESENTABLE"])
        self.assertTrue(payload["gates"]["SWAP_RANKING_RECORDED"])
        self.assertIn(payload["ranking"]["verdict"], {"taxonomy_holds", "taxonomy_killed"})
        self.assertIn("not new enumeration", payload["ranking"]["rule"])
        self.assertIn("Not text nomination", payload["process_disclosure"])
        self.assertIn("Universal calculus", payload["withheld"][0])

    def test_same_sixteen_point_cube(self) -> None:
        worlds = all_worlds()
        self.assertEqual(len(worlds), 16)
        self.assertEqual(fiber_count(worlds, q_id), 16)
        self.assertEqual(fiber_count(worlds, q_perm), 5)
        self.assertEqual(fiber_count(worlds, q_stab0), 8)

    def test_crossed_over_repair_fails_and_under_quotient_is_cheaper(self) -> None:
        worlds = all_worlds()
        self.assertTrue(is_representable(worlds, "q_stab0", "first_bit"))
        self.assertTrue(is_representable(worlds, "q_id", "first_bit"))
        self.assertFalse(is_representable(worlds, "q_perm", "first_bit"))
        self.assertTrue(is_representable(worlds, "q_perm", "bag"))
        self.assertTrue(is_representable(worlds, "q_id", "bag"))
        self.assertLess(fiber_count(worlds, q_perm), fiber_count(worlds, q_id))

    def test_ranking_follows_the_preregistered_rule(self) -> None:
        ranking = self.payload["ranking"]
        by_name = {row["name"]: row for row in self.payload["toys"]}
        over = by_name["first_bit"]
        under = by_name["bag"]
        self.assertTrue(over["typed_representable"])
        self.assertFalse(over["crossed_representable"])
        self.assertTrue(under["typed_representable"])
        self.assertTrue(under["crossed_representable"])
        self.assertLess(under["typed_fibres"], under["crossed_fibres"])
        expected_hold = (
            ranking["typed_wins"]
            and ranking["crossed_fails_over"]
            and ranking["under_quotient_cheaper"]
            and ranking["no_single_minimal_screen"]
        )
        if expected_hold:
            self.assertEqual(ranking["verdict"], "taxonomy_holds")
        else:
            self.assertEqual(ranking["verdict"], "taxonomy_killed")

    def test_deterministic_replay(self) -> None:
        first = self.payload
        second = evaluate_benchmark()
        self.assertEqual(first["ranking"], second["ranking"])
        self.assertEqual(first["toys"], second["toys"])
