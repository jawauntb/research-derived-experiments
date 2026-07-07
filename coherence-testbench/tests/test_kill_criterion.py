"""Smoke tests for the kill-criterion loader + verdict logic.

These do NOT exercise the decoders (that needs BBBD on disk); they lock the
invariants of the gate itself so the pre-registration cannot silently drift.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from coherence.config import load_kill_criterion  # noqa: E402


CFG = HERE.parent / "config" / "kill_criterion.yaml"


class TestKillCriterion(unittest.TestCase):
    def setUp(self):
        self.kc = load_kill_criterion(CFG)

    def test_content_hash_stable(self):
        # Loading twice yields the same hash — no accidental rewrite in loader.
        kc2 = load_kill_criterion(CFG)
        self.assertEqual(self.kc.content_hash, kc2.content_hash)

    def test_go_verdict_when_all_pass(self):
        v = self.kc.verdict(
            lso_bacc=0.65,
            bits_per_s=0.10,
            gen_gap=0.10,
            per_seed_baccs=[0.60, 0.62, 0.63, 0.61, 0.64],
        )
        self.assertEqual(v, "GO")

    def test_kill_verdict_when_at_chance(self):
        v = self.kc.verdict(
            lso_bacc=0.51,
            bits_per_s=0.001,
            gen_gap=0.20,
            per_seed_baccs=[0.50, 0.51, 0.52, 0.49, 0.51],
        )
        self.assertEqual(v, "KILL")

    def test_inconclusive_when_between(self):
        v = self.kc.verdict(
            lso_bacc=0.58,
            bits_per_s=0.03,
            gen_gap=0.20,
            per_seed_baccs=[0.55, 0.56, 0.57, 0.58, 0.59],
        )
        self.assertEqual(v, "INCONCLUSIVE")

    def test_seed_floor_blocks_go(self):
        # Same aggregate metrics but one seed below the per-seed floor.
        v = self.kc.verdict(
            lso_bacc=0.65,
            bits_per_s=0.10,
            gen_gap=0.10,
            per_seed_baccs=[0.60, 0.62, 0.54, 0.61, 0.64],
        )
        self.assertNotEqual(v, "GO")

    def test_gap_blocks_go(self):
        v = self.kc.verdict(
            lso_bacc=0.65,
            bits_per_s=0.10,
            gen_gap=0.30,  # too wide
            per_seed_baccs=[0.60, 0.62, 0.63, 0.61, 0.64],
        )
        self.assertNotEqual(v, "GO")


if __name__ == "__main__":
    unittest.main()
