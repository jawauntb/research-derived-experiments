#!/usr/bin/env python3
"""Search 2B program bodies against the frozen 2A-v1 empirical contract.

The earlier 2B search used symbolic proxy scores for intervention invention.
This bridge evaluates searched motif bodies against the actual Arc 2A
intervention-invention gate by mapping each body to the empirical control it
can express: surface shortcut, random probe, concern-only, target-only, or the
full concerned program inventor.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from experiments.concerned_syntax.intervention_invention import (
    run_experiment,
    run_role_transfer_experiment,
)
from experiments.viable_computational_bodies.haskell_gate import (
    HaskellGateUnavailable,
    HaskellVerdict,
    Runner,
    load_motif_verdict,
)

PROGRAM_BODY_MOTIFS: tuple[str, ...] = (
    "vector_surface_encoder",
    "flat_encoder",
    "reward_head",
    "world_model",
    "intervention_planner",
    "concern_policy",
    "causal_binding_head",
    "syntax_memory",
    "calibration_guard",
    "formal_guard",
    "role_specific_heads",
    "counterfactual_rollout",
    "shortcut_reward_head",
)

PROGRAM_BODY_COST = {
    "vector_surface_encoder": 2,
    "flat_encoder": 1,
    "reward_head": 1,
    "world_model": 2,
    "intervention_planner": 2,
    "concern_policy": 1,
    "causal_binding_head": 2,
    "syntax_memory": 1,
    "calibration_guard": 1,
    "formal_guard": 1,
    "role_specific_heads": 2,
    "counterfactual_rollout": 2,
    "shortcut_reward_head": 1,
}

PROGRAM_BODY_DEPENDENCIES = {
    "intervention_planner": {"world_model"},
    "concern_policy": {"world_model"},
    "causal_binding_head": {"vector_surface_encoder"},
    "syntax_memory": {"causal_binding_head"},
    "calibration_guard": {"concern_policy"},
    "role_specific_heads": {"causal_binding_head"},
    "counterfactual_rollout": {"world_model", "intervention_planner"},
}

TARGET_PROGRAM_BODY = frozenset(
    {
        "vector_surface_encoder",
        "flat_encoder",
        "reward_head",
        "world_model",
        "intervention_planner",
        "concern_policy",
        "causal_binding_head",
        "syntax_memory",
        "calibration_guard",
        "formal_guard",
    }
)

PROGRAM_BODY_STRATEGIES = ("reward_only", "syntax_proxy", "viability_guided")
MAX_PROGRAM_BODY_RESOURCE = 14


@dataclass(frozen=True)
class ProgramBodySpec:
    motifs: frozenset[str]

    @property
    def key(self) -> str:
        return "+".join(sorted(self.motifs))


@dataclass(frozen=True)
class ProgramBodyEvaluation:
    architecture: str
    strategy: str
    seed: int
    generation: int
    empirical_agent: str
    train_return: float
    parse_accuracy_high_concern: float
    action_accuracy: float
    subtree_accuracy: float
    high_concern_probe_rate: float
    low_concern_probe_rate: float
    target_accuracy_high_concern: float
    useful_program_rate_high_concern: float
    object_extraction_rate: float
    empirical_gate_pass: int
    formal_valid: int
    formal_source: str
    resource_cost: int
    body_gate: int
    violations: tuple[str, ...]


def program_body_resource_cost(spec: ProgramBodySpec) -> int:
    return sum(PROGRAM_BODY_COST[motif] for motif in spec.motifs)


def program_body_violations(spec: ProgramBodySpec) -> tuple[str, ...]:
    motifs = spec.motifs
    violations: list[str] = []
    for motif, deps in PROGRAM_BODY_DEPENDENCIES.items():
        if motif in motifs:
            missing = sorted(deps - motifs)
            if missing:
                violations.append(f"{motif}_missing_{'+'.join(missing)}")
    if "shortcut_reward_head" in motifs and "formal_guard" not in motifs:
        violations.append("shortcut_without_formal_guard")
    if "concern_policy" in motifs and "calibration_guard" not in motifs:
        violations.append("concern_without_calibration_guard")
    if program_body_resource_cost(spec) > MAX_PROGRAM_BODY_RESOURCE:
        violations.append("program_body_resource_over_budget")
    if "vector_surface_encoder" not in motifs and "flat_encoder" not in motifs:
        violations.append("missing_input_body")
    return tuple(violations)


def python_static_program_body_verdict(spec: ProgramBodySpec) -> HaskellVerdict:
    violations = program_body_violations(spec)
    return HaskellVerdict(
        formal_valid=not violations,
        resource_cost=program_body_resource_cost(spec),
        violations=violations,
        formal_source="python_static",
    )


class ProgramBodyFormalOracle:
    """Cached formal verdict source for searched motif bodies."""

    def __init__(
        self,
        *,
        mode: str = "auto",
        runner: Runner | None = None,
    ) -> None:
        if mode not in {"auto", "haskell", "python_static"}:
            raise ValueError(f"unknown formal mode: {mode}")
        self.mode = mode
        self.runner = runner
        self._haskell_unavailable = False
        self._cache: dict[str, HaskellVerdict] = {}

    def verdict(self, spec: ProgramBodySpec) -> HaskellVerdict:
        cached = self._cache.get(spec.key)
        if cached is not None:
            return cached

        if self.mode != "python_static" and not self._haskell_unavailable:
            try:
                verdict = load_motif_verdict(spec.motifs, runner=self.runner)
            except HaskellGateUnavailable:
                if self.mode == "haskell":
                    raise
                self._haskell_unavailable = True
            else:
                self._cache[spec.key] = verdict
                return verdict

        verdict = python_static_program_body_verdict(spec)
        self._cache[spec.key] = verdict
        return verdict


def _has(spec: ProgramBodySpec, *motifs: str) -> bool:
    return all(motif in spec.motifs for motif in motifs)


def empirical_agent_for_body(spec: ProgramBodySpec) -> str:
    """Map body motifs to the 2A-v1 empirical control the body can express."""

    has_concern = _has(spec, "concern_policy", "calibration_guard")
    has_target = _has(
        spec,
        "vector_surface_encoder",
        "causal_binding_head",
        "intervention_planner",
    )
    has_program = "intervention_planner" in spec.motifs
    if has_concern and has_target:
        return "concerned_program_inventor"
    if has_concern:
        return "concern_without_target"
    if has_target:
        return "target_without_concern"
    if has_program:
        return "random_program_probe"
    return "surface_program_shortcut"


def _train_return(spec: ProgramBodySpec, agent_stats: dict[str, Any]) -> float:
    value = 0.35 + 0.55 * float(agent_stats["action_accuracy"])
    if "shortcut_reward_head" in spec.motifs:
        value += 0.16
    if "reward_head" in spec.motifs:
        value += 0.05
    value -= 0.01 * max(0, program_body_resource_cost(spec) - 10)
    return max(0.0, min(1.0, value))


def evaluate_program_body(
    spec: ProgramBodySpec,
    *,
    strategy: str,
    seed: int,
    generation: int,
    agent_summary: dict[str, dict[str, Any]],
    formal_verdict: HaskellVerdict | None = None,
) -> ProgramBodyEvaluation:
    agent = empirical_agent_for_body(spec)
    stats = agent_summary[agent]
    verdict = formal_verdict or python_static_program_body_verdict(spec)
    formal_valid = int(verdict.formal_valid)
    cost = verdict.resource_cost
    empirical_gate = int(bool(stats["gate_pass"]))
    body_gate = int(
        empirical_gate
        and formal_valid
        and cost <= MAX_PROGRAM_BODY_RESOURCE
        and "formal_guard" in spec.motifs
        and "calibration_guard" in spec.motifs
    )
    return ProgramBodyEvaluation(
        architecture=spec.key,
        strategy=strategy,
        seed=seed,
        generation=generation,
        empirical_agent=agent,
        train_return=_train_return(spec, stats),
        parse_accuracy_high_concern=float(stats["parse_accuracy_high_concern"]),
        action_accuracy=float(stats["action_accuracy"]),
        subtree_accuracy=float(stats["subtree_accuracy"]),
        high_concern_probe_rate=float(stats["high_concern_probe_rate"]),
        low_concern_probe_rate=float(stats["low_concern_probe_rate"]),
        target_accuracy_high_concern=float(stats["target_accuracy_high_concern"]),
        useful_program_rate_high_concern=float(stats["useful_program_rate_high_concern"]),
        object_extraction_rate=float(stats["object_extraction_rate"]),
        empirical_gate_pass=empirical_gate,
        formal_valid=formal_valid,
        formal_source=verdict.formal_source,
        resource_cost=cost,
        body_gate=body_gate,
        violations=verdict.violations,
    )


def repair_program_body(spec: ProgramBodySpec) -> ProgramBodySpec:
    motifs = set(spec.motifs)
    changed = True
    while changed:
        changed = False
        for motif, deps in PROGRAM_BODY_DEPENDENCIES.items():
            if motif in motifs:
                missing = deps - motifs
                if missing:
                    motifs.update(missing)
                    changed = True
    if "concern_policy" in motifs:
        motifs.add("calibration_guard")
    if "shortcut_reward_head" in motifs:
        motifs.add("formal_guard")
    if "intervention_planner" in motifs:
        motifs.add("world_model")
    motifs.add("vector_surface_encoder")
    motifs.add("reward_head")
    return ProgramBodySpec(frozenset(motifs))


def promote_toward_program_body(spec: ProgramBodySpec) -> ProgramBodySpec:
    missing = sorted(TARGET_PROGRAM_BODY - spec.motifs)
    if not missing:
        return spec
    motifs = set(spec.motifs)
    motifs.add(missing[0])
    return repair_program_body(ProgramBodySpec(frozenset(motifs)))


def complete_program_contract(spec: ProgramBodySpec) -> ProgramBodySpec:
    """Complete partial concern/target bodies into the frozen 2A-v1 contract."""

    motifs = set(spec.motifs)
    has_target_side = {
        "intervention_planner",
        "causal_binding_head",
    } <= motifs
    has_concern_side = "concern_policy" in motifs
    if has_target_side or has_concern_side:
        motifs.update(TARGET_PROGRAM_BODY)
    return repair_program_body(ProgramBodySpec(frozenset(motifs)))


def mutate_program_body(spec: ProgramBodySpec, rng: random.Random) -> ProgramBodySpec:
    motifs = set(spec.motifs)
    motif = rng.choice(PROGRAM_BODY_MOTIFS)
    if motif in motifs and motif not in {"vector_surface_encoder", "reward_head"}:
        motifs.remove(motif)
    else:
        motifs.add(motif)
    return ProgramBodySpec(frozenset(motifs))


def _descriptor(spec: ProgramBodySpec) -> tuple[int, int, int, int]:
    return (
        int("concern_policy" in spec.motifs),
        int("causal_binding_head" in spec.motifs),
        int("intervention_planner" in spec.motifs),
        min(3, program_body_resource_cost(spec) // 4),
    )


def _novelty(
    spec: ProgramBodySpec,
    archive: dict[tuple[int, int, int, int], ProgramBodyEvaluation],
) -> float:
    return 1.0 if _descriptor(spec) not in archive else 0.1


def _ranking_score(
    evaluation: ProgramBodyEvaluation,
    spec: ProgramBodySpec,
    strategy: str,
    archive: dict[tuple[int, int, int, int], ProgramBodyEvaluation],
) -> float:
    if strategy == "reward_only":
        return evaluation.train_return
    if strategy == "syntax_proxy":
        return (
            evaluation.parse_accuracy_high_concern
            + evaluation.target_accuracy_high_concern
            + 0.20 * _novelty(spec, archive)
        )
    if strategy == "viability_guided":
        return (
            3.0 * evaluation.body_gate
            + 1.2 * evaluation.empirical_gate_pass
            + evaluation.parse_accuracy_high_concern
            + evaluation.target_accuracy_high_concern
            + evaluation.useful_program_rate_high_concern
            + 0.25 * _novelty(spec, archive)
            - 0.02 * max(0, evaluation.resource_cost - 11)
            - 0.40 * (1 - evaluation.formal_valid)
        )
    raise KeyError(strategy)


def run_program_body_search(
    *,
    strategy: str,
    seed: int,
    generations: int,
    population: int,
    agent_summary: dict[str, dict[str, Any]],
    formal_oracle: ProgramBodyFormalOracle | None = None,
) -> list[ProgramBodyEvaluation]:
    rng = random.Random(seed)
    oracle = formal_oracle or ProgramBodyFormalOracle(mode="auto")
    specs = [
        ProgramBodySpec(frozenset({"vector_surface_encoder", "reward_head"})),
        ProgramBodySpec(
            frozenset(
                {
                    "vector_surface_encoder",
                    "reward_head",
                    "shortcut_reward_head",
                }
            )
        ),
        ProgramBodySpec(
            frozenset(
                {
                    "vector_surface_encoder",
                    "reward_head",
                    "intervention_planner",
                    "causal_binding_head",
                }
            )
        ),
    ]
    while len(specs) < population:
        motifs = {"vector_surface_encoder", "reward_head"}
        for motif in PROGRAM_BODY_MOTIFS:
            if motif not in motifs and rng.random() < 0.18:
                motifs.add(motif)
        specs.append(ProgramBodySpec(frozenset(motifs)))

    archive: dict[tuple[int, int, int, int], ProgramBodyEvaluation] = {}
    history: list[ProgramBodyEvaluation] = []
    for generation in range(generations):
        candidates = list(specs)
        for spec in specs:
            candidates.append(mutate_program_body(spec, rng))
            if strategy == "viability_guided":
                candidates.append(repair_program_body(spec))
                candidates.append(promote_toward_program_body(spec))
                candidates.append(complete_program_contract(spec))

        scored: list[tuple[float, ProgramBodySpec, ProgramBodyEvaluation]] = []
        for spec in candidates:
            evaluation = evaluate_program_body(
                spec,
                strategy=strategy,
                seed=seed,
                generation=generation,
                agent_summary=agent_summary,
                formal_verdict=oracle.verdict(spec),
            )
            scored.append(
                (_ranking_score(evaluation, spec, strategy, archive), spec, evaluation)
            )
            desc = _descriptor(spec)
            if desc not in archive or evaluation.body_gate > archive[desc].body_gate:
                archive[desc] = evaluation

        scored.sort(key=lambda item: item[0], reverse=True)
        specs = [spec for _, spec, _ in scored[:population]]
        history.append(scored[0][2])
    return history


def run_coupled_sweep(
    *,
    strategies: tuple[str, ...] = PROGRAM_BODY_STRATEGIES,
    seeds: int,
    generations: int,
    population: int,
    train_trials: int,
    test_trials: int,
    epochs: int,
    base_seed: int,
    role_transfer_kind: str | None = None,
    formal_mode: str = "auto",
    seed_values: tuple[int, ...] | None = None,
) -> dict[str, Any]:
    rows: list[ProgramBodyEvaluation] = []
    transfer_summary: dict[str, dict[str, Any]] | None = None
    empirical_payloads: list[dict[str, Any]] = []
    formal_oracle = ProgramBodyFormalOracle(mode=formal_mode)
    run_seeds = seed_values or tuple(base_seed + idx for idx in range(seeds))
    for seed in run_seeds:
        payload = run_experiment(
            train_trials=train_trials,
            test_trials=test_trials,
            seed=seed,
            epochs=epochs,
        )
        empirical_payloads.append(
            {
                "seed": seed,
                "agent_summary": payload["agent_summary"],
            }
        )
        for strategy in strategies:
            rows.extend(
                run_program_body_search(
                    strategy=strategy,
                    seed=seed,
                    generations=generations,
                    population=population,
                    agent_summary=payload["agent_summary"],
                    formal_oracle=formal_oracle,
                )
            )

    if role_transfer_kind is not None:
        transfer_payload = run_role_transfer_experiment(
            train_trials=train_trials,
            test_trials=test_trials,
            seed=base_seed,
            epochs=epochs,
            heldout_kind=role_transfer_kind,
        )
        transfer_summary = transfer_payload["agent_summary"]

    return {
        "manifest": {
            "arc": "2A/2B",
            "name": "program_body_search_against_2a_v1",
            "contract": "2A-v1-pixels-observe_pair",
            "strategies": list(strategies),
            "seeds": len(run_seeds),
            "seed_values": list(run_seeds),
            "generations": generations,
            "population": population,
            "train_trials": train_trials,
            "test_trials": test_trials,
            "epochs": epochs,
            "base_seed": base_seed,
            "role_transfer_kind": role_transfer_kind,
            "formal_mode": formal_mode,
        },
        "summary": summarize_program_bodies(rows),
        "role_transfer_summary": transfer_summary,
        "empirical_payloads": empirical_payloads,
        "results": [asdict(row) for row in rows],
    }


def summarize_program_bodies(
    rows: list[ProgramBodyEvaluation],
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[ProgramBodyEvaluation]] = {}
    for row in rows:
        grouped.setdefault(row.strategy, []).append(row)

    summary: dict[str, dict[str, Any]] = {}
    for strategy, items in sorted(grouped.items()):
        final_by_seed: dict[int, ProgramBodyEvaluation] = {}
        for item in items:
            if item.seed not in final_by_seed or item.generation > final_by_seed[item.seed].generation:
                final_by_seed[item.seed] = item
        finals = list(final_by_seed.values())
        best = max(
            finals,
            key=lambda item: (
                item.body_gate,
                item.empirical_gate_pass,
                item.target_accuracy_high_concern,
                item.train_return,
            ),
        )
        body_gate_values = [item.body_gate for item in finals]
        summary[strategy] = {
            "n_seeds": len(finals),
            "body_gate_rate": mean(body_gate_values) if finals else 0.0,
            "body_gate_rate_sd": pstdev(body_gate_values) if len(finals) > 1 else 0.0,
            "empirical_gate_rate": mean(item.empirical_gate_pass for item in finals) if finals else 0.0,
            "formal_valid_rate": mean(item.formal_valid for item in finals) if finals else 0.0,
            "formal_haskell_rate": mean(item.formal_source == "haskell" for item in finals) if finals else 0.0,
            "formal_source": "+".join(sorted({item.formal_source for item in finals})),
            "target_accuracy_high_concern": mean(item.target_accuracy_high_concern for item in finals) if finals else 0.0,
            "useful_program_rate_high_concern": mean(item.useful_program_rate_high_concern for item in finals) if finals else 0.0,
            "low_concern_probe_rate": mean(item.low_concern_probe_rate for item in finals) if finals else 0.0,
            "train_return": mean(item.train_return for item in finals) if finals else 0.0,
            "resource_cost": mean(item.resource_cost for item in finals) if finals else 0.0,
            "best_architecture": best.architecture if finals else "",
            "best_empirical_agent": best.empirical_agent if finals else "",
            "gate_pass": bool(finals and mean(body_gate_values) >= 0.75),
        }
    return summary


def write_coupled_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    manifest = payload["manifest"]
    lines = [
        "# Program-Body Search Against 2A-v1",
        "",
        "Date: 2026-06-16",
        "",
        (
            "Question: can Arc 2B search discover formal, resource-bounded "
            "bodies whose motifs express the current Arc 2A intervention-"
            "invention contract?"
        ),
        "",
        (
            "Manifest: {seeds} seeds, {generations} generations, population "
            "{population}, {train_trials} train / {test_trials} test 2A trials, "
            "{epochs} epochs. Contract: `{contract}`."
        ).format(**manifest),
        "",
        "## Body Gate Summary",
        "",
        (
            "| Strategy | Body gate | Empirical gate | Formal valid | Haskell | "
            "Target high | Useful high | Low probe | Return | Cost | "
            "Best body | Agent | Formal source | Gate |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|",
    ]
    for strategy, stats in sorted(summary.items()):
        lines.append(
            "| {strategy} | {body:.3f} | {empirical:.3f} | {formal:.3f} | "
            "{haskell:.3f} | "
            "{target:.3f} | {useful:.3f} | {low:.3f} | {ret:.3f} | "
            "{cost:.3f} | `{best}` | `{agent}` | `{source}` | {gate} |".format(
                strategy=strategy,
                body=stats["body_gate_rate"],
                empirical=stats["empirical_gate_rate"],
                formal=stats["formal_valid_rate"],
                haskell=stats["formal_haskell_rate"],
                target=stats["target_accuracy_high_concern"],
                useful=stats["useful_program_rate_high_concern"],
                low=stats["low_concern_probe_rate"],
                ret=stats["train_return"],
                cost=stats["resource_cost"],
                best=stats["best_architecture"],
                agent=stats["best_empirical_agent"],
                source=stats["formal_source"],
                gate="PASS" if stats["gate_pass"] else "fail",
            )
        )

    transfer_summary = payload.get("role_transfer_summary")
    if transfer_summary:
        lines.extend(
            [
                "",
                "## 2A Role-Transfer Stress",
                "",
                (
                    "Held-out role kind: "
                    f"`{manifest['role_transfer_kind']}`. This is a stress "
                    "test, not yet a required body gate."
                ),
                "",
                "| Agent | Parse high | Action | Low probe | Target high | Useful high | Gate |",
                "|---|---:|---:|---:|---:|---:|---|",
            ]
        )
        for agent, stats in sorted(transfer_summary.items()):
            lines.append(
                "| {agent} | {parse:.3f} | {action:.3f} | {low:.3f} | "
                "{target:.3f} | {useful:.3f} | {gate} |".format(
                    agent=agent,
                    parse=stats["parse_accuracy_high_concern"],
                    action=stats["action_accuracy"],
                    low=stats["low_concern_probe_rate"],
                    target=stats["target_accuracy_high_concern"],
                    useful=stats["useful_program_rate_high_concern"],
                    gate="PASS" if stats["gate_pass"] else "fail",
                )
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "This is the first coupled Arc 2A/2B contract. The empirical "
                "2A-v1 gate is frozen as pixels plus an `observe_pair(a,b)` "
                "program menu. A searched body passes only if its motif set "
                "can express the empirical concerned-program-inventor control "
                "and also satisfies formal body constraints. When Cabal is "
                "available, candidate motif sets are checked by the Haskell "
                "ontology through `ontology-check --motifs`; otherwise the "
                "report records the explicit `python_static` fallback."
            ),
            "",
            (
                "`reward_only` is a body-side shortcut control. `syntax_proxy` "
                "can chase parse/target metrics without the full viability "
                "contract. `viability_guided` is accepted only if search "
                "reconstructs concern policy, calibration, target selection, "
                "program planning, binding, and formal guard motifs together."
            ),
            "",
            "Raw JSON remains local under `artifacts/viable_computational_bodies/`.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--generations", type=int, default=14)
    parser.add_argument("--population", type=int, default=14)
    parser.add_argument("--train-trials", type=int, default=650)
    parser.add_argument("--test-trials", type=int, default=260)
    parser.add_argument("--epochs", type=int, default=45)
    parser.add_argument("--base-seed", type=int, default=20260616)
    parser.add_argument(
        "--seed-list",
        help="Comma-separated explicit seed list; overrides --seeds/--base-seed.",
    )
    parser.add_argument("--role-transfer-kind", default="food_trap")
    parser.add_argument(
        "--formal-mode",
        choices=("auto", "haskell", "python_static"),
        default="auto",
    )
    parser.add_argument("--out", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    payload = run_coupled_sweep(
        seeds=args.seeds,
        generations=args.generations,
        population=args.population,
        train_trials=args.train_trials,
        test_trials=args.test_trials,
        epochs=args.epochs,
        base_seed=args.base_seed,
        role_transfer_kind=args.role_transfer_kind,
        formal_mode=args.formal_mode,
        seed_values=_parse_seed_list(args.seed_list),
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.report:
        write_coupled_report(args.report, payload)

    print("=== Program Body Search Against 2A-v1 ===")
    for strategy, stats in sorted(payload["summary"].items()):
        print(
            f"{strategy:16s} body_gate={stats['body_gate_rate']:.3f} "
            f"target={stats['target_accuracy_high_concern']:.3f} "
            f"useful={stats['useful_program_rate_high_concern']:.3f} "
            f"low_probe={stats['low_concern_probe_rate']:.3f} "
            f"gate={stats['gate_pass']}"
        )
    return 0


def _parse_seed_list(value: str | None) -> tuple[int, ...] | None:
    if not value:
        return None
    return tuple(int(item.strip()) for item in value.split(",") if item.strip())


if __name__ == "__main__":
    raise SystemExit(main())
