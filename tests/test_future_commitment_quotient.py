from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast
from unittest.mock import patch

import numpy as np

from experiments.future_commitment_quotient.analysis import (
    GATE_ORDER,
    best_threshold,
    evaluate_gates,
    summarize_rows,
)
from experiments.future_commitment_quotient.core import (
    ALPHABET,
    CONDITIONS,
    FAMILIES,
    FiniteAgent,
    build_condition_pair,
    build_family,
    build_mutant,
    cross_bisimulation,
    distinguishing_word_lengths,
    quotient_partition,
    shortest_distinguishing_word,
    verify_agent,
    verify_conjugacy,
)
from experiments.future_commitment_quotient.run_experiment import (
    _claim_calibration_audit,
    render_summary_markdown,
    run_registered,
)
from scripts.build_future_commitment_quotient_pdf import build_pdf


ROOT = Path(__file__).resolve().parents[1]


def _canonicalize_numeric_receipt(value: object) -> object:
    if isinstance(value, float):
        return round(value, 12)
    if isinstance(value, list):
        return [_canonicalize_numeric_receipt(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _canonicalize_numeric_receipt(item)
            for key, item in value.items()
        }
    return value


class FutureCommitmentConstructionTests(unittest.TestCase):
    def test_registered_design_is_frozen_and_complete(self) -> None:
        design_path = (
            ROOT
            / "experiments"
            / "future_commitment_quotient"
            / "registered_design.json"
        )
        design = json.loads(design_path.read_text(encoding="utf-8"))

        self.assertEqual(
            design["artifact_contract"],
            "future-commitment-quotient-design/v1",
        )
        self.assertEqual(
            design["confirmatory_seeds"],
            {"start": 0, "stop_exclusive": 64},
        )
        self.assertEqual(
            design["conditions"],
            ["RP_CP", "RD_CP", "RP_CA", "RD_CA"],
        )
        self.assertEqual(design["expected_confirmatory_rows"], 768)
        self.assertEqual(len(design["fatal_gates"]), 7)

    def test_family_agents_are_total_typed_and_coordinate_injective(self) -> None:
        for family in FAMILIES:
            agent = build_family(family)
            diagnostics = verify_agent(agent)

            self.assertEqual(agent.alphabet, ALPHABET)
            self.assertTrue(diagnostics["transition_total"])
            self.assertTrue(diagnostics["coordinate_injective"])
            self.assertEqual(diagnostics["n_states"], len(agent.states))
            self.assertEqual(agent.coordinates.shape[1], 8)

    def test_agent_validation_rejects_noninjective_coordinates(self) -> None:
        agent = build_family("parity")
        invalid = FiniteAgent(
            name="invalid",
            states=agent.states,
            alphabet=agent.alphabet,
            transitions=agent.transitions,
            outputs=agent.outputs,
            coordinates=np.zeros_like(agent.coordinates),
        )

        with self.assertRaisesRegex(ValueError, "injective"):
            verify_agent(invalid)

    def test_agent_validation_rejects_invalid_transition_target(self) -> None:
        agent = build_family("parity")
        transitions = agent.transitions.copy()
        transitions[0, 0] = len(agent.states)
        invalid = FiniteAgent(
            name="invalid",
            states=agent.states,
            alphabet=agent.alphabet,
            transitions=transitions,
            outputs=agent.outputs,
            coordinates=agent.coordinates,
        )

        with self.assertRaisesRegex(ValueError, "transition target"):
            verify_agent(invalid)


class FutureCommitmentTheoremTests(unittest.TestCase):
    def test_identity_clone_is_equivalent(self) -> None:
        agent = build_family("parity")
        relation = cross_bisimulation(agent, agent)

        self.assertTrue(np.all(np.diag(relation)))
        self.assertIsNone(shortest_distinguishing_word(agent, 0, agent, 0))

    def test_constant_output_machine_collapses_to_one_quotient_block(self) -> None:
        coordinates = np.arange(16, dtype=np.float64).reshape(2, 8)
        machine = FiniteAgent(
            name="constant",
            states=("a", "b"),
            alphabet=("tick",),
            transitions=np.asarray([[1], [0]], dtype=np.int64),
            outputs=("defer", "defer"),
            coordinates=coordinates,
        )

        partition = quotient_partition(machine)

        self.assertEqual(partition, ((0, 1),))

    def test_one_state_machine_is_already_a_minimal_quotient(self) -> None:
        machine = FiniteAgent(
            name="one-state",
            states=("only",),
            alphabet=("tick",),
            transitions=np.asarray([[0]], dtype=np.int64),
            outputs=("defer",),
            coordinates=np.zeros((1, 8), dtype=np.float64),
        )

        self.assertEqual(quotient_partition(machine), ((0,),))
        self.assertIsNone(shortest_distinguishing_word(machine, 0, machine, 0))

    def test_same_current_output_states_split_on_future_commitment(self) -> None:
        machine = FiniteAgent(
            name="future-split",
            states=("left", "right", "accept", "reject"),
            alphabet=("tick",),
            transitions=np.asarray([[2], [3], [2], [3]], dtype=np.int64),
            outputs=("defer", "defer", "accept", "reject"),
            coordinates=np.arange(32, dtype=np.float64).reshape(4, 8),
        )

        self.assertEqual(
            quotient_partition(machine),
            ((0,), (1,), (2,), (3,)),
        )
        self.assertEqual(
            shortest_distinguishing_word(machine, 0, machine, 1),
            ("tick",),
        )
        self.assertEqual(
            shortest_distinguishing_word(machine, 2, machine, 3),
            (),
        )

    def test_equal_current_outputs_can_have_delayed_witness(self) -> None:
        base = build_family("parity")
        mutant = build_mutant(base, "parity")

        witness = shortest_distinguishing_word(base, 0, mutant, 0)

        self.assertIsNotNone(witness)
        self.assertEqual(len(witness or ()), 3)
        self.assertLess(len(witness or ()), len(base.states) * len(mutant.states))

    def test_cross_bisimulation_rejects_alphabet_mismatch(self) -> None:
        base = build_family("parity")
        mismatched = FiniteAgent(
            name="mismatched",
            states=base.states,
            alphabet=("ZERO", *base.alphabet[1:]),
            transitions=base.transitions,
            outputs=base.outputs,
            coordinates=base.coordinates,
        )

        with self.assertRaisesRegex(ValueError, "same intervention alphabet"):
            cross_bisimulation(base, mismatched)

    def test_mutant_preserves_every_depth_one_commitment(self) -> None:
        for family in FAMILIES:
            base = build_family(family)
            mutant = build_mutant(base, family)
            self.assertEqual(base.outputs, mutant.outputs)
            for state in range(len(base.states)):
                for action_index in range(len(ALPHABET)):
                    left = base.transitions[state, action_index]
                    right = mutant.transitions[state, action_index]
                    self.assertEqual(base.outputs[left], mutant.outputs[right])

    def test_mutant_builder_rejects_non_load_bearing_alteration(self) -> None:
        base = build_family("parity")

        with (
            patch(
                "experiments.future_commitment_quotient.core."
                "shortest_distinguishing_word",
                return_value=None,
            ),
            self.assertRaisesRegex(ValueError, "not delayed and load-bearing"),
        ):
            build_mutant(base, "parity")

    def test_scrambled_conjugate_preserves_quotient_and_behavior(self) -> None:
        pair = build_condition_pair("modulo_three", seed=7, condition="RD_CP")

        self.assertTrue(verify_conjugacy(pair.left, pair.right, pair.alignment))
        self.assertTrue(
            np.all(pair.relation[np.arange(len(pair.alignment)), pair.alignment])
        )
        self.assertTrue(pair.scramble_integrity["coordinate_injective"])
        self.assertTrue(pair.scramble_integrity["geometry_changed"])
        self.assertTrue(pair.scramble_integrity["nonidentity_permutation"])
        self.assertEqual(pair.metrics["behavioral_disagreement"], 0.0)

    def test_coordinate_preserved_mutant_breaks_future_equivalence(self) -> None:
        pair = build_condition_pair("order", seed=11, condition="RP_CA")

        self.assertEqual(pair.metrics["coordinate_equality"], 1.0)
        self.assertEqual(pair.metrics["current_output_agreement"], 1.0)
        self.assertEqual(pair.metrics["depth_one_agreement"], 1.0)
        self.assertLess(cast(float, pair.metrics["quotient_agreement"]), 1.0)
        self.assertGreater(
            cast(float, pair.metrics["behavioral_disagreement"]),
            0.0,
        )
        self.assertGreaterEqual(
            cast(int, pair.metrics["shortest_witness_length"]),
            2,
        )

    def test_witness_and_bisimulation_agree_for_every_state_pair(self) -> None:
        base = build_family("modulo_three")
        mutant = build_mutant(base, "modulo_three")
        relation = cross_bisimulation(base, mutant)
        witness_lengths = distinguishing_word_lengths(base, mutant)

        for left_state in range(len(base.states)):
            for right_state in range(len(mutant.states)):
                witness = shortest_distinguishing_word(
                    base,
                    left_state,
                    mutant,
                    right_state,
                )
                self.assertEqual(
                    bool(relation[left_state, right_state]),
                    witness is None,
                )
                expected_length = -1 if witness is None else len(witness)
                self.assertEqual(
                    int(witness_lengths[left_state, right_state]),
                    expected_length,
                )


class FutureCommitmentAnalysisTests(unittest.TestCase):
    def test_claim_calibration_is_structured_and_anchored(self) -> None:
        audit = _claim_calibration_audit()

        self.assertTrue(audit["identifiers_match"])
        self.assertTrue(audit["machine_checks_pass"])
        self.assertTrue(audit["paper_sha256"]["matches"])
        self.assertTrue(audit["independent_review"]["approved"])
        self.assertEqual(audit["human_review"]["status"], "pending")
        self.assertTrue(audit["pass"])
        self.assertTrue(
            all(
                check["evidence_anchor_present"]
                and check["required_content_matches"]
                and all(check["required_content_present"].values())
                for check in audit["checks"].values()
            )
        )

    def test_claim_calibration_rejects_missing_required_content(self) -> None:
        package = ROOT / "experiments" / "future_commitment_quotient"
        paper_path = ROOT / "papers" / "future_commitment_quotient" / "paper.md"
        phrase = "This paper does not rescue that mechanism."
        mutated_paper = paper_path.read_text(encoding="utf-8").replace(phrase, "")
        checklist = json.loads(
            (package / "claim_calibration.json").read_text(encoding="utf-8")
        )

        with TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            temporary_paper = temporary_root / "paper.md"
            temporary_checklist = temporary_root / "claim_calibration.json"
            temporary_paper.write_text(mutated_paper, encoding="utf-8")
            checklist["paper_sha256"] = hashlib.sha256(
                temporary_paper.read_bytes()
            ).hexdigest()
            temporary_checklist.write_text(
                json.dumps(checklist, indent=2, sort_keys=True),
                encoding="utf-8",
            )

            audit = _claim_calibration_audit(
                calibration_path=temporary_checklist,
                paper_path=temporary_paper,
            )

        self.assertTrue(audit["paper_sha256"]["matches"])
        self.assertFalse(audit["machine_checks_pass"])
        self.assertFalse(
            audit["checks"]["prior_constraint_swap_null_preserved"][
                "required_content_present"
            ][phrase]
        )
        self.assertFalse(audit["pass"])

    def test_best_threshold_handles_constant_baseline(self) -> None:
        scores = np.ones(8, dtype=np.float64)
        labels = np.asarray([True, True, True, True, False, False, False, False])

        rule, accuracy = best_threshold(scores, labels)

        self.assertEqual(
            rule,
            {
                "kind": "constant_prediction",
                "prediction": True,
            },
        )
        self.assertEqual(accuracy, 0.5)

    def test_best_threshold_rejects_nonfinite_scores(self) -> None:
        scores = np.asarray([0.0, np.nan], dtype=np.float64)
        labels = np.asarray([True, False], dtype=bool)

        with self.assertRaisesRegex(ValueError, "scores must be finite"):
            best_threshold(scores, labels)

    def test_registered_factorial_passes_only_quotient_predictor(self) -> None:
        rows = []
        for family in FAMILIES:
            for seed in range(4):
                for condition in CONDITIONS:
                    rows.append(
                        build_condition_pair(
                            family,
                            seed=seed,
                            condition=condition,
                        ).to_row()
                    )

        summary = summarize_rows(rows, expected_seeds=range(4))

        self.assertEqual(
            summary["predictors"]["quotient_agreement"]["balanced_accuracy"],
            1.0,
        )
        for baseline in (
            "coordinate_geometry",
            "current_output_agreement",
            "depth_one_agreement",
        ):
            self.assertLessEqual(
                summary["predictors"][baseline]["balanced_accuracy"],
                0.5,
            )

    def test_f0_rejects_a_duplicate_that_masks_a_missing_cell(self) -> None:
        rows = [
            build_condition_pair(
                family,
                seed=seed,
                condition=condition,
            ).to_row()
            for family in FAMILIES
            for seed in range(2)
            for condition in CONDITIONS
        ]
        missing_index = next(
            index
            for index, row in enumerate(rows)
            if row["family"] == "parity"
            and row["seed"] == 0
            and row["condition"] == "RP_CP"
        )
        duplicate_index = next(
            index
            for index, row in enumerate(rows)
            if row["family"] == "parity"
            and row["seed"] == 1
            and row["condition"] == "RP_CP"
        )
        rows[missing_index] = dict(rows[duplicate_index])

        summary = summarize_rows(
            rows,
            expected_rows=24,
            expected_seeds=range(2),
        )

        provenance = summary["gates"]["F0_CONSTRUCTION_PROVENANCE"]
        self.assertFalse(provenance["pass"])
        self.assertFalse(provenance["observed"]["factorial_cells_exact"])

    def test_g4_rejects_a_family_failure_hidden_by_pooling(self) -> None:
        rows = [
            build_condition_pair(
                family,
                seed=0,
                condition=condition,
            ).to_row()
            for family in FAMILIES
            for condition in CONDITIONS
        ]

        def synthetic_predictor(
            _rows: object,
            *,
            metric: str,
        ) -> dict[str, object]:
            fold_accuracies = {family: 0.5 for family in FAMILIES}
            pooled_accuracy = 0.5
            if metric == "quotient_agreement":
                fold_accuracies = {family: 1.0 for family in FAMILIES}
                pooled_accuracy = 1.0
            elif metric == "coordinate_geometry_correlation":
                fold_accuracies["modulo_three"] = 1.0
                fold_accuracies["order"] = 0.0
            return {
                "balanced_accuracy": pooled_accuracy,
                "folds": {
                    family: {"test_balanced_accuracy": accuracy}
                    for family, accuracy in fold_accuracies.items()
                },
            }

        with patch(
            "experiments.future_commitment_quotient.analysis.leave_one_family_out",
            side_effect=synthetic_predictor,
        ):
            summary = summarize_rows(rows, expected_seeds=(0,))

        self.assertTrue(summary["gates"]["G3_FACTORIAL_PREDICTOR_SEPARATION"]["pass"])
        self.assertFalse(summary["per_family"]["modulo_three"]["predictor_separation"])
        self.assertFalse(summary["gates"]["G4_FAMILY_TRANSFER"]["pass"])

    def test_gate_failures_are_noncompensatory(self) -> None:
        passing = {gate: {"pass": True} for gate in GATE_ORDER}
        self.assertEqual(
            evaluate_gates(passing)["decision"],
            "ACCEPT_SCOPED_FINITE_QUOTIENT_CLAIM",
        )

        for gate in passing:
            mutated = {name: dict(result) for name, result in passing.items()}
            mutated[gate]["pass"] = False
            verdict = evaluate_gates(mutated)
            self.assertEqual(
                verdict["decision"],
                "WITHHOLD_SCOPED_FINITE_QUOTIENT_CLAIM",
            )
            self.assertIn(gate, verdict["failed_gates"])


class FutureCommitmentArtifactTests(unittest.TestCase):
    def test_committed_receipts_match_a_fresh_registered_run(self) -> None:
        package = ROOT / "experiments" / "future_commitment_quotient"
        payload = run_registered()
        committed_rows = [
            json.loads(line)
            for line in (package / "results" / "registered_rows.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        summary_text = (package / "results" / "summary.json").read_text(
            encoding="utf-8"
        )
        committed_summary = json.loads(
            summary_text,
            parse_constant=lambda value: self.fail(
                f"non-standard JSON constant: {value}"
            ),
        )

        self.assertEqual(
            _canonicalize_numeric_receipt(payload["rows"]),
            _canonicalize_numeric_receipt(committed_rows),
        )
        self.assertEqual(
            _canonicalize_numeric_receipt(payload["summary"]),
            _canonicalize_numeric_receipt(committed_summary),
        )
        self.assertEqual(
            render_summary_markdown(payload),
            (package / "results" / "summary.md").read_text(encoding="utf-8"),
        )
        json.dumps(payload["summary"], allow_nan=False)

    def test_pdf_builder_writes_parseable_synchronized_copies(self) -> None:
        with TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            output = temporary_root / "paper.pdf"
            copy = temporary_root / "copy.pdf"
            text_path = temporary_root / "paper.txt"

            build_pdf(output_pdf=output, copy_pdf=copy)
            info = subprocess.run(
                ["pdfinfo", str(output)],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            subprocess.run(
                ["pdftotext", str(output), str(text_path)],
                check=True,
            )
            extracted_text = text_path.read_text(encoding="utf-8")
            output_bytes = output.read_bytes()
            copy_bytes = copy.read_bytes()
            output_size = output.stat().st_size

        self.assertEqual(output_bytes, copy_bytes)
        self.assertGreater(output_size, 100_000)
        self.assertIn("Pages:", info)
        self.assertIn("The Coordinates Are Not the Causal Object", extracted_text)
        self.assertIn("ACCEPT_SCOPED_FINITE_QUOTIENT_CLAIM", extracted_text)
        self.assertIn("References", extracted_text)
