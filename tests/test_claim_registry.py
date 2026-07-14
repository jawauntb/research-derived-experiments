from __future__ import annotations

import json
import copy
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.validate_claim_registry import validate


class ClaimRegistryTests(unittest.TestCase):
    def test_committed_claims_reference_known_evidence(self) -> None:
        payload = validate()
        self.assertEqual(len(payload["claims"]), 12)

    def test_unknown_evidence_fails_closed(self) -> None:
        claims = json.loads(Path("docs/claim_registry.json").read_text())
        claims["claims"][0]["evidence_ids"] = ["EVID-DOES-NOT-EXIST"]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "claims.json"
            path.write_text(json.dumps(claims))
            with self.assertRaisesRegex(ValueError, "unknown evidence"):
                validate(path)

    def test_missing_or_unknown_root_fields_fail_closed(self) -> None:
        original = json.loads(Path("docs/claim_registry.json").read_text())
        mutations = [
            ("missing claims", lambda payload: payload.pop("claims")),
            ("missing generated_by", lambda payload: payload.pop("generated_by")),
            ("unknown field", lambda payload: payload.__setitem__("extra", True)),
        ]
        for label, mutate in mutations:
            with self.subTest(label=label), TemporaryDirectory() as directory:
                payload = copy.deepcopy(original)
                mutate(payload)
                path = Path(directory) / "claims.json"
                path.write_text(json.dumps(payload))
                with self.assertRaisesRegex(ValueError, "root fields"):
                    validate(path)

    def test_evidence_to_claim_link_must_resolve_bidirectionally(self) -> None:
        claims = json.loads(Path("docs/claim_registry.json").read_text())
        evidence = json.loads(Path("docs/program_evidence_registry.json").read_text())
        evidence["records"][0]["claim_ids"] = ["UNKNOWN_CLAIM"]
        with TemporaryDirectory() as directory:
            claims_path = Path(directory) / "claims.json"
            evidence_path = Path(directory) / "evidence.json"
            claims_path.write_text(json.dumps(claims))
            evidence_path.write_text(json.dumps(evidence))
            with self.assertRaisesRegex(ValueError, "unknown claim"):
                validate(claims_path, evidence_path)

    def test_claim_to_evidence_link_must_resolve_bidirectionally(self) -> None:
        claims = json.loads(Path("docs/claim_registry.json").read_text())
        evidence = json.loads(Path("docs/program_evidence_registry.json").read_text())
        claim_id = claims["claims"][0]["claim_id"]
        evidence_id = claims["claims"][0]["evidence_ids"][0]
        record = next(
            item for item in evidence["records"] if item["evidence_id"] == evidence_id
        )
        record["claim_ids"].remove(claim_id)
        with TemporaryDirectory() as directory:
            claims_path = Path(directory) / "claims.json"
            evidence_path = Path(directory) / "evidence.json"
            claims_path.write_text(json.dumps(claims))
            evidence_path.write_text(json.dumps(evidence))
            with self.assertRaisesRegex(ValueError, "not bidirectional"):
                validate(claims_path, evidence_path)


if __name__ == "__main__":
    unittest.main()
