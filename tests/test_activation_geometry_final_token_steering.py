from __future__ import annotations

import unittest

from experiments.activation_geometry.final_token_steering_pilot import (
    default_pair_specs,
    gate_summary,
    parse_scales,
    steering_prompt,
    summarize_scale,
    target_margin,
)
from experiments.concept_geometry.openai_embedding_probe import Concept


class FinalTokenSteeringPilotTest(unittest.TestCase):
    def test_parse_scales(self) -> None:
        self.assertEqual(parse_scales("0.5, 1"), [0.5, 1.0])
        with self.assertRaises(ValueError):
            parse_scales(" , ")

    def test_steering_prompt_places_target_as_option_b(self) -> None:
        prompt = steering_prompt(
            source_text="attractor: stable region",
            source_label="attractor",
            target_label="attractor network",
            distractor_label="prototype",
        )

        self.assertIn("A. attractor", prompt)
        self.assertIn("B. attractor network", prompt)
        self.assertIn("C. prototype", prompt)
        self.assertTrue(prompt.endswith("Answer:"))

    def test_summarize_scale_requires_forward_and_reverse_margin(self) -> None:
        baseline = {"source": -1.0, "target": -2.0, "distractor": -3.0}
        forward = {"source": -1.2, "target": -1.4, "distractor": -3.1}
        reverse = {"source": -0.8, "target": -2.4, "distractor": -2.7}
        summary = summarize_scale(
            baseline_scores=baseline,
            forward_scores=forward,
            reverse_scores=reverse,
        )

        self.assertGreater(target_margin(forward), target_margin(baseline))
        self.assertLess(target_margin(reverse), target_margin(baseline))
        self.assertTrue(summary["passes_signed_margin_gate"])

    def test_gate_summary_counts_rows_by_kind_and_role(self) -> None:
        rows = [
            {
                "scale": 1.0,
                "role": "primary",
                "kind": "positive",
                "summary": {"passes_signed_margin_gate": True},
            },
            {
                "scale": 1.0,
                "role": "primary",
                "kind": "control",
                "summary": {"passes_signed_margin_gate": False},
            },
            {
                "scale": 1.0,
                "role": "backup",
                "kind": "positive",
                "summary": {"passes_signed_margin_gate": False},
            },
        ]

        summary = gate_summary(rows, scale=1.0)

        self.assertEqual(summary["primary_positive_pass_count"], 1)
        self.assertEqual(summary["primary_positive_total"], 1)
        self.assertEqual(summary["backup_positive_pass_count"], 0)
        self.assertEqual(summary["primary_valence_control_pass_count"], 0)

    def test_default_pair_specs_include_promoted_and_control_pairs(self) -> None:
        concepts = [
            Concept("attractor", "attractor", "dynamics", "stable basin"),
            Concept(
                "attractor_network",
                "attractor network",
                "cognition",
                "settling memory",
            ),
            Concept("prototype", "prototype", "cognition", "central example"),
            Concept("autopoiesis", "autopoiesis", "agency", "self producing"),
            Concept("homeostasis", "homeostasis", "agency", "viable bounds"),
            Concept("self_boundary", "self boundary", "agency", "self split"),
            Concept("validity_gate", "validity gate", "constraint", "verifier"),
            Concept("weak_constraint", "weak constraint", "constraint", "loose rule"),
            Concept("simplicity_bias", "simplicity bias", "constraint", "shorter"),
            Concept(
                "conceptual_space",
                "conceptual space",
                "semantics",
                "meaning space",
            ),
            Concept(
                "representation_manifold",
                "representation manifold",
                "ai_geometry",
                "learned structure",
            ),
            Concept("embedding", "embedding", "ai_geometry", "vector"),
            Concept("valence", "valence", "agency", "value"),
            Concept(
                "activation_vector",
                "activation vector",
                "ai_geometry",
                "activation",
            ),
            Concept("steering_vector", "steering vector", "ai_geometry", "steer"),
        ]

        specs = default_pair_specs(concepts)
        by_kind = {kind: 0 for kind in ("positive", "exploratory", "control")}
        for spec in specs:
            by_kind[spec.kind] += 1

        self.assertEqual(by_kind["positive"], 3)
        self.assertEqual(by_kind["exploratory"], 1)
        self.assertEqual(by_kind["control"], 2)


if __name__ == "__main__":
    unittest.main()
