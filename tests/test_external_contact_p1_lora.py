from __future__ import annotations

import random
import unittest

from experiments.external_contact.p1_lora_metrics import (
    analyze_cells,
    cyclic_group,
    equivariance_count,
    spearman,
    wrong_group,
)


class ExternalContactP1LoraMetricsTest(unittest.TestCase):
    def test_spearman_handles_ties_and_direction(self) -> None:
        self.assertAlmostEqual(spearman([1.0, 1.0, 3.0], [0.0, 0.0, 2.0]), 1.0)
        self.assertAlmostEqual(spearman([1.0, 2.0, 3.0], [3.0, 2.0, 1.0]), -1.0)

    def test_cyclic_shift_table_has_full_equivariance(self) -> None:
        table = tuple((x + 4) % 11 for x in range(11))
        self.assertEqual(equivariance_count(table, cyclic_group(11)), 11)

    def test_wrong_group_excludes_non_identity_cyclic_shifts(self) -> None:
        wrong = wrong_group(13, rng=random.Random(0), target_size=13)
        cyclic = set(cyclic_group(13))
        non_identity_intersection = (set(wrong) & cyclic) - {tuple(range(13))}
        self.assertEqual(non_identity_intersection, set())

    def test_analyze_cells_marks_degenerate_constant_ood(self) -> None:
        cells = [
            {
                "ood_accuracy": 0.0,
                "weakness_oracle_norm": 1.0 / 13.0,
                "weakness_wrong_group_norm": 1.0 / 13.0,
                "final_train_loss": 0.01 + i,
                "ood_nll": 3.0 + i,
                "pythia_param_count": 70_000_000,
                "pythia_l2": 1000.0,
                "head_sharpness_proxy": 0.1 + i,
            }
            for i in range(4)
        ]
        analysis = analyze_cells(cells)
        self.assertTrue(analysis["P1_degenerate_ood_column"])
        self.assertFalse(analysis["P1_pass"])
        self.assertTrue(analysis["P1_hard_kill"])

    def test_analyze_cells_accepts_clean_weakness_signal(self) -> None:
        cells = []
        for i, weakness in enumerate([0.1, 0.2, 0.7, 0.9]):
            cells.append(
                {
                    "ood_accuracy": [0.0, 0.1, 0.8, 1.0][i],
                    "weakness_oracle_norm": weakness,
                    "weakness_wrong_group_norm": [0.2, 0.1, 0.1, 0.2][i],
                    "final_train_loss": 1.0,
                    "ood_nll": 2.0,
                    "pythia_param_count": 70_000_000,
                    "pythia_l2": 1000.0,
                    "head_sharpness_proxy": 0.5,
                }
            )
        analysis = analyze_cells(cells)
        self.assertEqual(analysis["n_cells"], 4)
        self.assertGreaterEqual(analysis["rho_weakness_vs_ood"], 0.9)
        self.assertTrue(analysis["P1_pass"])


if __name__ == "__main__":
    unittest.main()
