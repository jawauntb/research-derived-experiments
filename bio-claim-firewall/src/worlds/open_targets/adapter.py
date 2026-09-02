"""Fail-closed Open Targets 26.06 association adapter.

The release row is authoritative for the source-specific association and
score.  This adapter never upgrades that association into causality, efficacy,
or a universal biological statement.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

from worlds.registry import (
    WorldRegistryError,
    get_world,
    receipt_world_digest,
    validate_world_artifacts,
)

WORLD_ID = "open-targets"
WORLD_VERSION = "26.06"
OPEN_TARGETS_WORLD_ID = WORLD_ID
OPEN_TARGETS_WORLD_VERSION = WORLD_VERSION
CHECKER_VERSION = "open-targets/0.1.0"
SCHEMA_VERSION = "open-targets-association-ledger-0.1"
SOURCE_IDS = frozenset({"open-targets-graphql-26-06"})
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_CLAIM_FIELDS = frozenset(
    {
        "claim_id",
        "target_id",
        "disease_id",
        "evidence_source",
        "release",
        "score",
        "score_threshold",
        "assertion_type",
        "confidence_language",
        "world_id",
        "world_version",
    }
)
_FORBIDDEN_LANGUAGE = {
    "causal",
    "causes",
    "clinical_efficacy",
    "efficacy",
    "universal",
    "always",
    "treats",
}


class OutcomeKind(StrEnum):
    ACCEPTED_CONDITIONALLY = "ACCEPTED_CONDITIONALLY"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    CHECKER_ERROR = "CHECKER_ERROR"


class FixtureCorruption(ValueError):
    """Release fixture cannot be trusted."""


OpenTargetsIntegrityError = FixtureCorruption


@dataclass(frozen=True, slots=True)
class OpenTargetsClaim:
    target_id: str
    disease_id: str
    evidence_source: str
    release: str
    claim_id: str | None = None
    score: float | None = None
    score_threshold: float | None = None
    assertion_type: str | None = None
    confidence_language: str | None = None
    world_id: str = WORLD_ID
    world_version: str = WORLD_VERSION

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> OpenTargetsClaim:
        if not isinstance(value, Mapping):
            raise TypeError("Open Targets claim must be an object")
        unknown = set(value) - _CLAIM_FIELDS
        if unknown:
            raise ValueError(f"unknown Open Targets claim field(s): {sorted(unknown)}")
        required = ("target_id", "disease_id", "evidence_source", "release")
        missing = [
            field
            for field in required
            if not isinstance(value.get(field), str) or not value[field].strip()
        ]
        if missing:
            raise ValueError(f"missing Open Targets claim field(s): {missing}")
        if (
            value.get("world_id", WORLD_ID) != WORLD_ID
            or value.get("world_version", WORLD_VERSION) != WORLD_VERSION
        ):
            raise FixtureCorruption(
                "claim world identity does not match the selected Open Targets world"
            )
        for field in ("score", "score_threshold"):
            if field in value and (
                isinstance(value[field], bool)
                or not isinstance(value[field], (int, float))
                or not math.isfinite(float(value[field]))
            ):
                raise ValueError(f"{field} must be a finite number")
        for field in ("claim_id", "assertion_type", "confidence_language"):
            if value.get(field) is not None and (
                not isinstance(value[field], str) or not value[field].strip()
            ):
                raise ValueError(f"{field} must be non-empty text when present")
        return cls(
            target_id=value["target_id"].strip(),
            disease_id=value["disease_id"].strip(),
            evidence_source=value["evidence_source"].strip(),
            release=value["release"].strip(),
            claim_id=value.get("claim_id"),
            score=float(value["score"]) if "score" in value else None,
            score_threshold=float(value["score_threshold"])
            if "score_threshold" in value
            else None,
            assertion_type=value.get("assertion_type"),
            confidence_language=value.get("confidence_language"),
            world_id=value.get("world_id", WORLD_ID),
            world_version=value.get("world_version", WORLD_VERSION),
        )

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "target_id": self.target_id,
            "disease_id": self.disease_id,
            "evidence_source": self.evidence_source,
            "release": self.release,
        }
        for field in (
            "claim_id",
            "score",
            "score_threshold",
            "assertion_type",
            "confidence_language",
        ):
            value = getattr(self, field)
            if value is not None:
                result[field] = value
        if self.world_id != WORLD_ID or self.world_version != WORLD_VERSION:
            result["world_id"] = self.world_id
            result["world_version"] = self.world_version
        return result


@dataclass(frozen=True, slots=True)
class OpenTargetsOutcome:
    verdict: OutcomeKind
    reason_code: str
    message: str
    claim: dict[str, Any]
    world_id: str = WORLD_ID
    world_version: str = WORLD_VERSION
    winning_rule: str | None = None
    citations: tuple[str, ...] = ()
    snapshot_hashes: Mapping[str, str] | None = None
    receipt: Mapping[str, Any] | None = None
    evidence_payload: Mapping[str, Any] | None = None

    @property
    def outcome(self) -> str:
        return (
            "ACCEPTED"
            if self.verdict is OutcomeKind.ACCEPTED_CONDITIONALLY
            else self.verdict.value
        )

    @property
    def reason(self) -> str:
        return self.message

    @property
    def evidence(self) -> dict[str, Any] | None:
        if not self.citations:
            return None
        return (
            dict(self.evidence_payload)
            if self.evidence_payload is not None
            else {
                "record_ids": list(self.citations),
                "source_hashes": dict(self.snapshot_hashes or {}),
            }
        )

    @property
    def source_hashes(self) -> dict[str, str]:
        return dict(self.snapshot_hashes or {})

    def as_dict(self) -> dict[str, Any]:
        output: dict[str, Any] = {
            "verdict": self.verdict.value,
            "outcome": self.outcome,
            "reason_code": self.reason_code,
            "message": self.message,
            "reason": self.message,
            "claim": dict(self.claim),
            "evidence": self.evidence,
            "world_id": self.world_id,
            "world_version": self.world_version,
        }
        if self.winning_rule is not None:
            output["winning_rule"] = self.winning_rule
        if self.citations:
            output["citations"] = list(self.citations)
        if self.snapshot_hashes is not None:
            output["snapshot_hashes"] = dict(self.snapshot_hashes)
        if self.receipt is not None:
            output["receipt"] = dict(self.receipt)
        return output


OpenTargetsResult = OpenTargetsOutcome


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _validate_fixture(
    value: Mapping[str, Any],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    if (
        not isinstance(value, Mapping)
        or value.get("world_id") != WORLD_ID
        or value.get("version") != WORLD_VERSION
    ):
        raise FixtureCorruption(
            "fixture is bound to a different Open Targets world or version"
        )
    if value.get("schema_version") != SCHEMA_VERSION:
        raise FixtureCorruption("unsupported Open Targets ledger schema")
    hashes = value.get("source_hashes")
    if (
        not isinstance(hashes, Mapping)
        or set(hashes) != SOURCE_IDS
        or any(
            not isinstance(item, str) or not _SHA256.fullmatch(item)
            for item in hashes.values()
        )
    ):
        raise FixtureCorruption(
            "Open Targets fixture must declare complete official source hashes"
        )
    records = value.get("records")
    if not isinstance(records, list) or not records:
        raise FixtureCorruption("Open Targets fixture records must be a non-empty list")
    payload = {
        key: value[key]
        for key in ("schema_version", "world_id", "version", "source_hashes", "records")
    }
    if not isinstance(value.get("integrity_sha256"), str) or value[
        "integrity_sha256"
    ] != _digest(payload):
        raise FixtureCorruption("Open Targets fixture integrity digest mismatch")
    try:
        validate_world_artifacts(
            get_world(WORLD_ID, WORLD_VERSION),
            {"open-targets-derived-ledger": value["integrity_sha256"]},
        )
    except WorldRegistryError as exc:
        raise FixtureCorruption(str(exc)) from exc
    seen: set[str] = set()
    checked: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise FixtureCorruption("Open Targets records must be objects")
        item = dict(record)
        if (
            not isinstance(item.get("record_id"), str)
            or not item["record_id"]
            or item["record_id"] in seen
        ):
            raise FixtureCorruption("Open Targets record ids must be unique")
        seen.add(item["record_id"])
        if item.get("source") not in SOURCE_IDS:
            raise FixtureCorruption("Open Targets record has an unallowlisted source")
        for field in (
            "target_id",
            "disease_id",
            "evidence_source",
            "release",
            "score",
            "score_definition",
        ):
            if field not in item:
                raise FixtureCorruption(f"Open Targets record missing {field!r}")
        if (
            item["release"] != WORLD_VERSION
            or not isinstance(item["score"], (int, float))
            or isinstance(item["score"], bool)
            or not math.isfinite(float(item["score"]))
        ):
            raise FixtureCorruption("Open Targets record has invalid release or score")
        if (
            not isinstance(item["score_definition"], str)
            or not item["score_definition"].strip()
        ):
            raise FixtureCorruption(
                "Open Targets record has no source-specific score definition"
            )
        checked.append(item)
    return dict(hashes), checked


def load_fixture(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if path.is_dir():
        path = path / "release-26.06.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FixtureCorruption(f"cannot load Open Targets fixture: {exc}") from exc
    hashes, records = _validate_fixture(value)
    return {
        "schema_version": SCHEMA_VERSION,
        "world_id": WORLD_ID,
        "version": WORLD_VERSION,
        "source_hashes": hashes,
        "records": records,
        "integrity_sha256": value["integrity_sha256"],
    }


def _receipt(
    claim: OpenTargetsClaim,
    verdict: OutcomeKind,
    reason_code: str,
    message: str,
    *,
    hashes: Mapping[str, str],
    citations: Sequence[str],
    winning_rule: str | None,
    checker_version: str,
    evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    world_digest = receipt_world_digest(get_world(WORLD_ID, WORLD_VERSION), hashes)
    body: dict[str, Any] = {
        "schema_version": "2.0.0",
        "world_id": WORLD_ID,
        "world_version": WORLD_VERSION,
        "world_digest": world_digest,
        "claim": claim.as_dict(),
        "verdict": verdict.value,
        "outcome": "ACCEPTED"
        if verdict is OutcomeKind.ACCEPTED_CONDITIONALLY
        else verdict.value,
        "reason_code": reason_code,
        "message": message,
        "snapshot_hashes": dict(sorted(hashes.items())),
        "citations": list(citations),
        "checker_version": checker_version,
    }
    if winning_rule is not None:
        body["winning_rule"] = winning_rule
    if evidence is not None:
        body["evidence"] = dict(evidence)
    return {
        "receipt_version": "2",
        "receipt_id": _digest(body),
        "canonical_payload": body,
    }


class OpenTargetsAdapter:
    world_id = WORLD_ID
    world_version = WORLD_VERSION

    def __init__(
        self,
        fixture: Mapping[str, Any] | str | Path,
        *,
        checker_version: str = CHECKER_VERSION,
    ):
        if isinstance(fixture, (str, Path)):
            fixture = load_fixture(fixture)
        hashes, records = _validate_fixture(fixture)
        receipt_world_digest(get_world(WORLD_ID, WORLD_VERSION), hashes)
        self._hashes = hashes
        self._records = tuple(
            json.loads(json.dumps(record, sort_keys=True)) for record in records
        )
        self.checker_version = checker_version

    @classmethod
    def from_fixture(
        cls, path: str | Path, *, checker_version: str = CHECKER_VERSION
    ) -> OpenTargetsAdapter:
        return cls(path, checker_version=checker_version)

    from_path = from_fixture

    @property
    def source_hashes(self) -> dict[str, str]:
        return dict(self._hashes)

    def check(
        self,
        claim: OpenTargetsClaim | Mapping[str, Any],
        *,
        checker_version: str | None = None,
    ) -> OpenTargetsOutcome:
        checker_version = checker_version or self.checker_version
        try:
            parsed = (
                claim
                if isinstance(claim, OpenTargetsClaim)
                else OpenTargetsClaim.from_mapping(claim)
            )
            if parsed.world_id != WORLD_ID or parsed.world_version != WORLD_VERSION:
                raise FixtureCorruption(
                    "claim world identity does not match the selected Open Targets world"
                )
            return self._check_valid(parsed, checker_version=checker_version)
        except FixtureCorruption as exc:
            return self._error(claim, "CORRUPT_EVIDENCE", str(exc), checker_version)
        except (TypeError, ValueError) as exc:
            return self._error(
                claim, "CROSS_WORLD_OR_MALFORMED_INPUT", str(exc), checker_version
            )
        except Exception as exc:  # noqa: BLE001  # pragma: no cover - fail closed
            return self._error(
                claim, "UNEXPECTED_ADAPTER_FAILURE", str(exc), checker_version
            )

    verify = check

    def _check_valid(
        self, claim: OpenTargetsClaim, *, checker_version: str
    ) -> OpenTargetsOutcome:
        if claim.release != WORLD_VERSION:
            return self._finish(
                claim,
                OutcomeKind.REJECTED,
                "WRONG_RELEASE",
                f"Only Open Targets release {WORLD_VERSION} is bound to this world.",
                (),
                "OT.RELEASE.01",
                checker_version,
            )
        if claim.score_threshold is not None:
            return self._finish(
                claim,
                OutcomeKind.REJECTED,
                "UNSUPPORTED_SCORE_THRESHOLD",
                "A threshold claim is not licensed by a source-specific association row.",
                (),
                "OT.SCOPE.01",
                checker_version,
            )
        if claim.assertion_type is not None and claim.assertion_type.casefold() not in {
            "association",
            "target_disease_association",
        }:
            return self._finish(
                claim,
                OutcomeKind.REJECTED,
                "UNSUPPORTED_ASSERTION_TYPE",
                "This world supports association assertions only.",
                (),
                "OT.SCOPE.02",
                checker_version,
            )
        if claim.confidence_language is not None and any(
            term in claim.confidence_language.casefold() for term in _FORBIDDEN_LANGUAGE
        ):
            return self._finish(
                claim,
                OutcomeKind.REJECTED,
                "UNSUPPORTED_CLAIM_SCOPE",
                "The release row does not license causal, efficacy, or universal language.",
                (),
                "OT.SCOPE.03",
                checker_version,
            )
        matches = [
            r
            for r in self._records
            if r["target_id"] == claim.target_id
            and r["disease_id"] == claim.disease_id
            and r["evidence_source"] == claim.evidence_source
            and r["release"] == WORLD_VERSION
        ]
        if not matches:
            return self._finish(
                claim,
                OutcomeKind.INCONCLUSIVE,
                "ASSOCIATION_NOT_IN_PROJECTION",
                "The compact projection has no exact target, disease, and source tuple; absence from this projection cannot establish absence from the release.",
                (),
                None,
                checker_version,
            )
        if len(matches) != 1:
            return self._finish(
                claim,
                OutcomeKind.INCONCLUSIVE,
                "AMBIGUOUS_ASSOCIATION",
                "More than one exact source row matched; the release cannot be collapsed safely.",
                tuple(sorted(r["record_id"] for r in matches)),
                None,
                checker_version,
            )
        row = matches[0]
        if claim.score is not None and float(claim.score) != float(row["score"]):
            return self._finish(
                claim,
                OutcomeKind.REJECTED,
                "SCORE_MISMATCH",
                "The declared score is not the source-defined score in the pinned row.",
                (row["record_id"],),
                "OT.SCORE.01",
                checker_version,
            )
        evidence = {
            "record_id": row["record_id"],
            "target_id": row["target_id"],
            "disease_id": row["disease_id"],
            "evidence_source": row["evidence_source"],
            "release": row["release"],
            "score": row["score"],
            "score_definition": row["score_definition"],
            "source": row["source"],
        }
        return self._finish(
            claim,
            OutcomeKind.ACCEPTED_CONDITIONALLY,
            "SOURCE_SPECIFIC_ASSOCIATION_PRESENT",
            "The exact source-specific target-disease association exists in Open Targets release 26.06.",
            (row["record_id"],),
            "OT.ASSOCIATION.02",
            checker_version,
            evidence=evidence,
        )

    def _finish(
        self,
        claim: OpenTargetsClaim,
        verdict: OutcomeKind,
        reason_code: str,
        message: str,
        citations: Sequence[str],
        rule: str | None,
        checker_version: str,
        *,
        evidence: Mapping[str, Any] | None = None,
    ) -> OpenTargetsOutcome:
        bound_evidence = (
            dict(evidence)
            if evidence is not None
            else {
                "record_ids": list(citations),
                "source_hashes": dict(self._hashes),
            }
            if citations
            else None
        )
        receipt = _receipt(
            claim,
            verdict,
            reason_code,
            message,
            hashes=self._hashes,
            citations=citations,
            winning_rule=rule,
            checker_version=checker_version,
            evidence=bound_evidence,
        )
        return OpenTargetsOutcome(
            verdict,
            reason_code,
            message,
            claim.as_dict(),
            winning_rule=rule,
            citations=tuple(citations),
            snapshot_hashes=self._hashes,
            receipt=receipt,
            evidence_payload=bound_evidence,
        )

    def _error(
        self, claim: Any, reason_code: str, message: str, checker_version: str
    ) -> OpenTargetsOutcome:
        try:
            parsed = (
                claim
                if isinstance(claim, OpenTargetsClaim)
                else OpenTargetsClaim.from_mapping(claim)
            )
            payload = parsed.as_dict()
        except Exception:  # noqa: BLE001 - error receipts must survive malformed objects
            payload = (
                dict(claim) if isinstance(claim, Mapping) else {"unparsed": repr(claim)}
            )
        body = {
            "schema_version": "2.0.0",
            "world_id": WORLD_ID,
            "world_version": WORLD_VERSION,
            "world_digest": receipt_world_digest(
                get_world(WORLD_ID, WORLD_VERSION), self._hashes
            ),
            "verdict": OutcomeKind.CHECKER_ERROR.value,
            "outcome": OutcomeKind.CHECKER_ERROR.value,
            "reason_code": reason_code,
            "message": message,
            "claim": payload,
            "snapshot_hashes": dict(sorted(self._hashes.items())),
            "checker_version": checker_version,
            "citations": [],
        }
        return OpenTargetsOutcome(
            OutcomeKind.CHECKER_ERROR,
            reason_code,
            message,
            payload,
            snapshot_hashes=self._hashes,
            receipt={
                "receipt_version": "2",
                "receipt_id": _digest(body),
                "canonical_payload": body,
            },
        )


def check_open_targets_claim(
    claim: OpenTargetsClaim | Mapping[str, Any] | str | Path,
    fixture: Mapping[str, Any] | str | Path,
    *,
    checker_version: str = CHECKER_VERSION,
) -> OpenTargetsOutcome:
    claim_value: OpenTargetsClaim | Mapping[str, Any] = (
        {} if isinstance(claim, (str, Path)) else claim
    )
    fixture_value: Mapping[str, Any] | str | Path = fixture
    try:
        if isinstance(claim, (str, Path)):
            if not isinstance(fixture, Mapping):
                raise TypeError(
                    "reversed Open Targets arguments require a claim mapping"
                )
            claim_value, fixture_value = cast(Mapping[str, Any], fixture), claim
        return OpenTargetsAdapter(fixture_value).check(
            claim_value, checker_version=checker_version
        )
    except Exception as exc:  # noqa: BLE001 - corrupt fixture construction fails closed
        payload = dict(claim_value) if isinstance(claim_value, Mapping) else None
        body = {
            "schema_version": "2.0.0",
            "world_id": WORLD_ID,
            "world_version": WORLD_VERSION,
            "verdict": OutcomeKind.CHECKER_ERROR.value,
            "outcome": OutcomeKind.CHECKER_ERROR.value,
            "reason_code": "CORRUPT_EVIDENCE",
            "message": str(exc),
            "claim": payload,
            "snapshot_hashes": {},
            "citations": [],
            "checker_version": checker_version,
        }
        return OpenTargetsOutcome(
            OutcomeKind.CHECKER_ERROR,
            "CORRUPT_EVIDENCE",
            str(exc),
            payload or {},
            snapshot_hashes={},
            receipt={
                "receipt_version": "2",
                "receipt_id": _digest(body),
                "canonical_payload": body,
            },
        )


def validate_fixture(path: str | Path) -> dict[str, Any]:
    fixture = load_fixture(path)
    return {
        "world_id": WORLD_ID,
        "version": WORLD_VERSION,
        "record_count": len(fixture["records"]),
        "source_hashes": dict(sorted(fixture["source_hashes"].items())),
        "releases": sorted({row["release"] for row in fixture["records"]}),
        "score_definitions_preserved": all(
            bool(row["score_definition"]) for row in fixture["records"]
        ),
    }


__all__ = [
    "OPEN_TARGETS_WORLD_ID",
    "OPEN_TARGETS_WORLD_VERSION",
    "FixtureCorruption",
    "OpenTargetsAdapter",
    "OpenTargetsClaim",
    "OpenTargetsIntegrityError",
    "OpenTargetsOutcome",
    "OpenTargetsResult",
    "OutcomeKind",
    "check_open_targets_claim",
    "load_fixture",
    "validate_fixture",
]
