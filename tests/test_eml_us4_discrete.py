from __future__ import annotations

import unittest

from experiments.eml_us4_discrete.core import (
    EXACT_THIN,
    EXACT_ZERO,
    SEARCH_K,
    evaluate_benchmark,
)
from experiments.eml_us4_gradient.core import SINGLETON, ZERO_ONES, ZERO_X
from experiments.eml_variable_spectrum.core import enumerate_trees, labeled_count, parse_var


class EmlUs4DiscreteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = evaluate_benchmark()

    def test_benchmark_records_an_extra_basin_ranking(self) -> None:
        payload = self.payload
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["US4D_ENUMERATION"])
        self.assertTrue(payload["gates"]["US4D_EXACT_CONTROL"])
        self.assertTrue(payload["gates"]["US4D_FROZEN_LEAVES"])
        self.assertTrue(payload["gates"]["US4D_NOT_GD"])
        self.assertIn(payload["ranking"]["verdict"], {"phi_holds", "min_size_governs", "phi_killed"})
        self.assertIn("n_extra_basins", payload["ranking"]["rule"])
        self.assertIn("flip one leaf", payload["process_disclosure"])
        self.assertIn("Not GD", payload["process_disclosure"])

    def test_size_three_census_is_complete(self) -> None:
        trees = enumerate_trees(SEARCH_K)[SEARCH_K]
        self.assertEqual(len(trees), 80)
        self.assertEqual(labeled_count(SEARCH_K), 80)
        pretties = {tree.pretty() for tree in trees}
        self.assertIn(ZERO_ONES, pretties)
        self.assertIn(ZERO_X, pretties)
        self.assertIn(SINGLETON, pretties)
        self.assertEqual(parse_var(ZERO_ONES).n_internal, 3)
        self.assertEqual(parse_var(SINGLETON).n_internal, 3)

    def test_exact_control_is_two_versus_one(self) -> None:
        payload = self.payload
        by_name = {row["target"]: row for row in payload["searches"]}
        self.assertEqual(by_name["zero"]["n_exact"], 2)
        self.assertEqual(by_name["thin"]["n_exact"], 1)
        self.assertEqual(tuple(by_name["zero"]["exact_formulas"]), EXACT_ZERO)
        self.assertEqual(tuple(by_name["thin"]["exact_formulas"]), EXACT_THIN)

    def test_ranking_uses_extras_not_exact_totals(self) -> None:
        ranking = self.payload["ranking"]
        by_name = {row["target"]: row for row in self.payload["searches"]}
        self.assertEqual(ranking["zero_extra"], by_name["zero"]["n_extra_basins"])
        self.assertEqual(ranking["thin_extra"], by_name["thin"]["n_extra_basins"])
        self.assertEqual(ranking["zero_basins"], by_name["zero"]["n_basins"])
        self.assertEqual(ranking["thin_basins"], by_name["thin"]["n_basins"])
        if ranking["zero_extra"] == ranking["thin_extra"]:
            self.assertEqual(ranking["verdict"], "min_size_governs")
        elif ranking["zero_extra"] > ranking["thin_extra"]:
            self.assertEqual(ranking["verdict"], "phi_holds")
        else:
            self.assertEqual(ranking["verdict"], "phi_killed")
        self.assertGreater(ranking["zero_extra"], ranking["thin_extra"])
        self.assertEqual(ranking["zero_extra"], 43)
        self.assertEqual(ranking["thin_extra"], 28)

    def test_extras_terminate_on_exact_formulas(self) -> None:
        by_name = {row["target"]: row for row in self.payload["searches"]}
        zero_exact = set(EXACT_ZERO)
        thin_exact = set(EXACT_THIN)
        self.assertEqual(set(by_name["zero"]["terminals"]), zero_exact)
        self.assertEqual(set(by_name["thin"]["terminals"]), thin_exact)
        self.assertEqual(sum(by_name["zero"]["extra_end_counts"].values()), 43)
        self.assertEqual(sum(by_name["thin"]["extra_end_counts"].values()), 28)
        self.assertTrue(set(by_name["zero"]["extra_end_counts"]).issubset(zero_exact))
        self.assertTrue(set(by_name["thin"]["extra_end_counts"]).issubset(thin_exact))

    def test_deterministic_replay(self) -> None:
        first = self.payload
        second = evaluate_benchmark()
        self.assertEqual(first["ranking"], second["ranking"])
        self.assertEqual(
            [(row["target"], row["n_basins"], row["n_extra_basins"], row["extra_end_counts"]) for row in first["searches"]],
            [(row["target"], row["n_basins"], row["n_extra_basins"], row["extra_end_counts"]) for row in second["searches"]],
        )
