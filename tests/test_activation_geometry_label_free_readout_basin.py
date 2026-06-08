from __future__ import annotations

import unittest

from experiments.activation_geometry.label_free_readout_basin import (
    PATCH_TEXT_REGIMES,
    PATCH_VECTOR_SURFACES,
    aggregate_rows,
    baseline_pair_specs,
    dose_response_summaries,
    label_free_pair_specs,
    neutral_carrier_text,
    pair_specs_for_set,
    source_text_for_regime,
    specificity_rows,
    summarize_readout_delta,
    target_margin,
    transfer_baseline_summaries,
)


class LabelFreeReadoutBasinTest(unittest.TestCase):
    def test_pair_specs_include_basin_and_generic_controls(self) -> None:
        specs = label_free_pair_specs()
        by_id = {row.id: row for row in specs}

        self.assertEqual(len(specs), 7)
        self.assertEqual(
            by_id["attractor->attractor_network/d=prototype"].kind,
            "positive",
        )
        self.assertEqual(
            by_id["prototype->attractor_network/d=attractor"].kind,
            "source_family",
        )
        self.assertEqual(
            by_id["valence->activation_vector/d=steering_vector"].kind,
            "generic_control",
        )

    def test_baseline_pair_specs_sample_same_and_cross_category_pairs(self) -> None:
        concepts = [
            {"id": "a1", "category": "a"},
            {"id": "a2", "category": "a"},
            {"id": "a3", "category": "a"},
            {"id": "b1", "category": "b"},
            {"id": "b2", "category": "b"},
            {"id": "c1", "category": "c"},
        ]

        specs = baseline_pair_specs(concepts, sample_count=8, seed=1)
        combined = pair_specs_for_set(
            concepts,
            pair_set="combined",
            sample_count=8,
            seed=1,
        )

        self.assertEqual(len(specs), 8)
        self.assertTrue(any(row.kind == "baseline_same_category" for row in specs))
        self.assertTrue(any(row.kind == "baseline_cross_category" for row in specs))
        self.assertEqual(len(combined), len(label_free_pair_specs()) + len(specs))

    def test_source_text_regimes(self) -> None:
        self.assertEqual(neutral_carrier_text(label="attractor network"), "Concept label: attractor network.")
        self.assertEqual(
            source_text_for_regime(
                definition_text="definition",
                label="attractor network",
                patch_text_regime="definition",
            ),
            "definition",
        )
        self.assertEqual(
            source_text_for_regime(
                definition_text="definition",
                label="attractor network",
                patch_text_regime="neutral",
            ),
            "Concept label: attractor network.",
        )

    def test_readout_delta_summary_tracks_margin_and_rank(self) -> None:
        baseline = {"target": 0.1, "source": 0.3, "distractor": 0.2}
        patched = {"target": 0.5, "source": 0.1, "distractor": 0.0}
        summary = summarize_readout_delta(
            baseline_scores=baseline,
            patched_scores=patched,
            patched_target_rank=2,
        )

        self.assertAlmostEqual(target_margin(baseline), -0.15)
        self.assertAlmostEqual(target_margin(patched), 0.45)
        self.assertAlmostEqual(summary["target_margin_delta"], 0.6)
        self.assertTrue(summary["patched_target_top3"])

    def test_specificity_keeps_patch_text_regimes_separate(self) -> None:
        rows = []
        for patch_text_regime in PATCH_TEXT_REGIMES:
            for patch_mode, delta, rank in (
                ("target", 0.2, 1),
                ("distractor", 0.1, 4),
                ("random", -0.1, 5),
                ("source_noop", 0.0, 6),
            ):
                rows.append(
                    {
                        "kind": "positive",
                        "pair": "attractor->attractor_network/d=prototype",
                        "injection_layer": 5,
                        "readout_layer": 6,
                        "patch_text_regime": patch_text_regime,
                        "patch_mode": patch_mode,
                        "summary": {
                            "target_margin_delta": delta,
                            "patched_target_top3": rank <= 3,
                        },
                    }
                )

        specificity = specificity_rows(aggregate_rows(rows))

        self.assertEqual(len(specificity), 2)
        self.assertTrue(all(row["specific_target_pass"] for row in specificity))
        self.assertEqual(
            {row["patch_text_regime"] for row in specificity},
            set(PATCH_TEXT_REGIMES),
        )

    def test_specificity_keeps_patch_alpha_levels_separate(self) -> None:
        rows = []
        for patch_alpha, target_delta in ((0.25, 0.1), (1.0, 0.4)):
            for patch_mode, delta, rank in (
                ("target", target_delta, 1),
                ("distractor", 0.2, 4),
                ("random", -0.1, 5),
                ("source_noop", 0.0, 6),
            ):
                rows.append(
                    {
                        "kind": "positive",
                        "pair": "attractor->attractor_network/d=prototype",
                        "injection_layer": 5,
                        "readout_layer": 6,
                        "patch_alpha": patch_alpha,
                        "patch_text_regime": "definition",
                        "patch_mode": patch_mode,
                        "summary": {
                            "target_margin_delta": delta,
                            "patched_target_top3": rank <= 3,
                        },
                    }
                )

        specificity = specificity_rows(aggregate_rows(rows))
        by_alpha = {row["patch_alpha"]: row for row in specificity}

        self.assertEqual(set(by_alpha), {0.25, 1.0})
        self.assertFalse(by_alpha[0.25]["specific_target_pass"])
        self.assertTrue(by_alpha[1.0]["specific_target_pass"])

    def test_specificity_keeps_patch_vector_surfaces_separate(self) -> None:
        rows = []
        for patch_vector_surface, target_delta in (
            ("hidden_state", -0.1),
            ("hook_output", 0.4),
        ):
            for patch_mode, delta, rank in (
                ("target", target_delta, 1),
                ("distractor", 0.1, 4),
                ("random", -0.1, 5),
                ("source_noop", 0.0, 6),
            ):
                rows.append(
                    {
                        "kind": "positive",
                        "pair": "attractor->attractor_network/d=prototype",
                        "injection_layer": 6,
                        "readout_layer": 6,
                        "patch_alpha": 1.0,
                        "patch_vector_surface": patch_vector_surface,
                        "patch_text_regime": "definition",
                        "patch_mode": patch_mode,
                        "summary": {
                            "target_margin_delta": delta,
                            "patched_target_top3": rank <= 3,
                        },
                    }
                )

        specificity = specificity_rows(aggregate_rows(rows))
        by_surface = {row["patch_vector_surface"]: row for row in specificity}

        self.assertEqual(set(by_surface), set(PATCH_VECTOR_SURFACES))
        self.assertFalse(by_surface["hidden_state"]["specific_target_pass"])
        self.assertTrue(by_surface["hook_output"]["specific_target_pass"])

    def test_transfer_baseline_summary_reports_focus_percentiles(self) -> None:
        specificity = [
            {
                "patch_text_regime": "definition",
                "kind": "baseline_cross_category",
                "specific_target_pass": False,
                "target_mean_target_margin_delta": 0.1,
                "target_advantage_over_best_control": -0.1,
            },
            {
                "patch_text_regime": "definition",
                "kind": "baseline_same_category",
                "specific_target_pass": True,
                "target_mean_target_margin_delta": 0.2,
                "target_advantage_over_best_control": 0.2,
            },
            {
                "patch_text_regime": "definition",
                "kind": "positive",
                "specific_target_pass": True,
                "target_mean_target_margin_delta": 0.3,
                "target_advantage_over_best_control": 0.3,
            },
        ]

        summaries = transfer_baseline_summaries(specificity)
        baseline = [
            row for row in summaries
            if row["patch_text_regime"] == "definition"
            and row["kind"] == "baseline_distribution"
        ][0]
        positive = [
            row for row in summaries
            if row["patch_text_regime"] == "definition"
            and row["kind"] == "positive"
        ][0]

        self.assertEqual(baseline["count"], 2)
        self.assertEqual(baseline["specific_pass_count"], 1)
        self.assertEqual(positive["mean_advantage_percentile_vs_baseline"], 1.0)

    def test_dose_response_summaries_report_grid_cells(self) -> None:
        specificity = [
            {
                "patch_text_regime": "definition",
                "kind": "baseline_cross_category",
                "injection_layer": 4,
                "readout_layer": 6,
                "patch_alpha": 0.5,
                "specific_target_pass": True,
                "target_mean_target_margin_delta": 0.2,
                "target_advantage_over_best_control": 0.1,
            },
            {
                "patch_text_regime": "definition",
                "kind": "baseline_cross_category",
                "injection_layer": 4,
                "readout_layer": 6,
                "patch_alpha": 0.5,
                "specific_target_pass": False,
                "target_mean_target_margin_delta": -0.1,
                "target_advantage_over_best_control": -0.2,
            },
            {
                "patch_text_regime": "definition",
                "kind": "baseline_cross_category",
                "injection_layer": 5,
                "readout_layer": 6,
                "patch_alpha": 1.0,
                "specific_target_pass": True,
                "target_mean_target_margin_delta": 0.4,
                "target_advantage_over_best_control": 0.3,
            },
        ]

        summaries = dose_response_summaries(specificity)
        by_grid = {
            (row["injection_layer"], row["patch_alpha"]): row
            for row in summaries
        }

        self.assertEqual(by_grid[(4, 0.5)]["specific_pass_count"], 1)
        self.assertEqual(by_grid[(4, 0.5)]["specific_pass_rate"], 0.5)
        self.assertEqual(by_grid[(5, 1.0)]["mean_advantage_over_best_control"], 0.3)


if __name__ == "__main__":
    unittest.main()
