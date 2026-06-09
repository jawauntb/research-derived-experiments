from __future__ import annotations

import random
import unittest

import numpy as np
import torch

from experiments.rotation_weakness.dataset import (
    N_CLASSES,
    make_partial_rotation_split,
    materialize_split,
    rotate_image,
    rotation_group_elements,
    to_tensors,
)
from experiments.rotation_weakness.neural import (
    ModelConfig,
    _rotation_weakness,
    _wrong_group_invariance,
    make_model,
    train_one,
)


class DatasetTest(unittest.TestCase):
    def test_split_train_and_ood_disjoint(self) -> None:
        split = make_partial_rotation_split(n_rotations=8, train_per_class=3, seed=0)
        for label in range(N_CLASSES):
            train = set(split.train_rotations_per_class[label])
            ood = set(split.ood_rotations_per_class[label])
            self.assertEqual(train & ood, set())
            self.assertEqual(train | ood, set(range(8)))
            self.assertEqual(len(train), 3)

    def test_materialize_produces_tensors(self) -> None:
        split = make_partial_rotation_split(n_rotations=8, train_per_class=3, seed=0)
        train, ood = materialize_split(split, samples_per_class_rotation=4, seed=0)
        x, y = to_tensors(train)
        self.assertEqual(x.shape[1:], (1, 16, 16))
        self.assertEqual(len(set(y.tolist())), N_CLASSES)

    def test_rotation_group_elements(self) -> None:
        angles = rotation_group_elements(8)
        self.assertEqual(len(angles), 8)
        self.assertAlmostEqual(angles[1], 45.0)
        self.assertAlmostEqual(angles[2], 90.0)

    def test_rotate_image_is_approximately_invariant_under_360(self) -> None:
        img = np.zeros((16, 16), dtype=np.float32)
        img[8, 8] = 1.0
        rotated = rotate_image(img, 360.0)
        self.assertLess(np.abs(img - rotated).sum(), 1.0)


class NeuralTest(unittest.TestCase):
    def test_train_one_runs_with_full_orbit_augmentation(self) -> None:
        split = make_partial_rotation_split(n_rotations=4, train_per_class=2, seed=0)
        config = ModelConfig(
            seed=0,
            architecture="cnn",
            hidden_width=16,
            depth=1,
            init_scale=0.5,
            learning_rate=3e-3,
            weight_decay=0.0,
            epochs=20,
            optimizer="adam",
            augmentation="full_rotation",
            augmentation_strength=0,
        )
        art = train_one(split=split, config=config, samples_per_class_rotation=2)
        self.assertGreaterEqual(art.train_accuracy, 0.0)
        self.assertLessEqual(art.train_accuracy, 1.0)
        self.assertGreaterEqual(art.weakness_rotation_norm, 0.0)
        self.assertLessEqual(art.weakness_rotation_norm, 1.0)

    def test_rotation_weakness_of_constant_classifier_is_one(self) -> None:
        # A model that always outputs class 0 is trivially rotation-invariant.
        class Constant(torch.nn.Module):
            def forward(self, x):
                B = x.shape[0]
                logits = torch.zeros(B, N_CLASSES)
                logits[:, 0] = 1.0
                return logits

        model = Constant()
        x = torch.rand(8, 1, 16, 16)
        w = _rotation_weakness(model, x, n_rotations=4)
        self.assertEqual(w, 1.0)

    def test_wrong_group_invariance_returns_in_unit_interval(self) -> None:
        config = ModelConfig(
            seed=0,
            architecture="mlp",
            hidden_width=16,
            depth=1,
            init_scale=0.5,
            learning_rate=1e-2,
            weight_decay=0.0,
            epochs=5,
            optimizer="adam",
            augmentation="none",
            augmentation_strength=0,
        )
        model = make_model(config)
        x = torch.rand(8, 1, 16, 16)
        v = _wrong_group_invariance(model, x, n_perms=3, rng=random.Random(0))
        self.assertGreaterEqual(v, 0.0)
        self.assertLessEqual(v, 1.0)


if __name__ == "__main__":
    unittest.main()
