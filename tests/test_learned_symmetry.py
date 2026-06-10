from __future__ import annotations

import unittest

import numpy as np
import torch

from experiments.learned_symmetry.transform_generator import (
    infer_rotation_group_from_training,
    learned_group_invariance,
    random_group_baseline,
)
from experiments.rotation_weakness.dataset import (
    make_partial_rotation_split,
    materialize_split,
    rotation_group_elements,
    to_tensors,
)


class TransformGeneratorTest(unittest.TestCase):
    def test_inferred_group_recovers_oracle_z8(self) -> None:
        split = make_partial_rotation_split(n_rotations=8, train_per_class=3, seed=0)
        train, _ = materialize_split(split, samples_per_class_rotation=4, seed=0)
        train_x, train_y = to_tensors(train)
        learned = infer_rotation_group_from_training(
            train_x, train_y, n_candidates=24, threshold=0.5
        )
        oracle = set(rotation_group_elements(8))
        learned_set = set(learned.angles())
        # We should recover >= 7 of 8 oracle angles (allow 1 miss for noise).
        recovered = sum(
            1
            for o in oracle
            if any(
                abs(o - learned_angle) < 7.6
                or abs(360.0 - abs(o - learned_angle)) < 7.6
                for learned_angle in learned_set
            )
        )
        self.assertGreaterEqual(recovered, 7)

    def test_inferred_group_includes_identity(self) -> None:
        split = make_partial_rotation_split(n_rotations=8, train_per_class=3, seed=1)
        train, _ = materialize_split(split, samples_per_class_rotation=4, seed=1)
        train_x, train_y = to_tensors(train)
        learned = infer_rotation_group_from_training(
            train_x, train_y, n_candidates=24, threshold=0.5
        )
        self.assertIn(0.0, learned.angles())

    def test_random_group_has_target_size(self) -> None:
        rng = np.random.RandomState(0)
        rg = random_group_baseline(n_candidates=24, target_size=8, rng=rng)
        self.assertEqual(len(rg), 8)
        self.assertEqual(rg.angles()[0], 0.0)

    def test_learned_group_invariance_in_unit_interval(self) -> None:
        from experiments.rotation_weakness.dataset import make_partial_rotation_split, materialize_split, to_tensors
        split = make_partial_rotation_split(n_rotations=8, train_per_class=3, seed=2)
        train, _ = materialize_split(split, samples_per_class_rotation=4, seed=2)
        train_x, train_y = to_tensors(train)
        learned = infer_rotation_group_from_training(
            train_x, train_y, n_candidates=24, threshold=0.5
        )

        class Constant(torch.nn.Module):
            def forward(self, x):
                return torch.zeros(x.shape[0], 8) + torch.tensor([1.0] + [0.0] * 7)

        model = Constant()
        score = learned_group_invariance(model, train_x[:8], learned_group=learned)
        # Constant classifier is trivially invariant under any transform.
        self.assertAlmostEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
