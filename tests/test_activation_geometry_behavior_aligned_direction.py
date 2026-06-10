from __future__ import annotations

import unittest

from experiments.activation_geometry.behavior_aligned_direction import (
    LABEL_SCORING_REGIMES,
    PROMPT_FRAMES,
    SCORING_SURFACES,
    aggregate_rows,
    alignment_summary,
    generation_match_scores,
    gate_summaries,
    generated_text_matches_label,
    label_scoring_regime_parts,
    normalize_generated_text,
    parse_label_scoring_regimes,
    parse_direction_modes,
    parse_values,
    role_margin,
    summarize_binary_specificity,
    summarize_behavior_delta,
)
from experiments.activation_geometry.final_token_steering_pilot import pair_specs_for_set
from experiments.concept_geometry.openai_embedding_probe import Concept


class BehaviorAlignedDirectionTest(unittest.TestCase):
    def test_parse_direction_modes(self) -> None:
        self.assertEqual(
            parse_direction_modes(
                "target_learned, target_penalty_controls_1_0, "
                "target_penalty_hard_1_0, target_binary_controls_1_0, "
                "target_binary_pc1_resid, target_binary_pc3_whiten, "
                "target_binary_strict_opt_8, target_binary_strict_opt_16, "
                "caa_target_contrast"
            ),
            [
                "target_learned",
                "target_penalty_controls_1_0",
                "target_penalty_hard_1_0",
                "target_binary_controls_1_0",
                "target_binary_pc1_resid",
                "target_binary_pc3_whiten",
                "target_binary_strict_opt_8",
                "target_binary_strict_opt_16",
                "caa_target_contrast",
            ],
        )
        with self.assertRaises(ValueError):
            parse_direction_modes("centroid")

    def test_parse_heldout_alias_regimes(self) -> None:
        self.assertEqual(
            parse_values(
                "alias_0, alias_1, alias_2",
                allowed=LABEL_SCORING_REGIMES,
                name="Label regimes",
            ),
            ["alias_0", "alias_1", "alias_2"],
        )

    def test_prompt_frames_include_short_answer_interfaces(self) -> None:
        self.assertIn("source_short_answer", PROMPT_FRAMES)
        self.assertIn("latent_short_answer", PROMPT_FRAMES)
        self.assertEqual(
            parse_values(
                "source_short_answer",
                allowed=PROMPT_FRAMES,
                name="Prompt frame",
            ),
            ["source_short_answer"],
        )

    def test_scoring_surfaces_include_binary_relation_interface(self) -> None:
        self.assertIn("binary_relation", SCORING_SURFACES)
        self.assertEqual(
            parse_values(
                "binary_relation",
                allowed=SCORING_SURFACES,
                name="Scoring surface",
            ),
            ["binary_relation"],
        )

    def test_generation_match_helpers_use_phrase_boundaries(self) -> None:
        self.assertEqual(
            normalize_generated_text("Attractor-network!\n"),
            "attractor network",
        )
        self.assertTrue(
            generated_text_matches_label(
                generated_text="The answer is attractor network.",
                label="attractor_network",
            )
        )
        self.assertFalse(
            generated_text_matches_label(
                generated_text="This is schematic reasoning.",
                label="schema",
            )
        )
        scores = generation_match_scores(
            generated_text="Answer: homeostatic regulation",
            labels_by_role={
                "source": ["autopoiesis"],
                "target": ["homeostatic regulation", "homeostasis"],
                "distractor": ["self boundary"],
            },
        )

        self.assertEqual(scores["source"], 0.0)
        self.assertEqual(scores["target"], 1.0)
        self.assertEqual(scores["distractor"], 0.0)

    def test_parse_grouped_objective_label_regimes(self) -> None:
        self.assertEqual(
            parse_label_scoring_regimes(
                "alias_0+alias_1, canonical",
                name="Objective label regimes",
                allow_groups=True,
            ),
            ["alias_0+alias_1", "canonical"],
        )
        self.assertEqual(
            label_scoring_regime_parts("alias_0+alias_1", allow_groups=True),
            ["alias_0", "alias_1"],
        )
        with self.assertRaises(ValueError):
            parse_label_scoring_regimes(
                "alias_0+alias_1",
                name="Eval label regimes",
                allow_groups=False,
            )

    def test_expanded_pair_set_includes_more_controls(self) -> None:
        concept_ids = {
            "attractor",
            "attractor_network",
            "autopoiesis",
            "homeostasis",
            "validity_gate",
            "weak_constraint",
            "conceptual_space",
            "representation_manifold",
            "phase_space",
            "fixed_point",
            "prototype",
            "basin_of_attraction",
            "schema",
            "valence",
            "activation_vector",
            "steering_vector",
            "simplicity_bias",
            "embedding",
            "semantic_distance",
            "self_boundary",
        }
        concepts = [
            Concept(
                id=concept_id,
                label=concept_id.replace("_", " "),
                category="test",
                prompt=concept_id,
            )
            for concept_id in sorted(concept_ids)
        ]

        pairs = pair_specs_for_set(concepts, pair_set="expanded")
        positive_pairs = [pair for pair in pairs if pair.kind == "positive"]
        control_pairs = [pair for pair in pairs if pair.kind == "control"]

        self.assertGreater(len(positive_pairs), 3)
        self.assertGreater(len(control_pairs), 2)

    def test_target_disjoint_pair_set_controls_avoid_positive_targets(self) -> None:
        concept_ids = {
            "activation_vector",
            "attractor",
            "attractor_network",
            "autopoiesis",
            "basin_of_attraction",
            "conceptual_space",
            "embedding",
            "family_resemblance",
            "fixed_point",
            "homeostasis",
            "phase_space",
            "prototype",
            "regime_transition",
            "representation_manifold",
            "residual_content",
            "schema",
            "schema_revision",
            "self_boundary",
            "semantic_distance",
            "simplicity_bias",
            "steering_vector",
            "validity_gate",
            "valence",
            "weak_constraint",
        }
        concepts = [
            Concept(
                id=concept_id,
                label=concept_id.replace("_", " "),
                category="test",
                prompt=concept_id,
            )
            for concept_id in sorted(concept_ids)
        ]

        pairs = pair_specs_for_set(concepts, pair_set="expanded_target_disjoint")
        positive_targets = {pair.right for pair in pairs if pair.kind == "positive"}
        controls = [pair for pair in pairs if pair.kind == "control"]

        self.assertGreater(len(controls), 2)
        self.assertTrue(all(pair.control_class == "target_disjoint" for pair in controls))
        self.assertTrue(all(pair.right not in positive_targets for pair in controls))

    def test_random_relation_null_pair_set_is_target_disjoint(self) -> None:
        concept_rows = [
            ("attractor", "dynamics"),
            ("basin_of_attraction", "dynamics"),
            ("phase_space", "dynamics"),
            ("fixed_point", "dynamics"),
            ("attractor_network", "cognition"),
            ("prototype", "cognition"),
            ("schema", "cognition"),
            ("conceptual_space", "semantics"),
            ("semantic_distance", "semantics"),
            ("family_resemblance", "semantics"),
            ("embedding", "ai_geometry"),
            ("activation_vector", "ai_geometry"),
            ("steering_vector", "ai_geometry"),
            ("representation_manifold", "ai_geometry"),
            ("weak_constraint", "constraint"),
            ("simplicity_bias", "constraint"),
            ("validity_gate", "constraint"),
            ("regime_transition", "discovery"),
            ("schema_revision", "discovery"),
            ("residual_content", "discovery"),
            ("self_boundary", "agency"),
            ("autopoiesis", "agency"),
            ("homeostasis", "agency"),
            ("valence", "agency"),
        ]
        concepts = [
            Concept(
                id=concept_id,
                label=concept_id.replace("_", " "),
                category=category,
                prompt=concept_id,
            )
            for concept_id, category in concept_rows
        ]

        pairs = pair_specs_for_set(concepts, pair_set="expanded_random_nulls")
        positive_pairs = {(pair.left, pair.right) for pair in pairs if pair.kind == "positive"}
        positive_targets = {pair.right for pair in pairs if pair.kind == "positive"}
        controls = [pair for pair in pairs if pair.kind == "control"]

        self.assertEqual(len(controls), 10)
        self.assertEqual(
            sum(1 for pair in controls if pair.left == "valence" and pair.right == "steering_vector"),
            1,
        )
        self.assertTrue(all(pair.control_class == "random_relation_null" for pair in controls))
        self.assertTrue(all((pair.left, pair.right) not in positive_pairs for pair in controls))
        self.assertTrue(all(pair.right not in positive_targets for pair in controls))
        self.assertTrue(all(pair.distractor not in {pair.left, pair.right} for pair in controls))

    def test_layer3_strict_pocket_pair_set_keeps_random_null_controls(self) -> None:
        concept_rows = [
            ("attractor", "dynamics"),
            ("basin_of_attraction", "dynamics"),
            ("phase_space", "dynamics"),
            ("fixed_point", "dynamics"),
            ("attractor_network", "cognition"),
            ("prototype", "cognition"),
            ("schema", "cognition"),
            ("conceptual_space", "semantics"),
            ("semantic_distance", "semantics"),
            ("family_resemblance", "semantics"),
            ("embedding", "ai_geometry"),
            ("activation_vector", "ai_geometry"),
            ("steering_vector", "ai_geometry"),
            ("representation_manifold", "ai_geometry"),
            ("weak_constraint", "constraint"),
            ("simplicity_bias", "constraint"),
            ("validity_gate", "constraint"),
            ("regime_transition", "discovery"),
            ("schema_revision", "discovery"),
            ("residual_content", "discovery"),
            ("self_boundary", "agency"),
            ("autopoiesis", "agency"),
            ("homeostasis", "agency"),
            ("valence", "agency"),
        ]
        concepts = [
            Concept(
                id=concept_id,
                label=concept_id.replace("_", " "),
                category=category,
                prompt=concept_id,
            )
            for concept_id, category in concept_rows
        ]

        pairs = pair_specs_for_set(
            concepts,
            pair_set="layer3_strict_pocket_random_nulls",
        )
        positive_pairs = {(pair.left, pair.right) for pair in pairs if pair.kind == "positive"}
        controls = [pair for pair in pairs if pair.kind == "control"]

        self.assertEqual(
            positive_pairs,
            {
                ("attractor", "attractor_network"),
                ("fixed_point", "prototype"),
            },
        )
        self.assertEqual(len(controls), 10)
        self.assertEqual(
            sum(1 for pair in controls if pair.left == "valence" and pair.right == "steering_vector"),
            1,
        )
        self.assertTrue(all(pair.control_class == "random_relation_null" for pair in controls))
        self.assertTrue(all((pair.left, pair.right) not in positive_pairs for pair in controls))

    def test_layer3_strict_pocket_smoke_pair_set_is_minimal(self) -> None:
        concept_rows = [
            ("attractor", "dynamics"),
            ("attractor_network", "cognition"),
            ("prototype", "cognition"),
            ("embedding", "ai_geometry"),
            ("steering_vector", "ai_geometry"),
            ("valence", "agency"),
        ]
        concepts = [
            Concept(
                id=concept_id,
                label=concept_id.replace("_", " "),
                category=category,
                prompt=concept_id,
            )
            for concept_id, category in concept_rows
        ]

        pairs = pair_specs_for_set(concepts, pair_set="layer3_strict_pocket_smoke")

        self.assertEqual(
            [(pair.kind, pair.left, pair.right) for pair in pairs],
            [
                ("positive", "attractor", "attractor_network"),
                ("control", "valence", "steering_vector"),
            ],
        )
        self.assertEqual(pairs[1].control_class, "random_relation_null")

    def test_role_margin_and_behavior_delta_use_target_margin(self) -> None:
        baseline = {"source": -1.0, "target": -2.0, "distractor": -3.0}
        steered = {"source": -1.2, "target": -1.4, "distractor": -3.2}

        summary = summarize_behavior_delta(
            baseline_scores=baseline,
            steered_scores=steered,
        )

        self.assertAlmostEqual(role_margin(baseline, "target"), 0.0)
        self.assertAlmostEqual(role_margin(baseline, "source"), 1.5)
        self.assertGreater(summary["target_margin_delta"], 0)
        self.assertGreater(summary["target_logprob_delta"], 0)
        self.assertGreater(summary["target_minus_source_delta"], 0)
        self.assertGreater(summary["target_minus_distractor_delta"], 0)

    def test_aggregate_rows_gate_counts_and_alignment(self) -> None:
        rows = []
        for option_order, delta in zip(("std", "tds", "dst"), (0.2, 0.1, -0.05), strict=True):
            rows.append(
                {
                    "role": "primary",
                    "layer": 5,
                    "kind": "positive",
                    "pair": "validity_gate->weak_constraint",
                    "direction_mode": "target_learned",
                    "scale": 1.0,
                    "option_order": option_order,
                    "summary": {
                        "target_margin_delta": delta,
                        "target_logprob_delta": delta / 2,
                    },
                    "learned_alignment": {
                        "target_source_cosine": -0.1,
                        "target_distractor_cosine": -0.2,
                    },
                }
            )
        for option_order, delta in zip(("std", "tds", "dst"), (-0.2, -0.1, 0.05), strict=True):
            rows.append(
                {
                    "role": "primary",
                    "layer": 5,
                    "kind": "positive",
                    "pair": "validity_gate->weak_constraint",
                    "direction_mode": "source_learned",
                    "scale": 1.0,
                    "option_order": option_order,
                    "summary": {
                        "target_margin_delta": delta,
                        "target_logprob_delta": delta / 2,
                    },
                    "learned_alignment": {
                        "target_source_cosine": -0.1,
                        "target_distractor_cosine": -0.2,
                    },
                }
            )
        for option_order, delta in zip(("std", "tds", "dst"), (0.1, -0.1, -0.2), strict=True):
            rows.append(
                {
                    "role": "primary",
                    "layer": 5,
                    "kind": "control",
                    "pair": "valence->steering_vector",
                    "direction_mode": "target_learned",
                    "scale": 1.0,
                    "option_order": option_order,
                    "summary": {
                        "target_margin_delta": delta,
                        "target_logprob_delta": delta / 2,
                    },
                    "learned_alignment": {
                        "target_source_cosine": 0.3,
                        "target_distractor_cosine": 0.4,
                    },
                }
            )

        aggregates = aggregate_rows(rows)
        gates = gate_summaries(aggregates)
        alignments = alignment_summary(rows)

        target_positive = next(
            row
            for row in aggregates
            if row["kind"] == "positive" and row["direction_mode"] == "target_learned"
        )
        source_positive = next(
            row
            for row in aggregates
            if row["kind"] == "positive" and row["direction_mode"] == "source_learned"
        )
        positive_alignment = next(row for row in alignments if row["kind"] == "positive")
        target_gate = next(row for row in gates if row["direction_mode"] == "target_learned")

        self.assertTrue(target_positive["robust_pass"])
        self.assertFalse(source_positive["robust_pass"])
        self.assertEqual(target_gate["primary_positive_pass_count"], 1)
        self.assertEqual(target_gate["primary_valence_control_pass_count"], 0)
        self.assertAlmostEqual(positive_alignment["mean_target_source_cosine"], -0.1)
        self.assertAlmostEqual(positive_alignment["mean_target_distractor_cosine"], -0.2)

    def test_full_label_alias_rows_use_single_score_threshold(self) -> None:
        rows = [
            {
                "scoring_surface": "full_label",
                "prompt_frame": "latent_choice",
                "objective_label_scoring_regime": "alias",
                "eval_label_scoring_regime": "canonical",
                "role": "primary",
                "layer": 5,
                "kind": "positive",
                "pair": "attractor->attractor_network",
                "direction_mode": "target_learned",
                "scale": 1.0,
                "option_order": "full_label",
                "summary": {
                    "target_margin_delta": 0.2,
                    "target_logprob_delta": 0.1,
                },
                "learned_alignment": {
                    "target_source_cosine": 0.2,
                    "target_distractor_cosine": -0.1,
                },
            }
        ]

        aggregate = aggregate_rows(rows)[0]
        gate = gate_summaries([aggregate])[0]
        alignment = alignment_summary(rows)[0]

        self.assertTrue(aggregate["robust_pass"])
        self.assertEqual(aggregate["robust_pass_threshold"], 1)
        self.assertEqual(gate["scoring_surface"], "full_label")
        self.assertEqual(gate["objective_label_scoring_regime"], "alias")
        self.assertEqual(gate["eval_label_scoring_regime"], "canonical")
        self.assertEqual(gate["primary_positive_pass_count"], 1)
        self.assertEqual(alignment["eval_label_scoring_regime"], "canonical")

    def test_generation_match_gate_requires_steered_target_match(self) -> None:
        shared = {
            "scoring_surface": "generation_match",
            "prompt_frame": "source_passage",
            "objective_label_scoring_regime": "alias_0+alias_1",
            "eval_label_scoring_regime": "alias_2",
            "role": "primary",
            "layer": 5,
            "kind": "positive",
            "pair": "attractor->attractor_network",
            "scale": 1.0,
            "option_order": "generation_match",
            "summary": {
                "target_margin_delta": 0.5,
                "target_logprob_delta": 0.0,
            },
            "learned_alignment": {
                "target_source_cosine": 0.2,
                "target_distractor_cosine": -0.1,
            },
        }
        rows = [
            {
                **shared,
                "direction_mode": "target_learned",
                "scores": {
                    "baseline": {"source": 1.0, "target": 0.0, "distractor": 0.0},
                    "steered": {"source": 0.0, "target": 0.0, "distractor": 0.0},
                },
            },
            {
                **shared,
                "direction_mode": "caa_target_minus_source",
                "scores": {
                    "baseline": {"source": 1.0, "target": 0.0, "distractor": 0.0},
                    "steered": {"source": 0.0, "target": 1.0, "distractor": 0.0},
                },
            },
        ]

        aggregates = aggregate_rows(rows)
        source_suppression = next(
            row for row in aggregates if row["direction_mode"] == "target_learned"
        )
        target_match = next(
            row
            for row in aggregates
            if row["direction_mode"] == "caa_target_minus_source"
        )

        self.assertFalse(source_suppression["robust_pass"])
        self.assertEqual(source_suppression["score_surface_pass_count"], 0)
        self.assertTrue(target_match["robust_pass"])
        self.assertEqual(target_match["score_surface_pass_count"], 1)

    def test_generation_readout_gate_requires_target_score_increase(self) -> None:
        shared = {
            "scoring_surface": "generation_readout",
            "prompt_frame": "source_passage",
            "objective_label_scoring_regime": "alias_0+alias_1",
            "eval_label_scoring_regime": "alias_2",
            "role": "primary",
            "layer": 5,
            "kind": "positive",
            "pair": "attractor->attractor_network",
            "scale": 1.0,
            "option_order": "generation_readout",
            "learned_alignment": {
                "target_source_cosine": 0.2,
                "target_distractor_cosine": -0.1,
            },
        }
        rows = [
            {
                **shared,
                "direction_mode": "target_learned",
                "summary": {
                    "target_margin_delta": 0.5,
                    "target_logprob_delta": 0.0,
                },
            },
            {
                **shared,
                "direction_mode": "caa_target_minus_source",
                "scores": {
                    "baseline": {"best_role": "source"},
                    "steered": {"best_role": "target"},
                },
                "summary": {
                    "target_margin_delta": 0.5,
                    "target_logprob_delta": 0.1,
                },
            },
            {
                **shared,
                "direction_mode": "random_same_norm",
                "scores": {
                    "baseline": {"best_role": "source"},
                    "steered": {"best_role": "source"},
                },
                "summary": {
                    "target_margin_delta": 0.5,
                    "target_logprob_delta": 0.1,
                },
            },
        ]

        aggregates = aggregate_rows(rows)
        source_suppression = next(
            row for row in aggregates if row["direction_mode"] == "target_learned"
        )
        target_increase = next(
            row
            for row in aggregates
            if row["direction_mode"] == "caa_target_minus_source"
        )
        non_target_best_role = next(
            row for row in aggregates if row["direction_mode"] == "random_same_norm"
        )

        self.assertFalse(source_suppression["robust_pass"])
        self.assertEqual(source_suppression["score_surface_pass_count"], 0)
        self.assertFalse(non_target_best_role["robust_pass"])
        self.assertEqual(non_target_best_role["score_surface_pass_count"], 0)
        self.assertTrue(target_increase["robust_pass"])
        self.assertEqual(target_increase["score_surface_pass_count"], 1)

    def test_binary_relation_gate_requires_target_yes_margin_positive(self) -> None:
        shared = {
            "scoring_surface": "binary_relation",
            "prompt_frame": "source_passage",
            "objective_label_scoring_regime": "alias_0+alias_1",
            "eval_label_scoring_regime": "alias_2",
            "role": "primary",
            "layer": 5,
            "kind": "positive",
            "pair": "attractor->attractor_network",
            "scale": 1.0,
            "option_order": "binary_relation",
            "learned_alignment": {
                "target_source_cosine": 0.2,
                "target_distractor_cosine": -0.1,
            },
        }
        rows = [
            {
                **shared,
                "direction_mode": "target_learned",
                "scores": {
                    "steered": {"target": -0.1},
                },
                "summary": {
                    "target_margin_delta": 0.5,
                    "target_logprob_delta": 0.1,
                },
            },
            {
                **shared,
                "direction_mode": "caa_target_minus_source",
                "scores": {
                    "steered": {"target": 0.2},
                },
                "summary": {
                    "target_margin_delta": 0.5,
                    "target_logprob_delta": 0.1,
                },
            },
            {
                **shared,
                "direction_mode": "random_same_norm",
                "scores": {
                    "steered": {"target": 0.2},
                },
                "summary": {
                    "target_margin_delta": 0.5,
                    "target_logprob_delta": 0.0,
                },
            },
        ]

        aggregates = aggregate_rows(rows)
        negative_target = next(
            row for row in aggregates if row["direction_mode"] == "target_learned"
        )
        target_increase = next(
            row
            for row in aggregates
            if row["direction_mode"] == "caa_target_minus_source"
        )
        no_target_increase = next(
            row for row in aggregates if row["direction_mode"] == "random_same_norm"
        )

        self.assertFalse(negative_target["robust_pass"])
        self.assertEqual(negative_target["score_surface_pass_count"], 0)
        self.assertFalse(no_target_increase["robust_pass"])
        self.assertEqual(no_target_increase["score_surface_pass_count"], 0)
        self.assertTrue(target_increase["robust_pass"])
        self.assertEqual(target_increase["score_surface_pass_count"], 1)

    def test_binary_specificity_summarizes_yes_bias_controls(self) -> None:
        summary = summarize_binary_specificity(
            baseline_scores={
                "target": -2.0,
                "binary_control_margins": {"blank": -1.0, "generic": -0.5},
                "binary_carrier_margins": {"always_false": -1.2},
            },
            steered_scores={
                "target": 0.3,
                "binary_control_margins": {"blank": -0.7, "generic": 0.1},
                "binary_carrier_margins": {"always_false": -0.2},
            },
        )

        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertAlmostEqual(summary["target_delta"], 2.3)
        self.assertEqual(summary["max_control_delta_name"], "always_false")
        self.assertAlmostEqual(summary["max_control_delta"], 1.0)
        self.assertAlmostEqual(summary["target_delta_over_max_control_delta"], 1.3)
        self.assertEqual(summary["max_control_steered_name"], "generic")
        self.assertAlmostEqual(summary["target_steered_over_max_control_steered"], 0.2)

    def test_binary_relation_gate_rejects_yes_bias_control_leakage(self) -> None:
        shared = {
            "scoring_surface": "binary_relation",
            "prompt_frame": "source_passage",
            "objective_label_scoring_regime": "alias_0+alias_1",
            "eval_label_scoring_regime": "alias_2",
            "role": "primary",
            "layer": 5,
            "kind": "positive",
            "pair": "attractor->attractor_network",
            "scale": 1.0,
            "option_order": "binary_relation",
            "learned_alignment": {},
        }
        rows = [
            {
                **shared,
                "direction_mode": "target_binary_controls_1_0",
                "scores": {
                    "baseline": {
                        "source": -0.2,
                        "target": -2.0,
                        "distractor": -0.1,
                        "binary_control_margins": {"blank": -1.0, "generic": -1.0},
                        "binary_carrier_margins": {"always_false": -1.0},
                    },
                    "steered": {
                        "source": -0.1,
                        "target": 0.3,
                        "distractor": -0.2,
                        "binary_control_margins": {"blank": -0.5, "generic": -0.4},
                        "binary_carrier_margins": {"always_false": -0.2},
                    },
                },
                "summary": {
                    "target_margin_delta": 2.25,
                    "target_logprob_delta": 2.3,
                },
            },
            {
                **shared,
                "direction_mode": "target_binary_controls_2_0",
                "scores": {
                    "baseline": {
                        "source": -0.2,
                        "target": -2.0,
                        "distractor": -0.1,
                        "binary_control_margins": {"blank": -1.0, "generic": -1.0},
                        "binary_carrier_margins": {"always_false": -1.0},
                    },
                    "steered": {
                        "source": -0.1,
                        "target": 0.3,
                        "distractor": -0.2,
                        "binary_control_margins": {"blank": 0.4, "generic": -0.4},
                        "binary_carrier_margins": {"always_false": -0.2},
                    },
                },
                "summary": {
                    "target_margin_delta": 2.25,
                    "target_logprob_delta": 2.3,
                },
            },
            {
                **shared,
                "direction_mode": "target_binary_controls_4_0",
                "scores": {
                    "baseline": {
                        "source": -0.2,
                        "target": -2.0,
                        "distractor": -0.1,
                        "binary_control_margins": {"blank": -1.0, "generic": -1.0},
                        "binary_carrier_margins": {"always_false": -1.0},
                    },
                    "steered": {
                        "source": -0.1,
                        "target": 0.3,
                        "distractor": -0.2,
                        "binary_control_margins": {"blank": -0.5, "generic": -0.4},
                        "binary_carrier_margins": {"always_false": 0.2},
                    },
                },
                "summary": {
                    "target_margin_delta": 2.25,
                    "target_logprob_delta": 2.3,
                },
            },
        ]

        aggregates = aggregate_rows(rows)
        clean = next(
            row
            for row in aggregates
            if row["direction_mode"] == "target_binary_controls_1_0"
        )
        control_beats_target = next(
            row
            for row in aggregates
            if row["direction_mode"] == "target_binary_controls_2_0"
        )
        false_carrier_positive = next(
            row
            for row in aggregates
            if row["direction_mode"] == "target_binary_controls_4_0"
        )

        self.assertTrue(clean["robust_pass"])
        self.assertFalse(control_beats_target["robust_pass"])
        self.assertFalse(false_carrier_positive["robust_pass"])
        self.assertAlmostEqual(
            clean["mean_binary_target_delta_over_max_control_delta"],
            1.5,
        )


if __name__ == "__main__":
    unittest.main()
