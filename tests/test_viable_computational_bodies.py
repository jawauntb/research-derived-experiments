from __future__ import annotations

import unittest

from experiments.viable_computational_bodies.search import (
    ArchitectureSpec,
    evaluate_architecture,
    run_sweep,
    static_violations,
    summarize,
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


if __name__ == "__main__":
    unittest.main()

