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
VALENCE_CONTROL_PAIRS = (
    ("valence", "activation_vector"),
    ("valence", "steering_vector"),
)
DEFAULT_DISTRACTORS = {
    "attractor_network": "prototype",
    "homeostasis": "self_boundary",
    "weak_constraint": "simplicity_bias",
    "representation_manifold": "embedding",
    "activation_vector": "embedding",
    "steering_vector": "embedding",
}
DEFAULT_SCALES = (0.5, 1.0)


@dataclass(frozen=True)
class SteeringPair:
    left: str
    right: str
    kind: str
    distractor: str


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


def default_pair_specs(concepts: list[Concept]) -> list[SteeringPair]:
    concept_ids = {concept.id for concept in concepts}
    rows = []
    for kind, pairs in (
        ("positive", PROMOTED_STEERING_PAIRS),
        ("exploratory", EXPLORATORY_STEERING_PAIRS),
        ("control", VALENCE_CONTROL_PAIRS),
    ):
        for left, right in pairs:
            distractor = DEFAULT_DISTRACTORS[right]
            if left not in concept_ids or right not in concept_ids or distractor not in concept_ids:
                raise ValueError(f"Missing concept for pair {pair_id(left, right)}")
            rows.append(
                SteeringPair(
                    left=left,
                    right=right,
                    kind=kind,
                    distractor=distractor,
                )
            )
    return rows


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
