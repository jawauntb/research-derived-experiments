#!/usr/bin/env python3
"""Label-free role-slot induction for the 2A-v2 transfer contract.

This sidecar keeps the Phase 2 claim narrow. It does not discover arbitrary
objects, natural-image semantics, or a new program grammar. It starts from the
same rendered connected components used by the pixel gates, clusters component
appearance without role-token labels, grounds each induced active-cluster pair
through rich-program feedback, and then consumes the existing v2 transfer
repair contract. The semantic profile table is still supplied; the result is
label-free role-token calibration, not fully unsupervised semantic discovery.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from experiments.concerned_syntax import rich_program_language as rich
from experiments.concerned_syntax.benchmark import (
    HIGH_CONCERN_KINDS,
    LOW_CONCERN_KINDS,
    PARSES,
    ParseCandidate,
    ShapeTrial,
    _same_subtree,
    concern_gap,
    outcome_for_parse,
    preferred_action,
    utility,
)
from experiments.concerned_syntax.intervention_invention import (
    _padded_components,
    _random_pair,
)
from experiments.concerned_syntax.pixel_shapes import ExtractedComponent


UNSUPERVISED_SEMANTIC_AGENTS: tuple[str, ...] = (
    "learned_rich_program_composer",
    "unsupervised_semantic_family_only",
    "unsupervised_semantic_target_only",
    "unsupervised_semantic_rich_without_concern",
    "unsupervised_slot_semantic_world_model",
)

HELDOUT_ROLE_KINDS: tuple[str, ...] = HIGH_CONCERN_KINDS
HELDOUT_TRUE_PARSES: tuple[str, ...] = tuple(parse.name for parse in PARSES)


@dataclass(frozen=True)
class InducedKindProfile:
    kind: str
    family: str
    concern_weight: float
    role_pair: tuple[str, str]


KIND_PROFILES: dict[str, InducedKindProfile] = {
    "shield_poison": InducedKindProfile(
        kind="shield_poison",
        family="compose_move_observe",
        concern_weight=1.4,
        role_pair=("shield", "poison"),
    ),
    "repair_core": InducedKindProfile(
        kind="repair_core",
        family="move_anchor",
        concern_weight=1.2,
        role_pair=("repair", "core"),
    ),
    "food_trap": InducedKindProfile(
        kind="food_trap",
        family="ablate_pair",
        concern_weight=1.0,
        role_pair=("food", "trap"),
    ),
    "ornament_signal": InducedKindProfile(
        kind="ornament_signal",
        family="observe_pair",
        concern_weight=0.2,
        role_pair=("signal", "ornament"),
    ),
}

PROFILE_ORDER: tuple[str, ...] = tuple(HIGH_CONCERN_KINDS + LOW_CONCERN_KINDS)


@dataclass(frozen=True)
class UnsupervisedSlotInducer:
    cluster_centers: tuple[tuple[float, ...], ...]
    neutral_cluster: int
    pair_profiles: dict[tuple[int, int], InducedKindProfile]
    profile_support: dict[tuple[int, int], int]
    calibration_trials: int
    objective: str

    def cluster_for_component(self, component: ExtractedComponent) -> int:
        features = component_induction_features(component)
        return _nearest_center(features, self.cluster_centers)

    def component_clusters(self, example: rich.PixelExample) -> tuple[int, ...]:
        return tuple(
            self.cluster_for_component(component)
            for component in _padded_components(example)
        )

    def nonneutral_margin(self, component: ExtractedComponent) -> float:
        features = component_induction_features(component)
        neutral_distance = _squared_distance(
            features,
            self.cluster_centers[self.neutral_cluster],
        )
        active_distance = min(
            _squared_distance(features, center)
            for idx, center in enumerate(self.cluster_centers)
            if idx != self.neutral_cluster
        )
        return neutral_distance - active_distance

    def semantic_pair(self, example: rich.PixelExample) -> tuple[int, int]:
        return _semantic_pair_for_clusters(
            _padded_components(example),
            self.component_clusters(example),
            self.neutral_cluster,
            self,
        )

    def active_cluster_pair(self, example: rich.PixelExample) -> tuple[int, int]:
        clusters = self.component_clusters(example)
        pair = self.semantic_pair(example)
        left, right = sorted((clusters[pair[0]], clusters[pair[1]]))
        return (left, right)

    def profile_for_cluster_pair(
        self,
        cluster_pair: tuple[int, int],
    ) -> InducedKindProfile:
        if cluster_pair in self.pair_profiles:
            return self.pair_profiles[cluster_pair]
        if not self.pair_profiles:
            return KIND_PROFILES["ornament_signal"]
        return self.pair_profiles[
            min(
                self.pair_profiles,
                key=lambda known: _cluster_pair_distance(
                    cluster_pair,
                    known,
                    self.cluster_centers,
                ),
            )
        ]

    def profile_for_example(self, example: rich.PixelExample) -> InducedKindProfile:
        return self.profile_for_cluster_pair(self.active_cluster_pair(example))

    def decoded_roles(self, example: rich.PixelExample) -> tuple[str, ...]:
        roles = ["neutral"] * 6
        pair = self.semantic_pair(example)
        profile = self.profile_for_cluster_pair(self.active_cluster_pair(example))
        for slot_index, role in zip(pair, profile.role_pair):
            roles[slot_index] = role
        return tuple(roles)

    def decoded_trial(self, example: rich.PixelExample) -> ShapeTrial:
        profile = self.profile_for_example(example)
        return ShapeTrial(
            trial_id=example.trial.trial_id,
            kind=profile.kind,
            roles=self.decoded_roles(example),
            true_parse=example.trial.true_parse,
            alternate_parse=example.trial.alternate_parse,
            causal_pair=self.semantic_pair(example),
            concern_weight=profile.concern_weight,
        )

    def manifest_summary(self) -> dict[str, Any]:
        return {
            "cluster_count": len(self.cluster_centers),
            "neutral_cluster": self.neutral_cluster,
            "calibration_trials": self.calibration_trials,
            "objective": self.objective,
            "pair_profiles": [
                {
                    "clusters": list(cluster_pair),
                    "kind": profile.kind,
                    "family": profile.family,
                    "support": self.profile_support.get(cluster_pair, 0),
                }
                for cluster_pair, profile in sorted(self.pair_profiles.items())
            ],
        }


@dataclass(frozen=True)
class UnsupervisedSlotResult:
    trial_id: int
    axis: str
    heldout: str
    agent: str
    program: str
    family: str
    selected_pair: tuple[int, int] | None
    anchor: int | None
    probed: int
    high_concern: int
    induced_kind_correct: int
    induced_family_correct: int
    induced_pair_correct: int
    family_correct: int
    target_correct: int
    useful_program: int
    rich_program: int
    parse_correct: int
    action_correct: int
    subtree_correct: int
    object_extraction_ok: int
    mean_program_cost: float
    regret: float


def component_induction_features(component: ExtractedComponent) -> tuple[float, ...]:
    width = component.width or 1
    height = component.height or 1
    return (
        component.area / 100.0,
        component.mean_r / 255.0,
        component.mean_g / 255.0,
        component.mean_b / 255.0,
        component.width / rich.IMAGE_SIZE,
        component.height / rich.IMAGE_SIZE,
        component.density,
        min(width, height) / max(width, height),
        component.area / max(1.0, float(width * height)),
    )


def _squared_distance(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return sum((a - b) ** 2 for a, b in zip(left, right))


def _nearest_center(
    features: tuple[float, ...],
    centers: tuple[tuple[float, ...], ...],
) -> int:
    return min(
        range(len(centers)),
        key=lambda idx: (_squared_distance(features, centers[idx]), idx),
    )


def _mean_center(rows: list[tuple[float, ...]]) -> tuple[float, ...]:
    width = len(rows[0])
    return tuple(mean(row[col] for row in rows) for col in range(width))


def _fit_component_clusters(
    rows: list[tuple[float, ...]],
    *,
    cluster_count: int,
    iterations: int = 30,
) -> tuple[tuple[float, ...], ...]:
    unique_rows = tuple(sorted(set(rows)))
    if len(unique_rows) < cluster_count:
        raise ValueError(
            f"need at least {cluster_count} unique component appearances, "
            f"found {len(unique_rows)}"
        )
    if len(unique_rows) == cluster_count:
        return unique_rows

    centers: list[tuple[float, ...]] = [unique_rows[0]]
    while len(centers) < cluster_count:
        centers.append(
            max(
                unique_rows,
                key=lambda row: (
                    min(_squared_distance(row, center) for center in centers),
                    row,
                ),
            )
        )

    for _ in range(iterations):
        buckets: list[list[tuple[float, ...]]] = [[] for _ in centers]
        for row in rows:
            buckets[_nearest_center(row, tuple(centers))].append(row)
        next_centers = [
            _mean_center(bucket) if bucket else centers[idx]
            for idx, bucket in enumerate(buckets)
        ]
        if next_centers == centers:
            break
        centers = next_centers
    return tuple(centers)


def _neutral_cluster(
    examples: list[rich.PixelExample],
    centers: tuple[tuple[float, ...], ...],
) -> int:
    counts = [0 for _ in centers]
    for example in examples:
        for component in _padded_components(example):
            counts[_nearest_center(component_induction_features(component), centers)] += 1
    return max(range(len(counts)), key=lambda idx: (counts[idx], -idx))


def _semantic_pair_for_clusters(
    components: list[ExtractedComponent],
    clusters: tuple[int, ...],
    neutral_cluster: int,
    inducer: UnsupervisedSlotInducer | None,
) -> tuple[int, int]:
    active = [idx for idx, cluster in enumerate(clusters) if cluster != neutral_cluster]
    if len(active) == 2:
        left, right = sorted(active)
        return (left, right)

    def margin(slot_index: int) -> float:
        if inducer is not None:
            return inducer.nonneutral_margin(components[slot_index])
        features = component_induction_features(components[slot_index])
        neutral = _squared_distance(
            features,
            _LAST_CLUSTER_CONTEXT[neutral_cluster],
        )
        active_distance = min(
            _squared_distance(features, center)
            for idx, center in enumerate(_LAST_CLUSTER_CONTEXT)
            if idx != neutral_cluster
        )
        return neutral - active_distance

    scored = sorted(
        range(6),
        key=lambda idx: (margin(idx), -idx),
        reverse=True,
    )[:2]
    left, right = sorted(scored)
    return (left, right)


_LAST_CLUSTER_CONTEXT: tuple[tuple[float, ...], ...] = ()


def _temporary_semantic_pair(
    example: rich.PixelExample,
    centers: tuple[tuple[float, ...], ...],
    neutral_cluster: int,
) -> tuple[int, int]:
    global _LAST_CLUSTER_CONTEXT
    previous = _LAST_CLUSTER_CONTEXT
    _LAST_CLUSTER_CONTEXT = centers
    try:
        components = _padded_components(example)
        clusters = tuple(
            _nearest_center(component_induction_features(component), centers)
            for component in components
        )
        return _semantic_pair_for_clusters(
            components,
            clusters,
            neutral_cluster,
            None,
        )
    finally:
        _LAST_CLUSTER_CONTEXT = previous


def _temporary_cluster_pair(
    example: rich.PixelExample,
    centers: tuple[tuple[float, ...], ...],
    neutral_cluster: int,
) -> tuple[int, int]:
    pair = _temporary_semantic_pair(example, centers, neutral_cluster)
    components = _padded_components(example)
    clusters = tuple(
        _nearest_center(component_induction_features(component), centers)
        for component in components
    )
    left, right = sorted((clusters[pair[0]], clusters[pair[1]]))
    return (left, right)


def _roles_for_profile(
    pair: tuple[int, int],
    profile: InducedKindProfile,
) -> tuple[str, ...]:
    roles = ["neutral"] * 6
    for slot_index, role in zip(pair, profile.role_pair):
        roles[slot_index] = role
    return tuple(roles)


def _trial_for_profile(
    example: rich.PixelExample,
    pair: tuple[int, int],
    profile: InducedKindProfile,
) -> ShapeTrial:
    return ShapeTrial(
        trial_id=example.trial.trial_id,
        kind=profile.kind,
        roles=_roles_for_profile(pair, profile),
        true_parse=example.trial.true_parse,
        alternate_parse=example.trial.alternate_parse,
        causal_pair=pair,
        concern_weight=profile.concern_weight,
    )


def _infer_parse_from_observation(
    trial: ShapeTrial,
    pair: tuple[int, int],
    observed_bound: int | None,
) -> ParseCandidate:
    if observed_bound is None:
        return min(trial.candidate_parses, key=lambda parse: parse.description_length)
    for parse in trial.candidate_parses:
        if int(_same_subtree(parse, *pair)) == observed_bound:
            return parse
    return min(trial.candidate_parses, key=lambda parse: parse.description_length)


def _kind_profile_score(
    examples: list[rich.PixelExample],
    *,
    centers: tuple[tuple[float, ...], ...],
    neutral_cluster: int,
    profile: InducedKindProfile,
) -> float:
    # Synthetic interventional feedback is represented by the benchmark trial.
    # The inducer scores candidate profiles without consuming visible role
    # tokens or example.trial.roles, but this is still feedback-shaped
    # supervision rather than unconstrained unsupervised semantic discovery.
    score = 0.0
    for example in examples:
        pair = _temporary_semantic_pair(example, centers, neutral_cluster)
        decoded_trial = _trial_for_profile(example, pair, profile)
        decoded_high_concern = concern_gap(decoded_trial) >= 0.10
        selected_pair = pair if decoded_high_concern else None
        family_feedback = bool(
            pair == example.trial.causal_pair
            and profile.family == rich.required_family(example)
        )
        observed_bound = (
            rich.true_bound(example)
            if selected_pair is not None and family_feedback
            else None
        )
        inferred_parse = _infer_parse_from_observation(
            decoded_trial,
            pair,
            observed_bound,
        )
        pred_bound = int(_same_subtree(inferred_parse, *example.trial.causal_pair))
        pred_action = preferred_action(
            outcome_for_parse(decoded_trial, inferred_parse),
            decoded_trial.concern_weight,
        )
        true_outcome = outcome_for_parse(example.trial, example.trial.true_parse)
        true_action = preferred_action(true_outcome, example.trial.concern_weight)
        pred_parse = (
            example.trial.true_parse
            if pred_bound == rich.true_bound(example)
            else example.trial.alternate_parse
        )
        pred_outcome = outcome_for_parse(example.trial, pred_parse)
        high_match = int(decoded_high_concern == (concern_gap(example.trial) >= 0.10))
        score += float(pred_action == true_action)
        score += 0.45 * float(family_feedback)
        score += 0.20 * high_match
        score -= max(
            0.0,
            utility(true_outcome, example.trial.concern_weight)
            - utility(pred_outcome, example.trial.concern_weight),
        )
    return score / max(1, len(examples))


def induce_unsupervised_slot_semantics(
    calibration_examples: list[rich.PixelExample],
    *,
    seed: int = 0,
    epochs: int = 0,
    cluster_count: int = 9,
) -> UnsupervisedSlotInducer:
    del seed, epochs
    rows = [
        component_induction_features(component)
        for example in calibration_examples
        for component in _padded_components(example)
    ]
    centers = _fit_component_clusters(rows, cluster_count=cluster_count)
    neutral = _neutral_cluster(calibration_examples, centers)
    grouped: dict[tuple[int, int], list[rich.PixelExample]] = {}
    for example in calibration_examples:
        grouped.setdefault(
            _temporary_cluster_pair(example, centers, neutral),
            [],
        ).append(example)

    pair_profiles: dict[tuple[int, int], InducedKindProfile] = {}
    support: dict[tuple[int, int], int] = {}
    for cluster_pair, examples in grouped.items():
        scored = [
            (
                _kind_profile_score(
                    examples,
                    centers=centers,
                    neutral_cluster=neutral,
                    profile=KIND_PROFILES[kind],
                ),
                -PROFILE_ORDER.index(kind),
                KIND_PROFILES[kind],
            )
            for kind in PROFILE_ORDER
        ]
        pair_profiles[cluster_pair] = max(scored, key=lambda item: item[:2])[2]
        support[cluster_pair] = len(examples)

    return UnsupervisedSlotInducer(
        cluster_centers=centers,
        neutral_cluster=neutral,
        pair_profiles=pair_profiles,
        profile_support=support,
        calibration_trials=len(calibration_examples),
        objective=(
            "connected_component_kmeans_then_label_free_rich_program_feedback"
        ),
    )


def _cluster_pair_distance(
    left: tuple[int, int],
    right: tuple[int, int],
    centers: tuple[tuple[float, ...], ...],
) -> float:
    left_a, left_b = left
    right_a, right_b = right
    direct = _squared_distance(centers[left_a], centers[right_a]) + _squared_distance(
        centers[left_b],
        centers[right_b],
    )
    swapped = _squared_distance(centers[left_a], centers[right_b]) + _squared_distance(
        centers[left_b],
        centers[right_a],
    )
    return min(direct, swapped)


def summarize_inducer(
    examples: list[rich.PixelExample],
    inducer: UnsupervisedSlotInducer,
) -> dict[str, float]:
    kind_correct = 0
    family_correct = 0
    pair_correct = 0
    for example in examples:
        profile = inducer.profile_for_example(example)
        kind_correct += int(profile.kind == example.trial.kind)
        family_correct += int(profile.family == rich.required_family(example))
        pair_correct += int(inducer.semantic_pair(example) == example.trial.causal_pair)
    n = len(examples) or 1
    return {
        "cluster_count": float(len(inducer.cluster_centers)),
        "profile_count": float(len(inducer.pair_profiles)),
        "semantic_kind_accuracy": kind_correct / n,
        "semantic_family_accuracy": family_correct / n,
        "semantic_pair_accuracy": pair_correct / n,
    }


def _target_correct(
    example: rich.PixelExample,
    family: str,
    pair: tuple[int, int] | None,
    anchor: int | None,
) -> int:
    if family == "move_anchor":
        return int(anchor in set(example.trial.causal_pair))
    return int(pair == example.trial.causal_pair)


def _append_row(
    rows: list[UnsupervisedSlotResult],
    *,
    example: rich.PixelExample,
    inducer: UnsupervisedSlotInducer,
    axis: str,
    heldout: str,
    agent: str,
    family: str,
    selected_pair: tuple[int, int] | None,
    anchor: int | None,
    probed: bool,
    pred_bound: int,
    pred_action: str,
) -> None:
    profile = inducer.profile_for_example(example)
    induced_pair = inducer.semantic_pair(example)
    required = rich.required_family(example)
    family_correct = int(family == required)
    target_correct = _target_correct(example, family, selected_pair, anchor)
    useful_program = int(probed and family_correct and target_correct)
    target_bound = rich.true_bound(example)
    true_outcome = outcome_for_parse(example.trial, example.trial.true_parse)
    true_action = preferred_action(true_outcome, example.trial.concern_weight)
    pred_parse = (
        example.trial.true_parse
        if pred_bound == target_bound
        else example.trial.alternate_parse
    )
    pred_outcome = outcome_for_parse(example.trial, pred_parse)
    rows.append(
        UnsupervisedSlotResult(
            trial_id=example.trial.trial_id,
            axis=axis,
            heldout=heldout,
            agent=agent,
            program=rich._program_name(family, selected_pair, anchor),
            family=family,
            selected_pair=selected_pair,
            anchor=anchor,
            probed=int(probed),
            high_concern=int(concern_gap(example.trial) >= 0.10),
            induced_kind_correct=int(profile.kind == example.trial.kind),
            induced_family_correct=int(profile.family == required),
            induced_pair_correct=int(induced_pair == example.trial.causal_pair),
            family_correct=family_correct,
            target_correct=target_correct,
            useful_program=useful_program,
            rich_program=int(family in {"move_anchor", "ablate_pair", "compose_move_observe"}),
            parse_correct=int(pred_bound == target_bound),
            action_correct=int(pred_action == true_action),
            subtree_correct=int(pred_bound == target_bound),
            object_extraction_ok=int(len(example.components) == 6),
            mean_program_cost=rich._program_cost(family, probed),
            regret=max(
                0.0,
                utility(true_outcome, example.trial.concern_weight)
                - utility(pred_outcome, example.trial.concern_weight),
            ),
        )
    )


def _evaluate_learned_baseline(
    examples: list[rich.PixelExample],
    models: dict[str, rich.LinearBinaryModel],
    *,
    axis: str,
    heldout: str,
) -> list[UnsupervisedSlotResult]:
    rows: list[UnsupervisedSlotResult] = []
    for item in rich.evaluate_agent(
        examples,
        models,
        agent="concerned_program_composer",
    ):
        rows.append(
            UnsupervisedSlotResult(
                trial_id=item.trial_id,
                axis=axis,
                heldout=heldout,
                agent="learned_rich_program_composer",
                program=item.program,
                family=item.family,
                selected_pair=item.selected_pair,
                anchor=item.anchor,
                probed=item.probed,
                high_concern=item.high_concern,
                induced_kind_correct=0,
                induced_family_correct=0,
                induced_pair_correct=0,
                family_correct=item.family_correct,
                target_correct=item.target_correct,
                useful_program=item.useful_program,
                rich_program=item.rich_program,
                parse_correct=item.parse_correct,
                action_correct=item.action_correct,
                subtree_correct=item.subtree_correct,
                object_extraction_ok=item.object_extraction_ok,
                mean_program_cost=item.mean_program_cost,
                regret=item.regret,
            )
        )
    return rows


def _evaluate_unsupervised_agent(
    examples: list[rich.PixelExample],
    inducer: UnsupervisedSlotInducer,
    *,
    axis: str,
    heldout: str,
    agent: str,
) -> list[UnsupervisedSlotResult]:
    rows: list[UnsupervisedSlotResult] = []
    for example in examples:
        semantic_trial = inducer.decoded_trial(example)
        induced_pair = inducer.semantic_pair(example)
        profile = inducer.profile_for_example(example)
        decoded_high_concern = concern_gap(semantic_trial) >= 0.10

        if agent == "unsupervised_semantic_family_only":
            probed = decoded_high_concern
            family = profile.family if probed else "null"
            selected_pair = _random_pair(example, salt=271) if probed else None
        elif agent == "unsupervised_semantic_target_only":
            probed = True
            family = "observe_pair"
            selected_pair = induced_pair
        elif agent == "unsupervised_semantic_rich_without_concern":
            probed = True
            family = profile.family
            selected_pair = induced_pair
        elif agent == "unsupervised_slot_semantic_world_model":
            probed = decoded_high_concern
            family = profile.family if probed else "null"
            selected_pair = induced_pair if probed else None
        else:
            raise KeyError(agent)

        anchor = selected_pair[0] if selected_pair is not None else None
        target_ok = _target_correct(example, family, selected_pair, anchor)
        useful = bool(probed and family == rich.required_family(example) and target_ok)
        observed_bound = int(_same_subtree(example.trial.true_parse, *induced_pair)) if useful else None
        inference_pair = selected_pair if selected_pair is not None else induced_pair
        inferred_parse = _infer_parse_from_observation(
            semantic_trial,
            inference_pair,
            observed_bound,
        )
        pred_bound = int(_same_subtree(inferred_parse, *example.trial.causal_pair))
        pred_action = preferred_action(
            outcome_for_parse(semantic_trial, inferred_parse),
            semantic_trial.concern_weight,
        )
        _append_row(
            rows,
            example=example,
            inducer=inducer,
            axis=axis,
            heldout=heldout,
            agent=agent,
            family=family,
            selected_pair=selected_pair,
            anchor=anchor,
            probed=probed,
            pred_bound=pred_bound,
            pred_action=pred_action,
        )
    return rows


def evaluate_unsupervised_agents(
    examples: list[rich.PixelExample],
    models: dict[str, rich.LinearBinaryModel],
    inducer: UnsupervisedSlotInducer,
    *,
    axis: str,
    heldout: str,
) -> list[UnsupervisedSlotResult]:
    rows = _evaluate_learned_baseline(
        examples,
        models,
        axis=axis,
        heldout=heldout,
    )
    for agent in UNSUPERVISED_SEMANTIC_AGENTS:
        if agent == "learned_rich_program_composer":
            continue
        rows.extend(
            _evaluate_unsupervised_agent(
                examples,
                inducer,
                axis=axis,
                heldout=heldout,
                agent=agent,
            )
        )
    return rows


def _safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def summarize_results(rows: list[UnsupervisedSlotResult]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[UnsupervisedSlotResult]] = {}
    for row in rows:
        grouped.setdefault(row.agent, []).append(row)

    summary: dict[str, dict[str, Any]] = {}
    for agent, items in sorted(grouped.items()):
        high = [item for item in items if item.high_concern]
        low = [item for item in items if not item.high_concern]
        has_high = bool(high)
        parse_high = _safe_mean([item.parse_correct for item in high]) if has_high else 1.0
        subtree = _safe_mean([item.subtree_correct for item in high]) if has_high else 1.0
        high_program = _safe_mean([item.probed for item in high]) if has_high else 1.0
        low_program = _safe_mean([item.probed for item in low])
        family_high = _safe_mean([item.family_correct for item in high]) if has_high else 1.0
        target_high = _safe_mean([item.target_correct for item in high]) if has_high else 1.0
        useful_high = _safe_mean([item.useful_program for item in high]) if has_high else 1.0
        rich_high = _safe_mean([item.rich_program for item in high if item.probed]) if has_high else 1.0
        action = _safe_mean([item.action_correct for item in items])
        extraction = _safe_mean([item.object_extraction_ok for item in items])
        induced_kind = _safe_mean([item.induced_kind_correct for item in items])
        induced_family = _safe_mean([item.induced_family_correct for item in items])
        induced_pair = _safe_mean([item.induced_pair_correct for item in items])
        high_gate = (
            not has_high
            or (
                parse_high >= 0.75
                and subtree >= 0.75
                and high_program >= 0.70
                and family_high >= 0.70
                and target_high >= 0.70
                and useful_high >= 0.70
                and rich_high >= 0.70
            )
        )
        semantic_gate = (
            agent == "learned_rich_program_composer"
            or (
                induced_kind >= 0.95
                and induced_family >= 0.95
                and induced_pair >= 0.95
            )
        )
        summary[agent] = {
            "n": len(items),
            "high_concern_count": len(high),
            "semantic_kind_accuracy": induced_kind,
            "semantic_family_accuracy": induced_family,
            "semantic_pair_accuracy": induced_pair,
            "parse_accuracy_high_concern": parse_high,
            "action_accuracy": action,
            "subtree_accuracy": subtree,
            "object_extraction_rate": extraction,
            "high_concern_program_rate": high_program,
            "low_concern_program_rate": low_program,
            "family_accuracy_high_concern": family_high,
            "target_accuracy_high_concern": target_high,
            "useful_program_rate_high_concern": useful_high,
            "rich_program_rate_high_concern": rich_high,
            "mean_program_cost": _safe_mean([item.mean_program_cost for item in items]),
            "mean_regret": _safe_mean([item.regret for item in items]),
            "gate_pass": bool(
                extraction >= 0.99
                and semantic_gate
                and action >= 0.85
                and low_program <= 0.25
                and high_gate
            ),
        }
    return summary


def summarize_slice_payloads(
    payloads: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for payload in payloads:
        for name, stats in payload["agent_summary"].items():
            grouped.setdefault(name, []).append(stats)

    summary: dict[str, dict[str, Any]] = {}
    for name, rows in sorted(grouped.items()):
        metric_names = [
            metric
            for metric, value in rows[0].items()
            if isinstance(value, (int, float, bool))
        ]
        stats: dict[str, Any] = {}
        for metric in metric_names:
            values = [float(row[metric]) for row in rows]
            stats[metric] = mean(values)
            stats[f"{metric}_sd"] = pstdev(values) if len(values) > 1 else 0.0
        stats["transfer_gate_pass"] = bool(all(bool(row["gate_pass"]) for row in rows))
        summary[name] = stats
    return summary


def summarize_seed_payloads(
    payloads: list[dict[str, Any]],
    key: str = "agent_summary",
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for payload in payloads:
        for name, stats in payload[key].items():
            grouped.setdefault(name, []).append(stats)

    summary: dict[str, dict[str, Any]] = {}
    for name, rows in sorted(grouped.items()):
        metric_names = [
            metric
            for metric, value in rows[0].items()
            if isinstance(value, (int, float, bool))
        ]
        stats: dict[str, Any] = {}
        for metric in metric_names:
            values = [float(row[metric]) for row in rows]
            stats[metric] = mean(values)
            stats[f"{metric}_sd"] = pstdev(values) if len(values) > 1 else 0.0
        summary[name] = stats
    return summary


def summarize_modal_slice_results(
    seed_payloads: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for seed_payload in seed_payloads:
        for slice_payload in seed_payload.get("slice_results", []):
            key = (str(slice_payload["axis"]), str(slice_payload["heldout"]))
            grouped.setdefault(key, []).append(slice_payload)

    slice_results: list[dict[str, Any]] = []
    for (axis, heldout), payloads in sorted(grouped.items()):
        slice_results.append(
            {
                "axis": axis,
                "heldout": heldout,
                "agent_summary": summarize_seed_payloads(payloads, "agent_summary"),
                "semantic_summary": summarize_seed_payloads(payloads, "semantic_summary"),
            }
        )
    return slice_results


def _slice_examples(
    *,
    axis: str,
    heldout: str,
    train_trials: int,
    test_trials: int,
    seed: int,
) -> tuple[list[rich.PixelExample], list[rich.PixelExample]]:
    if axis == "role_kind":
        return (
            rich.make_filtered_pixel_examples(
                trials=train_trials,
                seed=seed,
                exclude_kinds={heldout},
            ),
            rich.make_filtered_pixel_examples(
                trials=test_trials,
                seed=seed + 1_300_000,
                include_kinds={heldout},
            ),
        )
    if axis == "true_parse":
        return (
            rich.make_filtered_pixel_examples(
                trials=train_trials,
                seed=seed,
                exclude_true_parses={heldout},
            ),
            rich.make_filtered_pixel_examples(
                trials=test_trials,
                seed=seed + 1_500_000,
                include_true_parses={heldout},
            ),
        )
    raise KeyError(axis)


def run_slice(
    *,
    axis: str,
    heldout: str,
    train_trials: int,
    test_trials: int,
    seed: int,
    epochs: int,
    inducer: UnsupervisedSlotInducer,
) -> dict[str, Any]:
    train_examples, test_examples = _slice_examples(
        axis=axis,
        heldout=heldout,
        train_trials=train_trials,
        test_trials=test_trials,
        seed=seed,
    )
    models = rich.train_rich_models(train_examples, seed=seed, epochs=epochs)
    rows = evaluate_unsupervised_agents(
        test_examples,
        models,
        inducer,
        axis=axis,
        heldout=heldout,
    )
    return {
        "axis": axis,
        "heldout": heldout,
        "semantic_summary": {
            "unsupervised_slot_inducer": summarize_inducer(
                test_examples,
                inducer,
            )
        },
        "agent_summary": summarize_results(rows),
        "results": [asdict(row) for row in rows],
    }


def run_experiment(
    *,
    train_trials: int,
    test_trials: int,
    seed: int,
    epochs: int,
    induction_calibration_trials: int = 600,
    heldout_kinds: tuple[str, ...] = HELDOUT_ROLE_KINDS,
    heldout_parses: tuple[str, ...] = HELDOUT_TRUE_PARSES,
) -> dict[str, Any]:
    calibration_examples = rich.make_filtered_pixel_examples(
        trials=induction_calibration_trials,
        seed=seed + 2_700_000,
    )
    inducer = induce_unsupervised_slot_semantics(
        calibration_examples,
        seed=seed + 2_900_000,
        epochs=max(20, epochs),
    )
    slice_payloads: list[dict[str, Any]] = []
    for offset, heldout_kind in enumerate(heldout_kinds):
        slice_payloads.append(
            run_slice(
                axis="role_kind",
                heldout=heldout_kind,
                train_trials=train_trials,
                test_trials=test_trials,
                seed=seed + offset * 10_000,
                epochs=epochs,
                inducer=inducer,
            )
        )
    for offset, heldout_parse in enumerate(heldout_parses):
        slice_payloads.append(
            run_slice(
                axis="true_parse",
                heldout=heldout_parse,
                train_trials=train_trials,
                test_trials=test_trials,
                seed=seed + 80_000 + offset * 10_000,
                epochs=epochs,
                inducer=inducer,
            )
        )

    return {
        "manifest": {
            "arc": "2A",
            "name": "unsupervised_slot_semantics_transfer",
            "contract": "2A-v2-pixels-rich_programs-transfer",
            "train_trials": train_trials,
            "test_trials": test_trials,
            "induction_calibration_trials": induction_calibration_trials,
            "seed": seed,
            "epochs": epochs,
            "heldout_kinds": list(heldout_kinds),
            "heldout_parses": list(heldout_parses),
            "agents": list(UNSUPERVISED_SEMANTIC_AGENTS),
            "program_families": list(rich.PROGRAM_FAMILIES),
            "perception": "connected_components_rgb_plus_unsupervised_slot_induction",
            "semantic_induction": (
                "label_free_connected_component_clusters_with_rich_program_feedback"
            ),
            "provided_induction_priors": [
                "semantic kind profile table",
                "program family by semantic profile",
            ],
            "allowed_induction_feedback": [
                "synthetic rich-program success",
                "action consistency",
                "viability regret",
            ],
            "forbidden_induction_labels": [
                "visible role tokens",
                "example.trial.roles",
            ],
            "inducer": inducer.manifest_summary(),
        },
        "semantic_summary": summarize_seed_payloads(
            slice_payloads,
            "semantic_summary",
        ),
        "agent_summary": summarize_slice_payloads(slice_payloads),
        "slice_results": slice_payloads,
    }


def _manifest_text(manifest: dict[str, Any]) -> str:
    if "seeds" in manifest:
        return (
            f"{len(manifest['seeds'])} seeds, {manifest['train_trials']} train trials "
            f"per held-out slice/seed, {manifest['test_trials']} test trials per "
            f"held-out slice/seed, {manifest['induction_calibration_trials']} "
            f"label-free induction trials/seed, {manifest['epochs']} SGD epochs, "
            f"role held-outs {', '.join(manifest['heldout_kinds'])}, parse "
            f"held-outs {', '.join(manifest['heldout_parses'])}."
        )
    return (
        f"{manifest['train_trials']} train trials per held-out slice, "
        f"{manifest['test_trials']} test trials per held-out slice, "
        f"{manifest['induction_calibration_trials']} label-free induction trials, "
        f"seed {manifest['seed']}, {manifest['epochs']} SGD epochs, role "
        f"held-outs {', '.join(manifest['heldout_kinds'])}, parse held-outs "
        f"{', '.join(manifest['heldout_parses'])}."
    )


def write_unsupervised_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["agent_summary"]
    semantic_summary = payload["semantic_summary"]["unsupervised_slot_inducer"]
    manifest = payload["manifest"]
    slice_results = payload.get("slice_results") or summarize_modal_slice_results(
        payload.get("results", [])
    )
    lines = [
        "# Label-Free Slot Semantics Transfer",
        "",
        "Date: 2026-06-18",
        "",
        (
            "Question: can the `2A-v2-pixels-rich_programs` transfer contract "
            "replace supervised visible role-token calibration with label-free "
            "connected-component slot induction plus downstream rich-program "
            "feedback?"
        ),
        "",
        f"Manifest: {_manifest_text(manifest)}",
        "",
        "## Induced Semantics",
        "",
        "| Clusters | Profiles | Kind | Family | Pair |",
        "|---:|---:|---:|---:|---:|",
        (
            "| {clusters:.0f} | {profiles:.0f} | {kind:.3f} | "
            "{family:.3f} | {pair:.3f} |".format(
                clusters=semantic_summary["cluster_count"],
                profiles=semantic_summary["profile_count"],
                kind=semantic_summary["semantic_kind_accuracy"],
                family=semantic_summary["semantic_family_accuracy"],
                pair=semantic_summary["semantic_pair_accuracy"],
            )
        ),
        "",
        "## Gate Summary",
        "",
        (
            "| Agent | Sem kind | Sem family | Sem pair | Parse high | Action | "
            "Family high | Target high | Useful high | Rich high | Low prog | "
            "Regret | Slice gate | Transfer gate |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for agent, stats in sorted(summary.items()):
        transfer_gate = float(stats.get("transfer_gate_pass", 0.0)) >= 0.999
        lines.append(
            "| {agent} | {kind:.3f} | {sem_family:.3f} | {pair:.3f} | "
            "{parse:.3f} | {action:.3f} | {family:.3f} | {target:.3f} | "
            "{useful:.3f} | {rich_prog:.3f} | {low:.3f} | {regret:.3f} | "
            "{gate:.3f} | {transfer} |".format(
                agent=agent,
                kind=stats["semantic_kind_accuracy"],
                sem_family=stats["semantic_family_accuracy"],
                pair=stats["semantic_pair_accuracy"],
                parse=stats["parse_accuracy_high_concern"],
                action=stats["action_accuracy"],
                family=stats["family_accuracy_high_concern"],
                target=stats["target_accuracy_high_concern"],
                useful=stats["useful_program_rate_high_concern"],
                rich_prog=stats["rich_program_rate_high_concern"],
                low=stats["low_concern_program_rate"],
                regret=stats["mean_regret"],
                gate=stats["gate_pass"],
                transfer="PASS" if transfer_gate else "fail",
            )
        )

    lines.extend(
        [
            "",
            "## Held-Out Slices",
            "",
            (
                "| Axis | Held-out | Agent | Sem kind | Sem pair | Family high | "
                "Target high | Useful high | Low prog | Gate |"
            ),
            "|---|---|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for slice_payload in slice_results:
        axis = slice_payload["axis"]
        heldout = slice_payload["heldout"]
        for agent, stats in sorted(slice_payload["agent_summary"].items()):
            gate_pass = float(stats["gate_pass"]) >= 0.999
            lines.append(
                "| {axis} | {heldout} | {agent} | {kind:.3f} | {pair:.3f} | "
                "{family:.3f} | {target:.3f} | {useful:.3f} | {low:.3f} | "
                "{gate} |".format(
                    axis=axis,
                    heldout=heldout,
                    agent=agent,
                    kind=stats["semantic_kind_accuracy"],
                    pair=stats["semantic_pair_accuracy"],
                    family=stats["family_accuracy_high_concern"],
                    target=stats["target_accuracy_high_concern"],
                    useful=stats["useful_program_rate_high_concern"],
                    low=stats["low_concern_program_rate"],
                    gate="PASS" if gate_pass else "fail",
                )
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The accepted agent does not train on visible role-token labels. "
                "It clusters rendered connected components into appearance "
                "slots, identifies the neutral cluster by prevalence, and "
                "grounds each active cluster pair by rich-program feedback and "
                "action consistency. It then uses the same v2 program family, "
                "target, concern, parse-observation, and action contract as "
                "the transfer repair gate."
            ),
            "",
            (
                "This is not natural-image object discovery, fully unsupervised "
                "world learning, fully unsupervised semantic-profile discovery, "
                "or open-ended program invention. The semantic profile table is "
                "provided and the feedback is synthetic and contract-shaped; "
                "the narrow claim is that role-slot semantics no longer require "
                "supervised role-token calibration."
            ),
            "",
            "Raw JSON remains local under `artifacts/concerned_syntax/`.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-trials", type=int, default=1200)
    parser.add_argument("--test-trials", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260618)
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--induction-calibration-trials", type=int, default=600)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    payload = run_experiment(
        train_trials=args.train_trials,
        test_trials=args.test_trials,
        seed=args.seed,
        epochs=args.epochs,
        induction_calibration_trials=args.induction_calibration_trials,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.report:
        write_unsupervised_report(args.report, payload)

    print("=== Unsupervised Slot Semantics Transfer Summary ===")
    semantic = payload["semantic_summary"]["unsupervised_slot_inducer"]
    print(
        "slot_inducer "
        f"clusters={semantic['cluster_count']:.0f} "
        f"profiles={semantic['profile_count']:.0f} "
        f"kind={semantic['semantic_kind_accuracy']:.3f} "
        f"family={semantic['semantic_family_accuracy']:.3f} "
        f"pair={semantic['semantic_pair_accuracy']:.3f}"
    )
    for agent, stats in sorted(payload["agent_summary"].items()):
        print(
            f"{agent:46s} sem_kind={stats['semantic_kind_accuracy']:.3f} "
            f"family={stats['family_accuracy_high_concern']:.3f} "
            f"target={stats['target_accuracy_high_concern']:.3f} "
            f"useful={stats['useful_program_rate_high_concern']:.3f} "
            f"rich={stats['rich_program_rate_high_concern']:.3f} "
            f"low_prog={stats['low_concern_program_rate']:.3f} "
            f"transfer={stats['transfer_gate_pass']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
