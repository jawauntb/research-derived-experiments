from __future__ import annotations

import unittest

from experiments.activation_geometry.steering_calibration_diagnostic import (
    aggregate_rows,
    calibration_prompt,
    gate_summaries,
    option_order_key,
    parse_direction_modes,
    parse_option_orders,
    role_slots,
    summarize_delta,
)


class SteeringCalibrationDiagnosticTest(unittest.TestCase):
    def test_parse_option_orders(self) -> None:
        self.assertEqual(
            parse_option_orders("std, tds"),
            [
                ("source", "target", "distractor"),
                ("target", "distractor", "source"),
            ],
        )
        with self.assertRaises(ValueError):
            parse_option_orders("bad")

    def test_parse_direction_modes(self) -> None:
        self.assertEqual(
            parse_direction_modes("raw_target_minus_source, random_same_norm"),
            ["raw_target_minus_source", "random_same_norm"],
        )
        with self.assertRaises(ValueError):
            parse_direction_modes("magic")

    def test_calibration_prompt_and_role_slots_follow_option_order(self) -> None:
        option_order = ("target", "distractor", "source")
        prompt = calibration_prompt(
            source_text="A concept prompt.",
            labels_by_role={
                "source": "attractor",
                "target": "attractor network",
                "distractor": "prototype",
            },
            option_order=option_order,
        )

        self.assertEqual(option_order_key(option_order), "tds")
        self.assertEqual(role_slots(option_order), {"target": "A", "distractor": "B", "source": "C"})
        self.assertIn("A. attractor network", prompt)
        self.assertIn("B. prototype", prompt)
        self.assertIn("C. attractor", prompt)

    def test_summarize_delta_reports_target_margin_change(self) -> None:
        baseline = {"source": -1.0, "target": -2.0, "distractor": -3.0}
        steered = {"source": -1.1, "target": -1.5, "distractor": -3.2}
        summary = summarize_delta(
            baseline_scores=baseline,
            steered_scores=steered,
        )

        self.assertGreater(summary["target_margin_delta"], 0)
        self.assertGreater(summary["target_minus_source_delta"], 0)

    def test_aggregate_rows_requires_two_option_orders_and_positive_mean(self) -> None:
        rows = []
        for option_order, delta in zip(("std", "tds", "dst"), (0.2, 0.1, -0.05), strict=True):
            rows.append(
                {
                    "role": "primary",
                    "layer": 12,
                    "kind": "positive",
                    "pair": "validity_gate->weak_constraint",
                    "direction_mode": "raw_target_minus_source",
                    "option_order": option_order,
                    "summary": {"target_margin_delta": delta},
                }
            )
        for option_order, delta in zip(("std", "tds", "dst"), (0.2, -0.3, -0.4), strict=True):
            rows.append(
                {
                    "role": "primary",
                    "layer": 12,
                    "kind": "control",
                    "pair": "valence->steering_vector",
                    "direction_mode": "raw_target_minus_source",
                    "option_order": option_order,
                    "summary": {"target_margin_delta": delta},
                }
            )

        aggregates = aggregate_rows(rows)
        summary = gate_summaries(aggregates)[0]

        positive = next(row for row in aggregates if row["kind"] == "positive")
        control = next(row for row in aggregates if row["kind"] == "control")
        self.assertTrue(positive["robust_pass"])
        self.assertFalse(control["robust_pass"])
        self.assertEqual(summary["primary_positive_pass_count"], 1)
        self.assertEqual(summary["primary_valence_control_pass_count"], 0)


if __name__ == "__main__":
    unittest.main()
