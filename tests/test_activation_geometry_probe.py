from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from experiments.activation_geometry.activation_geometry_probe import (
    activation_records,
    deterministic_activation,
    deterministic_layer_activations,
    parse_layers,
    payload_from_activations,
    payload_from_layer_activations,
    public_summary,
)
from experiments.concept_geometry.openai_embedding_probe import Concept


class ActivationGeometryProbeTest(unittest.TestCase):
    def test_parse_layers(self) -> None:
        self.assertEqual(parse_layers("0, 1,-1"), [0, 1, -1])
        with self.assertRaises(ValueError):
            parse_layers(" , ")

    def test_activation_records_from_paraphrases(self) -> None:
        concepts = [
            Concept(id="a", label="a", category="one", prompt="alpha"),
            Concept(id="b", label="b", category="two", prompt="beta"),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "paraphrases.json"
            path.write_text(
                json.dumps(
                    [
                        {"id": "a", "variants": ["alpha one", "alpha two"]},
                        {"id": "b", "variants": ["beta one", "beta two"]},
                    ]
                ),
                encoding="utf-8",
            )
            records = activation_records(concepts, path)

        self.assertEqual(len(records), 4)
        self.assertEqual(records[0].id, "a::v0")
        self.assertEqual(records[0].concept_id, "a")

    def test_payload_reports_raw_and_centered_geometry(self) -> None:
        concepts = [
            Concept(id="a", label="a", category="one", prompt="alpha"),
            Concept(id="b", label="b", category="one", prompt="beta"),
            Concept(id="c", label="c", category="two", prompt="gamma"),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "paraphrases.json"
            path.write_text(
                json.dumps(
                    [
                        {"id": "a", "variants": ["alpha one", "alpha two"]},
                        {"id": "b", "variants": ["beta one", "beta two"]},
                        {"id": "c", "variants": ["gamma one", "gamma two"]},
                    ]
                ),
                encoding="utf-8",
            )
            records = activation_records(concepts, path)

        activations = [
            deterministic_activation(record.text, layer=-1, dimensions=24)
            for record in records
        ]
        payload = payload_from_activations(
            concepts=concepts,
            records=records,
            activations=activations,
            model_id="deterministic",
            layer=-1,
            backend="dry-run",
            top_k=2,
            dry_run=True,
        )
        summary = public_summary(payload)

        self.assertEqual(summary["manifest"]["record_count"], 6)
        self.assertIn("raw", summary["summary"])
        self.assertIn("mean_centered", summary["summary"])

    def test_layer_sweep_payload_reports_compact_metrics(self) -> None:
        concepts = [
            Concept(id="attractor", label="attractor", category="math", prompt="alpha"),
            Concept(
                id="attractor_network",
                label="attractor network",
                category="cogsci",
                prompt="beta",
            ),
            Concept(
                id="conceptual_space",
                label="conceptual space",
                category="linguistics",
                prompt="gamma",
            ),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "paraphrases.json"
            path.write_text(
                json.dumps(
                    [
                        {"id": "attractor", "variants": ["alpha one", "alpha two"]},
                        {
                            "id": "attractor_network",
                            "variants": ["beta one", "beta two"],
                        },
                        {
                            "id": "conceptual_space",
                            "variants": ["gamma one", "gamma two"],
                        },
                    ]
                ),
                encoding="utf-8",
            )
            records = activation_records(concepts, path)

        layer_activations = deterministic_layer_activations(
            records,
            layers=[0, 1],
            dimensions=24,
        )
        payload = payload_from_layer_activations(
            concepts=concepts,
            records=records,
            layer_activations=layer_activations,
            model_id="deterministic",
            backend="dry-run",
            top_k=2,
            dry_run=True,
        )
        summary = public_summary(payload)

        self.assertEqual(summary["manifest"]["layers"], ["0", "1"])
        self.assertIn("0", summary["layer_metrics"])
        self.assertIn("mean_centered_bridge_lift", summary["layer_metrics"]["0"])
        self.assertIn(
            summary["top_layers_by_centered_bridge_lift"][0]["layer"],
            {"0", "1"},
        )


if __name__ == "__main__":
    unittest.main()
