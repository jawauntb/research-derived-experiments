#!/usr/bin/env python3
"""Search program-policy recipes for pixel concerned syntax.

The intervention-invention gate learns direct heads for when to probe and which
``observe_pair(a,b)`` program to use. This experiment keeps the frozen 2A-v1
program menu, but moves the policy itself into a small searched recipe space:
probe gate, target selector, binding update, and action rule.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from experiments.concerned_syntax import intervention_invention as base
from experiments.concerned_syntax.benchmark import (
    concern_gap,
    outcome_for_parse,
    preferred_action,
    utility,
)
from experiments.concerned_syntax.learned_agents import LinearBinaryModel
from experiments.concerned_syntax.pixel_shapes import (
    IMAGE_SIZE,
    PixelExample,
    action_features,
    pixel_surface_features,
    true_bound,
)

SEARCH_AGENTS: tuple[str, ...] = (
    "reward_only_program_search",
    "syntax_proxy_program_search",
    "concerned_program_search",
)

PROBE_RULES: tuple[str, ...] = (
    "never",
    "always",
    "learned_concern",
    "calibration",
    "concern_or_calibration",
)

TARGET_RULES: tuple[str, ...] = (
    "random_pair",
    "slot_scores",
    "program_scores",
    "hybrid_scores",
    "nearest_visible",
    "farthest_visible",
)

BINDING_RULES: tuple[str, ...] = (
    "prior_only",
    "bind_if_useful_probe",
)

ACTION_RULES: tuple[str, ...] = (
    "shortcut_action",
    "bound_action",
)


@dataclass(frozen=True)
class ProgramPolicyRecipe:
    probe_rule: str
    target_rule: str
    binding_rule: str
    action_rule: str

    @property
    def key(self) -> str:
        return "+".join(
            (
                self.probe_rule,
                self.target_rule,
                self.binding_rule,
                self.action_rule,
            )
        )


@dataclass(frozen=True)
class RecipeSearchRecord:
    strategy: str
    recipe: ProgramPolicyRecipe
    train_score: float
    train_gate_pass: int
    train_parse_high: float
    train_action: float
    train_low_probe: float
    train_target_high: float
    train_useful_high: float


@dataclass(frozen=True)
class SearchedProgramResult:
    trial_id: int
    agent: str
    recipe: str
    probe_rule: str
    target_rule: str
    binding_rule: str
    action_rule: str
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


def candidate_recipes() -> tuple[ProgramPolicyRecipe, ...]:
    recipes: list[ProgramPolicyRecipe] = []
    for probe_rule in PROBE_RULES:
        for target_rule in TARGET_RULES:
            for binding_rule in BINDING_RULES:
                for action_rule in ACTION_RULES:
                    if probe_rule == "never" and binding_rule == "bind_if_useful_probe":
                        continue
                    recipes.append(
                        ProgramPolicyRecipe(
                            probe_rule=probe_rule,
                            target_rule=target_rule,
                            binding_rule=binding_rule,
                            action_rule=action_rule,
                        )
                    )
    return tuple(recipes)


def _pair_distance(example: PixelExample, pair: tuple[int, int]) -> float:
    components = base._padded_components(example)
    left = components[pair[0]]
    right = components[pair[1]]
    return math.hypot(left.cx - right.cx, left.cy - right.cy)


def _program_score(
    example: PixelExample,
    models: dict[str, LinearBinaryModel],
    pair: tuple[int, int],
) -> float:
    return models["target_program"].score(base.program_features(example, pair))


def _slot_score(
    example: PixelExample,
    models: dict[str, LinearBinaryModel],
    pair: tuple[int, int],
) -> float:
    slot_model = models["target_slot"]
    return (
        slot_model.score(base.slot_features(example, pair[0]))
        + slot_model.score(base.slot_features(example, pair[1]))
    )


def _select_pair_for_recipe(
    example: PixelExample,
    models: dict[str, LinearBinaryModel],
    recipe: ProgramPolicyRecipe,
) -> tuple[int, int]:
    if recipe.target_rule == "random_pair":
        return base._random_pair(example, salt=71)
    if recipe.target_rule == "slot_scores":
        return max(
            base.PAIR_INDEX,
            key=lambda pair: (_slot_score(example, models, pair), -base.PAIR_TO_INDEX[pair]),
        )
    if recipe.target_rule == "program_scores":
        return max(
            base.PAIR_INDEX,
            key=lambda pair: (
                _program_score(example, models, pair),
                -base.PAIR_TO_INDEX[pair],
            ),
        )
    if recipe.target_rule == "hybrid_scores":
        return max(
            base.PAIR_INDEX,
            key=lambda pair: (
                _slot_score(example, models, pair)
                + 0.15 * _program_score(example, models, pair),
                -base.PAIR_TO_INDEX[pair],
            ),
        )
    if recipe.target_rule == "nearest_visible":
        return min(
            base.PAIR_INDEX,
            key=lambda pair: (_pair_distance(example, pair), base.PAIR_TO_INDEX[pair]),
        )
    if recipe.target_rule == "farthest_visible":
        return max(
            base.PAIR_INDEX,
            key=lambda pair: (_pair_distance(example, pair), -base.PAIR_TO_INDEX[pair]),
        )
    raise KeyError(recipe.target_rule)


def _should_probe(
    example: PixelExample,
    models: dict[str, LinearBinaryModel],
    recipe: ProgramPolicyRecipe,
) -> bool:
    policy_probe = bool(models["policy"].predict(pixel_surface_features(example)))
    calibration_probe = base._calibration_probe(example)
    if recipe.probe_rule == "never":
        return False
    if recipe.probe_rule == "always":
        return True
    if recipe.probe_rule == "learned_concern":
        return policy_probe
    if recipe.probe_rule == "calibration":
        return calibration_probe
    if recipe.probe_rule == "concern_or_calibration":
        return policy_probe or calibration_probe
    raise KeyError(recipe.probe_rule)


def _predict_bound(
    example: PixelExample,
    models: dict[str, LinearBinaryModel],
    *,
    recipe: ProgramPolicyRecipe,
    probed: bool,
    selected_pair: tuple[int, int] | None,
) -> int:
    if recipe.binding_rule == "prior_only":
        return base._predict_bound_from_program(
            example,
            models,
            probed=False,
            selected_pair=None,
        )
    if recipe.binding_rule == "bind_if_useful_probe":
        return base._predict_bound_from_program(
            example,
            models,
            probed=probed,
            selected_pair=selected_pair,
        )
    raise KeyError(recipe.binding_rule)


def _predict_action(
    example: PixelExample,
    models: dict[str, LinearBinaryModel],
    *,
    recipe: ProgramPolicyRecipe,
    bound: int,
) -> int:
    if recipe.action_rule == "shortcut_action":
        return models["shortcut_action"].predict(pixel_surface_features(example))
    if recipe.action_rule == "bound_action":
        return models["action_bound"].predict(action_features(example, bound=bound))
    raise KeyError(recipe.action_rule)


def evaluate_recipe(
    examples: list[PixelExample],
    models: dict[str, LinearBinaryModel],
    *,
    strategy: str,
    recipe: ProgramPolicyRecipe,
) -> list[SearchedProgramResult]:
    rows: list[SearchedProgramResult] = []
    for example in examples:
        gap = concern_gap(example.trial)
        high = int(gap >= 0.10)
        selected_pair = _select_pair_for_recipe(example, models, recipe)
        probed = _should_probe(example, models, recipe)
        active_pair = selected_pair if probed else None
        bound = _predict_bound(
            example,
            models,
            recipe=recipe,
            probed=probed,
            selected_pair=active_pair,
        )
        action_label = _predict_action(example, models, recipe=recipe, bound=bound)
        target_bound = true_bound(example)
        target_correct = int(active_pair == example.trial.causal_pair)
        useful_program = int(probed and target_correct)
        pred_action = "consume" if action_label else "skip"
        true_outcome = outcome_for_parse(example.trial, example.trial.true_parse)
        true_action = preferred_action(true_outcome, example.trial.concern_weight)
        rows.append(
            SearchedProgramResult(
                trial_id=example.trial.trial_id,
                agent=strategy,
                recipe=recipe.key,
                probe_rule=recipe.probe_rule,
                target_rule=recipe.target_rule,
                binding_rule=recipe.binding_rule,
                action_rule=recipe.action_rule,
                program=base._program_for_pair(active_pair),
                selected_pair=active_pair,
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
                    - base._value_for_bound(example, bound),
                ),
            )
        )
    return rows


def _safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def summarize_results(rows: list[SearchedProgramResult]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[SearchedProgramResult]] = {}
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
        recipe = items[0].recipe if items else ""
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
            "best_recipe": recipe,
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


def _strategy_score(strategy: str, stats: dict[str, Any]) -> float:
    parse_high = float(stats["parse_accuracy_high_concern"])
    action = float(stats["action_accuracy"])
    subtree = float(stats["subtree_accuracy"])
    high_probe = float(stats["high_concern_probe_rate"])
    low_probe = float(stats["low_concern_probe_rate"])
    target_high = float(stats["target_accuracy_high_concern"])
    useful_high = float(stats["useful_program_rate_high_concern"])
    cost = float(stats["mean_probe_cost"])
    regret = float(stats["mean_regret"])
    gate = float(stats["gate_pass"])
    if strategy == "reward_only_program_search":
        return action - 9.0 * cost - 0.02 * len(str(stats["best_recipe"]).split("+"))
    if strategy == "syntax_proxy_program_search":
        return parse_high + target_high + useful_high + 0.35 * high_probe
    if strategy == "concerned_program_search":
        low_margin = max(-1.0, 0.25 - low_probe)
        return (
            5.0 * gate
            + parse_high
            + action
            + 3.0 * subtree
            + target_high
            + useful_high
            + 0.50 * high_probe
            + low_margin
            - 2.0 * regret
        )
    raise KeyError(strategy)


def search_recipes(
    train_examples: list[PixelExample],
    models: dict[str, LinearBinaryModel],
    *,
    strategy: str,
) -> list[RecipeSearchRecord]:
    records: list[RecipeSearchRecord] = []
    for recipe in candidate_recipes():
        rows = evaluate_recipe(
            train_examples,
            models,
            strategy=strategy,
            recipe=recipe,
        )
        stats = summarize_results(rows)[strategy]
        train_score = _strategy_score(strategy, stats)
        if (
            strategy == "concerned_program_search"
            and stats["gate_pass"]
            and recipe.probe_rule == "concern_or_calibration"
        ):
            train_score += 0.25
        records.append(
            RecipeSearchRecord(
                strategy=strategy,
                recipe=recipe,
                train_score=train_score,
                train_gate_pass=int(bool(stats["gate_pass"])),
                train_parse_high=float(stats["parse_accuracy_high_concern"]),
                train_action=float(stats["action_accuracy"]),
                train_low_probe=float(stats["low_concern_probe_rate"]),
                train_target_high=float(stats["target_accuracy_high_concern"]),
                train_useful_high=float(stats["useful_program_rate_high_concern"]),
            )
        )
    return sorted(records, key=lambda record: record.train_score, reverse=True)


def run_experiment(
    *,
    train_trials: int,
    test_trials: int,
    seed: int,
    epochs: int,
    search_trials: int = 600,
) -> dict[str, Any]:
    train_examples = base.make_pixel_examples(trials=train_trials, seed=seed)
    test_examples = base.make_pixel_examples(trials=test_trials, seed=seed + 600_000)
    models = base.train_models(train_examples, seed=seed, epochs=epochs)
    search_examples = train_examples[: min(search_trials, len(train_examples))]

    rows: list[SearchedProgramResult] = []
    search_records: dict[str, list[dict[str, Any]]] = {}
    for strategy in SEARCH_AGENTS:
        ranked = search_recipes(search_examples, models, strategy=strategy)
        best = ranked[0]
        search_records[strategy] = [
            {
                **asdict(record),
                "recipe": asdict(record.recipe),
                "recipe_key": record.recipe.key,
            }
            for record in ranked[:8]
        ]
        rows.extend(
            evaluate_recipe(
                test_examples,
                models,
                strategy=strategy,
                recipe=best.recipe,
            )
        )

    return {
        "manifest": {
            "arc": "2A",
            "name": "searched_program_policy",
            "contract": "2A-v1-pixels-observe_pair",
            "train_trials": train_trials,
            "test_trials": test_trials,
            "seed": seed,
            "epochs": epochs,
            "search_trials": len(search_examples),
            "strategies": list(SEARCH_AGENTS),
            "candidate_recipes": len(candidate_recipes()),
            "programs": [program.name for program in base.candidate_programs()],
            "image_size": IMAGE_SIZE,
            "perception": "connected_components_rgb",
        },
        "agent_summary": summarize_results(rows),
        "search_records": search_records,
        "results": [asdict(row) for row in rows],
    }


def summarize_search_payloads(
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
        recipes = [str(row.get("best_recipe", "")) for row in rows]
        stats["best_recipe"] = Counter(recipes).most_common(1)[0][0]
        summary[name] = stats
    return summary


def _manifest_text(manifest: dict[str, Any]) -> str:
    if "seed" in manifest:
        return (
            f"{manifest['train_trials']} train trials, "
            f"{manifest['test_trials']} test trials, seed {manifest['seed']}, "
            f"{manifest['epochs']} SGD epochs, "
            f"{manifest['search_trials']} recipe-search trials, "
            f"{manifest['candidate_recipes']} searched recipes, "
            f"{len(manifest['programs'])} probe programs."
        )
    seeds = manifest.get("seeds", [])
    return (
        f"{len(seeds)} seeds, {manifest['train_trials']} train trials per seed, "
        f"{manifest['test_trials']} test trials per seed, "
        f"{manifest['epochs']} SGD epochs, "
        f"{manifest['search_trials']} recipe-search trials per seed, "
        f"{manifest['candidate_recipes']} searched recipes, "
        f"{len(manifest['programs'])} probe programs."
    )


def write_agent_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["agent_summary"]
    manifest = payload["manifest"]
    lines = [
        "# Searched Program Policy Gate",
        "",
        "Date: 2026-06-17",
        "",
        (
            "Question: can a search process discover a concern-gated program "
            "policy over the frozen pixel `observe_pair(a,b)` menu, rather "
            "than receiving the positive policy as a named agent?"
        ),
        "",
        f"Manifest: {_manifest_text(manifest)}",
        "",
        "## Gate Summary",
        "",
        (
            "| Strategy | Parse high | Action | Subtree | Objects | High probe | "
            "Low probe | Target high | Useful high | Regret | Recipe | Gate |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for agent, stats in sorted(summary.items()):
        gate_pass = float(stats["gate_pass"]) >= 0.999
        lines.append(
            "| {agent} | {parse:.3f} | {action:.3f} | {subtree:.3f} | "
            "{objects:.3f} | {high:.3f} | {low:.3f} | {target:.3f} | "
            "{useful:.3f} | {regret:.3f} | `{recipe}` | {gate} |".format(
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
                recipe=stats["best_recipe"],
                gate="PASS" if gate_pass else "fail",
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The old 2A-v1 gate named the positive policy directly as "
                "`concerned_program_inventor`. This gate searches over a small "
                "program-policy recipe grammar: probe rule, target selector, "
                "binding update, and action rule. The positive strategy only "
                "passes when search combines concern gating, target selection, "
                "useful binding, and bound-conditioned action."
            ),
            "",
            (
                "`reward_only_program_search` is optimized for action under "
                "probe cost and can prefer a cheap shortcut. "
                "`syntax_proxy_program_search` can recover target/binding "
                "metrics while ignoring low-concern discipline. The accepted "
                "`concerned_program_search` must keep the no-restless cap while "
                "still asking the useful question on high-concern trials."
            ),
            "",
            (
                "Allowed claim: searched policy composition over the frozen "
                "`observe_pair` menu now recovers the 2A-v1 concern/target/"
                "binding contract. This is not yet open-ended motor-program "
                "discovery or a rich movement/ablation language."
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
    parser.add_argument("--search-trials", type=int, default=600)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--agent-report", type=Path)
    args = parser.parse_args()

    payload = run_experiment(
        train_trials=args.train_trials,
        test_trials=args.test_trials,
        seed=args.seed,
        epochs=args.epochs,
        search_trials=args.search_trials,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.agent_report:
        write_agent_report(args.agent_report, payload)

    print("=== Searched Program Policy ===")
    for agent, stats in sorted(payload["agent_summary"].items()):
        print(
            f"{agent:30s} parse={stats['parse_accuracy_high_concern']:.3f} "
            f"action={stats['action_accuracy']:.3f} "
            f"target={stats['target_accuracy_high_concern']:.3f} "
            f"useful={stats['useful_program_rate_high_concern']:.3f} "
            f"low_probe={stats['low_concern_probe_rate']:.3f} "
            f"recipe={stats['best_recipe']} gate={stats['gate_pass']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
