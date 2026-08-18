from __future__ import annotations

import unittest

from experiments.delete_repair_generators.core import (
    EPISODES,
    denotation,
    enumerate_trees,
    evaluate_benchmark,
    tree_size,
)


class DeleteRepairGeneratorsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = evaluate_benchmark()

    def test_instrument_stays_valid_for_any_recorded_verdict(self) -> None:
        payload = self.payload
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["GEN_TWO_EPISODES"])
        self.assertTrue(payload["gates"]["GEN_SHARED_UNIVERSES"])
        self.assertTrue(payload["gates"]["GEN_REGISTERED_MINS"])
        self.assertTrue(payload["gates"]["GEN_ROUND_TRIPS"])
        self.assertIn(
            payload["ranking"]["verdict"],
            {"border_consolidated", "border_sharpened", "inconclusive"},
        )

    def test_sq_episode_replays_the_banked_numbers(self) -> None:
        sq = next(e for e in self.payload["episodes"] if e["episode_id"] == "sq_x4")
        self.assertEqual(sq["min_size_base"], 7)
        self.assertEqual(sq["min_size_ext"], 3)
        self.assertEqual(sq["mass_base"], 5)
        self.assertEqual(sq["mass_ext"], 14)
        self.assertTrue(sq["outside_fact"])

    def test_cube_episode_matches_registered_predictions(self) -> None:
        cube = next(e for e in self.payload["episodes"] if e["episode_id"] == "cube_x3")
        self.assertEqual(cube["min_size_base"], 5)
        self.assertEqual(cube["min_size_ext"], 2)
        self.assertEqual(cube["mass_base"], 2)
        self.assertEqual(cube["mass_ext"], 3)
        self.assertTrue(cube["screens_all_invariant"])
        self.assertTrue(cube["outside_fact"])

    def test_verdict_follows_the_preregistered_rule(self) -> None:
        ranking = self.payload["ranking"]
        if ranking["n_outside_facts"] == ranking["n_episodes"]:
            self.assertEqual(ranking["verdict"], "border_consolidated")
        elif ranking["n_outside_facts"] == 1:
            self.assertEqual(ranking["verdict"], "border_sharpened")
        else:
            self.assertEqual(ranking["verdict"], "inconclusive")

    def test_enumeration_semantics_for_the_cube_grammar(self) -> None:
        spec = next(s for s in EPISODES if s["macro"] == "cube")
        ext = enumerate_trees(spec["size_bound"], macro="cube")
        cube_of_x = ("cube", ("x",))
        self.assertIn(cube_of_x, ext)
        self.assertEqual(denotation(cube_of_x, 3), 3)
        self.assertEqual(tree_size(cube_of_x), 2)
        base = enumerate_trees(spec["size_bound"], macro=None)
        self.assertNotIn(cube_of_x, base)
        mul_chain = ("mul", ("x",), ("mul", ("x",), ("x",)))
        self.assertEqual(denotation(mul_chain, 3), 3)
        self.assertEqual(tree_size(mul_chain), 5)
        self.assertIn(mul_chain, base)

    def test_deterministic_replay(self) -> None:
        second = evaluate_benchmark()
        self.assertEqual(self.payload["ranking"], second["ranking"])
        self.assertEqual(self.payload["episodes"], second["episodes"])
