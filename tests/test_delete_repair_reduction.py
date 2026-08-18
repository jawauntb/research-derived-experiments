from __future__ import annotations

import unittest

from experiments.delete_repair_reduction.core import (
    SIZE_BOUND,
    denotation,
    enumerate_trees,
    evaluate_benchmark,
    tree_size,
)


class DeleteRepairReductionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = evaluate_benchmark()

    def test_instrument_stays_valid_for_any_recorded_verdict(self) -> None:
        payload = self.payload
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["RED_ENUMERATION"])
        self.assertTrue(payload["gates"]["RED_SHARED_UNIVERSE"])
        self.assertTrue(payload["gates"]["RED_TARGETS_INHABITED"])
        self.assertTrue(payload["gates"]["RED_ROUND_TRIP"])
        self.assertIn(
            payload["ranking"]["verdict"],
            {"outside_fact_found", "all_reduce", "inconclusive"},
        )

    def test_matches_banked_squaring_separation_numbers(self) -> None:
        ranking = self.payload["ranking"]
        # US-2/US-3 at n=2: formula 2^(n+1)-1 = 7, sq-tower n+1 = 3.
        self.assertEqual(ranking["min_size_x4_base"], 7)
        self.assertEqual(ranking["min_size_x4_ext"], 3)
        self.assertEqual(ranking["mass_x4_base"], 5)
        self.assertEqual(ranking["mass_x4_ext"], 14)

    def test_screens_are_invariant_on_the_shared_universe(self) -> None:
        for row in self.payload["screen_invariance"]:
            self.assertTrue(row["identical"], row["screen_id"])
            self.assertEqual(row["n_cells_base_view"], row["n_cells_ext_view"])
        self.assertTrue(self.payload["ranking"]["screens_all_invariant"])

    def test_two_point_separation_yields_outside_fact(self) -> None:
        ranking = self.payload["ranking"]
        if (
            ranking["shared_universe_ok"]
            and ranking["screens_all_invariant"]
            and ranking["access_changed"]
            and ranking["round_trip_identity"]
        ):
            self.assertEqual(ranking["verdict"], "outside_fact_found")
        self.assertIn("not a function of the (q, K) data", ranking["separation"])

    def test_enumeration_semantics(self) -> None:
        base = enumerate_trees(SIZE_BOUND, with_sq=False)
        ext = enumerate_trees(SIZE_BOUND, with_sq=True)
        self.assertEqual(len(base), 9)
        self.assertEqual(len(ext), 89)
        self.assertTrue(set(base).issubset(set(ext)))
        x4_formula = ("mul", ("mul", ("x",), ("x",)), ("mul", ("x",), ("x",)))
        x4_tower = ("sq", ("sq", ("x",)))
        self.assertEqual(denotation(x4_formula), 4)
        self.assertEqual(denotation(x4_tower), 4)
        self.assertEqual(tree_size(x4_formula), 7)
        self.assertEqual(tree_size(x4_tower), 3)
        self.assertIn(x4_formula, base)
        self.assertNotIn(x4_tower, base)
        self.assertIn(x4_tower, ext)

    def test_round_trip_is_identity_on_access(self) -> None:
        stages = {row["stage"]: row["min_size_x4"] for row in self.payload["round_trip"]}
        self.assertEqual(stages["ext_before_delete"], stages["ext_after_repair"])
        self.assertGreater(stages["base_after_delete"], stages["ext_before_delete"])

    def test_deterministic_replay(self) -> None:
        second = evaluate_benchmark()
        self.assertEqual(self.payload["ranking"], second["ranking"])
        self.assertEqual(self.payload["censuses"], second["censuses"])
