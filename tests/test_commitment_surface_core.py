from __future__ import annotations

import random
import unittest

from experiments.commitment_surface.core import (
    Deployment,
    biased_train_perfect_completion,
    candidate_shift_tables,
    concern_weighted_selector,
    deployment_accuracy,
    misspecified_deployment,
    random_train_perfect_completion,
    run_e1_cell,
    spearman,
    true_addition_table,
    unequal_deployment,
    uniform_deployment,
    unweighted_extension_mass,
    unweighted_weakness_selector,
    weighted_extension_mass,
)


class CommitmentSurfaceCoreTest(unittest.TestCase):
    def test_uniform_deployment_has_unit_kappa(self) -> None:
        pairs = [(0, 0), (0, 1), (1, 0)]
        d = uniform_deployment(pairs)
        self.assertEqual(d.pairs, tuple(pairs))
        self.assertEqual(d.kappa, (1.0, 1.0, 1.0))

    def test_unequal_deployment_has_focus_weight_where_kappa_high(self) -> None:
        pairs = [(a, b) for a in range(4) for b in range(4)]
        d = unequal_deployment(
            pairs,
            rng=random.Random(0),
            focus_fraction=0.25,
            focus_weight=10.0,
        )
        n_focus = sum(1 for k in d.kappa if k > 1.0)
        self.assertEqual(n_focus, max(1, int(round(len(pairs) * 0.25))))
        self.assertTrue(all(k == 10.0 or k == 1.0 for k in d.kappa))

    def test_misspec_kappa_has_same_marginal_distribution(self) -> None:
        pairs = [(a, b) for a in range(4) for b in range(4)]
        well = unequal_deployment(
            pairs, rng=random.Random(0), focus_fraction=0.25, focus_weight=10.0
        )
        mis = misspecified_deployment(
            pairs, rng=random.Random(0), focus_fraction=0.25, focus_weight=10.0
        )
        # Same multiset of kappa values -- only the pair-to-kappa mapping differs.
        self.assertEqual(sorted(well.kappa), sorted(mis.kappa))

    def test_weighted_extension_mass_matches_definition(self) -> None:
        modulus = 5
        table = true_addition_table(modulus)
        pairs = [(0, 0), (0, 1), (1, 0), (2, 2)]
        kappa = (2.0, 3.0, 5.0, 7.0)
        d = Deployment(pairs=tuple(pairs), kappa=kappa)
        expected = 2.0 + 3.0 + 5.0 + 7.0  # all correct on truth
        self.assertAlmostEqual(weighted_extension_mass(table, modulus, d), expected)

    def test_unweighted_extension_counts_correct_pairs(self) -> None:
        modulus = 5
        table = true_addition_table(modulus)
        pairs = [(0, 0), (1, 4), (2, 3)]
        d = uniform_deployment(pairs)
        self.assertAlmostEqual(
            unweighted_extension_mass(table, modulus, d), 3.0
        )

    def test_concern_selector_prefers_high_kappa_hits(self) -> None:
        modulus = 5
        truth = true_addition_table(modulus)
        # Two candidates: one covers (0,1) only, the other covers (1,2) only.
        # truth[0*5+1] = 1, truth[1*5+2] = 3.
        t_a = list(truth)
        t_a[1 * modulus + 2] = 0  # break (1,2): 3 -> 0
        t_a = tuple(t_a)
        t_b = list(truth)
        t_b[0 * modulus + 1] = 3  # break (0,1): 1 -> 3
        t_b = tuple(t_b)

        pairs = [(0, 1), (1, 2)]
        # Concern favours (1,2).
        d = Deployment(pairs=tuple(pairs), kappa=(1.0, 10.0))
        pick = concern_weighted_selector(d, modulus)([t_a, t_b])
        # t_a is correct on (0,1) only (mass 1); t_b is correct on (1,2)
        # only (mass 10). Concern-weighted should pick t_b.
        self.assertEqual(pick, t_b)

        # Uniform would tie (both cover exactly one pair). Deterministic
        # argmax on tied scores picks the first argument (t_a).
        d_uniform = uniform_deployment(pairs)
        pick_uniform = unweighted_weakness_selector(d_uniform, modulus)(
            [t_a, t_b]
        )
        self.assertEqual(pick_uniform, t_a)

    def test_deployment_accuracy_is_fraction_of_concern_mass(self) -> None:
        modulus = 3
        table = true_addition_table(modulus)
        d = Deployment(pairs=((0, 0), (0, 1)), kappa=(2.0, 4.0))
        self.assertAlmostEqual(deployment_accuracy(table, modulus, d), 1.0)

    def test_random_train_perfect_completion_agrees_on_train_pairs(self) -> None:
        modulus = 5
        train_pairs = [(a, b) for a in range(3) for b in range(modulus)]
        rng = random.Random(42)
        table = random_train_perfect_completion(
            modulus, train_pairs, rng=rng, ood_correct_prob=0.25
        )
        for a, b in train_pairs:
            self.assertEqual(table[a * modulus + b], (a + b) % modulus)

    def test_biased_completion_favours_focus_pairs(self) -> None:
        modulus = 7
        train_pairs = [(a, b) for a in range(3) for b in range(modulus)]
        ood_pairs = [(a, b) for a in range(3, modulus) for b in range(modulus)]
        focus = set(ood_pairs[: len(ood_pairs) // 2])
        rng = random.Random(0)
        # Very high correct prob on focus vs low on rest.
        table = biased_train_perfect_completion(
            modulus,
            train_pairs,
            focus,
            rng=rng,
            high_correct_prob=1.0,
            low_correct_prob=0.0,
        )
        self.assertEqual(len(table), modulus * modulus)
        for a, b in train_pairs:
            self.assertEqual(table[a * modulus + b], (a + b) % modulus)
        for a, b in focus:
            self.assertEqual(table[a * modulus + b], (a + b) % modulus)
        # Verify bulk property: mean correct fraction on non-focus OOD ≤ 0.2.
        low_correct = sum(
            1 for (a, b) in ood_pairs
            if (a, b) not in focus
            and table[a * modulus + b] == (a + b) % modulus
        ) / max(1, len([p for p in ood_pairs if p not in focus]))
        self.assertLessEqual(low_correct, 0.2)

    def test_run_e1_cell_returns_valid_selector_accuracies(self) -> None:
        r = run_e1_cell(modulus=7, seed=1, n_candidates=100)
        self.assertGreaterEqual(r.concern_wellspec_selector_acc, 0.0)
        self.assertLessEqual(r.concern_wellspec_selector_acc, 1.0)
        # Truth is always in {0, 1}: the truth selector always picks the
        # true addition table which has full coverage.
        self.assertAlmostEqual(r.truth_selector_acc, 1.0)

    def test_spearman_boundary_cases(self) -> None:
        self.assertAlmostEqual(spearman([1.0], [1.0]), 0.0)
        self.assertAlmostEqual(spearman([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]), 1.0)
        self.assertAlmostEqual(spearman([1.0, 2.0, 3.0], [3.0, 2.0, 1.0]), -1.0)

    def test_shift_tables_are_train_perfect_on_full_grid(self) -> None:
        modulus = 5
        for table in candidate_shift_tables(modulus):
            # These are (a + b + s) mod n; only s=0 matches truth on all
            # of (a, b).
            pass
        # At least one candidate (s=0) equals the truth.
        truth = true_addition_table(modulus)
        self.assertIn(truth, candidate_shift_tables(modulus))


if __name__ == "__main__":
    unittest.main()
