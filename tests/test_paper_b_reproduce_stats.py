from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.reproduce_paperB_stats import load_semantic_csv, load_spatial_csv


class PaperBReproduceStatsTests(unittest.TestCase):
    def test_spatial_csv_loader_restores_reward_xy_and_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spatial.csv"
            fields = [
                "arch",
                "condition",
                "seed",
                "reward_x",
                "reward_y",
                "final_loss",
                "coverage",
                "side",
                "Ng",
                "reward_z",
                "wrong_z_mean",
                "specificity_z",
                "reward_rank_percentile",
                "peak_error",
                "top10_com_error",
                "spatial_corr_reward_log_metric",
                "area_reward_z",
                "area_wrong_z_mean",
                "area_specificity_z",
                "area_reward_rank_percentile",
                "area_peak_error",
                "area_top10_com_error",
                "area_spatial_corr_reward_log_metric",
                "mean_area",
                "mean_stretch",
            ]
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerow({field: "1" for field in fields} | {"arch": "rnn", "condition": "reward"})

            rows = load_spatial_csv(path)

        self.assertEqual(rows[0]["arch"], "rnn")
        self.assertEqual(rows[0]["seed"], 1)
        self.assertEqual(rows[0]["reward_xy"], [1.0, 1.0])

    def test_semantic_csv_loader_restores_numeric_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "semantic.csv"
            fields = [
                "model_id",
                "model_slug",
                "objective",
                "condition",
                "seed",
                "target",
                "target_idx",
                "dataset_kind",
                "train_per_class",
                "test_per_class",
                "steps",
                "batch_size",
                "geom_dim",
                "concern_weight",
                "final_loss",
                "target_margin",
                "target_margin_z",
                "specificity_z",
                "target_rank_percentile",
                "target_centroid_margin_z",
                "target_knn_purity_z",
                "target_effective_rank_z",
                "target_knn_purity",
                "target_f1",
                "accuracy",
            ]
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerow({field: "1" for field in fields} | {
                    "model_id": "m",
                    "model_slug": "m",
                    "objective": "classifier",
                    "condition": "concern",
                    "target": "sci.space",
                    "dataset_kind": "20newsgroups",
                })

            rows = load_semantic_csv(path)

        self.assertEqual(rows[0]["seed"], 1)
        self.assertEqual(rows[0]["target"], "sci.space")
        self.assertEqual(rows[0]["target_margin_z"], 1.0)


if __name__ == "__main__":
    unittest.main()
