from __future__ import annotations

import unittest

from experiments.delete_repair_disanalogy.core import (
    DIAMOND,
    GRID,
    diamond_embeddings,
    evaluate_benchmark,
    grid_points,
    interval,
    is_causal,
    poset_of,
)
from experiments.delete_the_absolute.core import all_worlds, is_representable


class DeleteRepairDisanalogyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = evaluate_benchmark()

    def test_instrument_stays_valid_even_if_identification_reopens(self) -> None:
        payload = self.payload
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["DIS_ENUMERATION"])
        self.assertTrue(payload["gates"]["DIS_GRID"])
        self.assertTrue(payload["gates"]["DIS_PE_TYPED"])
        self.assertIn(
            payload["ranking"]["verdict"],
            {"disanalogy_holds", "identification_reopened"},
        )
        self.assertIn("Not a functor", payload["process_disclosure"])
        self.assertIn("functor", payload["withheld"][0])

    def test_grid_and_diamond_census(self) -> None:
        points = grid_points()
        self.assertEqual(len(points), GRID * GRID)
        self.assertEqual(len(set(points)), 16)
        diamonds = diamond_embeddings()
        self.assertEqual(len(diamonds), 196)
        self.assertTrue(all(poset_of(item) == DIAMOND for item in diamonds))
        lorentz = self.payload["lorentz_lamport"]
        self.assertEqual(lorentz["n_diamond"], 196)
        self.assertEqual(lorentz["n_injections"], 43680)

    def test_poset_does_not_fix_the_interval(self) -> None:
        lorentz = self.payload["lorentz_lamport"]
        self.assertEqual(lorentz["distinct_s2"], [-8, -4, -3, -1])
        self.assertEqual(lorentz["n_by_s2"], {"-1": 128, "-3": 32, "-4": 32, "-8": 4})
        self.assertTrue(lorentz["concurrency_constant"])
        first, second = lorentz["witnesses"][0], lorentz["witnesses"][1]
        self.assertNotEqual(first["s2_e1_e2"], second["s2_e1_e2"])
        a = tuple(tuple(event) for event in first["points"])
        b = tuple(tuple(event) for event in second["points"])
        self.assertEqual(poset_of(a), DIAMOND)
        self.assertEqual(poset_of(b), DIAMOND)
        self.assertEqual(interval(a[1], a[2]), first["s2_e1_e2"])
        self.assertFalse(is_causal(a[1], a[2]))
        self.assertFalse(is_causal(a[2], a[1]))

    def test_pe_cell_is_the_disclosed_prior(self) -> None:
        worlds = all_worlds()
        self.assertTrue(is_representable(worlds, "q_stab0", "first_bit"))
        self.assertFalse(is_representable(worlds, "q_perm", "first_bit"))
        pe = self.payload["pe"]
        self.assertIn("delete_the_absolute", pe["source"])
        self.assertTrue(pe["typed_representable"])
        self.assertFalse(pe["crossed_representable"])

    def test_ranking_follows_the_preregistered_rule(self) -> None:
        ranking = self.payload["ranking"]
        expected = (
            ranking["poset_does_not_fix_metric"]
            and ranking["poset_fixes_concurrency"]
            and ranking["pe_quotient_fails"]
            and ranking["pe_typed_works"]
        )
        if expected:
            self.assertEqual(ranking["verdict"], "disanalogy_holds")
        else:
            self.assertEqual(ranking["verdict"], "identification_reopened")

    def test_deterministic_replay(self) -> None:
        first = self.payload
        second = evaluate_benchmark()
        self.assertEqual(first["ranking"], second["ranking"])
        self.assertEqual(first["lorentz_lamport"], second["lorentz_lamport"])
