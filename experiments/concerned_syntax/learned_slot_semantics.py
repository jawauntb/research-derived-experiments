#!/usr/bin/env python3
"""Learned role-slot semantics for the 2A-v2 transfer contract.

The rich transfer-repair gate closes held-out role/parse transfer with an
explicit RGB role decoder. This sidecar replaces that decoder with a learned
slot-semantic classifier trained from visible role-token calibration examples,
then reruns the same v2 transfer gate. It is intentionally supervised and
synthetic: the claim is learned role-slot semantics over rendered objects, not
unsupervised object discovery or natural-image vision.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from experiments.concerned_syntax import rich_program_language as rich
from experiments.concerned_syntax.benchmark import (
    HIGH_CONCERN_KINDS,
    PARSES,
    ParseCandidate,
    ShapeTrial,
    _same_subtree,
    concern_gap,
    outcome_for_parse,
    preferred_action,
    utility,
)
from experiments.concerned_syntax.intervention_invention import _padded_components, _random_pair
from experiments.concerned_syntax.intervention_transfer_repair import _kind_and_weight
from experiments.concerned_syntax.pixel_shapes import ExtractedComponent, ROLE_STYLES

ROLE_NAMES: tuple[str, ...] = tuple(ROLE_STYLES)

LEARNED_SEMANTIC_AGENTS: tuple[str, ...] = (
    "learned_rich_program_composer",
    "learned_semantic_family_only",
    "learned_semantic_target_only",
    "learned_semantic_rich_without_concern",
    "learned_slot_semantic_world_model",
)

HELDOUT_ROLE_KINDS: tuple[str, ...] = HIGH_CONCERN_KINDS
HELDOUT_TRUE_PARSES: tuple[str, ...] = tuple(parse.name for parse in PARSES)


@dataclass(frozen=True)
class SlotSemanticDecoder:
    role_prototypes: dict[str, tuple[float, ...]]

    def scores(self, component: ExtractedComponent, slot_index: int) -> dict[str, float]:
        features = slot_semantic_features(component, slot_index)
        return {
            role: -sum(
                (value - prototype[col]) ** 2
                for col, value in enumerate(features)
            )
            for role, prototype in self.role_prototypes.items()
        }

    def predict_role(self, component: ExtractedComponent, slot_index: int) -> str:
        scores = self.scores(component, slot_index)
        return max(ROLE_NAMES, key=lambda role: (scores[role], -ROLE_NAMES.index(role)))

    def nonneutral_margin(self, component: ExtractedComponent, slot_index: int) -> float:
        scores = self.scores(component, slot_index)
        best_active = max(scores[role] for role in ROLE_NAMES if role != "neutral")
        return best_active - scores["neutral"]


@dataclass(frozen=True)
class SlotSemanticResult:
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
    semantic_roles_correct: int
    semantic_kind_correct: int
    semantic_pair_correct: int
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


def slot_semantic_features(component: ExtractedComponent, slot_index: int) -> list[float]:
    del slot_index
    red = component.mean_r / 255.0
    green = component.mean_g / 255.0
    blue = component.mean_b / 255.0
    return [
        component.area / 100.0,
        red,
        green,
        blue,
        component.width / rich.IMAGE_SIZE,
        component.height / rich.IMAGE_SIZE,
        component.density,
        max(red, green, blue),
        abs(red - green),
        abs(red - blue),
        abs(green - blue),
        red * green,
        red * blue,
        green * blue,
    ]


def _slot_training_rows(
    examples: list[rich.PixelExample],
) -> tuple[list[list[float]], list[str]]:
    features: list[list[float]] = []
    labels: list[str] = []
    for example in examples:
        padded = _padded_components(example)
        for slot_index, component in enumerate(padded):
            features.append(slot_semantic_features(component, slot_index))
            labels.append(example.trial.roles[slot_index])
    return features, labels


def train_slot_semantic_decoder(
    calibration_examples: list[rich.PixelExample],
    *,
    seed: int,
    epochs: int,
) -> SlotSemanticDecoder:
    del seed, epochs
    features, labels = _slot_training_rows(calibration_examples)
    role_prototypes: dict[str, tuple[float, ...]] = {}
    for role in ROLE_NAMES:
        role_rows = [row for row, label in zip(features, labels) if label == role]
        if not role_rows:
            raise ValueError(f"no calibration rows for role {role}")
        width = len(role_rows[0])
        role_prototypes[role] = tuple(
            mean(row[col] for row in role_rows)
            for col in range(width)
        )
    return SlotSemanticDecoder(role_prototypes)


def decoded_semantic_roles(
    example: rich.PixelExample,
    decoder: SlotSemanticDecoder,
) -> tuple[str, ...]:
    return tuple(
        decoder.predict_role(component, slot_index)
        for slot_index, component in enumerate(_padded_components(example))
    )


def semantic_role_pair(
    example: rich.PixelExample,
    decoder: SlotSemanticDecoder,
) -> tuple[int, int]:
    scored = sorted(
        range(6),
        key=lambda idx: (
            decoder.nonneutral_margin(_padded_components(example)[idx], idx),
            -idx,
        ),
        reverse=True,
    )[:2]
    left, right = sorted(scored)
    return (left, right)


def summarize_semantic_decoder(
    examples: list[rich.PixelExample],
    decoder: SlotSemanticDecoder,
) -> dict[str, float]:
    slot_total = 0
    slot_correct = 0
    kind_correct = 0
    pair_correct = 0
    scene_correct = 0
    for example in examples:
        decoded = decoded_semantic_roles(example, decoder)
        truth = tuple(example.trial.roles)
        slot_matches = [int(left == right) for left, right in zip(decoded, truth)]
        slot_total += len(slot_matches)
        slot_correct += sum(slot_matches)
        decoded_kind, _ = _kind_and_weight(decoded)
        kind_correct += int(decoded_kind == example.trial.kind)
        pair_correct += int(semantic_role_pair(example, decoder) == example.trial.causal_pair)
        scene_correct += int(len(slot_matches) == 6 and all(slot_matches))
    n = len(examples) or 1
    return {
        "slot_role_accuracy": slot_correct / slot_total if slot_total else 0.0,
        "scene_role_accuracy": scene_correct / n,
        "semantic_kind_accuracy": kind_correct / n,
        "semantic_pair_accuracy": pair_correct / n,
    }


def _semantic_trial(
    example: rich.PixelExample,
    decoder: SlotSemanticDecoder,
) -> ShapeTrial:
    roles = decoded_semantic_roles(example, decoder)
    kind, concern_weight = _kind_and_weight(roles)
    return ShapeTrial(
        trial_id=example.trial.trial_id,
        kind=kind,
        roles=roles,
        true_parse=example.trial.true_parse,
        alternate_parse=example.trial.alternate_parse,
        causal_pair=semantic_role_pair(example, decoder),
        concern_weight=concern_weight,
    )


def _family_from_semantic_roles(
    example: rich.PixelExample,
    decoder: SlotSemanticDecoder,
) -> str:
    roles = decoded_semantic_roles(example, decoder)
    kind, _ = _kind_and_weight(roles)
    return rich.REQUIRED_FAMILY_BY_KIND.get(kind, "observe_pair")


def _target_correct(
    example: rich.PixelExample,
    family: str,
    pair: tuple[int, int] | None,
    anchor: int | None,
) -> int:
    if family == "move_anchor":
        return int(anchor in set(example.trial.causal_pair))
    return int(pair == example.trial.causal_pair)


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


def _append_row(
    rows: list[SlotSemanticResult],
    *,
    example: rich.PixelExample,
    decoder: SlotSemanticDecoder,
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
    required = rich.required_family(example)
    decoded_roles = decoded_semantic_roles(example, decoder)
    decoded_kind, _ = _kind_and_weight(decoded_roles)
    semantic_pair = semantic_role_pair(example, decoder)
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
        SlotSemanticResult(
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
            semantic_roles_correct=int(decoded_roles == tuple(example.trial.roles)),
            semantic_kind_correct=int(decoded_kind == example.trial.kind),
            semantic_pair_correct=int(semantic_pair == example.trial.causal_pair),
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
) -> list[SlotSemanticResult]:
    rows: list[SlotSemanticResult] = []
    for item in rich.evaluate_agent(
        examples,
        models,
        agent="concerned_program_composer",
    ):
        rows.append(
            SlotSemanticResult(
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
                semantic_roles_correct=0,
                semantic_kind_correct=0,
                semantic_pair_correct=0,
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


def _evaluate_semantic_agent(
    examples: list[rich.PixelExample],
    decoder: SlotSemanticDecoder,
    *,
    axis: str,
    heldout: str,
    agent: str,
) -> list[SlotSemanticResult]:
    rows: list[SlotSemanticResult] = []
    for example in examples:
        semantic_trial = _semantic_trial(example, decoder)
        decoded_pair = semantic_role_pair(example, decoder)
        decoded_family = _family_from_semantic_roles(example, decoder)
        decoded_high_concern = concern_gap(semantic_trial) >= 0.10

        if agent == "learned_semantic_family_only":
            probed = decoded_high_concern
            family = decoded_family if probed else "null"
            selected_pair = _random_pair(example, salt=171) if probed else None
        elif agent == "learned_semantic_target_only":
            probed = True
            family = "observe_pair"
            selected_pair = decoded_pair
        elif agent == "learned_semantic_rich_without_concern":
            probed = True
            family = decoded_family
            selected_pair = decoded_pair
        elif agent == "learned_slot_semantic_world_model":
            probed = decoded_high_concern
            family = decoded_family if probed else "null"
            selected_pair = decoded_pair if probed else None
        else:
            raise KeyError(agent)

        anchor = selected_pair[0] if selected_pair is not None else None
        target_ok = _target_correct(example, family, selected_pair, anchor)
        useful = bool(probed and family == rich.required_family(example) and target_ok)
        observed_bound = int(_same_subtree(example.trial.true_parse, *decoded_pair)) if useful else None
        inference_pair = selected_pair if selected_pair is not None else decoded_pair
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
            decoder=decoder,
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


def evaluate_semantic_agents(
    examples: list[rich.PixelExample],
    models: dict[str, rich.LinearBinaryModel],
    decoder: SlotSemanticDecoder,
    *,
    axis: str,
    heldout: str,
) -> list[SlotSemanticResult]:
    rows = _evaluate_learned_baseline(
        examples,
        models,
        axis=axis,
        heldout=heldout,
    )
    for agent in LEARNED_SEMANTIC_AGENTS:
        if agent == "learned_rich_program_composer":
            continue
        rows.extend(
            _evaluate_semantic_agent(
                examples,
                decoder,
                axis=axis,
                heldout=heldout,
                agent=agent,
            )
        )
    return rows


def _safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def summarize_results(rows: list[SlotSemanticResult]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[SlotSemanticResult]] = {}
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
        semantic_roles = _safe_mean([item.semantic_roles_correct for item in items])
        semantic_kind = _safe_mean([item.semantic_kind_correct for item in items])
        semantic_pair = _safe_mean([item.semantic_pair_correct for item in items])
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
                semantic_roles >= 0.95
                and semantic_kind >= 0.95
                and semantic_pair >= 0.95
            )
        )
        summary[agent] = {
            "n": len(items),
            "high_concern_count": len(high),
            "semantic_role_scene_accuracy": semantic_roles,
            "semantic_kind_accuracy": semantic_kind,
            "semantic_pair_accuracy": semantic_pair,
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
    decoder: SlotSemanticDecoder,
) -> dict[str, Any]:
    train_examples, test_examples = _slice_examples(
        axis=axis,
        heldout=heldout,
        train_trials=train_trials,
        test_trials=test_trials,
        seed=seed,
    )
    models = rich.train_rich_models(train_examples, seed=seed, epochs=epochs)
    rows = evaluate_semantic_agents(
        test_examples,
        models,
        decoder,
        axis=axis,
        heldout=heldout,
    )
    return {
        "axis": axis,
        "heldout": heldout,
        "semantic_summary": {
            "learned_slot_semantic_decoder": summarize_semantic_decoder(
                test_examples,
                decoder,
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
    semantic_calibration_trials: int = 600,
    heldout_kinds: tuple[str, ...] = HELDOUT_ROLE_KINDS,
    heldout_parses: tuple[str, ...] = HELDOUT_TRUE_PARSES,
) -> dict[str, Any]:
    calibration_examples = rich.make_filtered_pixel_examples(
        trials=semantic_calibration_trials,
        seed=seed + 2_700_000,
    )
    decoder = train_slot_semantic_decoder(
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
                decoder=decoder,
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
                decoder=decoder,
            )
        )

    return {
        "manifest": {
            "arc": "2A",
            "name": "learned_slot_semantics_transfer",
            "contract": "2A-v2-pixels-rich_programs-transfer",
            "train_trials": train_trials,
            "test_trials": test_trials,
            "semantic_calibration_trials": semantic_calibration_trials,
            "seed": seed,
            "epochs": epochs,
            "heldout_kinds": list(heldout_kinds),
            "heldout_parses": list(heldout_parses),
            "agents": list(LEARNED_SEMANTIC_AGENTS),
            "program_families": list(rich.PROGRAM_FAMILIES),
            "perception": "connected_components_rgb_plus_learned_slot_semantics",
            "semantic_calibration": "supervised_visible_role_token_prototypes",
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
            f"held-out slice/seed, {manifest['semantic_calibration_trials']} "
            f"semantic calibration trials/seed, {manifest['epochs']} SGD epochs, "
            f"role held-outs {', '.join(manifest['heldout_kinds'])}, parse "
            f"held-outs {', '.join(manifest['heldout_parses'])}."
        )
    return (
        f"{manifest['train_trials']} train trials per held-out slice, "
        f"{manifest['test_trials']} test trials per held-out slice, "
        f"{manifest['semantic_calibration_trials']} semantic calibration trials, "
        f"seed {manifest['seed']}, {manifest['epochs']} SGD epochs, role "
        f"held-outs {', '.join(manifest['heldout_kinds'])}, parse held-outs "
        f"{', '.join(manifest['heldout_parses'])}."
    )


def write_semantic_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["agent_summary"]
    semantic_summary = payload["semantic_summary"]["learned_slot_semantic_decoder"]
    manifest = payload["manifest"]
    slice_results = payload.get("slice_results") or summarize_modal_slice_results(
        payload.get("results", [])
    )
    lines = [
        "# Learned Slot Semantics Transfer",
        "",
        "Date: 2026-06-18",
        "",
        (
            "Question: can the `2A-v2-pixels-rich_programs` transfer contract "
            "replace its explicit RGB role decoder with a learned supervised "
            "slot-semantic decoder while preserving held-out role-kind and "
            "true-parse transfer?"
        ),
        "",
        f"Manifest: {_manifest_text(manifest)}",
        "",
        "## Semantic Decoder",
        "",
        "| Slot roles | Scene roles | Kind | Pair |",
        "|---:|---:|---:|---:|",
        (
            "| {slot:.3f} | {scene:.3f} | {kind:.3f} | {pair:.3f} |".format(
                slot=semantic_summary["slot_role_accuracy"],
                scene=semantic_summary["scene_role_accuracy"],
                kind=semantic_summary["semantic_kind_accuracy"],
                pair=semantic_summary["semantic_pair_accuracy"],
            )
        ),
        "",
        "## Gate Summary",
        "",
        (
            "| Agent | Sem roles | Sem kind | Sem pair | Parse high | Action | "
            "Family high | Target high | Useful high | Rich high | Low prog | "
            "Regret | Slice gate | Transfer gate |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for agent, stats in sorted(summary.items()):
        transfer_gate = float(stats.get("transfer_gate_pass", 0.0)) >= 0.999
        lines.append(
            "| {agent} | {roles:.3f} | {kind:.3f} | {pair:.3f} | {parse:.3f} | "
            "{action:.3f} | {family:.3f} | {target:.3f} | {useful:.3f} | "
            "{rich_prog:.3f} | {low:.3f} | {regret:.3f} | {gate:.3f} | "
            "{transfer} |".format(
                agent=agent,
                roles=stats["semantic_role_scene_accuracy"],
                kind=stats["semantic_kind_accuracy"],
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
                "The accepted agent consumes learned slot semantics rather than "
                "nearest-color role decoding: a supervised prototype decoder "
                "maps each rendered component into a visible role token, then "
                "the world model binds target pair, program family, concern "
                "gate, parse observation, and action. Family-only, target-only, "
                "and ungated-rich controls keep the old shortcut failures "
                "visible under the same transfer slices."
            ),
            "",
            (
                "This is not unsupervised object discovery, natural-image "
                "vision, or open-ended program invention. The semantic decoder "
                "uses supervised visible role-token calibration, and the "
                "program grammar remains the provided v2 grammar."
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
    parser.add_argument("--semantic-calibration-trials", type=int, default=600)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    payload = run_experiment(
        train_trials=args.train_trials,
        test_trials=args.test_trials,
        seed=args.seed,
        epochs=args.epochs,
        semantic_calibration_trials=args.semantic_calibration_trials,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.report:
        write_semantic_report(args.report, payload)

    print("=== Learned Slot Semantics Transfer Summary ===")
    semantic = payload["semantic_summary"]["learned_slot_semantic_decoder"]
    print(
        "semantic_decoder "
        f"slot={semantic['slot_role_accuracy']:.3f} "
        f"scene={semantic['scene_role_accuracy']:.3f} "
        f"kind={semantic['semantic_kind_accuracy']:.3f} "
        f"pair={semantic['semantic_pair_accuracy']:.3f}"
    )
    for agent, stats in sorted(payload["agent_summary"].items()):
        print(
            f"{agent:40s} sem_kind={stats['semantic_kind_accuracy']:.3f} "
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
