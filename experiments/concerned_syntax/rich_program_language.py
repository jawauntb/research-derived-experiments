#!/usr/bin/env python3
"""2A-v2 concerned syntax with a richer intervention-program language."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from experiments.concerned_syntax.benchmark import (
    concern_gap,
    outcome_for_parse,
    preferred_action,
    utility,
)
from experiments.concerned_syntax.intervention_invention import (
    _calibration_probe,
    _predict_bound_from_program,
    _random_pair,
    _select_target_pair,
    _value_for_bound,
    make_filtered_pixel_examples,
    train_models,
)
from experiments.concerned_syntax.learned_agents import LinearBinaryModel, train_linear_binary
from experiments.concerned_syntax.pixel_shapes import (
    IMAGE_SIZE,
    PixelExample,
    action_features,
    pixel_surface_features,
    true_bound,
)

RICH_PROGRAM_AGENTS: tuple[str, ...] = (
    "surface_rich_shortcut",
    "random_rich_program",
    "family_without_target",
    "target_without_family",
    "rich_without_concern",
    "concerned_program_composer",
)

PROGRAM_FAMILIES: tuple[str, ...] = (
    "observe_pair",
    "move_anchor",
    "ablate_pair",
    "compose_move_observe",
)

REQUIRED_FAMILY_BY_KIND = {
    "shield_poison": "compose_move_observe",
    "repair_core": "move_anchor",
    "food_trap": "ablate_pair",
    "ornament_signal": "observe_pair",
}


@dataclass(frozen=True)
class RichProgram:
    name: str
    family: str
    cost: float
    pair: tuple[int, int] | None = None
    anchor: int | None = None


@dataclass(frozen=True)
class RichProgramResult:
    trial_id: int
    agent: str
    program: str
    family: str
    selected_pair: tuple[int, int] | None
    anchor: int | None
    probed: int
    high_concern: int
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


def candidate_programs() -> tuple[RichProgram, ...]:
    programs = [RichProgram("null", "null", 0.0)]
    for a in range(6):
        for b in range(a + 1, 6):
            programs.append(
                RichProgram(f"observe_pair_{a}_{b}", "observe_pair", 0.04, pair=(a, b))
            )
            programs.append(
                RichProgram(f"ablate_pair_{a}_{b}", "ablate_pair", 0.08, pair=(a, b))
            )
            programs.append(
                RichProgram(
                    f"compose_move_observe_{a}_{a}_{b}",
                    "compose_move_observe",
                    0.10,
                    pair=(a, b),
                    anchor=a,
                )
            )
            programs.append(
                RichProgram(
                    f"compose_move_observe_{b}_{a}_{b}",
                    "compose_move_observe",
                    0.10,
                    pair=(a, b),
                    anchor=b,
                )
            )
    for anchor in range(6):
        programs.append(
            RichProgram(f"move_anchor_{anchor}", "move_anchor", 0.06, anchor=anchor)
        )
    return tuple(programs)


def required_family(example: PixelExample) -> str:
    return REQUIRED_FAMILY_BY_KIND[example.trial.kind]


def train_rich_models(
    train_examples: list[PixelExample],
    *,
    seed: int,
    epochs: int,
) -> dict[str, LinearBinaryModel]:
    models = train_models(train_examples, seed=seed, epochs=epochs)
    family_x = [pixel_surface_features(example) for example in train_examples]
    for family in PROGRAM_FAMILIES:
        family_y = [int(required_family(example) == family) for example in train_examples]
        models[f"family_{family}"] = train_linear_binary(
            family_x,
            family_y,
            seed=seed + 101 + PROGRAM_FAMILIES.index(family),
            epochs=epochs,
            learning_rate=0.05,
        )
    return models


def _select_family(
    example: PixelExample,
    models: dict[str, LinearBinaryModel],
) -> str:
    return max(
        PROGRAM_FAMILIES,
        key=lambda family: (
            models[f"family_{family}"].score(pixel_surface_features(example)),
            -PROGRAM_FAMILIES.index(family),
        ),
    )


def _program_name(
    family: str,
    pair: tuple[int, int] | None,
    anchor: int | None,
) -> str:
    if family == "null":
        return "null"
    if family == "move_anchor":
        return f"move_anchor_{anchor}"
    if family == "observe_pair" and pair is not None:
        return f"observe_pair_{pair[0]}_{pair[1]}"
    if family == "ablate_pair" and pair is not None:
        return f"ablate_pair_{pair[0]}_{pair[1]}"
    if family == "compose_move_observe" and pair is not None:
        return f"compose_move_observe_{anchor}_{pair[0]}_{pair[1]}"
    return family


def _program_cost(family: str, probed: bool) -> float:
    if not probed:
        return 0.0
    if family == "observe_pair":
        return 0.04
    if family == "move_anchor":
        return 0.06
    if family == "ablate_pair":
        return 0.08
    if family == "compose_move_observe":
        return 0.10
    return 0.0


def _target_correct(
    example: PixelExample,
    family: str,
    pair: tuple[int, int] | None,
    anchor: int | None,
) -> int:
    if family == "move_anchor":
        return int(anchor in set(example.trial.causal_pair))
    return int(pair == example.trial.causal_pair)


def evaluate_agent(
    examples: list[PixelExample],
    models: dict[str, LinearBinaryModel],
    *,
    agent: str,
) -> list[RichProgramResult]:
    rows: list[RichProgramResult] = []
    for example in examples:
        gap = concern_gap(example.trial)
        high = int(gap >= 0.10)
        learned_pair = _select_target_pair(example, models)
        learned_family = _select_family(example, models)
        required = required_family(example)

        if agent == "surface_rich_shortcut":
            probed = False
            family = "null"
            selected_pair = None
            anchor = None
            bound = _predict_bound_from_program(
                example,
                models,
                probed=False,
                selected_pair=None,
            )
            action_label = models["shortcut_action"].predict(pixel_surface_features(example))
        elif agent == "random_rich_program":
            probed = True
            family = PROGRAM_FAMILIES[
                (example.trial.trial_id * 31 + len(example.components)) % len(PROGRAM_FAMILIES)
            ]
            selected_pair = _random_pair(example, salt=31)
            anchor = selected_pair[0]
            bound = _predict_bound_from_program(
                example,
                models,
                probed=False,
                selected_pair=None,
            )
            action_label = models["action_bound"].predict(action_features(example, bound=bound))
        elif agent == "family_without_target":
            policy_probe = bool(models["policy"].predict(pixel_surface_features(example)))
            probed = policy_probe or _calibration_probe(example)
            family = learned_family
            selected_pair = _random_pair(example, salt=43) if probed else None
            anchor = selected_pair[0] if selected_pair is not None else None
            useful = bool(
                probed
                and family == required
                and _target_correct(example, family, selected_pair, anchor)
            )
            bound = _predict_bound_from_program(
                example,
                models,
                probed=useful,
                selected_pair=example.trial.causal_pair if useful else selected_pair,
            )
            action_label = models["action_bound"].predict(action_features(example, bound=bound))
        elif agent == "target_without_family":
            probed = True
            family = "observe_pair"
            selected_pair = learned_pair
            anchor = selected_pair[0]
            useful = bool(
                family == required
                and _target_correct(example, family, selected_pair, anchor)
            )
            bound = _predict_bound_from_program(
                example,
                models,
                probed=useful,
                selected_pair=selected_pair,
            )
            action_label = models["action_bound"].predict(action_features(example, bound=bound))
        elif agent == "rich_without_concern":
            probed = True
            family = learned_family
            selected_pair = learned_pair
            anchor = selected_pair[0]
            useful = bool(
                family == required
                and _target_correct(example, family, selected_pair, anchor)
            )
            bound = _predict_bound_from_program(
                example,
                models,
                probed=useful,
                selected_pair=selected_pair,
            )
            action_label = models["action_bound"].predict(action_features(example, bound=bound))
        elif agent == "concerned_program_composer":
            policy_probe = bool(models["policy"].predict(pixel_surface_features(example)))
            probed = policy_probe or _calibration_probe(example)
            family = learned_family if probed else "null"
            selected_pair = learned_pair if probed else None
            anchor = selected_pair[0] if selected_pair is not None else None
            useful = bool(
                probed
                and family == required
                and _target_correct(example, family, selected_pair, anchor)
            )
            bound = _predict_bound_from_program(
                example,
                models,
                probed=useful,
                selected_pair=selected_pair,
            )
            action_label = models["action_bound"].predict(action_features(example, bound=bound))
        else:
            raise KeyError(agent)

        family_correct = int(family == required)
        target_correct = _target_correct(example, family, selected_pair, anchor)
        useful_program = int(probed and family_correct and target_correct)
        target_bound = true_bound(example)
        pred_action = "consume" if action_label else "skip"
        true_outcome = outcome_for_parse(example.trial, example.trial.true_parse)
        true_action = preferred_action(true_outcome, example.trial.concern_weight)
        rows.append(
            RichProgramResult(
                trial_id=example.trial.trial_id,
                agent=agent,
                program=_program_name(family, selected_pair, anchor),
                family=family,
                selected_pair=selected_pair,
                anchor=anchor,
                probed=int(probed),
                high_concern=high,
                family_correct=family_correct,
                target_correct=target_correct,
                useful_program=useful_program,
                rich_program=int(family in {"move_anchor", "ablate_pair", "compose_move_observe"}),
                parse_correct=int(bound == target_bound),
                action_correct=int(pred_action == true_action),
                subtree_correct=int(bound == target_bound),
                object_extraction_ok=int(len(example.components) == 6),
                mean_program_cost=_program_cost(family, probed),
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
) -> list[RichProgramResult]:
    rows: list[RichProgramResult] = []
    for agent in RICH_PROGRAM_AGENTS:
        rows.extend(evaluate_agent(examples, models, agent=agent))
    return rows


def _safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def summarize_results(rows: list[RichProgramResult]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[RichProgramResult]] = {}
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
        family_high = _safe_mean([item.family_correct for item in high])
        useful_high = _safe_mean([item.useful_program for item in high])
        rich_high = _safe_mean([item.rich_program for item in high if item.probed])
        summary[agent] = {
            "n": len(items),
            "parse_accuracy_high_concern": parse_high,
            "action_accuracy": action,
            "subtree_accuracy": subtree,
            "object_extraction_rate": extraction,
            "high_concern_program_rate": high_probe,
            "low_concern_program_rate": low_probe,
            "target_accuracy_high_concern": target_high,
            "family_accuracy_high_concern": family_high,
            "useful_program_rate_high_concern": useful_high,
            "rich_program_rate_high_concern": rich_high,
            "mean_program_cost": _safe_mean([item.mean_program_cost for item in items]),
            "mean_regret": _safe_mean([item.regret for item in items]),
            "gate_pass": bool(
                extraction >= 0.99
                and parse_high >= 0.75
                and action >= 0.85
                and subtree >= 0.75
                and high_probe >= 0.70
                and low_probe <= 0.25
                and target_high >= 0.70
                and family_high >= 0.70
                and useful_high >= 0.70
                and rich_high >= 0.70
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
    train_examples = make_filtered_pixel_examples(trials=train_trials, seed=seed)
    test_examples = make_filtered_pixel_examples(
        trials=test_trials,
        seed=seed + 1_100_000,
    )
    models = train_rich_models(train_examples, seed=seed, epochs=epochs)
    rows = evaluate_agents(test_examples, models)
    return {
        "manifest": {
            "arc": "2A",
            "name": "concerned_rich_program_language",
            "contract": "2A-v2-pixels-rich_programs",
            "train_trials": train_trials,
            "test_trials": test_trials,
            "seed": seed,
            "epochs": epochs,
            "agents": list(RICH_PROGRAM_AGENTS),
            "programs": [program.name for program in candidate_programs()],
            "program_families": list(PROGRAM_FAMILIES),
            "image_size": IMAGE_SIZE,
            "perception": "connected_components_rgb",
        },
        "agent_summary": summarize_results(rows),
        "results": [asdict(row) for row in rows],
    }


def summarize_seed_payloads(payloads: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
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
        summary[name] = stats
    return summary


def _manifest_text(manifest: dict[str, Any]) -> str:
    if "seed" in manifest:
        return (
            f"{manifest['train_trials']} train trials, "
            f"{manifest['test_trials']} test trials, seed {manifest['seed']}, "
            f"{manifest['epochs']} SGD epochs, "
            f"{len(manifest['programs'])} programs across "
            f"{len(manifest['program_families'])} families, "
            f"{manifest['image_size']}x{manifest['image_size']} RGB images."
        )
    seeds = manifest.get("seeds", [])
    return (
        f"{len(seeds)} seeds, {manifest['train_trials']} train trials per seed, "
        f"{manifest['test_trials']} test trials per seed, "
        f"{manifest['epochs']} SGD epochs, "
        f"{len(manifest['programs'])} programs across "
        f"{len(manifest['program_families'])} families, "
        f"{manifest['image_size']}x{manifest['image_size']} RGB images."
    )


def write_agent_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["agent_summary"]
    manifest = payload["manifest"]
    lines = [
        "# Concerned Rich Program Language",
        "",
        "Date: 2026-06-17",
        "",
        (
            "Question: can a pixel-level concerned-syntax agent choose among "
            "`observe_pair`, `move_anchor`, `ablate_pair`, and composed "
            "two-step programs while preserving low-concern discipline?"
        ),
        "",
        f"Manifest: {_manifest_text(manifest)}",
        "",
        "## Gate Summary",
        "",
        (
            "| Agent | Parse high | Action | Subtree | Objects | High prog | "
            "Low prog | Family high | Target high | Useful high | Rich high | "
            "Regret | Gate |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for agent, stats in sorted(summary.items()):
        gate_pass = float(stats["gate_pass"]) >= 0.999
        lines.append(
            "| {agent} | {parse:.3f} | {action:.3f} | {subtree:.3f} | "
            "{objects:.3f} | {high:.3f} | {low:.3f} | {family:.3f} | "
            "{target:.3f} | {useful:.3f} | {rich:.3f} | {regret:.3f} | "
            "{gate} |".format(
                agent=agent,
                parse=stats["parse_accuracy_high_concern"],
                action=stats["action_accuracy"],
                subtree=stats["subtree_accuracy"],
                objects=stats["object_extraction_rate"],
                high=stats["high_concern_program_rate"],
                low=stats["low_concern_program_rate"],
                family=stats["family_accuracy_high_concern"],
                target=stats["target_accuracy_high_concern"],
                useful=stats["useful_program_rate_high_concern"],
                rich=stats["rich_program_rate_high_concern"],
                regret=stats["mean_regret"],
                gate="PASS" if gate_pass else "fail",
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The v2 gate makes program-family choice part of intervention "
                "invention. High-concern role families require different useful "
                "program families: composed move+observe for shield/poison, "
                "move-anchor for repair/core, and ablation for food/trap. The "
                "accepted agent must learn when to act, what target matters, "
                "and which program family exposes the hidden binding."
            ),
            "",
            (
                "This is still a provided program grammar, not open-ended motor "
                "apparatus discovery. It is stronger than v1 because `observe_pair` "
                "alone is no longer the universal useful intervention."
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
    parser.add_argument("--seed", type=int, default=20260617)
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

    print("=== Concerned Rich Program Language Summary ===")
    for agent, stats in sorted(payload["agent_summary"].items()):
        print(
            f"{agent:28s} parse_high={stats['parse_accuracy_high_concern']:.3f} "
            f"action={stats['action_accuracy']:.3f} "
            f"family_high={stats['family_accuracy_high_concern']:.3f} "
            f"target_high={stats['target_accuracy_high_concern']:.3f} "
            f"useful_high={stats['useful_program_rate_high_concern']:.3f} "
            f"low_prog={stats['low_concern_program_rate']:.3f} "
            f"gate={stats['gate_pass']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
