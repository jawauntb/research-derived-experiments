from __future__ import annotations

import unittest

from experiments.activation_geometry.label_free_readout_basin import (
    PATCH_TEXT_REGIMES,
    aggregate_rows,
    label_free_pair_specs,
    neutral_carrier_text,
    source_text_for_regime,
    specificity_rows,
    summarize_readout_delta,
    target_margin,
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


if __name__ == "__main__":
    unittest.main()
