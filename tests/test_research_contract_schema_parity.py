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
    EXCEPTION_REASON_CODES,
    GIT_COMMIT_PATTERN,
    INTEGRITY_STATES,
    ISO_DATE_PATTERN,
    LEGACY_ADJUDICATION_STATEMENT,
    PACKAGE_ID_PATTERN,
    PROVENANCE_MODES,
    RUN_COVERAGE_STATES,
    SCHEMA_VERSION,
    SHA256_PATTERN,
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

    def test_contract_registry_schema_matches_shared_vocabulary(self) -> None:
        schema = self.schema("experiment_contract_registry.schema.json")
        self.assertEqual(schema["properties"]["schema_version"]["const"], SCHEMA_VERSION)
        self.assertEqual(schema["$defs"]["package_id"]["pattern"], PACKAGE_ID_PATTERN)
        self.assertEqual(schema["$defs"]["iso_date"]["pattern"], ISO_DATE_PATTERN)

        frozen = schema["properties"]["frozen_legacy"]["properties"]
        self.assertEqual(frozen["cutoff_commit"]["pattern"], GIT_COMMIT_PATTERN)
        self.assertEqual(frozen["sha256"]["pattern"], SHA256_PATTERN)

        run = schema["$defs"]["run_record"]["properties"]
        self.assertEqual(set(run["provenance_mode"]["enum"]), PROVENANCE_MODES)
        self.assertEqual(set(run["integrity_state"]["enum"]), INTEGRITY_STATES)
        self.assertEqual(run["claim_ids"]["items"]["pattern"], CLAIM_ID_PATTERN)
        self.assertEqual(run["evidence_ids"]["items"]["pattern"], EVIDENCE_ID_PATTERN)

        structured = schema["$defs"]["structured_package"]["properties"]
        self.assertEqual(set(structured["run_coverage"]["enum"]), RUN_COVERAGE_STATES)

        exception = schema["$defs"]["legacy_package"]["properties"]["exception"]
        fields = exception["properties"]
        self.assertEqual(set(fields["reason_code"]["enum"]), EXCEPTION_REASON_CODES)
        self.assertEqual(fields["adjudication"]["const"], LEGACY_ADJUDICATION_STATEMENT)
        self.assertEqual(fields["legacy_cutoff_commit"]["pattern"], GIT_COMMIT_PATTERN)
        for forbidden in ("status", "verdict", "claim_ids", "evidence_ids"):
            self.assertNotIn(forbidden, fields)
        self.assertIs(exception["additionalProperties"], False)

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

