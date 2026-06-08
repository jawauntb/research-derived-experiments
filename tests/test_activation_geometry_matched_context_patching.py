from __future__ import annotations

import unittest

from experiments.activation_geometry.matched_context_patching import (
    calibration_prompt,
    matched_context_prompt,
    option_order_key,
    patch_concept_for_mode,
)


class MatchedContextPatchingTest(unittest.TestCase):
    def test_patch_concept_for_mode(self) -> None:
        pair = {
            "left": "source",
            "right": "target",
            "distractor": "distractor",
            "random_patch": "random",
        }

        self.assertEqual(patch_concept_for_mode(pair, "target"), "target")
        self.assertEqual(patch_concept_for_mode(pair, "distractor"), "distractor")
        self.assertEqual(patch_concept_for_mode(pair, "random"), "random")
        self.assertEqual(patch_concept_for_mode(pair, "source_noop"), "source")
        with self.assertRaises(ValueError):
            patch_concept_for_mode(pair, "magic")

    def test_calibration_prompt_respects_option_order(self) -> None:
        prompt = calibration_prompt(
            source_text="Source text.",
            labels_by_role={
                "source": "Source",
                "target": "Target",
                "distractor": "Distractor",
            },
            option_order=("distractor", "target", "source"),
        )

        self.assertIn("A. Distractor\nB. Target\nC. Source", prompt)
        self.assertEqual(option_order_key(("distractor", "target", "source")), "dts")

    def test_matched_context_prompt_uses_patch_concept_text(self) -> None:
        pair = {
            "left": "source",
            "right": "target",
            "distractor": "distractor",
            "random_patch": "random",
        }
        source_texts = {
            "source": "Source concept text.",
            "target": "Target concept text.",
            "distractor": "Distractor concept text.",
            "random": "Random concept text.",
        }
        labels_by_role = {
            "source": "Source",
            "target": "Target",
            "distractor": "Distractor",
        }

        target_context = matched_context_prompt(
            pair=pair,
            mode="target",
            source_text_by_concept=source_texts,
            labels_by_role=labels_by_role,
            option_order=("source", "target", "distractor"),
        )
        source_context = matched_context_prompt(
            pair=pair,
            mode="source_noop",
            source_text_by_concept=source_texts,
            labels_by_role=labels_by_role,
            option_order=("source", "target", "distractor"),
        )

        self.assertEqual(target_context["patch_concept"], "target")
        self.assertTrue(target_context["prompt"].startswith("Target concept text."))
        self.assertEqual(source_context["patch_concept"], "source")
        self.assertTrue(source_context["prompt"].startswith("Source concept text."))


if __name__ == "__main__":
    unittest.main()
