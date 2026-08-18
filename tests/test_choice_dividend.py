from __future__ import annotations

import unittest
from fractions import Fraction

from experiments.choice_dividend.core import (
    EVEN_REGION,
    ODD_REGION,
    POPCOUNT_GE2_REGION,
    REGISTERED_TASKS,
    WORLDS,
    best_of_k_gains,
    choice_dividend,
    evaluate_benchmark,
    popcount,
    uniform_expectation,
)


class ChoiceDividendTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = evaluate_benchmark()

    def test_instrument_stays_valid_for_any_recorded_verdict(self) -> None:
        payload = self.payload
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["DIV_SINGLETON_ZERO"])
        self.assertTrue(payload["gates"]["DIV_FLAT_ZERO"])
        self.assertTrue(payload["gates"]["DIV_WIDE_POSITIVE"])
        self.assertTrue(payload["gates"]["DIV_EXACT_ARITHMETIC"])
        self.assertTrue(payload["gates"]["DIV_RANKING_RECORDED"])
        self.assertTrue(payload["gates"]["DIV_CLAIM_BOUNDARY"])
        self.assertIn(
            payload["ranking"]["verdict"],
            {"dividend_confirmed", "dividend_refuted", "inconclusive"},
        )
        self.assertIn("Valence", payload["withheld"][0])
        self.assertIn("learner half", payload["withheld"][1])

    def test_task_table_is_the_registered_literal(self) -> None:
        self.assertEqual(WORLDS, tuple(range(16)))
        self.assertEqual(EVEN_REGION, (0, 2, 4, 6, 8, 10, 12, 14))
        self.assertEqual(ODD_REGION, (1, 3, 5, 7, 9, 11, 13, 15))
        self.assertEqual(
            POPCOUNT_GE2_REGION, (3, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15)
        )
        self.assertEqual(len(REGISTERED_TASKS), 5)
        by_id = {spec["task_id"]: spec for spec in REGISTERED_TASKS}
        self.assertEqual(by_id["singleton_5"]["region"], (5,))
        self.assertEqual(by_id["singleton_12"]["region"], (12,))
        self.assertEqual(
            by_id["popcount_ge2"]["values"],
            tuple(
                Fraction(popcount(x) * 4 - (x % 3)) for x in POPCOUNT_GE2_REGION
            ),
        )
        self.assertEqual(
            by_id["odd_flat"]["values"], tuple(Fraction(5) for _ in range(8))
        )

    def test_each_dividend_is_exactly_the_registered_value(self) -> None:
        rows = {row["task_id"]: row for row in self.payload["tasks"]}
        expected = {
            "singleton_5": Fraction(0),
            "singleton_12": Fraction(0),
            "even_worlds": Fraction(7),
            "popcount_ge2": Fraction(73, 11),
            "odd_flat": Fraction(0),
        }
        for task_id, value in expected.items():
            self.assertEqual(Fraction(rows[task_id]["dividend"]), value)
            self.assertTrue(rows[task_id]["dividend_matches_registered"])
        self.assertEqual(
            self.payload["ranking"]["dividends"],
            {
                "singleton_5": "0",
                "singleton_12": "0",
                "even_worlds": "7",
                "popcount_ge2": "73/11",
                "odd_flat": "0",
            },
        )

    def test_singleton_tasks_have_all_zero_gains(self) -> None:
        rows = {row["task_id"]: row for row in self.payload["tasks"]}
        for task_id in ("singleton_5", "singleton_12"):
            row = rows[task_id]
            self.assertEqual(row["region_size"], 1)
            self.assertEqual(row["gains"], ["0"])
            self.assertTrue(row["final_gain_equals_dividend"])

    def test_even_worlds_gain_curve_is_exact(self) -> None:
        row = next(
            row for row in self.payload["tasks"] if row["task_id"] == "even_worlds"
        )
        self.assertEqual(row["uniform_expectation"], "7")
        self.assertEqual(row["best_value"], "14")
        self.assertEqual(
            row["gains"], ["-7", "-5", "-3", "-1", "1", "3", "5", "7"]
        )
        self.assertEqual(row["gain_first"], "-7")
        self.assertLess(Fraction(row["gain_first"]), 0)
        self.assertTrue(row["gains_weakly_increasing"])
        self.assertTrue(row["final_gain_equals_dividend"])

    def test_popcount_ge2_gain_curve_is_exact(self) -> None:
        row = next(
            row for row in self.payload["tasks"] if row["task_id"] == "popcount_ge2"
        )
        self.assertEqual(row["region_size"], 11)
        self.assertEqual(row["uniform_expectation"], "103/11")
        self.assertEqual(row["best_value"], "16")
        self.assertEqual(
            row["gains"],
            ["-15/11"] * 3 + ["18/11"] * 7 + ["73/11"],
        )
        self.assertLess(Fraction(row["gain_first"]), 0)
        self.assertTrue(row["gains_weakly_increasing"])
        self.assertTrue(row["final_gain_equals_dividend"])

    def test_flat_task_has_no_positive_gain_anywhere(self) -> None:
        row = next(
            row for row in self.payload["tasks"] if row["task_id"] == "odd_flat"
        )
        self.assertEqual(row["region_size"], 8)
        self.assertEqual(row["gains"], ["0"] * 8)
        for gain in row["gains"]:
            self.assertLessEqual(Fraction(gain), 0)
        self.assertTrue(row["final_gain_equals_dividend"])

    def test_dividend_helpers_match_the_direct_definition(self) -> None:
        values = tuple(Fraction(popcount(x) * 4 - (x % 3)) for x in POPCOUNT_GE2_REGION)
        self.assertEqual(uniform_expectation(values), Fraction(103, 11))
        self.assertEqual(choice_dividend(values), Fraction(73, 11))
        gains = best_of_k_gains(values)
        self.assertEqual(len(gains), 11)
        self.assertEqual(gains[-1], Fraction(73, 11))

    def test_ranking_follows_the_preregistered_rule(self) -> None:
        ranking = self.payload["ranking"]
        rows = {row["task_id"]: row for row in self.payload["tasks"]}
        zero_case_positive = any(
            Fraction(rows[task_id]["dividend"]) > 0
            for task_id in ("singleton_5", "singleton_12", "odd_flat")
        )
        wide_misses = any(
            not rows[task_id]["final_gain_equals_dividend"]
            for task_id in ("even_worlds", "popcount_ge2")
        )
        if ranking["singleton_zero"] and ranking["flat_zero"] and ranking["wide_positive"]:
            self.assertEqual(ranking["verdict"], "dividend_confirmed")
        elif zero_case_positive or wide_misses:
            self.assertEqual(ranking["verdict"], "dividend_refuted")
        else:
            self.assertEqual(ranking["verdict"], "inconclusive")

    def test_deterministic_replay(self) -> None:
        second = evaluate_benchmark()
        self.assertEqual(self.payload["ranking"], second["ranking"])
        self.assertEqual(self.payload["tasks"], second["tasks"])
