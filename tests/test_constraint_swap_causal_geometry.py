from __future__ import annotations

import copy
import json
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch

from experiments.constraint_swap_causal_geometry.analysis import (
    build_nuisance_rdms,
    summarize_registered_rows,
)
from experiments.constraint_swap_causal_geometry.core import (
    ExperimentConfig,
    GridTopology,
    action_histogram,
    all_decision_units,
    crossnobis_rdm,
    evaluate_gates,
    fit_crossnobis_precision,
    fit_low_rank_transport,
    future_language,
    oracle_action,
    partial_alignment,
    reachability_rdm,
)
from experiments.constraint_swap_causal_geometry.model import (
    collect_context,
    evaluate_context_accuracy,
    matched_random_transport,
    select_probe_units,
    train_model,
)


ROOT = Path(__file__).resolve().parents[1]


class ConstraintSwapWorldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.topology = GridTopology("torus", width=6, height=6)

    def test_registered_design_is_frozen_and_typed(self) -> None:
        path = (
            ROOT
            / "experiments"
            / "constraint_swap_causal_geometry"
            / "registered_design.json"
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            payload["artifact_contract"],
            "constraint-swap-causal-geometry/v1",
        )
        self.assertEqual(payload["confirmatory_seeds"], {"start": 0, "stop_exclusive": 32})
        self.assertEqual(payload["transport"]["rank"], 4)
        self.assertEqual(len(payload["fatal_gates"]), 7)

    def test_future_language_is_exact_and_handles_unreachable_goal(self) -> None:
        reachable = ((2, 1), (4, 3))
        unreachable = ((2, 1), (4, 2))

        phi_reachable = future_language(
            self.topology,
            reachable,
            constraint="A",
            horizon=4,
        )
        phi_unreachable = future_language(
            self.topology,
            unreachable,
            constraint="A",
            horizon=4,
        )

        self.assertEqual(phi_reachable.shape, (5**4,))
        self.assertGreater(float(np.sum(phi_reachable**2)), 0.0)
        self.assertEqual(float(np.sum(phi_unreachable**2)), 0.0)

    def test_constraint_languages_and_oracle_actions_are_orthogonal(self) -> None:
        unit = ((1, 1), (2, 0))
        self.assertGreater(
            float(np.sum(future_language(self.topology, unit, "A", horizon=4) ** 2)),
            0.0,
        )
        self.assertEqual(
            float(np.sum(future_language(self.topology, unit, "B", horizon=4) ** 2)),
            0.0,
        )
        self.assertEqual(oracle_action(unit, "A"), 1)
        self.assertEqual(oracle_action(unit, "B"), 0)

    def test_full_symmetric_schedule_matches_action_histograms(self) -> None:
        units = all_decision_units(self.topology)
        self.assertEqual(
            action_histogram(units, "A"),
            action_histogram(units, "B"),
        )

    def test_reachability_rdms_are_symmetric_and_distinct(self) -> None:
        units = all_decision_units(self.topology)[::13][:32]
        rdm_a, volumes_a = reachability_rdm(
            self.topology,
            units,
            "A",
            horizon=4,
        )
        rdm_b, volumes_b = reachability_rdm(
            self.topology,
            units,
            "B",
            horizon=4,
        )
        np.testing.assert_allclose(rdm_a, rdm_a.T)
        np.testing.assert_allclose(np.diag(rdm_a), 0.0)
        self.assertFalse(np.allclose(rdm_a, rdm_b))
        self.assertEqual(volumes_a.shape, volumes_b.shape)


class ConstraintSwapMetricTests(unittest.TestCase):
    def test_nuisance_builder_excludes_constant_columns_and_remains_full_rank(self) -> None:
        topology = GridTopology("torus", width=6, height=6)
        units = all_decision_units(topology)[::17][:48]
        nuisance, diagnostics = build_nuisance_rdms(topology, units, horizon=4)
        self.assertEqual(nuisance.shape[:2], (48, 48))
        self.assertTrue(diagnostics["full_rank"])
        self.assertNotIn("history_identity", diagnostics["included"])
        self.assertIn("history_identity", diagnostics["constant_controls"])

    def test_crossnobis_and_partial_alignment_recover_injected_geometry(self) -> None:
        rng = np.random.default_rng(7)
        coordinates = rng.normal(size=(18, 2))
        split_one = np.repeat(coordinates[:, None, :], 4, axis=1)
        split_two = np.repeat(coordinates[:, None, :], 4, axis=1)
        split_one += rng.normal(0, 0.02, size=split_one.shape)
        split_two += rng.normal(0, 0.02, size=split_two.shape)
        hidden = np.concatenate([split_one, split_two], axis=1)

        precision = fit_crossnobis_precision(hidden, shrinkage=0.1)
        hidden_rdm = crossnobis_rdm(hidden, precision=precision)
        target_rdm = np.sum(
            (coordinates[:, None, :] - coordinates[None, :, :]) ** 2,
            axis=-1,
        )
        nuisance = np.abs(
            rng.normal(size=(18, 1)) - rng.normal(size=(1, 18))
        )[..., None]

        result = partial_alignment(hidden_rdm, target_rdm, nuisance)

        self.assertGreater(result["correlation"], 0.9)
        self.assertGreater(result["residual_target_norm"], 0.0)
        self.assertTrue(result["full_rank"])
        triangle = np.triu_indices(len(coordinates), k=1)
        hidden_vector = hidden_rdm[triangle]
        target_vector = target_rdm[triangle]
        design = np.column_stack(
            [np.ones(len(hidden_vector)), nuisance[..., 0][triangle]]
        )
        projection = design @ np.linalg.pinv(design)
        expected = np.corrcoef(
            hidden_vector - projection @ hidden_vector,
            target_vector - projection @ target_vector,
        )[0, 1]
        self.assertAlmostEqual(result["correlation"], expected, places=12)

    def test_low_rank_transport_generalizes_to_heldout_rows(self) -> None:
        rng = np.random.default_rng(11)
        source = rng.normal(size=(80, 10))
        left = rng.normal(size=(10, 2))
        right = rng.normal(size=(2, 10))
        target = source + source @ left @ right + 0.1
        transport = fit_low_rank_transport(
            source[:50],
            target[:50],
            rank=2,
            ridge=1e-6,
        )

        moved = transport.apply(source[50:], dose=1.0)
        baseline_error = float(np.mean((source[50:] - target[50:]) ** 2))
        moved_error = float(np.mean((moved - target[50:]) ** 2))

        self.assertLess(moved_error, baseline_error * 0.05)
        np.testing.assert_allclose(transport.apply(source[50:], dose=0.0), source[50:])

    def test_gate_failures_are_noncompensatory(self) -> None:
        passing = {
            "F0_integrity_identifiability": {"pass": True},
            "F1_competence_measurement_sensitivity": {"pass": True},
            "G1_constraint_specific_geometry": {"pass": True},
            "G2_swap_tracking": {"pass": True},
            "G3_selective_impairment": {"pass": True},
            "G4_selective_rescue": {"pass": True},
            "G5_topology_transport": {"pass": True},
        }
        verdict = evaluate_gates(passing)
        self.assertEqual(verdict["decision"], "ACCEPT_SCOPED_CAUSAL_CLAIM")

        for gate in passing:
            mutated = copy.deepcopy(passing)
            mutated[gate]["pass"] = False
            verdict = evaluate_gates(mutated)
            self.assertNotEqual(verdict["decision"], "ACCEPT_SCOPED_CAUSAL_CLAIM")
            self.assertIn(gate, verdict["failed_gates"])

    def test_registered_config_has_disjoint_smoke_and_confirmatory_seeds(self) -> None:
        config = ExperimentConfig.registered()
        self.assertTrue(set(config.smoke_seeds).isdisjoint(config.confirmatory_seeds))
        self.assertEqual(config.hidden_size, 48)
        self.assertEqual(config.transport_rank, 4)

    def test_summary_does_not_pool_failed_direction(self) -> None:
        rows = []
        for seed in range(32):
            rows.append(
                {
                    "seed": seed,
                    "primary": {
                        "accuracy_A": 0.99,
                        "accuracy_B": 0.99,
                        "accuracy_D": 0.99,
                        "sham_accuracy": 0.5,
                        "known_geometry_lift": 0.5,
                        "geometry_A_specific": 0.2,
                        "geometry_B_specific": 0.2,
                        "swap_tau_AB": 0.2,
                        "swap_tau_BA": 0.2,
                        "no_swap_drift": 0.0,
                        "undo_B_specific_harm": 0.2,
                        "undo_A_specific_harm": 0.0,
                        "undo_B_opposite_shift": 0.2,
                        "undo_A_opposite_shift": 0.2,
                        "undo_B_geometry_shift": 0.2,
                        "undo_A_geometry_shift": 0.2,
                        "undo_B_decode_loss": 0.0,
                        "undo_A_decode_loss": 0.0,
                        "undo_B_norm_drift": 0.0,
                        "undo_A_norm_drift": 0.0,
                        "undo_B_cov_drift": 0.0,
                        "undo_A_cov_drift": 0.0,
                        "undo_B_monotone": 1.0,
                        "undo_A_monotone": 1.0,
                        "rescue_B_specific_gain": 0.2,
                        "rescue_A_specific_gain": 0.2,
                        "rescue_B_compatible_shift": 0.2,
                        "rescue_A_compatible_shift": 0.2,
                        "rescue_B_geometry_shift": 0.2,
                        "rescue_A_geometry_shift": 0.2,
                        "rescue_B_decode_loss": 0.0,
                        "rescue_A_decode_loss": 0.0,
                        "rescue_B_norm_drift": 0.0,
                        "rescue_A_norm_drift": 0.0,
                        "rescue_B_cov_drift": 0.0,
                        "rescue_A_cov_drift": 0.0,
                        "rescue_B_monotone": 1.0,
                        "rescue_A_monotone": 1.0,
                    },
                    "transfer": {},
                }
            )
            cast(dict[str, Any], rows[-1]["primary"]).update(
                {
                    f"geometry_{constraint}_over_{comparator}": 0.2
                    for constraint in ("A", "B")
                    for comparator in ("sensory", "physical", "action", "sham")
                }
            )
            rows[-1]["integrity"] = {
                "action_histograms_match": True,
                "reachability_rdm_correlation": 0.0,
                "primary_nuisance": {"full_rank": True, "max_vif": 1.0},
                "transfer_nuisance": {"full_rank": True, "max_vif": 1.0},
                "split_overlap": 0,
            }
        rows[0]["transfer"] = copy.deepcopy(rows[0]["primary"])
        for row in rows[1:]:
            row["transfer"] = copy.deepcopy(row["primary"])

        summary = summarize_registered_rows(rows, bootstrap_samples=200, seed=3)

        self.assertFalse(
            summary["verdict"]["gates"]["G3_selective_impairment"]["pass"]
        )
        self.assertEqual(
            summary["verdict"]["decision"],
            "REJECT_GEOMETRY_TO_BEHAVIOR_CAUSAL_CHAIN",
        )

        missing = copy.deepcopy(rows)
        missing[0].pop("integrity")
        withheld = summarize_registered_rows(missing, bootstrap_samples=200, seed=3)
        self.assertFalse(
            withheld["verdict"]["gates"]["F0_integrity_identifiability"]["pass"]
        )
        with self.assertRaisesRegex(ValueError, "exactly unique seeds"):
            summarize_registered_rows(rows[:-1], bootstrap_samples=200, seed=3)


class ConstraintSwapModelTests(unittest.TestCase):
    def test_meta_gru_learns_all_balanced_rules_on_smoke_seed(self) -> None:
        torch.set_num_threads(1)
        config = replace(
            ExperimentConfig.registered(),
            hidden_size=48,
            training_steps=600,
            batch_size=96,
            sequence_length=16,
        )
        topology = GridTopology("torus", width=6, height=6)

        model, receipt = train_model(seed=1000, config=config, topology=topology)
        accuracy = evaluate_context_accuracy(
            model,
            topology,
            constraints=("A", "B", "D"),
            demonstrations=12,
            histories=4,
            seed=881,
        )

        self.assertTrue(np.isfinite(receipt["final_loss"]))
        self.assertGreater(accuracy["A"], 0.80)
        self.assertGreater(accuracy["B"], 0.80)
        self.assertGreater(accuracy["D"], 0.80)

    def test_context_collection_and_random_transport_are_shape_safe(self) -> None:
        torch.set_num_threads(1)
        config = replace(
            ExperimentConfig.registered(),
            hidden_size=24,
            training_steps=120,
            batch_size=48,
            sequence_length=12,
        )
        topology = GridTopology("torus", width=6, height=6)
        model, _ = train_model(seed=1001, config=config, topology=topology)
        units = select_probe_units(topology, count=48, seed=17)
        context = collect_context(
            model,
            topology,
            units,
            prefix=("A",),
            demonstrations=(12,),
            histories=4,
            seed=99,
        )
        self.assertEqual(context.hidden.shape, (48, 4, 24))
        self.assertEqual(context.logits.shape, (48, 4, 2))
        self.assertEqual(context.labels.shape, (48,))

        rng = np.random.default_rng(123)
        source = rng.normal(size=(60, 24))
        target = source + 0.2 * rng.normal(size=(60, 24))
        fitted = fit_low_rank_transport(source, target, rank=4, ridge=0.001)
        random_control = matched_random_transport(
            fitted,
            calibration_hidden=source,
            seed=77,
        )
        self.assertEqual(random_control.rank, fitted.rank)
        self.assertAlmostEqual(
            float(np.linalg.norm(random_control.matrix)),
            float(np.linalg.norm(fitted.matrix)),
            places=8,
        )


if __name__ == "__main__":
    unittest.main()
