"""Deterministic, preregistered pilot-readiness evaluation.

The evaluator consumes a locked control corpus whose claims and source hashes
were frozen independently of the evaluated fixtures. It then binds each
adapter to the immutable :mod:`worlds.registry` contract. A fixture and its
manifest therefore cannot drift together and manufacture a passing result.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from worlds import WORLD_REGISTRY
from worlds.arc_vcc import ArcVCCAdapter, check_arc_vcc_claim
from worlds.arc_vcc import load_fixture as load_arc
from worlds.clinical_trials import ClinicalTrialsAdapter, check_clinical_trials_claim
from worlds.open_targets import OpenTargetsAdapter, check_open_targets_claim

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "worlds"
MANIFEST_ROOT = REPO_ROOT / "data" / "manifests" / "worlds"
PREREGISTRATION_ROOT = Path(__file__).resolve().parents[1] / "preregistration"
CONTROL_CORPUS_PATH = PREREGISTRATION_ROOT / "pilot_control_corpus.json"
SOURCE_TERMS_REVIEW_PATH = PREREGISTRATION_ROOT / "source-terms-review.json"
CLINICAL_REVIEW_PATH = PREREGISTRATION_ROOT / "clinical-trials-sec-review.json"
REGISTRY_PATH = REPO_ROOT / "src" / "worlds" / "registry.py"
WORLD_IDS = ("clinical-trials-sec", "open-targets", "arc-vcc")
REQUIRED_CONTROL_KINDS = frozenset(
    {"positive", "negative", "null", "corruption", "cross_world"}
)
DEFERRED_WORLDS = {
    "neurovault": "Deferred: no committed licensed evidence fixture or adapter.",
    "flywire-codex": "Deferred: no committed licensed evidence fixture or adapter.",
}
REQUIRED_SOURCE_TERMS_MAX_AGE_DAYS = 90
REQUIRED_CLINICAL_REVIEW_MAX_AGE_DAYS = 90


@dataclass(frozen=True)
class ControlResult:
    """One locked mutation and its observed adapter behavior."""

    control_id: str
    kind: str
    expected: tuple[str, ...]
    expected_reason_codes: tuple[str, ...]
    observed: str
    passed: bool
    reason_code: str
    message: str


@dataclass(frozen=True)
class GateEvidence:
    """One fatal gate with an auditable, non-compensable status."""

    gate_id: str
    status: str
    evidence: str


@dataclass(frozen=True)
class ReviewPolicy:
    """Locked evaluation clock and maximum ages for operator reviews."""

    evaluation_as_of: datetime
    source_terms_max_age_days: int
    clinical_relationship_max_age_days: int


@dataclass(frozen=True)
class SourceTermsReview:
    """Parsed source-terms review plus its independently locked timestamp."""

    reviewed_at: datetime
    rows: Mapping[tuple[str, str, str], Mapping[str, Any]]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_sha256(path: Path) -> str:
    """Hash file names and bytes so a multi-file fixture has one receipt."""

    if path.is_file():
        return _sha256(path)
    digest = hashlib.sha256()
    for item in sorted(
        candidate for candidate in path.rglob("*") if candidate.is_file()
    ):
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return value


def _load_protocol(path: Path = CONTROL_CORPUS_PATH) -> dict[str, dict[str, Any]]:
    corpus = _json(path)
    raw_worlds = corpus.get("worlds")
    if not isinstance(raw_worlds, list) or not raw_worlds:
        raise ValueError("locked control corpus must contain a non-empty worlds list")
    protocols: dict[str, dict[str, Any]] = {}
    for raw in raw_worlds:
        if not isinstance(raw, dict) or not isinstance(raw.get("world_id"), str):
            raise TypeError("each locked protocol must have a world_id")
        world_id = raw["world_id"]
        if world_id in protocols:
            raise ValueError(f"duplicate locked protocol for {world_id}")
        gate_ids = raw.get("fatal_gate_ids")
        controls = raw.get("controls")
        if (
            not isinstance(gate_ids, list)
            or not gate_ids
            or len(gate_ids) != len(set(gate_ids))
        ):
            raise ValueError(
                f"{world_id} requires a non-empty, duplicate-free fatal gate set"
            )
        if not isinstance(controls, list) or not controls:
            raise ValueError(f"{world_id} requires a non-empty control set")
        control_ids = [
            item.get("control_id") for item in controls if isinstance(item, Mapping)
        ]
        control_kinds = [
            item.get("kind") for item in controls if isinstance(item, Mapping)
        ]
        if len(control_ids) != len(controls) or any(
            not isinstance(item, str) or not item for item in control_ids
        ):
            raise ValueError(f"{world_id} has a malformed control id")
        if len(control_ids) != len(set(control_ids)):
            raise ValueError(f"{world_id} has duplicate control ids")
        if set(control_kinds) != REQUIRED_CONTROL_KINDS or len(control_kinds) != len(
            REQUIRED_CONTROL_KINDS
        ):
            raise ValueError(
                f"{world_id} must preregister exactly one control of every required kind"
            )
        for control in controls:
            if not isinstance(control.get("claim"), dict) or not control["claim"]:
                raise ValueError(
                    f"{world_id}/{control.get('control_id')} must freeze a non-empty claim"
                )
            expected = control.get("expected")
            if (
                not isinstance(expected, list)
                or not expected
                or any(not isinstance(item, str) for item in expected)
            ):
                raise ValueError(
                    f"{world_id}/{control.get('control_id')} must freeze expected outcomes"
                )
            expected_reason_codes = control.get("expected_reason_codes", [])
            if not isinstance(expected_reason_codes, list) or any(
                not isinstance(item, str) or not item for item in expected_reason_codes
            ):
                raise ValueError(
                    f"{world_id}/{control.get('control_id')} has malformed expected reason codes"
                )
        source_hashes = raw.get("registered_source_hashes")
        if not isinstance(source_hashes, dict) or not source_hashes:
            raise ValueError(f"{world_id} must freeze registered source hashes")
        protocols[world_id] = raw
    if set(protocols) != set(WORLD_IDS):
        raise ValueError(
            "locked control corpus must contain exactly the three pilot worlds"
        )
    return protocols


def _load_review_policy(path: Path = CONTROL_CORPUS_PATH) -> ReviewPolicy:
    corpus = _json(path)
    raw = corpus.get("review_freshness")
    if not isinstance(raw, Mapping):
        raise ValueError("locked control corpus must preregister review freshness")
    evaluation_as_of = _parse_utc(raw.get("evaluation_as_of"))
    source_max_age = raw.get("source_terms_max_age_days")
    clinical_max_age = raw.get("clinical_relationship_max_age_days")
    if (
        source_max_age != REQUIRED_SOURCE_TERMS_MAX_AGE_DAYS
        or clinical_max_age != REQUIRED_CLINICAL_REVIEW_MAX_AGE_DAYS
    ):
        raise ValueError("review freshness maximum ages differ from evaluator policy")
    return ReviewPolicy(evaluation_as_of, source_max_age, clinical_max_age)


def _outcome(result: Any) -> tuple[str, str, str]:
    observed = str(
        getattr(result, "outcome", getattr(result, "verdict", "CHECKER_ERROR"))
    )
    reason_code = str(getattr(result, "reason_code", ""))
    message = str(getattr(result, "reason", ""))
    if not reason_code:
        winning = getattr(result, "winning_rule", None)
        reason_code = str(winning.get("id", "")) if isinstance(winning, Mapping) else ""
    return observed, reason_code, message


def _control(spec: Mapping[str, Any], result: Any) -> ControlResult:
    observed, reason_code, message = _outcome(result)
    expected = tuple(str(item) for item in spec["expected"])
    expected_reason_codes = tuple(
        str(item) for item in spec.get("expected_reason_codes", [])
    )
    reason_passed = not expected_reason_codes or reason_code in expected_reason_codes
    return ControlResult(
        str(spec["control_id"]),
        str(spec["kind"]),
        expected,
        expected_reason_codes,
        observed,
        observed in expected and reason_passed,
        reason_code,
        message,
    )


def _copy_arc(destination: Path, *, fixture_root: Path) -> None:
    source = fixture_root / "arc_vcc"
    destination.mkdir()
    for name in ("metadata.json", "measurements.jsonl"):
        shutil.copy2(source / name, destination / name)


def _registered_source_hashes(world_id: str, version: str) -> dict[str, str]:
    world = WORLD_REGISTRY.resolve(world_id, version)
    values = {contract.source: contract.sha256 for contract in world.source_contracts}
    if any(value is None for value in values.values()):
        raise ValueError(
            f"registered pilot world {world_id} has an unhashed source contract"
        )
    return {key: str(value) for key, value in values.items()}


def _parse_utc(value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamp must be an RFC3339 UTC string ending in Z")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError("timestamp must resolve to UTC")
    return parsed


def _load_source_terms_review(path: Path) -> SourceTermsReview:
    review = _json(path)
    if review.get("schema_version") != "bio-claim-firewall-source-terms-review-0.1":
        raise ValueError("source-terms review has an unsupported schema")
    if review.get("reviewer_role") != "agent_operator_under_human_direction":
        raise ValueError("source-terms review must identify its operator role exactly")
    for field in ("reviewed_at", "review_method", "scope_exclusion"):
        if not isinstance(review.get(field), str) or not review[field].strip():
            raise ValueError(f"source-terms review is missing {field}")
    reviewed_at = _parse_utc(review["reviewed_at"])
    if "not legal advice" not in review["scope_exclusion"].casefold():
        raise ValueError("source-terms review must preserve its legal-advice exclusion")
    rows = review.get("sources")
    if not isinstance(rows, list) or not rows:
        raise ValueError("source-terms review must contain reviewed sources")
    indexed: dict[tuple[str, str, str], dict[str, Any]] = {}
    for raw in rows:
        if not isinstance(raw, dict):
            raise TypeError("source-terms review rows must be objects")
        key = (
            str(raw.get("world_id", "")),
            str(raw.get("world_version", "")),
            str(raw.get("source_id", "")),
        )
        if not all(key) or key in indexed:
            raise ValueError(
                "source-terms review has a missing or duplicate source key"
            )
        if raw.get("review_status") != "operator_terms_reviewed":
            raise ValueError("source-terms review row is not operator-reviewed")
        for field in (
            "license_id",
            "official_url",
            "terms_reference_url",
            "bounded_demo_obligation",
        ):
            if not isinstance(raw.get(field), str) or not raw[field].strip():
                raise ValueError(f"source-terms review row is missing {field}")
        if not raw["official_url"].startswith("https://") or not raw[
            "terms_reference_url"
        ].startswith("https://"):
            raise ValueError("source-terms review URLs must be HTTPS")
        indexed[key] = raw
    expected_keys = {
        (world_id, world.version, contract.source)
        for world_id in WORLD_IDS
        for world in (WORLD_REGISTRY.resolve(world_id, _pilot_version(world_id)),)
        for contract in world.source_contracts
        if contract.license != "internal-derived"
    }
    if set(indexed) != expected_keys:
        raise ValueError(
            "source-terms review must contain exactly the public pilot source contracts"
        )
    return SourceTermsReview(reviewed_at, indexed)


def _pilot_version(world_id: str) -> str:
    versions = [
        world.version for world in WORLD_REGISTRY.worlds if world.world_id == world_id
    ]
    if len(versions) != 1:
        raise ValueError(
            f"pilot world {world_id} must have exactly one registered version"
        )
    return versions[0]


def _license_binding_ok(
    manifest: Mapping[str, Any],
    *,
    world_id: str,
    version: str,
    source_terms_review: SourceTermsReview,
    review_policy: ReviewPolicy,
) -> bool:
    world = WORLD_REGISTRY.resolve(world_id, version)
    registered = {
        contract.source: contract.license
        for contract in world.source_contracts
        if contract.license != "internal-derived"
    }
    source_rows = manifest.get("sources")
    if not isinstance(source_rows, list) or not source_rows:
        return False
    rows = {
        str(item.get("source_id")): item
        for item in source_rows
        if isinstance(item, Mapping) and item.get("source_id")
    }
    reviewed_ids = {
        source_id
        for review_world, review_version, source_id in source_terms_review.rows
        if review_world == world_id and review_version == version
    }
    if set(rows) != set(registered) or reviewed_ids != set(registered):
        return False
    for source_id, license_id in registered.items():
        manifest_row = rows[source_id]
        manifest_license = manifest_row.get("license")
        review_row = source_terms_review.rows.get((world_id, version, source_id))
        contract = next(
            item for item in world.source_contracts if item.source == source_id
        )
        if not isinstance(manifest_license, Mapping) or review_row is None:
            return False
        if (
            license_id is None
            or manifest_license.get("id") != license_id
            or manifest_license.get("status") != "verified"
            or manifest_license.get("redistribution") in {"forbidden", "unknown", None}
            or review_row.get("license_id") != license_id
            or contract.official_url is None
            or contract.terms_reference_url is None
            or manifest_row.get("official_url") != contract.official_url
            or manifest_license.get("reference_url") != contract.terms_reference_url
            or review_row.get("official_url") != manifest_row.get("official_url")
            or review_row.get("terms_reference_url")
            != manifest_license.get("reference_url")
        ):
            return False
    return _review_is_fresh(
        source_terms_review.reviewed_at,
        manifest,
        evaluation_as_of=review_policy.evaluation_as_of,
        max_age_days=review_policy.source_terms_max_age_days,
    )


def _review_is_fresh(
    reviewed_at: datetime,
    manifest: Mapping[str, Any],
    *,
    evaluation_as_of: datetime,
    max_age_days: int,
) -> bool:
    data_clock = manifest.get("data_clock")
    if not isinstance(data_clock, Mapping):
        return False
    try:
        retrieval_at = _parse_utc(data_clock.get("retrieval_at"))
    except ValueError:
        return False
    age = evaluation_as_of - reviewed_at
    return retrieval_at <= reviewed_at <= evaluation_as_of and timedelta(
        0
    ) <= age <= timedelta(days=max_age_days)


def _clinical_review_binding_ok(
    fixture: Mapping[str, Any],
    review_path: Path,
    manifest: Mapping[str, Any],
    review_policy: ReviewPolicy,
) -> bool:
    review = _json(review_path)
    actual_review_hash = _sha256(review_path)
    if (
        review.get("schema_version") != "clinical-trials-sec-review-0.1"
        or review.get("world_id") != "clinical-trials-sec"
        or review.get("world_version") != "2025-09-01_2026-09-01"
        or review.get("reviewer_role") != "agent_operator_under_human_direction"
        or review.get("relationship_confirmed") is not True
    ):
        return False
    for field in ("reviewed_at", "review_method", "scope_exclusion"):
        if not isinstance(review.get(field), str) or not review[field].strip():
            return False
    if "does not establish efficacy" not in review["scope_exclusion"].casefold():
        return False
    try:
        reviewed_at = _parse_utc(review["reviewed_at"])
    except ValueError:
        return False
    records = fixture.get("records")
    if not isinstance(records, list):
        return False
    sec_rows = [
        row
        for row in records
        if isinstance(row, Mapping)
        and row.get("source") == "sec-edgar-submissions-and-archives"
    ]
    if len(sec_rows) != 1:
        return False
    sec_row = sec_rows[0]
    source_hashes = fixture.get("source_hashes")
    if not isinstance(source_hashes, Mapping):
        return False
    return (
        _review_is_fresh(
            reviewed_at,
            manifest,
            evaluation_as_of=review_policy.evaluation_as_of,
            max_age_days=review_policy.clinical_relationship_max_age_days,
        )
        and sec_row.get("review_artifact_sha256") == actual_review_hash
        and review.get("sec_source_sha256")
        == source_hashes.get("sec-edgar-submissions-and-archives")
        and review.get("reviewer_role") == sec_row.get("reviewer_role")
        and review.get("cik") == sec_row.get("cik")
        and review.get("sec_accession") == sec_row.get("sec_accession")
        and review.get("nct_id") == sec_row.get("nct_id")
        and review.get("sponsor") == sec_row.get("sponsor")
        and review.get("intervention") == sec_row.get("intervention")
        and review.get("exhibit_locator") == sec_row.get("exhibit_locator")
        and review.get("identity_span_locator") == sec_row.get("identity_span_locator")
        and review.get("identity_span_sha256") == sec_row.get("identity_span_sha256")
        and review.get("nct_span_locator") == sec_row.get("span_locator")
        and review.get("nct_span_sha256") == sec_row.get("asserted_span_sha256")
    )


def _artifact_digests(
    world_id: str,
    fixture_path: Path,
    manifest_path: Path,
    *,
    control_corpus_path: Path,
    source_terms_review_path: Path,
    clinical_review_path: Path | None = None,
) -> dict[str, str]:
    artifacts = {
        "registry_sha256": _sha256(REGISTRY_PATH),
        "evaluator_sha256": _sha256(Path(__file__)),
        "manifest_sha256": _sha256(manifest_path),
        "fixture_corpus_sha256": _tree_sha256(fixture_path),
        "preregistration_sha256": _sha256(PREREGISTRATION_ROOT / f"{world_id}.yaml"),
        "control_corpus_sha256": _sha256(control_corpus_path),
        "source_terms_review_sha256": _sha256(source_terms_review_path),
    }
    if clinical_review_path is not None:
        artifacts["clinical_review_sha256"] = _sha256(clinical_review_path)
    return artifacts


def _run_arc_controls(
    protocol: Mapping[str, Any],
    adapter: ArcVCCAdapter,
    *,
    fixture_root: Path,
) -> list[ControlResult]:
    results: list[ControlResult] = []
    for spec in protocol["controls"]:
        if spec["kind"] != "corruption":
            result = adapter.check(spec["claim"])
        else:
            mutation = spec["mutation"]
            with tempfile.TemporaryDirectory(prefix="bcf-arc-corrupt-") as temp:
                corrupt = Path(temp) / "arc_vcc"
                _copy_arc(corrupt, fixture_root=fixture_root)
                target = corrupt / str(mutation["file"])
                content = target.read_text(encoding="utf-8")
                changed = content.replace(
                    str(mutation["find"]), str(mutation["replace"]), 1
                )
                if changed == content:
                    raise ValueError(
                        "locked Arc corruption mutation did not change fixture bytes"
                    )
                target.write_text(changed, encoding="utf-8")
                result = check_arc_vcc_claim(corrupt, spec["claim"])
        results.append(_control(spec, result))
    return results


def _run_json_controls(
    protocol: Mapping[str, Any],
    adapter: Any,
    fixture_path: Path,
    checker: Any,
) -> list[ControlResult]:
    fixture = _json(fixture_path)
    results: list[ControlResult] = []
    for spec in protocol["controls"]:
        if spec["kind"] != "corruption":
            result = adapter.check(spec["claim"])
        else:
            mutation = spec["mutation"]
            changed = json.loads(json.dumps(fixture))
            record = changed["records"][int(mutation["record_index"])]
            if "delta" in mutation:
                field = str(mutation["field"])
                record[field] = float(record[field]) + float(mutation["delta"])
            else:
                record[str(mutation["field"])] = mutation["value"]
            with tempfile.TemporaryDirectory(prefix="bcf-json-corrupt-") as temp:
                corrupt = Path(temp) / fixture_path.name
                corrupt.write_text(json.dumps(changed), encoding="utf-8")
                result = checker(spec["claim"], corrupt)
        results.append(_control(spec, result))
    return results


def _manifest_gates(
    manifest: Mapping[str, Any],
    fixture_path: Path,
    source_hashes: Mapping[str, str],
    controls: Sequence[ControlResult],
    *,
    world_id: str,
    version: str,
    expected_gate_ids: Sequence[str],
    preregistered_source_hashes: Mapping[str, str],
    source_terms_review: SourceTermsReview,
    review_policy: ReviewPolicy,
    additional_artifact_binding_ok: bool = True,
    semantic_checks: Mapping[str, bool] | None = None,
) -> list[GateEvidence]:
    """Evaluate the exact locked fatal-gate set without vacuous passes."""

    declared = [
        str(raw.get("id", "")) if isinstance(raw, Mapping) else str(raw)
        for raw in manifest.get("fatal_gates", [])
    ]
    declaration_counts = Counter(declared)
    declaration_exact = (
        bool(declared)
        and len(declared) == len(expected_gate_ids)
        and set(declared) == set(expected_gate_ids)
        and all(count == 1 for count in declaration_counts.values())
    )
    registered_hashes = _registered_source_hashes(world_id, version)
    source_contract_exact = (
        bool(source_hashes)
        and dict(source_hashes) == registered_hashes
        and dict(preregistered_source_hashes) == registered_hashes
    )
    source_rows = manifest.get("sources", [])
    source_ids = {
        str(item.get("source_id"))
        for item in source_rows
        if isinstance(item, Mapping) and item.get("source_id")
    }
    public_registered_sources = {
        contract.source
        for contract in WORLD_REGISTRY.resolve(world_id, version).source_contracts
        if contract.license != "internal-derived"
    }
    identity_ok = (
        manifest.get("state") == "ADMITTED"
        and manifest.get("world_id") == world_id
        and manifest.get("version") == version
        and source_ids == public_registered_sources
        and source_contract_exact
    )
    transformation = manifest.get("transformation", {})
    primary_fixture = (
        fixture_path if fixture_path.is_file() else fixture_path / "measurements.jsonl"
    )
    derived_hash_ok = _sha256(primary_fixture) == transformation.get("sha256")
    hash_ok = derived_hash_ok and source_contract_exact
    license_ok = _license_binding_ok(
        manifest,
        world_id=world_id,
        version=version,
        source_terms_review=source_terms_review,
        review_policy=review_policy,
    )
    controls_exact = (
        bool(controls)
        and len(controls) == len(REQUIRED_CONTROL_KINDS)
        and len({item.control_id for item in controls}) == len(controls)
        and {item.kind for item in controls} == REQUIRED_CONTROL_KINDS
    )
    organic = [
        item for item in controls if item.kind in {"positive", "negative", "null"}
    ]
    organic_ok = (
        controls_exact and len(organic) == 3 and all(item.passed for item in organic)
    )
    isolation = [
        item for item in controls if item.kind in {"corruption", "cross_world"}
    ]
    isolation_ok = (
        controls_exact
        and len(isolation) == 2
        and all(item.passed for item in isolation)
    )
    semantic_checks = semantic_checks or {}
    gates: list[GateEvidence] = []
    for gate_id in expected_gate_ids:
        declaration_ok = declaration_exact and declaration_counts[gate_id] == 1
        if gate_id in {
            "dataset_license_scope",
            "license_and_redistribution",
            "license_and_custody",
        }:
            passed = declaration_ok and license_ok
            evidence = (
                "The manifest license ID, official source URL, and terms URL exactly "
                "match the immutable registry and a scope-limited operator review "
                "that is current for the manifest data clock."
            )
        elif gate_id in {"official_release_identity", "official_source_identity"}:
            passed = declaration_ok and identity_ok
            evidence = (
                "Manifest identity is ADMITTED and adapter hashes equal the immutable "
                "registry and preregistration contracts."
            )
        elif gate_id == "complete_hashes_and_schema":
            passed = declaration_ok and hash_ok and additional_artifact_binding_ok
            evidence = (
                "The derived fixture hash matches the manifest and adapter hashes "
                "exactly match the registered source contract; required review "
                "artifacts are present, hash-bound, and current for the locked "
                "evaluation date."
            )
        elif gate_id in {
            "split_integrity_no_leakage",
            "timestamp_cutoff_no_time_travel",
            "release_and_score_semantics",
        }:
            passed = declaration_ok and hash_ok and bool(semantic_checks.get(gate_id))
            evidence = (
                "The hash-bound fixture satisfies the preregistered world-specific "
                "semantic constraint."
            )
        elif gate_id == "organic_positive_negative_null_controls":
            passed = declaration_ok and organic_ok
            evidence = (
                "Exactly one locked positive, negative, and null control ran and "
                "matched its preregistered outcome."
            )
        elif gate_id == "world_isolation_and_fail_closed":
            passed = declaration_ok and isolation_ok
            evidence = (
                "Exactly one locked corruption and cross-world control ran and "
                "failed closed."
            )
        else:
            passed = False
            evidence = "No evaluator is registered for this required fatal gate."
        if not declaration_exact:
            evidence += (
                " Manifest fatal-gate declarations are missing, duplicated, or not "
                "the exact locked set."
            )
        gates.append(GateEvidence(gate_id, "PASS" if passed else "FAIL", evidence))
    return gates


def _world_result(
    world_id: str,
    manifest: Mapping[str, Any],
    controls: Sequence[ControlResult],
    gates: Sequence[GateEvidence],
    artifacts: Mapping[str, Any],
    *,
    required_gate_ids: Sequence[str] | None = None,
    required_control_ids: Sequence[str] | None = None,
    inspectable_scenario: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    required_gate_ids = tuple(required_gate_ids or [gate.gate_id for gate in gates])
    required_control_ids = tuple(
        required_control_ids or [control.control_id for control in controls]
    )
    gate_ids = [gate.gate_id for gate in gates]
    control_ids = [control.control_id for control in controls]
    gate_set_exact = (
        bool(required_gate_ids)
        and len(gate_ids) == len(required_gate_ids)
        and Counter(gate_ids) == Counter(required_gate_ids)
    )
    control_set_exact = (
        bool(required_control_ids)
        and len(control_ids) == len(required_control_ids)
        and Counter(control_ids) == Counter(required_control_ids)
    )
    fatal_pass = (
        gate_set_exact
        and control_set_exact
        and bool(gates)
        and bool(controls)
        and all(gate.status == "PASS" for gate in gates)
        and all(control.passed for control in controls)
    )
    return {
        "world_id": world_id,
        "version": manifest.get("version"),
        "modality": manifest.get("modality"),
        "manifest_state": manifest.get("state"),
        "status": "PASS" if fatal_pass else "FAIL",
        "protocol_exact": gate_set_exact and control_set_exact,
        "fatal_gates": [asdict(gate) for gate in gates],
        "controls": [
            {
                **asdict(control),
                "expected": list(control.expected),
                "expected_reason_codes": list(control.expected_reason_codes),
            }
            for control in controls
        ],
        "artifacts": dict(artifacts),
        "inspectable_scenario": (
            dict(inspectable_scenario) if inspectable_scenario is not None else None
        ),
        "scope_note": "PASS means bounded fixture/source consistency only; it does not establish authenticity, causality, efficacy, or universal truth.",
    }


def _scenario(
    protocol: Mapping[str, Any],
    controls: Sequence[ControlResult],
    manifest: Mapping[str, Any],
    *,
    world_id: str,
    version: str,
) -> dict[str, Any] | None:
    raw = protocol.get("inspectable_scenario")
    if not isinstance(raw, Mapping):
        return None
    control = next(
        (item for item in controls if item.control_id == raw.get("control_id")), None
    )
    locators = raw.get("source_locators")
    world = WORLD_REGISTRY.resolve(world_id, version)
    registered_locators = dict(world.scenario_locators)
    manifest_source_ids = {
        str(item.get("source_id"))
        for item in manifest.get("sources", [])
        if isinstance(item, Mapping) and item.get("source_id")
    }
    claim = next(
        (
            item.get("claim")
            for item in protocol.get("controls", [])
            if isinstance(item, Mapping)
            and item.get("control_id") == raw.get("control_id")
        ),
        None,
    )
    identity_ok = _scenario_identity_ok(world_id, claim, registered_locators)
    if (
        control is None
        or not isinstance(locators, list)
        or not locators
        or any(
            not isinstance(item, str) or not item.startswith("https://")
            for item in locators
        )
        or locators != list(registered_locators.values())
        or set(registered_locators) != manifest_source_ids
        or not identity_ok
    ):
        return {
            "status": "FAIL",
            "reason": "Declared scenario locators do not exactly match registered source and claim identities.",
        }
    return {
        "status": "DECLARED" if control.passed else "FAIL",
        "control_id": control.control_id,
        "observed": control.observed,
        "source_locators": list(locators),
        "scope_note": "Locator metadata exactly matches the registered source and claim identities; this offline run does not retrieve or independently validate the live page.",
    }


def _scenario_identity_ok(
    world_id: str,
    claim: object,
    registered_locators: Mapping[str, str],
) -> bool:
    if not isinstance(claim, Mapping):
        return False
    if world_id == "open-targets":
        locator = registered_locators.get("open-targets-graphql-26-06", "")
        return (
            f"/target/{claim.get('target_id')}/" in locator
            and f"/associations/{claim.get('disease_id')}" in locator
        )
    if world_id == "clinical-trials-sec":
        clinical = registered_locators.get("clinicaltrials-gov-api-v2", "")
        sec = registered_locators.get("sec-edgar-submissions-and-archives", "")
        cik = str(claim.get("cik", "")).lstrip("0")
        accession = str(claim.get("sec_accession", "")).replace("-", "")
        return (
            clinical.endswith(f"/study/{claim.get('nct_id')}")
            and bool(cik)
            and f"/data/{cik}/{accession}/" in sec
        )
    return not registered_locators


def _clinical_timestamp_semantics(
    fixture: Mapping[str, Any],
    protocol: Mapping[str, Any],
    controls: Sequence[ControlResult],
) -> bool:
    try:
        provenance = fixture["provenance"]
        if not isinstance(provenance, Mapping):
            return False
        window_start = _parse_utc(provenance["window_start"])
        window_end = _parse_utc(provenance["window_end"])
        record_times = [_parse_utc(item["accepted_at"]) for item in fixture["records"]]
        specs = {
            str(item["control_id"]): item
            for item in protocol["controls"]
            if isinstance(item, Mapping)
        }
        positive_as_of = _parse_utc(
            specs["clinical-trials-positive-timestamped-join"]["claim"]["as_of"]
        )
        cutoff_as_of = _parse_utc(
            specs["clinical-trials-null-post-cutoff"]["claim"]["as_of"]
        )
    except (KeyError, TypeError, ValueError):
        return False
    cutoff_control = next(
        (
            item
            for item in controls
            if item.control_id == "clinical-trials-null-post-cutoff"
        ),
        None,
    )
    return (
        bool(record_times)
        and window_start <= min(record_times) <= max(record_times) <= window_end
        and max(record_times) <= positive_as_of
        and cutoff_as_of < min(record_times)
        and cutoff_control is not None
        and cutoff_control.passed
        and cutoff_control.observed == "INCONCLUSIVE"
        and cutoff_control.reason_code == "POST_CUTOFF_EVIDENCE"
    )


def _arc_evaluation(
    protocol: Mapping[str, Any],
    *,
    fixture_root: Path,
    manifest_root: Path,
    control_corpus_path: Path,
    source_terms_review_path: Path,
    source_terms_review: SourceTermsReview,
    review_policy: ReviewPolicy,
) -> dict[str, Any]:
    fixture_path = fixture_root / "arc_vcc"
    fixture = load_arc(fixture_path)
    adapter = ArcVCCAdapter.from_path(fixture_path)
    controls = _run_arc_controls(protocol, adapter, fixture_root=fixture_root)
    manifest_path = manifest_root / "arc-vcc.json"
    manifest = _json(manifest_path)
    gates = _manifest_gates(
        manifest,
        fixture_path,
        adapter.source_hashes,
        controls,
        world_id="arc-vcc",
        version=str(protocol["version"]),
        expected_gate_ids=protocol["fatal_gate_ids"],
        preregistered_source_hashes=protocol["registered_source_hashes"],
        source_terms_review=source_terms_review,
        review_policy=review_policy,
        semantic_checks={
            "split_integrity_no_leakage": fixture.metadata.tuning_split
            != fixture.metadata.evaluation_split
            and len(
                {
                    (
                        item.perturbed_gene,
                        item.response_gene,
                        item.assay,
                        item.summary_statistic,
                    )
                    for item in fixture.measurements
                }
            )
            == len(fixture.measurements),
        },
    )
    return _world_result(
        "arc-vcc",
        manifest,
        controls,
        gates,
        _artifact_digests(
            "arc-vcc",
            fixture_path,
            manifest_path,
            control_corpus_path=control_corpus_path,
            source_terms_review_path=source_terms_review_path,
        ),
        required_gate_ids=protocol["fatal_gate_ids"],
        required_control_ids=[item["control_id"] for item in protocol["controls"]],
    )


def _open_targets_evaluation(
    protocol: Mapping[str, Any],
    *,
    fixture_root: Path,
    manifest_root: Path,
    control_corpus_path: Path,
    source_terms_review_path: Path,
    source_terms_review: SourceTermsReview,
    review_policy: ReviewPolicy,
) -> dict[str, Any]:
    fixture_path = fixture_root / "open_targets" / "release-26.06.json"
    fixture = _json(fixture_path)
    adapter = OpenTargetsAdapter(fixture_path)
    controls = _run_json_controls(
        protocol, adapter, fixture_path, check_open_targets_claim
    )
    manifest_path = manifest_root / "open-targets.json"
    manifest = _json(manifest_path)
    gates = _manifest_gates(
        manifest,
        fixture_path,
        adapter.source_hashes,
        controls,
        world_id="open-targets",
        version=str(protocol["version"]),
        expected_gate_ids=protocol["fatal_gate_ids"],
        preregistered_source_hashes=protocol["registered_source_hashes"],
        source_terms_review=source_terms_review,
        review_policy=review_policy,
        semantic_checks={
            "release_and_score_semantics": all(
                isinstance(item.get("score"), (int, float))
                and not isinstance(item.get("score"), bool)
                and isinstance(item.get("score_definition"), str)
                and bool(item["score_definition"].strip())
                for item in fixture["records"]
            ),
        },
    )
    return _world_result(
        "open-targets",
        manifest,
        controls,
        gates,
        _artifact_digests(
            "open-targets",
            fixture_path,
            manifest_path,
            control_corpus_path=control_corpus_path,
            source_terms_review_path=source_terms_review_path,
        ),
        required_gate_ids=protocol["fatal_gate_ids"],
        required_control_ids=[item["control_id"] for item in protocol["controls"]],
        inspectable_scenario=_scenario(
            protocol,
            controls,
            manifest,
            world_id="open-targets",
            version=str(protocol["version"]),
        ),
    )


def _clinical_trials_evaluation(
    protocol: Mapping[str, Any],
    *,
    fixture_root: Path,
    manifest_root: Path,
    control_corpus_path: Path,
    source_terms_review_path: Path,
    source_terms_review: SourceTermsReview,
    review_policy: ReviewPolicy,
    clinical_review_path: Path,
) -> dict[str, Any]:
    fixture_path = fixture_root / "clinical_trials" / "fixture.json"
    fixture = _json(fixture_path)
    adapter = ClinicalTrialsAdapter(fixture_path)
    controls = _run_json_controls(
        protocol, adapter, fixture_path, check_clinical_trials_claim
    )
    manifest_path = manifest_root / "clinical-trials-sec.json"
    manifest = _json(manifest_path)
    clinical_review_bound = _clinical_review_binding_ok(
        fixture, clinical_review_path, manifest, review_policy
    )
    gates = _manifest_gates(
        manifest,
        fixture_path,
        adapter.source_hashes,
        controls,
        world_id="clinical-trials-sec",
        version=str(protocol["version"]),
        expected_gate_ids=protocol["fatal_gate_ids"],
        preregistered_source_hashes=protocol["registered_source_hashes"],
        source_terms_review=source_terms_review,
        review_policy=review_policy,
        additional_artifact_binding_ok=clinical_review_bound,
        semantic_checks={
            "timestamp_cutoff_no_time_travel": _clinical_timestamp_semantics(
                fixture, protocol, controls
            ),
        },
    )
    return _world_result(
        "clinical-trials-sec",
        manifest,
        controls,
        gates,
        _artifact_digests(
            "clinical-trials-sec",
            fixture_path,
            manifest_path,
            control_corpus_path=control_corpus_path,
            source_terms_review_path=source_terms_review_path,
            clinical_review_path=clinical_review_path,
        ),
        required_gate_ids=protocol["fatal_gate_ids"],
        required_control_ids=[item["control_id"] for item in protocol["controls"]],
        inspectable_scenario=_scenario(
            protocol,
            controls,
            manifest,
            world_id="clinical-trials-sec",
            version=str(protocol["version"]),
        ),
    )


def evaluate_pilot(
    *,
    fixture_root: Path = FIXTURE_ROOT,
    manifest_root: Path = MANIFEST_ROOT,
    control_corpus_path: Path = CONTROL_CORPUS_PATH,
    source_terms_review_path: Path = SOURCE_TERMS_REVIEW_PATH,
    clinical_review_path: Path = CLINICAL_REVIEW_PATH,
) -> dict[str, Any]:
    """Run all locked offline controls and return a receipt-like report."""

    protocols = _load_protocol(control_corpus_path)
    review_policy = _load_review_policy(control_corpus_path)
    source_terms_review = _load_source_terms_review(source_terms_review_path)
    manifest_by_world = {
        world_id: _json(manifest_root / f"{world_id}.json") for world_id in WORLD_IDS
    }
    source_terms_current = all(
        _review_is_fresh(
            source_terms_review.reviewed_at,
            manifest_by_world[world_id],
            evaluation_as_of=review_policy.evaluation_as_of,
            max_age_days=review_policy.source_terms_max_age_days,
        )
        for world_id in WORLD_IDS
    )
    clinical_review = _json(clinical_review_path)
    try:
        clinical_reviewed_at = _parse_utc(clinical_review.get("reviewed_at"))
    except ValueError:
        clinical_reviewed_at = datetime.min.replace(tzinfo=UTC)
    clinical_review_current = _review_is_fresh(
        clinical_reviewed_at,
        manifest_by_world["clinical-trials-sec"],
        evaluation_as_of=review_policy.evaluation_as_of,
        max_age_days=review_policy.clinical_relationship_max_age_days,
    )
    preregistered_reviews_current = source_terms_current and clinical_review_current
    worlds = [
        _clinical_trials_evaluation(
            protocols["clinical-trials-sec"],
            fixture_root=fixture_root,
            manifest_root=manifest_root,
            control_corpus_path=control_corpus_path,
            source_terms_review_path=source_terms_review_path,
            source_terms_review=source_terms_review,
            review_policy=review_policy,
            clinical_review_path=clinical_review_path,
        ),
        _open_targets_evaluation(
            protocols["open-targets"],
            fixture_root=fixture_root,
            manifest_root=manifest_root,
            control_corpus_path=control_corpus_path,
            source_terms_review_path=source_terms_review_path,
            source_terms_review=source_terms_review,
            review_policy=review_policy,
        ),
        _arc_evaluation(
            protocols["arc-vcc"],
            fixture_root=fixture_root,
            manifest_root=manifest_root,
            control_corpus_path=control_corpus_path,
            source_terms_review_path=source_terms_review_path,
            source_terms_review=source_terms_review,
            review_policy=review_policy,
        ),
    ]
    world_ids = [world["world_id"] for world in worlds]
    three_distinct_worlds = (
        len(world_ids) == 3
        and len(set(world_ids)) == 3
        and set(world_ids) == set(WORLD_IDS)
    )
    all_admitted = bool(worlds) and all(
        world["manifest_state"] == "ADMITTED" for world in worlds
    )
    modalities = {str(protocols[world_id]["modality"]) for world_id in WORLD_IDS}
    roles = {str(protocols[world_id]["pilot_role"]) for world_id in WORLD_IDS}
    world_results = {str(world["world_id"]): world for world in worlds}
    declared_role_coverage = (
        "perturbational" in modalities
        and any(item.startswith("translational_") for item in modalities)
        and "commercial_due_diligence" in roles
        and all(
            protocols[world_id]["modality"]
            == WORLD_REGISTRY.resolve(
                world_id, str(protocols[world_id]["version"])
            ).modality
            == world_results[world_id]["modality"]
            for world_id in WORLD_IDS
        )
    )
    inspectable_worlds = {
        world["world_id"]
        for world in worlds
        if isinstance(world["inspectable_scenario"], Mapping)
        and world["inspectable_scenario"].get("status") == "DECLARED"
    }
    declared_scenario_locators_exact = {
        "clinical-trials-sec",
        "open-targets",
    } <= inspectable_worlds
    all_worlds_pass = bool(worlds) and all(
        world["status"] == "PASS" for world in worlds
    )
    pilot_ready = (
        all_worlds_pass
        and three_distinct_worlds
        and all_admitted
        and declared_role_coverage
        and declared_scenario_locators_exact
        and preregistered_reviews_current
    )
    return {
        "schema_version": "bio-claim-firewall-pilot-readiness-2",
        "evaluation_mode": "offline_deterministic_locked_controls",
        "evaluation_as_of": review_policy.evaluation_as_of.isoformat().replace(
            "+00:00", "Z"
        ),
        "review_freshness": {
            "source_terms_max_age_days": review_policy.source_terms_max_age_days,
            "clinical_relationship_max_age_days": review_policy.clinical_relationship_max_age_days,
            "source_terms_reviewed_at": source_terms_review.reviewed_at.isoformat().replace(
                "+00:00", "Z"
            ),
            "clinical_relationship_reviewed_at": clinical_reviewed_at.isoformat().replace(
                "+00:00", "Z"
            ),
        },
        "artifact_digests": {
            "registry_sha256": _sha256(REGISTRY_PATH),
            "evaluator_sha256": _sha256(Path(__file__)),
            "control_corpus_sha256": _sha256(control_corpus_path),
            "source_terms_review_sha256": _sha256(source_terms_review_path),
            "clinical_review_sha256": _sha256(clinical_review_path),
        },
        "readiness_requirements": {
            "three_distinct_preregistered_worlds": three_distinct_worlds,
            "all_manifests_admitted": all_admitted,
            "declared_perturbational_translational_pilot_roles_present": declared_role_coverage,
            "declared_clinical_and_open_targets_registered_locators_exact": declared_scenario_locators_exact,
            "preregistered_operator_reviews_current": preregistered_reviews_current,
            "all_fatal_gates_and_controls_pass": all_worlds_pass,
        },
        "worlds": worlds,
        "deferred_worlds": [
            {"world_id": key, "status": "DEFERRED", "reason": value}
            for key, value in sorted(DEFERRED_WORLDS.items())
        ],
        "pilot_ready": pilot_ready,
        "decision": ("READY_FOR_BOUNDED_PILOT" if pilot_ready else "WITHHOLD_PILOT"),
        "decision_rule": "Exactly three distinct ADMITTED worlds must satisfy their exact non-empty fatal-gate and control protocols, current preregistered review-age limits, and exact registered scenario-locator metadata; this is readiness to test usefulness with design partners, not evidence that usefulness or live-source availability has been demonstrated.",
        "limitations": [
            "A passing receipt establishes consistency with a hash-bound compact fixture, not source authenticity.",
            "Arc results are measurements, not STATE predictions; Open Targets results are associations, not causality or efficacy.",
            "ClinicalTrials.gov plus SEC results are disclosure consistency checks, not trial success or corporate-truth claims.",
            "Declared pilot roles and HTTPS locators are offline metadata; they do not establish commercial usefulness, customer demand, or current live-page availability.",
            "Operator source-terms and clinical relationship reviews are freshness-gated against each manifest data clock and the locked evaluation date; they are scope-limited reviews, not independent legal or scientific validation.",
        ],
    }


def write_report(output_dir: str | Path | None = None) -> dict[str, Any]:
    """Write stable JSON and Markdown reports, returning the report object."""

    report = evaluate_pilot()
    destination = (
        Path(output_dir)
        if output_dir is not None
        else Path(__file__).resolve().parents[1] / "results"
    )
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "pilot_readiness.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Bio Claim Firewall: pilot-readiness evaluation",
        "",
        f"Decision: **{report['decision']}**",
        "",
        "This deterministic offline run uses independently locked claims and immutable registry source contracts. PASS means bounded adapter/source consistency only; it does not establish authenticity, causality, efficacy, or universal truth.",
        "",
        "| World | Status | Fatal gates | Controls |",
        "| --- | --- | ---: | ---: |",
    ]
    for world in report["worlds"]:
        gate_count = sum(gate["status"] == "PASS" for gate in world["fatal_gates"])
        control_count = sum(control["passed"] for control in world["controls"])
        lines.append(
            f"| `{world['world_id']}` `{world['version']}` | **{world['status']}** | "
            f"{gate_count}/{len(world['fatal_gates'])} | "
            f"{control_count}/{len(world['controls'])} |"
        )
    lines += ["", "## Readiness requirements", ""]
    for requirement, passed in report["readiness_requirements"].items():
        lines.append(f"- `{requirement}`: **{'PASS' if passed else 'FAIL'}**")
    lines += ["", "## Deferred worlds", ""]
    for world in report["deferred_worlds"]:
        lines.append(f"- `{world['world_id']}` — {world['reason']}")
    lines += ["", "## Gate evidence", ""]
    for world in report["worlds"]:
        lines += [f"### {world['world_id']}", ""]
        for gate in world["fatal_gates"]:
            lines.append(
                f"- `{gate['gate_id']}`: **{gate['status']}** — {gate['evidence']}"
            )
    (destination / "pilot_readiness.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return report


if __name__ == "__main__":  # pragma: no cover
    result = write_report()
    print(
        json.dumps(
            {"decision": result["decision"], "pilot_ready": result["pilot_ready"]},
            sort_keys=True,
        )
    )
