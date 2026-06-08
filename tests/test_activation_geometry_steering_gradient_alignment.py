from __future__ import annotations

import unittest

from experiments.activation_geometry.steering_gradient_alignment import (
    aggregate_rows,
    alignment_summary,
    gate_summaries,
    parse_direction_modes,
    summarize_delta,
)


class SteeringGradientAlignmentTest(unittest.TestCase):
    def test_parse_direction_modes(self) -> None:
        self.assertEqual(
            parse_direction_modes("centroid, gradient_same_norm"),
            ["centroid", "gradient_same_norm"],
        )
        with self.assertRaises(ValueError):
            parse_direction_modes("magic")

    def test_summarize_delta_reports_margin_change(self) -> None:
        baseline = {"source": -1.0, "target": -2.0, "distractor": -3.0}
        steered = {"source": -1.2, "target": -1.6, "distractor": -3.1}

        summary = summarize_delta(
            baseline_scores=baseline,
            steered_scores=steered,
        )

        self.assertGreater(summary["target_margin_delta"], 0)
        self.assertGreater(summary["target_minus_source_delta"], 0)
        self.assertGreater(summary["target_minus_distractor_delta"], 0)

    def test_aggregate_rows_tracks_alignment_and_gate_counts(self) -> None:
        rows = []
        for option_order, delta, cosine in zip(
            ("std", "tds", "dst"),
            (0.1, 0.2, -0.05),
            (0.03, 0.02, -0.01),
            strict=True,
        ):
            rows.append(
                {
                    "role": "primary",
                    "layer": 12,
                    "kind": "positive",
                    "pair": "validity_gate->weak_constraint",
                    "direction_mode": "centroid",
                    "option_order": option_order,
                    "summary": {"target_margin_delta": delta},
                    "alignment": {"centroid_gradient_cosine": cosine},
                }
            )
        for option_order, delta in zip(("std", "tds", "dst"), (0.1, 0.2, 0.3), strict=True):
            rows.append(
                {
                    "role": "primary",
                    "layer": 12,
                    "kind": "positive",
                    "pair": "validity_gate->weak_constraint",
                    "direction_mode": "gradient_same_norm",
                    "option_order": option_order,
                    "summary": {"target_margin_delta": delta},
                    "alignment": {"centroid_gradient_cosine": 0.01},
                }
            )
        for option_order, delta in zip(("std", "tds", "dst"), (0.2, -0.3, -0.4), strict=True):
            rows.append(
                {
                    "role": "primary",
                    "layer": 12,
                    "kind": "control",
                    "pair": "valence->steering_vector",
                    "direction_mode": "centroid",
                    "option_order": option_order,
                    "summary": {"target_margin_delta": delta},
                    "alignment": {"centroid_gradient_cosine": 0.5},
                }
            )

        aggregates = aggregate_rows(rows)
        gates = gate_summaries(aggregates)
        alignments = alignment_summary(aggregates)

        centroid_positive = next(
            row
            for row in aggregates
            if row["kind"] == "positive" and row["direction_mode"] == "centroid"
        )
        centroid_control = next(row for row in aggregates if row["kind"] == "control")
        gradient_gate = next(row for row in gates if row["direction_mode"] == "gradient_same_norm")

        self.assertTrue(centroid_positive["robust_pass"])
        self.assertFalse(centroid_control["robust_pass"])
        self.assertAlmostEqual(
            centroid_positive["mean_centroid_gradient_cosine"],
            (0.03 + 0.02 - 0.01) / 3,
        )
        self.assertEqual(gradient_gate["primary_positive_pass_count"], 1)
        self.assertEqual(alignments[0]["role"], "primary")


if __name__ == "__main__":
    unittest.main()
