from __future__ import annotations

import unittest

from experiments.delete_repair_menu_blind.core import (
    MENU_BASE,
    MENU_EXT,
    coarsest_in_menu,
    evaluate_benchmark,
    q_pair01,
    q_pair23,
    representing_in_menu,
)
from experiments.delete_the_absolute.core import all_worlds, fiber_count


class DeleteRepairMenuBlindTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = evaluate_benchmark()

    def test_instrument_stays_valid_for_any_recorded_verdict(self) -> None:
        payload = self.payload
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["MB_ENUMERATION"])
        self.assertTrue(payload["gates"]["MB_MENUS"])
        self.assertTrue(payload["gates"]["MB_CHEAP_FROZEN"])
        self.assertTrue(payload["gates"]["MB_BASE_CONSISTENT"])
        self.assertTrue(payload["gates"]["MB_SCREEN_DEFINED"])
        self.assertIn(
            payload["ranking"]["verdict"],
            {"menu_blind_dead", "menu_blind_lives", "no_function", "inconclusive"},
        )
        self.assertIn("frozen", payload["specification"]["kappa_cheap"])

    def test_gold_flips_between_menus(self) -> None:
        flips = self.payload["flips"]
        self.assertEqual(
            {flip["case_id"] for flip in flips}, {"pair_eq_q_id", "pair23_q_id"}
        )
        for flip in flips:
            self.assertEqual(flip["gold_base"], "noop")
            self.assertEqual(flip["gold_ext"], "quotient")

    def test_cheap_collision_is_menu_relative(self) -> None:
        ranking = self.payload["ranking"]
        self.assertEqual(ranking["cheap_collisions_base"], 1)
        self.assertEqual(ranking["cheap_collisions_ext"], 0)
        self.assertEqual(ranking["cheap_hits_base"], 15)
        self.assertEqual(ranking["cheap_hits_ext"], 17)
        self.assertEqual(
            ranking["cheap_function_per_menu"], {"base": False, "ext": True}
        )
        base_collision = next(
            item for item in self.payload["collisions"] if item["menu"] == "base"
        )
        self.assertEqual(
            base_collision["case_ids"],
            [
                "bag_q_id",
                "count_ge2_q_id",
                "last_bit_q_id",
                "or_q_id",
                "pair23_q_id",
                "pair_eq_q_id",
                "parity_q_id",
            ],
        )
        self.assertEqual(base_collision["golds"], ["noop", "quotient"])

    def test_screen_is_exact_on_both_menus(self) -> None:
        ranking = self.payload["ranking"]
        self.assertEqual(ranking["screen_hits"], 34)
        self.assertEqual(ranking["screen_n"], 34)
        self.assertTrue(ranking["screen_exact"])
        pair_eq_ext = next(
            row
            for row in self.payload["rows"]
            if row["case_id"] == "pair_eq_q_id" and row["menu"] == "ext"
        )
        self.assertEqual(pair_eq_ext["gold"], "quotient")
        self.assertEqual(pair_eq_ext["chosen_screen"], "q_pair01")
        self.assertEqual(pair_eq_ext["n_representing"], 3)

    def test_new_screens_and_representing_sets(self) -> None:
        worlds = all_worlds()
        self.assertEqual(fiber_count(worlds, q_pair01), 12)
        self.assertEqual(fiber_count(worlds, q_pair23), 12)
        self.assertEqual(
            representing_in_menu("pair_eq", worlds, MENU_BASE), ["q_id"]
        )
        self.assertEqual(
            representing_in_menu("pair_eq", worlds, MENU_EXT),
            ["q_pair01", "q_pair23", "q_id"],
        )
        self.assertEqual(coarsest_in_menu("pair_eq", worlds, MENU_EXT), "q_pair01")
        self.assertEqual(coarsest_in_menu("pair23", worlds, MENU_EXT), "q_pair01")

    def test_naturality_splits_by_layer(self) -> None:
        ranking = self.payload["ranking"]
        self.assertTrue(ranking["relabel_action_natural"])
        self.assertFalse(ranking["tie_break_screen_natural"])
        self.assertEqual(
            ranking["tie_witnesses"], ["pair23->pair_eq", "pair_eq->pair23"]
        )
        for row in self.payload["relabels"]:
            self.assertTrue(row["action_natural"])
            if not row["screen_natural"]:
                self.assertEqual(row["source_choice"], row["image_choice"])

    def test_ranking_follows_the_preregistered_rule(self) -> None:
        ranking = self.payload["ranking"]
        if not ranking["screen_exact"]:
            self.assertEqual(ranking["verdict"], "no_function")
        elif ranking["n_flips"] > 0:
            self.assertEqual(ranking["verdict"], "menu_blind_dead")
        else:
            self.assertIn(
                ranking["verdict"], {"menu_blind_lives", "inconclusive"}
            )

    def test_deterministic_replay(self) -> None:
        second = evaluate_benchmark()
        self.assertEqual(self.payload["ranking"], second["ranking"])
        self.assertEqual(self.payload["flips"], second["flips"])
        self.assertEqual(self.payload["rows"], second["rows"])
