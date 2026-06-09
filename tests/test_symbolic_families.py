from __future__ import annotations

import random
import unittest

from experiments.symbolic_weakness.families import (
    color_permutation_trial,
    cyclic_group,
    cyclic_prefix_trial,
    dihedral_group,
    dihedral_reflection_trial,
    equivariance_count,
    equivariance_count_with_action,
    ground_truth_from_invariant,
    parity_coset_trial,
)
from experiments.symbolic_weakness.selectors import (
    SELECTORS,
    consistent_metrics,
)


class FamiliesTest(unittest.TestCase):
    def test_cyclic_group_size(self) -> None:
        g = cyclic_group(7)
        self.assertEqual(len(g), 7)

    def test_dihedral_group_size(self) -> None:
        g = dihedral_group(7)
        self.assertEqual(len(g), 14)

    def test_equivariance_count_identity_is_full(self) -> None:
        from experiments.symbolic_weakness.families import Candidate

        identity = Candidate(
            name="identity",
            predictions=tuple(range(7)),
            form_length=1,
            family="invariant",
        )
        self.assertEqual(equivariance_count(identity, cyclic_group(7)), 7)
        self.assertEqual(
            equivariance_count_with_action(identity, cyclic_group(7), cyclic_group(7)),
            7,
        )

    def test_cyclic_invariant_is_full_orbit(self) -> None:
        trial = cyclic_prefix_trial(rng=random.Random(3), modulus=11, train_window=3)
        truth = ground_truth_from_invariant(trial)
        from experiments.symbolic_weakness.families import Candidate

        truth_cand = Candidate(
            name="truth",
            predictions=truth,
            form_length=5,
            family="invariant",
        )
        self.assertEqual(equivariance_count(truth_cand, trial.group), 11)

    def test_dihedral_invariant_is_full_group(self) -> None:
        trial = dihedral_reflection_trial(rng=random.Random(3), modulus=11, train_window=3)
        truth = ground_truth_from_invariant(trial)
        from experiments.symbolic_weakness.families import Candidate

        truth_cand = Candidate(
            name="truth",
            predictions=truth,
            form_length=6,
            family="invariant",
        )
        self.assertEqual(
            equivariance_count_with_action(truth_cand, trial.group, trial.group),
            22,
        )

    def test_color_permutation_trial_shape(self) -> None:
        trial = color_permutation_trial(rng=random.Random(3), domain_size=5, train_window=2)
        self.assertEqual(trial.domain_size, 5)
        self.assertEqual(len(trial.train_examples), 2)
        self.assertEqual(len(trial.ood_inputs), 3)

    def test_parity_coset_trial_shape(self) -> None:
        trial = parity_coset_trial(rng=random.Random(3), domain_size=8)
        self.assertEqual(trial.domain_size, 8)
        self.assertEqual(len(trial.train_examples), 4)
        self.assertEqual(len(trial.ood_inputs), 4)


class SelectorsTest(unittest.TestCase):
    def _expect_clean_separation(
        self, family_builder, expected_weakness_inv_rate: float
    ) -> None:
        rng = random.Random(11)
        invariant_hits = {s: 0 for s in SELECTORS}
        ood_sums = {s: 0.0 for s in SELECTORS}
        N = 40
        for seed in range(N):
            trial = family_builder(random.Random(seed))
            metrics = consistent_metrics(trial, rng)
            for s, f in SELECTORS.items():
                c = f(metrics, rng)
                invariant_hits[s] += int(c.family == "invariant")
                ood_sums[s] += c.ood_accuracy
        # weakness_oracle must reach the expected invariant-rate threshold.
        self.assertGreaterEqual(
            invariant_hits["weakness_oracle"] / N, expected_weakness_inv_rate
        )
        # Surface-statistic baselines should not select the invariant.
        for s in ("train_loss", "simplicity", "compression", "mdl_program", "flatness_proxy"):
            self.assertLessEqual(invariant_hits[s] / N, 0.05)
        # Wrong-group control must NOT systematically select the invariant.
        self.assertLessEqual(invariant_hits["weakness_wrong_group"] / N, 0.25)

    def test_cyclic_selector_gap(self) -> None:
        self._expect_clean_separation(
            lambda r: cyclic_prefix_trial(rng=r, modulus=11, train_window=3),
            expected_weakness_inv_rate=0.95,
        )

    def test_dihedral_selector_gap(self) -> None:
        self._expect_clean_separation(
            lambda r: dihedral_reflection_trial(rng=r, modulus=11, train_window=3),
            expected_weakness_inv_rate=0.95,
        )


if __name__ == "__main__":
    unittest.main()
