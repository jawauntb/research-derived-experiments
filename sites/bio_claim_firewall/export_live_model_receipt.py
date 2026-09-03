"""Export a public allowlist-only receipt from ignored live-model summaries."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, NamedTuple, cast

SITE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SITE_ROOT.parents[1]
SUMMARY_ROOT = REPO_ROOT / "bio-claim-firewall/eval/live_claim_trajectories"
CASES_PATH = REPO_ROOT / "bio-claim-firewall/eval/live_claims/cases.json"
OUTPUT = SITE_ROOT / "live_model_receipt.json"
EXPECTED_STUDY_ID = "phase5-live-claim-adversarial"
EXPECTED_MANIFEST_SHA256 = (
    "a1ef4e8313077cf6fad18436da5d561288b283e533a430e1b8d2d2d87dfe1028"
)
# This is intentionally pinned.  Update it only after inspecting a newly
# generated receipt and checking the full serialized artifact into the site.
EXPECTED_PUBLIC_CANONICAL_DIGEST = (
    "2e24e4ae117abfc2357c82ae003ada5f27a9e1000cec5d817b35973c5b26a51e"
)
EXPECTED_SOURCE_IDS = frozenset(
    {
        "cellline.2026_pilot",
        "cellontology.2026_pilot",
        "hgnc.2026_pilot",
        "ncbitaxon.2026_pilot",
        "perturbseq.replogle_2022",
        "reactome.2026_pilot",
    }
)


class RunSpec(NamedTuple):
    stage: str
    label: str
    expected_sha256: str
    expected_prompt_ref: str
    expected_manifest_sha256: str
    expected_case_count: int
    path: Path


RUN_SPECS = (
    RunSpec(
        stage="baseline",
        label="Original parser",
        expected_sha256=(
            "5507040f61315a5639934e7ba32348c20a67cca1d98636a953b4b9f1bb194f66"
        ),
        expected_prompt_ref="claim_parser/k562_gene_effect@v1",
        expected_manifest_sha256=(
            "1d48433958df5685e41d408c6b0f25674df92f6379e509b3ade673bb14fa74c2"
        ),
        expected_case_count=12,
        path=SUMMARY_ROOT / "2026-09-02-openai-v1-baseline.summary.json",
    ),
    RunSpec(
        stage="prompt_only",
        label="Hardened prompt",
        expected_sha256=(
            "cc93645617fa9ce262d4714360333c665dbc8a9bc346de77c836c3f35396cf9e"
        ),
        expected_prompt_ref="claim_parser/k562_gene_effect@v2",
        expected_manifest_sha256=(
            "1d48433958df5685e41d408c6b0f25674df92f6379e509b3ade673bb14fa74c2"
        ),
        expected_case_count=12,
        path=SUMMARY_ROOT / "2026-09-02-openai-v2-confirmation.summary.json",
    ),
    RunSpec(
        stage="final_boundary",
        label="Prompt + positive grammar boundary",
        expected_sha256=(
            "12f8ea662ea4b86c9ff89cbe97b571c3a2319722315cb51dffdf5d0fb4160444"
        ),
        expected_prompt_ref="claim_parser/k562_gene_effect@v2",
        expected_manifest_sha256=EXPECTED_MANIFEST_SHA256,
        expected_case_count=16,
        path=(
            SUMMARY_ROOT
            / "2026-09-03-openai-v2-positive-grammar-confirmation.summary.json"
        ),
    ),
)
PUBLIC_TOP_LEVEL_FIELDS = {"schema_version", "experiment", "runs", "canonical_digest"}
PUBLIC_EXPERIMENT_FIELDS = {
    "study_id",
    "title",
    "provider",
    "model",
    "evidence_world",
    "scope",
    "boundary",
    "frozen",
    "live_endpoint",
    "manifest_sha256",
    "checker_version",
    "case_count",
    "repetitions",
    "total_repetitions",
    "source_hashes",
}
PUBLIC_RUN_FIELDS = {
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
}
PUBLIC_USAGE_FIELDS = {
    "total_calls",
    "successful_calls",
    "errors",
    "total_tokens",
    "total_latency_ms",
}
PUBLIC_CASE_FIELDS = {
    "case_id",
    "attack_class",
    "safe_repetitions",
    "total_repetitions",
}


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def _serialized(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _require_dict(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be an object")
    return cast(dict[str, Any], value)


def _require_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _require_sha256(value: object, label: str) -> str:
    text = _require_text(value, label)
    if len(text) != 64 or any(
        character not in "0123456789abcdef" for character in text
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return text


def _expected_case_identities(case_count: int) -> tuple[tuple[str, str], ...]:
    """Return the exact preregistered case identity set for the public proof."""
    raw = CASES_PATH.read_bytes()
    if _sha256(raw) != EXPECTED_MANIFEST_SHA256:
        raise ValueError("live case manifest digest is not the preregistered digest")
    cases = _require_dict(json.loads(raw), "cases")
    if cases.get("study_id") != EXPECTED_STUDY_ID or cases.get("repetitions") != 3:
        raise ValueError("live case manifest is not the expected study contract")
    raw_cases = cases.get("cases")
    if not isinstance(raw_cases, list) or len(raw_cases) != 16:
        raise ValueError("live case manifest must contain exactly sixteen cases")
    identities = []
    for index, item in enumerate(raw_cases):
        case = _require_dict(item, f"cases[{index}]")
        identities.append(
            (
                _require_text(case.get("case_id"), f"cases[{index}].case_id"),
                _require_text(case.get("attack_class"), f"cases[{index}].attack_class"),
            )
        )
    if len(set(identities)) != len(identities):
        raise ValueError("live case manifest contains duplicate identities")
    if case_count not in {12, 16}:
        raise ValueError("public run case count is not a registered matrix size")
    return tuple(identities[:case_count])


def sanitize_run(
    raw: dict[str, Any],
    spec: RunSpec,
    raw_bytes: bytes,
    *,
    strict_contract: bool = False,
) -> dict[str, Any]:
    """Construct one public run using only explicitly selected scalar fields."""
    summary_sha256 = _sha256(raw_bytes)
    if summary_sha256 != spec.expected_sha256:
        raise ValueError(f"summary digest mismatch for {spec.stage}")

    manifest = _require_dict(raw.get("manifest"), "manifest")
    approved_manifest = _require_sha256(
        manifest.get("approved_sha256"), "manifest.approved_sha256"
    )
    if (
        approved_manifest != spec.expected_manifest_sha256
        or manifest.get("loaded_sha256") != approved_manifest
    ):
        raise ValueError(f"manifest identity mismatch for {spec.stage}")
    case_count = _require_int(raw.get("case_count"), "case_count")
    repetitions = _require_int(raw.get("repetitions"), "repetitions")

    total_repetitions = _require_int(raw.get("total_repetitions"), "total_repetitions")
    safe_repetitions = _require_int(raw.get("safe_repetitions"), "safe_repetitions")
    if safe_repetitions > total_repetitions:
        raise ValueError("safe_repetitions cannot exceed total_repetitions")
    status = _require_text(raw.get("status"), "status")
    expected_status = "passed" if safe_repetitions == total_repetitions else "failed"
    if status != expected_status:
        raise ValueError(f"status disagrees with repetition totals for {spec.stage}")

    results = raw.get("results")
    if not isinstance(results, list) or len(results) != total_repetitions:
        raise ValueError(f"results do not match repetition total for {spec.stage}")
    grouped: dict[tuple[str, str], list[bool]] = defaultdict(list)
    parser_identities: set[tuple[str, str]] = set()
    prompt_refs: set[str] = set()
    for item in results:
        result = _require_dict(item, "result")
        case_id = _require_text(result.get("case_id"), "result.case_id")
        attack_class = _require_text(result.get("attack_class"), "result.attack_class")
        safe = result.get("safe")
        if not isinstance(safe, bool):
            raise TypeError("result.safe must be a boolean")
        grouped[(case_id, attack_class)].append(safe)
        parser = result.get("parser")
        if parser is not None:
            parser_data = _require_dict(parser, "result.parser")
            parser_identities.add(
                (
                    _require_text(parser_data.get("provider"), "parser.provider"),
                    _require_text(parser_data.get("model"), "parser.model"),
                )
            )
            prompt_refs.add(
                _require_text(parser_data.get("prompt_ref"), "parser.prompt_ref")
            )

    if len(parser_identities) != 1:
        raise ValueError(f"parser identity is not unique for {spec.stage}")
    if prompt_refs != {spec.expected_prompt_ref}:
        raise ValueError(
            f"prompt identity is not the expected version for {spec.stage}"
        )
    provider, model = next(iter(parser_identities))

    if strict_contract:
        expected_identities = set(_expected_case_identities(spec.expected_case_count))
        expected_total = spec.expected_case_count * 3
        if (
            case_count != spec.expected_case_count
            or repetitions != 3
            or total_repetitions != expected_total
        ):
            raise ValueError(f"{spec.stage} has the wrong preregistered shape")
        if set(grouped) != expected_identities:
            raise ValueError(
                f"case identities do not match the preregistered matrix for {spec.stage}"
            )
        if any(len(values) != 3 for values in grouped.values()):
            raise ValueError(
                f"each case must have exactly three repetitions for {spec.stage}"
            )

    case_results = []
    for (case_id, attack_class), values in sorted(grouped.items()):
        case_results.append(
            {
                "case_id": case_id,
                "attack_class": attack_class,
                "safe_repetitions": sum(values),
                "total_repetitions": len(values),
            }
        )

    parser_stats = _require_dict(
        _require_dict(raw.get("model_stats"), "model_stats").get("claim_parser"),
        "model_stats.claim_parser",
    )
    latency = parser_stats.get("total_latency_ms")
    if (
        isinstance(latency, bool)
        or not isinstance(latency, (int, float))
        or latency < 0
    ):
        raise ValueError(
            "model_stats.claim_parser.total_latency_ms must be non-negative"
        )

    total_calls = _require_int(parser_stats.get("total_calls"), "total_calls")
    successful_calls = _require_int(
        parser_stats.get("successful_calls"), "successful_calls"
    )
    errors = _require_int(parser_stats.get("errors"), "errors")
    if successful_calls + errors != total_calls:
        raise ValueError("model usage calls must equal successes plus errors")
    if total_calls > total_repetitions:
        raise ValueError("model usage cannot exceed repetition total")
    if successful_calls > total_calls or errors > total_calls:
        raise ValueError("model usage counts are inconsistent")

    return {
        "stage": spec.stage,
        "label": spec.label,
        "provider": provider,
        "model": model,
        "prompt_ref": spec.expected_prompt_ref,
        "status": status,
        "executed_at": _require_text(raw.get("executed_at"), "executed_at"),
        "safe_repetitions": safe_repetitions,
        "total_repetitions": total_repetitions,
        "summary_sha256": summary_sha256,
        "manifest_sha256": approved_manifest,
        "case_count": case_count,
        "repetitions": repetitions,
        "model_config_sha256": _require_sha256(
            raw.get("model_config_sha256"), "model_config_sha256"
        ),
        "model_usage": {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "errors": errors,
            "total_tokens": _require_int(
                parser_stats.get("total_tokens"), "total_tokens"
            ),
            # JavaScript's JSON representation is integral here; normalize
            # the Python float so the receipt has one cross-runtime value.
            "total_latency_ms": round(float(latency)),
        },
        "case_results": case_results,
    }


def _load_summary(spec: RunSpec) -> tuple[dict[str, Any], bytes]:
    raw_bytes = spec.path.read_bytes()
    value = json.loads(raw_bytes)
    return _require_dict(value, f"summary {spec.stage}"), raw_bytes


def build_receipt(run_specs: tuple[RunSpec, ...] = RUN_SPECS) -> dict[str, Any]:
    raw_runs = [_load_summary(spec) for spec in run_specs]
    first = raw_runs[0][0]
    if _require_text(first.get("study_id"), "study_id") != EXPECTED_STUDY_ID:
        raise ValueError("unexpected live-claim study")

    source_hashes = _require_dict(first.get("source_hashes"), "source_hashes")
    public_source_hashes = {
        _require_text(source, "source id"): _require_sha256(digest, "source digest")
        for source, digest in sorted(source_hashes.items())
    }
    checker_version = _require_text(first.get("checker_version"), "checker_version")

    for raw, _ in raw_runs[1:]:
        if (
            raw.get("source_hashes") != source_hashes
            or raw.get("checker_version") != checker_version
            or raw.get("study_id") != EXPECTED_STUDY_ID
        ):
            raise ValueError("live runs do not share one evidence and checker contract")

    runs = [
        sanitize_run(raw, spec, raw_bytes, strict_contract=True)
        for spec, (raw, raw_bytes) in zip(run_specs, raw_runs, strict=True)
    ]
    providers = {run["provider"] for run in runs}
    models = {run["model"] for run in runs}
    if len(providers) != 1 or len(models) != 1:
        raise ValueError("live runs do not share one model provider and identity")
    final = runs[-1]
    receipt: dict[str, Any] = {
        "schema_version": "live-model-receipt-v1",
        "experiment": {
            "study_id": EXPECTED_STUDY_ID,
            "title": "Frozen K562 adversarial claim-parser experiment",
            "provider": next(iter(providers)),
            "model": next(iter(models)),
            "evidence_world": "Replogle 2022 K562 Perturb-seq",
            "scope": (
                "Sixteen preregistered K562 claim and injection cases, repeated three "
                "times against one frozen evidence snapshot."
            ),
            "boundary": (
                "Recorded offline experiment with a reviewed positive K562 claim grammar "
                "and parser-to-input binding; this site exposes no live model endpoint."
            ),
            "frozen": True,
            "live_endpoint": False,
            "manifest_sha256": final["manifest_sha256"],
            "checker_version": checker_version,
            "case_count": final["case_count"],
            "repetitions": final["repetitions"],
            "total_repetitions": final["total_repetitions"],
            "source_hashes": public_source_hashes,
        },
        "runs": runs,
    }
    receipt["canonical_digest"] = _sha256(_canonical(receipt))
    return receipt


def validate_public_receipt(
    receipt: dict[str, Any],
    *,
    expected_digest: str | None = EXPECTED_PUBLIC_CANONICAL_DIGEST,
) -> None:
    """Validate the tracked artifact without requiring private run files."""
    if set(receipt) != PUBLIC_TOP_LEVEL_FIELDS:
        raise ValueError("public receipt has unexpected top-level fields")
    digest = _require_sha256(receipt.get("canonical_digest"), "canonical_digest")
    payload = dict(receipt)
    del payload["canonical_digest"]
    if _sha256(_canonical(payload)) != digest:
        raise ValueError("public receipt canonical digest mismatch")
    if expected_digest is not None and digest != expected_digest:
        raise ValueError(
            "public receipt canonical digest is not the pinned release digest"
        )

    experiment = _require_dict(receipt.get("experiment"), "experiment")
    if set(experiment) != PUBLIC_EXPERIMENT_FIELDS:
        raise ValueError("public experiment has unexpected fields")
    if (
        experiment.get("frozen") is not True
        or experiment.get("live_endpoint") is not False
    ):
        raise ValueError("public experiment boundary is not frozen and offline")
    _require_text(experiment.get("provider"), "experiment.provider")
    _require_text(experiment.get("model"), "experiment.model")
    _require_text(experiment.get("checker_version"), "experiment.checker_version")
    source_hashes = _require_dict(
        experiment.get("source_hashes"), "experiment.source_hashes"
    )
    if set(source_hashes) != EXPECTED_SOURCE_IDS:
        raise ValueError("public source identity set is not the pinned pilot world")
    for source, digest_value in source_hashes.items():
        _require_text(source, "experiment.source id")
        _require_sha256(digest_value, f"experiment.source_hashes[{source}]")
    experiment_case_count = _require_int(
        experiment.get("case_count"), "experiment.case_count"
    )
    experiment_repetitions = _require_int(
        experiment.get("repetitions"), "experiment.repetitions"
    )
    experiment_total = _require_int(
        experiment.get("total_repetitions"), "experiment.total_repetitions"
    )
    if (
        experiment.get("study_id") != EXPECTED_STUDY_ID
        or experiment.get("manifest_sha256") != EXPECTED_MANIFEST_SHA256
        or (experiment_case_count, experiment_repetitions, experiment_total)
        != (16, 3, 48)
    ):
        raise ValueError("public experiment shape or identity is not pinned")
    runs = receipt.get("runs")
    if not isinstance(runs, list) or len(runs) != len(RUN_SPECS):
        raise ValueError("public receipt must contain the three pinned runs")
    for run, spec in zip(runs, RUN_SPECS, strict=True):
        run_data = _require_dict(run, "run")
        if set(run_data) != PUBLIC_RUN_FIELDS:
            raise ValueError("public run has unexpected fields")
        if (
            run_data.get("stage") != spec.stage
            or run_data.get("label") != spec.label
            or run_data.get("summary_sha256") != spec.expected_sha256
            or run_data.get("prompt_ref") != spec.expected_prompt_ref
            or run_data.get("manifest_sha256") != spec.expected_manifest_sha256
            or run_data.get("case_count") != spec.expected_case_count
            or run_data.get("repetitions") != 3
            or run_data.get("provider") != experiment.get("provider")
            or run_data.get("model") != experiment.get("model")
        ):
            raise ValueError(f"public run identity mismatch for {spec.stage}")
        _require_text(run_data.get("executed_at"), "run.executed_at")
        _require_sha256(run_data.get("summary_sha256"), "run.summary_sha256")
        _require_sha256(run_data.get("model_config_sha256"), "run.model_config_sha256")
        usage = _require_dict(run_data.get("model_usage"), "run.model_usage")
        if set(usage) != PUBLIC_USAGE_FIELDS:
            raise ValueError("public model usage has unexpected fields")
        total = _require_int(run_data.get("total_repetitions"), "run.total_repetitions")
        safe = _require_int(run_data.get("safe_repetitions"), "run.safe_repetitions")
        expected_total = spec.expected_case_count * 3
        if total != expected_total or safe > total:
            raise ValueError(f"public run totals are invalid for {spec.stage}")
        expected_status = "passed" if safe == total else "failed"
        if run_data.get("status") != expected_status:
            raise ValueError(
                f"public run status disagrees with totals for {spec.stage}"
            )
        total_calls = _require_int(usage.get("total_calls"), "usage.total_calls")
        successful_calls = _require_int(
            usage.get("successful_calls"), "usage.successful_calls"
        )
        errors = _require_int(usage.get("errors"), "usage.errors")
        _require_int(usage.get("total_tokens"), "usage.total_tokens")
        _require_int(usage.get("total_latency_ms"), "usage.total_latency_ms")
        if successful_calls + errors != total_calls:
            raise ValueError(
                f"public model usage counts are inconsistent for {spec.stage}"
            )
        if (
            total_calls > total
            or successful_calls > total_calls
            or errors > total_calls
        ):
            raise ValueError(f"public model usage exceeds repetitions for {spec.stage}")
        expected_identities = set(_expected_case_identities(spec.expected_case_count))
        cases = run_data.get("case_results")
        if not isinstance(cases, list) or len(cases) != len(expected_identities):
            raise ValueError("public case_results must contain every registered case")
        observed: set[tuple[str, str]] = set()
        case_safe_total = 0
        case_repetition_total = 0
        for case in cases:
            case_data = _require_dict(case, "case result")
            if set(case_data) != PUBLIC_CASE_FIELDS:
                raise ValueError("public case result has unexpected fields")
            identity = (
                _require_text(case_data.get("case_id"), "case.case_id"),
                _require_text(case_data.get("attack_class"), "case.attack_class"),
            )
            if identity in observed or identity not in expected_identities:
                raise ValueError(
                    "public case identity is not the preregistered identity"
                )
            observed.add(identity)
            case_safe = _require_int(
                case_data.get("safe_repetitions"), "case.safe_repetitions"
            )
            case_total = _require_int(
                case_data.get("total_repetitions"), "case.total_repetitions"
            )
            if case_total != 3 or case_safe > case_total:
                raise ValueError("public case totals are invalid")
            case_safe_total += case_safe
            case_repetition_total += case_total
        if observed != expected_identities:
            raise ValueError("public case identities are incomplete")
        if case_safe_total != safe or case_repetition_total != total:
            raise ValueError(
                f"public case totals do not sum to run totals for {spec.stage}"
            )

    if [run["safe_repetitions"] for run in runs] != [9, 33, 48]:
        raise ValueError("public receipt does not preserve the recorded progression")

    serialized = _serialized(receipt).lower()
    for forbidden in (
        "openai_api_key",
        '"api_key"',
        '"environment"',
        "raw_provider_response",
        "/users/",
        "/private/",
    ):
        if forbidden in serialized:
            raise ValueError(
                "public receipt contains a forbidden private field or path"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the tracked public receipt is stale",
    )
    args = parser.parse_args()
    if args.check:
        present = [spec.path.is_file() for spec in RUN_SPECS]
        if any(present) and not all(present):
            raise SystemExit("private live-model summaries are incomplete")
        if all(present):
            expected = _serialized(build_receipt())
            if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != expected:
                raise SystemExit("public live-model receipt is stale")
            tracked = _require_dict(
                json.loads(OUTPUT.read_text(encoding="utf-8")), "public receipt"
            )
            validate_public_receipt(tracked)
        else:
            if not OUTPUT.is_file():
                raise SystemExit("public live-model receipt is missing")
            tracked = _require_dict(
                json.loads(OUTPUT.read_text(encoding="utf-8")), "public receipt"
            )
            validate_public_receipt(tracked)
        return 0
    receipt = build_receipt()
    # Generation is the one deliberate exception to the release pin: the
    # printed digest must be reviewed and then promoted into the constant
    # above before --check can accept the new artifact.
    validate_public_receipt(receipt, expected_digest=None)
    content = _serialized(receipt)
    OUTPUT.write_text(content, encoding="utf-8")
    print(
        json.dumps(
            {
                "canonical_digest": receipt["canonical_digest"],
                "run_count": len(receipt["runs"]),
                "safe_progression": [
                    run["safe_repetitions"] for run in receipt["runs"]
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
