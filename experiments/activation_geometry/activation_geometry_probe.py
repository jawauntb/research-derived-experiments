#!/usr/bin/env python3
"""Probe concept geometry in open-model activation spaces."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from experiments.concept_geometry.openai_embedding_probe import (
    Concept,
    cosine,
    load_concepts,
    mean,
    pairwise_similarities,
    summarize,
)
from experiments.concept_geometry.paraphrase_stability_probe import (
    BRIDGE_PAIRS,
    load_paraphrases,
    variant_concepts,
)


DEFAULT_MODEL_ID = "EleutherAI/pythia-70m-deduped"
DEFAULT_LAYER = -1


@dataclass(frozen=True)
class ActivationRecord:
    id: str
    concept_id: str
    label: str
    category: str
    variant_index: int
    text: str


def activation_records(concepts: list[Concept], paraphrase_path: Path) -> list[ActivationRecord]:
    paraphrases = load_paraphrases(paraphrase_path, concepts)
    variants = variant_concepts(concepts, paraphrases)
    return [
        ActivationRecord(
            id=variant.id,
            concept_id=variant.concept_id,
            label=variant.label,
            category=variant.category,
            variant_index=variant.variant_index,
            text=variant.prompt,
        )
        for variant in variants
    ]


def deterministic_activation(text: str, *, layer: int, dimensions: int = 96) -> list[float]:
    values: list[float] = []
    counter = 0
    while len(values) < dimensions:
        digest = hashlib.sha256(f"{layer}:{counter}:{text}".encode("utf-8")).digest()
        for byte in digest:
            values.append((byte / 127.5) - 1.0)
            if len(values) == dimensions:
                break
        counter += 1
    return values


def extract_transformer_activations(
    records: list[ActivationRecord],
    *,
    model_id: str,
    layer: int,
    batch_size: int,
    max_length: int,
) -> list[list[float]]:
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    try:
        torch = importlib.import_module("torch")
        transformers = importlib.import_module("transformers")
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Torch and Transformers are required unless --dry-run is used."
        ) from error

    token = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN") or None
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_id, token=token)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_id,
        dtype=torch.bfloat16 if device.type == "cuda" else torch.float32,
        token=token,
    )
    model.to(device)
    model.eval()

    activations: list[list[float]] = []
    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        encoded = tokenizer(
            [record.text for record in batch],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_length,
        )
        encoded = {name: value.to(device) for name, value in encoded.items()}
        with torch.inference_mode():
            outputs = model(**encoded, output_hidden_states=True, use_cache=False)
        hidden_states = outputs.hidden_states
        if not -len(hidden_states) <= layer < len(hidden_states):
            raise ValueError(
                f"Layer {layer} is outside hidden-state range "
                f"[-{len(hidden_states)}, {len(hidden_states) - 1}]"
            )
        pooled = mean_pool(hidden_states[layer], encoded["attention_mask"])
        activations.extend(pooled.float().cpu().tolist())
    return activations


def mean_pool(hidden_states: Any, attention_mask: Any) -> Any:
    mask = attention_mask.to(hidden_states.device).unsqueeze(-1).type_as(hidden_states)
    return (hidden_states * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)


def normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return [0.0 for _ in vector]
    return [value / norm for value in vector]


def centroid(vectors: list[list[float]]) -> list[float]:
    dimensions = len(vectors[0])
    averaged = [sum(vector[index] for vector in vectors) / len(vectors) for index in range(dimensions)]
    return normalize(averaged)


def center_vectors(vectors: list[list[float]]) -> list[list[float]]:
    dimensions = len(vectors[0])
    global_mean = [sum(vector[index] for vector in vectors) / len(vectors) for index in range(dimensions)]
    return [
        [value - global_mean[index] for index, value in enumerate(vector)]
        for vector in vectors
    ]


def concept_centroids(
    concepts: list[Concept],
    records: list[ActivationRecord],
    vectors: list[list[float]],
) -> list[list[float]]:
    by_concept: dict[str, list[list[float]]] = {concept.id: [] for concept in concepts}
    for record, vector in zip(records, vectors, strict=True):
        by_concept[record.concept_id].append(vector)
    return [centroid(by_concept[concept.id]) for concept in concepts]


def paraphrase_cohesion(
    concepts: list[Concept],
    records: list[ActivationRecord],
    vectors: list[list[float]],
) -> dict[str, Any]:
    by_concept: dict[str, list[list[float]]] = {concept.id: [] for concept in concepts}
    for record, vector in zip(records, vectors, strict=True):
        by_concept[record.concept_id].append(vector)

    means = []
    minimums = []
    by_concept_summary: dict[str, dict[str, float]] = {}
    for concept in concepts:
        similarities = []
        concept_vectors = by_concept[concept.id]
        for left_index, left in enumerate(concept_vectors):
            for right_index, right in enumerate(concept_vectors):
                if left_index >= right_index:
                    continue
                similarities.append(cosine(left, right))
        concept_mean = mean(similarities)
        concept_minimum = min(similarities)
        means.append(concept_mean)
        minimums.append(concept_minimum)
        by_concept_summary[concept.id] = {
            "mean_pairwise_cosine": concept_mean,
            "min_pairwise_cosine": concept_minimum,
        }

    return {
        "mean_paraphrase_cohesion": mean(means),
        "min_concept_mean_cohesion": min(means),
        "min_variant_pair_cohesion": min(minimums),
        "by_concept": by_concept_summary,
    }


def bridge_scores(
    concepts: list[Concept],
    concept_vectors: list[list[float]],
) -> list[dict[str, Any]]:
    index_by_id = {concept.id: index for index, concept in enumerate(concepts)}
    rows = []
    for left_id, right_id in BRIDGE_PAIRS:
        if left_id not in index_by_id or right_id not in index_by_id:
            continue
        rows.append(
            {
                "left": left_id,
                "right": right_id,
                "cosine": cosine(
                    concept_vectors[index_by_id[left_id]],
                    concept_vectors[index_by_id[right_id]],
                ),
            }
        )
    return rows


def bridge_lift(
    concepts: list[Concept],
    concept_vectors: list[list[float]],
) -> dict[str, Any]:
    bridge_set = {frozenset(pair) for pair in BRIDGE_PAIRS}
    bridge_rows = bridge_scores(concepts, concept_vectors)
    non_bridge_cross_category = [
        row["cosine"]
        for row in pairwise_similarities(concepts, concept_vectors)
        if not row["same_category"] and frozenset((row["left"], row["right"])) not in bridge_set
    ]
    bridge_values = [row["cosine"] for row in bridge_rows]
    non_bridge_mean = mean(non_bridge_cross_category)
    return {
        "bridge_scores": bridge_rows,
        "mean_bridge_cosine": mean(bridge_values),
        "mean_non_bridge_cross_category_cosine": non_bridge_mean,
        "bridge_lift": mean(bridge_values) - non_bridge_mean,
        "bridge_pairs_above_non_bridge_mean_rate": (
            sum(1 for value in bridge_values if value > non_bridge_mean) / len(bridge_values)
            if bridge_values
            else float("nan")
        ),
    }


def activation_norms(vectors: list[list[float]]) -> dict[str, float]:
    norms = [math.sqrt(sum(value * value for value in vector)) for vector in vectors]
    return {
        "mean": mean(norms),
        "min": min(norms),
        "max": max(norms),
    }


def geometry_summary(
    concepts: list[Concept],
    records: list[ActivationRecord],
    vectors: list[list[float]],
    *,
    top_k: int,
) -> dict[str, Any]:
    normalized_vectors = [normalize(vector) for vector in vectors]
    centroids = concept_centroids(concepts, records, normalized_vectors)
    return {
        "activation_norms": activation_norms(vectors),
        "paraphrase_cohesion": paraphrase_cohesion(concepts, records, normalized_vectors),
        "centroid_summary": summarize(concepts, centroids, top_k),
        "bridge_lift": bridge_lift(concepts, centroids),
        "centroid_vectors": {
            concept.id: vector for concept, vector in zip(concepts, centroids, strict=True)
        },
    }


def summarize_activations(
    concepts: list[Concept],
    records: list[ActivationRecord],
    activations: list[list[float]],
    *,
    top_k: int,
) -> dict[str, Any]:
    return {
        "raw": geometry_summary(concepts, records, activations, top_k=top_k),
        "mean_centered": geometry_summary(
            concepts,
            records,
            center_vectors(activations),
            top_k=top_k,
        ),
    }


def payload_from_activations(
    *,
    concepts: list[Concept],
    records: list[ActivationRecord],
    activations: list[list[float]],
    model_id: str,
    layer: int,
    backend: str,
    top_k: int,
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "manifest": {
            "model_id": "deterministic-dry-run" if dry_run else model_id,
            "layer": layer,
            "backend": backend,
            "concept_count": len(concepts),
            "record_count": len(records),
            "activation_dim": len(activations[0]) if activations else 0,
            "top_k": top_k,
            "dry_run": dry_run,
        },
        "records": [asdict(record) for record in records],
        "summary": summarize_activations(concepts, records, activations, top_k=top_k),
        "activations": {
            record.id: vector for record, vector in zip(records, activations, strict=True)
        },
    }


def compact_geometry(summary: dict[str, Any]) -> dict[str, Any]:
    compact = {}
    for name in ("raw", "mean_centered"):
        geometry = summary[name]
        centroid = geometry["centroid_summary"]
        compact[name] = {
            "activation_norms": geometry["activation_norms"],
            "paraphrase_cohesion": {
                key: value
                for key, value in geometry["paraphrase_cohesion"].items()
                if key != "by_concept"
            },
            "centroid_summary": {
                "concept_count": centroid["concept_count"],
                "category_count": centroid["category_count"],
                "within_category_mean_cosine": centroid["within_category_mean_cosine"],
                "across_category_mean_cosine": centroid["across_category_mean_cosine"],
                "category_separation": centroid["category_separation"],
                "mean_top_k_same_category_rate": centroid["mean_top_k_same_category_rate"],
            },
            "bridge_lift": {
                key: value
                for key, value in geometry["bridge_lift"].items()
                if key != "bridge_scores"
            },
            "bridge_scores": geometry["bridge_lift"]["bridge_scores"],
        }
    return compact


def public_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "manifest": payload["manifest"],
        "summary": compact_geometry(payload["summary"]),
    }


def write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concepts", type=Path, required=True)
    parser.add_argument("--paraphrases", type=Path, required=True)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--layer", type=int, default=DEFAULT_LAYER)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=96)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    concepts = load_concepts(args.concepts)
    records = activation_records(concepts, args.paraphrases)
    activations = (
        [
            deterministic_activation(record.text, layer=args.layer)
            for record in records
        ]
        if args.dry_run
        else extract_transformer_activations(
            records,
            model_id=args.model_id,
            layer=args.layer,
            batch_size=args.batch_size,
            max_length=args.max_length,
        )
    )
    payload = payload_from_activations(
        concepts=concepts,
        records=records,
        activations=activations,
        model_id=args.model_id,
        layer=args.layer,
        backend="dry-run" if args.dry_run else "local-transformers",
        top_k=args.top_k,
        dry_run=args.dry_run,
    )
    if args.out:
        write_payload(args.out, payload)
    print(json.dumps(public_summary(payload), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
