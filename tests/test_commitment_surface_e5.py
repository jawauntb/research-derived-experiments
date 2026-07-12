from __future__ import annotations

import hashlib
import unittest
from collections import Counter
from pathlib import Path

from experiments.commitment_surface.e5_core import (
    E5_CONFIRMATORY_GRID,
    E5_CONFIRMATORY_PARAMETERS,
    E5_GATE_METRICS,
    E5Arm,
    E5Config,
    ExposurePlan,
    SupervisedExposure,
    analyze_e5,
    audit_exposure,
    build_run_manifest,
    build_exposure_plans,
    cell_is_reusable,
    grid_spec_for_run_kind,
    lease_record_is_active,
    make_split,
    prioritize_launch_cells,
    validate_exposure_plans,
)

FROZEN_MODULI = (13, 17, 23)
FROZEN_SEEDS = (20260709, 20260809, 20260909)
FROZEN_CONFIRMATORY_PARAMETERS = {
    "sizes": ("70m", "160m", "410m"),
    "moduli": FROZEN_MODULI,
    "seeds": FROZEN_SEEDS,
    "arms": ("G-reg", "B-ref", "W-reg", "Cov", "A-ref"),
    "train_frac": 0.5,
    "train_shift_count": 3,
    "augmentation_multiplier": 3,
    "epochs": 160,
    "consistency_weight": 1.0,
    "lora_rank": 8,
    "lora_alpha": 16,
    "lora_dropout": 0.05,
    "lora_lr": 5e-4,
    "weight_decay": 0.0,
    "grad_clip": 1.0,
    "spectral_mass_fraction": 0.5,
    "candidate_batch_size": 32,
    "consistency_pair_batch_size": 1,
}
REPO_ROOT = Path(__file__).resolve().parents[1]
E5_DIRECTORY = REPO_ROOT / "experiments" / "commitment_surface"
FROZEN_EXECUTION_ENVIRONMENT = {
    "python": "3.12",
    "modal_client": "1.2.6",
    "dependencies": dict(
        line.split("==", maxsplit=1)
        for line in (E5_DIRECTORY / "e5_requirements.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if line
    ),
    "model_revisions": {
        "70m": "a39f36b100fe8a5377810d56c3f4789b9c53ac42",
        "160m": "50f5173d932e8e61f858120bcb800b97af589f46",
        "410m": "9879c9b5f8bea9051dcb0e68dff21493d67e9d4f",
    },
    "deployment": {
        "gpu": "L4",
        "memory_mib": 24576,
        "timeout_seconds": 21600,
        "max_containers": 12,
        "result_volume": "commitment-surface-e5-results-v2",
        "result_volume_version": 2,
        "cell_lease_dict": "commitment-surface-e5-cell-leases",
        "cell_lease_ttl_seconds": 22500,
        "pytorch_cuda_alloc_conf": "expandable_segments:True",
    },
}


class CommitmentSurfaceE5Test(unittest.TestCase):
    def setUp(self) -> None:
        self.config = E5Config(modulus=13, seed=20260709)
        self.split = make_split(self.config)
        self.plans = build_exposure_plans(self.split, self.config, offset=4)

    def test_split_and_intervention_sets_are_disjoint(self) -> None:
        self.assertFalse(set(self.split.train_inputs) & set(self.split.ood_inputs))
        self.assertFalse(set(self.split.k_train) & set(self.split.k_novel))
        self.assertEqual(
            set(self.split.train_inputs) | set(self.split.ood_inputs),
            set(range(self.config.modulus)),
        )

    def test_regularizers_never_receive_heldout_truth_labels(self) -> None:
        for arm in (E5Arm.G_REG, E5Arm.W_REG):
            audit = audit_exposure(self.plans[arm], self.split)
            self.assertEqual(audit.supervised_heldout_events, 0)
            self.assertEqual(audit.consistency_outside_train, 0)

        leaked = SupervisedExposure(
            self.split.ood_inputs[0],
            (self.split.ood_inputs[0] + 4) % self.config.modulus,
            "forbidden",
        )
        tampered = dict(self.plans)
        original = tampered[E5Arm.G_REG]
        tampered[E5Arm.G_REG] = ExposurePlan(
            E5Arm.G_REG,
            original.supervised + (leaked,),
            original.consistency,
        )
        with self.assertRaisesRegex(ValueError, "held-out truth labels"):
            validate_exposure_plans(tampered, self.split)

    def test_coverage_arm_matches_b_ref_label_exposure(self) -> None:
        b_audit = audit_exposure(self.plans[E5Arm.B_REF], self.split)
        cov_audit = audit_exposure(self.plans[E5Arm.COV], self.split)
        self.assertEqual(
            b_audit.supervised_heldout_events,
            cov_audit.supervised_heldout_events,
        )
        self.assertEqual(
            b_audit.supervised_heldout_unique,
            cov_audit.supervised_heldout_unique,
        )
        self.assertEqual(
            len(self.plans[E5Arm.B_REF].supervised),
            len(self.plans[E5Arm.COV].supervised),
        )

    def test_novel_shifts_never_appear_in_interventions(self) -> None:
        for arm in (E5Arm.G_REG, E5Arm.W_REG):
            used = {
                exposure.intervention_id
                for exposure in self.plans[arm].consistency
            }
            self.assertTrue(used)
            self.assertLessEqual(used, set(self.split.k_train))
            self.assertFalse(used & set(self.split.k_novel))

    def test_wrong_regularizer_is_volume_matched_in_every_frozen_stratum(
        self,
    ) -> None:
        for modulus in FROZEN_MODULI:
            for seed in FROZEN_SEEDS:
                with self.subTest(modulus=modulus, seed=seed):
                    config = E5Config(modulus=modulus, seed=seed)
                    split = make_split(config)
                    plans = build_exposure_plans(split, config, offset=4)
                    g_plan = plans[E5Arm.G_REG]
                    w_plan = plans[E5Arm.W_REG]
                    g_schedule = Counter(
                        (pair.source_input, pair.intervention_id)
                        for pair in g_plan.consistency
                    )
                    w_schedule = Counter(
                        (pair.source_input, pair.intervention_id)
                        for pair in w_plan.consistency
                    )

                    self.assertEqual(g_plan.supervised, w_plan.supervised)
                    self.assertEqual(g_schedule, w_schedule)
                    self.assertEqual(len(g_plan.consistency), len(w_plan.consistency))
                    self.assertTrue(
                        all(
                            pair.target_input in split.train_inputs
                            for pair in w_plan.consistency
                        )
                    )
                    wrong = w_plan.consistency[0].output_permutation
                    self.assertFalse(
                        any(
                            all(
                                wrong[value] == (value + shift) % modulus
                                for value in range(modulus)
                            )
                            for shift in range(modulus)
                        )
                    )

    def test_volume_mismatch_is_rejected(self) -> None:
        tampered = dict(self.plans)
        w_plan = tampered[E5Arm.W_REG]
        tampered[E5Arm.W_REG] = ExposurePlan(
            E5Arm.W_REG,
            w_plan.supervised,
            w_plan.consistency[:-1],
        )

        with self.assertRaisesRegex(ValueError, "volume-match"):
            validate_exposure_plans(tampered, self.split)

    def test_analysis_applies_frozen_generator_and_transport_gates(self) -> None:
        cells = []
        arm_metrics = {
            E5Arm.G_REG: (0.70, 0.61, 0.75, 0.10, 0.08),
            E5Arm.COV: (0.50, 0.45, 0.50, 0.04, 0.03),
            E5Arm.A_REF: (0.20, 0.18, 0.40, 0.01, 0.01),
            E5Arm.W_REG: (0.40, 0.35, 0.55, 0.02, 0.02),
            E5Arm.B_REF: (0.80, 0.72, 0.78, 0.12, 0.10),
        }
        for size, modulus, seed, arm_text in E5_CONFIRMATORY_GRID.expected_keys():
            values = arm_metrics[E5Arm(arm_text)]
            cells.append(
                {
                    "arm": arm_text,
                    "size": size,
                    "n": modulus,
                    "seed": seed,
                    "canonical_ood_accuracy": values[0],
                    "paraphrase_ood_accuracy": values[1],
                    "novel_k_equivariance_accuracy": values[2],
                    "canonical_normalized_patch_ce": values[3],
                    "paraphrase_normalized_patch_ce": values[4],
                    "integrity_pass": True,
                }
            )
        analysis = analyze_e5(cells, grid_spec=E5_CONFIRMATORY_GRID)
        self.assertTrue(analysis["confirmatory_ready"])
        self.assertTrue(analysis["grid_audit"]["grid_complete"])
        self.assertEqual(analysis["grid_audit"]["expected_cell_count"], 135)
        self.assertTrue(analysis["generator_learning_gate"])
        self.assertTrue(analysis["group_specificity_gate"])
        self.assertTrue(analysis["transport_gate"])
        self.assertEqual(analysis["verdict"], "generator_learning")

    def test_missing_or_duplicate_cell_blocks_confirmatory_verdict(self) -> None:
        cells = []
        for size, modulus, seed, arm in E5_CONFIRMATORY_GRID.expected_keys():
            cells.append(
                {
                    "arm": arm,
                    "size": size,
                    "n": modulus,
                    "seed": seed,
                    "canonical_ood_accuracy": 0.6,
                    "paraphrase_ood_accuracy": 0.6,
                    "novel_k_equivariance_accuracy": 0.6,
                    "canonical_normalized_patch_ce": 0.1,
                    "paraphrase_normalized_patch_ce": 0.1,
                    "integrity_pass": True,
                }
            )
        cells[-1] = dict(cells[0])

        analysis = analyze_e5(cells, grid_spec=E5_CONFIRMATORY_GRID)

        self.assertFalse(analysis["confirmatory_ready"])
        self.assertFalse(analysis["grid_audit"]["grid_complete"])
        self.assertEqual(len(analysis["grid_audit"]["missing_cells"]), 1)
        self.assertEqual(len(analysis["grid_audit"]["duplicate_cells"]), 1)
        self.assertEqual(analysis["verdict"], "pending_confirmatory_grid")

    def test_confirmatory_manifest_is_exact_and_rejects_drift(self) -> None:
        self.assertEqual(E5_CONFIRMATORY_PARAMETERS, FROZEN_CONFIRMATORY_PARAMETERS)
        config = dict(FROZEN_CONFIRMATORY_PARAMETERS)

        manifest = build_run_manifest(
            config,
            run_kind="confirmatory",
            execution_environment={"torch": "2.7.1"},
        )

        self.assertEqual(manifest["expected_cell_count"], 135)
        self.assertEqual(len(manifest["cells"]), 135)
        self.assertTrue(manifest["confirmatory_config_pass"])
        self.assertEqual(len(manifest["manifest_id"]), 64)

        changed_code = build_run_manifest(
            config,
            run_kind="confirmatory",
            implementation_fingerprint="different-code",
            execution_environment={"torch": "2.7.1"},
        )
        self.assertNotEqual(changed_code["manifest_id"], manifest["manifest_id"])
        changed_environment = build_run_manifest(
            config,
            run_kind="confirmatory",
            execution_environment={"torch": "2.7.0"},
        )
        self.assertNotEqual(
            changed_environment["manifest_id"], manifest["manifest_id"]
        )

        drifted = dict(config)
        drifted["epochs"] = 159
        with self.assertRaisesRegex(ValueError, "epochs"):
            build_run_manifest(drifted, run_kind="confirmatory")

    def test_launch_readiness_report_matches_current_manifest_source(self) -> None:
        digest = hashlib.sha256()
        for path in (
            E5_DIRECTORY / "modal_e5_generator_vs_coverage.py",
            E5_DIRECTORY / "e5_core.py",
            E5_DIRECTORY / "e5_requirements.txt",
        ):
            digest.update(path.name.encode("utf-8"))
            digest.update(path.read_bytes())
        implementation_fingerprint = digest.hexdigest()
        manifest = build_run_manifest(
            FROZEN_CONFIRMATORY_PARAMETERS,
            run_kind="confirmatory",
            implementation_fingerprint=implementation_fingerprint,
            execution_environment=FROZEN_EXECUTION_ENVIRONMENT,
        )
        report = (
            E5_DIRECTORY / "results" / "e5_launch_readiness_2026_07_10.md"
        ).read_text(encoding="utf-8")

        self.assertIn(implementation_fingerprint, report)
        self.assertIn(manifest["manifest_id"], report)

    def test_resume_requires_finite_gate_metrics_and_matching_manifest(self) -> None:
        cell = {
            "run_manifest_id": "manifest",
            "cell_id": "70m__n13__seed20260709__G-reg",
            "size": "70m",
            "n": 13,
            "seed": 20260709,
            "arm": "G-reg",
            "integrity_pass": True,
            **{metric: 0.5 for metric in E5_GATE_METRICS},
        }
        cell_id = str(cell["cell_id"])
        self.assertTrue(cell_is_reusable(cell, "manifest", cell_id))

        nonfinite = dict(cell)
        nonfinite[E5_GATE_METRICS[0]] = float("nan")
        self.assertFalse(cell_is_reusable(nonfinite, "manifest", cell_id))
        boolean_metric = dict(cell)
        boolean_metric[E5_GATE_METRICS[0]] = True
        self.assertFalse(cell_is_reusable(boolean_metric, "manifest", cell_id))
        impossible_accuracy = dict(cell)
        impossible_accuracy[E5_GATE_METRICS[0]] = 1.01
        self.assertFalse(
            cell_is_reusable(impossible_accuracy, "manifest", cell_id)
        )
        wrong_metadata = dict(cell)
        wrong_metadata["n"] = 17
        self.assertFalse(cell_is_reusable(wrong_metadata, "manifest", cell_id))
        self.assertFalse(cell_is_reusable(cell, "other", cell_id))

    def test_lease_activity_requires_a_finite_future_expiry(self) -> None:
        self.assertTrue(
            lease_record_is_active({"expires_at_unix": 11.0}, now_unix=10.0)
        )
        for record in (
            {"expires_at_unix": 10.0},
            {"expires_at_unix": float("nan")},
            {"expires_at_unix": True},
            {},
            None,
        ):
            with self.subTest(record=record):
                self.assertFalse(lease_record_is_active(record, now_unix=10.0))

    def test_invalid_cell_data_blocks_exact_confirmatory_grid(self) -> None:
        invalid_values = (float("nan"), float("inf"), None, "0.5", True)
        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value):
                cells = self._complete_confirmatory_cells()
                cells[0][E5_GATE_METRICS[0]] = invalid_value

                analysis = analyze_e5(cells, grid_spec=E5_CONFIRMATORY_GRID)

                self.assertTrue(analysis["grid_audit"]["grid_complete"])
                self.assertFalse(analysis["grid_audit"]["cell_data_complete"])
                self.assertFalse(analysis["confirmatory_ready"])
                self.assertEqual(analysis["verdict"], "pending_confirmatory_grid")

        cells = self._complete_confirmatory_cells()
        del cells[0][E5_GATE_METRICS[0]]
        analysis = analyze_e5(cells, grid_spec=E5_CONFIRMATORY_GRID)
        self.assertFalse(analysis["grid_audit"]["cell_data_complete"])
        self.assertFalse(analysis["confirmatory_ready"])

        for impossible_accuracy in (-0.01, 1.01):
            with self.subTest(impossible_accuracy=impossible_accuracy):
                cells = self._complete_confirmatory_cells()
                cells[0][E5_GATE_METRICS[0]] = impossible_accuracy
                analysis = analyze_e5(cells, grid_spec=E5_CONFIRMATORY_GRID)
                self.assertFalse(analysis["grid_audit"]["cell_data_complete"])
                self.assertFalse(analysis["confirmatory_ready"])

    def test_integrity_failure_blocks_exact_confirmatory_grid(self) -> None:
        for integrity_value in (False, None):
            with self.subTest(integrity_value=integrity_value):
                cells = self._complete_confirmatory_cells()
                cells[0]["integrity_pass"] = integrity_value

                analysis = analyze_e5(cells, grid_spec=E5_CONFIRMATORY_GRID)

                self.assertTrue(analysis["grid_audit"]["grid_complete"])
                self.assertFalse(analysis["grid_audit"]["cell_data_complete"])
                self.assertFalse(analysis["confirmatory_ready"])
                self.assertEqual(analysis["verdict"], "pending_confirmatory_grid")

    def test_run_kind_routes_only_confirmatory_to_frozen_grid(self) -> None:
        self.assertIsNone(grid_spec_for_run_kind("smoke"))
        self.assertIsNone(grid_spec_for_run_kind("development"))
        self.assertEqual(
            grid_spec_for_run_kind("confirmatory"), E5_CONFIRMATORY_GRID
        )

    @staticmethod
    def _complete_confirmatory_cells() -> list[dict[str, object]]:
        return [
            {
                "arm": arm,
                "size": size,
                "n": modulus,
                "seed": seed,
                **{metric: 0.5 for metric in E5_GATE_METRICS},
                "integrity_pass": True,
            }
            for size, modulus, seed, arm in E5_CONFIRMATORY_GRID.expected_keys()
        ]

    def test_launch_prioritizes_larger_models_and_regularizers(self) -> None:
        cells = [
            {"cell_id": "70-a", "size": "70m", "arm": "A-ref"},
            {"cell_id": "410-a", "size": "410m", "arm": "A-ref"},
            {"cell_id": "410-g", "size": "410m", "arm": "G-reg"},
            {"cell_id": "160-w", "size": "160m", "arm": "W-reg"},
        ]

        ordered = prioritize_launch_cells(cells)

        self.assertEqual(
            [cell["cell_id"] for cell in ordered],
            ["410-g", "410-a", "160-w", "70-a"],
        )

    def test_smoke_is_not_promoted_to_confirmatory_verdict(self) -> None:
        cells = []
        for arm in (E5Arm.G_REG, E5Arm.COV, E5Arm.A_REF):
            cells.append(
                {
                    "arm": arm.value,
                    "canonical_ood_accuracy": 0.5,
                    "paraphrase_ood_accuracy": 0.5,
                    "novel_k_equivariance_accuracy": 0.5,
                    "canonical_normalized_patch_ce": 0.1,
                    "paraphrase_normalized_patch_ce": 0.1,
                    "integrity_pass": True,
                }
            )
        analysis = analyze_e5(cells)
        self.assertTrue(analysis["smoke_pass"])
        self.assertFalse(analysis["confirmatory_ready"])
        self.assertEqual(analysis["verdict"], "pending_confirmatory_grid")


if __name__ == "__main__":
    unittest.main()
