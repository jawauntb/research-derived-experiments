from __future__ import annotations

import itertools
import json
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from experiments.information_limited_discovery.core import (
    DiscoveryProblem,
    find_obstruction,
    validate_obstruction,
)
from experiments.obstruction_aware_admission.core import (
    choose_policy_experiment,
    decide_admission,
    independent_optimal_cost,
    optimal_worst_case_cost,
    policy_worst_case_cost,
    run_policy_episode,
)
from experiments.obstruction_aware_admission.run_benchmark import run
from experiments.relative_identifiability.core import (
    FiniteExperimentSystem,
    FiniteTarget,
)


def make_problem(
    *,
    problem_id: str,
    outcomes: tuple[tuple[int, ...], ...],
    targets: tuple[int, ...],
    costs: tuple[int, ...],
    budget: int | None = None,
) -> DiscoveryProblem:
    experiments = tuple(f"e{index}" for index in range(len(costs)))
    return DiscoveryProblem(
        problem_id=problem_id,
        pair_id="test",
        variant="rich",
        domain="test",
        system=FiniteExperimentSystem(
            name=problem_id,
            realizations=tuple(f"r{index}" for index in range(len(outcomes))),
            experiments=experiments,
            outcomes=outcomes,
        ),
        target=FiniteTarget(name="tau", values=targets),
        allowed_family=experiments,
        budget=sum(costs) if budget is None else budget,
        experiment_costs=costs,
    )


class ObstructionAwareAdmissionTests(unittest.TestCase):
    def test_minimal_greedy_counterexample(self) -> None:
        problem = make_problem(
            problem_id="minimal_counterexample",
            outcomes=((1, 1), (1, 0), (0, 0), (0, 0)),
            targets=(1, 0, 0, 0),
            costs=(1, 2),
        )

        self.assertEqual(optimal_worst_case_cost(problem), 2)
        self.assertEqual(
            policy_worst_case_cost(problem, "greedy_target_pairs"),
            3,
        )
        self.assertEqual(
            choose_policy_experiment(
                problem,
                problem.system.realizations,
                problem.allowed_family,
                "exact",
            ),
            "e1",
        )
        self.assertEqual(
            choose_policy_experiment(
                problem,
                problem.system.realizations,
                problem.allowed_family,
                "greedy_target_pairs",
            ),
            "e0",
        )

    def test_exact_policy_recovers_where_greedy_exhausts_matched_budget(
        self,
    ) -> None:
        problem = make_problem(
            problem_id="matched_budget",
            outcomes=((1, 1), (1, 0), (0, 0), (0, 0)),
            targets=(1, 0, 0, 0),
            costs=(1, 2),
            budget=2,
        )
        for realization in problem.system.realizations:
            exact = run_policy_episode(problem, realization, "exact")
            self.assertEqual(exact.outcome, "recovered")
            self.assertEqual(exact.predicted_target, exact.actual_target)
            self.assertLessEqual(exact.total_cost, 2)

        for realization in ("r0", "r1"):
            greedy = run_policy_episode(
                problem,
                realization,
                "greedy_target_pairs",
            )
            self.assertEqual(greedy.outcome, "budget_exhausted")

    def test_decision_separates_recovery_impossibility_and_budget(self) -> None:
        determined = make_problem(
            problem_id="determined",
            outcomes=((0,), (1,)),
            targets=(1, 1),
            costs=(1,),
            budget=0,
        )
        terminal = make_problem(
            problem_id="terminal",
            outcomes=((0,), (0,)),
            targets=(0, 1),
            costs=(1,),
        )
        over_budget = make_problem(
            problem_id="over_budget",
            outcomes=((0,), (1,)),
            targets=(0, 1),
            costs=(2,),
            budget=1,
        )

        self.assertEqual(decide_admission(determined).status, "recovered")
        terminal_decision = decide_admission(terminal)
        self.assertEqual(terminal_decision.status, "terminal_obstruction")
        self.assertIsNotNone(terminal_decision.certificate)
        assert terminal_decision.certificate is not None
        self.assertTrue(
            validate_obstruction(terminal, terminal_decision.certificate)
        )
        budget_decision = decide_admission(over_budget)
        self.assertEqual(budget_decision.status, "budget_infeasible")
        self.assertEqual(budget_decision.required_worst_case_cost, 2)
        self.assertEqual(budget_decision.remaining_budget, 1)

    def test_spent_cost_must_match_transcript(self) -> None:
        problem = make_problem(
            problem_id="spent_cost",
            outcomes=((0,), (1,)),
            targets=(0, 1),
            costs=(1,),
        )
        with self.assertRaisesRegex(ValueError, "cost of the transcript"):
            decide_admission(
                problem,
                (("e0", 0),),
                spent_cost=0,
            )

    def test_certificate_mutations_fail_closed(self) -> None:
        problem = make_problem(
            problem_id="certificate",
            outcomes=((0,), (0,)),
            targets=(0, 1),
            costs=(1,),
        )
        valid = find_obstruction(problem, require_terminal=True)
        self.assertIsNotNone(valid)
        assert valid is not None
        self.assertTrue(validate_obstruction(problem, valid))
        self.assertFalse(
            validate_obstruction(
                problem,
                replace(valid, target_values=(0, 0)),
            )
        )
        self.assertFalse(
            validate_obstruction(
                problem,
                replace(valid, separating_experiments=("e0",)),
            )
        )

    def test_memoized_and_independent_costs_agree_on_small_domain(self) -> None:
        cases = 0
        for world_count in (2, 3):
            for experiment_count in (1, 2):
                bit_count = world_count * experiment_count
                for outcome_integer in range(1 << bit_count):
                    outcomes = tuple(
                        tuple(
                            (
                                outcome_integer
                                >> (world * experiment_count + experiment)
                            )
                            & 1
                            for experiment in range(experiment_count)
                        )
                        for world in range(world_count)
                    )
                    for target_integer in range(1, (1 << world_count) - 1):
                        targets = tuple(
                            (target_integer >> world) & 1
                            for world in range(world_count)
                        )
                        for costs in itertools.product(
                            (1, 2),
                            repeat=experiment_count,
                        ):
                            problem = make_problem(
                                problem_id="exhaustive_test",
                                outcomes=outcomes,
                                targets=targets,
                                costs=costs,
                            )
                            self.assertEqual(
                                optimal_worst_case_cost(problem),
                                independent_optimal_cost(problem),
                            )
                            cases += 1
        self.assertEqual(cases, 1776)

    def test_reduced_runner_is_deterministic_and_scope_limited(self) -> None:
        with TemporaryDirectory() as first, TemporaryDirectory() as second:
            paths = []
            receipts = []
            for directory in (first, second):
                root = Path(directory)
                json_path = root / "summary.json"
                receipt = run(
                    json_path=json_path,
                    markdown_path=root / "summary.md",
                    counterexample_path=root / "counterexample.json",
                    max_worlds=2,
                    max_experiments=2,
                )
                paths.append(json_path)
                receipts.append(receipt)

            self.assertEqual(paths[0].read_bytes(), paths[1].read_bytes())
            self.assertEqual(receipts[0], receipts[1])
            self.assertFalse(receipts[0]["all_passed"])
            self.assertEqual(
                receipts[0]["verdict"],
                "WITHHOLD_AND_INSPECT_FAILED_GATES",
            )
            parsed = json.loads(paths[0].read_text(encoding="utf-8"))
            self.assertEqual(
                parsed["exhaustive_screen"]["counts"]["cases"],
                144,
            )
            self.assertIsNone(
                parsed["exhaustive_screen"]["minimal_greedy_counterexample"]
            )


if __name__ == "__main__":
    unittest.main()
