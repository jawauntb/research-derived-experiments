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
from scripts.validate_experiment_manifest import (
    CONTRACT_COVERAGE_MODES,
    FROZEN_LEGACY_PACKAGES_SHA256,
    INTEGRITY_STATES,
    LEGACY_REASON_CODES,
    PROVENANCE_MODES,
    RUN_COVERAGE_STATES,
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

    def test_experiment_contract_registry_schema_matches_validator_vocabulary(self) -> None:
        schema = self.schema("experiment_contract_registry.schema.json")
        policy = schema["properties"]["legacy_policy"]["properties"]
        structured = schema["$defs"]["structured_package"]["properties"]
        run = schema["$defs"]["run_record"]["properties"]
        exception = schema["$defs"]["legacy_exception"]["properties"]

        self.assertEqual(schema["properties"]["schema_version"]["const"], SCHEMA_VERSION)
        coverage_modes = {
            schema["$defs"][branch["$ref"].split("/")[-1]]["properties"]["coverage_mode"]["const"]
            for branch in schema["$defs"]["package_record"]["oneOf"]
        }
        self.assertEqual(coverage_modes, CONTRACT_COVERAGE_MODES)
        self.assertEqual(set(structured["run_coverage"]["enum"]), RUN_COVERAGE_STATES)
        self.assertEqual(set(run["provenance_mode"]["enum"]), PROVENANCE_MODES)
        self.assertEqual(set(run["integrity_state"]["enum"]), INTEGRITY_STATES)
        self.assertEqual(set(exception["reason_code"]["enum"]), LEGACY_REASON_CODES)
        self.assertEqual(exception["adjudicates_claims"]["const"], False)
        self.assertEqual(policy["warning_days"]["const"], 30)
        self.assertEqual(policy["max_exception_horizon_days"]["const"], 180)
        self.assertEqual(
            policy["frozen_legacy_packages_sha256"]["const"],
            FROZEN_LEGACY_PACKAGES_SHA256,
        )


if __name__ == "__main__":
    unittest.main()
