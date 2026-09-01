"""Fail-closed ClinicalTrials.gov + SEC disclosure adapter.

Only compact, derived records are accepted.  Raw registry responses and SEC
filings are deliberately not part of this module or its fixtures.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

WORLD_ID = "clinical-trials-sec"
WORLD_VERSION = "2025-09-01_2026-09-01"
CLINICAL_TRIALS_WORLD_ID = WORLD_ID
CLINICAL_TRIALS_WORLD_VERSION = WORLD_VERSION
CHECKER_VERSION = "clinical-trials-sec/0.1.0"
SCHEMA_VERSION = "clinical-trials-sec-ledger-0.1"
SOURCE_IDS = frozenset({"clinicaltrials-gov-api-v2", "sec-edgar-submissions-and-archives"})
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_NCT = re.compile(r"^NCT\d{8}$")
_ACCESSION = re.compile(r"^\d{10}-\d{2}-\d{6}$")
_RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_CLAIM_FIELDS = frozenset(
    {
        "claim_id",
        "nct_id",
        "sponsor",
        "intervention",
        "sec_accession",
        "cik",
        "exhibit_locator",
        "asserted_span_sha256",
        "as_of",
        "world_id",
        "world_version",
    }
)


class OutcomeKind(StrEnum):
    """The only outcomes an adapter can emit."""

    ACCEPTED_CONDITIONALLY = "ACCEPTED_CONDITIONALLY"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    CHECKER_ERROR = "CHECKER_ERROR"


class FixtureCorruption(ValueError):
    """Fixture or evidence provenance cannot be trusted."""


ClinicalTrialsIntegrityError = FixtureCorruption


@dataclass(frozen=True, slots=True)
class ClinicalTrialsClaim:
    nct_id: str
    sponsor: str
    intervention: str
    sec_accession: str
    exhibit_locator: str
    asserted_span_sha256: str
    as_of: str
    cik: str | None = None
    claim_id: str | None = None
    world_id: str = WORLD_ID
    world_version: str = WORLD_VERSION

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> ClinicalTrialsClaim:
        if not isinstance(value, Mapping):
            raise TypeError("clinical-trials claim must be an object")
        unknown = set(value) - _CLAIM_FIELDS
        if unknown:
            raise ValueError(f"unknown clinical-trials claim field(s): {sorted(unknown)}")
        required = _CLAIM_FIELDS - {"claim_id", "cik", "world_id", "world_version"}
        missing = sorted(field for field in required if field not in value)
        if missing:
            raise ValueError(f"missing clinical-trials claim field(s): {missing}")
        text_fields = ("nct_id", "sponsor", "intervention", "sec_accession", "exhibit_locator", "asserted_span_sha256", "as_of")
        vals: dict[str, str] = {}
        for field in text_fields:
            item = value[field]
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"clinical-trials claim field {field!r} must be non-empty text")
            vals[field] = item.strip()
        if not _NCT.fullmatch(vals["nct_id"]):
            raise ValueError("nct_id must be an exact NCT######## identifier")
        if not _ACCESSION.fullmatch(vals["sec_accession"]):
            raise ValueError("sec_accession must be an exact SEC accession")
        cik = value.get("cik")
        if cik is not None and (not isinstance(cik, str) or not re.fullmatch(r"\d{10}", cik.strip())):
            raise ValueError("cik must be a ten-digit SEC identifier when present")
        if not _SHA256.fullmatch(vals["asserted_span_sha256"]):
            raise ValueError("asserted_span_sha256 must be a complete lowercase SHA-256")
        _parse_utc(vals["as_of"])
        claim_id = value.get("claim_id")
        if claim_id is not None and (not isinstance(claim_id, str) or not claim_id.strip()):
            raise ValueError("claim_id must be non-empty text when present")
        world_id = value.get("world_id", WORLD_ID)
        world_version = value.get("world_version", WORLD_VERSION)
        if world_id != WORLD_ID or world_version != WORLD_VERSION:
            raise FixtureCorruption("claim world identity does not match the selected Clinical Trials world")
        return cls(**vals, cik=cik.strip() if isinstance(cik, str) else None, claim_id=claim_id, world_id=world_id, world_version=world_version)

    def as_dict(self) -> dict[str, str]:
        result = {
            "nct_id": self.nct_id,
            "sponsor": self.sponsor,
            "intervention": self.intervention,
            "sec_accession": self.sec_accession,
            "exhibit_locator": self.exhibit_locator,
            "asserted_span_sha256": self.asserted_span_sha256,
            "as_of": self.as_of,
        }
        if self.cik is not None:
            result["cik"] = self.cik
        if self.claim_id is not None:
            result["claim_id"] = self.claim_id
        if self.world_id != WORLD_ID or self.world_version != WORLD_VERSION:
            result["world_id"] = self.world_id
            result["world_version"] = self.world_version
        return result


@dataclass(frozen=True, slots=True)
class ClinicalTrialsOutcome:
    """Stable, receipt-compatible adapter output."""

    verdict: OutcomeKind
    reason_code: str
    message: str
    claim: dict[str, str]
    world_id: str = WORLD_ID
    world_version: str = WORLD_VERSION
    winning_rule: str | None = None
    citations: tuple[str, ...] = ()
    snapshot_hashes: Mapping[str, str] | None = None
    receipt: Mapping[str, Any] | None = None
    evidence_payload: Mapping[str, Any] | None = None

    @property
    def outcome(self) -> str:
        return "ACCEPTED" if self.verdict is OutcomeKind.ACCEPTED_CONDITIONALLY else self.verdict.value

    @property
    def reason(self) -> str:
        return self.message

    @property
    def evidence(self) -> dict[str, Any] | None:
        if not self.citations:
            return None
        return dict(self.evidence_payload) if self.evidence_payload is not None else {"record_ids": list(self.citations), "source_hashes": dict(self.snapshot_hashes or {})}

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


ClinicalTrialsResult = ClinicalTrialsOutcome


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _parse_utc(value: str) -> datetime:
    if not _RFC3339.fullmatch(value):
        raise ValueError("timestamp must be RFC3339 UTC with a Z suffix")
    return datetime.fromisoformat(value).astimezone(UTC)


def _same_text(left: Any, right: Any) -> bool:
    return isinstance(left, str) and isinstance(right, str) and " ".join(left.split()).casefold() == " ".join(right.split()).casefold()


def _validate_hashes(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != SOURCE_IDS:
        raise FixtureCorruption("clinical-trials fixture must declare both official source hashes")
    hashes = dict(value)
    if any(not isinstance(item, str) or not _SHA256.fullmatch(item) for item in hashes.values()):
        raise FixtureCorruption("clinical-trials source hashes must be complete lowercase SHA-256 values")
    return hashes


def _validate_fixture(value: Mapping[str, Any]) -> tuple[dict[str, str], list[dict[str, Any]]]:
    if not isinstance(value, Mapping) or value.get("world_id") != WORLD_ID or value.get("version") != WORLD_VERSION:
        raise FixtureCorruption("fixture is bound to a different world or version")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise FixtureCorruption("unsupported clinical-trials ledger schema")
    hashes = _validate_hashes(value.get("source_hashes"))
    records = value.get("records")
    if not isinstance(records, list) or not records:
        raise FixtureCorruption("clinical-trials fixture records must be a non-empty list")
    canonical_payload = {key: value[key] for key in ("schema_version", "world_id", "version", "source_hashes", "records")}
    integrity = value.get("integrity_sha256")
    if not isinstance(integrity, str) or not _SHA256.fullmatch(integrity) or integrity != _digest(canonical_payload):
        raise FixtureCorruption("clinical-trials fixture integrity digest mismatch")
    seen: set[str] = set()
    checked: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise FixtureCorruption("clinical-trials records must be objects")
        item = dict(record)
        record_id = item.get("record_id")
        source = item.get("source")
        if not isinstance(record_id, str) or not record_id or record_id in seen:
            raise FixtureCorruption("clinical-trials record ids must be unique and non-empty")
        if source not in SOURCE_IDS:
            raise FixtureCorruption("clinical-trials record has an unallowlisted source")
        seen.add(record_id)
        for field in ("nct_id", "sponsor", "intervention", "accepted_at"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise FixtureCorruption(f"clinical-trials record missing {field!r}")
        if not _NCT.fullmatch(item["nct_id"]):
            raise FixtureCorruption("clinical-trials record has malformed nct_id")
        try:
            _parse_utc(item["accepted_at"])
        except ValueError as exc:
            raise FixtureCorruption(str(exc)) from exc
        if source == "sec-edgar-submissions-and-archives":
            if not isinstance(item.get("cik"), str) or not re.fullmatch(r"\d{10}", item["cik"]):
                raise FixtureCorruption("SEC record has malformed CIK")
            if not _ACCESSION.fullmatch(str(item.get("sec_accession", ""))):
                raise FixtureCorruption("SEC record has malformed accession")
            if not isinstance(item.get("exhibit_locator"), str) or not item["exhibit_locator"].strip():
                raise FixtureCorruption("SEC record is missing exhibit locator")
            if not isinstance(item.get("asserted_span_sha256"), str) or not _SHA256.fullmatch(item["asserted_span_sha256"]):
                raise FixtureCorruption("SEC record is missing asserted span hash")
            if item.get("human_confirmed") is not True:
                raise FixtureCorruption("SEC asserted spans must be human-confirmed")
            if not isinstance(item.get("span_locator"), str) or not item["span_locator"].strip():
                raise FixtureCorruption("SEC record is missing exact span locator")
        checked.append(item)
    return hashes, checked


def load_fixture(path: str | Path) -> dict[str, Any]:
    """Load and validate a compact derived fixture; never fetches a source."""
    path = Path(path)
    if path.is_dir():
        path = path / "fixture.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FixtureCorruption(f"cannot load clinical-trials fixture: {exc}") from exc
    hashes, records = _validate_fixture(value)
    return {"schema_version": SCHEMA_VERSION, "world_id": WORLD_ID, "version": WORLD_VERSION, "source_hashes": hashes, "records": records, "integrity_sha256": value["integrity_sha256"]}


def _receipt(claim: ClinicalTrialsClaim, verdict: OutcomeKind, reason_code: str, message: str, *, hashes: Mapping[str, str], citations: Sequence[str], winning_rule: str | None, checker_version: str, evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "2.0.0",
        "world_id": WORLD_ID,
        "world_version": WORLD_VERSION,
        "world_digest": _digest({"world_id": WORLD_ID, "version": WORLD_VERSION, "source_hashes": dict(sorted(hashes.items())), "adapter_schema": SCHEMA_VERSION}),
        "claim": claim.as_dict(),
        "verdict": verdict.value,
        "outcome": "ACCEPTED" if verdict is OutcomeKind.ACCEPTED_CONDITIONALLY else verdict.value,
        "reason_code": reason_code,
        "message": message,
        "snapshot_hashes": dict(sorted(hashes.items())),
        "citations": list(citations),
        "checker_version": checker_version,
    }
    if evidence is not None:
        body["evidence"] = dict(evidence)
    if winning_rule is not None:
        body["winning_rule"] = winning_rule
    return {"receipt_version": "2", "receipt_id": _digest(body), "canonical_payload": body}


class ClinicalTrialsAdapter:
    """Deterministic checker over one validated clinical-trials fixture."""

    world_id = WORLD_ID
    world_version = WORLD_VERSION

    def __init__(self, fixture: Mapping[str, Any] | str | Path, *, checker_version: str = CHECKER_VERSION):
        if isinstance(fixture, (str, Path)):
            fixture = load_fixture(fixture)
        hashes, records = _validate_fixture(fixture)
        self._hashes = hashes
        self._records = tuple(json.loads(json.dumps(record, sort_keys=True)) for record in records)
        self.checker_version = checker_version

    @classmethod
    def from_fixture(cls, path: str | Path, *, checker_version: str = CHECKER_VERSION) -> ClinicalTrialsAdapter:
        return cls(path, checker_version=checker_version)

    from_path = from_fixture

    @property
    def source_hashes(self) -> dict[str, str]:
        return dict(self._hashes)

    def check(self, claim: ClinicalTrialsClaim | Mapping[str, Any], *, checker_version: str | None = None) -> ClinicalTrialsOutcome:
        checker_version = checker_version or self.checker_version
        try:
            parsed = claim if isinstance(claim, ClinicalTrialsClaim) else ClinicalTrialsClaim.from_mapping(claim)
            return self._check_valid(parsed, checker_version=checker_version)
        except FixtureCorruption as exc:
            return self._error(claim, "CORRUPT_EVIDENCE", str(exc), checker_version)
        except (TypeError, ValueError) as exc:
            # Foreign world claims and malformed claim objects are explicit
            # checker errors, never guessed matches or ordinary rejections.
            return self._error(claim, "CROSS_WORLD_OR_MALFORMED_INPUT", str(exc), checker_version)
        except Exception as exc:  # noqa: BLE001  # pragma: no cover - fail closed
            return self._error(claim, "UNEXPECTED_ADAPTER_FAILURE", str(exc), checker_version)

    verify = check

    def _check_valid(self, claim: ClinicalTrialsClaim, *, checker_version: str) -> ClinicalTrialsOutcome:
        as_of = _parse_utc(claim.as_of)
        ct = [r for r in self._records if r["source"] == "clinicaltrials-gov-api-v2" and r["nct_id"] == claim.nct_id]
        sec = [r for r in self._records if r["source"] == "sec-edgar-submissions-and-archives" and r.get("sec_accession") == claim.sec_accession]
        if not ct or not sec:
            return self._finish(claim, OutcomeKind.INCONCLUSIVE, "IDENTITY_NOT_RESOLVED", "The exact NCT and SEC accession could not both be resolved.", (), None, checker_version)
        eligible_ct = [r for r in ct if _parse_utc(r["accepted_at"]) <= as_of]
        eligible_sec = [r for r in sec if _parse_utc(r["accepted_at"]) <= as_of]
        if not eligible_ct or not eligible_sec:
            return self._finish(claim, OutcomeKind.INCONCLUSIVE, "POST_CUTOFF_EVIDENCE", "Required source records were accepted after the asserted disclosure timestamp.", (), None, checker_version)
        if len(eligible_ct) != 1 or len(eligible_sec) != 1:
            return self._finish(claim, OutcomeKind.INCONCLUSIVE, "AMBIGUOUS_IDENTITY", "More than one eligible source record matched the requested identifier.", (), None, checker_version)
        ct_row, sec_row = eligible_ct[0], eligible_sec[0]
        if not (_same_text(claim.sponsor, ct_row["sponsor"]) and _same_text(claim.sponsor, sec_row["sponsor"])):
            return self._finish(claim, OutcomeKind.REJECTED, "SPONSOR_MISMATCH", "The declared sponsor does not match both timestamped source records.", (ct_row["record_id"], sec_row["record_id"]), "CTSEC.IDENTITY.01", checker_version)
        if not (_same_text(claim.intervention, ct_row["intervention"]) and _same_text(claim.intervention, sec_row["intervention"])):
            return self._finish(claim, OutcomeKind.REJECTED, "INTERVENTION_MISMATCH", "The declared intervention does not match both timestamped source records.", (ct_row["record_id"], sec_row["record_id"]), "CTSEC.IDENTITY.02", checker_version)
        if claim.cik is not None and claim.cik != sec_row["cik"]:
            return self._finish(claim, OutcomeKind.REJECTED, "CIK_MISMATCH", "The declared SEC CIK does not match the frozen filing metadata.", (sec_row["record_id"],), "CTSEC.IDENTITY.03", checker_version)
        if claim.exhibit_locator != sec_row["exhibit_locator"]:
            return self._finish(claim, OutcomeKind.REJECTED, "EXHIBIT_LOCATOR_MISMATCH", "The exhibit locator is not the human-confirmed locator in the frozen ledger.", (sec_row["record_id"],), "CTSEC.SPAN.01", checker_version)
        if claim.asserted_span_sha256 != sec_row["asserted_span_sha256"]:
            return self._finish(claim, OutcomeKind.REJECTED, "ASSERTED_SPAN_MISMATCH", "The asserted span hash differs from the human-confirmed span metadata.", (sec_row["record_id"],), "CTSEC.SPAN.02", checker_version)
        evidence = {"registry_record_id": ct_row["record_id"], "sec_record_id": sec_row["record_id"], "nct_id": ct_row["nct_id"], "cik": sec_row["cik"], "sec_accession": sec_row["sec_accession"], "exhibit_locator": sec_row["exhibit_locator"], "span_locator": sec_row["span_locator"], "asserted_span_sha256": sec_row["asserted_span_sha256"], "human_confirmed": True, "as_of": claim.as_of}
        return self._finish(claim, OutcomeKind.ACCEPTED_CONDITIONALLY, "REGISTERED_DISCLOSURE_CONSISTENT", "The human-confirmed disclosure locator and span are consistent with timestamped registry identity.", (ct_row["record_id"], sec_row["record_id"]), "CTSEC.CONSISTENCY.01", checker_version, evidence=evidence)

    def _finish(self, claim: ClinicalTrialsClaim, verdict: OutcomeKind, reason_code: str, message: str, citations: Sequence[str], rule: str | None, checker_version: str, *, evidence: Mapping[str, Any] | None = None) -> ClinicalTrialsOutcome:
        receipt = _receipt(claim, verdict, reason_code, message, hashes=self._hashes, citations=citations, winning_rule=rule, checker_version=checker_version, evidence=evidence)
        return ClinicalTrialsOutcome(verdict, reason_code, message, claim.as_dict(), winning_rule=rule, citations=tuple(citations), snapshot_hashes=self._hashes, receipt=receipt, evidence_payload=evidence)

    def _error(self, claim: Any, reason_code: str, message: str, checker_version: str) -> ClinicalTrialsOutcome:
        try:
            parsed = claim if isinstance(claim, ClinicalTrialsClaim) else ClinicalTrialsClaim.from_mapping(claim)
            payload = parsed.as_dict()
        except Exception:  # noqa: BLE001 - error receipts must survive malformed objects
            payload = dict(claim) if isinstance(claim, Mapping) else {"unparsed": repr(claim)}
        receipt_body = {"schema_version": "2.0.0", "world_id": WORLD_ID, "world_version": WORLD_VERSION, "verdict": OutcomeKind.CHECKER_ERROR.value, "outcome": OutcomeKind.CHECKER_ERROR.value, "reason_code": reason_code, "message": message, "claim": payload, "snapshot_hashes": dict(sorted(self._hashes.items())), "checker_version": checker_version, "citations": []}
        receipt = {"receipt_version": "2", "receipt_id": _digest(receipt_body), "canonical_payload": receipt_body}
        return ClinicalTrialsOutcome(OutcomeKind.CHECKER_ERROR, reason_code, message, payload, snapshot_hashes=self._hashes, receipt=receipt)


def check_clinical_trials_claim(claim: ClinicalTrialsClaim | Mapping[str, Any], fixture: Mapping[str, Any] | str | Path, *, checker_version: str = CHECKER_VERSION) -> ClinicalTrialsOutcome:
    """Convenience function used by scripts and future registry wiring."""
    if isinstance(claim, (str, Path)) and isinstance(fixture, Mapping):
        claim, fixture = fixture, claim
    try:
        return ClinicalTrialsAdapter(fixture).check(claim, checker_version=checker_version)
    except Exception as exc:  # noqa: BLE001 - corrupt fixture construction fails closed
        payload = dict(claim) if isinstance(claim, Mapping) else None
        body = {"schema_version": "2.0.0", "world_id": WORLD_ID, "world_version": WORLD_VERSION, "verdict": OutcomeKind.CHECKER_ERROR.value, "outcome": OutcomeKind.CHECKER_ERROR.value, "reason_code": "CORRUPT_EVIDENCE", "message": str(exc), "claim": payload, "snapshot_hashes": {}, "citations": [], "checker_version": checker_version}
        return ClinicalTrialsOutcome(OutcomeKind.CHECKER_ERROR, "CORRUPT_EVIDENCE", str(exc), payload or {}, snapshot_hashes={}, receipt={"receipt_version": "2", "receipt_id": _digest(body), "canonical_payload": body})


def validate_fixture(path: str | Path) -> dict[str, Any]:
    """Return compact provenance for a validated fixture without raw text."""
    fixture = load_fixture(path)
    return {"world_id": WORLD_ID, "version": WORLD_VERSION, "record_count": len(fixture["records"]), "source_hashes": dict(sorted(fixture["source_hashes"].items())), "human_confirmed_sec_spans": sum(row.get("source") == "sec-edgar-submissions-and-archives" and row.get("human_confirmed") is True for row in fixture["records"]), "raw_text_included": False}


__all__ = ["CLINICAL_TRIALS_WORLD_ID", "CLINICAL_TRIALS_WORLD_VERSION", "ClinicalTrialsAdapter", "ClinicalTrialsClaim", "ClinicalTrialsIntegrityError", "ClinicalTrialsOutcome", "ClinicalTrialsResult", "FixtureCorruption", "OutcomeKind", "check_clinical_trials_claim", "load_fixture", "validate_fixture"]
