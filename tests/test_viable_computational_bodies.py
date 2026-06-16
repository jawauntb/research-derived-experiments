from __future__ import annotations

import unittest

from experiments.concerned_syntax.vector_shapes import module_body_summary
from experiments.viable_computational_bodies.haskell_gate import (
    HaskellGateUnavailable,
    HaskellVerdict,
    load_body_verdicts,
    parse_named_verdicts,
)
from experiments.viable_computational_bodies.search import (
    ArchitectureSpec,
    evaluate_architecture,
    run_sweep,
    static_violations,
    summarize,
)
from experiments.viable_computational_bodies.modal_report import (
    summarize_modal_payload,
)


class ViableComputationalBodiesTest(unittest.TestCase):
    def test_static_rules_reject_planner_without_world_model(self) -> None:
        spec = ArchitectureSpec(frozenset({"flat_encoder", "reward_head", "intervention_planner"}))

        self.assertIn("intervention_planner_missing_world_model", static_violations(spec))

    def test_shortcut_without_guard_fails_anti_cheat(self) -> None:
        spec = ArchitectureSpec(frozenset({"flat_encoder", "reward_head", "shortcut_reward_head"}))
        evaluation = evaluate_architecture(
            spec,
            strategy="accuracy_only",
            seed=0,
            generation=0,
        )

        self.assertEqual(evaluation.formal_valid, 0)
        self.assertLess(evaluation.anti_cheat, 0.5)

    def test_target_body_passes_viability_gate(self) -> None:
        spec = ArchitectureSpec(
            frozenset(
                {
                    "flat_encoder",
                    "reward_head",
                    "tree_binder",
                    "syntax_memory",
                    "world_model",
                    "intervention_planner",
                    "role_specific_heads",
                    "formal_guard",
                }
            )
        )
        evaluation = evaluate_architecture(
            spec,
            strategy="viability_guided",
            seed=0,
            generation=0,
        )

        self.assertEqual(evaluation.viable, 1)

    def test_viability_guided_search_beats_accuracy_only_on_gates(self) -> None:
        rows = run_sweep(seeds=4, generations=12, population=14, base_seed=20260616)
        summary = summarize(rows)

        self.assertTrue(summary["viability_guided"]["gate_pass"])
        self.assertGreater(
            summary["viability_guided"]["final_viable_rate"],
            summary["accuracy_only"]["final_viable_rate"],
        )

    def test_modal_summary_preserves_strategy_gate(self) -> None:
        payload = {
            "results": [
                {
                    "strategy": "viability_guided",
                    "final": {
                        "viable": 1,
                        "concerned_syntax_score": 0.83,
                        "train_return": 0.49,
                        "formal_valid": 1,
                        "anti_cheat": 0.95,
                        "resource_cost": 11,
                        "architecture": "flat_encoder+formal_guard",
                    },
                },
                {
                    "strategy": "viability_guided",
                    "final": {
                        "viable": 1,
                        "concerned_syntax_score": 0.85,
                        "train_return": 0.51,
                        "formal_valid": 1,
                        "anti_cheat": 0.95,
                        "resource_cost": 11,
                        "architecture": "flat_encoder+formal_guard",
                    },
                },
            ]
        }

        summary = summarize_modal_payload(payload)

        self.assertTrue(summary["viability_guided"]["gate_pass"])
        self.assertAlmostEqual(
            summary["viability_guided"]["concerned_syntax_score"],
            0.84,
        )

    def test_haskell_gate_parses_named_json_verdicts(self) -> None:
        output = "\n".join(
            [
                (
                    '{"body":"modular_concerned_body","formal_valid":true,'
                    '"resource_cost":8,"violations":[]}'
                ),
                (
                    '{"body":"restless_vector_body","formal_valid":false,'
                    '"resource_cost":6,'
                    '"violations":["restless_without_calibration_guard"]}'
                ),
            ]
        )

        verdicts = parse_named_verdicts(output)

        self.assertTrue(verdicts["modular_concerned_body"].formal_valid)
        self.assertEqual(verdicts["modular_concerned_body"].resource_cost, 8)
        self.assertFalse(verdicts["restless_vector_body"].formal_valid)
        self.assertEqual(
            verdicts["restless_vector_body"].violations,
            ("restless_without_calibration_guard",),
        )

    def test_haskell_gate_runner_batches_body_names(self) -> None:
        seen: dict[str, tuple[str, ...]] = {}

        def runner(body_names: tuple[str, ...]) -> str:
            seen["body_names"] = body_names
            return (
                '{"body":"modular_concerned_body","formal_valid":true,'
                '"resource_cost":8,"violations":[]}\n'
                '{"body":"restless_vector_body","formal_valid":false,'
                '"resource_cost":6,'
                '"violations":["restless_without_calibration_guard"]}\n'
            )

        verdicts = load_body_verdicts(
            ["restless_vector_body", "modular_concerned_body"],
            runner=runner,
        )

        self.assertEqual(
            seen["body_names"],
            ("modular_concerned_body", "restless_vector_body"),
        )
        self.assertTrue(verdicts["modular_concerned_body"].formal_valid)

    def test_vector_body_summary_records_haskell_verdict_provenance(self) -> None:
        agent_stats = {
            agent: {
                "n": 10,
                "parse_accuracy_high_concern": 1.0,
                "action_accuracy": 1.0,
                "subtree_accuracy": 1.0,
                "surface_ambiguity_rate": 1.0,
                "high_concern_probe_rate": 1.0,
                "low_concern_probe_rate": 0.0,
                "mean_probe_cost": 0.04,
                "mean_regret": 0.0,
                "gate_pass": True,
            }
            for agent in (
                "surface_shortcut",
                "passive_vector",
                "restless_vector_probe",
                "concerned_vector_probe",
            )
        }
        body_summary = module_body_summary(
            agent_stats,
            formal_verdicts={
                "modular_concerned_body": HaskellVerdict(
                    formal_valid=True,
                    resource_cost=8,
                    violations=(),
                ),
                "restless_vector_body": HaskellVerdict(
                    formal_valid=False,
                    resource_cost=6,
                    violations=("restless_without_calibration_guard",),
                ),
            },
        )

        self.assertEqual(
            body_summary["modular_concerned_body"]["formal_source"],
            "haskell",
        )
        self.assertEqual(body_summary["modular_concerned_body"]["resource_cost"], 8)
        self.assertTrue(
            body_summary["modular_concerned_body"]["executable_module_gate"],
        )
        self.assertEqual(
            body_summary["restless_vector_body"]["formal_violations"],
            ["restless_without_calibration_guard"],
        )
        self.assertFalse(
            body_summary["restless_vector_body"]["executable_module_gate"],
        )
        self.assertEqual(
            body_summary["surface_reward_body"]["formal_source"],
            "python_static",
        )

    def test_live_haskell_gate_reports_known_bodies_when_available(self) -> None:
        try:
            verdicts = load_body_verdicts(
                ("modular_concerned_body", "restless_vector_body")
            )
        except HaskellGateUnavailable as exc:
            self.skipTest(str(exc))

        self.assertTrue(verdicts["modular_concerned_body"].formal_valid)
        self.assertEqual(verdicts["modular_concerned_body"].resource_cost, 8)
        self.assertFalse(verdicts["restless_vector_body"].formal_valid)
        self.assertEqual(
            verdicts["restless_vector_body"].violations,
            ("restless_without_calibration_guard",),
        )


if __name__ == "__main__":
    unittest.main()
