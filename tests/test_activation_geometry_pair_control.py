from __future__ import annotations

import unittest

from experiments.activation_geometry.activation_geometry_probe import (
    ActivationRecord,
    payload_from_layer_activations,
)
from experiments.activation_geometry.pair_control_diagnostic import (
    diagnostic_for_layer,
    holdout_vectors_by_concept,
    summarize_payload,
)
from experiments.concept_geometry.openai_embedding_probe import Concept


class PairControlDiagnosticTest(unittest.TestCase):
    def test_pair_diagnostic_reports_matched_and_shuffled_controls(self) -> None:
        concepts = [
            Concept(
                id="attractor",
                label="attractor",
                category="dynamics",
                prompt="stable basin",
            ),
            Concept(
                id="basin_of_attraction",
                label="basin",
                category="dynamics",
                prompt="initial states",
            ),
            Concept(
                id="attractor_network",
                label="attractor network",
                category="cognition",
                prompt="settling memory",
            ),
            Concept(
                id="prototype",
                label="prototype",
                category="cognition",
                prompt="central example",
            ),
            Concept(
                id="valence",
                label="valence",
                category="agency",
                prompt="value signal",
            ),
            Concept(
                id="homeostasis",
                label="homeostasis",
                category="agency",
                prompt="viable bounds",
            ),
            Concept(
                id="activation_vector",
                label="activation vector",
                category="ai_geometry",
                prompt="neural direction",
            ),
            Concept(
                id="embedding",
                label="embedding",
                category="ai_geometry",
                prompt="vector representation",
            ),
            Concept(
                id="conceptual_space",
                label="conceptual space",
                category="semantics",
                prompt="meaning geometry",
            ),
            Concept(
                id="semantic_distance",
                label="semantic distance",
                category="semantics",
                prompt="meaning distance",
            ),
            Concept(
                id="representation_manifold",
                label="representation manifold",
                category="ai_geometry",
                prompt="learned geometry",
            ),
            Concept(
                id="steering_vector",
                label="steering vector",
                category="ai_geometry",
                prompt="control direction",
            ),
            Concept(
                id="autopoiesis",
                label="autopoiesis",
                category="agency",
                prompt="self maintaining organization",
            ),
            Concept(
                id="validity_gate",
                label="validity gate",
                category="constraint",
                prompt="explicit verifier",
            ),
            Concept(
                id="weak_constraint",
                label="weak constraint",
                category="constraint",
                prompt="loose rule",
            ),
            Concept(
                id="simplicity_bias",
                label="simplicity bias",
                category="constraint",
                prompt="shorter explanations",
            ),
        ]
        bases = {
            "attractor": [1.0, 0.0, 0.0, 0.0],
            "attractor_network": [0.95, 0.05, 0.0, 0.0],
            "basin_of_attraction": [0.0, 1.0, 0.0, 0.0],
            "prototype": [0.0, 0.9, 0.1, 0.0],
            "valence": [0.0, 0.0, 1.0, 0.0],
            "activation_vector": [0.0, 0.0, 0.0, 1.0],
            "homeostasis": [0.0, 0.0, 0.9, 0.1],
            "embedding": [0.0, 0.0, 0.1, 0.9],
            "conceptual_space": [0.7, 0.0, 0.7, 0.0],
            "semantic_distance": [0.0, 0.7, 0.7, 0.0],
            "representation_manifold": [0.65, 0.0, 0.65, 0.1],
            "steering_vector": [0.0, 0.1, 0.1, 0.9],
            "autopoiesis": [0.0, 0.2, 0.8, 0.0],
            "validity_gate": [0.4, 0.4, 0.0, 0.0],
            "weak_constraint": [0.45, 0.35, 0.0, 0.0],
            "simplicity_bias": [0.0, 0.4, 0.4, 0.0],
        }
        records: list[ActivationRecord] = []
        vectors: list[list[float]] = []
        for concept in concepts:
            for variant_index in range(3):
                records.append(
                    ActivationRecord(
                        id=f"{concept.id}::v{variant_index}",
                        concept_id=concept.id,
                        label=concept.label,
                        category=concept.category,
                        variant_index=variant_index,
                        text=f"{concept.prompt} variant {variant_index}",
                    )
                )
                variant_shift = 0.01 * variant_index
                vectors.append([value + variant_shift for value in bases[concept.id]])
        payload = payload_from_layer_activations(
            concepts=concepts,
            records=records,
            layer_activations={"1": vectors},
            model_id="synthetic",
            backend="unit-test",
            top_k=2,
            dry_run=True,
            pooling="mean",
        )

        vectors_by_concept = holdout_vectors_by_concept(
            payload,
            concepts=concepts,
            layer="1",
            train_variant_indices={0, 1},
            holdout_variant_index=2,
        )
        layer_summary = diagnostic_for_layer(
            concepts=concepts,
            vectors_by_concept=vectors_by_concept,
            shuffle_count=32,
            seed=7,
        )
        payload_summary = summarize_payload(
            payload,
            concepts=concepts,
            train_variant_indices={0, 1},
            holdout_variant_index=2,
            layers=[1],
            shuffle_count=32,
            seed=7,
        )

        self.assertEqual(payload_summary["manifest"]["layers"], ["1"])
        self.assertEqual(layer_summary["positive_candidate_total"], 4)
        self.assertEqual(layer_summary["control_pair_total"], 2)
        first_positive = layer_summary["positive_candidate_pairs"][0]
        self.assertGreater(first_positive["matched_control_count"], 0)
        self.assertGreater(first_positive["shuffled_label_count"], 0)
        self.assertIn("promoted_for_steering", first_positive)


if __name__ == "__main__":
    unittest.main()
