#!/usr/bin/env python3
"""Search 2B executable bodies against learned object-slot 2A transfer.

The previous searched executable-body gate consumed the label-free slot
semantics transfer contract. This sidecar upgrades the consumed 2A contract to
the current learned-object-slot + discovered-profile path: learned foreground
slots, fixed slot-local center search, profile induction, concern gating,
target binding, family routing, and rich program composition must all be
covered by the selected body.

This is still bounded executable-module search over a synthetic contract. It
is not full neural architecture search or natural-image object discovery.
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

from experiments.concerned_syntax.learned_object_slots import run_experiment

REQUIRED_OBJECT_SLOT_EXECUTABLE_MODULES: frozenset[str] = frozenset(
    {
        "learned_foreground_extractor",
        "object_slot_centerer",
        "discovered_profile_inducer",
        "profile_action_template",
        "concern_gate",
        "target_binder",
        "program_family_router",
        "rich_program_composer",
        "world_model",
        "formal_guard",
    }
)

OBJECT_SLOT_MODULE_CATALOG: tuple[str, ...] = (
    "learned_foreground_extractor",
    "object_slot_centerer",
    "discovered_profile_inducer",
    "profile_action_template",
    "concern_gate",
    "target_binder",
    "program_family_router",
    "rich_program_composer",
    "world_model",
    "formal_guard",
    "action_head",
    "reward_head",
    "component_slot_encoder",
    "label_free_slot_inducer",
    "surface_shortcut_head",
    "learned_composer_head",
    "family_proxy_head",
    "target_proxy_head",
    "ungated_program_executor",
    "profile_memory",
)

OBJECT_SLOT_MODULE_COST: dict[str, int] = {
    "learned_foreground_extractor": 3,
    "object_slot_centerer": 2,
    "discovered_profile_inducer": 3,
    "profile_action_template": 1,
    "concern_gate": 1,
    "target_binder": 2,
    "program_family_router": 2,
    "rich_program_composer": 2,
    "world_model": 2,
    "formal_guard": 1,
    "action_head": 1,
    "reward_head": 1,
    "component_slot_encoder": 2,
    "label_free_slot_inducer": 2,
    "surface_shortcut_head": 1,
    "learned_composer_head": 2,
    "family_proxy_head": 1,
    "target_proxy_head": 1,
    "ungated_program_executor": 1,
    "profile_memory": 1,
}

OBJECT_SLOT_MODULE_DEPENDENCIES: dict[str, set[str]] = {
    "object_slot_centerer": {"learned_foreground_extractor"},
    "discovered_profile_inducer": {"object_slot_centerer"},
    "profile_action_template": {"discovered_profile_inducer"},
    "concern_gate": {"discovered_profile_inducer"},
    "target_binder": {"discovered_profile_inducer", "world_model"},
    "program_family_router": {"discovered_profile_inducer"},
    "rich_program_composer": {"program_family_router", "world_model"},
    "action_head": {"target_binder", "world_model"},
    "family_proxy_head": {"program_family_router"},
    "target_proxy_head": {"target_binder"},
    "ungated_program_executor": {"rich_program_composer"},
    "profile_memory": {"discovered_profile_inducer"},
}

TARGET_OBJECT_SLOT_EXECUTABLE_BODY: frozenset[str] = frozenset(
    {
        "learned_foreground_extractor",
        "object_slot_centerer",
        "discovered_profile_inducer",
        "profile_action_template",
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

UNGATED_OBJECT_SLOT_RICH_BODY: frozenset[str] = frozenset(
    {
        "learned_foreground_extractor",
        "object_slot_centerer",
        "discovered_profile_inducer",
        "profile_action_template",
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

OBJECT_SLOT_EXECUTABLE_STRATEGIES: tuple[str, ...] = (
    "reward_only",
    "family_proxy",
    "target_proxy",
    "ungated_rich_proxy",
    "viability_guided",
)

MAX_OBJECT_SLOT_RESOURCE = 24


@dataclass(frozen=True)
class ObjectSlotExecutableSpec:
    modules: frozenset[str]

    @property
    def key(self) -> str:
        return "+".join(sorted(self.modules))


@dataclass(frozen=True)
class ObjectSlotExecutableVerdict:
    formal_valid: bool
    resource_cost: int
    violations: tuple[str, ...]
    formal_source: str = "python_static"


@dataclass(frozen=True)
class ObjectSlotExecutableEvaluation:
    architecture: str
    strategy: str
    seed: int
    generation: int
    empirical_agent: str
    train_return: float
    slot_recovery_rate: float
    scene_recovery_rate: float
    profile_cluster_purity: float
    semantic_family_accuracy: float
    semantic_pair_accuracy: float
    profile_action_consistency: float
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
    object_slot_body_gate: int
    missing_modules: tuple[str, ...]
    violations: tuple[str, ...]


def object_slot_resource_cost(spec: ObjectSlotExecutableSpec) -> int:
    return sum(OBJECT_SLOT_MODULE_COST[module] for module in spec.modules)


def object_slot_violations(spec: ObjectSlotExecutableSpec) -> tuple[str, ...]:
    modules = spec.modules
    violations: list[str] = []
    for module, deps in OBJECT_SLOT_MODULE_DEPENDENCIES.items():
        if module in modules:
            missing = sorted(deps - modules)
            if missing:
                violations.append(f"{module}_missing_{'+'.join(missing)}")
    if "concern_gate" in modules and "formal_guard" not in modules:
        violations.append("concern_without_formal_guard")
    if "surface_shortcut_head" in modules and "formal_guard" not in modules:
        violations.append("shortcut_without_formal_guard")
    if "target_binder" in modules and "discovered_profile_inducer" not in modules:
        violations.append("target_without_discovered_profiles")
    if (
        "rich_program_composer" in modules
        and "program_family_router" not in modules
    ):
        violations.append("composer_without_family_router")
    if (
        "component_slot_encoder" in modules
        and "learned_foreground_extractor" not in modules
    ):
        violations.append("legacy_component_slots_without_learned_extractor")
    if object_slot_resource_cost(spec) > MAX_OBJECT_SLOT_RESOURCE:
        violations.append("object_slot_resource_over_budget")
    if "learned_foreground_extractor" not in modules:
        violations.append("missing_learned_foreground_extractor")
    return tuple(violations)


def python_static_object_slot_verdict(
    spec: ObjectSlotExecutableSpec,
) -> ObjectSlotExecutableVerdict:
    violations = object_slot_violations(spec)
    return ObjectSlotExecutableVerdict(
        formal_valid=not violations,
        resource_cost=object_slot_resource_cost(spec),
        violations=violations,
    )


def _has(spec: ObjectSlotExecutableSpec, *modules: str) -> bool:
    return all(module in spec.modules for module in modules)


def empirical_agent_for_object_slot_executable(
    spec: ObjectSlotExecutableSpec,
) -> str:
    """Map modules to the learned-object-slot 2A agent they can express."""

    has_profiles = _has(
        spec,
        "learned_foreground_extractor",
        "object_slot_centerer",
        "discovered_profile_inducer",
    )
    has_templates = has_profiles and _has(spec, "profile_action_template")
    has_concern = _has(spec, "concern_gate", "formal_guard")
    has_target = has_profiles and _has(spec, "target_binder", "world_model")
    has_family = has_profiles and _has(spec, "program_family_router")
    has_composer = _has(spec, "rich_program_composer", "program_family_router")

    if (
        has_templates
        and has_concern
        and has_target
        and has_family
        and has_composer
    ):
        return "learned_object_slot_discovered_world_model"
    if has_templates and has_target and has_family and has_composer:
        return "learned_object_slot_rich_without_concern"
    if has_profiles and has_target:
        return "learned_object_slot_target_only"
    if has_profiles and has_family:
        return "learned_object_slot_family_only"
    return "learned_rich_program_composer"


def _module_coverage(spec: ObjectSlotExecutableSpec) -> tuple[float, tuple[str, ...]]:
    missing = tuple(sorted(REQUIRED_OBJECT_SLOT_EXECUTABLE_MODULES - spec.modules))
    coverage = 1.0 - (len(missing) / len(REQUIRED_OBJECT_SLOT_EXECUTABLE_MODULES))
    return coverage, missing


def _train_return(spec: ObjectSlotExecutableSpec, stats: dict[str, Any]) -> float:
    value = 0.34 + 0.52 * float(stats["action_accuracy"])
    if "surface_shortcut_head" in spec.modules:
        value += 0.16
    if "reward_head" in spec.modules:
        value += 0.05
    if "learned_composer_head" in spec.modules:
        value += 0.04
    value -= 0.007 * max(0, object_slot_resource_cost(spec) - 14)
    return max(0.0, min(1.0, value))


def evaluate_object_slot_executable(
    spec: ObjectSlotExecutableSpec,
    *,
    strategy: str,
    seed: int,
    generation: int,
    agent_summary: dict[str, dict[str, Any]],
    extractor_summary: dict[str, Any],
    formal_verdict: ObjectSlotExecutableVerdict | None = None,
) -> ObjectSlotExecutableEvaluation:
    agent = empirical_agent_for_object_slot_executable(spec)
    stats = agent_summary[agent]
    verdict = formal_verdict or python_static_object_slot_verdict(spec)
    coverage, missing = _module_coverage(spec)
    transfer_pass = int(bool(stats.get("transfer_gate_pass", False)))
    formal_valid = int(verdict.formal_valid)
    slot_recovery = float(extractor_summary["slot_recovery_rate"])
    scene_recovery = float(extractor_summary["scene_recovery_rate"])
    gate = int(
        transfer_pass
        and not missing
        and formal_valid
        and verdict.resource_cost <= MAX_OBJECT_SLOT_RESOURCE
        and slot_recovery >= 0.95
        and scene_recovery >= 0.95
        and float(stats["profile_cluster_purity"]) >= 0.95
        and float(stats["semantic_family_accuracy"]) >= 0.95
        and float(stats["semantic_pair_accuracy"]) >= 0.95
        and float(stats["profile_action_consistency"]) >= 0.95
        and float(stats["action_accuracy"]) >= 0.85
        and float(stats["low_concern_program_rate"]) <= 0.25
        and float(stats["family_accuracy_high_concern"]) >= 0.70
        and float(stats["target_accuracy_high_concern"]) >= 0.70
        and float(stats["useful_program_rate_high_concern"]) >= 0.70
        and float(stats["rich_program_rate_high_concern"]) >= 0.70
    )
    return ObjectSlotExecutableEvaluation(
        architecture=spec.key,
        strategy=strategy,
        seed=seed,
        generation=generation,
        empirical_agent=agent,
        train_return=_train_return(spec, stats),
        slot_recovery_rate=slot_recovery,
        scene_recovery_rate=scene_recovery,
        profile_cluster_purity=float(stats["profile_cluster_purity"]),
        semantic_family_accuracy=float(stats["semantic_family_accuracy"]),
        semantic_pair_accuracy=float(stats["semantic_pair_accuracy"]),
        profile_action_consistency=float(stats["profile_action_consistency"]),
        transfer_gate_pass=transfer_pass,
        parse_accuracy_high_concern=float(stats["parse_accuracy_high_concern"]),
        action_accuracy=float(stats["action_accuracy"]),
        family_accuracy_high_concern=float(stats["family_accuracy_high_concern"]),
        target_accuracy_high_concern=float(stats["target_accuracy_high_concern"]),
        useful_program_rate_high_concern=float(
            stats["useful_program_rate_high_concern"]
        ),
        rich_program_rate_high_concern=float(stats["rich_program_rate_high_concern"]),
        low_concern_program_rate=float(stats["low_concern_program_rate"]),
        module_coverage=coverage,
        formal_valid=formal_valid,
        formal_source=verdict.formal_source,
        resource_cost=verdict.resource_cost,
        object_slot_body_gate=gate,
        missing_modules=missing,
        violations=verdict.violations,
    )


def repair_object_slot_executable(
    spec: ObjectSlotExecutableSpec,
) -> ObjectSlotExecutableSpec:
    modules = set(spec.modules)
    changed = True
    while changed:
        changed = False
        for module, deps in OBJECT_SLOT_MODULE_DEPENDENCIES.items():
            if module in modules:
                missing = deps - modules
                if missing:
                    modules.update(missing)
                    changed = True
    if "concern_gate" in modules:
        modules.add("formal_guard")
    if (
        "target_binder" in modules
        or "program_family_router" in modules
        or "profile_action_template" in modules
    ):
        modules.update(
            {
                "learned_foreground_extractor",
                "object_slot_centerer",
                "discovered_profile_inducer",
            }
        )
    if "rich_program_composer" in modules:
        modules.add("program_family_router")
        modules.add("world_model")
    modules.add("learned_foreground_extractor")
    modules.add("reward_head")
    return ObjectSlotExecutableSpec(frozenset(modules))


def promote_toward_object_slot_executable(
    spec: ObjectSlotExecutableSpec,
) -> ObjectSlotExecutableSpec:
    missing = sorted(TARGET_OBJECT_SLOT_EXECUTABLE_BODY - spec.modules)
    if not missing:
        return spec
    modules = set(spec.modules)
    modules.add(missing[0])
    return repair_object_slot_executable(ObjectSlotExecutableSpec(frozenset(modules)))


def promote_family_proxy(
    spec: ObjectSlotExecutableSpec,
) -> ObjectSlotExecutableSpec:
    modules = set(spec.modules)
    modules.update(
        {
            "learned_foreground_extractor",
            "object_slot_centerer",
            "discovered_profile_inducer",
            "program_family_router",
            "family_proxy_head",
            "reward_head",
        }
    )
    return repair_object_slot_executable(ObjectSlotExecutableSpec(frozenset(modules)))


def promote_target_proxy(
    spec: ObjectSlotExecutableSpec,
) -> ObjectSlotExecutableSpec:
    modules = set(spec.modules)
    modules.update(
        {
            "learned_foreground_extractor",
            "object_slot_centerer",
            "discovered_profile_inducer",
            "target_binder",
            "target_proxy_head",
            "world_model",
            "reward_head",
        }
    )
    return repair_object_slot_executable(ObjectSlotExecutableSpec(frozenset(modules)))


def promote_ungated_rich(
    spec: ObjectSlotExecutableSpec,
) -> ObjectSlotExecutableSpec:
    modules = set(spec.modules)
    modules.update(UNGATED_OBJECT_SLOT_RICH_BODY)
    modules.discard("concern_gate")
    modules.discard("formal_guard")
    return repair_object_slot_executable(ObjectSlotExecutableSpec(frozenset(modules)))


def complete_object_slot_contract(
    spec: ObjectSlotExecutableSpec,
) -> ObjectSlotExecutableSpec:
    modules = set(spec.modules)
    has_profile_path = bool(
        {
            "object_slot_centerer",
            "discovered_profile_inducer",
            "profile_action_template",
            "profile_memory",
        }
        & modules
    )
    has_body_path = bool(
        {
            "concern_gate",
            "target_binder",
            "program_family_router",
            "rich_program_composer",
        }
        & modules
    )
    if has_profile_path or has_body_path:
        modules.update(TARGET_OBJECT_SLOT_EXECUTABLE_BODY)
    return repair_object_slot_executable(ObjectSlotExecutableSpec(frozenset(modules)))


def mutate_object_slot_executable(
    spec: ObjectSlotExecutableSpec,
    rng: random.Random,
) -> ObjectSlotExecutableSpec:
    modules = set(spec.modules)
    module = rng.choice(OBJECT_SLOT_MODULE_CATALOG)
    if module in modules and module not in {"learned_foreground_extractor", "reward_head"}:
        modules.remove(module)
    else:
        modules.add(module)
    return ObjectSlotExecutableSpec(frozenset(modules))


def _descriptor(spec: ObjectSlotExecutableSpec) -> tuple[int, int, int, int, int, int]:
    return (
        int("object_slot_centerer" in spec.modules),
        int("discovered_profile_inducer" in spec.modules),
        int("concern_gate" in spec.modules),
        int("target_binder" in spec.modules),
        int("program_family_router" in spec.modules),
        min(6, object_slot_resource_cost(spec) // 4),
    )


def _novelty(
    spec: ObjectSlotExecutableSpec,
    archive: dict[tuple[int, int, int, int, int, int], ObjectSlotExecutableEvaluation],
) -> float:
    return 1.0 if _descriptor(spec) not in archive else 0.1


def _ranking_score(
    evaluation: ObjectSlotExecutableEvaluation,
    spec: ObjectSlotExecutableSpec,
    strategy: str,
    archive: dict[tuple[int, int, int, int, int, int], ObjectSlotExecutableEvaluation],
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
            - 0.02 * max(0, evaluation.resource_cost - 11)
        )
    if strategy == "target_proxy":
        concern_penalty = 0.25 if "concern_gate" in spec.modules else 0.0
        return (
            evaluation.semantic_pair_accuracy
            + evaluation.target_accuracy_high_concern
            + 0.15 * _novelty(spec, archive)
            - 0.45 * (1 - evaluation.formal_valid)
            - concern_penalty
            - 0.02 * max(0, evaluation.resource_cost - 12)
        )
    if strategy == "ungated_rich_proxy":
        ungated_bonus = 0.35 if "concern_gate" not in spec.modules else -0.35
        return (
            evaluation.profile_cluster_purity
            + evaluation.profile_action_consistency
            + evaluation.family_accuracy_high_concern
            + evaluation.target_accuracy_high_concern
            + evaluation.useful_program_rate_high_concern
            + evaluation.rich_program_rate_high_concern
            + ungated_bonus
            - 0.02 * max(0, evaluation.resource_cost - 17)
        )
    if strategy == "viability_guided":
        return (
            4.0 * evaluation.object_slot_body_gate
            + 1.4 * evaluation.transfer_gate_pass
            + evaluation.slot_recovery_rate
            + evaluation.scene_recovery_rate
            + evaluation.profile_cluster_purity
            + evaluation.semantic_family_accuracy
            + evaluation.semantic_pair_accuracy
            + evaluation.profile_action_consistency
            + evaluation.family_accuracy_high_concern
            + evaluation.target_accuracy_high_concern
            + evaluation.useful_program_rate_high_concern
            + evaluation.rich_program_rate_high_concern
            + 0.25 * _novelty(spec, archive)
            - 0.45 * (1 - evaluation.formal_valid)
            - 0.02 * max(0, evaluation.resource_cost - 21)
            - 0.35 * max(0.0, evaluation.low_concern_program_rate - 0.25)
        )
    raise KeyError(strategy)


def _initial_specs(
    rng: random.Random,
    population: int,
) -> list[ObjectSlotExecutableSpec]:
    specs = [
        ObjectSlotExecutableSpec(frozenset({"component_slot_encoder", "reward_head"})),
        ObjectSlotExecutableSpec(
            frozenset(
                {
                    "component_slot_encoder",
                    "reward_head",
                    "surface_shortcut_head",
                    "learned_composer_head",
                }
            )
        ),
        promote_family_proxy(ObjectSlotExecutableSpec(frozenset())),
        promote_target_proxy(ObjectSlotExecutableSpec(frozenset())),
        ObjectSlotExecutableSpec(UNGATED_OBJECT_SLOT_RICH_BODY),
    ]
    while len(specs) < population:
        modules = {"learned_foreground_extractor", "reward_head"}
        for module in OBJECT_SLOT_MODULE_CATALOG:
            if module not in modules and rng.random() < 0.16:
                modules.add(module)
        specs.append(ObjectSlotExecutableSpec(frozenset(modules)))
    return specs


def run_object_slot_executable_search(
    *,
    strategy: str,
    seed: int,
    generations: int,
    population: int,
    agent_summary: dict[str, dict[str, Any]],
    extractor_summary: dict[str, Any],
) -> list[ObjectSlotExecutableEvaluation]:
    rng = random.Random(seed)
    specs = _initial_specs(rng, population)
    archive: dict[tuple[int, int, int, int, int, int], ObjectSlotExecutableEvaluation] = {}
    history: list[ObjectSlotExecutableEvaluation] = []

    for generation in range(generations):
        candidates = list(specs)
        for spec in specs:
            candidates.append(mutate_object_slot_executable(spec, rng))
            candidates.append(repair_object_slot_executable(spec))
            if strategy == "family_proxy":
                candidates.append(promote_family_proxy(spec))
            elif strategy == "target_proxy":
                candidates.append(promote_target_proxy(spec))
            elif strategy == "ungated_rich_proxy":
                candidates.append(promote_ungated_rich(spec))
            elif strategy == "viability_guided":
                candidates.append(promote_toward_object_slot_executable(spec))
                candidates.append(complete_object_slot_contract(spec))

        scored: list[
            tuple[float, ObjectSlotExecutableSpec, ObjectSlotExecutableEvaluation]
        ] = []
        for spec in candidates:
            evaluation = evaluate_object_slot_executable(
                spec,
                strategy=strategy,
                seed=seed,
                generation=generation,
                agent_summary=agent_summary,
                extractor_summary=extractor_summary,
                formal_verdict=python_static_object_slot_verdict(spec),
            )
            scored.append((_ranking_score(evaluation, spec, strategy, archive), spec, evaluation))
            desc = _descriptor(spec)
            if (
                desc not in archive
                or evaluation.object_slot_body_gate
                > archive[desc].object_slot_body_gate
            ):
                archive[desc] = evaluation

        scored.sort(key=lambda item: item[0], reverse=True)
        specs = [spec for _, spec, _ in scored[:population]]
        history.append(scored[0][2])
    return history


def run_seed_search(
    *,
    seed: int,
    strategies: tuple[str, ...] = OBJECT_SLOT_EXECUTABLE_STRATEGIES,
    generations: int,
    population: int,
    train_trials: int,
    test_trials: int,
    epochs: int,
    induction_calibration_trials: int,
    extractor_calibration_trials: int,
    extractor_epochs: int | None = None,
) -> dict[str, Any]:
    transfer_payload = run_experiment(
        train_trials=train_trials,
        test_trials=test_trials,
        seed=seed,
        epochs=epochs,
        induction_calibration_trials=induction_calibration_trials,
        extractor_calibration_trials=extractor_calibration_trials,
        extractor_epochs=extractor_epochs,
    )
    extractor_summary = transfer_payload["extractor_summary"]["learned_object_slots"]
    rows: list[ObjectSlotExecutableEvaluation] = []
    for strategy in strategies:
        rows.extend(
            run_object_slot_executable_search(
                strategy=strategy,
                seed=seed,
                generations=generations,
                population=population,
                agent_summary=transfer_payload["agent_summary"],
                extractor_summary=extractor_summary,
            )
        )
    return {
        "seed": seed,
        "agent_summary": transfer_payload["agent_summary"],
        "extractor_summary": transfer_payload["extractor_summary"],
        "semantic_summary": transfer_payload["semantic_summary"],
        "results": [asdict(row) for row in rows],
        "summary": summarize_object_slot_rows(rows),
    }


def run_object_slot_executable_sweep(
    *,
    strategies: tuple[str, ...] = OBJECT_SLOT_EXECUTABLE_STRATEGIES,
    seeds: int,
    generations: int,
    population: int,
    train_trials: int,
    test_trials: int,
    epochs: int,
    induction_calibration_trials: int,
    extractor_calibration_trials: int,
    base_seed: int,
    seed_values: tuple[int, ...] | None = None,
    extractor_epochs: int | None = None,
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
            extractor_calibration_trials=extractor_calibration_trials,
            extractor_epochs=extractor_epochs,
        )
        for seed in run_seeds
    ]
    return object_slot_payload(
        seed_payloads=seed_payloads,
        strategies=strategies,
        generations=generations,
        population=population,
        train_trials=train_trials,
        test_trials=test_trials,
        epochs=epochs,
        induction_calibration_trials=induction_calibration_trials,
        extractor_calibration_trials=extractor_calibration_trials,
        extractor_epochs=extractor_epochs,
        seed_values=run_seeds,
        base_seed=base_seed,
    )


ObjectSlotRow = ObjectSlotExecutableEvaluation | Mapping[str, Any]


def _row_value(row: ObjectSlotRow, key: str) -> Any:
    if isinstance(row, Mapping):
        mapping = cast(Mapping[str, Any], row)
        return mapping[key]
    return getattr(row, key)


def summarize_object_slot_rows(
    rows: Sequence[ObjectSlotRow],
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[ObjectSlotRow]] = {}
    for row in rows:
        grouped.setdefault(str(_row_value(row, "strategy")), []).append(row)

    summary: dict[str, dict[str, Any]] = {}
    for strategy, items in sorted(grouped.items()):
        final_by_seed: dict[int, ObjectSlotRow] = {}
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
                int(_row_value(item, "object_slot_body_gate")),
                int(_row_value(item, "transfer_gate_pass")),
                float(_row_value(item, "module_coverage")),
                float(_row_value(item, "semantic_pair_accuracy")),
                float(_row_value(item, "target_accuracy_high_concern")),
                float(_row_value(item, "train_return")),
            ),
        )
        gates = [int(_row_value(item, "object_slot_body_gate")) for item in finals]
        summary[strategy] = {
            "n_seeds": len(finals),
            "object_slot_body_gate_rate": mean(gates) if finals else 0.0,
            "object_slot_body_gate_rate_sd": pstdev(gates)
            if len(finals) > 1
            else 0.0,
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
            "slot_recovery_rate": mean(
                float(_row_value(item, "slot_recovery_rate")) for item in finals
            )
            if finals
            else 0.0,
            "scene_recovery_rate": mean(
                float(_row_value(item, "scene_recovery_rate")) for item in finals
            )
            if finals
            else 0.0,
            "profile_cluster_purity": mean(
                float(_row_value(item, "profile_cluster_purity")) for item in finals
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
            "profile_action_consistency": mean(
                float(_row_value(item, "profile_action_consistency"))
                for item in finals
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
    return summarize_object_slot_rows(rows)


def object_slot_payload(
    *,
    seed_payloads: list[dict[str, Any]],
    strategies: tuple[str, ...],
    generations: int,
    population: int,
    train_trials: int,
    test_trials: int,
    epochs: int,
    induction_calibration_trials: int,
    extractor_calibration_trials: int,
    extractor_epochs: int | None,
    seed_values: tuple[int, ...],
    base_seed: int,
) -> dict[str, Any]:
    return {
        "manifest": {
            "arc": "2A/2B",
            "name": "object_slot_executable_modules_2a_v2",
            "contract": "2A-v2-learned_object_slots-discovered_profiles",
            "strategies": list(strategies),
            "seeds": len(seed_values),
            "seed_values": list(seed_values),
            "generations": generations,
            "population": population,
            "train_trials": train_trials,
            "test_trials": test_trials,
            "induction_calibration_trials": induction_calibration_trials,
            "extractor_calibration_trials": extractor_calibration_trials,
            "extractor_epochs": extractor_epochs,
            "epochs": epochs,
            "base_seed": base_seed,
            "required_modules": sorted(REQUIRED_OBJECT_SLOT_EXECUTABLE_MODULES),
            "max_resource_cost": MAX_OBJECT_SLOT_RESOURCE,
        },
        "results": seed_payloads,
        "summary": summarize_seed_payloads(seed_payloads),
    }


def _manifest_text(manifest: dict[str, Any]) -> str:
    extractor_epochs = manifest.get("extractor_epochs")
    extractor_text = (
        f"{extractor_epochs} extractor epochs"
        if extractor_epochs is not None
        else "default extractor epochs"
    )
    return (
        f"{manifest['seeds']} seeds, {manifest['generations']} generations, "
        f"population {manifest['population']}, {manifest['train_trials']} train / "
        f"{manifest['test_trials']} test trials per held-out slice/seed, "
        f"{manifest['induction_calibration_trials']} profile-induction trials/seed, "
        f"{manifest['extractor_calibration_trials']} extractor calibration "
        f"images/seed, {manifest['epochs']} policy epochs, {extractor_text}. "
        f"Contract: `{manifest['contract']}`."
    )


def write_object_slot_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    manifest = payload["manifest"]
    lines = [
        "# Object-Slot Executable Modules Against Discovered 2A-v2 Transfer",
        "",
        "Date: 2026-06-22",
        "",
        (
            "Question: can Arc 2B search executable module bodies that consume "
            "the learned-object-slot plus discovered-profile 2A transfer "
            "contract, rather than the older label-free supplied-profile "
            "contract?"
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
            "| Strategy | Body gate | Transfer | Formal | Slot | Scene | Purity | "
            "Sem pair | Action template | Modules | Family | Target | Useful | "
            "Rich | Low prog | Cost | Best body | Agent | Formal source | Gate |"
        ),
        (
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
            "---:|---:|---:|---|---|---|---|"
        ),
    ]
    for strategy, stats in sorted(summary.items()):
        lines.append(
            "| {strategy} | {gate_rate:.3f} | {transfer:.3f} | {formal:.3f} | "
            "{slot:.3f} | {scene:.3f} | {purity:.3f} | {pair:.3f} | "
            "{template:.3f} | {modules:.3f} | {family:.3f} | {target:.3f} | "
            "{useful:.3f} | {rich:.3f} | {low:.3f} | {cost:.3f} | `{best}` | "
            "`{agent}` | `{source}` | {gate} |".format(
                strategy=strategy,
                gate_rate=stats["object_slot_body_gate_rate"],
                transfer=stats["transfer_gate_rate"],
                formal=stats["formal_valid_rate"],
                slot=stats["slot_recovery_rate"],
                scene=stats["scene_recovery_rate"],
                purity=stats["profile_cluster_purity"],
                pair=stats["semantic_pair_accuracy"],
                template=stats["profile_action_consistency"],
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
                "the complete learned object-slot executable body: learned "
                "foreground extraction, slot-local center search, discovered "
                "profile induction, action-template grounding, concern gating, "
                "target binding, family routing, rich composition, world-model "
                "support, and a formal guard."
            ),
            "",
            (
                "`reward_only`, `family_proxy`, `target_proxy`, and "
                "`ungated_rich_proxy` remain rejected. They can prefer return "
                "shortcuts, family routing, target binding, or rich composition, "
                "but they do not simultaneously inherit learned object-slot "
                "recovery, discovered-profile transfer, full module coverage, "
                "formal validity, and low-concern discipline."
            ),
            "",
            (
                "This result upgrades which 2A contract 2B consumes. It is "
                "not natural-image object discovery, full slot attention, or "
                "trainable neural architecture search. The fixed synthetic "
                "renderer, six-slot layout, slot-local center search, bounded "
                "module grammar, and contract-shaped feedback remain explicit "
                "scaffolds."
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
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--generations", type=int, default=8)
    parser.add_argument("--population", type=int, default=10)
    parser.add_argument("--train-trials", type=int, default=120)
    parser.add_argument("--test-trials", type=int, default=50)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--induction-calibration-trials", type=int, default=80)
    parser.add_argument("--extractor-calibration-trials", type=int, default=80)
    parser.add_argument("--extractor-epochs", type=int)
    parser.add_argument("--base-seed", type=int, default=20260622)
    parser.add_argument(
        "--seed-list",
        help="Comma-separated explicit seed list; overrides --seeds/--base-seed.",
    )
    parser.add_argument("--out", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    payload = run_object_slot_executable_sweep(
        seeds=args.seeds,
        generations=args.generations,
        population=args.population,
        train_trials=args.train_trials,
        test_trials=args.test_trials,
        epochs=args.epochs,
        induction_calibration_trials=args.induction_calibration_trials,
        extractor_calibration_trials=args.extractor_calibration_trials,
        extractor_epochs=args.extractor_epochs,
        base_seed=args.base_seed,
        seed_values=_parse_seed_list(args.seed_list),
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.report:
        write_object_slot_report(args.report, payload)

    print("=== Object-Slot Executable Modules Against 2A-v2 Transfer ===")
    for strategy, stats in sorted(payload["summary"].items()):
        print(
            f"{strategy:22s} gate={stats['object_slot_body_gate_rate']:.3f} "
            f"transfer={stats['transfer_gate_rate']:.3f} "
            f"slot={stats['slot_recovery_rate']:.3f} "
            f"modules={stats['module_coverage']:.3f} "
            f"family={stats['family_accuracy_high_concern']:.3f} "
            f"target={stats['target_accuracy_high_concern']:.3f} "
            f"low_prog={stats['low_concern_program_rate']:.3f} "
            f"agent={stats['best_empirical_agent']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
