from __future__ import annotations

import unittest

from experiments.structure_compiler.core import (
    MEDIA,
    evaluate_benchmark,
    run_structure,
)


class StructureCompilerTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_every_medium_roundtrips(self) -> None:
        traj = run_structure()
        for medium in MEDIA:
            embodiment = medium.compile_fn(traj)
            recovered = medium.readback_fn(embodiment)
            self.assertEqual(recovered, traj, msg=f"{medium.name} did not round-trip")

    def test_structure_has_phase_transition_and_hysteresis(self) -> None:
        traj = run_structure()
        regimes = {node.regime for node in traj}
        self.assertEqual(regimes, {"low", "high"})
        # A level strictly between the two thresholds occurs in both regimes.
        ambiguous = {node.regime for node in traj if 2 < node.level < 5}
        self.assertEqual(ambiguous, {"low", "high"})

    def test_media_are_one_work(self) -> None:
        payload = evaluate_benchmark()
        self.assertTrue(payload["gates"]["cross_medium_structural_identity"])


if __name__ == "__main__":
    unittest.main()
