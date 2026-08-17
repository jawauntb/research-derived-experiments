from __future__ import annotations

import unittest

from experiments.eml_us4_gradient.core import SINGLETON, ZERO_ONES, ZERO_X
from experiments.eml_us4_search.core import SEARCH_K, evaluate_benchmark
from experiments.eml_variable_spectrum.core import enumerate_trees, labeled_count, parse_var


class EmlUs4SearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = evaluate_benchmark()

    def test_benchmark_records_a_ranking(self) -> None:
        payload = self.payload
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["US4S_ENUMERATION"])
        self.assertTrue(payload["gates"]["US4S_EXACT_CONTROL"])
        self.assertTrue(payload["gates"]["US4S_PERTURBED_CORRECT"])
        self.assertTrue(payload["gates"]["US4S_PROCESS_IS_NOT_GIBBS"])
        self.assertTrue(payload["gates"]["US4S_NOT_MATCHING_ONLY"])
        self.assertIn(payload["ranking"]["verdict"], {"phi_holds", "min_size_governs", "phi_killed"})
        self.assertIn("every size-3 skeleton", payload["process_disclosure"])

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

    def test_deterministic_replay(self) -> None:
        first = self.payload
        second = evaluate_benchmark()
        self.assertEqual(first["ranking"], second["ranking"])
        self.assertEqual(
            [(row["target"], row["n_gd_skeletons"], row["extra_skeletons"]) for row in first["searches"]],
            [(row["target"], row["n_gd_skeletons"], row["extra_skeletons"]) for row in second["searches"]],
        )
