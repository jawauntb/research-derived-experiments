from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.validate_experiment_manifest import CLAIM_TIERS, STATUSES, validate


ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "experiment_manifest.schema.json"


def valid_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "experiment_id": "demo_experiment",
        "hypothesis": "The intervention improves the registered primary metric.",
        "claim_tier": "causal",
        "controls": [
            {
                "control_id": "matched_null",
                "description": "Matched run without the intervention.",
            }
        ],
        "seeds": [11, 23, 47],
        "runtime": {
            "execution_class": "local_cpu",
            "command": ["python", "experiments/demo/run.py"],
            "estimated_minutes": 5,
        },
        "dependencies": [
            {"name": "numpy", "version": ">=1.26,<2.2"},
        ],
        "gates": [
            {
                "gate_id": "PRIMARY_EFFECT",
                "criterion": "mean_delta >= 0.10",
            },
            {
                "gate_id": "NEGATIVE_CONTROL",
                "criterion": "abs(control_delta) <= 0.02",
            },
        ],
        "artifacts": [
            {
                "kind": "summary",
                "path": "experiments/demo/results/summary.json",
                "public": True,
            }
        ],
        "status": "planned",
    }


class ExperimentManifestTests(unittest.TestCase):
    def write_manifest(self, directory: str, payload: dict) -> Path:
        path = Path(directory) / "experiment_manifest.json"
        path.write_text(json.dumps(payload))
        return path

    def test_schema_and_validator_accept_the_same_valid_contract(self) -> None:
        schema = json.loads(SCHEMA.read_text())
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.0")
        self.assertEqual(set(schema["properties"]["claim_tier"]["enum"]), CLAIM_TIERS)
        self.assertEqual(set(schema["properties"]["status"]["enum"]), STATUSES)

        with TemporaryDirectory() as directory:
            payload = validate(self.write_manifest(directory, valid_manifest()))

        self.assertEqual(payload["experiment_id"], "demo_experiment")

    def test_all_contract_fields_are_required(self) -> None:
        required = {
            "hypothesis",
            "claim_tier",
            "controls",
            "seeds",
            "runtime",
            "dependencies",
            "gates",
            "artifacts",
            "status",
        }
        schema = json.loads(SCHEMA.read_text())
        self.assertTrue(required.issubset(schema["required"]))

        for field in sorted(required):
            with self.subTest(field=field), TemporaryDirectory() as directory:
                payload = valid_manifest()
                del payload[field]
                with self.assertRaisesRegex(ValueError, f"missing required field: {field}"):
                    validate(self.write_manifest(directory, payload))

    def test_unknown_status_fails_closed(self) -> None:
        payload = valid_manifest()
        payload["status"] = "done"
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "status is not canonical: done"):
                validate(self.write_manifest(directory, payload))

    def test_unknown_claim_tier_fails_closed(self) -> None:
        payload = valid_manifest()
        payload["claim_tier"] = "universal"
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "claim_tier is not canonical: universal"):
                validate(self.write_manifest(directory, payload))

    def test_duplicate_gate_ids_fail_closed(self) -> None:
        payload = valid_manifest()
        duplicate = copy.deepcopy(payload["gates"][0])
        duplicate["criterion"] = "a differently worded criterion"
        payload["gates"].append(duplicate)
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "duplicate gate_id: PRIMARY_EFFECT"):
                validate(self.write_manifest(directory, payload))


if __name__ == "__main__":
    unittest.main()
