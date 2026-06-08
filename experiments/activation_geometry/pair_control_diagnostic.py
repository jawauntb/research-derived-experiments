#!/usr/bin/env python3
"""Pair-level controls for held-out activation bridge diagnostics."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from experiments.activation_geometry.activation_geometry_probe import (
    parse_layers,
    write_payload,
)
from experiments.activation_geometry.heldout_readout_pilot import (
    CONTROL_BRIDGE_CANDIDATES,
    POSITIVE_BRIDGE_CANDIDATES,
    activation_records_from_payload,
    centered_normalized_vectors,
    concept_vectors_in_order,
    non_bridge_cross_category_mean,
    vectors_for_layer,
)
from experiments.concept_geometry.openai_embedding_probe import (
    Concept,
    cosine,
    load_concepts,
    mean,
)
from experiments.concept_geometry.paraphrase_stability_probe import BRIDGE_PAIRS


DEFAULT_SHUFFLE_COUNT = 512
DEFAULT_SEED = 20260608


def concept_by_id(concepts: list[Concept]) -> dict[str, Concept]:
    return {concept.id: concept for concept in concepts}


def category_ids(concepts: list[Concept]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for concept in concepts:
        groups.setdefault(concept.category, []).append(concept.id)
    return groups


def pair_key(
    category_by_concept: dict[str, str],
    left: str,
    right: str,
) -> tuple[str, str]:
    left_category = category_by_concept[left]
    right_category = category_by_concept[right]
    return (
        (left_category, right_category)
        if left_category <= right_category
        else (right_category, left_category)
    )


def pair_token(left: str, right: str) -> frozenset[str]:
    return frozenset((left, right))


def all_candidate_pairs() -> tuple[tuple[str, str], ...]:
    return POSITIVE_BRIDGE_CANDIDATES + CONTROL_BRIDGE_CANDIDATES


def all_unordered_pairs(concepts: list[Concept]) -> list[tuple[str, str]]:
    pairs = []
    for left_index, left in enumerate(concepts):
        for right in concepts[left_index + 1 :]:
            pairs.append((left.id, right.id))
    return pairs


def quantile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = position - lower
    return sorted_values[lower] * (1 - fraction) + sorted_values[upper] * fraction


def empirical_p_value(value: float, controls: list[float]) -> float:
    if not controls:
        return float("nan")
    return (sum(1 for control in controls if control >= value) + 1) / (len(controls) + 1)


def matched_control_values(
    *,
    concepts: list[Concept],
    vectors_by_concept: dict[str, list[float]],
    left: str,
    right: str,
) -> list[float]:
    category_by_concept = {
        concept.id: concept.category for concept in concepts
    }
    target_key = pair_key(category_by_concept, left, right)
    bridge_tokens = {pair_token(*pair) for pair in BRIDGE_PAIRS}
    candidate_token = pair_token(left, right)
    values = []
    for control_left, control_right in all_unordered_pairs(concepts):
        control_token = pair_token(control_left, control_right)
        if control_token == candidate_token or control_token in bridge_tokens:
            continue
        if pair_key(category_by_concept, control_left, control_right) != target_key:
            continue
        values.append(
            cosine(
                vectors_by_concept[control_left],
                vectors_by_concept[control_right],
            )
        )
    return values


def category_preserving_shuffle_values(
    *,
    concepts: list[Concept],
    vectors_by_concept: dict[str, list[float]],
    left: str,
    right: str,
    count: int,
    seed: int,
) -> list[float]:
    groups = category_ids(concepts)
    bridge_tokens = {pair_token(*pair) for pair in BRIDGE_PAIRS}
    candidate_token = pair_token(left, right)
    rng = random.Random(seed)
    values = []
    categories = sorted(groups)
    for _ in range(count):
        mapping: dict[str, str] = {}
        for category in categories:
            original_ids = groups[category]
            shuffled_ids = list(original_ids)
            rng.shuffle(shuffled_ids)
            mapping.update(zip(original_ids, shuffled_ids))
        shuffled_left = mapping[left]
        shuffled_right = mapping[right]
        shuffled_token = pair_token(shuffled_left, shuffled_right)
        if shuffled_token == candidate_token or shuffled_token in bridge_tokens:
            continue
        values.append(
            cosine(
                vectors_by_concept[shuffled_left],
                vectors_by_concept[shuffled_right],
            )
        )
    return values


def diagnostic_row(
    *,
    concepts: list[Concept],
    vectors_by_concept: dict[str, list[float]],
    left: str,
    right: str,
    baseline: float,
    shuffle_count: int,
    seed: int,
) -> dict[str, Any]:
    concept_lookup = concept_by_id(concepts)
    value = cosine(vectors_by_concept[left], vectors_by_concept[right])
    matched_values = matched_control_values(
        concepts=concepts,
        vectors_by_concept=vectors_by_concept,
        left=left,
        right=right,
    )
    shuffled_values = category_preserving_shuffle_values(
        concepts=concepts,
        vectors_by_concept=vectors_by_concept,
        left=left,
        right=right,
        count=shuffle_count,
        seed=seed,
    )
    matched_p95 = quantile(matched_values, 0.95)
    shuffled_p95 = quantile(shuffled_values, 0.95)
    above_non_bridge_mean = value > baseline
    above_matched_p95 = value > matched_p95 if matched_values else False
    above_shuffled_p95 = value > shuffled_p95 if shuffled_values else False
    return {
        "left": left,
        "right": right,
        "left_category": concept_lookup[left].category,
        "right_category": concept_lookup[right].category,
        "cosine": value,
        "above_non_bridge_mean": above_non_bridge_mean,
        "matched_control_count": len(matched_values),
        "matched_control_mean": mean(matched_values),
        "matched_control_p95": matched_p95,
        "matched_empirical_p": empirical_p_value(value, matched_values),
        "above_matched_control_p95": above_matched_p95,
        "shuffled_label_count": len(shuffled_values),
        "shuffled_label_mean": mean(shuffled_values),
        "shuffled_label_p95": shuffled_p95,
        "shuffled_empirical_p": empirical_p_value(value, shuffled_values),
        "above_shuffled_label_p95": above_shuffled_p95,
        "promoted_for_steering": (
            above_non_bridge_mean and above_matched_p95 and above_shuffled_p95
        ),
    }


def diagnostic_for_layer(
    *,
    concepts: list[Concept],
    vectors_by_concept: dict[str, list[float]],
    shuffle_count: int,
    seed: int,
) -> dict[str, Any]:
    ordered_vectors = concept_vectors_in_order(concepts, vectors_by_concept)
    baseline = non_bridge_cross_category_mean(concepts, ordered_vectors)
    positive_rows = [
        diagnostic_row(
            concepts=concepts,
            vectors_by_concept=vectors_by_concept,
            left=left,
            right=right,
            baseline=baseline,
            shuffle_count=shuffle_count,
            seed=seed + index,
        )
        for index, (left, right) in enumerate(POSITIVE_BRIDGE_CANDIDATES)
    ]
    control_rows = [
        diagnostic_row(
            concepts=concepts,
            vectors_by_concept=vectors_by_concept,
            left=left,
            right=right,
            baseline=baseline,
            shuffle_count=shuffle_count,
            seed=seed + len(POSITIVE_BRIDGE_CANDIDATES) + index,
        )
        for index, (left, right) in enumerate(CONTROL_BRIDGE_CANDIDATES)
    ]
    return {
        "heldout_non_bridge_cross_category_mean": baseline,
        "positive_candidate_pairs": positive_rows,
        "control_pairs": control_rows,
        "positive_promoted_count": sum(
            1 for row in positive_rows if row["promoted_for_steering"]
        ),
        "positive_candidate_total": len(positive_rows),
        "control_promoted_count": sum(
            1 for row in control_rows if row["promoted_for_steering"]
        ),
        "control_pair_total": len(control_rows),
    }


def holdout_vectors_by_concept(
    payload: dict[str, Any],
    *,
    concepts: list[Concept],
    layer: str,
    train_variant_indices: set[int],
    holdout_variant_index: int,
) -> dict[str, list[float]]:
    records = activation_records_from_payload(payload)
    centered_vectors = centered_normalized_vectors(
        records,
        vectors_for_layer(payload, layer),
        train_variant_indices=train_variant_indices,
    )
    holdout_records = [
        record for record in records if record.variant_index == holdout_variant_index
    ]
    if len(holdout_records) != len(concepts):
        raise ValueError(
            f"Expected one holdout record per concept at variant {holdout_variant_index}; "
            f"found {len(holdout_records)} for {len(concepts)} concepts"
        )
    return {record.concept_id: centered_vectors[record.id] for record in holdout_records}


def summarize_payload(
    payload: dict[str, Any],
    *,
    concepts: list[Concept],
    train_variant_indices: set[int],
    holdout_variant_index: int,
    layers: list[int] | None,
    shuffle_count: int,
    seed: int,
) -> dict[str, Any]:
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
            "shuffle_count": shuffle_count,
            "seed": seed,
            "concept_count": len(concepts),
        },
        "layers": {
            layer: diagnostic_for_layer(
                concepts=concepts,
                vectors_by_concept=holdout_vectors_by_concept(
                    payload,
                    concepts=concepts,
                    layer=layer,
                    train_variant_indices=train_variant_indices,
                    holdout_variant_index=holdout_variant_index,
                ),
                shuffle_count=shuffle_count,
                seed=seed + layer_index * 1009,
            )
            for layer_index, layer in enumerate(selected_layers)
        },
    }


def public_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "manifest": payload["manifest"],
        "layers": {
            layer: {
                "heldout_non_bridge_cross_category_mean": summary[
                    "heldout_non_bridge_cross_category_mean"
                ],
                "positive_promoted_count": summary["positive_promoted_count"],
                "positive_candidate_total": summary["positive_candidate_total"],
                "control_promoted_count": summary["control_promoted_count"],
                "control_pair_total": summary["control_pair_total"],
                "positive_candidate_pairs": summary["positive_candidate_pairs"],
                "control_pairs": summary["control_pairs"],
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
    parser.add_argument("--shuffle-count", type=int, default=DEFAULT_SHUFFLE_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
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
                shuffle_count=args.shuffle_count,
                seed=args.seed,
            )
        )

    payload = {
        "manifest": {
            "payloads": [str(path) for path in args.payload],
            "train_variant_indices": sorted(train_variant_indices),
            "holdout_variant_index": args.holdout_variant,
            "shuffle_count": args.shuffle_count,
            "seed": args.seed,
            "concept_count": len(concepts),
            "candidate_pairs": [
                {"left": left, "right": right}
                for left, right in all_candidate_pairs()
            ],
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
