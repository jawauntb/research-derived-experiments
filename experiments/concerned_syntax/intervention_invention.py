#!/usr/bin/env python3
"""Pixel-level concerned intervention invention.

This gate removes the last provided-intervention crutch from the pixel
concerned-syntax experiment. The agent receives extracted object features from
the rendered image and a menu of candidate probe programs. It must learn both
when to spend an intervention and which object pair to probe.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from experiments.concerned_syntax.benchmark import (
    _same_subtree,
    concern_gap,
    make_trial,
    outcome_for_parse,
    preferred_action,
    utility,
)
from experiments.concerned_syntax.learned_agents import (
    PAIR_INDEX,
    PAIR_TO_INDEX,
    LinearBinaryModel,
    train_linear_binary,
)
from experiments.concerned_syntax.pixel_shapes import (
    IMAGE_SIZE,
    ExtractedComponent,
    PixelExample,
    action_features,
    extract_components,
    make_pixel_examples,
    parse_features,
    pixel_surface_features,
    render_pixel_surface,
    true_bound,
)

PROGRAM_AGENTS: tuple[str, ...] = (
    "surface_program_shortcut",
    "random_program_probe",
    "concern_without_target",
    "target_without_concern",
    "concerned_program_inventor",
)


@dataclass(frozen=True)
class ProbeProgram:
    name: str
    kind: str
    cost: float
    pair: tuple[int, int] | None = None


@dataclass(frozen=True)
class ProgramResult:
    trial_id: int
    agent: str
    program: str
    selected_pair: tuple[int, int] | None
    probed: int
    high_concern: int
    target_correct: int
    useful_program: int
    parse_correct: int
    action_correct: int
    subtree_correct: int
    object_extraction_ok: int
    mean_probe_cost: float
    regret: float


def candidate_programs() -> tuple[ProbeProgram, ...]:
    programs = [ProbeProgram("null", "null", 0.0)]
    programs.extend(
        ProbeProgram(f"observe_pair_{a}_{b}", "observe_pair", 0.04, pair=(a, b))
        for a, b in PAIR_INDEX
    )
    return tuple(programs)


def make_filtered_pixel_examples(
    *,
    trials: int,
    seed: int,
    include_kinds: set[str] | None = None,
    exclude_kinds: set[str] | None = None,
) -> list[PixelExample]:
    """Generate pixel examples under role-kind filters for transfer stress tests."""

    rng = random.Random(seed)
    examples: list[PixelExample] = []
    attempts = 0
    while len(examples) < trials:
        trial = make_trial(attempts, rng)
        attempts += 1
        if include_kinds is not None and trial.kind not in include_kinds:
            continue
        if exclude_kinds is not None and trial.kind in exclude_kinds:
            continue
        image = render_pixel_surface(trial)
        examples.append(
            PixelExample(
                trial=trial,
                image=image,
                components=extract_components(image),
            )
        )
    return examples


def _blank_component() -> ExtractedComponent:
    center = (IMAGE_SIZE - 1) / 2.0
    return ExtractedComponent(
        cx=center,
        cy=center,
        area=0,
        mean_r=0.0,
        mean_g=0.0,
        mean_b=0.0,
        width=0,
        height=0,
        density=0.0,
    )


def _base_pixel_center(index: int) -> tuple[float, float]:
    angle = 2.0 * math.pi * index / 6.0
    scale = 15.0
    center = (IMAGE_SIZE - 1) / 2.0
    return (
        center + math.cos(angle) * scale,
        center - math.sin(angle) * scale,
    )


def _padded_components(example: PixelExample) -> list[ExtractedComponent]:
    components = list(example.components[:6])
    if len(components) == 6:
        unused = set(range(6))
        aligned: list[ExtractedComponent] = []
        for position in range(6):
            px, py = _base_pixel_center(position)
            choice = min(
                unused,
                key=lambda idx: (components[idx].cx - px) ** 2
                + (components[idx].cy - py) ** 2,
            )
            unused.remove(choice)
            aligned.append(components[choice])
        return aligned
    while len(components) < 6:
        components.append(_blank_component())
    return components


def _component_features(component: ExtractedComponent) -> list[float]:
    center = (IMAGE_SIZE - 1) / 2.0
    return [
        (component.cx - center) / center,
        (center - component.cy) / center,
        component.area / 100.0,
        component.mean_r / 255.0,
        component.mean_g / 255.0,
        component.mean_b / 255.0,
        component.width / IMAGE_SIZE,
        component.height / IMAGE_SIZE,
        component.density,
    ]


def _pair_one_hot(pair: tuple[int, int]) -> list[float]:
    features = [0.0] * len(PAIR_INDEX)
    features[PAIR_TO_INDEX[pair]] = 1.0
    return features


def slot_features(example: PixelExample, index: int) -> list[float]:
    """Features for learning whether an extracted object participates in a probe."""

    components = _padded_components(example)
    features = _component_features(components[index])
    position = [0.0] * 6
    position[index] = 1.0
    features.extend(position)
    for other_index, other in enumerate(components):
        if other_index == index:
            continue
        features.extend(_component_features(other))
    return features


def program_features(example: PixelExample, pair: tuple[int, int]) -> list[float]:
    """Features for deciding whether ``observe_pair(a,b)`` is the useful program."""

    components = _padded_components(example)
    left = components[pair[0]]
    right = components[pair[1]]
    left_features = _component_features(left)
    right_features = _component_features(right)
    unordered_min = [min(a, b) for a, b in zip(left_features, right_features)]
    unordered_max = [max(a, b) for a, b in zip(left_features, right_features)]
    unordered_sum = [a + b for a, b in zip(left_features, right_features)]
    unordered_gap = [abs(a - b) for a, b in zip(left_features, right_features)]
    distance = math.hypot(
        (left.cx - right.cx) / IMAGE_SIZE,
        (left.cy - right.cy) / IMAGE_SIZE,
    )

    features = pixel_surface_features(example)
    features.extend(_pair_one_hot(pair))
    features.extend(left_features)
    features.extend(right_features)
    features.extend(unordered_min)
    features.extend(unordered_max)
    features.extend(unordered_sum)
    features.extend(unordered_gap)
    features.append(distance)
    return features


def _true_action_label(example: PixelExample) -> int:
    outcome = outcome_for_parse(example.trial, example.trial.true_parse)
    return int(preferred_action(outcome, example.trial.concern_weight) == "consume")


def train_models(
    train_examples: list[PixelExample],
    *,
    seed: int,
    epochs: int,
) -> dict[str, LinearBinaryModel]:
    policy_x = [pixel_surface_features(example) for example in train_examples]
    policy_y = [int(concern_gap(example.trial) >= 0.10) for example in train_examples]

    target_x: list[list[float]] = []
    target_y: list[int] = []
    slot_x: list[list[float]] = []
    slot_y: list[int] = []
    for example in train_examples:
        causal_slots = set(example.trial.causal_pair)
        for index in range(6):
            label = int(index in causal_slots)
            repeats = 2 if label else 1
            for _ in range(repeats):
                slot_x.append(slot_features(example, index))
                slot_y.append(label)
        for pair in PAIR_INDEX:
            label = int(pair == example.trial.causal_pair)
            repeats = 10 if label else 1
            for _ in range(repeats):
                target_x.append(program_features(example, pair))
                target_y.append(label)

    bound_x = [
        parse_features(example, observed=True, observed_bound=true_bound(example))
        for example in train_examples
    ]
    prior_x = [
        parse_features(example, observed=False, observed_bound=0)
        for example in train_examples
    ]
    bound_y = [true_bound(example) for example in train_examples]

    action_x = [
        action_features(example, bound=true_bound(example))
        for example in train_examples
    ]
    action_y = [_true_action_label(example) for example in train_examples]
    shortcut_x = [pixel_surface_features(example) for example in train_examples]

    return {
        "policy": train_linear_binary(
            policy_x,
            policy_y,
            seed=seed + 41,
            epochs=epochs,
        ),
        "target_program": train_linear_binary(
            target_x,
            target_y,
            seed=seed + 42,
            epochs=epochs,
            learning_rate=0.05,
        ),
        "target_slot": train_linear_binary(
            slot_x,
            slot_y,
            seed=seed + 47,
            epochs=epochs,
            learning_rate=0.05,
        ),
        "bound_probe": train_linear_binary(
            bound_x,
            bound_y,
            seed=seed + 43,
            epochs=epochs,
        ),
        "bound_prior": train_linear_binary(
            prior_x,
            bound_y,
            seed=seed + 44,
            epochs=epochs,
        ),
        "action_bound": train_linear_binary(
            action_x,
            action_y,
            seed=seed + 45,
            epochs=epochs,
        ),
        "shortcut_action": train_linear_binary(
            shortcut_x,
            action_y,
            seed=seed + 46,
            epochs=epochs,
        ),
    }


def _select_target_pair(
    example: PixelExample,
    models: dict[str, LinearBinaryModel],
) -> tuple[int, int]:
    program_model = models["target_program"]
    slot_model = models["target_slot"]
    slot_scores = [
        slot_model.score(slot_features(example, index))
        for index in range(6)
    ]
    return max(
        PAIR_INDEX,
        key=lambda pair: (
            slot_scores[pair[0]]
            + slot_scores[pair[1]]
            + 0.15 * program_model.score(program_features(example, pair)),
            -PAIR_TO_INDEX[pair],
        ),
    )


def _random_pair(example: PixelExample, *, salt: int) -> tuple[int, int]:
    idx = (
        example.trial.trial_id * 1_103_515_245
        + salt * 97_531
        + len(example.components) * 17
    ) % len(PAIR_INDEX)
    return PAIR_INDEX[idx]


def _calibration_probe(example: PixelExample, *, percent: int = 15) -> bool:
    component_code = sum(
        (idx + 1) * (component.area + int(component.mean_g))
        for idx, component in enumerate(example.components)
    )
    code = (
        example.trial.trial_id * 2_654_435_761
        + component_code
        + int(example.trial.concern_weight * 1000)
    ) % 100
    return code < percent


def _predict_bound_from_program(
    example: PixelExample,
    models: dict[str, LinearBinaryModel],
    *,
    probed: bool,
    selected_pair: tuple[int, int] | None,
) -> int:
    useful = bool(probed and selected_pair == example.trial.causal_pair)
    if useful:
        observed = true_bound(example)
        return models["bound_probe"].predict(
            parse_features(example, observed=True, observed_bound=observed)
        )
    return models["bound_prior"].predict(
        parse_features(example, observed=False, observed_bound=0)
    )


def _value_for_bound(example: PixelExample, bound: int) -> float:
    true_outcome = outcome_for_parse(example.trial, example.trial.true_parse)
    if bound == true_bound(example):
        return utility(true_outcome, example.trial.concern_weight)
    alternate_outcome = outcome_for_parse(
        example.trial,
        example.trial.alternate_parse,
    )
    return utility(alternate_outcome, example.trial.concern_weight)


def _program_for_pair(pair: tuple[int, int] | None) -> str:
    if pair is None:
        return "null"
    return f"observe_pair_{pair[0]}_{pair[1]}"


def evaluate_agent(
    examples: list[PixelExample],
    models: dict[str, LinearBinaryModel],
    *,
    agent: str,
) -> list[ProgramResult]:
    rows: list[ProgramResult] = []
    for example in examples:
        gap = concern_gap(example.trial)
        high = int(gap >= 0.10)
        learned_pair = _select_target_pair(example, models)

        if agent == "surface_program_shortcut":
            probed = False
            selected_pair = None
            bound = _predict_bound_from_program(
                example,
                models,
                probed=False,
                selected_pair=None,
            )
            action_label = models["shortcut_action"].predict(
                pixel_surface_features(example)
            )
        elif agent == "random_program_probe":
            probed = True
            selected_pair = _random_pair(example, salt=11)
            bound = _predict_bound_from_program(
                example,
                models,
                probed=probed,
                selected_pair=selected_pair,
            )
            action_label = models["action_bound"].predict(
                action_features(example, bound=bound)
            )
        elif agent == "concern_without_target":
            policy_probe = bool(
                models["policy"].predict(pixel_surface_features(example))
            )
            probed = policy_probe or _calibration_probe(example)
            selected_pair = _random_pair(example, salt=23) if probed else None
            bound = _predict_bound_from_program(
                example,
                models,
                probed=probed,
                selected_pair=selected_pair,
            )
            action_label = models["action_bound"].predict(
                action_features(example, bound=bound)
            )
        elif agent == "target_without_concern":
            probed = True
            selected_pair = learned_pair
            bound = _predict_bound_from_program(
                example,
                models,
                probed=probed,
                selected_pair=selected_pair,
            )
            action_label = models["action_bound"].predict(
                action_features(example, bound=bound)
            )
        elif agent == "concerned_program_inventor":
            policy_probe = bool(
                models["policy"].predict(pixel_surface_features(example))
            )
            probed = policy_probe or _calibration_probe(example)
            selected_pair = learned_pair if probed else None
            bound = _predict_bound_from_program(
                example,
                models,
                probed=probed,
                selected_pair=selected_pair,
            )
            action_label = models["action_bound"].predict(
                action_features(example, bound=bound)
            )
        else:
            raise KeyError(agent)

        target_bound = true_bound(example)
        target_correct = int(selected_pair == example.trial.causal_pair)
        useful_program = int(probed and target_correct)
        pred_action = "consume" if action_label else "skip"
        true_outcome = outcome_for_parse(example.trial, example.trial.true_parse)
        true_action = preferred_action(true_outcome, example.trial.concern_weight)
        rows.append(
            ProgramResult(
                trial_id=example.trial.trial_id,
                agent=agent,
                program=_program_for_pair(selected_pair),
                selected_pair=selected_pair,
                probed=int(probed),
                high_concern=high,
                target_correct=target_correct,
                useful_program=useful_program,
                parse_correct=int(bound == target_bound),
                action_correct=int(pred_action == true_action),
                subtree_correct=int(bound == target_bound),
                object_extraction_ok=int(len(example.components) == 6),
                mean_probe_cost=0.04 if probed else 0.0,
                regret=max(
                    0.0,
                    utility(true_outcome, example.trial.concern_weight)
                    - _value_for_bound(example, bound),
                ),
            )
        )
    return rows


def evaluate_agents(
    examples: list[PixelExample],
    models: dict[str, LinearBinaryModel],
) -> list[ProgramResult]:
    rows: list[ProgramResult] = []
    for agent in PROGRAM_AGENTS:
        rows.extend(evaluate_agent(examples, models, agent=agent))
    return rows


def _safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def summarize_results(rows: list[ProgramResult]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[ProgramResult]] = {}
    for row in rows:
        grouped.setdefault(row.agent, []).append(row)

    summary: dict[str, dict[str, Any]] = {}
    for agent, items in grouped.items():
        high = [item for item in items if item.high_concern]
        low = [item for item in items if not item.high_concern]
        high_probe = _safe_mean([item.probed for item in high])
        low_probe = _safe_mean([item.probed for item in low])
        parse_high = _safe_mean([item.parse_correct for item in high])
        action = _safe_mean([item.action_correct for item in items])
        subtree = _safe_mean([item.subtree_correct for item in items])
        extraction = _safe_mean([item.object_extraction_ok for item in items])
        target_high = _safe_mean([item.target_correct for item in high])
        useful_high = _safe_mean([item.useful_program for item in high])
        summary[agent] = {
            "n": len(items),
            "parse_accuracy_high_concern": parse_high,
            "action_accuracy": action,
            "subtree_accuracy": subtree,
            "object_extraction_rate": extraction,
            "high_concern_probe_rate": high_probe,
            "low_concern_probe_rate": low_probe,
            "target_accuracy_high_concern": target_high,
            "useful_program_rate_high_concern": useful_high,
            "mean_probe_cost": _safe_mean([item.mean_probe_cost for item in items]),
            "mean_regret": _safe_mean([item.regret for item in items]),
            "gate_pass": bool(
                extraction >= 0.99
                and parse_high >= 0.75
                and action >= 0.85
                and subtree >= 0.75
                and high_probe >= 0.70
                and low_probe <= 0.25
                and target_high >= 0.75
                and useful_high >= 0.70
            ),
        }
    return summary


def run_experiment(
    *,
    train_trials: int,
    test_trials: int,
    seed: int,
    epochs: int,
) -> dict[str, Any]:
    train_examples = make_pixel_examples(trials=train_trials, seed=seed)
    test_examples = make_pixel_examples(trials=test_trials, seed=seed + 500_000)
    models = train_models(train_examples, seed=seed, epochs=epochs)
    rows = evaluate_agents(test_examples, models)
    return {
        "manifest": {
            "arc": "2A",
            "name": "concerned_intervention_invention",
            "train_trials": train_trials,
            "test_trials": test_trials,
            "seed": seed,
            "epochs": epochs,
            "agents": list(PROGRAM_AGENTS),
            "programs": [program.name for program in candidate_programs()],
            "image_size": IMAGE_SIZE,
            "perception": "connected_components_rgb",
        },
        "agent_summary": summarize_results(rows),
        "results": [asdict(row) for row in rows],
    }


def run_role_transfer_experiment(
    *,
    train_trials: int,
    test_trials: int,
    seed: int,
    epochs: int,
    heldout_kind: str,
) -> dict[str, Any]:
    """Train with one role-pair kind held out, then evaluate on that kind."""

    train_examples = make_filtered_pixel_examples(
        trials=train_trials,
        seed=seed,
        exclude_kinds={heldout_kind},
    )
    test_examples = make_filtered_pixel_examples(
        trials=test_trials,
        seed=seed + 700_000,
        include_kinds={heldout_kind},
    )
    models = train_models(train_examples, seed=seed, epochs=epochs)
    rows = evaluate_agents(test_examples, models)
    return {
        "manifest": {
            "arc": "2A",
            "name": "concerned_intervention_invention_role_transfer",
            "contract": "2A-v1-pixels-observe_pair",
            "train_trials": train_trials,
            "test_trials": test_trials,
            "seed": seed,
            "epochs": epochs,
            "heldout_kind": heldout_kind,
            "agents": list(PROGRAM_AGENTS),
            "programs": [program.name for program in candidate_programs()],
            "image_size": IMAGE_SIZE,
            "perception": "connected_components_rgb",
        },
        "agent_summary": summarize_results(rows),
        "results": [asdict(row) for row in rows],
    }


def summarize_seed_payloads(payloads: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
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


def _manifest_text(manifest: dict[str, Any]) -> str:
    if "seed" in manifest:
        return (
            f"{manifest['train_trials']} train trials, "
            f"{manifest['test_trials']} test trials, seed {manifest['seed']}, "
            f"{manifest['epochs']} SGD epochs, "
            f"{len(manifest['programs'])} probe programs, "
            f"{manifest['image_size']}x{manifest['image_size']} RGB images."
        )
    seeds = manifest.get("seeds", [])
    return (
        f"{len(seeds)} seeds, {manifest['train_trials']} train trials per seed, "
        f"{manifest['test_trials']} test trials per seed, "
        f"{manifest['epochs']} SGD epochs, "
        f"{len(manifest['programs'])} probe programs, "
        f"{manifest['image_size']}x{manifest['image_size']} RGB images."
    )


def write_agent_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["agent_summary"]
    manifest = payload["manifest"]
    lines = [
        "# Concerned Intervention Invention",
        "",
        "Date: 2026-06-16",
        "",
        (
            "Question: can a pixel-level concerned-syntax agent learn both "
            "when to intervene and which object-pair probe program makes the "
            "viability-relevant hidden binding observable?"
        ),
        "",
        f"Manifest: {_manifest_text(manifest)}",
        "",
        "## Gate Summary",
        "",
        (
            "| Agent | Parse high | Action | Subtree | Objects | High probe | "
            "Low probe | Target high | Useful high | Regret | Gate |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for agent, stats in sorted(summary.items()):
        gate_pass = float(stats["gate_pass"]) >= 0.999
        lines.append(
            "| {agent} | {parse:.3f} | {action:.3f} | {subtree:.3f} | "
            "{objects:.3f} | {high:.3f} | {low:.3f} | {target:.3f} | "
            "{useful:.3f} | {regret:.3f} | {gate} |".format(
                agent=agent,
                parse=stats["parse_accuracy_high_concern"],
                action=stats["action_accuracy"],
                subtree=stats["subtree_accuracy"],
                objects=stats["object_extraction_rate"],
                high=stats["high_concern_probe_rate"],
                low=stats["low_concern_probe_rate"],
                target=stats["target_accuracy_high_concern"],
                useful=stats["useful_program_rate_high_concern"],
                regret=stats["mean_regret"],
                gate="PASS" if gate_pass else "fail",
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This gate makes probe target selection part of the task. The agent "
            "does not receive the causal pair as metadata; it sees extracted "
            "pixel-object features and scores candidate `observe_pair(a,b)` "
            "programs. The accepted agent must choose a useful target under "
            "a concern gate. Surface shortcuts fail hidden binding, random "
            "program probes waste budget, concern without target probes at "
            "the right time but asks the wrong question, and target without "
            "concern violates the low-concern cap.",
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
    parser.add_argument("--seed", type=int, default=20260616)
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--agent-report", type=Path)
    args = parser.parse_args()

    payload = run_experiment(
        train_trials=args.train_trials,
        test_trials=args.test_trials,
        seed=args.seed,
        epochs=args.epochs,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.agent_report:
        write_agent_report(args.agent_report, payload)

    print("=== Concerned Intervention Invention Summary ===")
    for agent, stats in sorted(payload["agent_summary"].items()):
        print(
            f"{agent:28s} parse_high={stats['parse_accuracy_high_concern']:.3f} "
            f"action={stats['action_accuracy']:.3f} "
            f"target_high={stats['target_accuracy_high_concern']:.3f} "
            f"useful_high={stats['useful_program_rate_high_concern']:.3f} "
            f"low_probe={stats['low_concern_probe_rate']:.3f} "
            f"gate={stats['gate_pass']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
