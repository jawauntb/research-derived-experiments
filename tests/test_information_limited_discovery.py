from __future__ import annotations

import itertools
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from experiments.information_limited_discovery.core import (
    DiscoveryProblem,
    ScopedObstructionCertificate,
    candidate_worlds,
    find_obstruction,
    run_episode,
    validate_obstruction,
)
from experiments.information_limited_discovery.fixtures import load_problems
from experiments.information_limited_discovery.run_benchmark import run
from experiments.relative_identifiability.core import (
    FactorizationCertificate,
    FiniteExperimentSystem,
    FiniteTarget,
    ObstructionCertificate,
    identify_target,
)


ROOT = Path(__file__).resolve().parent.parent


class InformationLimitedDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.problems = load_problems()
        cls.by_id = {problem.problem_id: problem for problem in cls.problems}

    def test_fixture_has_three_matched_coarse_rich_pairs(self) -> None:
        grouped: dict[str, set[str]] = {}
        for problem in self.problems:
            grouped.setdefault(problem.pair_id, set()).add(problem.variant)
        self.assertEqual(len(grouped), 3)
        self.assertTrue(
            all(variants == {"coarse", "rich"} for variants in grouped.values())
        )

    def test_local_and_terminal_obstructions_are_distinct(self) -> None:
        coarse = self.by_id["mechanism_external_only"]
        terminal = find_obstruction(coarse)
        self.assertIsNotNone(terminal)
        assert terminal is not None
        self.assertEqual(terminal.scope, "terminal")
        self.assertEqual(terminal.separating_experiments, ())
        self.assertTrue(validate_obstruction(coarse, terminal))

        rich = self.by_id["mechanism_with_internal_patch"]
        local = find_obstruction(rich)
        self.assertIsNotNone(local)
        assert local is not None
        self.assertEqual(local.scope, "local")
        self.assertIn("internal_patch", local.separating_experiments)
        self.assertTrue(validate_obstruction(rich, local))
        self.assertIsNone(find_obstruction(rich, require_terminal=True))

    def test_obstruction_first_policy_reproduces_every_matched_transition(
        self,
    ) -> None:
        for problem in self.problems:
            for realization in problem.system.realizations:
                with self.subTest(
                    problem=problem.problem_id,
                    realization=realization,
                ):
                    result = run_episode(
                        problem,
                        realization,
                        "obstruction_first",
                    )
                    if problem.variant == "coarse":
                        self.assertEqual(result.outcome, "terminal_obstruction")
                        assert result.certificate is not None
                        self.assertTrue(
                            validate_obstruction(problem, result.certificate)
                        )
                    else:
                        self.assertEqual(result.outcome, "recovered")
                        self.assertEqual(
                            result.predicted_target,
                            result.actual_target,
                        )

    def test_target_aware_policy_avoids_registered_distractor(self) -> None:
        problem = self.by_id["mechanism_with_internal_patch"]
        targeted = run_episode(
            problem,
            "mechanism_b_action_1",
            "obstruction_first",
        )
        fixed = run_episode(
            problem,
            "mechanism_b_action_1",
            "fixed_order",
        )
        self.assertEqual(targeted.outcome, "recovered")
        self.assertEqual(targeted.observations[0][0], "internal_patch")
        self.assertEqual(fixed.outcome, "budget_exhausted")
        self.assertEqual(fixed.observations[0][0], "external_readout")
        assert fixed.certificate is not None
        self.assertEqual(fixed.certificate.scope, "local")

    def test_lucky_guess_and_unsupported_abstention_are_not_certificates(
        self,
    ) -> None:
        problem = self.by_id["automata_with_delayed_probe"]
        guess = run_episode(problem, "accepts_after_two", "always_guess")
        abstain = run_episode(problem, "accepts_after_two", "always_abstain")
        self.assertEqual(guess.outcome, "guess")
        self.assertEqual(guess.predicted_target, guess.actual_target)
        self.assertGreater(
            len(
                {
                    problem.target.values[
                        problem.system.realizations.index(candidate)
                    ]
                    for candidate in candidate_worlds(problem, ())
                }
            ),
            1,
        )
        self.assertEqual(abstain.outcome, "unsupported_abstention")
        self.assertIsNone(abstain.certificate)

    def test_invalid_terminal_certificates_fail_closed(self) -> None:
        coarse = self.by_id["mechanism_external_only"]
        valid = find_obstruction(coarse, require_terminal=True)
        self.assertIsNotNone(valid)
        assert valid is not None
        self.assertFalse(
            validate_obstruction(
                coarse,
                replace(
                    valid,
                    left="mechanism_a_action_0",
                    right="mechanism_a_action_1",
                    target_values=("A", "A"),
                ),
            )
        )

        rich = self.by_id["mechanism_with_internal_patch"]
        forged = ScopedObstructionCertificate(
            problem_id=rich.problem_id,
            scope="terminal",
            left="mechanism_a_action_0",
            right="mechanism_b_action_0",
            target_values=("A", "B"),
            observed_transcript=(),
            separating_experiments=(),
        )
        self.assertFalse(validate_obstruction(rich, forged))

    def test_observations_reject_duplicates_wrong_types_and_disallowed_experiments(
        self,
    ) -> None:
        problem = self.by_id["mechanism_external_only"]
        with self.assertRaisesRegex(ValueError, "unique"):
            candidate_worlds(
                problem,
                (("external_readout", 0), ("external_readout", 0)),
            )
        with self.assertRaisesRegex(ValueError, "wrong type"):
            candidate_worlds(problem, (("external_readout", "0"),))
        with self.assertRaisesRegex(ValueError, "permitted"):
            candidate_worlds(problem, (("internal_patch", "A"),))

    def test_all_small_binary_systems_match_direct_factorization(self) -> None:
        realizations = ("r0", "r1", "r2")
        experiments = ("e0", "e1")
        cases = 0
        for flat_outcomes in itertools.product((0, 1), repeat=6):
            outcomes = tuple(
                tuple(flat_outcomes[row * 2 : row * 2 + 2])
                for row in range(3)
            )
            system = FiniteExperimentSystem(
                name="exhaustive",
                realizations=realizations,
                experiments=experiments,
                outcomes=outcomes,
            )
            for target_values in itertools.product((0, 1), repeat=3):
                target = FiniteTarget("target", target_values)
                for size in range(3):
                    for family in itertools.combinations(experiments, size):
                        problem = DiscoveryProblem(
                            problem_id="exhaustive",
                            pair_id="exhaustive",
                            variant="rich",
                            domain="test",
                            system=system,
                            target=target,
                            allowed_family=family,
                            budget=len(family),
                            experiment_costs=(1, 1),
                        )
                        direct = identify_target(system, target, family)
                        obstruction = find_obstruction(
                            problem,
                            require_terminal=True,
                        )
                        self.assertEqual(
                            isinstance(direct, ObstructionCertificate),
                            obstruction is not None,
                        )
                        if isinstance(direct, FactorizationCertificate):
                            for realization in realizations:
                                result = run_episode(problem, realization)
                                self.assertEqual(result.outcome, "recovered")
                                self.assertEqual(
                                    result.predicted_target,
                                    result.actual_target,
                                )
                        cases += 1
        self.assertEqual(cases, 2048)

    def test_runner_writes_replayable_passing_receipt(self) -> None:
        with TemporaryDirectory() as directory:
            json_path = Path(directory) / "summary.json"
            markdown_path = Path(directory) / "summary.md"
            receipt = run(
                json_path=json_path,
                markdown_path=markdown_path,
            )
            self.assertTrue(receipt["all_passed"])
            self.assertEqual(receipt["task_count"], 6)
            self.assertTrue(json_path.is_file())
            self.assertIn(
                "deterministic finite benchmark mechanics",
                markdown_path.read_text(),
            )


if __name__ == "__main__":
    unittest.main()
