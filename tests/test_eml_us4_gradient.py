from __future__ import annotations

import math
import unittest

from experiments.eml_us4_gradient.core import (
    SINGLETON,
    ZERO_ONES,
    ZERO_X,
    apply_ranking,
    evaluate_benchmark,
    n_weight_leaves,
    target_grid,
)
from experiments.eml_variable_spectrum.core import parse_var


class EmlUs4GradientTest(unittest.TestCase):
    def test_targets_are_registered_before_ranking(self) -> None:
        zero = parse_var(ZERO_ONES)
        singleton = parse_var(SINGLETON)
        x_zero = parse_var(ZERO_X)
        self.assertEqual(zero.n_internal, 3)
        self.assertEqual(singleton.n_internal, 3)
        self.assertEqual(x_zero.n_internal, 3)
        self.assertTrue(all(math.isclose(value, 0.0, abs_tol=1e-12) for value in target_grid(ZERO_ONES)))
        self.assertTrue(all(math.isclose(value, 0.0, abs_tol=1e-12) for value in target_grid(ZERO_X)))
        singleton_grid = target_grid(SINGLETON)
        self.assertFalse(all(abs(value) < 1e-9 for value in singleton_grid))
        expected = math.e - math.log(math.e - 1.0)
        for value in singleton_grid:
            self.assertAlmostEqual(value, expected, places=12)
        self.assertEqual(n_weight_leaves(zero), 4)
        self.assertEqual(n_weight_leaves(singleton), 4)
        self.assertEqual(n_weight_leaves(x_zero), 2)

    def test_process_is_master_formula_gd_not_gibbs(self) -> None:
        payload = evaluate_benchmark()
        disclosure = payload["process_disclosure"]
        self.assertIn("gradient descent on a master formula", disclosure)
        self.assertIn("not a Gibbs sampler", disclosure)
        self.assertIn("not Odrzywołek's neural bootstrap", disclosure)
        self.assertTrue(payload["gates"]["US4G_PROCESS_IS_NOT_GIBBS_SAMPLER"])
        self.assertTrue(payload["gates"]["US4G_CLAIM_BOUNDARY"])
        self.assertEqual(payload["registered"]["process"], "master_formula_gd")

    def test_ranking_rule_is_applied_not_peeked(self) -> None:
        payload = evaluate_benchmark()
        ranking = payload["ranking"]
        zero = ranking["zero_successes"]
        singleton = ranking["singleton_successes"]
        expected = apply_ranking(zero, singleton, payload["gates"]["US4G_PERTURBED_CORRECT"])
        self.assertEqual(ranking["verdict"], expected["verdict"])
        self.assertEqual(ranking["claim"], expected["claim"])
        self.assertIn(ranking["claim"], {"supported", "rejected", "withheld"})
        self.assertIn(
            ranking["verdict"],
            {"phi_holds", "min_size_governs", "phi_killed", "withheld_optimizer"},
        )
        if ranking["verdict"] == "min_size_governs":
            self.assertEqual(zero, singleton)
            self.assertEqual(ranking["claim"], "rejected")
        if ranking["verdict"] == "phi_holds":
            self.assertGreaterEqual(zero, singleton + ranking["margin"])
        if ranking["verdict"] == "phi_killed":
            self.assertGreater(singleton, zero)

    def test_deterministic_replay(self) -> None:
        first = evaluate_benchmark()
        second = evaluate_benchmark()
        self.assertEqual(first["ranking"], second["ranking"])
        self.assertEqual(first["recoveries"], second["recoveries"])
        self.assertTrue(first["gates"]["US4G_DETERMINISTIC"])

    def test_perturbed_correct_is_noncompensatory(self) -> None:
        payload = evaluate_benchmark()
        self.assertTrue(payload["gates"]["US4G_PERTURBED_CORRECT"])
        self.assertTrue(payload["gates"]["US4G_TARGETS_REGISTERED"])
        self.assertEqual(payload["status"], "pass")
        perturbed = next(row for row in payload["recoveries"] if row["mode"] == "perturbed_correct")
        self.assertGreaterEqual(perturbed["n_success"], 1)
        if not payload["gates"]["US4G_PERTURBED_CORRECT"]:
            self.assertEqual(payload["ranking"]["claim"], "withheld")
