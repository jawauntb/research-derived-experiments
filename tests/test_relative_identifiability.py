#!/usr/bin/env python3
"""Regression and exhaustive finite checks for relative identifiability."""

from __future__ import annotations

import itertools
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from experiments.relative_identifiability.core import (
    FactorizationCertificate,
    FiniteExperimentSystem,
    FiniteTarget,
    ObstructionCertificate,
    analyze_refinement,
    identify_target,
    minimal_identifying_families,
)
from experiments.relative_identifiability.fixtures import load_regression_suite
from experiments.relative_identifiability.lean_gate import run_lean_gate
from experiments.relative_identifiability.run_regressions import run


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = (
    ROOT
    / "experiments"
    / "relative_identifiability"
    / "fixtures"
    / "midas_regressions.json"
)
CONTRACT_PATH = (
    ROOT / "experiments" / "relative_identifiability" / "midas_contract.json"
)
LEAN_PATH = (
    ROOT / "formal" / "relative-identifiability" / "RelativeIdentifiability.lean"
)
SUMMARY_JSON_PATH = (
    ROOT / "experiments" / "relative_identifiability" / "results" / "summary.json"
)
SUMMARY_MARKDOWN_PATH = SUMMARY_JSON_PATH.with_suffix(".md")


def _system(
    outcomes: tuple[tuple[object, ...], ...],
) -> FiniteExperimentSystem:
    return FiniteExperimentSystem(
        name="test",
        realizations=("r0", "r1", "r2"),
        experiments=("e0", "e1", "e2"),
        outcomes=outcomes,
    )


class ConstructionTests(unittest.TestCase):
    def test_rejects_partial_or_malformed_tables(self) -> None:
        with self.assertRaisesRegex(ValueError, "one row per realization"):
            FiniteExperimentSystem(
                name="partial",
                realizations=("r0", "r1"),
                experiments=("e0",),
                outcomes=((0,),),
            )
        with self.assertRaisesRegex(ValueError, "one outcome per experiment"):
            FiniteExperimentSystem(
                name="ragged",
                realizations=("r0", "r1"),
                experiments=("e0", "e1"),
                outcomes=((0, 1), (0,)),
            )
        with self.assertRaisesRegex(ValueError, "unique"):
            FiniteExperimentSystem(
                name="duplicate",
                realizations=("r0", "r0"),
                experiments=("e0",),
                outcomes=((0,), (1,)),
            )
        with self.assertRaisesRegex(ValueError, "unique"):
            FiniteExperimentSystem(
                name="duplicate-experiments",
                realizations=("r0",),
                experiments=("e0", "e0"),
                outcomes=((0, 0),),
            )

    def test_rejects_cross_type_python_equality_collisions(self) -> None:
        with self.assertRaisesRegex(ValueError, "one runtime type"):
            FiniteExperimentSystem(
                name="mixed-outcomes",
                realizations=("r0", "r1"),
                experiments=("e0",),
                outcomes=((0,), (False,)),
            )
        with self.assertRaisesRegex(ValueError, "one runtime type"):
            FiniteTarget("mixed-target", (0, False))

    def test_rejects_unknown_experiment_and_wrong_target_arity(self) -> None:
        system = _system(((0, 0, 0), (0, 1, 1), (1, 0, 1)))
        with self.assertRaisesRegex(ValueError, "unknown experiment"):
            system.partition(("missing",))
        with self.assertRaisesRegex(ValueError, "one value per realization"):
            identify_target(system, FiniteTarget("bad", (0, 1)), ("e0",))


class TheoremEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.system = _system(((0, 0, 0), (0, 1, 1), (1, 0, 1)))

    def test_empty_family_and_constant_target(self) -> None:
        target = FiniteTarget("constant", ("x", "x", "x"))
        result = identify_target(self.system, target, ())
        self.assertIsInstance(result, FactorizationCertificate)
        assert isinstance(result, FactorizationCertificate)
        self.assertEqual(result.blocks, (("r0", "r1", "r2"),))
        self.assertEqual(result.block_targets, ("x",))

    def test_single_realization_needs_no_experiments(self) -> None:
        system = FiniteExperimentSystem(
            name="singleton",
            realizations=("only",),
            experiments=("unused",),
            outcomes=(("value",),),
        )
        target = FiniteTarget("identity", ("only",))
        result = identify_target(system, target, ())
        self.assertIsInstance(result, FactorizationCertificate)
        assert isinstance(result, FactorizationCertificate)
        self.assertEqual(result.blocks, (("only",),))
        search = minimal_identifying_families(system, target)
        self.assertEqual(search.minimum_size, 0)
        self.assertEqual(search.families, ((),))

    def test_obstruction_certificate_is_small_and_deterministic(self) -> None:
        target = FiniteTarget("identity", ("left", "right", "third"))
        result = identify_target(self.system, target, ("e0",))
        self.assertIsInstance(result, ObstructionCertificate)
        assert isinstance(result, ObstructionCertificate)
        self.assertEqual((result.left, result.right), ("r0", "r1"))
        self.assertEqual(result.shared_transcript, (0,))
        self.assertEqual((result.left_target, result.right_target), ("left", "right"))

    def test_richer_family_refines_and_redundant_experiment_does_not(self) -> None:
        strict = analyze_refinement(self.system, ("e0",), ("e0", "e1"))
        self.assertTrue(strict.is_refinement)
        self.assertTrue(strict.strict)
        self.assertEqual(strict.added_experiments, ("e1",))
        self.assertEqual(
            strict.split_blocks,
            ((("r0",), ("r1",)),),
        )
        self.assertEqual(strict.separating_experiments, ("e1",))

        redundant_system = _system(((0, 0, 0), (0, 0, 1), (1, 1, 0)))
        redundant = analyze_refinement(
            redundant_system,
            ("e0",),
            ("e0", "e1"),
        )
        self.assertTrue(redundant.is_refinement)
        self.assertFalse(redundant.strict)
        self.assertEqual(redundant.split_blocks, ())
        self.assertEqual(redundant.separating_experiments, ())

    def test_refinement_requires_nested_families(self) -> None:
        with self.assertRaisesRegex(ValueError, "must contain the coarse family"):
            analyze_refinement(self.system, ("e0", "e1"), ("e1", "e2"))

    def test_minimum_identifying_families_include_all_ties(self) -> None:
        tied_system = _system(((0, 0, 0), (0, 1, 1), (1, 1, 1)))
        target = FiniteTarget("r0-vs-rest", (0, 1, 1))
        search = minimal_identifying_families(tied_system, target)
        self.assertEqual(search.minimum_size, 1)
        self.assertEqual(search.families, (("e1",), ("e2",)))
        self.assertIsNone(search.full_family_obstruction)

    def test_full_family_collision_is_terminal_obstruction(self) -> None:
        system = _system(((0, 0, 0), (0, 0, 0), (1, 1, 1)))
        target = FiniteTarget("identity", ("a", "b", "c"))
        search = minimal_identifying_families(system, target)
        self.assertIsNone(search.minimum_size)
        self.assertEqual(search.families, ())
        self.assertIsInstance(
            search.full_family_obstruction,
            ObstructionCertificate,
        )


class RegisteredFixtureTests(unittest.TestCase):
    def test_fixture_is_machine_readable_and_matches_expected_verdicts(self) -> None:
        suite = load_regression_suite(FIXTURE_PATH)
        self.assertEqual(
            suite.schema_version,
            "relative-identifiability-regression/v1",
        )
        receipts = suite.run()
        self.assertEqual(len(receipts["cases"]), 5)
        self.assertEqual(len(receipts["refinements"]), 2)
        self.assertTrue(receipts["all_passed"])

    def test_fixture_json_contains_no_unregistered_result_fields(self) -> None:
        raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            set(raw),
            {"schema_version", "systems", "cases", "refinements"},
        )

    def test_runner_writes_replayable_public_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            json_path = temporary / "summary.json"
            markdown_path = temporary / "summary.md"
            receipt = run(FIXTURE_PATH, json_path, markdown_path)
            self.assertTrue(receipt["all_passed"])
            self.assertEqual(
                json.loads(json_path.read_text(encoding="utf-8")),
                receipt,
            )
            self.assertIn(
                "**Python fixture verdict:** `PASS`",
                markdown_path.read_text(encoding="utf-8"),
            )

    def test_committed_receipts_match_a_fresh_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            json_path = temporary / "summary.json"
            markdown_path = temporary / "summary.md"
            run(FIXTURE_PATH, json_path, markdown_path)
            self.assertEqual(
                json_path.read_bytes(),
                SUMMARY_JSON_PATH.read_bytes(),
            )
            self.assertEqual(
                markdown_path.read_bytes(),
                SUMMARY_MARKDOWN_PATH.read_bytes(),
            )

    def test_loader_rejects_vacuous_and_incomplete_suites(self) -> None:
        raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "empty.json"
            raw["cases"] = []
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "at least one case"):
                load_regression_suite(path)

    def test_registered_certificate_mismatch_fails_the_receipt(self) -> None:
        raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        raw["cases"][0]["expected"]["block_targets"] = [1, 0]
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            fixture_path = temporary / "mismatch.json"
            json_path = temporary / "summary.json"
            markdown_path = temporary / "summary.md"
            fixture_path.write_text(json.dumps(raw), encoding="utf-8")
            receipt = run(fixture_path, json_path, markdown_path)
            self.assertFalse(receipt["all_passed"])
            self.assertFalse(receipt["cases"][0]["passed"])
            self.assertIn(
                "**Python fixture verdict:** `FAIL`",
                markdown_path.read_text(encoding="utf-8"),
            )

    def test_custom_fixture_requires_explicit_outputs(self) -> None:
        with self.assertRaisesRegex(ValueError, "explicit JSON and Markdown"):
            run(FIXTURE_PATH.with_name("other.json"))

    def test_midas_contract_maps_every_theorem_to_live_checks(self) -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        lean_source = LEAN_PATH.read_text(encoding="utf-8")
        test_source = Path(__file__).read_text(encoding="utf-8")
        self.assertEqual(
            contract["schema_version"],
            "midas-relative-identifiability/v1",
        )
        self.assertEqual(
            [theorem["id"] for theorem in contract["theorems"]],
            ["T1", "T2", "T3", "T4"],
        )
        for theorem in contract["theorems"]:
            self.assertTrue(
                theorem["lean_declarations"] or theorem["python_regressions"]
            )
            for declaration in theorem["lean_declarations"]:
                self.assertIn(declaration, lean_source)
            for regression in theorem["python_regressions"]:
                self.assertIn(f"def {regression}", test_source)

    def test_lean_source_has_no_proof_placeholders(self) -> None:
        lean_source = LEAN_PATH.read_text(encoding="utf-8").lower()
        self.assertNotIn("sorry", lean_source)
        self.assertNotIn("admit", lean_source)

    @unittest.skipUnless(shutil.which("lake"), "lake is not installed")
    def test_lean_package_builds_when_available(self) -> None:
        receipt = run_lean_gate()
        self.assertTrue(receipt.built)
        self.assertEqual(receipt.toolchain, "leanprover/lean4:v4.31.0")


class ExhaustiveBinaryTableTests(unittest.TestCase):
    def test_all_three_by_three_binary_tables(self) -> None:
        families = tuple(
            family
            for size in range(4)
            for family in itertools.combinations(("e0", "e1", "e2"), size)
        )

        for flat_outcomes in itertools.product((0, 1), repeat=9):
            outcomes = tuple(
                tuple(flat_outcomes[row * 3 : (row + 1) * 3]) for row in range(3)
            )
            system = _system(outcomes)
            direct_partitions: dict[
                tuple[str, ...],
                tuple[tuple[str, ...], ...],
            ] = {}
            for family in families:
                indices = tuple(
                    system.experiments.index(experiment) for experiment in family
                )
                blocks: dict[tuple[object, ...], list[str]] = {}
                for realization, row in zip(
                    system.realizations,
                    outcomes,
                    strict=True,
                ):
                    transcript = tuple(row[index] for index in indices)
                    blocks.setdefault(transcript, []).append(realization)
                direct_partitions[family] = tuple(
                    tuple(block) for block in blocks.values()
                )

            for coarse in families:
                for rich in families:
                    if set(coarse).issubset(rich):
                        receipt = analyze_refinement(system, coarse, rich)
                        self.assertTrue(receipt.is_refinement)
                        coarse_blocks = direct_partitions[coarse]
                        rich_blocks = direct_partitions[rich]
                        self.assertEqual(
                            receipt.strict,
                            coarse_blocks != rich_blocks,
                        )
                        expected_splits = tuple(
                            tuple(
                                rich_block
                                for rich_block in rich_blocks
                                if set(coarse_block).intersection(rich_block)
                            )
                            for coarse_block in coarse_blocks
                            if sum(
                                bool(set(coarse_block).intersection(rich_block))
                                for rich_block in rich_blocks
                            )
                            > 1
                        )
                        self.assertEqual(receipt.split_blocks, expected_splits)
                        added = tuple(
                            experiment
                            for experiment in rich
                            if experiment not in coarse
                        )
                        expected_separators = tuple(
                            experiment
                            for experiment in added
                            if any(
                                len(
                                    {
                                        outcomes[
                                            system.realizations.index(realization)
                                        ][system.experiments.index(experiment)]
                                        for realization in block
                                    }
                                )
                                > 1
                                for block in coarse_blocks
                            )
                        )
                        self.assertEqual(
                            receipt.separating_experiments,
                            expected_separators,
                        )

            for target_values in itertools.product((0, 1), repeat=3):
                target = FiniteTarget("binary", target_values)
                expected_minimum: list[tuple[str, ...]] = []

                for family in families:
                    expected_identifiable = all(
                        len(
                            {
                                target_values[system.realizations.index(realization)]
                                for realization in block
                            }
                        )
                        == 1
                        for block in direct_partitions[family]
                    )

                    result = identify_target(system, target, family)
                    self.assertEqual(
                        isinstance(result, FactorizationCertificate),
                        expected_identifiable,
                    )
                    if expected_identifiable:
                        expected_minimum.append(family)

                search = minimal_identifying_families(system, target)
                if expected_minimum:
                    minimum_size = min(map(len, expected_minimum))
                    self.assertEqual(search.minimum_size, minimum_size)
                    self.assertEqual(
                        search.families,
                        tuple(
                            family
                            for family in expected_minimum
                            if len(family) == minimum_size
                        ),
                    )
                else:
                    self.assertIsNone(search.minimum_size)
                    self.assertIsInstance(
                        search.full_family_obstruction,
                        ObstructionCertificate,
                    )


if __name__ == "__main__":
    unittest.main()
