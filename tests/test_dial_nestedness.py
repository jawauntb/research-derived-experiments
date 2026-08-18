from __future__ import annotations

import unittest
from fractions import Fraction

from experiments.dial_nestedness.core import (
    all_partitions,
    evaluate_benchmark,
    level_partition,
    partition_distortion,
    refines,
)


class DialNestednessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = evaluate_benchmark()

    def test_instrument_stays_valid_for_any_recorded_verdict(self) -> None:
        payload = self.payload
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["NEST_ENUMERATION_COMPLETE"])
        self.assertTrue(payload["gates"]["NEST_RATE_MONOTONE"])
        self.assertTrue(payload["gates"]["NEST_D0_IS_LEVELS"])
        self.assertIn(
            payload["ranking"]["verdict"],
            {
                "nestedness_fails_generally",
                "nestedness_holds_here",
                "inconclusive",
            },
        )

    def test_enumeration_is_bell_5(self) -> None:
        partitions = all_partitions()
        self.assertEqual(len(partitions), 52)
        self.assertEqual(len(set(partitions)), 52)

    def test_rates_match_registration(self) -> None:
        ranking = self.payload["ranking"]
        self.assertEqual(ranking["rates"], [5, 3, 2, 2, 1])
        self.assertTrue(ranking["rates_match_registered"])
        self.assertTrue(ranking["rate_monotone"])

    def test_d0_optimizer_is_the_level_partition_uniquely(self) -> None:
        row0 = self.payload["budget_rows"][0]
        self.assertEqual(row0["optimal_rate"], 5)
        self.assertEqual(row0["n_optimizers"], 1)
        self.assertEqual(
            row0["optimizers"][0],
            [list(cell) for cell in level_partition()],
        )

    def test_all_optimizer_nesting_fails_with_witness(self) -> None:
        ranking = self.payload["ranking"]
        self.assertFalse(ranking["all_nested"])
        witness = ranking["nest_witness"]
        self.assertIsNotNone(witness)
        assert witness is not None
        fine = tuple(tuple(cell) for cell in witness["fine_optimizer"])
        coarse = tuple(tuple(cell) for cell in witness["coarse_optimizer"])
        self.assertFalse(refines(fine, coarse))
        self.assertLessEqual(
            partition_distortion(fine),
            Fraction(witness["budget_fine"]),
        )
        self.assertLessEqual(
            partition_distortion(coarse),
            Fraction(witness["budget_coarse"]),
        )

    def test_a_chosen_chain_nests(self) -> None:
        ranking = self.payload["ranking"]
        self.assertTrue(ranking["chain_exists"])
        chain = ranking["chain"]
        self.assertIsNotNone(chain)
        assert chain is not None
        self.assertEqual(len(chain), 5)
        for i in range(len(chain) - 1):
            fine = tuple(tuple(cell) for cell in chain[i])
            coarse = tuple(tuple(cell) for cell in chain[i + 1])
            self.assertTrue(refines(fine, coarse))

    def test_verdict_follows_the_preregistered_rule(self) -> None:
        ranking = self.payload["ranking"]
        if ranking["rate_monotone"] and not ranking["all_nested"]:
            self.assertEqual(ranking["verdict"], "nestedness_fails_generally")
        elif ranking["rate_monotone"] and ranking["all_nested"]:
            self.assertEqual(ranking["verdict"], "nestedness_holds_here")
        else:
            self.assertEqual(ranking["verdict"], "inconclusive")

    def test_deterministic_replay(self) -> None:
        second = evaluate_benchmark()
        self.assertEqual(self.payload["ranking"], second["ranking"])
        self.assertEqual(self.payload["budget_rows"], second["budget_rows"])
