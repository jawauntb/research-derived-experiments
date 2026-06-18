from __future__ import annotations

import random
import unittest

from experiments.concerned_syntax.benchmark import (
    Intervention,
    concern_gap,
    choose_intervention,
    information_gain,
    make_trial,
    outcome_for_parse,
    run_trials,
    summarize,
)
from experiments.concerned_syntax.learned_agents import (
    run_experiment,
    summarize_seed_payloads,
)
from experiments.concerned_syntax.learned_pixel_extractor import (
    run_experiment as run_learned_pixel_extractor_experiment,
    summarize_seed_payloads as summarize_learned_pixel_extractor_payloads,
)
from experiments.concerned_syntax.intervention_invention import (
    run_parse_transfer_experiment,
    run_experiment as run_program_experiment,
    run_role_transfer_experiment,
    run_transfer_suite,
    summarize_seed_payloads as summarize_program_payloads,
    summarize_transfer_payloads,
)
from experiments.concerned_syntax.modal_report import summarize_modal_payload
from experiments.concerned_syntax.pixel_shapes import (
    extract_components,
    render_pixel_surface,
    run_experiment as run_pixel_experiment,
    summarize_seed_payloads as summarize_pixel_payloads,
)
from experiments.concerned_syntax.searched_program_policy import (
    run_experiment as run_searched_program_experiment,
    summarize_search_payloads,
)
from experiments.concerned_syntax.rich_program_language import (
    run_experiment as run_rich_program_experiment,
    summarize_seed_payloads as summarize_rich_program_payloads,
)
from experiments.concerned_syntax.vector_shapes import (
    run_experiment as run_vector_experiment,
    summarize_seed_payloads as summarize_vector_payloads,
    vector_surface,
)


class ConcernedSyntaxTest(unittest.TestCase):
    def test_same_surface_can_have_different_concern_outcomes(self) -> None:
        rng = random.Random(1)
        trial = make_trial(0, rng)
        # Force until the sampled trial is high-concern enough for the test.
        for idx in range(1, 50):
            if concern_gap(trial) >= 0.10:
                break
            trial = make_trial(idx, rng)

        true_outcome = outcome_for_parse(trial, trial.true_parse)
        alt_outcome = outcome_for_parse(trial, trial.alternate_parse)

        self.assertNotEqual(true_outcome, alt_outcome)
        self.assertGreaterEqual(concern_gap(trial), 0.10)

    def test_pair_probe_reveals_parse_when_constituency_differs(self) -> None:
        trial = make_trial(0, random.Random(4))
        probe = Intervention("pair_probe", "pair_probe", 0.04, pair=trial.causal_pair)

        self.assertEqual(information_gain(trial, probe), 1.0)

    def test_concerned_selector_avoids_low_concern_restless_probe(self) -> None:
        rng = random.Random(7)
        low_trial = make_trial(0, rng)
        for idx in range(1, 100):
            if concern_gap(low_trial) < 0.10:
                break
            low_trial = make_trial(idx, rng)

        intervention = choose_intervention(low_trial, "concerned_syntax", random.Random(8))

        self.assertEqual(intervention.name, "null")

    def test_benchmark_summary_separates_concerned_syntax(self) -> None:
        rows = run_trials(trials=200, seed=20260616)
        summary = summarize(rows)

        self.assertTrue(summary["concerned_syntax"]["gate_pass"])
        self.assertFalse(summary["flat_valence"]["gate_pass"])
        self.assertLessEqual(
            summary["concerned_syntax"]["low_concern_probe_rate"],
            0.25,
        )

    def test_modal_summary_averages_seed_gates(self) -> None:
        payload = {
            "results": [
                {
                    "summary": {
                        "concerned_syntax": {
                            "parse_accuracy_high_concern": 1.0,
                            "action_accuracy": 1.0,
                            "subtree_accuracy": 0.8,
                            "high_concern_probe_rate": 1.0,
                            "low_concern_probe_rate": 0.0,
                            "mean_regret": 0.002,
                            "gate_pass": True,
                        }
                    }
                },
                {
                    "summary": {
                        "concerned_syntax": {
                            "parse_accuracy_high_concern": 1.0,
                            "action_accuracy": 1.0,
                            "subtree_accuracy": 0.82,
                            "high_concern_probe_rate": 1.0,
                            "low_concern_probe_rate": 0.0,
                            "mean_regret": 0.004,
                            "gate_pass": True,
                        }
                    }
                },
            ]
        }

        summary = summarize_modal_payload(payload)

        self.assertEqual(
            summary["concerned_syntax"]["gate_pass_rate"],
            1.0,
        )
        self.assertAlmostEqual(
            summary["concerned_syntax"]["mean_regret"],
            0.003,
        )

    def test_learned_agent_gate_separates_body_failures(self) -> None:
        payload = run_experiment(
            train_trials=600,
            test_trials=240,
            seed=20260616,
            epochs=40,
        )
        agents = payload["agent_summary"]
        bodies = payload["body_summary"]

        self.assertTrue(agents["learned_concerned_syntax"]["gate_pass"])
        self.assertFalse(agents["restless_tree"]["gate_pass"])
        self.assertEqual(agents["restless_tree"]["low_concern_probe_rate"], 1.0)
        self.assertFalse(agents["planner_no_tree"]["gate_pass"])
        self.assertLess(
            agents["planner_no_tree"]["parse_accuracy_high_concern"],
            agents["learned_concerned_syntax"]["parse_accuracy_high_concern"],
        )
        self.assertTrue(bodies["guarded_syntax_body"]["executable_body_gate"])
        self.assertFalse(bodies["restless_tree_body"]["executable_body_gate"])

    def test_learned_modal_summary_averages_gate_rates(self) -> None:
        payloads = [
            {
                "agent_summary": {
                    "learned_concerned_syntax": {
                        "parse_accuracy_high_concern": 1.0,
                        "gate_pass": True,
                    }
                }
            },
            {
                "agent_summary": {
                    "learned_concerned_syntax": {
                        "parse_accuracy_high_concern": 0.8,
                        "gate_pass": False,
                    }
                }
            },
        ]

        summary = summarize_seed_payloads(payloads, "agent_summary")

        self.assertAlmostEqual(
            summary["learned_concerned_syntax"]["parse_accuracy_high_concern"],
            0.9,
        )
        self.assertAlmostEqual(
            summary["learned_concerned_syntax"]["gate_pass"],
            0.5,
        )

    def test_vector_surface_does_not_encode_hidden_parse(self) -> None:
        rng = random.Random(99)
        trial = make_trial(0, rng)
        swapped = type(trial)(
            trial_id=trial.trial_id,
            kind=trial.kind,
            roles=trial.roles,
            true_parse=trial.alternate_parse,
            alternate_parse=trial.true_parse,
            causal_pair=trial.causal_pair,
            concern_weight=trial.concern_weight,
        )

        self.assertEqual(vector_surface(trial), vector_surface(swapped))

    def test_vector_agent_gate_separates_surface_and_restless_failures(self) -> None:
        payload = run_vector_experiment(
            train_trials=650,
            test_trials=260,
            seed=20260616,
            epochs=45,
        )
        agents = payload["agent_summary"]
        bodies = payload["body_summary"]

        self.assertTrue(agents["concerned_vector_probe"]["gate_pass"])
        self.assertFalse(agents["surface_shortcut"]["gate_pass"])
        self.assertFalse(agents["passive_vector"]["gate_pass"])
        self.assertFalse(agents["restless_vector_probe"]["gate_pass"])
        self.assertEqual(
            agents["restless_vector_probe"]["low_concern_probe_rate"],
            1.0,
        )
        self.assertGreater(
            agents["concerned_vector_probe"]["parse_accuracy_high_concern"],
            agents["passive_vector"]["parse_accuracy_high_concern"],
        )
        self.assertTrue(bodies["modular_concerned_body"]["executable_module_gate"])
        self.assertFalse(bodies["restless_vector_body"]["executable_module_gate"])

    def test_vector_modal_summary_averages_gate_rates(self) -> None:
        payloads = [
            {
                "agent_summary": {
                    "concerned_vector_probe": {
                        "parse_accuracy_high_concern": 1.0,
                        "gate_pass": True,
                    }
                }
            },
            {
                "agent_summary": {
                    "concerned_vector_probe": {
                        "parse_accuracy_high_concern": 0.8,
                        "gate_pass": False,
                    }
                }
            },
        ]

        summary = summarize_vector_payloads(payloads, "agent_summary")

        self.assertAlmostEqual(
            summary["concerned_vector_probe"]["parse_accuracy_high_concern"],
            0.9,
        )
        self.assertAlmostEqual(summary["concerned_vector_probe"]["gate_pass"], 0.5)

    def test_pixel_surface_does_not_encode_hidden_parse(self) -> None:
        rng = random.Random(101)
        trial = make_trial(0, rng)
        swapped = type(trial)(
            trial_id=trial.trial_id,
            kind=trial.kind,
            roles=trial.roles,
            true_parse=trial.alternate_parse,
            alternate_parse=trial.true_parse,
            causal_pair=trial.causal_pair,
            concern_weight=trial.concern_weight,
        )

        self.assertEqual(render_pixel_surface(trial), render_pixel_surface(swapped))

    def test_pixel_component_extractor_recovers_six_visible_parts(self) -> None:
        trial = make_trial(0, random.Random(20260616))

        components = extract_components(render_pixel_surface(trial))

        self.assertEqual(len(components), 6)
        self.assertTrue(all(component.area > 20 for component in components))

    def test_pixel_agent_gate_separates_surface_passive_and_restless_failures(self) -> None:
        payload = run_pixel_experiment(
            train_trials=650,
            test_trials=260,
            seed=20260616,
            epochs=45,
        )
        agents = payload["agent_summary"]

        self.assertTrue(agents["concerned_pixel_probe"]["gate_pass"])
        self.assertFalse(agents["surface_pixel_shortcut"]["gate_pass"])
        self.assertFalse(agents["passive_pixel"]["gate_pass"])
        self.assertFalse(agents["restless_pixel_probe"]["gate_pass"])
        self.assertEqual(
            agents["restless_pixel_probe"]["low_concern_probe_rate"],
            1.0,
        )
        self.assertEqual(
            agents["concerned_pixel_probe"]["object_extraction_rate"],
            1.0,
        )
        self.assertGreater(
            agents["concerned_pixel_probe"]["parse_accuracy_high_concern"],
            agents["passive_pixel"]["parse_accuracy_high_concern"],
        )

    def test_pixel_modal_summary_averages_gate_rates(self) -> None:
        payloads = [
            {
                "agent_summary": {
                    "concerned_pixel_probe": {
                        "parse_accuracy_high_concern": 1.0,
                        "gate_pass": True,
                    }
                }
            },
            {
                "agent_summary": {
                    "concerned_pixel_probe": {
                        "parse_accuracy_high_concern": 0.8,
                        "gate_pass": False,
                    }
                }
            },
        ]

        summary = summarize_pixel_payloads(payloads, "agent_summary")

        self.assertAlmostEqual(
            summary["concerned_pixel_probe"]["parse_accuracy_high_concern"],
            0.9,
        )
        self.assertAlmostEqual(summary["concerned_pixel_probe"]["gate_pass"], 0.5)

    def test_learned_pixel_extractor_preserves_pixel_gate(self) -> None:
        payload = run_learned_pixel_extractor_experiment(
            train_trials=240,
            test_trials=100,
            seed=20260617,
            epochs=24,
            extractor_samples_per_image=72,
        )
        agents = payload["agent_summary"]
        extractor = payload["extractor_summary"]["learned_foreground_slots"]

        self.assertGreaterEqual(extractor["slot_recovery_rate"], 0.95)
        self.assertGreaterEqual(extractor["scene_recovery_rate"], 0.90)
        self.assertTrue(agents["concerned_pixel_probe"]["gate_pass"])
        self.assertFalse(agents["surface_pixel_shortcut"]["gate_pass"])
        self.assertFalse(agents["passive_pixel"]["gate_pass"])
        self.assertFalse(agents["restless_pixel_probe"]["gate_pass"])
        self.assertEqual(
            agents["restless_pixel_probe"]["low_concern_probe_rate"],
            1.0,
        )

    def test_learned_pixel_extractor_modal_summary_averages_gate_rates(self) -> None:
        payloads = [
            {
                "agent_summary": {
                    "concerned_pixel_probe": {
                        "parse_accuracy_high_concern": 1.0,
                        "gate_pass": True,
                    }
                },
                "extractor_summary": {
                    "learned_foreground_slots": {
                        "slot_recovery_rate": 1.0,
                    }
                },
            },
            {
                "agent_summary": {
                    "concerned_pixel_probe": {
                        "parse_accuracy_high_concern": 0.8,
                        "gate_pass": False,
                    }
                },
                "extractor_summary": {
                    "learned_foreground_slots": {
                        "slot_recovery_rate": 0.9,
                    }
                },
            },
        ]

        agent_summary = summarize_learned_pixel_extractor_payloads(
            payloads,
            "agent_summary",
        )
        extractor_summary = summarize_learned_pixel_extractor_payloads(
            payloads,
            "extractor_summary",
        )

        self.assertAlmostEqual(
            agent_summary["concerned_pixel_probe"]["parse_accuracy_high_concern"],
            0.9,
        )
        self.assertAlmostEqual(agent_summary["concerned_pixel_probe"]["gate_pass"], 0.5)
        self.assertAlmostEqual(
            extractor_summary["learned_foreground_slots"]["slot_recovery_rate"],
            0.95,
        )

    def test_intervention_invention_gate_requires_concern_and_target(self) -> None:
        payload = run_program_experiment(
            train_trials=650,
            test_trials=260,
            seed=20260616,
            epochs=45,
        )
        agents = payload["agent_summary"]

        self.assertTrue(agents["concerned_program_inventor"]["gate_pass"])
        self.assertFalse(agents["surface_program_shortcut"]["gate_pass"])
        self.assertFalse(agents["random_program_probe"]["gate_pass"])
        self.assertFalse(agents["concern_without_target"]["gate_pass"])
        self.assertFalse(agents["target_without_concern"]["gate_pass"])
        self.assertGreaterEqual(
            agents["concerned_program_inventor"]["target_accuracy_high_concern"],
            0.95,
        )
        self.assertLess(
            agents["concern_without_target"]["target_accuracy_high_concern"],
            0.25,
        )
        self.assertEqual(
            agents["target_without_concern"]["low_concern_probe_rate"],
            1.0,
        )

    def test_intervention_invention_modal_summary_averages_gate_rates(self) -> None:
        payloads = [
            {
                "agent_summary": {
                    "concerned_program_inventor": {
                        "target_accuracy_high_concern": 1.0,
                        "gate_pass": True,
                    }
                }
            },
            {
                "agent_summary": {
                    "concerned_program_inventor": {
                        "target_accuracy_high_concern": 0.5,
                        "gate_pass": False,
                    }
                }
            },
        ]

        summary = summarize_program_payloads(payloads, "agent_summary")

        self.assertAlmostEqual(
            summary["concerned_program_inventor"]["target_accuracy_high_concern"],
            0.75,
        )
        self.assertAlmostEqual(
            summary["concerned_program_inventor"]["gate_pass"],
            0.5,
        )

    def test_intervention_invention_role_transfer_records_heldout_kind(self) -> None:
        payload = run_role_transfer_experiment(
            train_trials=300,
            test_trials=120,
            seed=20260616,
            epochs=25,
            heldout_kind="food_trap",
        )
        agents = payload["agent_summary"]

        self.assertEqual(payload["manifest"]["heldout_kind"], "food_trap")
        self.assertEqual(
            payload["manifest"]["contract"],
            "2A-v1-pixels-observe_pair",
        )
        self.assertIn("concerned_program_inventor", agents)
        self.assertIn("target_accuracy_high_concern", agents["concerned_program_inventor"])

    def test_searched_program_policy_requires_searching_concern_and_target(self) -> None:
        payload = run_searched_program_experiment(
            train_trials=240,
            test_trials=100,
            seed=20260617,
            epochs=24,
        )
        agents = payload["agent_summary"]

        self.assertTrue(agents["concerned_program_search"]["gate_pass"])
        self.assertFalse(agents["reward_only_program_search"]["gate_pass"])
        self.assertFalse(agents["syntax_proxy_program_search"]["gate_pass"])
        self.assertGreaterEqual(
            agents["concerned_program_search"]["target_accuracy_high_concern"],
            0.95,
        )
        self.assertLessEqual(
            agents["concerned_program_search"]["low_concern_probe_rate"],
            0.25,
        )
        self.assertIn(
            "concern",
            agents["concerned_program_search"]["best_recipe"],
        )
        self.assertIn(
            "bind_if_useful_probe",
            agents["concerned_program_search"]["best_recipe"],
        )

    def test_searched_program_policy_modal_summary_preserves_recipe_mode(self) -> None:
        payloads = [
            {
                "agent_summary": {
                    "concerned_program_search": {
                        "target_accuracy_high_concern": 1.0,
                        "best_recipe": "concern_or_calibration+hybrid_scores",
                        "gate_pass": True,
                    }
                }
            },
            {
                "agent_summary": {
                    "concerned_program_search": {
                        "target_accuracy_high_concern": 0.5,
                        "best_recipe": "concern_or_calibration+hybrid_scores",
                        "gate_pass": False,
                    }
                }
            },
        ]

        summary = summarize_search_payloads(payloads, "agent_summary")

        self.assertAlmostEqual(
            summary["concerned_program_search"]["target_accuracy_high_concern"],
            0.75,
        )
        self.assertAlmostEqual(
            summary["concerned_program_search"]["gate_pass"],
            0.5,
        )
        self.assertEqual(
            summary["concerned_program_search"]["best_recipe"],
            "concern_or_calibration+hybrid_scores",
        )

    def test_rich_program_language_requires_concern_target_and_family(self) -> None:
        payload = run_rich_program_experiment(
            train_trials=650,
            test_trials=260,
            seed=20260617,
            epochs=45,
        )
        agents = payload["agent_summary"]

        self.assertTrue(agents["concerned_program_composer"]["gate_pass"])
        self.assertFalse(agents["surface_rich_shortcut"]["gate_pass"])
        self.assertFalse(agents["random_rich_program"]["gate_pass"])
        self.assertFalse(agents["family_without_target"]["gate_pass"])
        self.assertFalse(agents["target_without_family"]["gate_pass"])
        self.assertFalse(agents["rich_without_concern"]["gate_pass"])
        self.assertGreaterEqual(
            agents["concerned_program_composer"]["family_accuracy_high_concern"],
            0.95,
        )
        self.assertGreaterEqual(
            agents["concerned_program_composer"]["target_accuracy_high_concern"],
            0.95,
        )
        self.assertLess(
            agents["family_without_target"]["target_accuracy_high_concern"],
            0.25,
        )
        self.assertEqual(
            agents["target_without_family"]["family_accuracy_high_concern"],
            0.0,
        )
        self.assertEqual(
            agents["rich_without_concern"]["low_concern_program_rate"],
            1.0,
        )

    def test_rich_program_language_modal_summary_averages_gate_rates(self) -> None:
        payloads = [
            {
                "agent_summary": {
                    "concerned_program_composer": {
                        "family_accuracy_high_concern": 1.0,
                        "gate_pass": True,
                    }
                }
            },
            {
                "agent_summary": {
                    "concerned_program_composer": {
                        "family_accuracy_high_concern": 0.5,
                        "gate_pass": False,
                    }
                }
            },
        ]

        summary = summarize_rich_program_payloads(payloads)

        self.assertAlmostEqual(
            summary["concerned_program_composer"]["family_accuracy_high_concern"],
            0.75,
        )
        self.assertAlmostEqual(
            summary["concerned_program_composer"]["gate_pass"],
            0.5,
        )

    def test_intervention_invention_parse_transfer_records_heldout_parse(self) -> None:
        payload = run_parse_transfer_experiment(
            train_trials=300,
            test_trials=120,
            seed=20260616,
            epochs=25,
            heldout_parse="repeat_concat",
        )
        agents = payload["agent_summary"]

        self.assertEqual(payload["manifest"]["heldout_parse"], "repeat_concat")
        self.assertEqual(
            payload["manifest"]["contract"],
            "2A-v1-pixels-observe_pair",
        )
        self.assertEqual(payload["manifest"]["heldout_axis"], "true_parse")
        self.assertIn("concerned_program_inventor", agents)

    def test_intervention_transfer_suite_records_axes(self) -> None:
        payload = run_transfer_suite(
            train_trials=180,
            test_trials=80,
            seed=20260616,
            epochs=15,
            heldout_kinds=("food_trap",),
            heldout_parses=("repeat_concat",),
        )
        summary = payload["summary"]

        self.assertIn("role_kind", summary["slice_summary"])
        self.assertIn("true_parse", summary["slice_summary"])
        self.assertEqual(
            summary["transfer_gate"]["agent"],
            "concerned_program_inventor",
        )
        self.assertIn("weakest_axis", summary["transfer_gate"])

    def test_intervention_transfer_summary_requires_all_slices(self) -> None:
        payloads = [
            {
                "iid_agent_summary": {
                    "concerned_program_inventor": {
                        "gate_pass": True,
                        "target_accuracy_high_concern": 1.0,
                    }
                },
                "transfer_slices": [
                    {
                        "axis": "role_kind",
                        "heldout": "food_trap",
                        "agent_summary": {
                            "concerned_program_inventor": {
                                "gate_pass": False,
                                "target_accuracy_high_concern": 0.4,
                            }
                        },
                    }
                ],
            }
        ]

        summary = summarize_transfer_payloads(payloads)

        self.assertFalse(summary["transfer_gate"]["gate_pass"])
        self.assertEqual(summary["transfer_gate"]["weakest_axis"], "role_kind")
        self.assertEqual(summary["transfer_gate"]["weakest_heldout"], "food_trap")


if __name__ == "__main__":
    unittest.main()
