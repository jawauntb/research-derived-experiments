#!/usr/bin/env python3
"""Search executable module bodies against the label-free 2A-v2 contract.

The previous executable-body gate used compact hand-instantiated bodies over
the repaired 2A-v2 transfer contract. This module adds a bounded body search:
candidate executable module sets are mutated, repaired, promoted, and selected
against the newest label-free slot-semantics transfer gate. The result is still
not full neural architecture search; it is searched executable body contracts
over the provided synthetic rich-program world.
"""

from __future__ import annotations

import argparse
import json
import random
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, cast

from experiments.concerned_syntax.unsupervised_slot_semantics import run_experiment

REQUIRED_SEARCHED_EXECUTABLE_MODULES: frozenset[str] = frozenset(
    {
        "component_slot_encoder",
        "label_free_slot_inducer",
        "semantic_profile_grounder",
        "concern_gate",
        "target_binder",
        "program_family_router",
        "rich_program_composer",
        "world_model",
        "formal_guard",
    }
)

EXECUTABLE_MODULE_CATALOG: tuple[str, ...] = (
    "component_slot_encoder",
    "label_free_slot_inducer",
    "semantic_profile_grounder",
    "concern_gate",
    "target_binder",
    "program_family_router",
    "rich_program_composer",
    "world_model",
    "formal_guard",
    "action_head",
    "reward_head",
    "surface_shortcut_head",
    "learned_composer_head",
    "family_proxy_head",
    "target_proxy_head",
    "ungated_program_executor",
    "profile_memory",
)

EXECUTABLE_MODULE_COST: dict[str, int] = {
    "component_slot_encoder": 2,
    "label_free_slot_inducer": 3,
    "semantic_profile_grounder": 2,
    "concern_gate": 1,
    "target_binder": 2,
    "program_family_router": 2,
    "rich_program_composer": 2,
    "world_model": 2,
    "formal_guard": 1,
    "action_head": 1,
    "reward_head": 1,
    "surface_shortcut_head": 1,
    "learned_composer_head": 2,
    "family_proxy_head": 1,
    "target_proxy_head": 1,
    "ungated_program_executor": 1,
    "profile_memory": 1,
}

EXECUTABLE_MODULE_DEPENDENCIES: dict[str, set[str]] = {
    "label_free_slot_inducer": {"component_slot_encoder"},
    "semantic_profile_grounder": {"label_free_slot_inducer"},
    "concern_gate": {"semantic_profile_grounder"},
    "target_binder": {"semantic_profile_grounder", "world_model"},
    "program_family_router": {"semantic_profile_grounder"},
    "rich_program_composer": {"program_family_router", "world_model"},
    "action_head": {"target_binder", "world_model"},
    "family_proxy_head": {"program_family_router"},
    "target_proxy_head": {"target_binder"},
    "ungated_program_executor": {"rich_program_composer"},
    "profile_memory": {"semantic_profile_grounder"},
}

TARGET_SEARCHED_EXECUTABLE_BODY: frozenset[str] = frozenset(
    {
        "component_slot_encoder",
        "label_free_slot_inducer",
        "semantic_profile_grounder",
        "concern_gate",
        "target_binder",
        "program_family_router",
        "rich_program_composer",
        "world_model",
        "formal_guard",
        "action_head",
        "reward_head",
        "profile_memory",
    }
)

UNGATED_RICH_EXECUTABLE_BODY: frozenset[str] = frozenset(
    {
        "component_slot_encoder",
        "label_free_slot_inducer",
        "semantic_profile_grounder",
        "target_binder",
        "program_family_router",
        "rich_program_composer",
        "world_model",
        "action_head",
        "reward_head",
        "ungated_program_executor",
        "profile_memory",
    }
)

SEARCHED_EXECUTABLE_STRATEGIES: tuple[str, ...] = (
    "reward_only",
    "family_proxy",
    "target_proxy",
    "ungated_rich_proxy",
    "viability_guided",
)

MAX_SEARCHED_EXECUTABLE_RESOURCE = 21


@dataclass(frozen=True)
class SearchedExecutableSpec:
    modules: frozenset[str]

    @property
    def key(self) -> str:
        return "+".join(sorted(self.modules))


@dataclass(frozen=True)
class ExecutableModuleVerdict:
    formal_valid: bool
    resource_cost: int
    violations: tuple[str, ...]
    formal_source: str = "python_static"


@dataclass(frozen=True)
class SearchedExecutableEvaluation:
    architecture: str
    strategy: str
    seed: int
    generation: int
    empirical_agent: str
    train_return: float
    semantic_kind_accuracy: float
    semantic_family_accuracy: float
    semantic_pair_accuracy: float
    transfer_gate_pass: int
    parse_accuracy_high_concern: float
    action_accuracy: float
    family_accuracy_high_concern: float
    target_accuracy_high_concern: float
    useful_program_rate_high_concern: float
    rich_program_rate_high_concern: float
    low_concern_program_rate: float
    module_coverage: float
    formal_valid: int
    formal_source: str
    resource_cost: int
    executable_module_gate: int
    missing_modules: tuple[str, ...]
    violations: tuple[str, ...]


def searched_executable_resource_cost(spec: SearchedExecutableSpec) -> int:
    return sum(EXECUTABLE_MODULE_COST[module] for module in spec.modules)


def searched_executable_violations(spec: SearchedExecutableSpec) -> tuple[str, ...]:
    modules = spec.modules
    violations: list[str] = []
    for module, deps in EXECUTABLE_MODULE_DEPENDENCIES.items():
        if module in modules:
            missing = sorted(deps - modules)
            if missing:
                violations.append(f"{module}_missing_{'+'.join(missing)}")
    if "concern_gate" in modules and "formal_guard" not in modules:
        violations.append("concern_without_formal_guard")
    if "surface_shortcut_head" in modules and "formal_guard" not in modules:
        violations.append("shortcut_without_formal_guard")
    if "rich_program_composer" in modules and "program_family_router" not in modules:
        violations.append("composer_without_family_router")
    if "target_binder" in modules and "semantic_profile_grounder" not in modules:
        violations.append("target_without_label_free_semantics")
    if searched_executable_resource_cost(spec) > MAX_SEARCHED_EXECUTABLE_RESOURCE:
        violations.append("searched_executable_resource_over_budget")
    if "component_slot_encoder" not in modules:
        violations.append("missing_component_slots")
    return tuple(violations)


def python_static_executable_verdict(spec: SearchedExecutableSpec) -> ExecutableModuleVerdict:
    violations = searched_executable_violations(spec)
    return ExecutableModuleVerdict(
        formal_valid=not violations,
        resource_cost=searched_executable_resource_cost(spec),
        violations=violations,
    )


def _has(spec: SearchedExecutableSpec, *modules: str) -> bool:
    return all(module in spec.modules for module in modules)


def empirical_agent_for_searched_executable(spec: SearchedExecutableSpec) -> str:
    """Map executable modules to the label-free 2A-v2 agent they can express."""

    has_semantics = _has(
        spec,
        "component_slot_encoder",
        "label_free_slot_inducer",
        "semantic_profile_grounder",
    )
    has_concern = _has(spec, "concern_gate", "formal_guard")
    has_target = has_semantics and _has(spec, "target_binder", "world_model")
    has_family = has_semantics and _has(spec, "program_family_router")
    has_composer = _has(spec, "rich_program_composer", "program_family_router")

    if has_semantics and has_concern and has_target and has_family and has_composer:
        return "unsupervised_slot_semantic_world_model"
    if has_semantics and has_target and has_family and has_composer:
        return "unsupervised_semantic_rich_without_concern"
    if has_semantics and has_target:
        return "unsupervised_semantic_target_only"
    if has_semantics and has_family:
        return "unsupervised_semantic_family_only"
    return "learned_rich_program_composer"


def _module_coverage(spec: SearchedExecutableSpec) -> tuple[float, tuple[str, ...]]:
    missing = tuple(sorted(REQUIRED_SEARCHED_EXECUTABLE_MODULES - spec.modules))
    coverage = 1.0 - (len(missing) / len(REQUIRED_SEARCHED_EXECUTABLE_MODULES))
    return coverage, missing


def _train_return(spec: SearchedExecutableSpec, stats: dict[str, Any]) -> float:
    value = 0.34 + 0.52 * float(stats["action_accuracy"])
    if "surface_shortcut_head" in spec.modules:
        value += 0.16
    if "reward_head" in spec.modules:
        value += 0.05
    if "learned_composer_head" in spec.modules:
        value += 0.04
    value -= 0.008 * max(0, searched_executable_resource_cost(spec) - 12)
    return max(0.0, min(1.0, value))


def evaluate_searched_executable(
    spec: SearchedExecutableSpec,
    *,
    strategy: str,
    seed: int,
    generation: int,
    agent_summary: dict[str, dict[str, Any]],
    formal_verdict: ExecutableModuleVerdict | None = None,
) -> SearchedExecutableEvaluation:
    agent = empirical_agent_for_searched_executable(spec)
    stats = agent_summary[agent]
    verdict = formal_verdict or python_static_executable_verdict(spec)
    coverage, missing = _module_coverage(spec)
    transfer_pass = int(bool(stats.get("transfer_gate_pass", False)))
    formal_valid = int(verdict.formal_valid)
    gate = int(
        transfer_pass
        and not missing
        and formal_valid
        and verdict.resource_cost <= MAX_SEARCHED_EXECUTABLE_RESOURCE
        and float(stats["semantic_kind_accuracy"]) >= 0.95
        and float(stats["semantic_family_accuracy"]) >= 0.95
        and float(stats["semantic_pair_accuracy"]) >= 0.95
        and float(stats["action_accuracy"]) >= 0.85
        and float(stats["low_concern_program_rate"]) <= 0.25
        and float(stats["family_accuracy_high_concern"]) >= 0.70
        and float(stats["target_accuracy_high_concern"]) >= 0.70
        and float(stats["useful_program_rate_high_concern"]) >= 0.70
        and float(stats["rich_program_rate_high_concern"]) >= 0.70
    )
    return SearchedExecutableEvaluation(
        architecture=spec.key,
        strategy=strategy,
        seed=seed,
        generation=generation,
        empirical_agent=agent,
        train_return=_train_return(spec, stats),
        semantic_kind_accuracy=float(stats["semantic_kind_accuracy"]),
        semantic_family_accuracy=float(stats["semantic_family_accuracy"]),
        semantic_pair_accuracy=float(stats["semantic_pair_accuracy"]),
        transfer_gate_pass=transfer_pass,
        parse_accuracy_high_concern=float(stats["parse_accuracy_high_concern"]),
        action_accuracy=float(stats["action_accuracy"]),
        family_accuracy_high_concern=float(stats["family_accuracy_high_concern"]),
        target_accuracy_high_concern=float(stats["target_accuracy_high_concern"]),
        useful_program_rate_high_concern=float(stats["useful_program_rate_high_concern"]),
        rich_program_rate_high_concern=float(stats["rich_program_rate_high_concern"]),
        low_concern_program_rate=float(stats["low_concern_program_rate"]),
        module_coverage=coverage,
        formal_valid=formal_valid,
        formal_source=verdict.formal_source,
        resource_cost=verdict.resource_cost,
        executable_module_gate=gate,
        missing_modules=missing,
        violations=verdict.violations,
    )


def repair_searched_executable(spec: SearchedExecutableSpec) -> SearchedExecutableSpec:
    modules = set(spec.modules)
    changed = True
    while changed:
        changed = False
        for module, deps in EXECUTABLE_MODULE_DEPENDENCIES.items():
            if module in modules:
                missing = deps - modules
                if missing:
                    modules.update(missing)
                    changed = True
    if "concern_gate" in modules:
        modules.add("formal_guard")
    if "target_binder" in modules or "program_family_router" in modules:
        modules.add("semantic_profile_grounder")
        modules.add("label_free_slot_inducer")
        modules.add("component_slot_encoder")
    if "rich_program_composer" in modules:
        modules.add("program_family_router")
        modules.add("world_model")
    modules.add("component_slot_encoder")
    modules.add("reward_head")
    return SearchedExecutableSpec(frozenset(modules))


def promote_toward_searched_executable(
    spec: SearchedExecutableSpec,
) -> SearchedExecutableSpec:
    missing = sorted(TARGET_SEARCHED_EXECUTABLE_BODY - spec.modules)
    if not missing:
        return spec
    modules = set(spec.modules)
    modules.add(missing[0])
    return repair_searched_executable(SearchedExecutableSpec(frozenset(modules)))


def promote_family_proxy(spec: SearchedExecutableSpec) -> SearchedExecutableSpec:
    modules = set(spec.modules)
    modules.update(
        {
            "component_slot_encoder",
            "label_free_slot_inducer",
            "semantic_profile_grounder",
            "program_family_router",
            "family_proxy_head",
            "reward_head",
        }
    )
    return repair_searched_executable(SearchedExecutableSpec(frozenset(modules)))


def promote_target_proxy(spec: SearchedExecutableSpec) -> SearchedExecutableSpec:
    modules = set(spec.modules)
    modules.update(
        {
            "component_slot_encoder",
            "label_free_slot_inducer",
            "semantic_profile_grounder",
            "target_binder",
            "target_proxy_head",
            "world_model",
            "reward_head",
        }
    )
    return repair_searched_executable(SearchedExecutableSpec(frozenset(modules)))


def promote_ungated_rich(spec: SearchedExecutableSpec) -> SearchedExecutableSpec:
    modules = set(spec.modules)
    modules.update(UNGATED_RICH_EXECUTABLE_BODY)
    modules.discard("concern_gate")
    modules.discard("formal_guard")
    return repair_searched_executable(SearchedExecutableSpec(frozenset(modules)))


def complete_label_free_contract(spec: SearchedExecutableSpec) -> SearchedExecutableSpec:
    modules = set(spec.modules)
    has_semantics = bool(
        {
            "label_free_slot_inducer",
            "semantic_profile_grounder",
            "profile_memory",
        }
        & modules
    )
    has_body = bool(
        {
            "concern_gate",
            "target_binder",
            "program_family_router",
            "rich_program_composer",
        }
        & modules
    )
    if has_semantics or has_body:
        modules.update(TARGET_SEARCHED_EXECUTABLE_BODY)
    return repair_searched_executable(SearchedExecutableSpec(frozenset(modules)))


def mutate_searched_executable(
    spec: SearchedExecutableSpec,
    rng: random.Random,
) -> SearchedExecutableSpec:
    modules = set(spec.modules)
    module = rng.choice(EXECUTABLE_MODULE_CATALOG)
    if module in modules and module not in {"component_slot_encoder", "reward_head"}:
        modules.remove(module)
    else:
        modules.add(module)
    return SearchedExecutableSpec(frozenset(modules))


def _descriptor(spec: SearchedExecutableSpec) -> tuple[int, int, int, int, int, int]:
    return (
        int("label_free_slot_inducer" in spec.modules),
        int("concern_gate" in spec.modules),
        int("target_binder" in spec.modules),
        int("program_family_router" in spec.modules),
        int("rich_program_composer" in spec.modules),
        min(5, searched_executable_resource_cost(spec) // 4),
    )


def _novelty(
    spec: SearchedExecutableSpec,
    archive: dict[tuple[int, int, int, int, int, int], SearchedExecutableEvaluation],
) -> float:
    return 1.0 if _descriptor(spec) not in archive else 0.1


def _ranking_score(
    evaluation: SearchedExecutableEvaluation,
    spec: SearchedExecutableSpec,
    strategy: str,
    archive: dict[tuple[int, int, int, int, int, int], SearchedExecutableEvaluation],
) -> float:
    if strategy == "reward_only":
        return evaluation.train_return
    if strategy == "family_proxy":
        concern_penalty = 0.25 if "concern_gate" in spec.modules else 0.0
        return (
            evaluation.semantic_family_accuracy
            + evaluation.family_accuracy_high_concern
            + 0.15 * _novelty(spec, archive)
            - 0.45 * (1 - evaluation.formal_valid)
            - concern_penalty
            - 0.02 * max(0, evaluation.resource_cost - 9)
        )
    if strategy == "target_proxy":
        concern_penalty = 0.25 if "concern_gate" in spec.modules else 0.0
        return (
            evaluation.semantic_pair_accuracy
            + evaluation.target_accuracy_high_concern
            + 0.15 * _novelty(spec, archive)
            - 0.45 * (1 - evaluation.formal_valid)
            - concern_penalty
            - 0.02 * max(0, evaluation.resource_cost - 10)
        )
    if strategy == "ungated_rich_proxy":
        ungated_bonus = 0.35 if "concern_gate" not in spec.modules else -0.35
        return (
            evaluation.semantic_kind_accuracy
            + evaluation.family_accuracy_high_concern
            + evaluation.target_accuracy_high_concern
            + evaluation.useful_program_rate_high_concern
            + evaluation.rich_program_rate_high_concern
            + ungated_bonus
            - 0.02 * max(0, evaluation.resource_cost - 15)
        )
    if strategy == "viability_guided":
        return (
            4.0 * evaluation.executable_module_gate
            + 1.4 * evaluation.transfer_gate_pass
            + evaluation.semantic_kind_accuracy
            + evaluation.semantic_family_accuracy
            + evaluation.semantic_pair_accuracy
            + evaluation.family_accuracy_high_concern
            + evaluation.target_accuracy_high_concern
            + evaluation.useful_program_rate_high_concern
            + evaluation.rich_program_rate_high_concern
            + 0.25 * _novelty(spec, archive)
            - 0.45 * (1 - evaluation.formal_valid)
            - 0.02 * max(0, evaluation.resource_cost - 18)
            - 0.35 * max(0.0, evaluation.low_concern_program_rate - 0.25)
        )
    raise KeyError(strategy)


def _initial_specs(rng: random.Random, population: int) -> list[SearchedExecutableSpec]:
    specs = [
        SearchedExecutableSpec(frozenset({"component_slot_encoder", "reward_head"})),
        SearchedExecutableSpec(
            frozenset(
                {
                    "component_slot_encoder",
                    "reward_head",
                    "surface_shortcut_head",
                    "learned_composer_head",
                }
            )
        ),
        promote_family_proxy(SearchedExecutableSpec(frozenset())),
        promote_target_proxy(SearchedExecutableSpec(frozenset())),
        SearchedExecutableSpec(UNGATED_RICH_EXECUTABLE_BODY),
    ]
    while len(specs) < population:
        modules = {"component_slot_encoder", "reward_head"}
        for module in EXECUTABLE_MODULE_CATALOG:
            if module not in modules and rng.random() < 0.17:
                modules.add(module)
        specs.append(SearchedExecutableSpec(frozenset(modules)))
    return specs


def run_searched_executable_search(
    *,
    strategy: str,
    seed: int,
    generations: int,
    population: int,
    agent_summary: dict[str, dict[str, Any]],
) -> list[SearchedExecutableEvaluation]:
    rng = random.Random(seed)
    specs = _initial_specs(rng, population)
    archive: dict[tuple[int, int, int, int, int, int], SearchedExecutableEvaluation] = {}
    history: list[SearchedExecutableEvaluation] = []

    for generation in range(generations):
        candidates = list(specs)
        for spec in specs:
            candidates.append(mutate_searched_executable(spec, rng))
            candidates.append(repair_searched_executable(spec))
            if strategy == "family_proxy":
                candidates.append(promote_family_proxy(spec))
            elif strategy == "target_proxy":
                candidates.append(promote_target_proxy(spec))
            elif strategy == "ungated_rich_proxy":
                candidates.append(promote_ungated_rich(spec))
            elif strategy == "viability_guided":
                candidates.append(promote_toward_searched_executable(spec))
                candidates.append(complete_label_free_contract(spec))

        scored: list[
            tuple[float, SearchedExecutableSpec, SearchedExecutableEvaluation]
        ] = []
        for spec in candidates:
            evaluation = evaluate_searched_executable(
                spec,
                strategy=strategy,
                seed=seed,
                generation=generation,
                agent_summary=agent_summary,
                formal_verdict=python_static_executable_verdict(spec),
            )
            scored.append(
                (_ranking_score(evaluation, spec, strategy, archive), spec, evaluation)
            )
            desc = _descriptor(spec)
            if (
                desc not in archive
                or evaluation.executable_module_gate
                > archive[desc].executable_module_gate
            ):
                archive[desc] = evaluation

        scored.sort(key=lambda item: item[0], reverse=True)
        specs = [spec for _, spec, _ in scored[:population]]
        history.append(scored[0][2])
    return history


def run_seed_search(
    *,
    seed: int,
    strategies: tuple[str, ...] = SEARCHED_EXECUTABLE_STRATEGIES,
    generations: int,
    population: int,
    train_trials: int,
    test_trials: int,
    epochs: int,
    induction_calibration_trials: int,
) -> dict[str, Any]:
    transfer_payload = run_experiment(
        train_trials=train_trials,
        test_trials=test_trials,
        seed=seed,
        epochs=epochs,
        induction_calibration_trials=induction_calibration_trials,
    )
    rows: list[SearchedExecutableEvaluation] = []
    for strategy in strategies:
        rows.extend(
            run_searched_executable_search(
                strategy=strategy,
                seed=seed,
                generations=generations,
                population=population,
                agent_summary=transfer_payload["agent_summary"],
            )
        )
    return {
        "seed": seed,
        "agent_summary": transfer_payload["agent_summary"],
        "semantic_summary": transfer_payload["semantic_summary"],
        "results": [asdict(row) for row in rows],
        "summary": summarize_searched_executable_rows(rows),
    }


def run_searched_executable_sweep(
    *,
    strategies: tuple[str, ...] = SEARCHED_EXECUTABLE_STRATEGIES,
    seeds: int,
    generations: int,
    population: int,
    train_trials: int,
    test_trials: int,
    epochs: int,
    induction_calibration_trials: int,
    base_seed: int,
    seed_values: tuple[int, ...] | None = None,
) -> dict[str, Any]:
    run_seeds = seed_values or tuple(base_seed + idx for idx in range(seeds))
    seed_payloads = [
        run_seed_search(
            seed=seed,
            strategies=strategies,
            generations=generations,
            population=population,
            train_trials=train_trials,
            test_trials=test_trials,
            epochs=epochs,
            induction_calibration_trials=induction_calibration_trials,
        )
        for seed in run_seeds
    ]
    return searched_executable_payload(
        seed_payloads=seed_payloads,
        strategies=strategies,
        generations=generations,
        population=population,
        train_trials=train_trials,
        test_trials=test_trials,
        epochs=epochs,
        induction_calibration_trials=induction_calibration_trials,
        seed_values=run_seeds,
        base_seed=base_seed,
    )


SearchedExecutableRow = SearchedExecutableEvaluation | Mapping[str, Any]


def _row_value(row: SearchedExecutableRow, key: str) -> Any:
    if isinstance(row, Mapping):
        mapping = cast(Mapping[str, Any], row)
        return mapping[key]
    return getattr(row, key)


def summarize_searched_executable_rows(
    rows: Sequence[SearchedExecutableRow],
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[SearchedExecutableRow]] = {}
    for row in rows:
        grouped.setdefault(str(_row_value(row, "strategy")), []).append(row)

    summary: dict[str, dict[str, Any]] = {}
    for strategy, items in sorted(grouped.items()):
        final_by_seed: dict[int, SearchedExecutableRow] = {}
        for item in items:
            seed = int(_row_value(item, "seed"))
            generation = int(_row_value(item, "generation"))
            if seed not in final_by_seed or generation > int(
                _row_value(final_by_seed[seed], "generation")
            ):
                final_by_seed[seed] = item
        finals = list(final_by_seed.values())
        best = max(
            finals,
            key=lambda item: (
                int(_row_value(item, "executable_module_gate")),
                int(_row_value(item, "transfer_gate_pass")),
                float(_row_value(item, "module_coverage")),
                float(_row_value(item, "semantic_pair_accuracy")),
                float(_row_value(item, "target_accuracy_high_concern")),
                float(_row_value(item, "train_return")),
            ),
        )
        gates = [int(_row_value(item, "executable_module_gate")) for item in finals]
        summary[strategy] = {
            "n_seeds": len(finals),
            "executable_module_gate_rate": mean(gates) if finals else 0.0,
            "executable_module_gate_rate_sd": pstdev(gates) if len(finals) > 1 else 0.0,
            "transfer_gate_rate": mean(
                int(_row_value(item, "transfer_gate_pass")) for item in finals
            )
            if finals
            else 0.0,
            "formal_valid_rate": mean(
                int(_row_value(item, "formal_valid")) for item in finals
            )
            if finals
            else 0.0,
            "semantic_kind_accuracy": mean(
                float(_row_value(item, "semantic_kind_accuracy")) for item in finals
            )
            if finals
            else 0.0,
            "semantic_family_accuracy": mean(
                float(_row_value(item, "semantic_family_accuracy")) for item in finals
            )
            if finals
            else 0.0,
            "semantic_pair_accuracy": mean(
                float(_row_value(item, "semantic_pair_accuracy")) for item in finals
            )
            if finals
            else 0.0,
            "family_accuracy_high_concern": mean(
                float(_row_value(item, "family_accuracy_high_concern"))
                for item in finals
            )
            if finals
            else 0.0,
            "target_accuracy_high_concern": mean(
                float(_row_value(item, "target_accuracy_high_concern"))
                for item in finals
            )
            if finals
            else 0.0,
            "useful_program_rate_high_concern": mean(
                float(_row_value(item, "useful_program_rate_high_concern"))
                for item in finals
            )
            if finals
            else 0.0,
            "rich_program_rate_high_concern": mean(
                float(_row_value(item, "rich_program_rate_high_concern"))
                for item in finals
            )
            if finals
            else 0.0,
            "low_concern_program_rate": mean(
                float(_row_value(item, "low_concern_program_rate")) for item in finals
            )
            if finals
            else 0.0,
            "module_coverage": mean(
                float(_row_value(item, "module_coverage")) for item in finals
            )
            if finals
            else 0.0,
            "train_return": mean(
                float(_row_value(item, "train_return")) for item in finals
            )
            if finals
            else 0.0,
            "resource_cost": mean(
                float(_row_value(item, "resource_cost")) for item in finals
            )
            if finals
            else 0.0,
            "best_architecture": str(_row_value(best, "architecture")) if finals else "",
            "best_empirical_agent": str(_row_value(best, "empirical_agent"))
            if finals
            else "",
            "formal_source": "+".join(
                sorted({str(_row_value(item, "formal_source")) for item in finals})
            ),
            "gate_pass": bool(finals and mean(gates) >= 0.75),
        }
    return summary


def summarize_seed_payloads(
    payloads: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for payload in payloads:
        rows.extend(payload["results"])
    return summarize_searched_executable_rows(rows)


def searched_executable_payload(
    *,
    seed_payloads: list[dict[str, Any]],
    strategies: tuple[str, ...],
    generations: int,
    population: int,
    train_trials: int,
    test_trials: int,
    epochs: int,
    induction_calibration_trials: int,
    seed_values: tuple[int, ...],
    base_seed: int,
) -> dict[str, Any]:
    return {
        "manifest": {
            "arc": "2A/2B",
            "name": "searched_executable_modules_label_free_2a_v2",
            "contract": "2A-v2-pixels-rich_programs-label_free_transfer",
            "strategies": list(strategies),
            "seeds": len(seed_values),
            "seed_values": list(seed_values),
            "generations": generations,
            "population": population,
            "train_trials": train_trials,
            "test_trials": test_trials,
            "induction_calibration_trials": induction_calibration_trials,
            "epochs": epochs,
            "base_seed": base_seed,
            "required_modules": sorted(REQUIRED_SEARCHED_EXECUTABLE_MODULES),
            "max_resource_cost": MAX_SEARCHED_EXECUTABLE_RESOURCE,
        },
        "results": seed_payloads,
        "summary": summarize_seed_payloads(seed_payloads),
    }


def _manifest_text(manifest: dict[str, Any]) -> str:
    return (
        f"{manifest['seeds']} seeds, {manifest['generations']} generations, "
        f"population {manifest['population']}, {manifest['train_trials']} train / "
        f"{manifest['test_trials']} test trials per held-out slice/seed, "
        f"{manifest['induction_calibration_trials']} label-free induction trials/seed, "
        f"{manifest['epochs']} epochs. Contract: `{manifest['contract']}`."
    )


def write_searched_executable_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    manifest = payload["manifest"]
    lines = [
        "# Searched Executable Modules Against Label-Free 2A-v2 Transfer",
        "",
        "Date: 2026-06-22",
        "",
        (
            "Question: can Arc 2B search executable module bodies that consume "
            "the label-free `2A-v2-pixels-rich_programs` transfer contract, "
            "rather than accepting a compact hand-instantiated body?"
        ),
        "",
        f"Manifest: {_manifest_text(manifest)}",
        "",
        "Required modules: "
        + ", ".join(f"`{module}`" for module in manifest["required_modules"])
        + ".",
        "",
        "## Body Search Summary",
        "",
        (
            "| Strategy | Body gate | Transfer | Formal | Sem kind | Sem pair | "
            "Modules | Family | Target | Useful | Rich | Low prog | Cost | "
            "Best body | Agent | Formal source | Gate |"
        ),
        (
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
            "---|---|---|---|"
        ),
    ]
    for strategy, stats in sorted(summary.items()):
        lines.append(
            "| {strategy} | {gate_rate:.3f} | {transfer:.3f} | {formal:.3f} | "
            "{sem_kind:.3f} | {sem_pair:.3f} | {modules:.3f} | "
            "{family:.3f} | {target:.3f} | {useful:.3f} | {rich:.3f} | "
            "{low:.3f} | {cost:.3f} | `{best}` | `{agent}` | `{source}` | "
            "{gate} |".format(
                strategy=strategy,
                gate_rate=stats["executable_module_gate_rate"],
                transfer=stats["transfer_gate_rate"],
                formal=stats["formal_valid_rate"],
                sem_kind=stats["semantic_kind_accuracy"],
                sem_pair=stats["semantic_pair_accuracy"],
                modules=stats["module_coverage"],
                family=stats["family_accuracy_high_concern"],
                target=stats["target_accuracy_high_concern"],
                useful=stats["useful_program_rate_high_concern"],
                rich=stats["rich_program_rate_high_concern"],
                low=stats["low_concern_program_rate"],
                cost=stats["resource_cost"],
                best=stats["best_architecture"],
                agent=stats["best_empirical_agent"],
                source=stats["formal_source"],
                gate="PASS" if stats["gate_pass"] else "fail",
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "`viability_guided` is accepted only when search reconstructs "
                "the complete label-free executable body: component slots, "
                "slot induction, semantic profile grounding, concern gating, "
                "target binding, family routing, rich composition, world-model "
                "support, and a formal guard."
            ),
            "",
            (
                "`reward_only`, `family_proxy`, `target_proxy`, and "
                "`ungated_rich_proxy` fail for different reasons. They can "
                "prefer return shortcuts, family routing, target binding, or "
                "rich composition, but they do not simultaneously inherit the "
                "held-out label-free transfer gate, module coverage, and "
                "low-concern no-program discipline."
            ),
            "",
            (
                "This is searched executable-module discovery over a bounded "
                "contract grammar. It is not full neural architecture search, "
                "natural-image object discovery, or fully unsupervised semantic "
                "profile discovery."
            ),
            "",
            "Raw JSON remains local under `artifacts/viable_computational_bodies/`.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_seed_list(value: str | None) -> tuple[int, ...] | None:
    if not value:
        return None
    return tuple(int(item.strip()) for item in value.split(",") if item.strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=2)
    parser.add_argument("--generations", type=int, default=10)
    parser.add_argument("--population", type=int, default=12)
    parser.add_argument("--train-trials", type=int, default=300)
    parser.add_argument("--test-trials", type=int, default=120)
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--induction-calibration-trials", type=int, default=180)
    parser.add_argument("--base-seed", type=int, default=20260622)
    parser.add_argument(
        "--seed-list",
        help="Comma-separated explicit seed list; overrides --seeds/--base-seed.",
    )
    parser.add_argument("--out", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    payload = run_searched_executable_sweep(
        seeds=args.seeds,
        generations=args.generations,
        population=args.population,
        train_trials=args.train_trials,
        test_trials=args.test_trials,
        epochs=args.epochs,
        induction_calibration_trials=args.induction_calibration_trials,
        base_seed=args.base_seed,
        seed_values=_parse_seed_list(args.seed_list),
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.report:
        write_searched_executable_report(args.report, payload)

    print("=== Searched Executable Modules Against Label-Free 2A-v2 Transfer ===")
    for strategy, stats in sorted(payload["summary"].items()):
        print(
            f"{strategy:22s} gate={stats['executable_module_gate_rate']:.3f} "
            f"transfer={stats['transfer_gate_rate']:.3f} "
            f"modules={stats['module_coverage']:.3f} "
            f"family={stats['family_accuracy_high_concern']:.3f} "
            f"target={stats['target_accuracy_high_concern']:.3f} "
            f"low_prog={stats['low_concern_program_rate']:.3f} "
            f"agent={stats['best_empirical_agent']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
