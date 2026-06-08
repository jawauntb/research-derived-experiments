#!/usr/bin/env python3
"""Held-out paraphrase readout pilot for activation geometry."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from experiments.activation_geometry.activation_geometry_probe import (
    ActivationRecord,
    centroid,
    normalize,
    parse_layers,
    write_payload,
)
from experiments.concept_geometry.openai_embedding_probe import (
    Concept,
    cosine,
    load_concepts,
    mean,
    pairwise_similarities,
)
from experiments.concept_geometry.paraphrase_stability_probe import BRIDGE_PAIRS


POSITIVE_BRIDGE_CANDIDATES = (
    ("attractor", "attractor_network"),
    ("conceptual_space", "representation_manifold"),
    ("autopoiesis", "homeostasis"),
    ("validity_gate", "weak_constraint"),
)
CONTROL_BRIDGE_CANDIDATES = (
    ("valence", "activation_vector"),
    ("valence", "steering_vector"),
)


def activation_records_from_payload(payload: dict[str, Any]) -> list[ActivationRecord]:
    return [
        ActivationRecord(
            id=str(record["id"]),
            concept_id=str(record["concept_id"]),
            label=str(record["label"]),
            category=str(record["category"]),
            variant_index=int(record["variant_index"]),
            text=str(record["text"]),
        )
        for record in payload["records"]
    ]


def vector_mean(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        raise ValueError("Cannot compute a mean over no vectors")
    dimensions = len(vectors[0])
    return [
        sum(vector[index] for vector in vectors) / len(vectors)
        for index in range(dimensions)
    ]


def subtract(left: list[float], right: list[float]) -> list[float]:
    return [left_value - right_value for left_value, right_value in zip(left, right)]


def centered_normalized_vectors(
    records: list[ActivationRecord],
    vectors_by_record: dict[str, list[float]],
    *,
    train_variant_indices: set[int],
) -> dict[str, list[float]]:
    train_vectors = [
        vectors_by_record[record.id]
        for record in records
        if record.variant_index in train_variant_indices
    ]
    train_mean = vector_mean(train_vectors)
    return {
        record.id: normalize(subtract(vectors_by_record[record.id], train_mean))
        for record in records
    }


def train_centroids(
    concepts: list[Concept],
    records: list[ActivationRecord],
    vectors_by_record: dict[str, list[float]],
    *,
    train_variant_indices: set[int],
) -> dict[str, list[float]]:
    by_concept: dict[str, list[list[float]]] = {concept.id: [] for concept in concepts}
    for record in records:
        if record.variant_index in train_variant_indices:
            by_concept[record.concept_id].append(vectors_by_record[record.id])
    return {
        concept.id: centroid(by_concept[concept.id])
        for concept in concepts
        if by_concept[concept.id]
    }


def nearest_concept(
    vector: list[float],
    centroids_by_concept: dict[str, list[float]],
) -> tuple[str, float]:
    scores = [
        (concept_id, cosine(vector, concept_vector))
        for concept_id, concept_vector in centroids_by_concept.items()
    ]
    return max(scores, key=lambda item: item[1])


def non_bridge_cross_category_mean(
    concepts: list[Concept],
    concept_vectors: list[list[float]],
) -> float:
    bridge_set = {frozenset(pair) for pair in BRIDGE_PAIRS}
    values = [
        row["cosine"]
        for row in pairwise_similarities(concepts, concept_vectors)
        if not row["same_category"]
        and frozenset((row["left"], row["right"])) not in bridge_set
    ]
    return mean(values)


def candidate_pair_rows(
    concepts: list[Concept],
    vectors_by_concept: dict[str, list[float]],
    candidate_pairs: tuple[tuple[str, str], ...],
    *,
    baseline: float,
) -> list[dict[str, Any]]:
    concept_ids = {concept.id for concept in concepts}
    rows = []
    for left, right in candidate_pairs:
        if left not in concept_ids or right not in concept_ids:
            continue
        value = cosine(vectors_by_concept[left], vectors_by_concept[right])
        rows.append(
            {
                "left": left,
                "right": right,
                "cosine": value,
                "above_non_bridge_mean": value > baseline,
            }
        )
    return rows


def concept_vectors_in_order(
    concepts: list[Concept],
    vectors_by_concept: dict[str, list[float]],
) -> list[list[float]]:
    return [vectors_by_concept[concept.id] for concept in concepts]


def heldout_layer_summary(
    *,
    concepts: list[Concept],
    records: list[ActivationRecord],
    vectors_by_record: dict[str, list[float]],
    train_variant_indices: set[int],
    holdout_variant_index: int,
) -> dict[str, Any]:
    centered_vectors = centered_normalized_vectors(
        records,
        vectors_by_record,
        train_variant_indices=train_variant_indices,
    )
    centroids_by_concept = train_centroids(
        concepts,
        records,
        centered_vectors,
        train_variant_indices=train_variant_indices,
    )
    category_by_concept = {concept.id: concept.category for concept in concepts}
    holdout_records = [
        record for record in records if record.variant_index == holdout_variant_index
    ]
    if len(holdout_records) != len(concepts):
        raise ValueError(
            f"Expected one holdout record per concept at variant {holdout_variant_index}; "
            f"found {len(holdout_records)} for {len(concepts)} concepts"
        )

    predictions = []
    correct_concept = 0
    correct_category = 0
    correct_scores = []
    nearest_scores = []
    for record in holdout_records:
        nearest_id, nearest_score = nearest_concept(
            centered_vectors[record.id],
            centroids_by_concept,
        )
        correct_score = cosine(
            centered_vectors[record.id],
            centroids_by_concept[record.concept_id],
        )
        is_concept_correct = nearest_id == record.concept_id
        is_category_correct = category_by_concept[nearest_id] == record.category
        correct_concept += int(is_concept_correct)
        correct_category += int(is_category_correct)
        correct_scores.append(correct_score)
        nearest_scores.append(nearest_score)
        predictions.append(
            {
                "concept_id": record.concept_id,
                "category": record.category,
                "nearest_concept_id": nearest_id,
                "nearest_category": category_by_concept[nearest_id],
                "nearest_cosine": nearest_score,
                "correct_concept_cosine": correct_score,
                "concept_correct": is_concept_correct,
                "category_correct": is_category_correct,
            }
        )

    holdout_vectors_by_concept = {
        record.concept_id: centered_vectors[record.id] for record in holdout_records
    }
    ordered_holdout_vectors = concept_vectors_in_order(concepts, holdout_vectors_by_concept)
    baseline = non_bridge_cross_category_mean(concepts, ordered_holdout_vectors)
    bridge_rows = candidate_pair_rows(
        concepts,
        holdout_vectors_by_concept,
        tuple(BRIDGE_PAIRS),
        baseline=baseline,
    )
    positive_rows = candidate_pair_rows(
        concepts,
        holdout_vectors_by_concept,
        POSITIVE_BRIDGE_CANDIDATES,
        baseline=baseline,
    )
    control_rows = candidate_pair_rows(
        concepts,
        holdout_vectors_by_concept,
        CONTROL_BRIDGE_CANDIDATES,
        baseline=baseline,
    )
    bridge_values = [row["cosine"] for row in bridge_rows]
    bridge_above_baseline_rate = (
        sum(1 for row in bridge_rows if row["above_non_bridge_mean"]) / len(bridge_rows)
        if bridge_rows
        else float("nan")
    )
    return {
        "holdout_variant_index": holdout_variant_index,
        "train_variant_indices": sorted(train_variant_indices),
        "holdout_count": len(holdout_records),
        "concept_accuracy": correct_concept / len(holdout_records),
        "category_accuracy": correct_category / len(holdout_records),
        "mean_correct_concept_cosine": mean(correct_scores),
        "mean_nearest_cosine": mean(nearest_scores),
        "heldout_non_bridge_cross_category_mean": baseline,
        "heldout_all_bridge_mean_cosine": mean(bridge_values),
        "heldout_all_bridge_lift": mean(bridge_values) - baseline,
        "heldout_all_bridge_above_baseline_rate": bridge_above_baseline_rate,
        "positive_candidate_pass_count": sum(
            1 for row in positive_rows if row["above_non_bridge_mean"]
        ),
        "positive_candidate_total": len(positive_rows),
        "control_pair_pass_count": sum(
            1 for row in control_rows if row["above_non_bridge_mean"]
        ),
        "control_pair_total": len(control_rows),
        "positive_candidate_pairs": positive_rows,
        "control_pairs": control_rows,
        "predictions": predictions,
    }


def vectors_for_layer(
    payload: dict[str, Any],
    layer: str,
) -> dict[str, list[float]]:
    return {
        str(record_id): vector
        for record_id, vector in payload["activations_by_layer"][layer].items()
    }


def summarize_payload(
    payload: dict[str, Any],
    *,
    concepts: list[Concept],
    train_variant_indices: set[int],
    holdout_variant_index: int,
    layers: list[int] | None,
) -> dict[str, Any]:
    records = activation_records_from_payload(payload)
    available_layers = [str(layer) for layer in payload["manifest"]["layers"]]
    selected_layers = [str(layer) for layer in layers] if layers else available_layers
    missing_layers = [layer for layer in selected_layers if layer not in available_layers]
    if missing_layers:
        raise ValueError(f"Payload does not contain layers: {', '.join(missing_layers)}")

    return {
        "manifest": {
            "model_id": payload["manifest"]["model_id"],
            "pooling": payload["manifest"].get("pooling", "unknown"),
            "layers": selected_layers,
            "train_variant_indices": sorted(train_variant_indices),
            "holdout_variant_index": holdout_variant_index,
            "record_count": len(records),
            "concept_count": len(concepts),
        },
        "layers": {
            layer: heldout_layer_summary(
                concepts=concepts,
                records=records,
                vectors_by_record=vectors_for_layer(payload, layer),
                train_variant_indices=train_variant_indices,
                holdout_variant_index=holdout_variant_index,
            )
            for layer in selected_layers
        },
    }


def public_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "manifest": payload["manifest"],
        "layers": {
            layer: {
                key: value
                for key, value in summary.items()
                if key not in {"predictions"}
            }
            for layer, summary in payload["layers"].items()
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concepts", type=Path, required=True)
    parser.add_argument("--payload", type=Path, action="append", required=True)
    parser.add_argument("--train-variants", default="0,1")
    parser.add_argument("--holdout-variant", type=int, default=2)
    parser.add_argument("--layers")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    concepts = load_concepts(args.concepts)
    train_variant_indices = set(parse_layers(args.train_variants))
    selected_layers = parse_layers(args.layers) if args.layers else None
    runs = []
    for path in args.payload:
        raw_payload = json.loads(path.read_text(encoding="utf-8"))
        runs.append(
            summarize_payload(
                raw_payload,
                concepts=concepts,
                train_variant_indices=train_variant_indices,
                holdout_variant_index=args.holdout_variant,
                layers=selected_layers,
            )
        )

    payload = {
        "manifest": {
            "payloads": [str(path) for path in args.payload],
            "train_variant_indices": sorted(train_variant_indices),
            "holdout_variant_index": args.holdout_variant,
            "concept_count": len(concepts),
        },
        "concepts": [asdict(concept) for concept in concepts],
        "runs": runs,
    }
    if args.out:
        write_payload(args.out, payload)
    print(json.dumps({"runs": [public_summary(run) for run in runs]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
