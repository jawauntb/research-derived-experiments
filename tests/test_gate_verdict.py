from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.validate_gate_verdict import discover_verdicts, known_claim_ids, validate


ROOT = Path(__file__).resolve().parent.parent
COMMITTED = (
    ROOT
    / "experiments"
    / "commitment_surface"
    / "results"
    / "gate_verdicts"
    / "e5_strict_coverage.json"
)
MANIFEST = ROOT / "experiments" / "commitment_surface" / "experiment_manifest.json"


class GateVerdictTests(unittest.TestCase):
    def test_committed_gate_verdict_is_registered_and_valid(self) -> None:
        verdict = validate(COMMITTED, claims=known_claim_ids())
        self.assertEqual(verdict["status"], "fail")
        self.assertIn(COMMITTED, discover_verdicts())

    def test_unknown_claim_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "claim_id is not registered"):
            validate(COMMITTED, claims={"SOME_OTHER_CLAIM"})

    def test_gate_must_be_registered_in_neighboring_manifest(self) -> None:
        payload = json.loads(COMMITTED.read_text())
        payload["gate_id"] = "E5_UNKNOWN_GATE"
        with TemporaryDirectory() as directory:
            path = Path(directory) / "verdict.json"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "not registered in experiment manifest"):
                validate(path, manifest_path=MANIFEST)

    def test_dangling_evidence_ref_fails_closed(self) -> None:
        payload = json.loads(COMMITTED.read_text())
        payload["evidence_refs"] = ["experiments/missing/result.json"]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "verdict.json"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "does not resolve"):
                validate(path)

    def test_unknown_and_missing_fields_fail_closed(self) -> None:
        original = json.loads(COMMITTED.read_text())
        mutations = [
            ("missing", lambda payload: payload.pop("observed"), "missing required field"),
            ("unknown", lambda payload: payload.__setitem__("extra", True), "unknown field"),
        ]
        for label, mutate, message in mutations:
            with self.subTest(label=label), TemporaryDirectory() as directory:
                payload = copy.deepcopy(original)
                mutate(payload)
                path = Path(directory) / "verdict.json"
                path.write_text(json.dumps(payload))
                with self.assertRaisesRegex(ValueError, message):
                    validate(path)


if __name__ == "__main__":
    unittest.main()
