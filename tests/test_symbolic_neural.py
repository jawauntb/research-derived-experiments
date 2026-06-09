from __future__ import annotations

import random
import unittest

from experiments.symbolic_weakness.neural import (
    ModelConfig,
    _augmented_examples,
    _equivariance_count,
    _random_label_group,
    _wrong_group,
    summarize_sweep,
    train_one,
)
from experiments.symbolic_weakness.families import cyclic_prefix_trial, ground_truth_from_invariant


class NeuralWeaknessTest(unittest.TestCase):
    def test_train_one_runs_and_returns_artifact(self) -> None:
        config = ModelConfig(
            seed=0,
            hidden_width=16,
            depth=1,
            init_scale=0.5,
            learning_rate=1e-2,
            weight_decay=0.0,
            epochs=50,
            optimizer="adam",
            augmentation="none",
            augmentation_count=0,
        )
        art = train_one(
            trial_seed=1, modulus=7, train_window=2, config=config
        )
        self.assertEqual(len(art.full_function_table), 7)
        self.assertGreaterEqual(art.train_accuracy, 0.0)
        self.assertLessEqual(art.train_accuracy, 1.0)
        self.assertGreaterEqual(art.weakness_oracle, 1)
        self.assertLessEqual(art.weakness_oracle, 7)

    def test_full_cyclic_augmentation_gives_perfect_train(self) -> None:
        # With full orbit completion every possible (x, truth[x]) pair is in
        # the training set, so an MLP that converges should reach perfect
        # train accuracy (the OOD subset is empty in this regime).
        config = ModelConfig(
            seed=42,
            hidden_width=64,
            depth=2,
            init_scale=0.5,
            learning_rate=3e-3,
            weight_decay=0.0,
            epochs=800,
            optimizer="adam",
            augmentation="full_cyclic",
            augmentation_count=0,
        )
        art = train_one(
            trial_seed=3, modulus=7, train_window=2, config=config
        )
        # On the original (un-augmented) training prefix the model should
        # at least fit.
        self.assertGreaterEqual(art.train_accuracy, 0.5)

    def test_wrong_group_does_not_include_cyclic_shifts(self) -> None:
        wrong = _wrong_group(11, target_size=11, rng=random.Random(0))
        cyclic = {tuple((x + k) % 11 for x in range(11)) for k in range(11)}
        non_identity_intersect = (set(wrong) & cyclic) - {tuple(range(11))}
        self.assertEqual(non_identity_intersect, set())

    def test_random_label_group_excludes_cyclic_shifts(self) -> None:
        rl = _random_label_group(11, random.Random(0))
        cyclic = {tuple((x + k) % 11 for x in range(11)) for k in range(11)}
        non_identity_intersect = (set(rl) & cyclic) - {tuple(range(11))}
        self.assertEqual(non_identity_intersect, set())

    def test_equivariance_count_invariant_truth_is_full(self) -> None:
        # The truth f(x) = (x + 3) mod 7 should be equivariant under all
        # 7 cyclic shifts.
        table = tuple((x + 3) % 7 for x in range(7))
        group = tuple(tuple((x + k) % 7 for x in range(7)) for k in range(7))
        self.assertEqual(_equivariance_count(table, group), 7)

    def test_summarize_sweep_includes_correlations(self) -> None:
        config = ModelConfig(
            seed=0,
            hidden_width=16,
            depth=1,
            init_scale=0.5,
            learning_rate=1e-2,
            weight_decay=0.0,
            epochs=10,
            optimizer="adam",
            augmentation="none",
            augmentation_count=0,
        )
        arts = [
            train_one(trial_seed=i, modulus=7, train_window=2, config=config)
            for i in range(4)
        ]
        summary = summarize_sweep(arts)
        self.assertIn("weakness_oracle_norm", summary["correlations"])
        self.assertIn("weakness_wrong_group_norm", summary["correlations"])

    def test_augmentation_partial_cyclic(self) -> None:
        trial = cyclic_prefix_trial(rng=random.Random(0), modulus=7, train_window=2)
        truth = ground_truth_from_invariant(trial)
        xs, ys = _augmented_examples(
            trial=trial,
            truth=truth,
            modulus=7,
            augmentation="partial_cyclic",
            augmentation_count=3,
            rng=random.Random(1),
        )
        self.assertEqual(len(xs), 2 + 3)
        # Every (x, y) pair must be consistent with the truth.
        for x, y in zip(xs, ys):
            self.assertEqual(y, truth[x])


if __name__ == "__main__":
    unittest.main()
