from __future__ import annotations

import random
import unittest

from experiments.symbolic_weakness.experiment import (
    choose_compression,
    choose_simplicity,
    choose_weakness,
    consistent_metrics,
    global_shift_candidate,
    local_prefix_patch_candidate,
    make_trial,
    metrics_for,
    run_trial,
    translation_equivariance_count,
)


class SymbolicWeaknessTest(unittest.TestCase):
    def test_global_shift_is_translation_equivariant(self) -> None:
        candidate = global_shift_candidate(modulus=7, offset=2)

        self.assertEqual(translation_equivariance_count(candidate, 7), 7)

    def test_local_prefix_patch_fits_train_but_breaks_equivariance(self) -> None:
        trial = make_trial(rng=random.Random(4), modulus=7, train_window=3)
        candidate = local_prefix_patch_candidate(trial)
        metrics = metrics_for(candidate, trial)

        self.assertEqual(metrics.train_accuracy, 1.0)
        self.assertLess(metrics.ood_accuracy, 1.0)
        self.assertLess(metrics.equivariance_count, trial.modulus)

    def test_simplicity_and_compression_choose_local_patch(self) -> None:
        trial = make_trial(rng=random.Random(4), modulus=7, train_window=3)
        metrics = consistent_metrics(trial)

        simple = choose_simplicity(metrics, random.Random(1))
        compressed = choose_compression(metrics, random.Random(1))

        self.assertEqual(simple.family, "local_patch")
        self.assertEqual(compressed.family, "local_patch")

    def test_weakness_chooses_invariant_shift(self) -> None:
        trial = make_trial(rng=random.Random(4), modulus=7, train_window=3)
        metrics = consistent_metrics(trial)

        chosen = choose_weakness(metrics, random.Random(1))

        self.assertEqual(chosen.family, "invariant")
        self.assertEqual(chosen.ood_accuracy, 1.0)

    def test_run_trial_exposes_selector_gap(self) -> None:
        trial = make_trial(rng=random.Random(4), modulus=7, train_window=3)
        rows = run_trial(trial=trial, rng=random.Random(1))
        by_selector = {row.selector: row for row in rows}

        self.assertEqual(by_selector["simplicity"].family, "local_patch")
        self.assertEqual(by_selector["compression"].family, "local_patch")
        self.assertEqual(by_selector["weakness"].family, "invariant")
        self.assertLess(by_selector["simplicity"].ood_accuracy, 1.0)
        self.assertEqual(by_selector["weakness"].ood_accuracy, 1.0)


if __name__ == "__main__":
    unittest.main()
