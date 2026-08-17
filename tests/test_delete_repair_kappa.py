from __future__ import annotations

import unittest

from experiments.delete_repair_kappa.core import (
    coarsest_representing,
    evaluate_benchmark,
    kappa_screen,
)
from experiments.delete_repair_surgery.core import CASES
from experiments.delete_the_absolute.core import all_worlds


class DeleteRepairKappaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = evaluate_benchmark()

    def test_instrument_stays_valid_for_any_recorded_verdict(self) -> None:
        payload = self.payload
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["KAP_ENUMERATION"])
        self.assertTrue(payload["gates"]["KAP_SCREEN_DEFINED"])
        self.assertTrue(payload["gates"]["KAP_RELABEL"])
        self.assertIn(
            payload["ranking"]["verdict"],
            {"calculus_is_sic", "calculus_holds", "no_function"},
        )
        self.assertIn("specified before", payload["process_disclosure"])
        self.assertIn("master object", payload["withheld"][0])

    def test_cheap_signature_is_not_a_function(self) -> None:
        ranking = self.payload["ranking"]
        self.assertFalse(ranking["cheap_is_function"])
        self.assertEqual(ranking["n_cheap_collisions"], 1)
        collision = self.payload["collisions"][0]
        self.assertEqual(
            set(collision["case_ids"]),
            {"bag_q_id", "last_bit_q_id", "parity_q_id", "pair_eq_q_id"},
        )
        self.assertEqual(set(collision["golds"]), {"noop", "quotient"})
        self.assertIn("pair_eq_q_id", collision["case_ids"])

    def test_written_function_hits_the_suite_and_fixes_the_grain(self) -> None:
        ranking = self.payload["ranking"]
        self.assertEqual(ranking["screen_hits"], 11)
        self.assertEqual(ranking["screen_n"], 11)
        self.assertTrue(ranking["screen_exact"])
        self.assertTrue(ranking["pair_eq_screen_is_noop"])
        pair_eq = next(
            row for row in self.payload["cases"] if row["case_id"] == "pair_eq_q_id"
        )
        self.assertEqual(pair_eq["screen"], "noop")
        self.assertEqual(pair_eq["chosen_screen"], "q_id")
        self.assertEqual(pair_eq["n_representing"], 1)

    def test_uniqueness_fails_without_the_tie_break(self) -> None:
        ranking = self.payload["ranking"]
        self.assertTrue(ranking["uniqueness_fails"])
        self.assertEqual(ranking["max_representing"], 5)
        self.assertTrue(ranking["noncommute"])
        bag = next(row for row in self.payload["cases"] if row["case_id"] == "bag_q_id")
        self.assertEqual(bag["n_representing"], 5)
        self.assertEqual(bag["chosen_screen"], "q_perm")

    def test_relabel_and_coarsest_are_specified_maps(self) -> None:
        worlds = all_worlds()
        self.assertEqual(coarsest_representing("first_bit", worlds), "q_stab0")
        self.assertEqual(coarsest_representing("last_bit", worlds), "q_stab_last")
        self.assertEqual(coarsest_representing("bag", worlds), "q_perm")
        self.assertEqual(coarsest_representing("pair_eq", worlds), "q_id")
        first = next(spec for spec in CASES if spec["case_id"] == "first_bit_q_perm")
        self.assertEqual(kappa_screen(first, worlds)["screen_id"], "q_stab0")
        self.assertTrue(self.payload["ranking"]["relabel_natural"])
        self.assertTrue(all(row["natural"] for row in self.payload["relabels"]))

    def test_ranking_follows_the_preregistered_rule(self) -> None:
        ranking = self.payload["ranking"]
        if ranking["cheap_is_function"] and ranking["screen_exact"]:
            self.assertEqual(ranking["verdict"], "calculus_holds")
        elif (
            (not ranking["cheap_is_function"])
            and ranking["screen_exact"]
            and ranking["uniqueness_fails"]
            and ranking["noncommute"]
        ):
            self.assertEqual(ranking["verdict"], "calculus_is_sic")
        else:
            self.assertEqual(ranking["verdict"], "no_function")

    def test_deterministic_replay(self) -> None:
        first = self.payload
        second = evaluate_benchmark()
        self.assertEqual(first["ranking"], second["ranking"])
        self.assertEqual(first["collisions"], second["collisions"])
        self.assertEqual(first["cases"], second["cases"])
