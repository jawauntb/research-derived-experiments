from __future__ import annotations

import unittest
from fractions import Fraction

from experiments.delete_repair_concern.core import (
    concern_of,
    evaluate_benchmark,
    kappa_concern,
    representing_set_for_bag,
    serving_cost,
)
from experiments.delete_the_absolute.core import all_worlds


class DeleteRepairConcernTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = evaluate_benchmark()

    def test_instrument_stays_valid_for_any_recorded_verdict(self) -> None:
        payload = self.payload
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["CON_REPRESENTING_SET"])
        self.assertTrue(payload["gates"]["CON_COST_MATRIX_RECORDED"])
        self.assertTrue(payload["gates"]["CON_CONCERNS_REGISTERED"])
        self.assertTrue(payload["gates"]["CON_REVERSAL"])
        self.assertTrue(payload["gates"]["CON_BOUNDARY"])
        self.assertIn(
            payload["ranking"]["verdict"],
            {"concern_does_work", "concern_idle", "inconclusive"},
        )
        self.assertIn("Valence", payload["withheld"][0])

    def test_bag_has_five_representing_screens(self) -> None:
        worlds = all_worlds()
        candidates = representing_set_for_bag(worlds)
        self.assertEqual(
            candidates, ["q_perm", "q_rot", "q_stab0", "q_stab_last", "q_id"]
        )
        self.assertEqual(self.payload["ranking"]["representing_set"], candidates)

    def test_registered_concerns_select_four_distinct_screens(self) -> None:
        choices = {
            row["concern_id"]: row["chosen_screen"] for row in self.payload["concerns"]
        }
        self.assertEqual(choices["delta_bag"], "q_perm")
        self.assertEqual(choices["bag_first"], "q_stab0")
        self.assertEqual(choices["bag_last"], "q_stab_last")
        self.assertEqual(choices["bag_pair_eq"], "q_id")
        self.assertEqual(choices["bag_parity"], "q_perm")
        self.assertEqual(choices["all_six"], "q_id")
        self.assertEqual(self.payload["ranking"]["n_distinct_choices"], 4)

    def test_unweighted_choice_is_strictly_beaten_with_exact_gap(self) -> None:
        ranking = self.payload["ranking"]
        self.assertEqual(ranking["unweighted_choice"], "q_perm")
        self.assertTrue(ranking["unweighted_strictly_beaten"])
        self.assertEqual(ranking["max_gap"], "21/2")
        bag_first = next(
            row for row in self.payload["concerns"] if row["concern_id"] == "bag_first"
        )
        self.assertEqual(bag_first["gap_vs_unweighted"], "21/2")
        self.assertTrue(bag_first["beats_unweighted_choice"])

    def test_reversal_naturality_of_the_mirrored_pair(self) -> None:
        self.assertTrue(self.payload["ranking"]["reversal_natural"])
        for row in self.payload["naturality"]:
            self.assertTrue(row["natural"])

    def test_phase_boundary_is_exactly_11_27(self) -> None:
        ranking = self.payload["ranking"]
        self.assertEqual(ranking["phase_boundary_exact"], "11/27")
        self.assertTrue(ranking["phase_boundary_confirmed"])
        by_eps = {
            Fraction(row["epsilon"]): row["chosen_screen"]
            for row in self.payload["boundary_sweep"]
        }
        self.assertEqual(by_eps[Fraction(0)], "q_perm")
        self.assertEqual(by_eps[Fraction(22, 54)], "q_perm")
        self.assertEqual(by_eps[Fraction(23, 54)], "q_id")
        self.assertEqual(by_eps[Fraction(1)], "q_id")

    def test_cost_model_matches_registration(self) -> None:
        worlds = all_worlds()
        represents, cost = serving_cost("q_perm", "bag", worlds)
        self.assertTrue(represents)
        self.assertEqual(cost, Fraction(5))
        represents, cost = serving_cost("q_perm", "first_bit", worlds)
        self.assertFalse(represents)
        self.assertEqual(cost, Fraction(32))
        chosen, costs = kappa_concern(
            concern_of({"bag": Fraction(1, 2), "first_bit": Fraction(1, 2)}),
            representing_set_for_bag(worlds),
            worlds,
        )
        self.assertEqual(chosen, "q_stab0")
        self.assertEqual(costs["q_stab0"], Fraction(8))
        self.assertEqual(costs["q_perm"], Fraction(37, 2))

    def test_ranking_follows_the_preregistered_rule(self) -> None:
        ranking = self.payload["ranking"]
        if (
            ranking["n_distinct_choices"] >= 3
            and ranking["reversal_natural"]
            and ranking["unweighted_strictly_beaten"]
        ):
            self.assertEqual(ranking["verdict"], "concern_does_work")
        elif ranking["n_distinct_choices"] == 1:
            self.assertEqual(ranking["verdict"], "concern_idle")
        else:
            self.assertEqual(ranking["verdict"], "inconclusive")

    def test_deterministic_replay(self) -> None:
        second = evaluate_benchmark()
        self.assertEqual(self.payload["ranking"], second["ranking"])
        self.assertEqual(self.payload["concerns"], second["concerns"])
        self.assertEqual(self.payload["boundary_sweep"], second["boundary_sweep"])
