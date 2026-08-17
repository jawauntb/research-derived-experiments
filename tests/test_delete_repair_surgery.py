from __future__ import annotations

import unittest

from experiments.delete_repair_connection.core import AFFINE_A, AFFINE_B, kirchhoff_prediction, path_map
from experiments.delete_repair_surgery.core import (
    AFFINE_C,
    MENU,
    decide,
    evaluate_benchmark,
)


class DeleteRepairSurgeryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = evaluate_benchmark()

    def test_instrument_stays_valid_even_if_the_one_shot_rule_dies(self) -> None:
        payload = self.payload
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["SUR_ENUMERATION"])
        self.assertTrue(payload["gates"]["SUR_GOLD_DEFINED"])
        self.assertTrue(payload["gates"]["SUR_NAME_BLIND"])
        self.assertTrue(payload["gates"]["SUR_HELD_OUT_CONNECTION"])
        self.assertIn(payload["ranking"]["verdict"], {"surgery_holds", "surgery_killed"})
        self.assertIn("Not text nomination", payload["process_disclosure"])
        self.assertIn("LLM", payload["withheld"][1])

    def test_construction_is_disclosed_and_exact(self) -> None:
        ranking = self.payload["ranking"]
        self.assertEqual(ranking["construction_hits"], 4)
        self.assertEqual(ranking["construction_n"], 4)
        self.assertEqual(list(MENU), self.payload["menu"])

    def test_held_out_grain_miss_is_pair_eq_on_identity_screen(self) -> None:
        ranking = self.payload["ranking"]
        self.assertEqual(ranking["held_out_n"], 7)
        self.assertEqual(ranking["held_out_hits"], 6)
        self.assertFalse(ranking["held_out_exact"])
        self.assertTrue(ranking["pair_eq_id_is_the_grain_miss"])
        self.assertEqual(ranking["verdict"], "surgery_killed")
        pair_eq_id = next(
            row for row in self.payload["cases"] if row["case_id"] == "pair_eq_q_id"
        )
        self.assertEqual(pair_eq_id["gold"], "noop")
        self.assertEqual(pair_eq_id["policy"], "quotient")
        self.assertFalse(pair_eq_id["hit"])

    def test_policy_is_name_blind(self) -> None:
        pair_eq_id = next(
            row for row in self.payload["cases"] if row["case_id"] == "pair_eq_q_id"
        )
        identity = next(
            row for row in self.payload["cases"] if row["case_id"] == "identity_q_id"
        )
        self.assertEqual(decide(pair_eq_id["signature"]), "quotient")
        self.assertEqual(decide(identity["signature"]), "noop")
        self.assertNotIn("task_id", pair_eq_id["signature"])
        self.assertNotIn("screen_id", pair_eq_id["signature"])

    def test_held_out_affine_cycle_is_new_and_escapes_kirchhoff(self) -> None:
        self.assertNotEqual(AFFINE_C, AFFINE_A)
        self.assertNotEqual(AFFINE_C, AFFINE_B)
        self.assertNotEqual(path_map(AFFINE_C), kirchhoff_prediction(AFFINE_C))
        affine_c = next(
            row for row in self.payload["cases"] if row["case_id"] == "bag_q_perm_affine_c"
        )
        self.assertEqual(affine_c["gold"], "transport")
        self.assertTrue(affine_c["hit"])

    def test_ranking_follows_the_preregistered_rule(self) -> None:
        ranking = self.payload["ranking"]
        if ranking["held_out_exact"]:
            self.assertEqual(ranking["verdict"], "surgery_holds")
        else:
            self.assertEqual(ranking["verdict"], "surgery_killed")

    def test_deterministic_replay(self) -> None:
        first = self.payload
        second = evaluate_benchmark()
        self.assertEqual(first["ranking"], second["ranking"])
        self.assertEqual(first["cases"], second["cases"])
