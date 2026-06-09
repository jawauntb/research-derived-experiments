from __future__ import annotations

import unittest

from experiments.activation_geometry.behavior_aligned_direction import (
    LABEL_SCORING_REGIMES,
    aggregate_rows,
    alignment_summary,
    gate_summaries,
    parse_direction_modes,
    parse_values,
    role_margin,
    summarize_behavior_delta,
)


class BehaviorAlignedDirectionTest(unittest.TestCase):
    def test_parse_direction_modes(self) -> None:
        self.assertEqual(
            parse_direction_modes(
                "target_learned, target_penalty_controls_1_0, target_penalty_hard_1_0"
            ),
            [
                "target_learned",
                "target_penalty_controls_1_0",
                "target_penalty_hard_1_0",
            ],
        )
        with self.assertRaises(ValueError):
            parse_direction_modes("centroid")

    def test_parse_heldout_alias_regimes(self) -> None:
        self.assertEqual(
            parse_values(
                "alias_0, alias_1",
                allowed=LABEL_SCORING_REGIMES,
                name="Label regimes",
            ),
            ["alias_0", "alias_1"],
        )

    def test_role_margin_and_behavior_delta_use_target_margin(self) -> None:
        baseline = {"source": -1.0, "target": -2.0, "distractor": -3.0}
        steered = {"source": -1.2, "target": -1.4, "distractor": -3.2}

        summary = summarize_behavior_delta(
            baseline_scores=baseline,
            steered_scores=steered,
        )

        self.assertAlmostEqual(role_margin(baseline, "target"), 0.0)
        self.assertAlmostEqual(role_margin(baseline, "source"), 1.5)
        self.assertGreater(summary["target_margin_delta"], 0)
        self.assertGreater(summary["target_logprob_delta"], 0)
        self.assertGreater(summary["target_minus_source_delta"], 0)
        self.assertGreater(summary["target_minus_distractor_delta"], 0)

    def test_aggregate_rows_gate_counts_and_alignment(self) -> None:
        rows = []
        for option_order, delta in zip(("std", "tds", "dst"), (0.2, 0.1, -0.05), strict=True):
            rows.append(
                {
                    "role": "primary",
                    "layer": 5,
                    "kind": "positive",
                    "pair": "validity_gate->weak_constraint",
                    "direction_mode": "target_learned",
                    "scale": 1.0,
                    "option_order": option_order,
                    "summary": {
                        "target_margin_delta": delta,
                        "target_logprob_delta": delta / 2,
                    },
                    "learned_alignment": {
                        "target_source_cosine": -0.1,
                        "target_distractor_cosine": -0.2,
                    },
                }
            )
        for option_order, delta in zip(("std", "tds", "dst"), (-0.2, -0.1, 0.05), strict=True):
            rows.append(
                {
                    "role": "primary",
                    "layer": 5,
                    "kind": "positive",
                    "pair": "validity_gate->weak_constraint",
                    "direction_mode": "source_learned",
                    "scale": 1.0,
                    "option_order": option_order,
                    "summary": {
                        "target_margin_delta": delta,
                        "target_logprob_delta": delta / 2,
                    },
                    "learned_alignment": {
                        "target_source_cosine": -0.1,
                        "target_distractor_cosine": -0.2,
                    },
                }
            )
        for option_order, delta in zip(("std", "tds", "dst"), (0.1, -0.1, -0.2), strict=True):
            rows.append(
                {
                    "role": "primary",
                    "layer": 5,
                    "kind": "control",
                    "pair": "valence->steering_vector",
                    "direction_mode": "target_learned",
                    "scale": 1.0,
                    "option_order": option_order,
                    "summary": {
                        "target_margin_delta": delta,
                        "target_logprob_delta": delta / 2,
                    },
                    "learned_alignment": {
                        "target_source_cosine": 0.3,
                        "target_distractor_cosine": 0.4,
                    },
                }
            )

        aggregates = aggregate_rows(rows)
        gates = gate_summaries(aggregates)
        alignments = alignment_summary(rows)

        target_positive = next(
            row
            for row in aggregates
            if row["kind"] == "positive" and row["direction_mode"] == "target_learned"
        )
        source_positive = next(
            row
            for row in aggregates
            if row["kind"] == "positive" and row["direction_mode"] == "source_learned"
        )
        positive_alignment = next(row for row in alignments if row["kind"] == "positive")
        target_gate = next(row for row in gates if row["direction_mode"] == "target_learned")

        self.assertTrue(target_positive["robust_pass"])
        self.assertFalse(source_positive["robust_pass"])
        self.assertEqual(target_gate["primary_positive_pass_count"], 1)
        self.assertEqual(target_gate["primary_valence_control_pass_count"], 0)
        self.assertAlmostEqual(positive_alignment["mean_target_source_cosine"], -0.1)
        self.assertAlmostEqual(positive_alignment["mean_target_distractor_cosine"], -0.2)

    def test_full_label_alias_rows_use_single_score_threshold(self) -> None:
        rows = [
            {
                "scoring_surface": "full_label",
                "prompt_frame": "latent_choice",
                "objective_label_scoring_regime": "alias",
                "eval_label_scoring_regime": "canonical",
                "role": "primary",
                "layer": 5,
                "kind": "positive",
                "pair": "attractor->attractor_network",
                "direction_mode": "target_learned",
                "scale": 1.0,
                "option_order": "full_label",
                "summary": {
                    "target_margin_delta": 0.2,
                    "target_logprob_delta": 0.1,
                },
                "learned_alignment": {
                    "target_source_cosine": 0.2,
                    "target_distractor_cosine": -0.1,
                },
            }
        ]

        aggregate = aggregate_rows(rows)[0]
        gate = gate_summaries([aggregate])[0]
        alignment = alignment_summary(rows)[0]

        self.assertTrue(aggregate["robust_pass"])
        self.assertEqual(aggregate["robust_pass_threshold"], 1)
        self.assertEqual(gate["scoring_surface"], "full_label")
        self.assertEqual(gate["objective_label_scoring_regime"], "alias")
        self.assertEqual(gate["eval_label_scoring_regime"], "canonical")
        self.assertEqual(gate["primary_positive_pass_count"], 1)
        self.assertEqual(alignment["eval_label_scoring_regime"], "canonical")


if __name__ == "__main__":
    unittest.main()
