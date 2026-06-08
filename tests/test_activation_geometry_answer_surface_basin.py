from __future__ import annotations

import unittest

from experiments.activation_geometry.answer_surface_basin_diagnostic import (
    LABEL_REGIMES,
    PATCH_TEXT_REGIMES,
    aggregate_rows,
    answer_surface_pair_specs,
    calibration_prompt,
    concept_label,
    gate_summaries,
    neutral_carrier_text,
    source_text_for_regime,
    specificity_rows,
)


class AnswerSurfaceBasinDiagnosticTest(unittest.TestCase):
    def test_pair_specs_cover_source_family_sweep(self) -> None:
        specs = answer_surface_pair_specs()
        ids = {row.id for row in specs}

        self.assertEqual(len(specs), 5)
        self.assertIn("dynamics:attractor->attractor_network/d=prototype", ids)
        self.assertIn("dynamics:prototype->attractor_network/d=attractor", ids)
        self.assertIn("dynamics:basin_of_attraction->attractor_network/d=attractor", ids)

    def test_label_and_patch_text_regimes(self) -> None:
        self.assertEqual(
            concept_label(
                concept_id="attractor_network",
                canonical_label="attractor network",
                label_regime="canonical",
            ),
            "attractor network",
        )
        self.assertEqual(
            concept_label(
                concept_id="attractor_network",
                canonical_label="attractor network",
                label_regime="alias",
            ),
            "recurrent stable-state network",
        )
        self.assertEqual(
            concept_label(
                concept_id="attractor_network",
                canonical_label="attractor network",
                label_regime="symbol",
            ),
            "signal beta",
        )
        self.assertEqual(neutral_carrier_text(label="signal beta"), "Concept label: signal beta.")
        self.assertEqual(
            source_text_for_regime(
                definition_text="definition text",
                label="signal beta",
                patch_text_regime="definition",
            ),
            "definition text",
        )
        self.assertEqual(
            source_text_for_regime(
                definition_text="definition text",
                label="signal beta",
                patch_text_regime="neutral",
            ),
            "Concept label: signal beta.",
        )

    def test_calibration_prompt_uses_surface_labels(self) -> None:
        prompt = calibration_prompt(
            source_text="attractor: a stable region",
            labels_by_role={
                "source": "signal alpha",
                "target": "signal beta",
                "distractor": "signal epsilon",
            },
            option_order=("source", "target", "distractor"),
            prompt_frame="dynamics",
        )

        self.assertIn("B. signal beta", prompt)
        self.assertIn("stable-state dynamics", prompt)

    def test_aggregation_keeps_label_and_patch_regimes_separate(self) -> None:
        rows = []
        for label_regime in LABEL_REGIMES[:2]:
            for patch_text_regime in PATCH_TEXT_REGIMES:
                for patch_mode, delta in (
                    ("target", 0.2),
                    ("distractor", 0.1),
                    ("random", -0.1),
                    ("source_noop", 0.0),
                ):
                    for option_order in ("std", "tds", "dst"):
                        rows.append(
                            {
                                "role": "primary",
                                "layer": 5,
                                "kind": "positive",
                                "pair": "dynamics:attractor->attractor_network/d=prototype",
                                "label_regime": label_regime,
                                "patch_text_regime": patch_text_regime,
                                "patch_mode": patch_mode,
                                "option_order": option_order,
                                "summary": {"target_margin_delta": delta},
                            }
                        )

        aggregates = aggregate_rows(rows)
        specificity = specificity_rows(aggregates)
        summaries = gate_summaries(specificity)

        self.assertEqual(len(specificity), 4)
        self.assertTrue(all(row["specific_target_pass"] for row in specificity))
        primary_canonical_definition = [
            row
            for row in summaries
            if row["role"] == "primary"
            and row["label_regime"] == "canonical"
            and row["patch_text_regime"] == "definition"
        ][0]
        self.assertEqual(primary_canonical_definition["positive_specific_pass_count"], 1)
        self.assertEqual(primary_canonical_definition["positive_total"], 1)


if __name__ == "__main__":
    unittest.main()
