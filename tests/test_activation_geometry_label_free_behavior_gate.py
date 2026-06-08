from __future__ import annotations

import unittest

from experiments.activation_geometry.label_free_behavior_gate import (
    DEFAULT_OPTION_ORDERS,
    aggregate_rows,
    blank_carrier_text,
    behavior_prompt,
    definition_without_label_text,
    full_label_prompt,
    gate_summaries,
    label_only_text,
    neutral_carrier_text,
    source_text_for_regime,
    specificity_rows,
    summarize_behavior_delta,
)


class LabelFreeBehaviorGateTest(unittest.TestCase):
    def test_prompt_and_patch_regime_text(self) -> None:
        prompt = behavior_prompt(
            source_text="attractor: a stable region",
            labels_by_role={
                "source": "attractor",
                "target": "attractor network",
                "distractor": "prototype",
            },
            option_order=("target", "distractor", "source"),
        )

        self.assertIn("A. attractor network", prompt)
        self.assertIn("C. attractor", prompt)
        latent_prompt = behavior_prompt(
            source_text="attractor: a stable region",
            labels_by_role={
                "source": "attractor",
                "target": "attractor network",
                "distractor": "prototype",
            },
            option_order=("target", "distractor", "source"),
            prompt_frame="latent_choice",
        )
        self.assertNotIn("Passage:", latent_prompt)
        self.assertIn("current internal state", latent_prompt)
        label_prompt = full_label_prompt(
            source_text="attractor: a stable region",
            prompt_frame="source_passage",
        )
        self.assertIn("Passage:", label_prompt)
        self.assertTrue(label_prompt.endswith("Concept:"))
        latent_label_prompt = full_label_prompt(
            source_text="unused",
            prompt_frame="latent_choice",
        )
        self.assertNotIn("unused", latent_label_prompt)
        self.assertIn("internal state", latent_label_prompt)
        self.assertEqual(
            neutral_carrier_text(label="attractor network"),
            "Concept label: attractor network.",
        )
        self.assertEqual(label_only_text(label="attractor network"), "attractor network")
        self.assertEqual(blank_carrier_text(), "Concept label: [omitted].")
        self.assertEqual(
            definition_without_label_text(
                definition_text="attractor: a stable region",
                label="attractor",
            ),
            "a stable region",
        )
        self.assertEqual(
            source_text_for_regime(
                definition_text="definition",
                label="label",
                patch_text_regime="definition",
            ),
            "definition",
        )
        self.assertEqual(
            source_text_for_regime(
                definition_text="definition",
                label="label",
                patch_text_regime="neutral",
            ),
            "Concept label: label.",
        )
        self.assertEqual(
            source_text_for_regime(
                definition_text="label: definition body",
                label="label",
                patch_text_regime="definition_without_label",
            ),
            "definition body",
        )
        self.assertEqual(
            source_text_for_regime(
                definition_text="definition",
                label="label",
                patch_text_regime="label_only",
            ),
            "label",
        )
        self.assertEqual(
            source_text_for_regime(
                definition_text="definition",
                label="label",
                patch_text_regime="blank_carrier",
            ),
            "Concept label: [omitted].",
        )
        self.assertEqual(
            source_text_for_regime(
                definition_text="definition",
                label="label",
                shuffled_label="other",
                patch_text_regime="shuffled_label",
            ),
            "Concept label: other.",
        )
        with self.assertRaises(ValueError):
            source_text_for_regime(
                definition_text="definition",
                label="label",
                patch_text_regime="shuffled_label",
            )

    def test_summarize_behavior_delta_reports_margin_and_logprob_changes(self) -> None:
        summary = summarize_behavior_delta(
            baseline_scores={"source": -1.0, "target": -2.0, "distractor": -3.0},
            patched_scores={"source": -1.2, "target": -1.4, "distractor": -3.2},
        )

        self.assertGreater(summary["target_margin_delta"], 0)
        self.assertGreater(summary["target_logprob_delta"], 0)
        self.assertGreater(summary["target_minus_source_delta"], 0)

    def test_specificity_requires_target_to_beat_controls_by_regime(self) -> None:
        rows = []
        deltas_by_regime_and_mode = {
            "definition": {
                "target": (0.3, 0.2, -0.05),
                "distractor": (0.1, 0.1, 0.1),
                "random": (0.0, -0.1, 0.1),
                "source_noop": (0.05, -0.05, 0.0),
            },
            "neutral": {
                "target": (0.1, 0.1, 0.1),
                "distractor": (0.2, 0.2, 0.2),
                "random": (0.0, 0.0, 0.0),
                "source_noop": (0.0, 0.0, 0.0),
            },
        }
        for patch_text_regime in ("definition", "neutral"):
            for mode, deltas in deltas_by_regime_and_mode[patch_text_regime].items():
                for option_order, delta in zip(
                    DEFAULT_OPTION_ORDERS,
                    deltas,
                    strict=True,
                ):
                    rows.append(
                        {
                            "kind": "positive",
                            "pair": "attractor->attractor_network/d=prototype",
                            "prompt_frame": "source_passage",
                            "injection_layer": 6,
                            "patch_alpha": 1.0,
                            "patch_vector_surface": "hook_output",
                            "patch_text_regime": patch_text_regime,
                            "patch_mode": mode,
                            "option_order": list(option_order),
                            "summary": {
                                "target_margin_delta": delta,
                                "target_logprob_delta": delta / 2,
                            },
                        }
                    )

        aggregates = aggregate_rows(rows)
        specificity = specificity_rows(aggregates)
        summaries = gate_summaries(specificity)
        by_regime = {row["patch_text_regime"]: row for row in specificity}

        self.assertTrue(by_regime["definition"]["specific_target_pass"])
        self.assertEqual(by_regime["definition"]["best_control_mode"], "distractor")
        self.assertFalse(by_regime["neutral"]["specific_target_pass"])
        definition_summary = [
            row
            for row in summaries
            if row["patch_text_regime"] == "definition"
            and row["prompt_frame"] == "source_passage"
            and row["injection_layer"] == 6
            and row["patch_alpha"] == 1.0
        ][0]
        self.assertEqual(definition_summary["specific_pass_count"], 1)

    def test_full_label_single_probe_can_pass_when_specific(self) -> None:
        rows = []
        for mode, delta in {
            "target": 0.3,
            "distractor": 0.1,
            "random": -0.1,
            "source_noop": 0.0,
        }.items():
            rows.append(
                {
                    "kind": "positive",
                    "pair": "attractor->attractor_network/d=prototype",
                    "prompt_frame": "latent_choice",
                    "scoring_surface": "full_label",
                    "injection_layer": 6,
                    "patch_alpha": 1.0,
                    "patch_vector_surface": "hook_output",
                    "patch_text_regime": "definition",
                    "patch_mode": mode,
                    "option_order": [],
                    "summary": {
                        "target_margin_delta": delta,
                        "target_logprob_delta": delta / 2,
                    },
                }
            )

        aggregates = aggregate_rows(rows)
        specificity = specificity_rows(aggregates)
        summaries = gate_summaries(specificity)
        target = next(row for row in aggregates if row["patch_mode"] == "target")
        specific = specificity[0]

        self.assertEqual(target["robust_pass_threshold"], 1)
        self.assertTrue(target["robust_pass"])
        self.assertEqual(specific["scoring_surface"], "full_label")
        self.assertTrue(specific["specific_target_pass"])
        self.assertEqual(summaries[0]["scoring_surface"], "full_label")


if __name__ == "__main__":
    unittest.main()
