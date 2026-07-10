from __future__ import annotations

from statistics import mean
import unittest

from experiments.commitment_surface.core import run_e1_cell
from experiments.commitment_surface.e1_misspecification_variance import (
    _pick_weighted,
    derive_assignment_seed,
    prepare_cell,
    quantile,
    run_randomization_audit,
    wilson_interval,
)


class E1MisspecificationVarianceTest(unittest.TestCase):
    def test_prepared_cell_exactly_reconstructs_original_selectors(self) -> None:
        prepared = prepare_cell(modulus=7, structural_seed=0, n_candidates=40)
        original = run_e1_cell(modulus=7, seed=0, n_candidates=40)

        self.assertAlmostEqual(
            prepared.unweighted_accuracy,
            original.unweighted_selector_acc,
        )
        self.assertAlmostEqual(
            prepared.original_misspec_gap,
            original.concern_misspec_selector_acc
            - original.unweighted_selector_acc,
        )
        self.assertEqual(len(prepared.candidate_masks), original.n_candidates)

    def test_weighted_pick_preserves_first_argmax_tie_breaking(self) -> None:
        candidates = (0b0011, 0b1100, 0b0101)
        self.assertEqual(_pick_weighted(candidates, 0, 10.0), 0)
        self.assertEqual(_pick_weighted(candidates, 0b1100, 10.0), 1)

    def test_namespaced_assignment_seeds_are_deterministic_and_unique(self) -> None:
        seeds = {
            derive_assignment_seed(202607092136, replicate, modulus, cell_seed)
            for replicate in range(4)
            for modulus in (7, 11)
            for cell_seed in range(3)
        }
        self.assertEqual(len(seeds), 24)
        self.assertEqual(
            derive_assignment_seed(202607092136, 2, 11, 1),
            derive_assignment_seed(202607092136, 2, 11, 1),
        )

    def test_small_audit_is_reproducible_and_preserves_assignments(self) -> None:
        cells = [
            prepare_cell(modulus=7, structural_seed=seed, n_candidates=20)
            for seed in range(2)
        ]
        observed = mean(cell.original_misspec_gap for cell in cells)
        kwargs = {
            "moduli": (7,),
            "structural_seeds": 2,
            "replicates": 32,
            "base_seed": 12345,
            "n_candidates": 20,
            "observed_gap": observed,
        }
        first = run_randomization_audit(**kwargs)
        second = run_randomization_audit(**kwargs)

        self.assertEqual(
            first["aggregate_replicate_gaps"],
            second["aggregate_replicate_gaps"],
        )
        checks = first["assumption_audit"]["checks"]
        self.assertTrue(checks["observed_gap_reconstruction_matches"])
        self.assertTrue(checks["structure_invariant"])
        self.assertTrue(checks["assignment_cardinality_preserved"])
        self.assertTrue(checks["derived_assignment_seeds_unique"])
        self.assertEqual(first["null_distribution"]["n"], 32)

    def test_quantile_and_wilson_boundaries(self) -> None:
        self.assertAlmostEqual(quantile([0.0, 10.0], 0.25), 2.5)
        low, high = wilson_interval(0, 100)
        self.assertEqual(low, 0.0)
        self.assertGreater(high, 0.0)
        self.assertLess(high, 0.05)


if __name__ == "__main__":
    unittest.main()
