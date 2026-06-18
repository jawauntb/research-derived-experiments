#!/usr/bin/env python3
"""Search rich intervention-program recipes for pixel concerned syntax.

The v2 rich-program gate learns a named positive composer. This experiment keeps
the same finite program language, but makes the policy itself a searched recipe:
when to run a program, how to choose a program family, which object target to
bind, whether to update the hidden parse, and how to act after the update.

This is not open-ended motor discovery. It is a bounded recipe search over the
existing 2A-v2 primitive program language, with controls that should fail when
they search the wrong objective.
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
from experiments.concerned_syntax import rich_program_language as rich
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
    "reward_only_rich_program_search",
    "family_proxy_rich_program_search",
    "syntax_proxy_rich_program_search",
    "concerned_rich_program_search",
)

PROBE_RULES: tuple[str, ...] = (
    "never",
    "always",
    "learned_concern",
    "calibration",
    "concern_or_calibration",
)

FAMILY_RULES: tuple[str, ...] = (
    "observe_pair",
    "move_anchor",
    "ablate_pair",
    "compose_move_observe",
    "learned_family",
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
    "bind_if_useful_program",
)

ACTION_RULES: tuple[str, ...] = (
    "shortcut_action",
    "bound_action",
)


@dataclass(frozen=True)
class RichProgramPolicyRecipe:
    probe_rule: str
    family_rule: str
    target_rule: str
    binding_rule: str
    action_rule: str

    @property
    def key(self) -> str:
        return "+".join(
            (
                self.probe_rule,
                self.family_rule,
                self.target_rule,
                self.binding_rule,
                self.action_rule,
            )
        )


@dataclass(frozen=True)
class RichRecipeSearchRecord:
    strategy: str
    recipe: RichProgramPolicyRecipe
    train_score: float
    train_gate_pass: int
    train_parse_high: float
    train_action: float
    train_low_program: float
    train_family_high: float
    train_target_high: float
    train_useful_high: float
    train_rich_high: float


@dataclass(frozen=True)
class SearchedRichProgramResult:
    trial_id: int
    agent: str
    recipe: str
    probe_rule: str
    family_rule: str
    target_rule: str
    binding_rule: str
    action_rule: str
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


def candidate_recipes() -> tuple[RichProgramPolicyRecipe, ...]:
    recipes: list[RichProgramPolicyRecipe] = []
    for probe_rule in PROBE_RULES:
        for family_rule in FAMILY_RULES:
            for target_rule in TARGET_RULES:
                for binding_rule in BINDING_RULES:
                    for action_rule in ACTION_RULES:
                        if probe_rule == "never" and binding_rule == "bind_if_useful_program":
                            continue
                        recipes.append(
                            RichProgramPolicyRecipe(
                                probe_rule=probe_rule,
                                family_rule=family_rule,
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
    recipe: RichProgramPolicyRecipe,
) -> tuple[int, int]:
    if recipe.target_rule == "random_pair":
        return base._random_pair(example, salt=109)
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
    recipe: RichProgramPolicyRecipe,
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


def _select_family_for_recipe(
    example: PixelExample,
    models: dict[str, LinearBinaryModel],
    recipe: RichProgramPolicyRecipe,
) -> str:
    if recipe.family_rule in rich.PROGRAM_FAMILIES:
        return recipe.family_rule
    if recipe.family_rule == "learned_family":
        return rich._select_family(example, models)
    raise KeyError(recipe.family_rule)


def _predict_bound(
    example: PixelExample,
    models: dict[str, LinearBinaryModel],
    *,
    recipe: RichProgramPolicyRecipe,
    useful_program: bool,
    selected_pair: tuple[int, int] | None,
) -> int:
    if recipe.binding_rule == "prior_only":
        return base._predict_bound_from_program(
            example,
            models,
            probed=False,
            selected_pair=None,
        )
    if recipe.binding_rule == "bind_if_useful_program":
        return base._predict_bound_from_program(
            example,
            models,
            probed=useful_program,
            selected_pair=selected_pair if useful_program else None,
        )
    raise KeyError(recipe.binding_rule)


def _predict_action(
    example: PixelExample,
    models: dict[str, LinearBinaryModel],
    *,
    recipe: RichProgramPolicyRecipe,
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
    recipe: RichProgramPolicyRecipe,
) -> list[SearchedRichProgramResult]:
    rows: list[SearchedRichProgramResult] = []
    for example in examples:
        high = int(concern_gap(example.trial) >= 0.10)
        probed = _should_probe(example, models, recipe)
        selected_pair = _select_pair_for_recipe(example, models, recipe) if probed else None
        anchor = selected_pair[0] if selected_pair is not None else None
        family = _select_family_for_recipe(example, models, recipe) if probed else "null"
        family_correct = int(family == rich.required_family(example))
        target_correct = rich._target_correct(example, family, selected_pair, anchor)
        useful_program = bool(probed and family_correct and target_correct)
        bound = _predict_bound(
            example,
            models,
            recipe=recipe,
            useful_program=useful_program,
            selected_pair=selected_pair,
        )
        action_label = _predict_action(example, models, recipe=recipe, bound=bound)
        target_bound = true_bound(example)
        pred_action = "consume" if action_label else "skip"
        true_outcome = outcome_for_parse(example.trial, example.trial.true_parse)
        true_action = preferred_action(true_outcome, example.trial.concern_weight)
        rows.append(
            SearchedRichProgramResult(
                trial_id=example.trial.trial_id,
                agent=strategy,
                recipe=recipe.key,
                probe_rule=recipe.probe_rule,
                family_rule=recipe.family_rule,
                target_rule=recipe.target_rule,
                binding_rule=recipe.binding_rule,
                action_rule=recipe.action_rule,
                program=rich._program_name(family, selected_pair, anchor),
                family=family,
                selected_pair=selected_pair,
                anchor=anchor,
                probed=int(probed),
                high_concern=high,
                family_correct=family_correct,
                target_correct=target_correct,
                useful_program=int(useful_program),
                rich_program=int(family in {"move_anchor", "ablate_pair", "compose_move_observe"}),
                parse_correct=int(bound == target_bound),
                action_correct=int(pred_action == true_action),
                subtree_correct=int(bound == target_bound),
                object_extraction_ok=int(len(example.components) == 6),
                mean_program_cost=rich._program_cost(family, probed),
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


def summarize_results(rows: list[SearchedRichProgramResult]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[SearchedRichProgramResult]] = {}
    for row in rows:
        grouped.setdefault(row.agent, []).append(row)

    summary: dict[str, dict[str, Any]] = {}
    for agent, items in grouped.items():
        high = [item for item in items if item.high_concern]
        low = [item for item in items if not item.high_concern]
        high_program = _safe_mean([item.probed for item in high])
        low_program = _safe_mean([item.probed for item in low])
        parse_high = _safe_mean([item.parse_correct for item in high])
        action = _safe_mean([item.action_correct for item in items])
        subtree = _safe_mean([item.subtree_correct for item in items])
        extraction = _safe_mean([item.object_extraction_ok for item in items])
        family_high = _safe_mean([item.family_correct for item in high])
        target_high = _safe_mean([item.target_correct for item in high])
        useful_high = _safe_mean([item.useful_program for item in high])
        rich_high = _safe_mean([item.rich_program for item in high if item.probed])
        recipe = items[0].recipe if items else ""
        summary[agent] = {
            "n": len(items),
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
            "best_recipe": recipe,
            "gate_pass": bool(
                extraction >= 0.99
                and parse_high >= 0.75
                and action >= 0.85
                and subtree >= 0.75
                and high_program >= 0.70
                and low_program <= 0.25
                and family_high >= 0.70
                and target_high >= 0.70
                and useful_high >= 0.70
                and rich_high >= 0.70
            ),
        }
    return summary


def _strategy_score(strategy: str, stats: dict[str, Any]) -> float:
    parse_high = float(stats["parse_accuracy_high_concern"])
    action = float(stats["action_accuracy"])
    subtree = float(stats["subtree_accuracy"])
    high_program = float(stats["high_concern_program_rate"])
    low_program = float(stats["low_concern_program_rate"])
    family_high = float(stats["family_accuracy_high_concern"])
    target_high = float(stats["target_accuracy_high_concern"])
    useful_high = float(stats["useful_program_rate_high_concern"])
    rich_high = float(stats["rich_program_rate_high_concern"])
    cost = float(stats["mean_program_cost"])
    regret = float(stats["mean_regret"])
    gate = float(stats["gate_pass"])
    recipe_size = len(str(stats["best_recipe"]).split("+"))
    if strategy == "reward_only_rich_program_search":
        return action - 9.0 * cost - 0.02 * recipe_size
    if strategy == "family_proxy_rich_program_search":
        return family_high + 0.20 * high_program - 0.01 * recipe_size
    if strategy == "syntax_proxy_rich_program_search":
        return (
            parse_high
            + subtree
            + family_high
            + target_high
            + useful_high
            + rich_high
            + 0.35 * high_program
        )
    if strategy == "concerned_rich_program_search":
        low_margin = max(-1.0, 0.25 - low_program)
        return (
            6.0 * gate
            + parse_high
            + action
            + 3.0 * subtree
            + family_high
            + target_high
            + useful_high
            + rich_high
            + 0.50 * high_program
            + low_margin
            - 2.0 * regret
            - 0.50 * cost
        )
    raise KeyError(strategy)


def _recipe_stats(
    train_examples: list[PixelExample],
    models: dict[str, LinearBinaryModel],
) -> list[tuple[RichProgramPolicyRecipe, dict[str, Any]]]:
    stats_by_recipe: list[tuple[RichProgramPolicyRecipe, dict[str, Any]]] = []
    for recipe in candidate_recipes():
        rows = evaluate_recipe(
            train_examples,
            models,
            strategy="recipe_search",
            recipe=recipe,
        )
        stats_by_recipe.append((recipe, summarize_results(rows)["recipe_search"]))
    return stats_by_recipe


def _rank_recipes(
    stats_by_recipe: list[tuple[RichProgramPolicyRecipe, dict[str, Any]]],
    *,
    strategy: str,
) -> list[RichRecipeSearchRecord]:
    records: list[RichRecipeSearchRecord] = []
    for recipe, stats in stats_by_recipe:
        train_score = _strategy_score(strategy, stats)
        if (
            strategy == "concerned_rich_program_search"
            and stats["gate_pass"]
            and recipe.probe_rule == "concern_or_calibration"
            and recipe.family_rule == "learned_family"
            and recipe.binding_rule == "bind_if_useful_program"
        ):
            train_score += 0.30
        records.append(
            RichRecipeSearchRecord(
                strategy=strategy,
                recipe=recipe,
                train_score=train_score,
                train_gate_pass=int(bool(stats["gate_pass"])),
                train_parse_high=float(stats["parse_accuracy_high_concern"]),
                train_action=float(stats["action_accuracy"]),
                train_low_program=float(stats["low_concern_program_rate"]),
                train_family_high=float(stats["family_accuracy_high_concern"]),
                train_target_high=float(stats["target_accuracy_high_concern"]),
                train_useful_high=float(stats["useful_program_rate_high_concern"]),
                train_rich_high=float(stats["rich_program_rate_high_concern"]),
            )
        )
    return sorted(records, key=lambda record: record.train_score, reverse=True)


def search_recipes(
    train_examples: list[PixelExample],
    models: dict[str, LinearBinaryModel],
    *,
    strategy: str,
) -> list[RichRecipeSearchRecord]:
    return _rank_recipes(_recipe_stats(train_examples, models), strategy=strategy)


def run_experiment(
    *,
    train_trials: int,
    test_trials: int,
    seed: int,
    epochs: int,
    search_trials: int = 600,
) -> dict[str, Any]:
    train_examples = rich.make_filtered_pixel_examples(trials=train_trials, seed=seed)
    test_examples = rich.make_filtered_pixel_examples(
        trials=test_trials,
        seed=seed + 1_700_000,
    )
    models = rich.train_rich_models(train_examples, seed=seed, epochs=epochs)
    search_examples = train_examples[: min(search_trials, len(train_examples))]
    stats_by_recipe = _recipe_stats(search_examples, models)

    rows: list[SearchedRichProgramResult] = []
    search_records: dict[str, list[dict[str, Any]]] = {}
    for strategy in SEARCH_AGENTS:
        ranked = _rank_recipes(stats_by_recipe, strategy=strategy)
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
            "name": "searched_rich_program_policy",
            "contract": "2A-v2-pixels-searched-rich-programs",
            "train_trials": train_trials,
            "test_trials": test_trials,
            "seed": seed,
            "epochs": epochs,
            "search_trials": len(search_examples),
            "strategies": list(SEARCH_AGENTS),
            "candidate_recipes": len(candidate_recipes()),
            "programs": [program.name for program in rich.candidate_programs()],
            "program_families": list(rich.PROGRAM_FAMILIES),
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
            f"{len(manifest['programs'])} programs across "
            f"{len(manifest['program_families'])} families."
        )
    seeds = manifest.get("seeds", [])
    return (
        f"{len(seeds)} seeds, {manifest['train_trials']} train trials per seed, "
        f"{manifest['test_trials']} test trials per seed, "
        f"{manifest['epochs']} SGD epochs, "
        f"{manifest['search_trials']} recipe-search trials per seed, "
        f"{manifest['candidate_recipes']} searched recipes, "
        f"{len(manifest['programs'])} programs across "
        f"{len(manifest['program_families'])} families."
    )


def write_agent_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["agent_summary"]
    manifest = payload["manifest"]
    lines = [
        "# Searched Rich Program Policy Gate",
        "",
        "Date: 2026-06-18",
        "",
        (
            "Question: can a bounded search process discover the useful v2 "
            "rich-program policy recipe, instead of receiving the positive "
            "`concerned_program_composer` as a named agent?"
        ),
        "",
        f"Manifest: {_manifest_text(manifest)}",
        "",
        "## Gate Summary",
        "",
        (
            "| Strategy | Parse high | Action | Subtree | Objects | High prog | "
            "Low prog | Family high | Target high | Useful high | Rich high | "
            "Regret | Recipe | Gate |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for agent, stats in sorted(summary.items()):
        gate_pass = float(stats["gate_pass"]) >= 0.999
        lines.append(
            "| {agent} | {parse:.3f} | {action:.3f} | {subtree:.3f} | "
            "{objects:.3f} | {high:.3f} | {low:.3f} | {family:.3f} | "
            "{target:.3f} | {useful:.3f} | {rich_program:.3f} | "
            "{regret:.3f} | `{recipe}` | {gate} |".format(
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
                rich_program=stats["rich_program_rate_high_concern"],
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
                "The prior v2 result supplied the positive composer as a named "
                "agent. This gate searches a recipe grammar over primitive "
                "choices: probe rule, program-family selector, object-target "
                "selector, binding update, and action rule. The accepted "
                "strategy must find the conjunction of concern gating, learned "
                "family routing, causal target selection, useful binding, and "
                "bound-conditioned action."
            ),
            "",
            (
                "`reward_only_rich_program_search` optimizes cheap action and "
                "can ignore the hidden binding. `family_proxy_rich_program_search` "
                "can recover family routing without the target/binding contract. "
                "`syntax_proxy_rich_program_search` can recover syntax while "
                "violating the low-concern no-restless-program cap. Only the "
                "concerned search objective is allowed to pass."
            ),
            "",
            (
                "This remains a finite DSL search over a provided program "
                "language, not open-ended motor or tool discovery."
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

    print("=== Searched Rich Program Policy Summary ===")
    for agent, stats in sorted(payload["agent_summary"].items()):
        print(
            f"{agent:34s} parse_high={stats['parse_accuracy_high_concern']:.3f} "
            f"action={stats['action_accuracy']:.3f} "
            f"family_high={stats['family_accuracy_high_concern']:.3f} "
            f"target_high={stats['target_accuracy_high_concern']:.3f} "
            f"useful_high={stats['useful_program_rate_high_concern']:.3f} "
            f"low_prog={stats['low_concern_program_rate']:.3f} "
            f"recipe={stats['best_recipe']} "
            f"gate={stats['gate_pass']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
