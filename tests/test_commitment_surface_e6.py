from __future__ import annotations

import hashlib
import unittest
from dataclasses import fields
from typing import Any

from experiments.commitment_surface.e6_analysis import (
    analyze_e6,
    build_run_manifest,
    cell_is_reusable,
    grid_spec_for_run_kind,
)
from experiments.commitment_surface.e6_core import (
    E6_BOOTSTRAP_EPOCHS,
    E6_CANDIDATE_PROPOSER,
    E6_CONFIRMATORY_GRID,
    E6_CONFIRMATORY_PARAMETERS,
    E6_GATE_METRICS,
    Candidate,
    CandidatePool,
    CommitmentSurfaceSignal,
    E6Arm,
    E6Config,
    GroundTruthSignal,
    audit_matched_rounds,
    collapse_trajectory,
    derive_e6_seed,
    plan_round,
    plan_self_training_loop,
)
from experiments.commitment_surface.e6_runtime import (
    GPU_MAX_CONTAINERS,
    GPU_TYPE,
    build_execution_strata,
    candidate_input_ids,
    paired_proposer_schedule,
    prioritize_strata,
    validate_stratum_result,
    validate_runtime_arms,
)


FROZEN_CONFIRMATORY_PARAMETERS = {
    "sizes": ("70m", "160m", "410m"),
    "moduli": (13, 17, 23),
    "seed_slots": (0, 1, 2),
    "arms": ("SC", "CS", "GT", "A-ref"),
    "base_seed": 20260713,
    "rounds": 6,
    "train_frac": 0.5,
    "train_shift_count": 3,
    "bootstrap_epochs": 160,
    "generations_per_input": 8,
    "candidate_proposer": "paired_half_mix",
    "generation_temperature": 0.8,
    "round_epochs": 40,
    "selection_fraction": 0.5,
    "lora_rank": 8,
    "lora_alpha": 16,
    "lora_dropout": 0.05,
    "lora_lr": 5e-4,
    "weight_decay": 0.0,
    "grad_clip": 1.0,
    "spectral_mass_fraction": 0.5,
    "patch_ce_threshold": 0.05,
    "collapse_tolerance": 0.05,
    "patch_dip_tolerance": 0.01,
    "transport_retention_fraction": 0.75,
    "generator_coverage_margin": 0.10,
    "candidate_batch_size": 32,
}


class CommitmentSurfaceE6Test(unittest.TestCase):
    def setUp(self) -> None:
        self.config = E6Config(modulus=13, seed_slot=0)
        self.pool = CandidatePool(
            round_index=1,
            candidates=tuple(
                Candidate(
                    f"{prefix}{index}",
                    input_id * 8 + index,
                    input_id,
                    majority if index < 5 else majority + index - 4,
                )
                for input_id, (prefix, majority) in enumerate((("a", 1), ("b", 4)))
                for index in range(8)
            ),
        )
        self.cs_signals = tuple(
            CommitmentSurfaceSignal(
                candidate.candidate_id,
                canonical_patch_ce=0.30 - 0.01 * candidate.order,
                transported_patch_ce=(
                    0.10
                    if candidate.order < 5 or 8 <= candidate.order < 13
                    else 0.01
                ),
            )
            for candidate in self.pool.candidates
        )
        self.gt_signals = tuple(
            GroundTruthSignal(candidate.candidate_id, candidate.order % 2 == 0)
            for candidate in self.pool.candidates
        )

    def test_frozen_grid_and_parameters_match_the_preregistration(self) -> None:
        self.assertEqual(E6_CONFIRMATORY_PARAMETERS, FROZEN_CONFIRMATORY_PARAMETERS)
        self.assertEqual(len(E6_CONFIRMATORY_GRID.expected_keys()), 108)
        self.assertEqual(E6_CONFIRMATORY_GRID.seed_slots, (0, 1, 2))
        self.assertEqual(E6_BOOTSTRAP_EPOCHS, 160)
        self.assertEqual(E6_CANDIDATE_PROPOSER, "paired_half_mix")

    def test_runner_uses_symmetric_current_adapter_proposals_on_l4(self) -> None:
        self.assertEqual(GPU_TYPE, "L4")
        self.assertEqual(GPU_MAX_CONTAINERS, 12)
        self.assertEqual(
            paired_proposer_schedule(8),
            ("SC", "CS", "SC", "CS", "SC", "CS", "SC", "CS"),
        )
        with self.assertRaisesRegex(ValueError, "even"):
            paired_proposer_schedule(7)

    def test_runner_groups_arm_cells_into_coupled_gpu_strata(self) -> None:
        manifest = build_run_manifest(
            FROZEN_CONFIRMATORY_PARAMETERS,
            run_kind="confirmatory",
            implementation_fingerprint="runner-test",
        )

        strata = build_execution_strata(manifest["cells"])

        self.assertEqual(len(strata), 27)
        self.assertTrue(all(len(stratum["cell_ids"]) == 4 for stratum in strata))
        self.assertEqual(strata[0]["stratum_id"], "70m__n13__slot0")
        ordered = prioritize_strata(strata)
        self.assertEqual(ordered[0]["size"], "410m")
        self.assertEqual(ordered[-1]["size"], "70m")

    def test_runner_requires_exact_stratum_result_cell_ids(self) -> None:
        expected = ("cell-SC", "cell-CS", "cell-A-ref")
        result = [{"cell_id": cell_id, "integrity_pass": True} for cell_id in expected]

        validated = validate_stratum_result(
            result,
            expected_cell_ids=expected,
        )

        self.assertEqual(tuple(cell["cell_id"] for cell in validated), expected)
        for invalid in (
            [],
            result[:-1],
            [result[0], result[0], result[2]],
            [result[1], result[0], result[2]],
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "exactly match"):
                    validate_stratum_result(
                        invalid,
                        expected_cell_ids=expected,
                    )
        with self.assertRaisesRegex(TypeError, "list"):
            validate_stratum_result(
                RuntimeError("worker failed"),
                expected_cell_ids=expected,
            )

    def test_candidate_inputs_cover_ood_and_novel_shift_images(self) -> None:
        inputs = candidate_input_ids(
            train_inputs=(0, 2),
            ood_inputs=(1, 3),
            novel_shifts=(2,),
            modulus=5,
        )
        self.assertEqual(inputs, (1, 2, 3, 4))

    def test_runtime_arm_validation_preserves_coupling_and_run_kind(self) -> None:
        validate_runtime_arms(("SC", "CS", "A-ref"), run_kind="smoke")
        validate_runtime_arms(("SC", "CS", "GT", "A-ref"), run_kind="confirmatory")
        with self.assertRaisesRegex(ValueError, "SC and CS"):
            validate_runtime_arms(("SC", "A-ref"), run_kind="development")
        with self.assertRaisesRegex(ValueError, "all four"):
            validate_runtime_arms(("SC", "CS", "A-ref"), run_kind="confirmatory")

    def test_namespaced_seed_derivation_matches_frozen_sha256_formula(self) -> None:
        expected = int.from_bytes(
            hashlib.sha256(
                b"e6|20260713|candidate|70m|13|SC-CS|2|1"
            ).digest()[:8],
            "big",
        )
        actual = derive_e6_seed(
            base_seed=20260713,
            namespace="candidate",
            size="70m",
            modulus=13,
            arm_scope="SC-CS",
            round_index=2,
            seed_slot=1,
        )
        self.assertEqual(actual, expected)
        self.assertNotEqual(
            actual,
            derive_e6_seed(
                base_seed=20260713,
                namespace="generation",
                size="70m",
                modulus=13,
                arm_scope="SC-CS",
                round_index=2,
                seed_slot=1,
            ),
        )
        with self.assertRaisesRegex(ValueError, "namespace"):
            derive_e6_seed(
                base_seed=20260713,
                namespace="labels",
                size="70m",
                modulus=13,
                arm_scope="CS",
                round_index=1,
                seed_slot=0,
            )

    def test_round_plan_matches_sc_and_cs_pool_and_selection_volume(self) -> None:
        round_plan = plan_round(
            self.pool,
            self.config,
            cs_signals=self.cs_signals,
            gt_signals=self.gt_signals,
        )
        sc = round_plan.selection_for(E6Arm.SC)
        cs = round_plan.selection_for(E6Arm.CS)
        gt = round_plan.selection_for(E6Arm.GT)
        a_ref = round_plan.selection_for(E6Arm.A_REF)

        self.assertEqual(sc.pool_digest, cs.pool_digest)
        self.assertEqual(sc.selected_candidate_count, 8)
        self.assertEqual(cs.selected_candidate_count, 8)
        self.assertEqual(gt.selected_candidate_count, 8)
        expected = ("a0", "a1", "a2", "a3", "a4", "b0", "b1", "b2")
        self.assertEqual(sc.selected_candidate_ids, expected)
        self.assertEqual(cs.selected_candidate_ids, expected)
        self.assertEqual(a_ref.selected_candidate_count, 0)
        self.assertEqual(a_ref.selected_candidate_ids, ())
        self.assertNotIn("correct", {field.name for field in fields(CommitmentSurfaceSignal)})
        self.assertNotIn(
            "truth_label", {field.name for field in fields(CommitmentSurfaceSignal)}
        )

    def test_cs_rejects_a_pool_without_enough_transport_survivors(self) -> None:
        insufficient = tuple(
            CommitmentSurfaceSignal(
                candidate.candidate_id,
                canonical_patch_ce=0.20,
                transported_patch_ce=0.10 if candidate.order < 7 else 0.0,
            )
            for candidate in self.pool.candidates
        )
        with self.assertRaisesRegex(ValueError, "eligible CS candidates"):
            plan_round(
                self.pool,
                self.config,
                cs_signals=insufficient,
                gt_signals=self.gt_signals,
            )

    def test_round_plan_requires_exact_generation_count_per_input(self) -> None:
        incomplete_pool = CandidatePool(
            round_index=1,
            candidates=self.pool.candidates[:-1],
        )
        with self.assertRaisesRegex(ValueError, "8 generations"):
            plan_round(
                incomplete_pool,
                self.config,
                cs_signals=self.cs_signals[:-1],
                gt_signals=self.gt_signals[:-1],
            )

    def test_pool_rejects_duplicate_candidate_identity_or_order(self) -> None:
        with self.assertRaisesRegex(ValueError, "candidate_id"):
            CandidatePool(
                round_index=1,
                candidates=(
                    Candidate("dup", 0, 0, 1),
                    Candidate("dup", 1, 1, 2),
                ),
            )
        with self.assertRaisesRegex(ValueError, "order"):
            CandidatePool(
                round_index=1,
                candidates=(
                    Candidate("a", 0, 0, 1),
                    Candidate("b", 0, 1, 2),
                ),
            )

    def test_six_round_loop_is_complete_and_audits_pairing(self) -> None:
        pools = tuple(
            CandidatePool(
                round_index=round_index,
                candidates=self.pool.candidates,
            )
            for round_index in range(1, 7)
        )
        cs_by_round = {index: self.cs_signals for index in range(1, 7)}
        gt_by_round = {index: self.gt_signals for index in range(1, 7)}

        loop = plan_self_training_loop(
            pools,
            self.config,
            cs_signals_by_round=cs_by_round,
            gt_signals_by_round=gt_by_round,
        )

        self.assertEqual([item.round_index for item in loop], list(range(1, 7)))
        audit = audit_matched_rounds(loop)
        self.assertTrue(audit["pass"])
        self.assertEqual(audit["matched_round_count"], 6)

        with self.assertRaisesRegex(ValueError, "exactly rounds 1..6"):
            plan_self_training_loop(
                pools[:-1],
                self.config,
                cs_signals_by_round=cs_by_round,
                gt_signals_by_round=gt_by_round,
            )

    def test_collapse_trajectory_uses_the_frozen_tolerance(self) -> None:
        self.assertEqual(
            collapse_trajectory((0.40, 0.60, 0.55, 0.549), tolerance=0.05),
            (False, False, False, True),
        )
        with self.assertRaisesRegex(ValueError, "tolerance must be finite"):
            collapse_trajectory((0.4, 0.5), tolerance=float("nan"))

    def test_confirmatory_manifest_is_exact_and_rejects_drift(self) -> None:
        manifest = build_run_manifest(
            FROZEN_CONFIRMATORY_PARAMETERS,
            run_kind="confirmatory",
            implementation_fingerprint="test-code",
            execution_environment={"torch": "2.7.1"},
        )
        self.assertEqual(manifest["expected_cell_count"], 108)
        self.assertEqual(len(manifest["cells"]), 108)
        self.assertTrue(manifest["confirmatory_config_pass"])
        self.assertEqual(len(manifest["manifest_id"]), 64)

        changed_code = build_run_manifest(
            FROZEN_CONFIRMATORY_PARAMETERS,
            run_kind="confirmatory",
            implementation_fingerprint="changed-code",
            execution_environment={"torch": "2.7.1"},
        )
        self.assertNotEqual(changed_code["manifest_id"], manifest["manifest_id"])

        drifted = dict(FROZEN_CONFIRMATORY_PARAMETERS)
        drifted["rounds"] = 5
        with self.assertRaisesRegex(ValueError, "rounds"):
            build_run_manifest(drifted, run_kind="confirmatory")

        extended = dict(FROZEN_CONFIRMATORY_PARAMETERS)
        extended["reward_weight"] = 0.5
        with self.assertRaisesRegex(ValueError, "unexpected:reward_weight"):
            build_run_manifest(extended, run_kind="confirmatory")

    def test_analysis_applies_all_frozen_gates_to_complete_grid(self) -> None:
        cells = self._complete_confirmatory_cells()

        analysis = analyze_e6(cells, grid_spec=E6_CONFIRMATORY_GRID)

        self.assertTrue(analysis["confirmatory_ready"])
        self.assertTrue(analysis["grid_audit"]["grid_complete"])
        self.assertTrue(analysis["g1_no_collapse"])
        self.assertTrue(analysis["sc_expected_collapse"])
        self.assertTrue(analysis["g2_load_bearing_gain"])
        self.assertTrue(analysis["g3_transport_survival"])
        self.assertTrue(analysis["g4_not_mere_coverage"])
        self.assertTrue(analysis["g5_exposure_integrity"])
        self.assertEqual(analysis["verdict"], "surface_supported")

    def test_pool_or_count_mismatch_blocks_confirmatory_readiness(self) -> None:
        for field, value in (
            ("pool_digest", "f" * 64),
            ("candidate_pool_count", 16),
            ("selected_candidate_count", 3),
        ):
            with self.subTest(field=field):
                cells = self._complete_confirmatory_cells()
                cs_cell = next(cell for cell in cells if cell["arm"] == "CS")
                cs_cell["rounds"][0][field] = value

                analysis = analyze_e6(cells, grid_spec=E6_CONFIRMATORY_GRID)

                self.assertFalse(analysis["g5_exposure_integrity"])
                self.assertFalse(analysis["confirmatory_ready"])
                self.assertEqual(analysis["verdict"], "pending_confirmatory_grid")

    def test_invalid_gain_or_selection_volume_blocks_confirmatory_readiness(self) -> None:
        cells = self._complete_confirmatory_cells()
        cells[0]["rounds"][0]["generator_gain"] = 1.01
        analysis = analyze_e6(cells, grid_spec=E6_CONFIRMATORY_GRID)
        self.assertFalse(analysis["grid_audit"]["cell_data_complete"])
        self.assertFalse(analysis["confirmatory_ready"])

        cells = self._complete_confirmatory_cells()
        for arm in ("SC", "CS"):
            cell = next(item for item in cells if item["arm"] == arm)
            cell["rounds"][0]["selected_candidate_count"] = 0
        analysis = analyze_e6(cells, grid_spec=E6_CONFIRMATORY_GRID)
        self.assertTrue(analysis["g5_exposure_integrity"])
        self.assertFalse(analysis["grid_audit"]["cell_data_complete"])
        self.assertFalse(analysis["confirmatory_ready"])

    def test_each_science_gate_has_a_negative_case(self) -> None:
        mutations = {
            "g2_load_bearing_gain": lambda row: row.update(
                canonical_normalized_patch_ce=0.0
            ),
            "g3_transport_survival": lambda row: row.update(
                transported_normalized_patch_ce=0.04
            ),
            "g4_not_mere_coverage": lambda row: row.update(generator_gain=0.14),
        }
        round_indexes = {
            "g2_load_bearing_gain": 3,
            "g3_transport_survival": 5,
            "g4_not_mere_coverage": 2,
        }
        for gate, mutate in mutations.items():
            with self.subTest(gate=gate):
                cells = self._complete_confirmatory_cells()
                for cell in cells:
                    if cell["arm"] == "CS":
                        mutate(cell["rounds"][round_indexes[gate]])

                analysis = analyze_e6(cells, grid_spec=E6_CONFIRMATORY_GRID)

                self.assertTrue(analysis["confirmatory_ready"])
                self.assertFalse(analysis[gate])
                self.assertEqual(analysis["verdict"], "kill_or_draw")

    def test_missing_duplicate_or_invalid_cell_blocks_confirmatory_verdict(self) -> None:
        cells = self._complete_confirmatory_cells()
        cells[-1] = dict(cells[0])
        analysis = analyze_e6(cells, grid_spec=E6_CONFIRMATORY_GRID)
        self.assertFalse(analysis["confirmatory_ready"])
        self.assertEqual(len(analysis["grid_audit"]["missing_cells"]), 1)
        self.assertEqual(len(analysis["grid_audit"]["duplicate_cells"]), 1)

        cells = self._complete_confirmatory_cells()
        cells[0]["rounds"][0][E6_GATE_METRICS[0]] = float("nan")
        analysis = analyze_e6(cells, grid_spec=E6_CONFIRMATORY_GRID)
        self.assertFalse(analysis["grid_audit"]["cell_data_complete"])
        self.assertFalse(analysis["confirmatory_ready"])

    def test_both_arms_collapsing_supports_intrinsic_hypothesis(self) -> None:
        cells = self._complete_confirmatory_cells()
        for cell in cells:
            if cell["arm"] != "CS":
                continue
            for row, accuracy in zip(
                cell["rounds"], (0.40, 0.60, 0.70, 0.58, 0.54, 0.50)
            ):
                row["canonical_ood_accuracy"] = accuracy

        analysis = analyze_e6(cells, grid_spec=E6_CONFIRMATORY_GRID)

        self.assertTrue(analysis["confirmatory_ready"])
        self.assertFalse(analysis["g1_no_collapse"])
        self.assertTrue(analysis["sc_expected_collapse"])
        self.assertEqual(analysis["verdict"], "intrinsic_supported")

    def test_resume_requires_complete_finite_trajectory_and_matching_metadata(self) -> None:
        cell = self._complete_confirmatory_cells()[0]
        cell_id = "70m__n13__slot0__SC"
        cell["run_manifest_id"] = "manifest"
        cell["cell_id"] = cell_id
        self.assertTrue(cell_is_reusable(cell, "manifest", cell_id))

        incomplete = dict(cell)
        incomplete["rounds"] = cell["rounds"][:-1]
        self.assertFalse(cell_is_reusable(incomplete, "manifest", cell_id))
        wrong_metadata = dict(cell)
        wrong_metadata["n"] = 17
        self.assertFalse(cell_is_reusable(wrong_metadata, "manifest", cell_id))
        self.assertFalse(cell_is_reusable(cell, "other", cell_id))

    def test_only_confirmatory_run_kind_uses_the_frozen_grid(self) -> None:
        self.assertIsNone(grid_spec_for_run_kind("smoke"))
        self.assertIsNone(grid_spec_for_run_kind("development"))
        self.assertEqual(
            grid_spec_for_run_kind("confirmatory"), E6_CONFIRMATORY_GRID
        )

    def test_smoke_can_pass_but_never_promotes_a_scientific_verdict(self) -> None:
        cells = [
            cell
            for cell in self._complete_confirmatory_cells()
            if cell["size"] == "70m"
            and cell["n"] == 13
            and cell["seed_slot"] == 0
            and cell["arm"] in {"SC", "CS", "A-ref"}
        ]
        analysis = analyze_e6(cells)
        self.assertTrue(analysis["smoke_pass"])
        self.assertFalse(analysis["confirmatory_ready"])
        self.assertEqual(analysis["verdict"], "pending_confirmatory_grid")

    def test_incomplete_analysis_does_not_claim_sc_collapse(self) -> None:
        analysis = analyze_e6([])
        self.assertIsNone(analysis["sc_expected_collapse"])

    @staticmethod
    def _complete_confirmatory_cells() -> list[dict[str, Any]]:
        accuracy = {
            "SC": (0.40, 0.55, 0.65, 0.55, 0.48, 0.45),
            "CS": (0.35, 0.45, 0.55, 0.62, 0.68, 0.70),
            "GT": (0.50, 0.65, 0.75, 0.82, 0.87, 0.90),
            "A-ref": (0.20, 0.20, 0.20, 0.20, 0.20, 0.20),
        }
        paraphrase = {
            "SC": (0.35, 0.48, 0.57, 0.49, 0.43, 0.40),
            "CS": (0.30, 0.40, 0.50, 0.57, 0.63, 0.65),
            "GT": (0.45, 0.58, 0.68, 0.76, 0.81, 0.84),
            "A-ref": (0.18, 0.18, 0.18, 0.18, 0.18, 0.18),
        }
        patch = {
            "SC": (0.01, 0.02, 0.03, 0.02, 0.01, 0.01),
            "CS": (0.02, 0.04, 0.06, 0.07, 0.08, 0.10),
            "GT": (0.03, 0.05, 0.08, 0.10, 0.12, 0.14),
            "A-ref": (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        }
        transported_patch = {
            "SC": (0.0, 0.01, 0.02, 0.01, 0.0, 0.0),
            "CS": (0.01, 0.03, 0.05, 0.06, 0.07, 0.08),
            "GT": (0.02, 0.04, 0.07, 0.09, 0.11, 0.12),
            "A-ref": (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        }
        cells: list[dict[str, Any]] = []
        for size, modulus, seed_slot, arm in E6_CONFIRMATORY_GRID.expected_keys():
            rounds = []
            for index in range(6):
                shared_pool = hashlib.sha256(
                    f"{size}|{modulus}|{seed_slot}|{index + 1}".encode()
                ).hexdigest()
                rounds.append(
                    {
                        "round": index + 1,
                        "canonical_ood_accuracy": accuracy[arm][index],
                        "paraphrase_ood_accuracy": paraphrase[arm][index],
                        "novel_k_equivariance_accuracy": accuracy[arm][index],
                        "canonical_normalized_patch_ce": patch[arm][index],
                        "transported_normalized_patch_ce": transported_patch[arm][index],
                        "generator_gain": 0.20 if arm == "CS" else 0.05,
                        "coverage_gain": 0.05 if arm == "CS" else 0.04,
                        "candidate_pool_count": 8,
                        "selected_candidate_count": 0 if arm == "A-ref" else 4,
                        "pool_digest": shared_pool,
                        "split_integrity_pass": True,
                        "reward_leakage_pass": True,
                        "patch_integrity_pass": True,
                    }
                )
            cells.append(
                {
                    "arm": arm,
                    "size": size,
                    "n": modulus,
                    "seed_slot": seed_slot,
                    "rounds": rounds,
                    "integrity_pass": True,
                }
            )
        return cells


if __name__ == "__main__":
    unittest.main()
