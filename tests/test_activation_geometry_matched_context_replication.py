from __future__ import annotations

import unittest

from experiments.activation_geometry.matched_context_replication import (
    max_abs_source_noop_delta,
    replication_rows,
    summarize_by_layer_pair,
    summarize_by_variant_pair,
)


def payload(seed: int, variant: int, rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "manifest": {
            "model_id": "toy",
            "context_variant_index": variant,
            "seed": seed,
        },
        "specificity_rows": rows,
        "aggregate_rows": [
            {
                "patch_mode": "source_noop",
                "mean_target_margin_delta": 0.0,
            }
        ],
    }


class MatchedContextReplicationTest(unittest.TestCase):
    def test_summarize_by_layer_pair_counts_specific_and_robust_passes(self) -> None:
        rows = replication_rows(
            [
                payload(
                    1,
                    0,
                    [
                        {
                            "role": "primary",
                            "layer": 5,
                            "kind": "positive",
                            "pair": "a->b",
                            "target_mean_target_margin_delta": 0.2,
                            "target_advantage_over_best_control": 0.1,
                            "target_robust_pass": True,
                            "specific_target_pass": True,
                            "best_control_mode": "distractor",
                            "best_control_mean_target_margin_delta": 0.1,
                        }
                    ],
                ),
                payload(
                    2,
                    0,
                    [
                        {
                            "role": "primary",
                            "layer": 5,
                            "kind": "positive",
                            "pair": "a->b",
                            "target_mean_target_margin_delta": 0.1,
                            "target_advantage_over_best_control": -0.1,
                            "target_robust_pass": True,
                            "specific_target_pass": False,
                            "best_control_mode": "random",
                            "best_control_mean_target_margin_delta": 0.2,
                        }
                    ],
                ),
            ]
        )

        summary = summarize_by_layer_pair(rows)[0]

        self.assertEqual(summary["specific_pass_count"], 1)
        self.assertEqual(summary["robust_pass_count"], 2)
        self.assertEqual(summary["total"], 2)
        self.assertAlmostEqual(summary["mean_target_margin_delta"], 0.15)
        self.assertAlmostEqual(summary["mean_target_advantage_over_best_control"], 0.0)

    def test_summarize_by_variant_pair_filters_layer(self) -> None:
        rows = replication_rows(
            [
                payload(
                    1,
                    2,
                    [
                        {
                            "role": "primary",
                            "layer": 4,
                            "kind": "positive",
                            "pair": "a->b",
                            "target_mean_target_margin_delta": 0.4,
                            "target_advantage_over_best_control": 0.4,
                            "target_robust_pass": True,
                            "specific_target_pass": True,
                            "best_control_mode": "source_noop",
                            "best_control_mean_target_margin_delta": 0.0,
                        },
                        {
                            "role": "backup",
                            "layer": 5,
                            "kind": "positive",
                            "pair": "a->b",
                            "target_mean_target_margin_delta": 0.2,
                            "target_advantage_over_best_control": 0.1,
                            "target_robust_pass": True,
                            "specific_target_pass": True,
                            "best_control_mode": "distractor",
                            "best_control_mean_target_margin_delta": 0.1,
                        },
                    ],
                )
            ]
        )

        summaries = summarize_by_variant_pair(rows, layer=5)

        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["context_variant_index"], 2)
        self.assertEqual(summaries[0]["layer"], 5)

    def test_max_abs_source_noop_delta(self) -> None:
        payloads = [
            {
                "aggregate_rows": [
                    {
                        "patch_mode": "source_noop",
                        "mean_target_margin_delta": -0.25,
                    },
                    {
                        "patch_mode": "target",
                        "mean_target_margin_delta": 10.0,
                    },
                ]
            }
        ]

        self.assertEqual(max_abs_source_noop_delta(payloads), 0.25)


if __name__ == "__main__":
    unittest.main()
