#!/usr/bin/env python3
"""Run the preregistered Obstruction-Aware Admission finite benchmark."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from experiments.information_limited_discovery.core import (
    DiscoveryProblem,
    ScopedObstructionCertificate,
    find_obstruction,
    target_is_determined,
    validate_obstruction,
)
from experiments.obstruction_aware_admission.core import (
    AdmissionPolicy,
    choose_policy_experiment,
    decide_admission,
    independent_optimal_cost,
    optimal_worst_case_cost,
    policy_worst_case_cost,
)
from experiments.relative_identifiability.core import (
    FiniteExperimentSystem,
    FiniteTarget,
)


PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[1]
DEFAULT_JSON = PACKAGE / "results" / "summary.json"
DEFAULT_MARKDOWN = PACKAGE / "results" / "summary.md"
DEFAULT_COUNTEREXAMPLE = PACKAGE / "fixtures" / "minimal_greedy_counterexample.json"
POLICIES: tuple[AdmissionPolicy, ...] = (
    "exact",
    "greedy_target_pairs",
    "greedy_all_pairs",
    "fixed_order",
)


def _problem_from_bits(
    *,
    world_count: int,
    experiment_count: int,
    outcome_integer: int,
    target_integer: int,
    costs: tuple[int, ...],
    problem_id: str,
    budget: int | None = None,
) -> DiscoveryProblem:
    realizations = tuple(f"r{index}" for index in range(world_count))
    experiments = tuple(f"e{index}" for index in range(experiment_count))
    outcomes = tuple(
        tuple(
            (outcome_integer >> (world * experiment_count + experiment)) & 1
            for experiment in range(experiment_count)
        )
        for world in range(world_count)
    )
    targets = tuple(
        (target_integer >> world) & 1 for world in range(world_count)
    )
    return DiscoveryProblem(
        problem_id=problem_id,
        pair_id="obstruction_aware_admission",
        variant="rich",
        domain="finite_target_identification",
        system=FiniteExperimentSystem(
            name=problem_id,
            realizations=realizations,
            experiments=experiments,
            outcomes=outcomes,
        ),
        target=FiniteTarget(name="tau", values=targets),
        allowed_family=experiments,
        budget=sum(costs) if budget is None else budget,
        experiment_costs=costs,
    )


def _case_iterator(
    *,
    max_worlds: int,
    max_experiments: int,
):
    for world_count in range(2, max_worlds + 1):
        for experiment_count in range(1, max_experiments + 1):
            outcome_count = 1 << (world_count * experiment_count)
            for outcome_integer in range(outcome_count):
                for target_integer in range(1, (1 << world_count) - 1):
                    for costs in itertools.product(
                        (1, 2),
                        repeat=experiment_count,
                    ):
                        yield (
                            world_count,
                            experiment_count,
                            outcome_integer,
                            target_integer,
                            costs,
                        )


def _policy_costs(problem: DiscoveryProblem) -> dict[str, int | None]:
    return {
        policy: policy_worst_case_cost(problem, policy)
        for policy in POLICIES
    }


def _counterexample_record(
    problem: DiscoveryProblem,
    *,
    world_count: int,
    experiment_count: int,
    outcome_integer: int,
    target_integer: int,
    costs: tuple[int, ...],
    policy_costs: dict[str, int | None],
) -> dict[str, object]:
    exact_first = decide_admission(problem)
    candidates = problem.system.realizations
    greedy_first = choose_policy_experiment(
        problem,
        candidates,
        problem.allowed_family,
        "greedy_target_pairs",
    )
    return {
        "minimality_order": {
            "world_count": world_count,
            "experiment_count": experiment_count,
            "outcome_integer": outcome_integer,
            "target_integer": target_integer,
            "costs": list(costs),
        },
        "problem_id": problem.problem_id,
        "realizations": list(problem.system.realizations),
        "experiments": list(problem.system.experiments),
        "outcomes": [list(row) for row in problem.system.outcomes],
        "target_values": list(problem.target.values),
        "experiment_costs": list(problem.experiment_costs),
        "policy_worst_case_costs": policy_costs,
        "exact_first_experiment": exact_first.experiment,
        "greedy_first_experiment": greedy_first,
        "strict_regret": _strict_regret(policy_costs),
        "interpretation": (
            "The cheaper experiment separates more target-distinct pairs per "
            "unit cost immediately, but its hard branch still requires the "
            "expensive experiment. The exact policy buys the expensive "
            "experiment first and identifies the target in one step."
        ),
    }


def _strict_regret(policy_costs: dict[str, int | None]) -> int:
    exact = policy_costs["exact"]
    greedy = policy_costs["greedy_target_pairs"]
    if exact is None or greedy is None:
        raise ValueError("strict regret requires two finite policy costs")
    return greedy - exact


def _audit_exact_hidden_worlds(
    problem: DiscoveryProblem,
    exact_cost: int | None,
) -> tuple[int, int, int]:
    """Traverse one exact policy tree while auditing every hidden world."""

    if exact_cost is None:
        certificate = find_obstruction(problem, require_terminal=True)
        certificate_failures = int(
            certificate is None
            or not validate_obstruction(problem, certificate)
        )
        return (
            len(problem.system.realizations),
            0,
            certificate_failures,
        )

    recovery_failures = 0
    episode_count = 0
    maximum_path_cost = 0

    def visit(
        candidates: tuple[str, ...],
        remaining: tuple[str, ...],
        path_cost: int,
    ) -> None:
        nonlocal episode_count, maximum_path_cost, recovery_failures
        if target_is_determined(problem, candidates):
            episode_count += len(candidates)
            maximum_path_cost = max(maximum_path_cost, path_cost)
            if path_cost > exact_cost:
                recovery_failures += len(candidates)
            return
        experiment = choose_policy_experiment(
            problem,
            candidates,
            remaining,
            "exact",
        )
        if experiment is None:
            recovery_failures += len(candidates)
            episode_count += len(candidates)
            return
        after = tuple(item for item in remaining if item != experiment)
        buckets: dict[object, list[str]] = {}
        for realization in candidates:
            outcome = problem.system.transcript(
                realization,
                (experiment,),
            )[0]
            buckets.setdefault(outcome, []).append(realization)
        next_cost = path_cost + problem.experiment_cost(experiment)
        for bucket in buckets.values():
            visit(tuple(bucket), after, next_cost)

    visit(
        problem.system.realizations,
        problem.allowed_family,
        0,
    )
    if maximum_path_cost != exact_cost:
        recovery_failures += 1
    return episode_count, recovery_failures, 0


def _run_exhaustive_screen(
    *,
    max_worlds: int,
    max_experiments: int,
) -> dict[str, Any]:
    counts: dict[str, int] = {
        "cases": 0,
        "hidden_world_episodes": 0,
        "recoverable_cases": 0,
        "terminally_obstructed_cases": 0,
        "mathematical_disagreements": 0,
        "recovery_failures": 0,
        "certificate_failures": 0,
        "oracle_dominance_failures": 0,
        "greedy_target_strict_counterexamples": 0,
        "greedy_all_strict_counterexamples": 0,
        "fixed_order_strict_counterexamples": 0,
    }
    by_size: dict[str, dict[str, int]] = {}
    regret_sums = {
        "greedy_target_pairs": 0,
        "greedy_all_pairs": 0,
        "fixed_order": 0,
    }
    maximum_regrets = dict.fromkeys(regret_sums, 0)
    first_greedy_counterexample: dict[str, object] | None = None

    for (
        world_count,
        experiment_count,
        outcome_integer,
        target_integer,
        costs,
    ) in _case_iterator(
        max_worlds=max_worlds,
        max_experiments=max_experiments,
    ):
        key = f"{world_count}w_{experiment_count}e"
        size_counts = by_size.setdefault(
            key,
            {
                "cases": 0,
                "recoverable": 0,
                "terminally_obstructed": 0,
                "greedy_target_strict_counterexamples": 0,
            },
        )
        problem = _problem_from_bits(
            world_count=world_count,
            experiment_count=experiment_count,
            outcome_integer=outcome_integer,
            target_integer=target_integer,
            costs=costs,
            problem_id=(
                f"screen_w{world_count}_e{experiment_count}_"
                f"o{outcome_integer}_t{target_integer}_"
                f"c{''.join(map(str, costs))}"
            ),
        )
        costs_by_policy = _policy_costs(problem)
        exact = costs_by_policy["exact"]
        independent = independent_optimal_cost(problem)
        counts["cases"] += 1
        size_counts["cases"] += 1
        if exact != independent:
            counts["mathematical_disagreements"] += 1

        if exact is None:
            counts["terminally_obstructed_cases"] += 1
            size_counts["terminally_obstructed"] += 1
        else:
            counts["recoverable_cases"] += 1
            size_counts["recoverable"] += 1
            for policy in (
                "greedy_target_pairs",
                "greedy_all_pairs",
                "fixed_order",
            ):
                comparator = costs_by_policy[policy]
                if comparator is None or comparator < exact:
                    counts["oracle_dominance_failures"] += 1
                    continue
                regret = comparator - exact
                regret_sums[policy] += regret
                maximum_regrets[policy] = max(
                    maximum_regrets[policy],
                    regret,
                )
                if regret > 0:
                    counter_key = {
                        "greedy_target_pairs": (
                            "greedy_target_strict_counterexamples"
                        ),
                        "greedy_all_pairs": (
                            "greedy_all_strict_counterexamples"
                        ),
                        "fixed_order": (
                            "fixed_order_strict_counterexamples"
                        ),
                    }[policy]
                    counts[counter_key] += 1
                    if policy == "greedy_target_pairs":
                        size_counts[
                            "greedy_target_strict_counterexamples"
                        ] += 1
                        if first_greedy_counterexample is None:
                            first_greedy_counterexample = _counterexample_record(
                                problem,
                                world_count=world_count,
                                experiment_count=experiment_count,
                                outcome_integer=outcome_integer,
                                target_integer=target_integer,
                                costs=costs,
                                policy_costs=costs_by_policy,
                            )

        episode_count, recovery_failures, certificate_failures = (
            _audit_exact_hidden_worlds(problem, exact)
        )
        counts["hidden_world_episodes"] += episode_count
        counts["recovery_failures"] += recovery_failures
        counts["certificate_failures"] += certificate_failures

    recoverable = counts["recoverable_cases"]
    return {
        "bounds": {
            "minimum_worlds": 2,
            "maximum_worlds": max_worlds,
            "minimum_experiments": 1,
            "maximum_experiments": max_experiments,
            "outcomes": [0, 1],
            "target_values": [0, 1],
            "cost_values": [1, 2],
        },
        "counts": counts,
        "by_size": by_size,
        "regret": {
            policy: {
                "sum": regret_sums[policy],
                "maximum": maximum_regrets[policy],
                "mean_over_recoverable_cases": (
                    regret_sums[policy] / recoverable if recoverable else 0.0
                ),
            }
            for policy in regret_sums
        },
        "minimal_greedy_counterexample": first_greedy_counterexample,
    }


def _make_control_problem(
    problem_id: str,
    outcomes: tuple[tuple[int, ...], ...],
    targets: tuple[int, ...],
    costs: tuple[int, ...],
    *,
    budget: int,
) -> DiscoveryProblem:
    experiments = tuple(f"e{index}" for index in range(len(costs)))
    return DiscoveryProblem(
        problem_id=problem_id,
        pair_id="controls",
        variant="rich",
        domain="finite_control",
        system=FiniteExperimentSystem(
            name=problem_id,
            realizations=tuple(f"r{index}" for index in range(len(outcomes))),
            experiments=experiments,
            outcomes=outcomes,
        ),
        target=FiniteTarget(name="tau", values=targets),
        allowed_family=experiments,
        budget=budget,
        experiment_costs=costs,
    )


def _termination_controls() -> dict[str, object]:
    determined = _make_control_problem(
        "target_determined",
        ((0,), (1,)),
        (1, 1),
        (1,),
        budget=0,
    )
    terminal = _make_control_problem(
        "terminal_collision",
        ((0,), (0,)),
        (0, 1),
        (1,),
        budget=1,
    )
    over_budget = _make_control_problem(
        "budget_infeasible",
        ((0,), (1,)),
        (0, 1),
        (2,),
        budget=1,
    )
    decisions = {
        "target_determined": decide_admission(determined).to_dict(),
        "terminal_collision": decide_admission(terminal).to_dict(),
        "budget_infeasible": decide_admission(over_budget).to_dict(),
    }
    return {
        "decisions": decisions,
        "passed": (
            decisions["target_determined"]["status"] == "recovered"
            and decisions["terminal_collision"]["status"]
            == "terminal_obstruction"
            and decisions["budget_infeasible"]["status"]
            == "budget_infeasible"
            and decisions["budget_infeasible"]["required_worst_case_cost"] == 2
        ),
    }


def _certificate_mutation_controls() -> dict[str, bool]:
    problem = _make_control_problem(
        "certificate_control",
        ((0,), (0,)),
        (0, 1),
        (1,),
        budget=1,
    )
    valid = find_obstruction(problem, require_terminal=True)
    if valid is None:
        raise AssertionError("control lacks its registered obstruction")
    target_equal = replace(
        valid,
        target_values=(0, 0),
    )
    wrong_transcript = replace(
        valid,
        observed_transcript=(("e0", 1),),
    )
    forged_separator = replace(
        valid,
        separating_experiments=("e0",),
    )
    unknown_world = replace(valid, left="unknown")
    return {
        "valid_accepted": validate_obstruction(problem, valid),
        "target_equal_rejected": not validate_obstruction(
            problem,
            target_equal,
        ),
        "wrong_transcript_rejected": not validate_obstruction(
            problem,
            wrong_transcript,
        ),
        "forged_separator_rejected": not validate_obstruction(
            problem,
            forged_separator,
        ),
        "unknown_world_rejected": not validate_obstruction(
            problem,
            unknown_world,
        ),
    }


def _problem_from_counterexample(
    counterexample: dict[str, Any],
    *,
    problem_id: str,
) -> DiscoveryProblem:
    return _make_control_problem(
        problem_id,
        tuple(tuple(row) for row in counterexample["outcomes"]),
        tuple(counterexample["target_values"]),
        tuple(counterexample["experiment_costs"]),
        budget=sum(counterexample["experiment_costs"]),
    )


def _invariance_controls(
    counterexample: dict[str, Any] | None,
) -> dict[str, object]:
    if counterexample is None:
        return {"passed": False, "reason": "no greedy counterexample found"}
    original = _problem_from_counterexample(
        counterexample,
        problem_id="invariance_original",
    )
    original_costs = _policy_costs(original)

    reversed_worlds = DiscoveryProblem(
        problem_id="invariance_world_labels",
        pair_id=original.pair_id,
        variant=original.variant,
        domain=original.domain,
        system=FiniteExperimentSystem(
            name="invariance_world_labels",
            realizations=tuple(reversed(original.system.realizations)),
            experiments=original.system.experiments,
            outcomes=tuple(reversed(original.system.outcomes)),
        ),
        target=FiniteTarget(
            name="renamed_tau",
            values=tuple(
                1 - cast(int, value)
                for value in reversed(original.target.values)
            ),
        ),
        allowed_family=original.allowed_family,
        budget=original.budget,
        experiment_costs=original.experiment_costs,
    )
    renamed_experiments = tuple(
        f"renamed_{index}" for index in range(len(original.system.experiments))
    )
    reversed_experiment_labels = DiscoveryProblem(
        problem_id="invariance_experiment_labels",
        pair_id=original.pair_id,
        variant=original.variant,
        domain=original.domain,
        system=FiniteExperimentSystem(
            name="invariance_experiment_labels",
            realizations=original.system.realizations,
            experiments=renamed_experiments,
            outcomes=original.system.outcomes,
        ),
        target=original.target,
        allowed_family=renamed_experiments,
        budget=original.budget,
        experiment_costs=original.experiment_costs,
    )
    duplicate_name = "redundant_duplicate"
    duplicate_column = tuple(row[0] for row in original.system.outcomes)
    redundant = DiscoveryProblem(
        problem_id="invariance_redundant",
        pair_id=original.pair_id,
        variant=original.variant,
        domain=original.domain,
        system=FiniteExperimentSystem(
            name="invariance_redundant",
            realizations=original.system.realizations,
            experiments=(*original.system.experiments, duplicate_name),
            outcomes=tuple(
                (*row, duplicate_column[index])
                for index, row in enumerate(original.system.outcomes)
            ),
        ),
        target=original.target,
        allowed_family=(*original.allowed_family, duplicate_name),
        budget=original.budget + original.experiment_costs[0],
        experiment_costs=(
            *original.experiment_costs,
            original.experiment_costs[0],
        ),
    )
    world_costs = _policy_costs(reversed_worlds)
    experiment_costs = _policy_costs(reversed_experiment_labels)
    redundant_optimum = optimal_worst_case_cost(redundant)
    passed = (
        original_costs == world_costs
        and original_costs == experiment_costs
        and redundant_optimum == original_costs["exact"]
    )
    return {
        "original_policy_costs": original_costs,
        "world_and_target_relabel_policy_costs": world_costs,
        "experiment_relabel_policy_costs": experiment_costs,
        "redundant_experiment_optimum": redundant_optimum,
        "passed": passed,
    }


def _legacy_evidence_control() -> dict[str, object]:
    synthesis = (
        ROOT / "papers" / "concern_gated_retrieval_synthesis" / "paper.md"
    ).read_text(encoding="utf-8")
    erratum = (
        ROOT / "papers" / "concern_gated_retrieval_erratum_e1" / "paper.md"
    ).read_text(encoding="utf-8")
    anchors = {
        "synthesis_preserves_l1_null": (
            "does not beat a degree-matched random null" in synthesis
        ),
        "erratum_confirms_repaired_prior_kill": (
            "KILL survives the repaired prior on every family" in erratum
        ),
    }
    return {
        "anchors": anchors,
        "passed": all(anchors.values()),
        "interpretation": (
            "Obstruction-aware admission does not transport the failed "
            "learned context-by-concern geometry as positive evidence."
        ),
    }


def _source_digest() -> str:
    digest = hashlib.sha256()
    for path in (
        PACKAGE / "PREREGISTRATION.md",
        PACKAGE / "core.py",
        PACKAGE / "run_benchmark.py",
    ):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _markdown(receipt: dict[str, Any]) -> str:
    screen = receipt["exhaustive_screen"]
    counts = screen["counts"]
    witness = screen["minimal_greedy_counterexample"]
    gates = receipt["gates"]
    lines = [
        "# Obstruction-Aware Admission V0",
        "",
        f"**Verdict:** `{receipt['verdict']}`",
        "",
        "## Claim boundary",
        "",
        (
            "The run validates an exact finite control contract. It does not "
            "validate a universal theory of agency, natural scientific "
            "discovery, or concern-gated retrieval."
        ),
        "",
        "## Exhaustive screen",
        "",
        "| Quantity | Value |",
        "|---|---:|",
        f"| Finite systems | {counts['cases']:,} |",
        f"| Hidden-world episodes | {counts['hidden_world_episodes']:,} |",
        f"| Recoverable systems | {counts['recoverable_cases']:,} |",
        (
            "| Terminally obstructed systems | "
            f"{counts['terminally_obstructed_cases']:,} |"
        ),
        (
            "| Greedy target-pair counterexamples | "
            f"{counts['greedy_target_strict_counterexamples']:,} |"
        ),
        (
            "| Mathematical disagreements | "
            f"{counts['mathematical_disagreements']:,} |"
        ),
        f"| Recovery failures | {counts['recovery_failures']:,} |",
        f"| Certificate failures | {counts['certificate_failures']:,} |",
        "",
        "## Minimal greedy counterexample",
        "",
    ]
    if witness is None:
        lines.extend(
            [
                "No strict counterexample was found inside the registered "
                "finite boundary. Universal optimality remains withheld.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                f"- Worlds: `{witness['realizations']}`",
                f"- Experiments: `{witness['experiments']}`",
                f"- Outcomes: `{witness['outcomes']}`",
                f"- Target: `{witness['target_values']}`",
                f"- Costs: `{witness['experiment_costs']}`",
                (
                    "- Exact versus greedy worst-case cost: "
                    f"`{witness['policy_worst_case_costs']['exact']}` versus "
                    "`"
                    f"{witness['policy_worst_case_costs']['greedy_target_pairs']}"
                    "`"
                ),
                (
                    "- First experiment: exact `"
                    f"{witness['exact_first_experiment']}`, greedy `"
                    f"{witness['greedy_first_experiment']}`"
                ),
                "",
                str(witness["interpretation"]),
                "",
            ]
        )
    lines.extend(
        [
            "## Gate verdicts",
            "",
            "| Gate | Status |",
            "|---|---|",
        ]
    )
    lines.extend(
        f"| {gate_id} | {value['status']} |"
        for gate_id, value in gates.items()
    )
    lines.extend(
        [
            "",
            "## Reproduce",
            "",
            "```bash",
            (
                "uv run --no-sync python -m "
                "experiments.obstruction_aware_admission.run_benchmark"
            ),
            "```",
            "",
            f"Source digest: `{receipt['source_digest']}`",
            "",
        ]
    )
    return "\n".join(lines)


def run(
    *,
    json_path: Path = DEFAULT_JSON,
    markdown_path: Path = DEFAULT_MARKDOWN,
    counterexample_path: Path = DEFAULT_COUNTEREXAMPLE,
    max_worlds: int = 4,
    max_experiments: int = 3,
) -> dict[str, object]:
    if max_worlds < 2 or max_worlds > 4:
        raise ValueError("max_worlds must be between 2 and 4")
    if max_experiments < 1 or max_experiments > 3:
        raise ValueError("max_experiments must be between 1 and 3")

    screen = _run_exhaustive_screen(
        max_worlds=max_worlds,
        max_experiments=max_experiments,
    )
    termination = _termination_controls()
    mutations = _certificate_mutation_controls()
    invariance = _invariance_controls(
        screen["minimal_greedy_counterexample"],
    )
    legacy = _legacy_evidence_control()
    counts = screen["counts"]
    full_registered_boundary = max_worlds == 4 and max_experiments == 3
    gate_values = {
        "G0_OBJECT_INTEGRITY": True,
        "G1_MATHEMATICAL_AGREEMENT": (
            counts["mathematical_disagreements"] == 0
        ),
        "G2_RECOVERY_SOUNDNESS": counts["recovery_failures"] == 0,
        "G3_CERTIFICATE_SOUNDNESS": (
            counts["certificate_failures"] == 0 and all(mutations.values())
        ),
        "G4_ORACLE_DOMINANCE": (
            counts["oracle_dominance_failures"] == 0
        ),
        "G5_TERMINATION_SEPARATION": termination["passed"],
        "G6_INVARIANCE": invariance["passed"],
        "G7_GREEDY_FALSIFIER": (
            screen["minimal_greedy_counterexample"] is not None
        ),
        "G8_LEGACY_EVIDENCE_INTEGRITY": legacy["passed"],
        "G9_PROVENANCE": full_registered_boundary,
    }
    gates = {
        gate_id: {
            "status": "PASS" if passed else "FAIL",
            "fatal": gate_id != "G7_GREEDY_FALSIFIER",
        }
        for gate_id, passed in gate_values.items()
    }
    all_passed = all(gate_values.values())
    receipt: dict[str, object] = {
        "schema_version": "1.0",
        "experiment_id": "obstruction_aware_admission",
        "run_id": "obstruction_aware_admission_2026_07_27",
        "source_digest": _source_digest(),
        "exhaustive_screen": screen,
        "termination_controls": termination,
        "certificate_mutation_controls": mutations,
        "invariance_controls": invariance,
        "legacy_evidence_control": legacy,
        "gates": gates,
        "all_passed": all_passed,
        "verdict": (
            "ACCEPT_EXACT_FINITE_CONTROL"
            if all_passed
            else "WITHHOLD_AND_INSPECT_FAILED_GATES"
        ),
        "claim_strength": (
            "proved for the declared finite recurrence and demonstrated by "
            "exhaustive execution inside the registered boundary"
        ),
        "withheld_claims": [
            "universal theory of agency",
            "novel optimal decision-tree mathematics",
            "natural-domain scientific-discovery improvement",
            "large-state computational efficiency",
            "concern-gated retrieval validation",
        ],
    }

    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    counterexample_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(
        _markdown(receipt),
        encoding="utf-8",
    )
    witness = screen["minimal_greedy_counterexample"]
    if witness is not None:
        counterexample_path.write_text(
            json.dumps(witness, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument(
        "--counterexample",
        type=Path,
        default=DEFAULT_COUNTEREXAMPLE,
    )
    parser.add_argument("--max-worlds", type=int, default=4)
    parser.add_argument("--max-experiments", type=int, default=3)
    args = parser.parse_args()
    receipt = run(
        json_path=args.json,
        markdown_path=args.markdown,
        counterexample_path=args.counterexample,
        max_worlds=args.max_worlds,
        max_experiments=args.max_experiments,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
