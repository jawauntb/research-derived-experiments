#!/usr/bin/env python3
"""Run the registered obstruction-first benchmark and write public receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from experiments.information_limited_discovery.core import (
    DiscoveryProblem,
    EpisodeResult,
    ExperimentPolicy,
    ScopedObstructionCertificate,
    candidate_worlds,
    find_obstruction,
    recoverable_within_budget,
    run_episode,
    target_is_determined,
    validate_obstruction,
)
from experiments.information_limited_discovery.fixtures import (
    DEFAULT_FIXTURE,
    load_problems,
)
from experiments.relative_identifiability.core import (
    FiniteExperimentSystem,
    FiniteTarget,
)


PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[1]
DEFAULT_JSON = PACKAGE / "results" / "summary.json"
DEFAULT_MARKDOWN = PACKAGE / "results" / "summary.md"
POLICIES: tuple[ExperimentPolicy, ...] = (
    "obstruction_first",
    "uncertainty_first",
    "fixed_order",
    "always_guess",
    "always_abstain",
)


def _episode_score(
    problem: DiscoveryProblem,
    result: EpisodeResult,
) -> dict[str, object]:
    candidates = candidate_worlds(problem, result.observations)
    certificate_valid = (
        result.certificate is not None
        and validate_obstruction(problem, result.certificate)
    )
    certified_recovery = (
        result.outcome == "recovered"
        and result.predicted_target == result.actual_target
        and target_is_determined(problem, candidates)
    )
    certified_terminal = (
        result.outcome == "terminal_obstruction"
        and certificate_valid
        and result.certificate is not None
        and result.certificate.scope == "terminal"
    )
    guess_correct = (
        result.outcome == "guess"
        and result.predicted_target == result.actual_target
    )
    overclaim = (
        result.outcome == "guess"
        and not target_is_determined(problem, candidates)
    )
    unsupported_abstention = result.outcome == "unsupported_abstention"
    unnecessary_abstention = (
        unsupported_abstention and recoverable_within_budget(problem)
    )
    return {
        "certified_recovery": certified_recovery,
        "certified_terminal_obstruction": certified_terminal,
        "budget_exhausted": result.outcome == "budget_exhausted",
        "guess_correct": guess_correct,
        "overclaim": overclaim,
        "unsupported_abstention": unsupported_abstention,
        "unnecessary_abstention": unnecessary_abstention,
        "emitted_certificate_valid": (
            None if result.certificate is None else certificate_valid
        ),
    }


def _summarize_policy(
    rows: list[dict[str, Any]],
    policy: ExperimentPolicy,
) -> dict[str, object]:
    selected = [row for row in rows if row["episode"]["policy"] == policy]
    metric_names = (
        "certified_recovery",
        "certified_terminal_obstruction",
        "budget_exhausted",
        "guess_correct",
        "overclaim",
        "unsupported_abstention",
        "unnecessary_abstention",
    )
    counts = {
        metric: sum(bool(row["score"][metric]) for row in selected)
        for metric in metric_names
    }
    episode_count = len(selected)
    acting = policy in (
        "obstruction_first",
        "uncertainty_first",
        "fixed_order",
    )
    return {
        "episodes": episode_count,
        "counts": counts,
        "rates": {
            metric: (counts[metric] / episode_count if episode_count else 0.0)
            for metric in metric_names
        },
        "mean_steps": (
            sum(row["episode"]["steps"] for row in selected) / episode_count
            if acting and episode_count
            else None
        ),
        "mean_cost": (
            sum(row["episode"]["total_cost"] for row in selected) / episode_count
            if acting and episode_count
            else None
        ),
    }


def _matched_transition_checks(
    problems: tuple[DiscoveryProblem, ...],
    rows: list[dict[str, Any]],
) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    pair_ids = sorted({problem.pair_id for problem in problems})
    for pair_id in pair_ids:
        selected = [
            row
            for row in rows
            if row["episode"]["pair_id"] == pair_id
            and row["episode"]["policy"] == "obstruction_first"
        ]
        coarse = [row for row in selected if row["episode"]["variant"] == "coarse"]
        rich = [row for row in selected if row["episode"]["variant"] == "rich"]
        coarse_pass = bool(coarse) and all(
            row["score"]["certified_terminal_obstruction"] for row in coarse
        )
        rich_pass = bool(rich) and all(
            row["score"]["certified_recovery"] for row in rich
        )
        checks.append(
            {
                "pair_id": pair_id,
                "coarse_episode_count": len(coarse),
                "rich_episode_count": len(rich),
                "coarse_terminal_obstruction": coarse_pass,
                "rich_recovery": rich_pass,
                "passed": coarse_pass and rich_pass,
            }
        )
    return checks


def _invalid_certificate_controls(
    problems: tuple[DiscoveryProblem, ...],
) -> dict[str, bool]:
    by_id = {problem.problem_id: problem for problem in problems}
    coarse = by_id["mechanism_external_only"]
    rich = by_id["mechanism_with_internal_patch"]
    valid_terminal = find_obstruction(coarse, require_terminal=True)
    if valid_terminal is None:
        raise AssertionError("registered coarse task lacks terminal obstruction")

    target_equal = replace(
        valid_terminal,
        left="mechanism_a_action_0",
        right="mechanism_a_action_1",
        target_values=("A", "A"),
    )
    separable_as_terminal = ScopedObstructionCertificate(
        problem_id=rich.problem_id,
        scope="terminal",
        left="mechanism_a_action_0",
        right="mechanism_b_action_0",
        target_values=("A", "B"),
        observed_transcript=(),
        separating_experiments=(),
    )
    wrong_transcript = replace(
        valid_terminal,
        observed_transcript=(("external_readout", 999),),
    )
    return {
        "valid_terminal_accepted": validate_obstruction(
            coarse,
            valid_terminal,
        ),
        "target_equal_rejected": not validate_obstruction(coarse, target_equal),
        "separable_terminal_rejected": not validate_obstruction(
            rich,
            separable_as_terminal,
        ),
        "wrong_transcript_rejected": not validate_obstruction(
            coarse,
            wrong_transcript,
        ),
    }


def _permuted_problem(
    problem: DiscoveryProblem,
) -> tuple[DiscoveryProblem, dict[str, str]]:
    indices = tuple(reversed(range(len(problem.system.realizations))))
    old_to_new = {
        problem.system.realizations[index]: f"renamed_world_{offset}"
        for offset, index in enumerate(indices)
    }
    target_labels: dict[object, str] = {}
    renamed_targets: list[str] = []
    for index in indices:
        value = problem.target.values[index]
        target_labels.setdefault(value, f"renamed_target_{len(target_labels)}")
        renamed_targets.append(target_labels[value])
    renamed = DiscoveryProblem(
        problem_id=f"{problem.problem_id}_permuted",
        pair_id=f"{problem.pair_id}_permuted",
        variant=problem.variant,
        domain=problem.domain,
        system=FiniteExperimentSystem(
            name=f"{problem.system.name}_permuted",
            realizations=tuple(old_to_new[problem.system.realizations[i]] for i in indices),
            experiments=problem.system.experiments,
            outcomes=tuple(problem.system.outcomes[i] for i in indices),
        ),
        target=FiniteTarget(
            name=f"{problem.target.name}_permuted",
            values=tuple(renamed_targets),
        ),
        allowed_family=problem.allowed_family,
        budget=problem.budget,
        experiment_costs=problem.experiment_costs,
    )
    return renamed, old_to_new


def _label_permutation_control(
    problems: tuple[DiscoveryProblem, ...],
) -> dict[str, object]:
    comparisons = 0
    passed = True
    for problem in problems:
        renamed, old_to_new = _permuted_problem(problem)
        for realization in problem.system.realizations:
            original = run_episode(problem, realization, "obstruction_first")
            permuted = run_episode(
                renamed,
                old_to_new[realization],
                "obstruction_first",
            )
            comparisons += 1
            if (
                original.outcome,
                original.steps,
                original.total_cost,
                None
                if original.certificate is None
                else original.certificate.scope,
            ) != (
                permuted.outcome,
                permuted.steps,
                permuted.total_cost,
                None
                if permuted.certificate is None
                else permuted.certificate.scope,
            ):
                passed = False
    return {"comparisons": comparisons, "passed": passed}


def render_markdown(receipt: dict[str, Any]) -> str:
    verdict = "PASS" if receipt["all_passed"] else "FAIL"
    lines = [
        "# Information-Limited Discovery V0",
        "",
        f"**Registered V0 verdict:** `{verdict}`",
        "",
        f"**Fixture SHA-256:** `{receipt['fixture']['sha256']}`",
        "",
        "## Matched experiment-family transitions",
        "",
        "| Pair | Coarse terminal obstruction | Rich recovery | Pass |",
        "|---|---:|---:|---:|",
    ]
    for check in receipt["matched_transitions"]:
        lines.append(
            "| {pair_id} | {coarse} | {rich} | {passed} |".format(
                pair_id=check["pair_id"],
                coarse="yes" if check["coarse_terminal_obstruction"] else "no",
                rich="yes" if check["rich_recovery"] else "no",
                passed="yes" if check["passed"] else "no",
            )
        )
    lines.extend(
        [
            "",
            "## Policy outcomes",
            "",
            "| Policy | Episodes | Recovery | Terminal | Budget | Overclaim | Unsupported abstention | Unnecessary abstention |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for policy, summary in receipt["policy_summaries"].items():
        counts = summary["counts"]
        lines.append(
            "| {policy} | {episodes} | {recovery} | {terminal} | {budget} | {overclaim} | {unsupported} | {unnecessary} |".format(
                policy=policy,
                episodes=summary["episodes"],
                recovery=counts["certified_recovery"],
                terminal=counts["certified_terminal_obstruction"],
                budget=counts["budget_exhausted"],
                overclaim=counts["overclaim"],
                unsupported=counts["unsupported_abstention"],
                unnecessary=counts["unnecessary_abstention"],
            )
        )
    lines.extend(
        [
            "",
            "## Control gates",
            "",
            f"- Emitted certificates valid: `{str(receipt['controls']['emitted_certificates_valid']).lower()}`",
            f"- Invalid-certificate mutations rejected: `{str(receipt['controls']['invalid_certificate_mutations_passed']).lower()}`",
            f"- Label-permutation comparisons: `{receipt['controls']['label_permutation']['comparisons']}` (`{'pass' if receipt['controls']['label_permutation']['passed'] else 'fail'}`)",
            f"- All five outcome classes observed: `{str(receipt['controls']['outcome_classes_observed']).lower()}`",
            "",
            "## Scope",
            "",
            "This receipt validates deterministic finite benchmark mechanics only.",
            "The domain names describe encoded tables; they are not evidence that",
            "the method performs scientific discovery in natural systems.",
            "",
        ]
    )
    return "\n".join(lines)


def run(
    fixture_path: Path = DEFAULT_FIXTURE,
    json_path: Path | None = None,
    markdown_path: Path | None = None,
) -> dict[str, Any]:
    fixture_path = fixture_path.resolve()
    if fixture_path != DEFAULT_FIXTURE.resolve() and (
        json_path is None or markdown_path is None
    ):
        raise ValueError(
            "custom fixtures require explicit JSON and Markdown output paths"
        )
    json_path = DEFAULT_JSON if json_path is None else json_path
    markdown_path = DEFAULT_MARKDOWN if markdown_path is None else markdown_path
    problems = load_problems(fixture_path)

    rows: list[dict[str, Any]] = []
    for problem in problems:
        for policy in POLICIES:
            for realization in problem.system.realizations:
                result = run_episode(problem, realization, policy)
                rows.append(
                    {
                        "episode": result.to_dict(),
                        "score": _episode_score(problem, result),
                    }
                )

    matched = _matched_transition_checks(problems, rows)
    invalid_controls = _invalid_certificate_controls(problems)
    label_control = _label_permutation_control(problems)
    emitted_valid = all(
        row["score"]["emitted_certificate_valid"] is not False
        for row in rows
    )
    observed_outcomes = Counter(row["episode"]["outcome"] for row in rows)
    required_outcomes = {
        "recovered",
        "terminal_obstruction",
        "budget_exhausted",
        "guess",
        "unsupported_abstention",
    }
    outcome_classes_observed = required_outcomes.issubset(observed_outcomes)
    policy_summaries = {
        policy: _summarize_policy(rows, policy) for policy in POLICIES
    }
    guess_counts = cast(
        dict[str, int],
        policy_summaries["always_guess"]["counts"],
    )
    abstain_counts = cast(
        dict[str, int],
        policy_summaries["always_abstain"]["counts"],
    )
    guess_episode_count = cast(
        int,
        policy_summaries["always_guess"]["episodes"],
    )
    controls = {
        "emitted_certificates_valid": emitted_valid,
        "invalid_certificate_controls": invalid_controls,
        "invalid_certificate_mutations_passed": all(invalid_controls.values()),
        "label_permutation": label_control,
        "outcome_class_counts": dict(sorted(observed_outcomes.items())),
        "outcome_classes_observed": outcome_classes_observed,
        "lucky_guesses_remain_overclaims": (
            guess_counts["overclaim"] == guess_episode_count
        ),
        "unsupported_abstentions_not_certified": (
            abstain_counts["certified_terminal_obstruction"] == 0
        ),
        "recoverable_task_abstentions_marked_unnecessary": (
            abstain_counts["unnecessary_abstention"] > 0
        ),
    }
    all_passed = (
        all(check["passed"] for check in matched)
        and emitted_valid
        and controls["invalid_certificate_mutations_passed"]
        and label_control["passed"]
        and outcome_classes_observed
        and controls["lucky_guesses_remain_overclaims"]
        and controls["unsupported_abstentions_not_certified"]
        and controls["recoverable_task_abstentions_marked_unnecessary"]
    )
    try:
        fixture_label = str(fixture_path.relative_to(ROOT))
    except ValueError:
        fixture_label = str(fixture_path)
    receipt: dict[str, Any] = {
        "schema_version": "1.0",
        "benchmark": "information_limited_discovery_v0",
        "claim_scope": "deterministic finite benchmark mechanics",
        "all_passed": all_passed,
        "fixture": {
            "path": fixture_label,
            "sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
        },
        "task_count": len(problems),
        "episode_count": len(rows),
        "matched_transitions": matched,
        "policy_summaries": policy_summaries,
        "controls": controls,
        "episodes": rows,
    }
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(receipt), encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args()
    try:
        receipt = run(args.fixture, args.json_out, args.markdown_out)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["all_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
