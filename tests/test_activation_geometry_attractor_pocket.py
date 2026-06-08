from __future__ import annotations

import unittest

from experiments.activation_geometry.attractor_pocket_diagnostic import (
    ATTRACTOR_DISTRACTORS,
    PROMPT_FRAMES,
    attractor_gate_summaries,
    attractor_pair_specs,
    calibration_prompt,
    pair_id,
    prompt_instruction,
)


class AttractorPocketDiagnosticTest(unittest.TestCase):
    def test_pair_specs_cover_distractor_and_near_neighbor_controls(self) -> None:
        specs = attractor_pair_specs()
        positives = [row for row in specs if row.kind == "positive"]
        target_controls = [row for row in specs if row.kind == "target_near_control"]
        source_controls = [row for row in specs if row.kind == "source_near_control"]

        self.assertEqual(len(positives), len(PROMPT_FRAMES) * len(ATTRACTOR_DISTRACTORS))
        self.assertEqual(len(target_controls), len(PROMPT_FRAMES) * 2)
        self.assertEqual(len(source_controls), len(PROMPT_FRAMES) * 2)
        self.assertIn("closest:attractor->attractor_network/d=prototype", {row.id for row in specs})

    def test_pair_id_includes_frame_and_distractor(self) -> None:
        self.assertEqual(
            pair_id(
                frame="dynamics",
                left="attractor",
                right="attractor_network",
                distractor="schema",
            ),
            "dynamics:attractor->attractor_network/d=schema",
        )

    def test_prompt_frame_changes_instruction(self) -> None:
        prompt = calibration_prompt(
            source_text="attractor: a stable region",
            labels_by_role={
                "source": "attractor",
                "target": "attractor network",
                "distractor": "schema",
            },
            option_order=("source", "target", "distractor"),
            prompt_frame="dynamics",
        )

        self.assertIn(prompt_instruction("dynamics"), prompt)
        self.assertIn("B. attractor network", prompt)
        with self.assertRaises(ValueError):
            prompt_instruction("missing")

    def test_attractor_gate_summary_tracks_near_neighbor_leakage(self) -> None:
        specificity = [
            {
                "role": "primary",
                "kind": "positive",
                "specific_target_pass": True,
                "target_mean_target_margin_delta": 0.2,
                "target_advantage_over_best_control": 0.1,
            },
            {
                "role": "primary",
                "kind": "positive",
                "specific_target_pass": True,
                "target_mean_target_margin_delta": 0.1,
                "target_advantage_over_best_control": 0.05,
            },
            {
                "role": "primary",
                "kind": "target_near_control",
                "specific_target_pass": True,
                "target_mean_target_margin_delta": 0.1,
                "target_advantage_over_best_control": 0.03,
            },
            {
                "role": "primary",
                "kind": "source_near_control",
                "specific_target_pass": False,
                "target_mean_target_margin_delta": -0.1,
                "target_advantage_over_best_control": -0.2,
            },
        ]

        primary = attractor_gate_summaries(specificity)[0]

        self.assertEqual(primary["positive_specific_pass_count"], 2)
        self.assertEqual(primary["target_near_control_specific_pass_count"], 1)
        self.assertEqual(primary["source_near_control_specific_pass_count"], 0)
        self.assertFalse(primary["near_controls_clear"])
        self.assertFalse(primary["focused_gate_pass"])
        self.assertAlmostEqual(primary["positive_mean_target_margin_delta"], 0.15)


if __name__ == "__main__":
    unittest.main()
