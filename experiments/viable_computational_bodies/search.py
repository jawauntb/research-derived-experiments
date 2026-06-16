#!/usr/bin/env python3
"""Arc 2B: viability-guided computational body evolution.

This module implements a small typed architecture grammar. It is intentionally
symbolic: the purpose is to make the selection pressure and anti-cheat gates
auditable before spending Modal cycles on learned architectures.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any


MOTIFS: tuple[str, ...] = (
    "flat_encoder",
    "reward_head",
    "shortcut_reward_head",
    "tree_binder",
    "syntax_memory",
    "world_model",
    "intervention_planner",
    "role_specific_heads",
    "counterfactual_rollout",
    "formal_guard",
    "self_repair",
)

RESOURCE_COST = {
    "flat_encoder": 1,
    "reward_head": 1,
    "shortcut_reward_head": 1,
    "tree_binder": 2,
    "syntax_memory": 1,
    "world_model": 2,
    "intervention_planner": 2,
    "role_specific_heads": 2,
    "counterfactual_rollout": 2,
    "formal_guard": 1,
    "self_repair": 1,
}

DEPENDENCIES = {
    "syntax_memory": {"tree_binder"},
    "intervention_planner": {"world_model"},
    "role_specific_heads": {"tree_binder"},
    "counterfactual_rollout": {"world_model", "intervention_planner"},
    "self_repair": {"formal_guard"},
}

TARGET_BODY = frozenset(
    {
        "flat_encoder",
        "reward_head",
        "tree_binder",
        "syntax_memory",
        "world_model",
        "intervention_planner",
        "role_specific_heads",
        "formal_guard",
    }
)

STRATEGIES = ("accuracy_only", "novelty_only", "viability_guided")
MAX_RESOURCE = 12


@dataclass(frozen=True)
class ArchitectureSpec:
    motifs: frozenset[str]

    @property
    def key(self) -> str:
        return "+".join(sorted(self.motifs))


@dataclass(frozen=True)
class Evaluation:
    architecture: str
    strategy: str
    seed: int
    generation: int
    train_return: float
    concerned_syntax_score: float
    parse_congruity: float
    subtree_facilitation: float
    intervention_invention: float
    self_world_split: float
    anti_cheat: float
    resource_cost: int
    formal_valid: int
    viable: int
    violations: tuple[str, ...]


def resource_cost(spec: ArchitectureSpec) -> int:
    return sum(RESOURCE_COST[motif] for motif in spec.motifs)


def static_violations(spec: ArchitectureSpec) -> tuple[str, ...]:
    violations: list[str] = []
    for motif, deps in DEPENDENCIES.items():
        if motif in spec.motifs:
            missing = sorted(deps - spec.motifs)
            if missing:
                violations.append(f"{motif}_missing_{'+'.join(missing)}")
    if "shortcut_reward_head" in spec.motifs and "formal_guard" not in spec.motifs:
        violations.append("shortcut_without_formal_guard")
    if resource_cost(spec) > MAX_RESOURCE:
        violations.append("resource_over_budget")
    if "flat_encoder" not in spec.motifs:
        violations.append("missing_input_body")
    return tuple(violations)


def _has(spec: ArchitectureSpec, *motifs: str) -> bool:
    return all(motif in spec.motifs for motif in motifs)


def evaluate_architecture(
    spec: ArchitectureSpec,
    *,
    strategy: str,
    seed: int,
    generation: int,
) -> Evaluation:
    violations = static_violations(spec)
    formal_valid = int(not violations)
    cost = resource_cost(spec)
    motifs = spec.motifs

    train_return = 0.35
    if "reward_head" in motifs:
        train_return += 0.25
    if "shortcut_reward_head" in motifs:
        train_return += 0.30
    if "world_model" in motifs:
        train_return += 0.08
    if "intervention_planner" in motifs:
        train_return += 0.06
    if "tree_binder" in motifs:
        train_return += 0.05
    train_return -= max(0, cost - 8) * 0.015
    train_return = max(0.0, min(1.0, train_return))

    parse_congruity = 0.15 + 0.55 * _has(spec, "tree_binder") + 0.25 * _has(
        spec, "tree_binder", "syntax_memory"
    )
    subtree_facilitation = 0.20 + 0.70 * _has(spec, "tree_binder")
    intervention_invention = 0.10 + 0.45 * _has(
        spec, "world_model", "intervention_planner"
    ) + 0.30 * _has(spec, "counterfactual_rollout")
    self_world_split = 0.20 + 0.30 * _has(
        spec, "world_model", "role_specific_heads"
    ) + 0.30 * _has(spec, "syntax_memory", "role_specific_heads")
    anti_cheat = 0.95
    if "shortcut_reward_head" in motifs:
        anti_cheat = 0.25 if "formal_guard" not in motifs else 0.70
    elif "formal_guard" not in motifs:
        anti_cheat = 0.68
    if formal_valid == 0:
        anti_cheat = min(anti_cheat, 0.40)

    gate_scores = (
        min(1.0, parse_congruity),
        min(1.0, subtree_facilitation),
        min(1.0, intervention_invention),
        min(1.0, self_world_split),
        min(1.0, anti_cheat),
    )
    concerned_syntax_score = mean(gate_scores)
    viable = int(
        formal_valid
        and cost <= MAX_RESOURCE
        and parse_congruity >= 0.85
        and subtree_facilitation >= 0.85
        and intervention_invention >= 0.55
        and self_world_split >= 0.75
        and "formal_guard" in motifs
        and anti_cheat >= 0.70
    )

    return Evaluation(
        architecture=spec.key,
        strategy=strategy,
        seed=seed,
        generation=generation,
        train_return=train_return,
        concerned_syntax_score=concerned_syntax_score,
        parse_congruity=min(1.0, parse_congruity),
        subtree_facilitation=min(1.0, subtree_facilitation),
        intervention_invention=min(1.0, intervention_invention),
        self_world_split=min(1.0, self_world_split),
        anti_cheat=min(1.0, anti_cheat),
        resource_cost=cost,
        formal_valid=formal_valid,
        viable=viable,
        violations=violations,
    )


def mutate(spec: ArchitectureSpec, rng: random.Random) -> ArchitectureSpec:
    motifs = set(spec.motifs)
    motif = rng.choice(MOTIFS)
    if motif in motifs and motif not in {"flat_encoder"}:
        motifs.remove(motif)
    else:
        motifs.add(motif)
    return ArchitectureSpec(frozenset(motifs))


def repair_dependencies(spec: ArchitectureSpec) -> ArchitectureSpec:
    motifs = set(spec.motifs)
    changed = True
    while changed:
        changed = False
        for motif, deps in DEPENDENCIES.items():
            if motif in motifs:
                missing = deps - motifs
                if missing:
                    motifs.update(missing)
                    changed = True
    if "shortcut_reward_head" in motifs:
        motifs.add("formal_guard")
    motifs.add("flat_encoder")
    return ArchitectureSpec(frozenset(motifs))


def promote_toward_target(spec: ArchitectureSpec) -> ArchitectureSpec:
    missing = sorted(TARGET_BODY - spec.motifs)
    if not missing:
        return spec
    motifs = set(spec.motifs)
    motifs.add(missing[0])
    return repair_dependencies(ArchitectureSpec(frozenset(motifs)))


def descriptor(spec: ArchitectureSpec) -> tuple[int, int, int, int]:
    return (
        int("tree_binder" in spec.motifs),
        int("intervention_planner" in spec.motifs),
        int("role_specific_heads" in spec.motifs),
        min(3, resource_cost(spec) // 4),
    )


def novelty(spec: ArchitectureSpec, archive: dict[tuple[int, int, int, int], Evaluation]) -> float:
    desc = descriptor(spec)
    if desc not in archive:
        return 1.0
    return 0.1


def _ranking_score(
    evaluation: Evaluation,
    spec: ArchitectureSpec,
    strategy: str,
    archive: dict[tuple[int, int, int, int], Evaluation],
) -> float:
    if strategy == "accuracy_only":
        return evaluation.train_return
    if strategy == "novelty_only":
        return novelty(spec, archive) + 0.10 * evaluation.concerned_syntax_score
    if strategy == "viability_guided":
        return (
            2.0 * evaluation.viable
            + evaluation.concerned_syntax_score
            + 0.15 * novelty(spec, archive)
            - 0.02 * max(0, evaluation.resource_cost - 9)
        )
    raise KeyError(strategy)


def run_search(
    *,
    strategy: str,
    seed: int,
    generations: int,
    population: int,
) -> list[Evaluation]:
    rng = random.Random(seed)
    specs = [
        ArchitectureSpec(frozenset({"flat_encoder", "reward_head"})),
        ArchitectureSpec(frozenset({"flat_encoder", "reward_head", "shortcut_reward_head"})),
        ArchitectureSpec(frozenset({"flat_encoder", "reward_head", "tree_binder"})),
    ]
    while len(specs) < population:
        motifs = {"flat_encoder", "reward_head"}
        for motif in MOTIFS:
            if motif not in motifs and rng.random() < 0.20:
                motifs.add(motif)
        specs.append(ArchitectureSpec(frozenset(motifs)))

    archive: dict[tuple[int, int, int, int], Evaluation] = {}
    history: list[Evaluation] = []
    for generation in range(generations):
        candidates = list(specs)
        for spec in specs:
            candidates.append(mutate(spec, rng))
            if strategy == "viability_guided":
                candidates.append(promote_toward_target(spec))
                candidates.append(repair_dependencies(spec))

        scored: list[tuple[float, ArchitectureSpec, Evaluation]] = []
        for spec in candidates:
            evaluation = evaluate_architecture(
                spec,
                strategy=strategy,
                seed=seed,
                generation=generation,
            )
            scored.append(
                (_ranking_score(evaluation, spec, strategy, archive), spec, evaluation)
            )
            desc = descriptor(spec)
            if desc not in archive or evaluation.concerned_syntax_score > archive[desc].concerned_syntax_score:
                archive[desc] = evaluation

        scored.sort(key=lambda item: item[0], reverse=True)
        specs = [spec for _, spec, _ in scored[:population]]
        history.append(scored[0][2])
    return history


def run_sweep(
    *,
    strategies: tuple[str, ...] = STRATEGIES,
    seeds: int,
    generations: int,
    population: int,
    base_seed: int,
) -> list[Evaluation]:
    rows: list[Evaluation] = []
    for strategy in strategies:
        for idx in range(seeds):
            rows.extend(
                run_search(
                    strategy=strategy,
                    seed=base_seed + idx,
                    generations=generations,
                    population=population,
                )
            )
    return rows


def summarize(rows: list[Evaluation]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[Evaluation]] = {}
    for row in rows:
        grouped.setdefault(row.strategy, []).append(row)

    summary: dict[str, dict[str, Any]] = {}
    for strategy, items in grouped.items():
        final_by_seed: dict[int, Evaluation] = {}
        for item in items:
            if item.seed not in final_by_seed or item.generation > final_by_seed[item.seed].generation:
                final_by_seed[item.seed] = item
        finals = list(final_by_seed.values())
        summary[strategy] = {
            "n_seeds": len(finals),
            "final_viable_rate": mean(item.viable for item in finals) if finals else 0.0,
            "final_concerned_syntax_score": mean(item.concerned_syntax_score for item in finals) if finals else 0.0,
            "final_train_return": mean(item.train_return for item in finals) if finals else 0.0,
            "formal_valid_rate": mean(item.formal_valid for item in finals) if finals else 0.0,
            "best_architecture": max(
                finals,
                key=lambda item: (item.viable, item.concerned_syntax_score, item.train_return),
            ).architecture
            if finals
            else "",
            "gate_pass": bool(
                finals
                and mean(item.viable for item in finals) >= 0.75
                and mean(item.concerned_syntax_score for item in finals) >= 0.80
            ),
        }
    return summary


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Viable Computational Bodies Pilot",
        "",
        "Date: 2026-06-16",
        "",
        "Question: does viability-guided architecture evolution find syntax-bearing computational bodies more reliably than reward-only or novelty-only selection?",
        "",
        "## Gate Summary",
        "",
        "| Strategy | Viable rate | Syntax score | Train return | Formal valid | Best architecture | Gate |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for strategy, stats in sorted(payload["summary"].items()):
        lines.append(
            "| {strategy} | {viable:.3f} | {syntax:.3f} | {train:.3f} | {formal:.3f} | `{best}` | {gate} |".format(
                strategy=strategy,
                viable=stats["final_viable_rate"],
                syntax=stats["final_concerned_syntax_score"],
                train=stats["final_train_return"],
                formal=stats["formal_valid_rate"],
                best=stats["best_architecture"],
                gate="PASS" if stats["gate_pass"] else "fail",
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The pilot is a search-regime sanity check. The key anti-cheat distinction is that `accuracy_only` can prefer shortcut reward heads that look strong on train return but fail formal and concerned-syntax gates. `viability_guided` is accepted only if it repeatedly discovers bodies with tree binding, syntax memory, role-specific heads, world modeling, intervention planning, and formal guards under the resource budget.",
            "",
            "Raw JSON remains local under `artifacts/viable_computational_bodies/`.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=12)
    parser.add_argument("--generations", type=int, default=18)
    parser.add_argument("--population", type=int, default=18)
    parser.add_argument("--base-seed", type=int, default=20260616)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    rows = run_sweep(
        seeds=args.seeds,
        generations=args.generations,
        population=args.population,
        base_seed=args.base_seed,
    )
    payload = {
        "manifest": {
            "arc": "2B",
            "name": "viable_computational_bodies",
            "seeds": args.seeds,
            "generations": args.generations,
            "population": args.population,
            "base_seed": args.base_seed,
            "strategies": list(STRATEGIES),
        },
        "summary": summarize(rows),
        "results": [asdict(row) for row in rows],
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.report:
        write_report(args.report, payload)

    print("=== Viable Computational Bodies Summary ===")
    for strategy, stats in sorted(payload["summary"].items()):
        print(
            f"{strategy:18s} viable={stats['final_viable_rate']:.3f} "
            f"syntax={stats['final_concerned_syntax_score']:.3f} "
            f"train={stats['final_train_return']:.3f} "
            f"gate={stats['gate_pass']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
