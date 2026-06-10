from __future__ import annotations

import unittest

import torch

from experiments.learned_symmetry.causal_validation import (
    _augment_with_angles,
    _rotate_batch,
    run_causal_unit,
)
from experiments.rotation_weakness.neural import ModelConfig


class CausalValidationTest(unittest.TestCase):
    def test_rotate_batch_identity_passes_through(self) -> None:
        x = torch.rand(4, 1, 16, 16)
        y = _rotate_batch(x, 0.0)
        self.assertTrue(torch.equal(x, y))

    def test_augment_with_angles_grows_dataset(self) -> None:
        x = torch.rand(8, 1, 16, 16)
        y = torch.zeros(8, dtype=torch.long)
        ax, ay = _augment_with_angles(x, y, angles=[0.0, 45.0, 90.0])
        # 0.0 is skipped (identity); 45 and 90 each add 8 rows.
        self.assertEqual(ax.shape[0], 8 + 8 + 8)
        self.assertEqual(ay.shape[0], 24)

    def test_augment_with_empty_angles_returns_original(self) -> None:
        x = torch.rand(4, 1, 16, 16)
        y = torch.zeros(4, dtype=torch.long)
        ax, ay = _augment_with_angles(x, y, angles=[])
        self.assertEqual(ax.shape[0], 4)
        self.assertEqual(ay.shape[0], 4)

    def test_run_causal_unit_returns_four_regimes(self) -> None:
        config = ModelConfig(
            seed=0,
            architecture="mlp",
            hidden_width=16,
            depth=1,
            init_scale=0.5,
            learning_rate=3e-3,
            weight_decay=0.0,
            epochs=30,
            optimizer="adam",
            augmentation="none",
            augmentation_strength=0,
        )
        rows = run_causal_unit(
            config=config,
            n_rotations=4,
            train_per_class=2,
            split_seed=1,
            candidates=12,
            threshold=0.5,
        )
        regimes = {r.regime for r in rows}
        self.assertEqual(regimes, {"none", "oracle_aug", "learned_aug", "random_aug"})
        for r in rows:
            self.assertGreaterEqual(r.ood_accuracy, 0.0)
            self.assertLessEqual(r.ood_accuracy, 1.0)


if __name__ == "__main__":
    unittest.main()
