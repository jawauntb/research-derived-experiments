from __future__ import annotations

import math
import unittest

from experiments.commitment_surface.e2_e3_neural_sweep import (
    Config,
    all_pairs,
    ce_with_subspace_ablation,
    fit_group_mean_subspace,
    make_model,
    run_cell,
)


class RankNormalizedPatchTest(unittest.TestCase):
    def test_group_mean_subspace_hits_requested_mass(self) -> None:
        import torch

        config = Config(
            modulus=7,
            seed=11,
            train_frac=0.5,
            arm="A",
            hidden_width=16,
            depth=1,
            epochs=1,
            learning_rate=1e-3,
            weight_decay=0.0,
            aug_orbit_size=1,
            top_k_patch=2,
            subspace_mass_fraction=0.5,
        )
        model = make_model(config)
        center, basis, realized, rank = fit_group_mean_subspace(
            model,
            config.modulus,
            torch.device("cpu"),
            grouping="sum",
            target_mass_fraction=0.5,
        )

        self.assertEqual(center.shape, (1, config.hidden_width))
        self.assertEqual(basis.shape, (config.hidden_width, rank))
        self.assertGreater(rank, 0)
        self.assertGreaterEqual(realized, 0.5)
        self.assertLessEqual(realized, 1.0)

        patched_ce = ce_with_subspace_ablation(
            model,
            config.modulus,
            all_pairs(config.modulus),
            torch.device("cpu"),
            center=center,
            basis=basis,
        )
        self.assertTrue(math.isfinite(patched_ce))

    def test_run_cell_records_width_comparable_metrics(self) -> None:
        config = Config(
            modulus=7,
            seed=17,
            train_frac=0.5,
            arm="B",
            hidden_width=16,
            depth=1,
            epochs=2,
            learning_rate=3e-3,
            weight_decay=0.0,
            aug_orbit_size=1,
            top_k_patch=2,
            subspace_mass_fraction=0.5,
        )
        result = run_cell(config)

        self.assertGreater(result.subspace_rank, 0)
        self.assertGreaterEqual(result.subspace_mass_fraction, 0.5)
        self.assertTrue(math.isfinite(result.subspace_patch_ce_delta))
        self.assertAlmostEqual(
            result.subspace_patch_ce_per_mass,
            result.subspace_patch_ce_delta / result.subspace_mass_fraction,
        )

    def test_invalid_grouping_is_rejected(self) -> None:
        import torch

        config = Config(
            modulus=7,
            seed=3,
            train_frac=0.5,
            arm="A",
            hidden_width=8,
            depth=1,
            epochs=1,
            learning_rate=1e-3,
            weight_decay=0.0,
            aug_orbit_size=1,
            top_k_patch=1,
        )
        with self.assertRaisesRegex(ValueError, "unsupported grouping"):
            fit_group_mean_subspace(
                make_model(config),
                config.modulus,
                torch.device("cpu"),
                grouping="not-a-group",
                target_mass_fraction=0.5,
            )


if __name__ == "__main__":
    unittest.main()
