from __future__ import annotations

import unittest

from experiments.commitment_surface.e5_core import (
    E5Arm,
    E5Config,
    ExposurePlan,
    SupervisedExposure,
    analyze_e5,
    audit_exposure,
    build_exposure_plans,
    make_split,
    validate_exposure_plans,
)


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

    def test_analysis_applies_frozen_generator_and_transport_gates(self) -> None:
        cells = []
        arm_metrics = {
            E5Arm.G_REG: (0.70, 0.61, 0.75, 0.10, 0.08),
            E5Arm.COV: (0.50, 0.45, 0.50, 0.04, 0.03),
            E5Arm.A_REF: (0.20, 0.18, 0.40, 0.01, 0.01),
            E5Arm.W_REG: (0.40, 0.35, 0.55, 0.02, 0.02),
            E5Arm.B_REF: (0.80, 0.72, 0.78, 0.12, 0.10),
        }
        for arm, values in arm_metrics.items():
            for seed in range(3):
                cells.append(
                    {
                        "arm": arm.value,
                        "seed": seed,
                        "canonical_ood_accuracy": values[0],
                        "paraphrase_ood_accuracy": values[1],
                        "novel_k_equivariance_accuracy": values[2],
                        "canonical_normalized_patch_ce": values[3],
                        "paraphrase_normalized_patch_ce": values[4],
                        "integrity_pass": True,
                    }
                )
        analysis = analyze_e5(cells)
        self.assertTrue(analysis["confirmatory_ready"])
        self.assertTrue(analysis["generator_learning_gate"])
        self.assertTrue(analysis["group_specificity_gate"])
        self.assertTrue(analysis["transport_gate"])
        self.assertEqual(analysis["verdict"], "generator_learning")

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
