from __future__ import annotations

import unittest
from fractions import Fraction

from experiments.delete_repair_concern.core import (
    kappa_concern,
    representing_set_for_bag,
)
from experiments.delete_repair_concern_estimation.core import (
    REGISTERED_SEQUENCES,
    SEQ_BAG,
    SEQ_MIX,
    SEQ_PAIR,
    evaluate_benchmark,
    plugin_weights,
)
from experiments.delete_the_absolute.core import all_worlds


class DeleteRepairConcernEstimationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = evaluate_benchmark()

    def test_instrument_stays_valid_for_any_recorded_verdict(self) -> None:
        payload = self.payload
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["EST_SEQUENCES_REGISTERED"])
        self.assertTrue(payload["gates"]["EST_EXACT_ARITHMETIC"])
        self.assertTrue(payload["gates"]["EST_ORACLE_ANCHORS"])
        self.assertTrue(payload["gates"]["EST_CONVERGENCE_RECORDED"])
        self.assertTrue(payload["gates"]["EST_MISSPEC_RECORDED"])
        self.assertIn(
            payload["ranking"]["verdict"],
            {"estimation_works", "estimation_fails", "inconclusive"},
        )
        self.assertIn("Valence", payload["withheld"][0])

    def test_sequences_are_registered_literals(self) -> None:
        self.assertEqual(SEQ_BAG, ("bag",) * 24)
        self.assertEqual(SEQ_MIX, ("bag", "first_bit") * 12)
        self.assertEqual(SEQ_PAIR, ("bag", "pair_eq") * 12)
        self.assertEqual(len(REGISTERED_SEQUENCES), 3)
        for spec in REGISTERED_SEQUENCES:
            self.assertEqual(len(spec["draws"]), 24)

    def test_oracle_anchors_match_door3_banked_choices(self) -> None:
        worlds = all_worlds()
        candidates = representing_set_for_bag(worlds)
        banked = {"seq_bag": "q_perm", "seq_mix": "q_stab0", "seq_pair": "q_id"}
        for spec in REGISTERED_SEQUENCES:
            chosen, _costs = kappa_concern(spec["oracle_concern"], candidates, worlds)
            self.assertEqual(chosen, banked[spec["sequence_id"]])
            self.assertEqual(spec["oracle_choice"], banked[spec["sequence_id"]])
        for row in self.payload["sequences"]:
            self.assertTrue(row["oracle_anchor_ok"])

    def test_seq_bag_converges_at_registered_step_1(self) -> None:
        row = next(
            row for row in self.payload["sequences"] if row["sequence_id"] == "seq_bag"
        )
        self.assertEqual(row["registered_step"], 1)
        self.assertEqual(row["observed_step"], 1)
        self.assertTrue(row["step_matches_registered"])
        self.assertTrue(row["final_matches_oracle"])
        trace = [
            entry
            for entry in self.payload["trace"]
            if entry["sequence_id"] == "seq_bag"
        ]
        self.assertTrue(all(entry["matches_oracle"] for entry in trace))

    def test_seq_mix_converges_at_registered_step_2(self) -> None:
        row = next(
            row for row in self.payload["sequences"] if row["sequence_id"] == "seq_mix"
        )
        self.assertEqual(row["registered_step"], 2)
        self.assertEqual(row["observed_step"], 2)
        self.assertTrue(row["step_matches_registered"])
        trace = {
            entry["n"]: entry
            for entry in self.payload["trace"]
            if entry["sequence_id"] == "seq_mix"
        }
        self.assertEqual(trace[1]["plugin_choice"], "q_perm")
        self.assertFalse(trace[1]["matches_oracle"])
        for n in range(2, 25):
            self.assertEqual(trace[n]["plugin_choice"], "q_stab0")

    def test_seq_pair_converges_at_registered_step_6(self) -> None:
        row = next(
            row for row in self.payload["sequences"] if row["sequence_id"] == "seq_pair"
        )
        self.assertEqual(row["registered_step"], 6)
        self.assertEqual(row["observed_step"], 6)
        self.assertTrue(row["step_matches_registered"])
        trace = {
            entry["n"]: entry
            for entry in self.payload["trace"]
            if entry["sequence_id"] == "seq_pair"
        }
        for n in (1, 3, 5):
            self.assertEqual(trace[n]["plugin_choice"], "q_perm")
            self.assertFalse(trace[n]["matches_oracle"])
        for n in (2, 4):
            self.assertEqual(trace[n]["plugin_choice"], "q_id")
        for n in range(6, 25):
            self.assertEqual(trace[n]["plugin_choice"], "q_id")
        self.assertEqual(trace[5]["weights"]["pair_eq"], "2/5")
        self.assertEqual(trace[7]["weights"]["pair_eq"], "3/7")

    def test_full_trace_recorded_for_all_sequences(self) -> None:
        self.assertEqual(len(self.payload["trace"]), 72)
        for spec in REGISTERED_SEQUENCES:
            rows = [
                entry
                for entry in self.payload["trace"]
                if entry["sequence_id"] == spec["sequence_id"]
            ]
            self.assertEqual([entry["n"] for entry in rows], list(range(1, 25)))

    def test_misspec_gap_is_exactly_4(self) -> None:
        misspec = self.payload["misspec"]
        self.assertEqual(misspec["foreign_choice"], "q_stab0")
        self.assertEqual(misspec["oracle_choice"], "q_id")
        self.assertEqual(Fraction(misspec["cost_foreign"]), Fraction(20))
        self.assertEqual(Fraction(misspec["cost_oracle"]), Fraction(16))
        self.assertEqual(Fraction(misspec["gap"]), Fraction(4))
        self.assertEqual(self.payload["ranking"]["misspec_gap"], "4")

    def test_plugin_weights_are_exact_frequencies(self) -> None:
        weights = dict(plugin_weights(SEQ_PAIR, 5))
        self.assertEqual(weights, {"bag": Fraction(3, 5), "pair_eq": Fraction(2, 5)})
        self.assertEqual(dict(plugin_weights(SEQ_BAG, 7)), {"bag": Fraction(1)})

    def test_ranking_follows_the_preregistered_rule(self) -> None:
        ranking = self.payload["ranking"]
        if ranking["all_steps_match_registered"] and ranking["all_finals_match_oracle"]:
            self.assertEqual(ranking["verdict"], "estimation_works")
        elif not ranking["all_finals_match_oracle"]:
            self.assertEqual(ranking["verdict"], "estimation_fails")
        else:
            self.assertEqual(ranking["verdict"], "inconclusive")

    def test_deterministic_replay(self) -> None:
        second = evaluate_benchmark()
        self.assertEqual(self.payload["ranking"], second["ranking"])
        self.assertEqual(self.payload["sequences"], second["sequences"])
        self.assertEqual(self.payload["trace"], second["trace"])
        self.assertEqual(self.payload["misspec"], second["misspec"])
