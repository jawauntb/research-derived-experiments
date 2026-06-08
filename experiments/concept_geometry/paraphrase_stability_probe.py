#!/usr/bin/env python3
"""Stress-test concept geometry against paraphrases and model changes."""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from experiments.concept_geometry.openai_embedding_probe import (
    Concept,
    cosine,
    deterministic_embedding,
    load_concepts,
    mean,
    nearest_neighbors,
    openai_embeddings,
    pairwise_similarities,
    summarize,
)


DEFAULT_MODELS = ("text-embedding-3-small", "text-embedding-3-large")
BRIDGE_PAIRS = (
    ("attractor", "attractor_network"),
    ("attractor_network", "activation_vector"),
    ("conceptual_space", "representation_manifold"),
    ("embedding", "activation_vector"),
    ("embedding", "steering_vector"),
    ("autopoiesis", "self_boundary"),
    ("autopoiesis", "homeostasis"),
    ("validity_gate", "weak_constraint"),
    ("validity_gate", "residual_content"),
    ("valence", "activation_vector"),
    ("valence", "steering_vector"),
    ("valence", "attractor"),
)


@dataclass(frozen=True)
class ParaphraseSet:
    id: str
    variants: list[str]


@dataclass(frozen=True)
class VariantConcept:
    id: str
    concept_id: str
    label: str
    category: str
    variant_index: int
    prompt: str


def load_paraphrases(path: Path, concepts: list[Concept]) -> dict[str, ParaphraseSet]:
    data = json.loads(path.read_text(encoding="utf-8"))
    paraphrases = {item["id"]: ParaphraseSet(**item) for item in data}
    concept_ids = {concept.id for concept in concepts}
    missing = sorted(concept_ids - paraphrases.keys())
    extras = sorted(paraphrases.keys() - concept_ids)
    too_short = sorted(
        concept_id
        for concept_id, paraphrase_set in paraphrases.items()
        if concept_id in concept_ids and len(paraphrase_set.variants) < 2
    )
    if missing or extras or too_short:
        raise ValueError(
            json.dumps(
                {
                    "missing_concept_ids": missing,
                    "extra_paraphrase_ids": extras,
                    "concepts_with_too_few_variants": too_short,
                },
                sort_keys=True,
            )
        )
    return paraphrases


def variant_concepts(
    concepts: list[Concept],
    paraphrases: dict[str, ParaphraseSet],
) -> list[VariantConcept]:
    variants: list[VariantConcept] = []
    for concept in concepts:
        for index, prompt in enumerate(paraphrases[concept.id].variants):
            variants.append(
                VariantConcept(
                    id=f"{concept.id}::v{index}",
                    concept_id=concept.id,
                    label=concept.label,
                    category=concept.category,
                    variant_index=index,
                    prompt=prompt,
                )
            )
    return variants


def normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector]


def centroid(vectors: list[list[float]]) -> list[float]:
    dimensions = len(vectors[0])
    averaged = [sum(vector[index] for vector in vectors) / len(vectors) for index in range(dimensions)]
    return normalize(averaged)


def pearson(left: list[float], right: list[float]) -> float:
    left_mean = mean(left)
    right_mean = mean(right)
    numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right))
    left_denominator = math.sqrt(sum((a - left_mean) ** 2 for a in left))
    right_denominator = math.sqrt(sum((b - right_mean) ** 2 for b in right))
    if left_denominator == 0 or right_denominator == 0:
        return float("nan")
    return numerator / (left_denominator * right_denominator)


def embedding_input(variants: list[VariantConcept]) -> list[Concept]:
    return [
        Concept(
            id=variant.id,
            label=variant.label,
            category=variant.category,
            prompt=variant.prompt,
        )
        for variant in variants
    ]


def concept_centroids(
    concepts: list[Concept],
    variants: list[VariantConcept],
    embeddings: list[list[float]],
) -> list[list[float]]:
    by_concept: dict[str, list[list[float]]] = {concept.id: [] for concept in concepts}
    for variant, embedding in zip(variants, embeddings):
        by_concept[variant.concept_id].append(embedding)
    return [centroid(by_concept[concept.id]) for concept in concepts]


def paraphrase_cohesion(
    concepts: list[Concept],
    variants: list[VariantConcept],
    embeddings: list[list[float]],
) -> dict[str, Any]:
    by_concept: dict[str, list[list[float]]] = {concept.id: [] for concept in concepts}
    for variant, embedding in zip(variants, embeddings):
        by_concept[variant.concept_id].append(embedding)

    concept_rows: dict[str, dict[str, Any]] = {}
    means = []
    minimums = []
    for concept in concepts:
        similarities = []
        vectors = by_concept[concept.id]
        for left_index, left in enumerate(vectors):
            for right_index, right in enumerate(vectors):
                if left_index >= right_index:
                    continue
                similarities.append(cosine(left, right))
        concept_mean = mean(similarities)
        concept_minimum = min(similarities)
        means.append(concept_mean)
        minimums.append(concept_minimum)
        concept_rows[concept.id] = {
            "mean_pairwise_cosine": concept_mean,
            "min_pairwise_cosine": concept_minimum,
        }

    return {
        "mean_paraphrase_cohesion": mean(means),
        "min_concept_mean_cohesion": min(means),
        "min_variant_pair_cohesion": min(minimums),
        "by_concept": concept_rows,
    }


def bridge_scores(
    concepts: list[Concept],
    centroid_embeddings: list[list[float]],
) -> list[dict[str, Any]]:
    index_by_id = {concept.id: index for index, concept in enumerate(concepts)}
    rows = []
    for left_id, right_id in BRIDGE_PAIRS:
        if left_id not in index_by_id or right_id not in index_by_id:
            continue
        left_index = index_by_id[left_id]
        right_index = index_by_id[right_id]
        rows.append(
            {
                "left": left_id,
                "right": right_id,
                "cosine": cosine(centroid_embeddings[left_index], centroid_embeddings[right_index]),
            }
        )
    return rows


def kernel_values(concepts: list[Concept], embeddings: list[list[float]]) -> list[float]:
    return [row["cosine"] for row in pairwise_similarities(concepts, embeddings)]


def neighbor_overlap(
    concepts: list[Concept],
    left_embeddings: list[list[float]],
    right_embeddings: list[list[float]],
    top_k: int,
) -> dict[str, Any]:
    left_neighbors = nearest_neighbors(concepts, left_embeddings, top_k)
    right_neighbors = nearest_neighbors(concepts, right_embeddings, top_k)
    by_concept: dict[str, float] = {}
    for concept in concepts:
        left_ids = {neighbor["id"] for neighbor in left_neighbors[concept.id]}
        right_ids = {neighbor["id"] for neighbor in right_neighbors[concept.id]}
        by_concept[concept.id] = len(left_ids & right_ids) / len(left_ids | right_ids)
    return {
        "mean_top_k_neighbor_overlap": mean(list(by_concept.values())),
        "by_concept": by_concept,
    }


def summarize_model(
    concepts: list[Concept],
    variants: list[VariantConcept],
    embeddings: list[list[float]],
    top_k: int,
) -> dict[str, Any]:
    centroids = concept_centroids(concepts, variants, embeddings)
    return {
        "variant_count": len(variants),
        "paraphrase_cohesion": paraphrase_cohesion(concepts, variants, embeddings),
        "centroid_summary": summarize(concepts, centroids, top_k),
        "bridge_scores": bridge_scores(concepts, centroids),
        "centroid_embeddings": {
            concept.id: embedding for concept, embedding in zip(concepts, centroids)
        },
    }


def compare_models(
    concepts: list[Concept],
    model_summaries: dict[str, dict[str, Any]],
    top_k: int,
) -> dict[str, Any]:
    if len(model_summaries) < 2:
        return {}

    model_names = list(model_summaries)
    comparisons: dict[str, Any] = {}
    for left_index, left_model in enumerate(model_names):
        for right_model in model_names[left_index + 1 :]:
            left_embeddings = [model_summaries[left_model]["centroid_embeddings"][concept.id] for concept in concepts]
            right_embeddings = [model_summaries[right_model]["centroid_embeddings"][concept.id] for concept in concepts]
            comparisons[f"{left_model}__{right_model}"] = {
                "pairwise_kernel_pearson": pearson(
                    kernel_values(concepts, left_embeddings),
                    kernel_values(concepts, right_embeddings),
                ),
                "neighbor_overlap": neighbor_overlap(concepts, left_embeddings, right_embeddings, top_k),
                "bridge_score_delta": [
                    {
                        "left": left_score["left"],
                        "right": left_score["right"],
                        "left_model_cosine": left_score["cosine"],
                        "right_model_cosine": right_score["cosine"],
                        "absolute_delta": abs(left_score["cosine"] - right_score["cosine"]),
                    }
                    for left_score, right_score in zip(
                        model_summaries[left_model]["bridge_scores"],
                        model_summaries[right_model]["bridge_scores"],
                    )
                ],
            }
    return comparisons


def public_summary(payload: dict[str, Any]) -> dict[str, Any]:
    model_summaries = {}
    for model, summary in payload["model_summaries"].items():
        centroid_summary = summary["centroid_summary"]
        model_summaries[model] = {
            "variant_count": summary["variant_count"],
            "paraphrase_cohesion": {
                key: value
                for key, value in summary["paraphrase_cohesion"].items()
                if key != "by_concept"
            },
            "centroid_summary": {
                "concept_count": centroid_summary["concept_count"],
                "category_count": centroid_summary["category_count"],
                "within_category_mean_cosine": centroid_summary["within_category_mean_cosine"],
                "across_category_mean_cosine": centroid_summary["across_category_mean_cosine"],
                "category_separation": centroid_summary["category_separation"],
                "mean_top_k_same_category_rate": centroid_summary["mean_top_k_same_category_rate"],
            },
            "bridge_scores": summary["bridge_scores"],
        }
    return {
        "manifest": payload["manifest"],
        "model_summaries": model_summaries,
        "cross_model": payload["cross_model"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concepts", type=Path, required=True)
    parser.add_argument("--paraphrases", type=Path, required=True)
    parser.add_argument("--models", nargs="+", default=list(DEFAULT_MODELS))
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    concepts = load_concepts(args.concepts)
    paraphrases = load_paraphrases(args.paraphrases, concepts)
    variants = variant_concepts(concepts, paraphrases)
    embedding_concepts = embedding_input(variants)

    model_summaries: dict[str, dict[str, Any]] = {}
    raw_embeddings: dict[str, dict[str, list[float]]] = {}
    model_names = ["deterministic-dry-run"] if args.dry_run else args.models
    for model in model_names:
        embeddings = (
            [deterministic_embedding(concept.prompt) for concept in embedding_concepts]
            if args.dry_run
            else openai_embeddings(embedding_concepts, model)
        )
        model_summaries[model] = summarize_model(concepts, variants, embeddings, args.top_k)
        raw_embeddings[model] = {
            variant.id: embedding for variant, embedding in zip(variants, embeddings)
        }

    payload = {
        "manifest": {
            "models": model_names,
            "concept_source": str(args.concepts),
            "paraphrase_source": str(args.paraphrases),
            "concept_count": len(concepts),
            "variant_count": len(variants),
            "top_k": args.top_k,
            "dry_run": args.dry_run,
        },
        "concepts": [asdict(concept) for concept in concepts],
        "variants": [asdict(variant) for variant in variants],
        "model_summaries": model_summaries,
        "cross_model": compare_models(concepts, model_summaries, args.top_k),
        "embeddings": raw_embeddings,
    }

    output = json.dumps(payload, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    print(json.dumps(public_summary(payload), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
