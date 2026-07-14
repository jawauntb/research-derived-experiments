from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.research_contracts import (
    CLAIM_ID_PATTERN,
    CLAIM_STATUSES,
    CLAIM_TIERS,
    EVIDENCE_ID_PATTERN,
    EVIDENCE_STATUSES,
    SCHEMA_VERSION,
)


ROOT = Path(__file__).resolve().parent.parent


class ResearchContractSchemaParityTests(unittest.TestCase):
    def schema(self, name: str) -> dict:
        return json.loads((ROOT / "schemas" / name).read_text())

    def test_claim_schema_matches_shared_vocabulary(self) -> None:
        schema = self.schema("claim_registry.schema.json")
        claim = schema["$defs"]["claim"]["properties"]
        self.assertEqual(schema["properties"]["schema_version"]["const"], SCHEMA_VERSION)
        self.assertEqual(set(claim["claim_tier"]["enum"]), CLAIM_TIERS)
        self.assertEqual(set(claim["status"]["enum"]), CLAIM_STATUSES)
        self.assertEqual(claim["claim_id"]["pattern"], CLAIM_ID_PATTERN)
        self.assertEqual(claim["evidence_ids"]["items"]["pattern"], EVIDENCE_ID_PATTERN)

    def test_evidence_and_gate_schemas_match_shared_vocabulary(self) -> None:
        evidence = self.schema("program_evidence_registry.schema.json")
        record = evidence["$defs"]["evidence_record"]["properties"]
        gate = self.schema("gate_verdict.schema.json")["properties"]
        self.assertEqual(set(record["status"]["enum"]), EVIDENCE_STATUSES)
        self.assertEqual(record["evidence_id"]["pattern"], EVIDENCE_ID_PATTERN)
        self.assertEqual(set(gate["status"]["enum"]), EVIDENCE_STATUSES)
        self.assertEqual(set(gate["claim_tier"]["enum"]), CLAIM_TIERS)
        self.assertEqual(gate["claim_id"]["pattern"], CLAIM_ID_PATTERN)


if __name__ == "__main__":
    unittest.main()

