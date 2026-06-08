from __future__ import annotations

import unittest

from experiments.activation_geometry.causal_patching_diagnostic import (
    aggregate_rows,
    attach_random_patch_concepts,
    gate_summaries,
    parse_patch_modes,
    specificity_rows,
    summarize_delta,
)


class CausalPatchingDiagnosticTest(unittest.TestCase):
    def test_parse_patch_modes(self) -> None:
        self.assertEqual(
            parse_patch_modes("target, random"),
            ["target", "random"],
        )
        with self.assertRaises(ValueError):
            parse_patch_modes("magic")

    def test_summarize_delta_reports_target_margin_change(self) -> None:
        baseline = {"source": -1.0, "target": -2.0, "distractor": -3.0}
        patched = {"source": -1.1, "target": -1.4, "distractor": -3.1}

        summary = summarize_delta(
            baseline_scores=baseline,
            patched_scores=patched,
        )

        self.assertGreater(summary["target_margin_delta"], 0)
        self.assertGreater(summary["target_minus_source_delta"], 0)

    def test_attach_random_patch_prefers_target_category(self) -> None:
        concepts = [
            {"id": "source", "category": "a"},
            {"id": "target", "category": "b"},
            {"id": "distractor", "category": "b"},
            {"id": "same_category", "category": "b"},
            {"id": "other", "category": "c"},
        ]
        pairs = [
            {
                "left": "source",
                "right": "target",
                "distractor": "distractor",
                "kind": "positive",
            }
        ]

        patched = attach_random_patch_concepts(concepts, pairs, seed=7)

        self.assertEqual(patched[0]["random_patch"], "same_category")
        self.assertEqual(patched[0]["random_patch_scope"], "target_category")

    def test_specificity_requires_target_to_beat_controls(self) -> None:
        rows = []
        deltas_by_mode = {
            "target": (0.3, 0.2, -0.05),
            "distractor": (0.1, 0.1, 0.1),
            "random": (0.0, -0.1, 0.1),
            "source_noop": (0.05, -0.05, 0.0),
        }
        for mode, deltas in deltas_by_mode.items():
            for option_order, delta in zip(("std", "tds", "dst"), deltas, strict=True):
                rows.append(
                    {
                        "role": "primary",
                        "layer": 12,
                        "kind": "positive",
                        "pair": "validity_gate->weak_constraint",
                        "patch_mode": mode,
                        "option_order": option_order,
                        "summary": {"target_margin_delta": delta},
                    }
                )
        control_deltas_by_mode = {
            "target": (0.2, 0.2, 0.2),
            "distractor": (0.4, 0.4, 0.4),
            "random": (0.0, 0.0, 0.0),
            "source_noop": (0.0, 0.0, 0.0),
        }
        for mode, deltas in control_deltas_by_mode.items():
            for option_order, delta in zip(("std", "tds", "dst"), deltas, strict=True):
                rows.append(
                    {
                        "role": "primary",
                        "layer": 12,
                        "kind": "control",
                        "pair": "valence->steering_vector",
                        "patch_mode": mode,
                        "option_order": option_order,
                        "summary": {"target_margin_delta": delta},
                    }
                )

        aggregates = aggregate_rows(rows)
        specificity = specificity_rows(aggregates)
        gates = gate_summaries(specificity)

        positive = next(row for row in specificity if row["kind"] == "positive")
        control = next(row for row in specificity if row["kind"] == "control")

        self.assertTrue(positive["specific_target_pass"])
        self.assertEqual(positive["best_control_mode"], "distractor")
        self.assertFalse(control["specific_target_pass"])
        self.assertEqual(gates[0]["positive_specific_pass_count"], 1)
        self.assertEqual(gates[0]["valence_control_specific_pass_count"], 0)


if __name__ == "__main__":
    unittest.main()
