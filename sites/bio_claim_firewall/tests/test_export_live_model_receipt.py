import hashlib
import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "export_live_model_receipt.py"


def load_exporter():
    spec = importlib.util.spec_from_file_location(
        "export_live_model_receipt", MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load live receipt exporter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LiveModelReceiptExporterTests(unittest.TestCase):
    def test_sanitize_run_is_allowlist_only(self):
        exporter = load_exporter()
        raw = {
            "schema_version": "0.1.0",
            "study_id": "phase5-live-claim-adversarial",
            "status": "passed",
            "executed_at": "2026-09-02T16:23:01+00:00",
            "case_count": 1,
            "repetitions": 3,
            "total_repetitions": 3,
            "safe_repetitions": 3,
            "checker_version": "0.1.0",
            "model_config_sha256": "a" * 64,
            "model_stats": {
                "claim_parser": {
                    "errors": 0,
                    "successful_calls": 3,
                    "total_calls": 3,
                    "total_latency_ms": 123.8,
                    "total_tokens": 456,
                    "raw_provider_response": "must-not-ship",
                }
            },
            "manifest": {"approved_sha256": "b" * 64, "loaded_sha256": "b" * 64},
            "source_hashes": {"dataset": "c" * 64},
            "results": [
                {
                    "case_id": "LIVE-01",
                    "attack_class": "supported_positive_control",
                    "safe": True,
                    "local_path": "/private/tmp/run.json",
                    "error": "must-not-ship",
                    "parser": {
                        "provider": "openai",
                        "model": "gpt-test",
                        "prompt_ref": "claim_parser/test@v1",
                        "api_key": "must-not-ship",
                    },
                },
                {
                    "case_id": "LIVE-01",
                    "attack_class": "supported_positive_control",
                    "safe": True,
                    "parser": {
                        "provider": "openai",
                        "model": "gpt-test",
                        "prompt_ref": "claim_parser/test@v1",
                    },
                },
                {
                    "case_id": "LIVE-01",
                    "attack_class": "supported_positive_control",
                    "safe": True,
                    "parser": {
                        "provider": "openai",
                        "model": "gpt-test",
                        "prompt_ref": "claim_parser/test@v1",
                    },
                },
            ],
            "environment": {"OPENAI_API_KEY": "must-not-ship"},
        }
        raw_bytes = json.dumps(raw, sort_keys=True).encode()
        run = exporter.sanitize_run(
            raw,
            exporter.RunSpec(
                stage="final_boundary",
                label="Prompt + deterministic boundary",
                expected_sha256=hashlib.sha256(raw_bytes).hexdigest(),
                expected_prompt_ref="claim_parser/test@v1",
                expected_manifest_sha256="b" * 64,
                expected_case_count=1,
                path=Path("ignored.summary.json"),
            ),
            raw_bytes,
        )

        self.assertEqual(
            set(run),
            {
                "stage",
                "label",
                "provider",
                "model",
                "prompt_ref",
                "status",
                "executed_at",
                "safe_repetitions",
                "total_repetitions",
                "summary_sha256",
                "manifest_sha256",
                "case_count",
                "repetitions",
                "model_config_sha256",
                "model_usage",
                "case_results",
            },
        )
        self.assertEqual(
            set(run["case_results"][0]),
            {"case_id", "attack_class", "safe_repetitions", "total_repetitions"},
        )
        serialized = json.dumps(run)
        self.assertNotIn("must-not-ship", serialized)
        self.assertNotIn("/private/", serialized)
        self.assertNotIn("api_key", serialized.lower())
        self.assertEqual(run["provider"], "openai")
        self.assertEqual(run["model"], "gpt-test")

    def test_sanitize_run_rejects_digest_mismatch(self):
        exporter = load_exporter()
        raw = {"status": "passed"}
        with self.assertRaisesRegex(ValueError, "digest"):
            exporter.sanitize_run(
                raw,
                exporter.RunSpec(
                    stage="baseline",
                    label="Original parser",
                    expected_sha256="0" * 64,
                    expected_prompt_ref="claim_parser/test@v1",
                    expected_manifest_sha256="b" * 64,
                    expected_case_count=1,
                    path=Path("ignored.summary.json"),
                ),
                b"{}",
            )

    def test_sanitize_run_rejects_mixed_parser_identity(self):
        exporter = load_exporter()
        results = [
            {
                "case_id": "LIVE-01",
                "attack_class": "control",
                "safe": True,
                "parser": {
                    "provider": "openai",
                    "model": model,
                    "prompt_ref": "claim_parser/test@v1",
                },
            }
            for model in ("gpt-a", "gpt-b")
        ]
        raw = {
            "status": "passed",
            "executed_at": "2026-09-02T16:23:01+00:00",
            "case_count": 1,
            "repetitions": 2,
            "total_repetitions": 2,
            "safe_repetitions": 2,
            "model_config_sha256": "a" * 64,
            "manifest": {"approved_sha256": "b" * 64, "loaded_sha256": "b" * 64},
            "model_stats": {
                "claim_parser": {
                    "errors": 0,
                    "successful_calls": 2,
                    "total_calls": 2,
                    "total_latency_ms": 10,
                    "total_tokens": 20,
                }
            },
            "results": results,
        }
        raw_bytes = json.dumps(raw, sort_keys=True).encode()
        with self.assertRaisesRegex(ValueError, "parser identity"):
            exporter.sanitize_run(
                raw,
                exporter.RunSpec(
                    stage="baseline",
                    label="Original parser",
                    expected_sha256=hashlib.sha256(raw_bytes).hexdigest(),
                    expected_prompt_ref="claim_parser/test@v1",
                    expected_manifest_sha256="b" * 64,
                    expected_case_count=1,
                    path=Path("ignored.summary.json"),
                ),
                raw_bytes,
            )

    def test_build_receipt_binds_the_public_payload(self):
        exporter = load_exporter()
        if not all(spec.path.is_file() for spec in exporter.RUN_SPECS):
            self.skipTest("private live-run summaries are not present in this checkout")
        receipt = exporter.build_receipt()
        digest = receipt.pop("canonical_digest")
        canonical = json.dumps(
            receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()

        self.assertEqual(hashlib.sha256(canonical).hexdigest(), digest)
        self.assertEqual(
            [run["safe_repetitions"] for run in receipt["runs"]], [9, 33, 48]
        )
        self.assertEqual(receipt["experiment"]["total_repetitions"], 48)
        self.assertEqual(receipt["experiment"]["provider"], "openai")
        self.assertTrue(receipt["experiment"]["frozen"])
        exporter.validate_public_receipt(
            {**receipt, "canonical_digest": digest}, expected_digest=None
        )

    def test_build_receipt_requires_exact_case_matrix_and_integral_usage(self):
        exporter = load_exporter()
        if not all(spec.path.is_file() for spec in exporter.RUN_SPECS):
            self.skipTest("private live-run summaries are not present in this checkout")
        receipt = exporter.build_receipt()
        exporter.validate_public_receipt(receipt, expected_digest=None)
        self.assertEqual(receipt["experiment"]["case_count"], 16)
        self.assertEqual(receipt["experiment"]["repetitions"], 3)
        for run, spec in zip(receipt["runs"], exporter.RUN_SPECS, strict=True):
            expected = set(exporter._expected_case_identities(spec.expected_case_count))
            self.assertEqual(
                {
                    (case["case_id"], case["attack_class"])
                    for case in run["case_results"]
                },
                expected,
            )
            self.assertIsInstance(run["model_usage"]["total_latency_ms"], int)
            self.assertEqual(
                run["model_usage"]["total_calls"],
                run["model_usage"]["successful_calls"] + run["model_usage"]["errors"],
            )

    def test_public_validation_rejects_tampered_totals_and_case_identity(self):
        exporter = load_exporter()
        if not all(spec.path.is_file() for spec in exporter.RUN_SPECS):
            self.skipTest("private live-run summaries are not present in this checkout")
        receipt = exporter.build_receipt()

        totals_tampered = deepcopy(receipt)
        totals_tampered["runs"][0]["case_results"][0]["safe_repetitions"] += 1
        totals_tampered["canonical_digest"] = exporter._sha256(
            exporter._canonical(
                {
                    key: value
                    for key, value in totals_tampered.items()
                    if key != "canonical_digest"
                }
            )
        )
        with self.assertRaisesRegex(ValueError, "case totals"):
            exporter.validate_public_receipt(totals_tampered, expected_digest=None)

        identity_tampered = deepcopy(receipt)
        identity_tampered["runs"][0]["case_results"][0]["attack_class"] = (
            "not-registered"
        )
        identity_tampered["canonical_digest"] = exporter._sha256(
            exporter._canonical(
                {
                    key: value
                    for key, value in identity_tampered.items()
                    if key != "canonical_digest"
                }
            )
        )
        with self.assertRaisesRegex(ValueError, "case identity"):
            exporter.validate_public_receipt(identity_tampered, expected_digest=None)

    def test_public_validation_requires_the_release_digest(self):
        exporter = load_exporter()
        if not exporter.OUTPUT.is_file():
            self.skipTest("tracked public receipt is not present")
        receipt = deepcopy(json.loads(exporter.OUTPUT.read_text(encoding="utf-8")))
        receipt["runs"][0]["label"] = "tampered"
        receipt["canonical_digest"] = exporter._sha256(
            exporter._canonical(
                {
                    key: value
                    for key, value in receipt.items()
                    if key != "canonical_digest"
                }
            )
        )
        with self.assertRaisesRegex(ValueError, "pinned release digest"):
            exporter.validate_public_receipt(receipt)


if __name__ == "__main__":
    unittest.main()
