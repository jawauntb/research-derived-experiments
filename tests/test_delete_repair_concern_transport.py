from __future__ import annotations

import unittest
from fractions import Fraction

from experiments.delete_repair_concern_transport.core import (
    concern_of,
    evaluate_benchmark,
    kappa_concern_menu,
)
from experiments.delete_the_absolute.core import all_worlds


class DeleteRepairConcernTransportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = evaluate_benchmark()

    def test_instrument_stays_valid_for_any_recorded_verdict(self) -> None:
        payload = self.payload
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["CT_CANDIDATE_SETS"])
        self.assertTrue(payload["gates"]["CT_DELTA_ANCHOR"])
        self.assertTrue(payload["gates"]["CT_BOUNDARIES_CONFIRMED"])
        self.assertTrue(payload["gates"]["CT_REVERSAL"])
        self.assertIn(
            payload["ranking"]["verdict"],
            {
                "transport_holds_boundary_moves",
                "boundary_menu_stable",
                "transport_fails",
                "inconclusive",
            },
        )

    def test_representing_sets_grow_with_the_menu(self) -> None:
        ranking = self.payload["ranking"]
        self.assertEqual(len(ranking["base_candidates"]), 5)
        self.assertEqual(len(ranking["ext_candidates"]), 7)
        self.assertIn("q_pair01", ranking["ext_candidates"])
        self.assertIn("q_pair23", ranking["ext_candidates"])

    def test_boundary_is_menu_relative(self) -> None:
        ranking = self.payload["ranking"]
        self.assertEqual(ranking["base_boundary"], "11/27")
        self.assertEqual(ranking["ext_boundary"], "7/27")
        self.assertTrue(ranking["boundary_menu_relative"])
        for report in self.payload["boundaries"]:
            self.assertTrue(report["confirmed"], report["menu"])
        ext = next(r for r in self.payload["boundaries"] if r["menu"] == "ext")
        self.assertEqual(ext["choice_below"], "q_perm")
        self.assertEqual(ext["choice_above"], "q_pair01")

    def test_pair_eq_concern_choice_flips_with_the_menu(self) -> None:
        choices = {
            (row["menu"], row["concern_id"]): row["chosen_screen"]
            for row in self.payload["concerns"]
        }
        self.assertEqual(choices[("base", "bag_pair_eq")], "q_id")
        self.assertEqual(choices[("ext", "bag_pair_eq")], "q_pair01")
        self.assertEqual(choices[("base", "delta_bag")], "q_perm")
        self.assertEqual(choices[("ext", "delta_bag")], "q_perm")

    def test_reversal_naturality_under_both_menus(self) -> None:
        self.assertTrue(self.payload["ranking"]["reversal_natural_both_menus"])
        for row in self.payload["naturality"]:
            self.assertTrue(row["natural"], row["menu"])
            self.assertEqual(row["source_choice"], "q_stab0")
            self.assertEqual(row["image_choice"], "q_stab_last")

    def test_exact_crossing_arithmetic(self) -> None:
        worlds = all_worlds()
        at_tie = kappa_concern_menu(
            concern_of({"bag": 1 - Fraction(7, 27), "pair_eq": Fraction(7, 27)}),
            "ext",
            worlds,
        )
        self.assertEqual(at_tie, "q_perm")
        above = kappa_concern_menu(
            concern_of({"bag": 1 - Fraction(8, 27), "pair_eq": Fraction(8, 27)}),
            "ext",
            worlds,
        )
        self.assertEqual(above, "q_pair01")

    def test_verdict_follows_the_preregistered_rule(self) -> None:
        ranking = self.payload["ranking"]
        if not ranking["reversal_natural_both_menus"]:
            self.assertEqual(ranking["verdict"], "transport_fails")
        elif ranking["boundary_menu_relative"]:
            self.assertEqual(ranking["verdict"], "transport_holds_boundary_moves")
        else:
            self.assertIn(
                ranking["verdict"], {"boundary_menu_stable", "inconclusive"}
            )

    def test_deterministic_replay(self) -> None:
        second = evaluate_benchmark()
        self.assertEqual(self.payload["ranking"], second["ranking"])
        self.assertEqual(self.payload["boundaries"], second["boundaries"])
