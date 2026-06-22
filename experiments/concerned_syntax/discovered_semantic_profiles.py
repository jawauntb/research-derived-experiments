#!/usr/bin/env python3
"""Discovered semantic profiles for the 2A-v2 transfer contract.

This sidecar preserves the label-free connected-component slot setup from
``unsupervised_slot_semantics`` but removes the supplied semantic profile table
from the accepted agent. Calibration examples are converted into anonymous
intervention traces: which cluster pair was active, which candidate rich-program
family produced useful parse evidence, how much utility changed across the
bound/unbound alternatives, and which action each alternative supported.

The inducer fits one profile per active cluster pair from those traces. It does
not receive visible role tokens, ``example.trial.kind``, ``example.trial.roles``,
or a handwritten kind/profile table. Ground-truth fields remain available to the
synthetic feedback generator and evaluator, which is why the allowed claim is
semantic-profile induction inside this connected-component benchmark rather
than fully open-ended semantic discovery.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from experiments.concerned_syntax import rich_program_language as rich
from experiments.concerned_syntax.benchmark import (
    HIGH_CONCERN_KINDS,
    PARSES,
    ParseCandidate,
    _same_subtree,
    concern_gap,
    outcome_for_parse,
    preferred_action,
    utility,
)
from experiments.concerned_syntax.intervention_invention import _padded_components, _random_pair
from experiments.concerned_syntax.pixel_shapes import ExtractedComponent
from experiments.concerned_syntax.unsupervised_slot_semantics import (
    _cluster_pair_distance,
    _fit_component_clusters,
    _nearest_center,
    _neutral_cluster,
    _safe_mean,
    _slice_examples,
    _squared_distance,
    _target_correct,
    _temporary_cluster_pair,
    _temporary_semantic_pair,
    component_induction_features,
)


DISCOVERED_SEMANTIC_AGENTS: tuple[str, ...] = (
    "learned_rich_program_composer",
    "discovered_semantic_family_only",
    "discovered_semantic_target_only",
    "discovered_semantic_rich_without_concern",
    "discovered_semantic_world_model",
)

HELDOUT_ROLE_KINDS: tuple[str, ...] = HIGH_CONCERN_KINDS
HELDOUT_TRUE_PARSES: tuple[str, ...] = tuple(parse.name for parse in PARSES)
DISCOVERY_FAMILIES: tuple[str, ...] = rich.PROGRAM_FAMILIES


@dataclass(frozen=True)
class DiscoveryTrace:
    cluster_pair: tuple[int, int]
    semantic_pair: tuple[int, int]
    family_success: dict[str, int]
    utility_gap: float
    action_by_bound: tuple[str, str]


@dataclass(frozen=True)
class DiscoveredSemanticProfile:
    profile_id: str
    family: str
    high_concern: bool
    action_by_bound: tuple[str, str]
    support: int
    family_success_rate: float
    utility_gap: float
    action_template_consistency: float

    def action_for_bound(self, bound: int) -> str:
        return self.action_by_bound[1 if bound else 0]


@dataclass(frozen=True)
class DiscoveredSemanticInducer:
    cluster_centers: tuple[tuple[float, ...], ...]
    neutral_cluster: int
    pair_profiles: dict[tuple[int, int], DiscoveredSemanticProfile]
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
        components = _padded_components(example)
        clusters = self.component_clusters(example)
        active = [idx for idx, cluster in enumerate(clusters) if cluster != self.neutral_cluster]
        if len(active) == 2:
            left, right = sorted(active)
            return (left, right)
        scored = sorted(
            range(6),
            key=lambda idx: (self.nonneutral_margin(components[idx]), -idx),
            reverse=True,
        )[:2]
        left, right = sorted(scored)
        return (left, right)

    def active_cluster_pair(self, example: rich.PixelExample) -> tuple[int, int]:
        clusters = self.component_clusters(example)
        pair = self.semantic_pair(example)
        left, right = sorted((clusters[pair[0]], clusters[pair[1]]))
        return (left, right)

    def profile_for_cluster_pair(
        self,
        cluster_pair: tuple[int, int],
    ) -> DiscoveredSemanticProfile:
        if cluster_pair in self.pair_profiles:
            return self.pair_profiles[cluster_pair]
        if not self.pair_profiles:
            return DiscoveredSemanticProfile(
                profile_id="fallback_low_observe",
                family="observe_pair",
                high_concern=False,
                action_by_bound=("skip", "skip"),
                support=0,
                family_success_rate=0.0,
                utility_gap=0.0,
                action_template_consistency=0.0,
            )
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

    def profile_for_example(self, example: rich.PixelExample) -> DiscoveredSemanticProfile:
        return self.profile_for_cluster_pair(self.active_cluster_pair(example))

    def manifest_summary(self) -> dict[str, Any]:
        return {
            "cluster_count": len(self.cluster_centers),
            "neutral_cluster": self.neutral_cluster,
            "calibration_trials": self.calibration_trials,
            "objective": self.objective,
            "pair_profiles": [
                {
                    "clusters": list(cluster_pair),
                    "profile_id": profile.profile_id,
                    "family": profile.family,
                    "high_concern": profile.high_concern,
                    "support": self.profile_support.get(cluster_pair, 0),
                    "family_success_rate": profile.family_success_rate,
                    "utility_gap": profile.utility_gap,
                    "action_by_bound": list(profile.action_by_bound),
                    "action_template_consistency": profile.action_template_consistency,
                }
                for cluster_pair, profile in sorted(self.pair_profiles.items())
            ],
        }


@dataclass(frozen=True)
class DiscoveredSemanticResult:
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
    profile_cluster_purity_correct: int
    induced_family_correct: int
    induced_pair_correct: int
    profile_action_consistent: int
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


def _parse_with_bound(
    parses: tuple[ParseCandidate, ParseCandidate],
    pair: tuple[int, int],
    bound: int,
) -> ParseCandidate:
    for parse in parses:
        if int(_same_subtree(parse, *pair)) == bound:
            return parse
    return min(parses, key=lambda parse: parse.description_length)


def _action_template_for_example(
    example: rich.PixelExample,
    pair: tuple[int, int],
) -> tuple[str, str]:
    actions: list[str] = []
    for bound in (0, 1):
        parse = _parse_with_bound(example.trial.candidate_parses, pair, bound)
        outcome = outcome_for_parse(example.trial, parse)
        actions.append(preferred_action(outcome, example.trial.concern_weight))
    return (actions[0], actions[1])


def _utility_gap_for_example(
    example: rich.PixelExample,
    pair: tuple[int, int],
) -> float:
    values = []
    for bound in (0, 1):
        parse = _parse_with_bound(example.trial.candidate_parses, pair, bound)
        outcome = outcome_for_parse(example.trial, parse)
        values.append(utility(outcome, example.trial.concern_weight))
    return max(values) - min(values)


def _family_success_feedback(
    example: rich.PixelExample,
    pair: tuple[int, int],
    family: str,
) -> int:
    """Synthetic environment feedback, not an inducer-visible profile table."""

    return int(
        pair == example.trial.causal_pair
        and family == rich.required_family(example)
    )


def _trace_for_example(
    example: rich.PixelExample,
    *,
    centers: tuple[tuple[float, ...], ...],
    neutral_cluster: int,
) -> DiscoveryTrace:
    pair = _temporary_semantic_pair(example, centers, neutral_cluster)
    cluster_pair = _temporary_cluster_pair(example, centers, neutral_cluster)
    return DiscoveryTrace(
        cluster_pair=cluster_pair,
        semantic_pair=pair,
        family_success={
            family: _family_success_feedback(example, pair, family)
            for family in DISCOVERY_FAMILIES
        },
        utility_gap=_utility_gap_for_example(example, pair),
        action_by_bound=_action_template_for_example(example, pair),
    )


def _majority_action(
    traces: list[DiscoveryTrace],
    *,
    bound: int,
) -> tuple[str, float]:
    counts: Counter[str] = Counter(trace.action_by_bound[bound] for trace in traces)
    if not counts:
        return ("skip", 0.0)
    action, count = max(counts.items(), key=lambda item: (item[1], item[0]))
    return (action, count / len(traces))


def _fit_profile(
    profile_index: int,
    traces: list[DiscoveryTrace],
) -> DiscoveredSemanticProfile:
    family_rates = {
        family: _safe_mean([trace.family_success[family] for trace in traces])
        for family in DISCOVERY_FAMILIES
    }
    family = max(
        DISCOVERY_FAMILIES,
        key=lambda candidate: (
            family_rates[candidate],
            -DISCOVERY_FAMILIES.index(candidate),
        ),
    )
    action_0, consistency_0 = _majority_action(traces, bound=0)
    action_1, consistency_1 = _majority_action(traces, bound=1)
    utility_gap_value = _safe_mean([trace.utility_gap for trace in traces])
    return DiscoveredSemanticProfile(
        profile_id=f"discovered_profile_{profile_index}",
        family=family,
        high_concern=utility_gap_value >= 0.10,
        action_by_bound=(action_0, action_1),
        support=len(traces),
        family_success_rate=family_rates[family],
        utility_gap=utility_gap_value,
        action_template_consistency=min(consistency_0, consistency_1),
    )


def induce_discovered_semantic_profiles(
    calibration_examples: list[rich.PixelExample],
    *,
    seed: int = 0,
    epochs: int = 0,
    cluster_count: int = 9,
) -> DiscoveredSemanticInducer:
    del seed, epochs
    rows = [
        component_induction_features(component)
        for example in calibration_examples
        for component in _padded_components(example)
    ]
    centers = _fit_component_clusters(rows, cluster_count=cluster_count)
    neutral = _neutral_cluster(calibration_examples, centers)

    grouped: dict[tuple[int, int], list[DiscoveryTrace]] = {}
    for example in calibration_examples:
        trace = _trace_for_example(
            example,
            centers=centers,
            neutral_cluster=neutral,
        )
        grouped.setdefault(trace.cluster_pair, []).append(trace)

    pair_profiles: dict[tuple[int, int], DiscoveredSemanticProfile] = {}
    support: dict[tuple[int, int], int] = {}
    for idx, (cluster_pair, traces) in enumerate(sorted(grouped.items())):
        pair_profiles[cluster_pair] = _fit_profile(idx, traces)
        support[cluster_pair] = len(traces)

    return DiscoveredSemanticInducer(
        cluster_centers=centers,
        neutral_cluster=neutral,
        pair_profiles=pair_profiles,
        profile_support=support,
        calibration_trials=len(calibration_examples),
        objective=(
            "connected_component_kmeans_then_profile_induction_from_"
            "family_success_utility_gap_and_action_templates"
        ),
    )


def _profile_cluster_purity_by_pair(
    examples: list[rich.PixelExample],
    inducer: DiscoveredSemanticInducer,
) -> dict[tuple[int, int], set[int]]:
    grouped: dict[tuple[int, int], Counter[str]] = {}
    for index, example in enumerate(examples):
        cluster_pair = inducer.active_cluster_pair(example)
        grouped.setdefault(cluster_pair, Counter())[example.trial.kind] += 1

    pure_indices: dict[tuple[int, int], set[int]] = {}
    for cluster_pair, counts in grouped.items():
        if not counts:
            pure_indices[cluster_pair] = set()
            continue
        majority_kind = max(counts.items(), key=lambda item: (item[1], item[0]))[0]
        pure_indices[cluster_pair] = {
            index
            for index, example in enumerate(examples)
            if inducer.active_cluster_pair(example) == cluster_pair
            and example.trial.kind == majority_kind
        }
    return pure_indices


def summarize_inducer(
    examples: list[rich.PixelExample],
    inducer: DiscoveredSemanticInducer,
) -> dict[str, float]:
    pure_indices = _profile_cluster_purity_by_pair(examples, inducer)
    purity_correct = 0
    family_correct = 0
    pair_correct = 0
    action_consistent = 0
    for index, example in enumerate(examples):
        profile = inducer.profile_for_example(example)
        cluster_pair = inducer.active_cluster_pair(example)
        true_bound = rich.true_bound(example)
        true_action = preferred_action(
            outcome_for_parse(example.trial, example.trial.true_parse),
            example.trial.concern_weight,
        )
        purity_correct += int(index in pure_indices.get(cluster_pair, set()))
        family_correct += int(profile.family == rich.required_family(example))
        pair_correct += int(inducer.semantic_pair(example) == example.trial.causal_pair)
        action_consistent += int(profile.action_for_bound(true_bound) == true_action)
    n = len(examples) or 1
    return {
        "cluster_count": float(len(inducer.cluster_centers)),
        "profile_count": float(len(inducer.pair_profiles)),
        "profile_cluster_purity": purity_correct / n,
        "semantic_family_accuracy": family_correct / n,
        "semantic_pair_accuracy": pair_correct / n,
        "profile_action_consistency": action_consistent / n,
    }


def _infer_parse_from_observation(
    parses: tuple[ParseCandidate, ParseCandidate],
    pair: tuple[int, int],
    observed_bound: int | None,
) -> ParseCandidate:
    if observed_bound is None:
        return min(parses, key=lambda parse: parse.description_length)
    return _parse_with_bound(parses, pair, observed_bound)


def _append_row(
    rows: list[DiscoveredSemanticResult],
    *,
    example: rich.PixelExample,
    inducer: DiscoveredSemanticInducer,
    pure_indices: dict[tuple[int, int], set[int]],
    example_index: int,
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
    cluster_pair = inducer.active_cluster_pair(example)
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
        DiscoveredSemanticResult(
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
            profile_cluster_purity_correct=int(
                example_index in pure_indices.get(cluster_pair, set())
            ),
            induced_family_correct=int(profile.family == required),
            induced_pair_correct=int(induced_pair == example.trial.causal_pair),
            profile_action_consistent=int(profile.action_for_bound(target_bound) == true_action),
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
) -> list[DiscoveredSemanticResult]:
    rows: list[DiscoveredSemanticResult] = []
    for item in rich.evaluate_agent(
        examples,
        models,
        agent="concerned_program_composer",
    ):
        rows.append(
            DiscoveredSemanticResult(
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
                profile_cluster_purity_correct=0,
                induced_family_correct=0,
                induced_pair_correct=0,
                profile_action_consistent=0,
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


def _evaluate_discovered_agent(
    examples: list[rich.PixelExample],
    inducer: DiscoveredSemanticInducer,
    *,
    axis: str,
    heldout: str,
    agent: str,
) -> list[DiscoveredSemanticResult]:
    rows: list[DiscoveredSemanticResult] = []
    pure_indices = _profile_cluster_purity_by_pair(examples, inducer)
    for example_index, example in enumerate(examples):
        induced_pair = inducer.semantic_pair(example)
        profile = inducer.profile_for_example(example)

        if agent == "discovered_semantic_family_only":
            probed = profile.high_concern
            family = profile.family if probed else "null"
            selected_pair = _random_pair(example, salt=271) if probed else None
        elif agent == "discovered_semantic_target_only":
            probed = True
            family = "observe_pair"
            selected_pair = induced_pair
        elif agent == "discovered_semantic_rich_without_concern":
            probed = True
            family = profile.family
            selected_pair = induced_pair
        elif agent == "discovered_semantic_world_model":
            probed = profile.high_concern
            family = profile.family if probed else "null"
            selected_pair = induced_pair if probed else None
        else:
            raise KeyError(agent)

        anchor = selected_pair[0] if selected_pair is not None else None
        target_ok = _target_correct(example, family, selected_pair, anchor)
        useful = bool(probed and family == rich.required_family(example) and target_ok)
        observed_bound = rich.true_bound(example) if useful else None
        inference_pair = selected_pair if selected_pair is not None else induced_pair
        inferred_parse = _infer_parse_from_observation(
            example.trial.candidate_parses,
            inference_pair,
            observed_bound,
        )
        pred_bound = int(_same_subtree(inferred_parse, *example.trial.causal_pair))
        pred_action = profile.action_for_bound(pred_bound)
        _append_row(
            rows,
            example=example,
            inducer=inducer,
            pure_indices=pure_indices,
            example_index=example_index,
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


def evaluate_discovered_agents(
    examples: list[rich.PixelExample],
    models: dict[str, rich.LinearBinaryModel],
    inducer: DiscoveredSemanticInducer,
    *,
    axis: str,
    heldout: str,
) -> list[DiscoveredSemanticResult]:
    rows = _evaluate_learned_baseline(
        examples,
        models,
        axis=axis,
        heldout=heldout,
    )
    for agent in DISCOVERED_SEMANTIC_AGENTS:
        if agent == "learned_rich_program_composer":
            continue
        rows.extend(
            _evaluate_discovered_agent(
                examples,
                inducer,
                axis=axis,
                heldout=heldout,
                agent=agent,
            )
        )
    return rows


def summarize_results(rows: list[DiscoveredSemanticResult]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[DiscoveredSemanticResult]] = {}
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
        profile_purity = _safe_mean([item.profile_cluster_purity_correct for item in items])
        induced_family = _safe_mean([item.induced_family_correct for item in items])
        induced_pair = _safe_mean([item.induced_pair_correct for item in items])
        action_template = _safe_mean([item.profile_action_consistent for item in items])
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
                profile_purity >= 0.95
                and induced_family >= 0.95
                and induced_pair >= 0.95
                and action_template >= 0.95
            )
        )
        summary[agent] = {
            "n": len(items),
            "high_concern_count": len(high),
            "profile_cluster_purity": profile_purity,
            "semantic_family_accuracy": induced_family,
            "semantic_pair_accuracy": induced_pair,
            "profile_action_consistency": action_template,
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


def run_slice(
    *,
    axis: str,
    heldout: str,
    train_trials: int,
    test_trials: int,
    seed: int,
    epochs: int,
    inducer: DiscoveredSemanticInducer,
) -> dict[str, Any]:
    train_examples, test_examples = _slice_examples(
        axis=axis,
        heldout=heldout,
        train_trials=train_trials,
        test_trials=test_trials,
        seed=seed,
    )
    models = rich.train_rich_models(train_examples, seed=seed, epochs=epochs)
    rows = evaluate_discovered_agents(
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
            "discovered_semantic_inducer": summarize_inducer(
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
    inducer = induce_discovered_semantic_profiles(
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
            "name": "discovered_semantic_profiles_transfer",
            "contract": "2A-v2-pixels-rich_programs-transfer",
            "train_trials": train_trials,
            "test_trials": test_trials,
            "induction_calibration_trials": induction_calibration_trials,
            "seed": seed,
            "epochs": epochs,
            "heldout_kinds": list(heldout_kinds),
            "heldout_parses": list(heldout_parses),
            "agents": list(DISCOVERED_SEMANTIC_AGENTS),
            "program_families": list(DISCOVERY_FAMILIES),
            "perception": "connected_components_rgb_plus_label_free_slot_induction",
            "semantic_induction": (
                "profile_induction_from_intervention_family_success_"
                "utility_gap_and_action_templates"
            ),
            "provided_induction_priors": [
                "generic rich-program family menu",
                "bound/unbound parse alternatives",
            ],
            "removed_induction_priors": [
                "semantic kind profile table",
                "kind-to-family mapping",
                "kind-to-role-pair mapping",
                "kind-to-concern-weight mapping",
            ],
            "allowed_induction_feedback": [
                "candidate family exposed useful parse evidence",
                "utility gap across bound/unbound alternatives",
                "action supported by each bound alternative",
            ],
            "forbidden_induction_labels": [
                "visible role tokens",
                "example.trial.kind",
                "example.trial.roles",
                "supplied semantic profile table",
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
            f"profile-induction trials/seed, {manifest['epochs']} SGD epochs, "
            f"role held-outs {', '.join(manifest['heldout_kinds'])}, parse "
            f"held-outs {', '.join(manifest['heldout_parses'])}."
        )
    return (
        f"{manifest['train_trials']} train trials per held-out slice, "
        f"{manifest['test_trials']} test trials per held-out slice, "
        f"{manifest['induction_calibration_trials']} profile-induction trials, "
        f"seed {manifest['seed']}, {manifest['epochs']} SGD epochs, role "
        f"held-outs {', '.join(manifest['heldout_kinds'])}, parse held-outs "
        f"{', '.join(manifest['heldout_parses'])}."
    )


def write_discovered_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["agent_summary"]
    semantic_summary = payload["semantic_summary"]["discovered_semantic_inducer"]
    manifest = payload["manifest"]
    slice_results = payload.get("slice_results") or summarize_modal_slice_results(
        payload.get("results", [])
    )
    lines = [
        "# Discovered Semantic Profiles Transfer",
        "",
        "Date: 2026-06-22",
        "",
        (
            "Question: can the `2A-v2-pixels-rich_programs` transfer contract "
            "replace the supplied semantic profile table with profiles induced "
            "from intervention/outcome and action-consistency traces?"
        ),
        "",
        f"Manifest: {_manifest_text(manifest)}",
        "",
        "## Induced Semantics",
        "",
        "| Clusters | Profiles | Cluster purity | Family | Pair | Action template |",
        "|---:|---:|---:|---:|---:|---:|",
        (
            "| {clusters:.0f} | {profiles:.0f} | {purity:.3f} | "
            "{family:.3f} | {pair:.3f} | {action:.3f} |".format(
                clusters=semantic_summary["cluster_count"],
                profiles=semantic_summary["profile_count"],
                purity=semantic_summary["profile_cluster_purity"],
                family=semantic_summary["semantic_family_accuracy"],
                pair=semantic_summary["semantic_pair_accuracy"],
                action=semantic_summary["profile_action_consistency"],
            )
        ),
        "",
        "## Gate Summary",
        "",
        (
            "| Agent | Purity | Sem family | Sem pair | Action template | Parse high | "
            "Action | Family high | Target high | Useful high | Rich high | "
            "Low prog | Regret | Slice gate | Transfer gate |"
        ),
        (
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
            "---:|---:|---|"
        ),
    ]
    for agent, stats in sorted(summary.items()):
        transfer_gate = float(stats.get("transfer_gate_pass", 0.0)) >= 0.999
        lines.append(
            "| {agent} | {purity:.3f} | {sem_family:.3f} | {pair:.3f} | "
            "{template:.3f} | {parse:.3f} | {action:.3f} | {family:.3f} | "
            "{target:.3f} | {useful:.3f} | {rich_prog:.3f} | {low:.3f} | "
            "{regret:.3f} | {gate:.3f} | {transfer} |".format(
                agent=agent,
                purity=stats["profile_cluster_purity"],
                sem_family=stats["semantic_family_accuracy"],
                pair=stats["semantic_pair_accuracy"],
                template=stats["profile_action_consistency"],
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
                "| Axis | Held-out | Agent | Purity | Sem pair | Family high | "
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
                "| {axis} | {heldout} | {agent} | {purity:.3f} | {pair:.3f} | "
                "{family:.3f} | {target:.3f} | {useful:.3f} | {low:.3f} | "
                "{gate} |".format(
                    axis=axis,
                    heldout=heldout,
                    agent=agent,
                    purity=stats["profile_cluster_purity"],
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
                "The accepted agent clusters rendered connected components, "
                "identifies active cluster pairs, and fits an anonymous profile "
                "for each pair from candidate-family success feedback, "
                "bound/unbound utility gaps, and action templates. It does not "
                "receive the old semantic kind profile table, kind-to-family "
                "mapping, role-pair table, or concern-weight table."
            ),
            "",
            (
                "This is semantic-profile induction inside the synthetic "
                "connected-component 2A-v2 world. It is not natural-image object "
                "discovery, fully open-ended semantics, human or neural "
                "validation, or open-ended motor/apparatus invention. The "
                "feedback remains synthetic and contract-shaped."
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
    parser.add_argument("--seed", type=int, default=20260622)
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
        write_discovered_report(args.report, payload)

    print("=== Discovered Semantic Profiles Transfer Summary ===")
    semantic = payload["semantic_summary"]["discovered_semantic_inducer"]
    print(
        "semantic_inducer "
        f"clusters={semantic['cluster_count']:.0f} "
        f"profiles={semantic['profile_count']:.0f} "
        f"purity={semantic['profile_cluster_purity']:.3f} "
        f"family={semantic['semantic_family_accuracy']:.3f} "
        f"pair={semantic['semantic_pair_accuracy']:.3f} "
        f"action_template={semantic['profile_action_consistency']:.3f}"
    )
    for agent, stats in sorted(payload["agent_summary"].items()):
        print(
            f"{agent:46s} purity={stats['profile_cluster_purity']:.3f} "
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
