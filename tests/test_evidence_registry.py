from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.validate_evidence_registry import validate


class EvidenceRegistryTests(unittest.TestCase):
    def test_committed_registry_is_valid(self) -> None:
        payload = validate()
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(set(payload["statuses"]), {
            "pass",
            "fail",
            "inconclusive",
            "not_run",
            "superseded",
            "retired",
        })

    def test_duplicate_evidence_ids_fail_closed(self) -> None:
        payload = validate()
        record = {
            "evidence_id": "EVID-DEMO-001",
            "experiment": "demo",
            "status": "not_run",
            "claim_ids": ["DEMO_CLAIM"],
            "artifact_refs": ["experiments/demo/README.md"],
        }
        payload["records"] = [record, dict(record)]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "duplicate evidence_id"):
                validate(path)

    def test_unknown_status_fails_closed(self) -> None:
        payload = validate()
        payload["statuses"]["pending"] = "ambiguous"
        with TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "exactly the six canonical statuses"):
                validate(path)


if __name__ == "__main__":
    unittest.main()
