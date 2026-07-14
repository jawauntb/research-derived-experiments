from __future__ import annotations

import unittest

from experiments.common.causal_use import (
    CausalUseObservation,
    evaluate_synthetic_scm_feature,
    summarize_causal_use,
)


def fixture(kind: str, *, scale: float = 1.0) -> list[CausalUseObservation]:
    rows: list[CausalUseObservation] = []
    for surface in ("choice", "policy"):
        for replicate_index in range(4):
            for dose in (0.0, 0.5, 1.0):
                mass = scale * (1.0 + dose)
                jitter = 0.01 * (replicate_index - 1.5)
                if kind == "causal":
                    specific_per_mass = dose * (0.9 if surface == "choice" else 0.7) + jitter
                elif kind == "decodable_only":
                    specific_per_mass = jitter
                elif kind == "null":
                    specific_per_mass = -0.1 * dose + jitter
                else:
                    raise ValueError(kind)
                control_per_mass = 0.2 * dose
                rows.append(
                    CausalUseObservation(
                        surface=surface,
                        replicate=f"seed-{replicate_index}",
                        dose=dose,
                        target_loss_delta=(control_per_mass + specific_per_mass) * mass,
                        wrong_subspace_loss_delta=control_per_mass * mass,
                        removed_mass=mass,
                    )
                )
    return rows


class CausalUseTests(unittest.TestCase):
    def test_declared_effect_profiles_rank_correctly(self) -> None:
        causal = summarize_causal_use(fixture("causal"), bootstrap_samples=100)
        decodable = summarize_causal_use(fixture("decodable_only"), bootstrap_samples=100)
        null = summarize_causal_use(fixture("null"), bootstrap_samples=100)
        self.assertGreater(causal.transport_score, decodable.transport_score)
        self.assertGreaterEqual(decodable.transport_score, null.transport_score)
        self.assertGreater(causal.ci_low, 0.1)

    def test_equal_decodability_does_not_imply_equal_causal_use(self) -> None:
        causal = evaluate_synthetic_scm_feature("causal")
        decodable = evaluate_synthetic_scm_feature("decodable_only")
        null = evaluate_synthetic_scm_feature("null")

        self.assertEqual(causal.decoding_accuracy, 1.0)
        self.assertEqual(decodable.decoding_accuracy, causal.decoding_accuracy)
        self.assertEqual(null.decoding_accuracy, 0.5)

        causal_summary = summarize_causal_use(list(causal.observations), bootstrap_samples=100)
        decodable_summary = summarize_causal_use(
            list(decodable.observations), bootstrap_samples=100
        )
        null_summary = summarize_causal_use(list(null.observations), bootstrap_samples=100)
        self.assertGreater(causal_summary.ci_low, 0.0)
        self.assertEqual(decodable_summary.transport_score, 0.0)
        self.assertEqual(null_summary.transport_score, 0.0)

    def test_mass_normalization_is_invariant_to_width_or_activation_scale(self) -> None:
        narrow = summarize_causal_use(fixture("causal", scale=1.0), bootstrap_samples=100)
        wide = summarize_causal_use(fixture("causal", scale=8.0), bootstrap_samples=100)
        self.assertAlmostEqual(narrow.transport_score, wide.transport_score, places=12)
        self.assertAlmostEqual(narrow.ci_low, wide.ci_low, places=12)

    def test_transport_score_is_the_weakest_commitment_surface(self) -> None:
        summary = summarize_causal_use(fixture("causal"), bootstrap_samples=100)
        per_surface = {surface.surface: surface.positive_auc for surface in summary.surfaces}
        self.assertEqual(summary.transport_score, min(per_surface.values()))
        self.assertLess(per_surface["policy"], per_surface["choice"])

    def test_incomplete_replicate_grid_fails_closed(self) -> None:
        rows = fixture("causal")
        rows.pop()
        with self.assertRaisesRegex(ValueError, "complete unique dose grid"):
            summarize_causal_use(rows, bootstrap_samples=10)


if __name__ == "__main__":
    unittest.main()
