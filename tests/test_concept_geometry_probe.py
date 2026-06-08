from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from experiments.concept_geometry.openai_embedding_probe import (
    deterministic_embedding,
    load_concepts,
    summarize,
)


class ConceptGeometryProbeTest(unittest.TestCase):
    def test_deterministic_embedding_is_unit_length(self) -> None:
        embedding = deterministic_embedding("attractor", dimensions=16)
        norm = sum(value * value for value in embedding) ** 0.5

        self.assertEqual(len(embedding), 16)
        self.assertAlmostEqual(norm, 1.0)

    def test_load_and_summarize_concepts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "concepts.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "id": "a",
                            "label": "a",
                            "category": "one",
                            "prompt": "alpha concept",
                        },
                        {
                            "id": "b",
                            "label": "b",
                            "category": "one",
                            "prompt": "beta concept",
                        },
                        {
                            "id": "c",
                            "label": "c",
                            "category": "two",
                            "prompt": "gamma concept",
                        },
                    ]
                ),
                encoding="utf-8",
            )

            concepts = load_concepts(path)
            embeddings = [deterministic_embedding(concept.prompt, dimensions=16) for concept in concepts]
            summary = summarize(concepts, embeddings, top_k=2)

        self.assertEqual(summary["concept_count"], 3)
        self.assertEqual(summary["category_count"], 2)
        self.assertIn("nearest_neighbors", summary)


if __name__ == "__main__":
    unittest.main()
