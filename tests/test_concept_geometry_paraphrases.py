from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from experiments.concept_geometry.openai_embedding_probe import Concept, deterministic_embedding
from experiments.concept_geometry.paraphrase_stability_probe import (
    embedding_input,
    load_paraphrases,
    pearson,
    summarize_model,
    variant_concepts,
)


class ConceptGeometryParaphraseTest(unittest.TestCase):
    def test_load_paraphrases_requires_each_concept(self) -> None:
        concepts = [
            Concept(id="a", label="a", category="one", prompt="alpha"),
            Concept(id="b", label="b", category="two", prompt="beta"),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "paraphrases.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "id": "a",
                            "variants": ["alpha one", "alpha two"],
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_paraphrases(path, concepts)

    def test_summarize_model_reports_paraphrase_cohesion(self) -> None:
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
                        {"id": "a", "variants": ["alpha first", "alpha second"]},
                        {"id": "b", "variants": ["beta first", "beta second"]},
                        {"id": "c", "variants": ["gamma first", "gamma second"]},
                    ]
                ),
                encoding="utf-8",
            )

            paraphrases = load_paraphrases(path, concepts)
            variants = variant_concepts(concepts, paraphrases)
            embedding_concepts = embedding_input(variants)
            embeddings = [
                deterministic_embedding(concept.prompt, dimensions=16)
                for concept in embedding_concepts
            ]
            summary = summarize_model(concepts, variants, embeddings, top_k=2)

        self.assertEqual(summary["variant_count"], 6)
        self.assertIn("paraphrase_cohesion", summary)
        self.assertIn("centroid_summary", summary)

    def test_pearson_matches_identical_vectors(self) -> None:
        self.assertAlmostEqual(pearson([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]), 1.0)


if __name__ == "__main__":
    unittest.main()
