from __future__ import annotations

import unittest

from scripts.summarize_semantic_concern_sweep import paired_effects, summarize


def row(seed: int, target: str, condition: str, margin_z: float, model: str = "model/a", objective: str = "classifier"):
    return {
        "model_id": model,
        "model_slug": model.replace("/", "__"),
        "objective": objective,
        "condition": condition,
        "seed": seed,
        "target": target,
        "dataset_kind": "20newsgroups",
        "target_margin_z": margin_z,
        "specificity_z": margin_z * 1.1,
        "target_rank_percentile": 0.75,
        "target_centroid_margin_z": margin_z * 0.8,
        "target_knn_purity_z": margin_z * 0.6,
        "target_effective_rank_z": margin_z * 0.2,
        "target_f1": 0.7 + margin_z * 0.01,
        "accuracy": 0.72 + margin_z * 0.01,
    }


class SemanticConcernSummaryTests(unittest.TestCase):
    def test_pairs_concern_against_uniform_and_random_controls(self) -> None:
        rows = [
            row(1, "sci.space", "uniform", 0.1),
            row(1, "sci.space", "random_matched", 0.2),
            row(1, "sci.space", "concern", 0.6),
        ]

        effects = paired_effects(rows)

        self.assertEqual(len(effects), 1)
        self.assertAlmostEqual(effects[0]["margin_lift_vs_uniform"], 0.5)
        self.assertAlmostEqual(effects[0]["margin_lift_vs_random"], 0.4)

    def test_summary_requires_real_dataset_for_gate(self) -> None:
        rows = []
        for seed in range(1, 9):
            for target in ("sci.space", "sci.med"):
                rows.extend([
                    row(seed, target, "uniform", 0.0),
                    row(seed, target, "random_matched", 0.1),
                    row(seed, target, "concern", 0.6),
                ])
        payload = {
            "manifest": {"target_bootstrap_se": 0.2},
            "rows": rows,
        }

        summary = summarize(payload)

        family = next(iter(summary["families"].values()))
        self.assertTrue(family["gate"]["uniform_lift_positive"])
        self.assertTrue(family["gate"]["random_lift_positive"])
        self.assertTrue(family["gate"]["real_20newsgroups"])

        payload["rows"][0]["dataset_kind"] = "synthetic_fallback"
        summary = summarize(payload)
        family = next(iter(summary["families"].values()))
        self.assertFalse(family["gate"]["real_20newsgroups"])
        self.assertFalse(family["gate"]["pass"])


if __name__ == "__main__":
    unittest.main()

