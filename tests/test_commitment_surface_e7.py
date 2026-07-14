from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock

from experiments.commitment_surface.e7_selective_subspace import (
    ARMS,
    BASE_SEED,
    CheckpointRecord,
    TASK_MODULI,
    WIDTHS,
    E7Config,
    StreamResult,
    _apply_budget_audit,
    analyze_gates,
    derive_e7_seed,
    exact_grid_seeds,
    make_model,
    one_hot_pairs_padded,
    run_experiment,
    run_stream,
    validate_pilot_receipt,
    weighted_group_subspace,
    write_summary_markdown,
)


class E7SelectiveSubspaceTest(unittest.TestCase):
    def test_frozen_grid_and_namespaced_seed_contract(self) -> None:
        self.assertEqual(ARMS, ("P_none", "P_ewc", "P_sub", "P_wrong"))
        self.assertEqual(TASK_MODULI, (17, 19, 23, 29))
        self.assertEqual(WIDTHS, (96, 128))
        self.assertEqual(BASE_SEED, 202607131200)

        seeds = exact_grid_seeds()
        self.assertEqual(len(seeds), 128)
        self.assertEqual(len(set(seeds.values())), 128)

        source = "e7|202607131200|cell|17|P_sub|2|96"
        expected = int(hashlib.sha256(source.encode()).hexdigest(), 16) % (2**31)
        self.assertEqual(
            derive_e7_seed(
                namespace="cell",
                task=17,
                arm_scope="P_sub",
                seed_index=2,
                width=96,
            ),
            expected,
        )
        init_seeds = {
            derive_e7_seed(
                namespace="initialization",
                task="stream",
                arm_scope="matched",
                seed_index=1,
                width=96,
            )
            for _arm in ARMS
        }
        self.assertEqual(len(init_seeds), 1)

    def test_padded_encoder_keeps_one_model_shape_across_moduli(self) -> None:
        import torch

        encoded = one_hot_pairs_padded([(16, 16)], modulus=17, max_modulus=29)
        self.assertEqual(tuple(encoded.shape), (1, 58))
        self.assertEqual(float(encoded.sum().item()), 2.0)
        self.assertEqual(float(encoded[0, 16].item()), 1.0)
        self.assertEqual(float(encoded[0, 29 + 16].item()), 1.0)
        with self.assertRaisesRegex(ValueError, "outside modulus"):
            one_hot_pairs_padded([(17, 0)], modulus=17, max_modulus=29)
        self.assertTrue(torch.isfinite(encoded).all())

    def test_weighted_boundary_axis_hits_exact_protected_mass(self) -> None:
        import torch

        cfg = E7Config(
            task_moduli=(5, 7),
            widths=(8,),
            seeds=1,
            epochs=1,
            max_modulus=7,
        )
        model = make_model(cfg, width=8)
        fitted = weighted_group_subspace(
            model,
            modulus=5,
            max_modulus=7,
            grouping="sum",
            target_mass=0.5,
            device=torch.device("cpu"),
        )
        self.assertGreater(fitted.rank, 0)
        self.assertGreaterEqual(fitted.full_rank_mass, 0.5)
        self.assertAlmostEqual(fitted.protected_mass, 0.5, places=6)
        self.assertEqual(tuple(fitted.basis.shape), (8, fitted.rank))
        self.assertEqual(tuple(fitted.axis_weights.shape), (fitted.rank,))

    def test_tiny_stream_is_strictly_sequential_and_complete(self) -> None:
        cfg = E7Config(
            task_moduli=(5, 7),
            widths=(8,),
            seeds=1,
            epochs=1,
            max_modulus=7,
            learning_rate=1e-3,
        )
        result = run_stream(cfg, arm="P_sub", width=8, seed_index=0)

        self.assertEqual([row.task_modulus for row in result.checkpoints], [5, 7])
        self.assertEqual(
            [(row.boundary_index, row.evaluated_modulus) for row in result.metrics],
            [(1, 5), (2, 5), (2, 7)],
        )
        self.assertEqual(result.optimizer_steps, 2)
        self.assertEqual(result.protection_backward_steps, 1)
        self.assertEqual(result.data_exposure, {"5": 1, "7": 1})
        self.assertTrue(result.seed_integrity)
        self.assertTrue(all(math.isfinite(row.ood_accuracy) for row in result.metrics))

    def test_matched_arm_scheduler_preserves_initialization_and_budget(self) -> None:
        cfg = E7Config(
            task_moduli=(5,),
            widths=(8,),
            seeds=1,
            epochs=4,
            max_modulus=5,
            aug_orbit_size=0,
        )
        streams, integrity = run_experiment(cfg)

        self.assertEqual(len(streams), 4)
        self.assertTrue(integrity["seed"])
        self.assertEqual(len({stream.initialization_seed for stream in streams}), 1)
        self.assertEqual(
            len({stream.metrics[0].ood_accuracy for stream in streams}), 1
        )

    def test_budget_audit_uses_per_arm_work_not_shared_barrier_makespan(self) -> None:
        cfg = E7Config(
            task_moduli=(5,),
            widths=(8,),
            seeds=1,
            epochs=2,
            max_modulus=5,
            aug_orbit_size=0,
        )
        streams, _integrity = run_experiment(cfg)
        for stream in streams:
            stream.checkpoints[0].wall_clock_seconds = 10.0
            stream.checkpoints[0].budget_wall_clock_seconds = 1.0
        streams[0].checkpoints[0].budget_wall_clock_seconds = 1.1

        audit = _apply_budget_audit(streams)

        self.assertFalse(audit["pass"])
        self.assertGreater(audit["max_relative_wall_clock_range"], 0.02)
        self.assertTrue(all(not stream.budget_integrity for stream in streams))

    def test_arm_failure_aborts_barrier_instead_of_deadlocking(self) -> None:
        cfg = E7Config(
            task_moduli=(5,),
            widths=(8,),
            seeds=1,
            epochs=1,
            max_modulus=5,
        )

        def fail_one_arm(*_args, arm: str, task_barrier, **_kwargs):
            if arm == "P_none":
                raise RuntimeError("injected arm failure")
            with self.assertRaises(threading.BrokenBarrierError):
                task_barrier.wait(timeout=2.0)

        with mock.patch(
            "experiments.commitment_surface.e7_selective_subspace.run_stream",
            side_effect=fail_one_arm,
        ):
            with self.assertRaisesRegex(RuntimeError, "injected arm failure"):
                run_experiment(cfg)

    def test_gate_analysis_is_strict_at_both_widths(self) -> None:
        def summary(width: int, arm: str, patch: float, retained: float, final: float):
            return {
                "width": width,
                "arm": arm,
                "valid_streams": 4,
                "earlier_patch_ce_per_mass": patch,
                "retained_ood_accuracy": retained,
                "final_task_ood_accuracy": final,
            }

        rows = []
        for width in WIDTHS:
            rows.extend(
                [
                    summary(width, "P_none", 0.10, 0.20, 0.50),
                    summary(width, "P_ewc", 0.14, 0.40, 0.55),
                    summary(width, "P_sub", 0.20, 0.431, 0.531),
                    summary(width, "P_wrong", 0.149, 0.25, 0.52),
                ]
            )
        passed = analyze_gates(rows)
        self.assertEqual(passed["strict_verdict"], "PASS")
        self.assertTrue(all(passed["gates"].values()))

        rows[-2]["retained_ood_accuracy"] = 0.429999
        failed = analyze_gates(rows)
        self.assertEqual(failed["strict_verdict"], "FAIL")
        self.assertFalse(failed["gates"]["G3_frontier_dominance_both_widths"])

        rows[0]["valid_streams"] = 3
        invalid = analyze_gates(rows)
        self.assertEqual(invalid["strict_verdict"], "INVALID")
        self.assertEqual(invalid["margins"], {})

    def test_confirmatory_requires_the_exact_frozen_pilot_receipt(self) -> None:
        cfg = E7Config(task_moduli=TASK_MODULI[:2], widths=(WIDTHS[0],), seeds=1)
        payload = {
            "run_kind": "pilot",
            "status": "complete",
            "config": json.loads(json.dumps(asdict(cfg))),
            "protection_lambda": 1.0,
            "stream_count": 4,
            "checkpoint_count": 8,
            "stability_rows": 4,
            "valid_streams": 4,
            "integrity": {
                "seed": True,
                "sequential": True,
                "protected_mass": True,
                "budget": True,
            },
        }
        streams = []
        for arm_index, arm in enumerate(ARMS):
            checkpoints = []
            for boundary_index, modulus in enumerate(TASK_MODULI[:2], start=1):
                checkpoints.append(
                    CheckpointRecord(
                        boundary_index=boundary_index,
                        task_modulus=modulus,
                        cell_seed=arm_index * 2 + boundary_index,
                        split_seed=100 + boundary_index,
                        augmentation_seed=200 + boundary_index,
                        train_pairs=1,
                        ood_pairs=1,
                        labeled_examples_seen=1,
                        optimizer_steps=1000,
                        active_protection_backward_steps=0,
                        wall_clock_seconds=1.0,
                        median_step_seconds=0.001,
                        budget_wall_clock_seconds=1.0,
                        compatibility_rank=1,
                        compatibility_full_rank_mass=0.5,
                        compatibility_protected_mass=0.5,
                        wrong_rank=1,
                        wrong_full_rank_mass=0.5,
                        wrong_protected_mass=0.5,
                    )
                )
            streams.append(
                StreamResult(
                    arm=arm,
                    width=96,
                    seed_index=0,
                    initialization_seed=42,
                    checkpoints=checkpoints,
                    metrics=[],
                    optimizer_steps=2000,
                    protection_backward_steps=0,
                    data_exposure={"17": 1000, "19": 1000},
                    seed_integrity=True,
                    sequential_integrity=True,
                    mass_integrity=True,
                    budget_integrity=True,
                    budget_relative_wall_clock_range=0.0,
                )
            )
        payload["streams"] = [asdict(stream) for stream in streams]
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "pilot.json"
            receipt.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(validate_pilot_receipt(receipt), payload)

            payload["config"]["aug_orbit_size"] = 0
            receipt.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "frozen E7 pilot grid"):
                validate_pilot_receipt(receipt)

    def test_committed_invalid_result_round_trips_without_gate_margins(self) -> None:
        result_path = Path(
            "experiments/commitment_surface/results/"
            "e7_selective_subspace_2026_07_13.json"
        )
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "invalid")
        self.assertEqual(payload["gate_analysis"]["strict_verdict"], "INVALID")
        self.assertEqual(len(payload["integrity"]["budget_detail"]["failures"]), 6)

        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "result.md"
            write_summary_markdown(payload, report)
            rendered = report.read_text(encoding="utf-8")
        self.assertIn("INVALID — NO SCIENTIFIC VERDICT", rendered)
        self.assertIn("6 of 32 matched groups", rendered)


if __name__ == "__main__":
    unittest.main()
