from __future__ import annotations

import unittest

from experiments.activation_geometry.activation_geometry_probe import (
    ActivationRecord,
    payload_from_layer_activations,
)
from experiments.activation_geometry.heldout_readout_pilot import (
    public_summary,
    summarize_payload,
)
from experiments.concept_geometry.openai_embedding_probe import Concept


class HeldoutReadoutPilotTest(unittest.TestCase):
    def test_summarize_payload_reports_holdout_metrics(self) -> None:
        concepts = [
            Concept(
                id="attractor",
                label="attractor",
                category="math",
                prompt="math basin",
            ),
            Concept(
                id="attractor_network",
                label="attractor network",
                category="cogsci",
                prompt="cognitive basin",
            ),
            Concept(
                id="valence",
                label="valence",
                category="affect",
                prompt="positive negative tone",
            ),
            Concept(
                id="activation_vector",
                label="activation vector",
                category="ai",
                prompt="neural direction",
            ),
        ]
        records: list[ActivationRecord] = []
        vectors: list[list[float]] = []
        bases = {
            "attractor": [1.0, 0.0, 0.0, 0.0],
            "attractor_network": [0.85, 0.15, 0.0, 0.0],
            "valence": [0.0, 0.0, 1.0, 0.0],
            "activation_vector": [0.0, 0.0, 0.0, 1.0],
        }
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
                vectors.append(
                    [
                        value + variant_shift
                        for value in bases[concept.id]
                    ]
                )

        payload = payload_from_layer_activations(
            concepts=concepts,
            records=records,
            layer_activations={"2": vectors},
            model_id="synthetic",
            backend="unit-test",
            top_k=2,
            dry_run=True,
            pooling="mean",
        )

        summary = summarize_payload(
            payload,
            concepts=concepts,
            train_variant_indices={0, 1},
            holdout_variant_index=2,
            layers=[2],
        )
        public = public_summary(summary)
        layer = summary["layers"]["2"]

        self.assertEqual(summary["manifest"]["layers"], ["2"])
        self.assertEqual(layer["holdout_count"], 4)
        self.assertEqual(layer["positive_candidate_total"], 1)
        self.assertEqual(layer["control_pair_total"], 1)
        self.assertGreaterEqual(layer["concept_accuracy"], 0.0)
        self.assertLessEqual(layer["concept_accuracy"], 1.0)
        self.assertNotIn("predictions", public["layers"]["2"])


if __name__ == "__main__":
    unittest.main()
