#!/usr/bin/env python3
"""Helpers for final-token activation steering pilots."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from experiments.concept_geometry.openai_embedding_probe import Concept


PROMOTED_STEERING_PAIRS = (
    ("attractor", "attractor_network"),
    ("autopoiesis", "homeostasis"),
    ("validity_gate", "weak_constraint"),
)
EXPLORATORY_STEERING_PAIRS = (
    ("conceptual_space", "representation_manifold"),
)
EXPANDED_POSITIVE_STEERING_PAIRS = (
    *PROMOTED_STEERING_PAIRS,
    *EXPLORATORY_STEERING_PAIRS,
    ("phase_space", "conceptual_space"),
    ("fixed_point", "prototype"),
    ("basin_of_attraction", "schema"),
)
LAYER3_STRICT_POCKET_POSITIVE_PAIRS = (
    ("attractor", "attractor_network"),
    ("fixed_point", "prototype"),
)
LAYER3_STRICT_POCKET_SMOKE_POSITIVE_PAIRS = (
    ("attractor", "attractor_network"),
)
VALENCE_CONTROL_PAIRS = (
    ("valence", "activation_vector"),
    ("valence", "steering_vector"),
)
EXPANDED_CONTROL_PAIRS = (
    *VALENCE_CONTROL_PAIRS,
    ("simplicity_bias", "embedding"),
    ("semantic_distance", "validity_gate"),
    ("homeostasis", "representation_manifold"),
)
TARGET_DISJOINT_CONTROL_PAIRS = (
    ("valence", "activation_vector"),
    ("valence", "steering_vector"),
    ("simplicity_bias", "embedding"),
    ("semantic_distance", "validity_gate"),
    ("family_resemblance", "regime_transition"),
    ("self_boundary", "residual_content"),
)
RANDOM_RELATION_NULL_PAIRS = (
    ("valence", "steering_vector"),
    ("schema_revision", "steering_vector"),
    ("embedding", "residual_content"),
    ("residual_content", "self_boundary"),
    ("steering_vector", "semantic_distance"),
    ("residual_content", "valence"),
    ("self_boundary", "embedding"),
    ("regime_transition", "activation_vector"),
    ("regime_transition", "family_resemblance"),
    ("simplicity_bias", "residual_content"),
)
DEFAULT_DISTRACTORS = {
    "attractor_network": "prototype",
    "homeostasis": "self_boundary",
    "weak_constraint": "simplicity_bias",
    "representation_manifold": "embedding",
    "conceptual_space": "semantic_distance",
    "prototype": "schema",
    "schema": "prototype",
    "embedding": "activation_vector",
    "validity_gate": "simplicity_bias",
    "regime_transition": "schema_revision",
    "residual_content": "schema_revision",
    "activation_vector": "embedding",
    "steering_vector": "embedding",
}
FALLBACK_DISTRACTOR_PRIORITY = (
    "prototype",
    "schema_revision",
    "embedding",
    "simplicity_bias",
    "self_boundary",
    "semantic_distance",
    "activation_vector",
    "homeostasis",
)
DEFAULT_SCALES = (0.5, 1.0)


@dataclass(frozen=True)
class SteeringPair:
    left: str
    right: str
    kind: str
    distractor: str
    control_class: str = ""


def pair_id(left: str, right: str) -> str:
    return f"{left}->{right}"


def parse_scales(value: str) -> list[float]:
    scales = []
    for part in value.split(","):
        token = part.strip()
        if not token:
            continue
        scales.append(float(token))
    if not scales:
        raise ValueError("At least one scale must be provided")
    return scales


def concept_by_id(concepts: list[Concept]) -> dict[str, Concept]:
    return {concept.id: concept for concept in concepts}


def distractor_for(*, left: str, right: str, concept_ids: set[str]) -> str:
    default = DEFAULT_DISTRACTORS.get(right)
    if default:
        return default
    blocked = {left, right}
    for candidate in FALLBACK_DISTRACTOR_PRIORITY:
        if candidate in concept_ids and candidate not in blocked:
            return candidate
    for candidate in sorted(concept_ids):
        if candidate not in blocked:
            return candidate
    raise ValueError(f"Could not choose distractor for {pair_id(left, right)}")


def pair_specs_for_set(concepts: list[Concept], *, pair_set: str) -> list[SteeringPair]:
    concept_ids = {concept.id for concept in concepts}
    rows = []
    if pair_set == "promoted":
        pair_groups = (
            ("positive", PROMOTED_STEERING_PAIRS, ""),
            ("exploratory", EXPLORATORY_STEERING_PAIRS, ""),
            ("control", VALENCE_CONTROL_PAIRS, "valence"),
        )
    elif pair_set == "expanded":
        pair_groups = (
            ("positive", EXPANDED_POSITIVE_STEERING_PAIRS, ""),
            ("control", EXPANDED_CONTROL_PAIRS, "mixed_handpicked"),
        )
    elif pair_set == "expanded_target_disjoint":
        pair_groups = (
            ("positive", EXPANDED_POSITIVE_STEERING_PAIRS, ""),
            ("control", TARGET_DISJOINT_CONTROL_PAIRS, "target_disjoint"),
        )
    elif pair_set == "expanded_random_nulls":
        pair_groups = (
            ("positive", EXPANDED_POSITIVE_STEERING_PAIRS, ""),
            ("control", RANDOM_RELATION_NULL_PAIRS, "random_relation_null"),
        )
    elif pair_set == "layer3_strict_pocket_random_nulls":
        pair_groups = (
            ("positive", LAYER3_STRICT_POCKET_POSITIVE_PAIRS, ""),
            ("control", RANDOM_RELATION_NULL_PAIRS, "random_relation_null"),
        )
    elif pair_set == "layer3_strict_pocket_smoke":
        pair_groups = (
            ("positive", LAYER3_STRICT_POCKET_SMOKE_POSITIVE_PAIRS, ""),
            ("control", (("valence", "steering_vector"),), "random_relation_null"),
        )
    else:
        raise ValueError(
            "Pair set must be one of: promoted, expanded, "
            "expanded_target_disjoint, expanded_random_nulls, "
            "layer3_strict_pocket_random_nulls, layer3_strict_pocket_smoke"
        )
    for kind, pairs, control_class in pair_groups:
        for left, right in pairs:
            distractor = distractor_for(left=left, right=right, concept_ids=concept_ids)
            if left not in concept_ids or right not in concept_ids or distractor not in concept_ids:
                raise ValueError(f"Missing concept for pair {pair_id(left, right)}")
            rows.append(
                SteeringPair(
                    left=left,
                    right=right,
                    kind=kind,
                    distractor=distractor,
                    control_class=control_class,
                )
            )
    return rows


def default_pair_specs(concepts: list[Concept]) -> list[SteeringPair]:
    return pair_specs_for_set(concepts, pair_set="promoted")


def steering_prompt(
    *,
    source_text: str,
    source_label: str,
    target_label: str,
    distractor_label: str,
) -> str:
    return (
        f"{source_text}\n\n"
        "Choose the closest related concept.\n"
        f"A. {source_label}\n"
        f"B. {target_label}\n"
        f"C. {distractor_label}\n"
        "Answer:"
    )


def target_margin(scores: dict[str, float]) -> float:
    return scores["target"] - ((scores["source"] + scores["distractor"]) / 2)


def target_minus_source(scores: dict[str, float]) -> float:
    return scores["target"] - scores["source"]


def summarize_scale(
    *,
    baseline_scores: dict[str, float],
    forward_scores: dict[str, float],
    reverse_scores: dict[str, float],
) -> dict[str, Any]:
    baseline_margin = target_margin(baseline_scores)
    forward_margin = target_margin(forward_scores)
    reverse_margin = target_margin(reverse_scores)
    baseline_target_minus_source = target_minus_source(baseline_scores)
    forward_target_minus_source = target_minus_source(forward_scores)
    reverse_target_minus_source = target_minus_source(reverse_scores)
    forward_delta = forward_margin - baseline_margin
    reverse_delta = reverse_margin - baseline_margin
    return {
        "baseline_target_margin": baseline_margin,
        "forward_target_margin": forward_margin,
        "reverse_target_margin": reverse_margin,
        "forward_margin_delta": forward_delta,
        "reverse_margin_delta": reverse_delta,
        "signed_margin_effect": forward_delta - reverse_delta,
        "baseline_target_minus_source": baseline_target_minus_source,
        "forward_target_minus_source": forward_target_minus_source,
        "reverse_target_minus_source": reverse_target_minus_source,
        "forward_target_minus_source_delta": (
            forward_target_minus_source - baseline_target_minus_source
        ),
        "reverse_target_minus_source_delta": (
            reverse_target_minus_source - baseline_target_minus_source
        ),
        "passes_signed_margin_gate": forward_delta > 0 and reverse_delta < 0,
    }


def compact_steering_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "pair": row["pair"],
            "kind": row["kind"],
            "role": row["role"],
            "layer": row["layer"],
            "scale": row["scale"],
            "direction_norm": row["direction_norm"],
            "forward_margin_delta": row["summary"]["forward_margin_delta"],
            "reverse_margin_delta": row["summary"]["reverse_margin_delta"],
            "signed_margin_effect": row["summary"]["signed_margin_effect"],
            "passes_signed_margin_gate": row["summary"]["passes_signed_margin_gate"],
        }
        for row in rows
    ]


def gate_summary(rows: list[dict[str, Any]], *, scale: float) -> dict[str, Any]:
    selected = [row for row in rows if row["scale"] == scale]
    primary_positive = [
        row for row in selected if row["role"] == "primary" and row["kind"] == "positive"
    ]
    backup_positive = [
        row for row in selected if row["role"] == "backup" and row["kind"] == "positive"
    ]
    control_positive = [
        row for row in selected if row["role"] == "control" and row["kind"] == "positive"
    ]
    primary_controls = [
        row for row in selected if row["role"] == "primary" and row["kind"] == "control"
    ]
    return {
        "scale": scale,
        "primary_positive_pass_count": sum(
            1 for row in primary_positive if row["summary"]["passes_signed_margin_gate"]
        ),
        "primary_positive_total": len(primary_positive),
        "backup_positive_pass_count": sum(
            1 for row in backup_positive if row["summary"]["passes_signed_margin_gate"]
        ),
        "backup_positive_total": len(backup_positive),
        "control_layer_positive_pass_count": sum(
            1 for row in control_positive if row["summary"]["passes_signed_margin_gate"]
        ),
        "control_layer_positive_total": len(control_positive),
        "primary_valence_control_pass_count": sum(
            1 for row in primary_controls if row["summary"]["passes_signed_margin_gate"]
        ),
        "primary_valence_control_total": len(primary_controls),
    }


def public_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "manifest": payload["manifest"],
        "gate_summaries": payload["gate_summaries"],
        "rows": compact_steering_rows(payload["rows"]),
    }


def write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def serializable_pair_specs(pairs: list[SteeringPair]) -> list[dict[str, Any]]:
    return [asdict(pair) for pair in pairs]
