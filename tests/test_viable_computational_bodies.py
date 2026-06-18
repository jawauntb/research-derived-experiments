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
from experiments.viable_computational_bodies.program_body_search import (
    ProgramBodySpec,
    empirical_agent_for_body,
    evaluate_program_body,
    program_body_violations,
    run_program_body_search,
    summarize_program_bodies,
)
from experiments.viable_computational_bodies.rich_program_body_search import (
    TARGET_RICH_PROGRAM_BODY,
    RichBodyFormalOracle,
    RichBodySpec,
    empirical_agent_for_rich_body,
    evaluate_rich_body,
    rich_body_violations,
    run_rich_body_search,
    summarize_rich_bodies,
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

    def test_program_body_mapping_separates_concern_and_target(self) -> None:
        concern_only = ProgramBodySpec(
            frozenset(
                {
                    "vector_surface_encoder",
                    "reward_head",
                    "world_model",
                    "concern_policy",
                    "calibration_guard",
                }
            )
        )
        target_only = ProgramBodySpec(
            frozenset(
                {
                    "vector_surface_encoder",
                    "reward_head",
                    "world_model",
                    "intervention_planner",
                    "causal_binding_head",
                }
            )
        )
        full = ProgramBodySpec(
            frozenset(
                {
                    "vector_surface_encoder",
                    "reward_head",
                    "world_model",
                    "intervention_planner",
                    "concern_policy",
                    "calibration_guard",
                    "causal_binding_head",
                    "formal_guard",
                }
            )
        )

        self.assertEqual(empirical_agent_for_body(concern_only), "concern_without_target")
        self.assertEqual(empirical_agent_for_body(target_only), "target_without_concern")
        self.assertEqual(empirical_agent_for_body(full), "concerned_program_inventor")

    def test_program_body_rejects_concern_without_calibration(self) -> None:
        spec = ProgramBodySpec(
            frozenset(
                {
                    "vector_surface_encoder",
                    "reward_head",
                    "world_model",
                    "concern_policy",
                }
            )
        )

        self.assertIn(
            "concern_without_calibration_guard",
            program_body_violations(spec),
        )

    def test_program_body_search_uses_empirical_2a_contract(self) -> None:
        summary = {
            "surface_program_shortcut": {
                "parse_accuracy_high_concern": 0.50,
                "action_accuracy": 0.88,
                "subtree_accuracy": 0.50,
                "high_concern_probe_rate": 0.0,
                "low_concern_probe_rate": 0.0,
                "target_accuracy_high_concern": 0.0,
                "useful_program_rate_high_concern": 0.0,
                "object_extraction_rate": 1.0,
                "gate_pass": False,
            },
            "random_program_probe": {
                "parse_accuracy_high_concern": 0.52,
                "action_accuracy": 0.87,
                "subtree_accuracy": 0.53,
                "high_concern_probe_rate": 1.0,
                "low_concern_probe_rate": 1.0,
                "target_accuracy_high_concern": 0.06,
                "useful_program_rate_high_concern": 0.06,
                "object_extraction_rate": 1.0,
                "gate_pass": False,
            },
            "concern_without_target": {
                "parse_accuracy_high_concern": 0.53,
                "action_accuracy": 0.88,
                "subtree_accuracy": 0.52,
                "high_concern_probe_rate": 1.0,
                "low_concern_probe_rate": 0.16,
                "target_accuracy_high_concern": 0.09,
                "useful_program_rate_high_concern": 0.09,
                "object_extraction_rate": 1.0,
                "gate_pass": False,
            },
            "target_without_concern": {
                "parse_accuracy_high_concern": 1.0,
                "action_accuracy": 1.0,
                "subtree_accuracy": 1.0,
                "high_concern_probe_rate": 1.0,
                "low_concern_probe_rate": 1.0,
                "target_accuracy_high_concern": 1.0,
                "useful_program_rate_high_concern": 1.0,
                "object_extraction_rate": 1.0,
                "gate_pass": False,
            },
            "concerned_program_inventor": {
                "parse_accuracy_high_concern": 1.0,
                "action_accuracy": 1.0,
                "subtree_accuracy": 0.80,
                "high_concern_probe_rate": 1.0,
                "low_concern_probe_rate": 0.16,
                "target_accuracy_high_concern": 1.0,
                "useful_program_rate_high_concern": 1.0,
                "object_extraction_rate": 1.0,
                "gate_pass": True,
            },
        }
        full = ProgramBodySpec(
            frozenset(
                {
                    "vector_surface_encoder",
                    "reward_head",
                    "world_model",
                    "intervention_planner",
                    "concern_policy",
                    "calibration_guard",
                    "causal_binding_head",
                    "formal_guard",
                }
            )
        )
        evaluation = evaluate_program_body(
            full,
            strategy="viability_guided",
            seed=0,
            generation=0,
            agent_summary=summary,
        )
        rows = run_program_body_search(
            strategy="viability_guided",
            seed=20260616,
            generations=10,
            population=12,
            agent_summary=summary,
        )
        search_summary = summarize_program_bodies(rows)

        self.assertEqual(evaluation.body_gate, 1)
        self.assertTrue(search_summary["viability_guided"]["gate_pass"])
        self.assertEqual(
            search_summary["viability_guided"]["best_empirical_agent"],
            "concerned_program_inventor",
        )

    def test_rich_body_mapping_requires_family_and_composer(self) -> None:
        target_only = RichBodySpec(
            frozenset(
                {
                    "vector_surface_encoder",
                    "reward_head",
                    "world_model",
                    "intervention_planner",
                    "causal_binding_head",
                }
            )
        )
        family_without_target = RichBodySpec(
            frozenset(
                {
                    "vector_surface_encoder",
                    "reward_head",
                    "world_model",
                    "program_family_head",
                }
            )
        )
        no_concern = RichBodySpec(
            frozenset(
                {
                    "vector_surface_encoder",
                    "reward_head",
                    "world_model",
                    "intervention_planner",
                    "causal_binding_head",
                    "program_family_head",
                    "rich_program_composer",
                }
            )
        )
        full = RichBodySpec(TARGET_RICH_PROGRAM_BODY)

        self.assertEqual(
            empirical_agent_for_rich_body(target_only),
            "target_without_family",
        )
        self.assertEqual(
            empirical_agent_for_rich_body(family_without_target),
            "family_without_target",
        )
        self.assertEqual(
            empirical_agent_for_rich_body(no_concern),
            "rich_without_concern",
        )
        self.assertEqual(
            empirical_agent_for_rich_body(full),
            "concerned_program_composer",
        )

    def test_rich_body_rejects_composer_without_family_head(self) -> None:
        spec = RichBodySpec(
            frozenset(
                {
                    "vector_surface_encoder",
                    "reward_head",
                    "world_model",
                    "intervention_planner",
                    "rich_program_composer",
                    "formal_guard",
                }
            )
        )

        self.assertIn(
            "rich_program_composer_missing_program_family_head",
            rich_body_violations(spec),
        )

    def test_rich_body_formal_oracle_accepts_v2_motifs(self) -> None:
        oracle = RichBodyFormalOracle(mode="python_static")
        verdict = oracle.verdict(RichBodySpec(TARGET_RICH_PROGRAM_BODY))

        self.assertTrue(verdict.formal_valid)
        self.assertLessEqual(verdict.resource_cost, 18)
        self.assertEqual(verdict.violations, ())

    def test_rich_program_body_search_uses_empirical_2a_v2_contract(self) -> None:
        summary = {
            "surface_rich_shortcut": {
                "parse_accuracy_high_concern": 0.50,
                "action_accuracy": 0.88,
                "subtree_accuracy": 0.50,
                "high_concern_program_rate": 0.0,
                "low_concern_program_rate": 0.0,
                "family_accuracy_high_concern": 0.0,
                "target_accuracy_high_concern": 0.0,
                "useful_program_rate_high_concern": 0.0,
                "rich_program_rate_high_concern": 0.0,
                "object_extraction_rate": 1.0,
                "gate_pass": False,
            },
            "random_rich_program": {
                "parse_accuracy_high_concern": 0.52,
                "action_accuracy": 0.87,
                "subtree_accuracy": 0.53,
                "high_concern_program_rate": 1.0,
                "low_concern_program_rate": 1.0,
                "family_accuracy_high_concern": 0.24,
                "target_accuracy_high_concern": 0.06,
                "useful_program_rate_high_concern": 0.02,
                "rich_program_rate_high_concern": 0.75,
                "object_extraction_rate": 1.0,
                "gate_pass": False,
            },
            "family_without_target": {
                "parse_accuracy_high_concern": 0.54,
                "action_accuracy": 0.88,
                "subtree_accuracy": 0.53,
                "high_concern_program_rate": 1.0,
                "low_concern_program_rate": 0.16,
                "family_accuracy_high_concern": 1.0,
                "target_accuracy_high_concern": 0.08,
                "useful_program_rate_high_concern": 0.08,
                "rich_program_rate_high_concern": 0.82,
                "object_extraction_rate": 1.0,
                "gate_pass": False,
            },
            "target_without_family": {
                "parse_accuracy_high_concern": 0.72,
                "action_accuracy": 0.91,
                "subtree_accuracy": 0.72,
                "high_concern_program_rate": 1.0,
                "low_concern_program_rate": 1.0,
                "family_accuracy_high_concern": 0.25,
                "target_accuracy_high_concern": 1.0,
                "useful_program_rate_high_concern": 0.25,
                "rich_program_rate_high_concern": 0.0,
                "object_extraction_rate": 1.0,
                "gate_pass": False,
            },
            "rich_without_concern": {
                "parse_accuracy_high_concern": 1.0,
                "action_accuracy": 1.0,
                "subtree_accuracy": 1.0,
                "high_concern_program_rate": 1.0,
                "low_concern_program_rate": 1.0,
                "family_accuracy_high_concern": 1.0,
                "target_accuracy_high_concern": 1.0,
                "useful_program_rate_high_concern": 1.0,
                "rich_program_rate_high_concern": 0.80,
                "object_extraction_rate": 1.0,
                "gate_pass": False,
            },
            "concerned_program_composer": {
                "parse_accuracy_high_concern": 1.0,
                "action_accuracy": 1.0,
                "subtree_accuracy": 1.0,
                "high_concern_program_rate": 1.0,
                "low_concern_program_rate": 0.16,
                "family_accuracy_high_concern": 1.0,
                "target_accuracy_high_concern": 1.0,
                "useful_program_rate_high_concern": 1.0,
                "rich_program_rate_high_concern": 0.80,
                "object_extraction_rate": 1.0,
                "gate_pass": True,
            },
        }
        full = RichBodySpec(TARGET_RICH_PROGRAM_BODY)
        oracle = RichBodyFormalOracle(mode="python_static")
        evaluation = evaluate_rich_body(
            full,
            strategy="viability_guided",
            seed=0,
            generation=0,
            agent_summary=summary,
            formal_verdict=oracle.verdict(full),
        )
        rows = run_rich_body_search(
            strategy="viability_guided",
            seed=20260618,
            generations=8,
            population=10,
            agent_summary=summary,
            formal_oracle=oracle,
        )
        search_summary = summarize_rich_bodies(rows)

        self.assertEqual(evaluation.body_gate, 1)
        self.assertTrue(search_summary["viability_guided"]["gate_pass"])
        self.assertEqual(
            search_summary["viability_guided"]["best_empirical_agent"],
            "concerned_program_composer",
        )


if __name__ == "__main__":
    unittest.main()
