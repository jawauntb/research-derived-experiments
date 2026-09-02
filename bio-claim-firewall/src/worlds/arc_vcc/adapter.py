"""Fail-closed Arc VCC H1 measurement adapter.

The adapter is deliberately a small measurement checker, not a virtual-cell
 model runner. It reads a hash-bound JSONL fixture derived from Arc's official
 committed real H1 sample, derives direction from the
signed summary statistic and frozen threshold, and emits a stable receipt
payload.  No State code, weights, predictions, or benchmark artifacts are
accepted by this module.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from audit import canonicalize_for_hash

from worlds.registry import (
    WorldRegistryError,
    get_world,
    receipt_world_digest,
    validate_world_artifacts,
)

ARC_VCC_WORLD_ID = "arc-vcc"
ARC_VCC_WORLD_VERSION = "2025-h1-measurements"
ARC_VCC_SCHEMA_VERSION = "arc-vcc-claim-v1"
ARC_VCC_RULE_VERSION = "arc-vcc-rules-v1"
ARC_VCC_SOURCE_ID = "arc-cell-eval2-h1-vcc-real-subset"
ARC_VCC_SOURCE_COMMIT = "ddfc5df73c997b2f113a560bd863fb068f2b453a"
ARC_VCC_OFFICIAL_URL = (
    "https://raw.githubusercontent.com/ArcInstitute/cell-eval2/"
    f"{ARC_VCC_SOURCE_COMMIT}/docs/data/H1-VCC-2025-training.h5ad"
)
_FIXTURE_SCHEMA_VERSION = "arc-vcc-measurement-ledger-0.1"
_DIRECTIONS = frozenset({"increases", "decreases", "null"})
_SPLITS = frozenset({"development", "locked_holdout"})
_HEX64 = set("0123456789abcdef")

Direction = Literal["increases", "decreases", "null"]
Outcome = Literal["ACCEPTED", "REJECTED", "INCONCLUSIVE", "CHECKER_ERROR"]


class ArcVCCIntegrityError(ValueError):
    """The Arc fixture is absent, malformed, or changed after freezing."""


def _canonical_json(value: Any) -> bytes:
    return canonicalize_for_hash(value)


def _world_digest(source_hashes: Mapping[str, str]) -> str:
    world = get_world(ARC_VCC_WORLD_ID, ARC_VCC_WORLD_VERSION)
    return receipt_world_digest(world, source_hashes)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ArcVCCIntegrityError(f"{field} must be a non-empty string")
    return value.strip()


def _require_sha(value: Any, field: str) -> str:
    value = _require_text(value, field).lower()
    if len(value) != 64 or set(value) - _HEX64:
        raise ArcVCCIntegrityError(f"{field} must be a lowercase sha256 digest")
    return value


def _finite_number(value: Any, field: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
    ):
        raise ArcVCCIntegrityError(f"{field} must be a finite number")
    return float(value)


def _direction(value: Any) -> Direction:
    value = _require_text(value, "direction").casefold()
    if value not in _DIRECTIONS:
        raise ArcVCCIntegrityError(f"unsupported direction {value!r}")
    return cast(Direction, value)


@dataclass(frozen=True, slots=True)
class FixtureMetadata:
    """Provenance and frozen split information for an Arc fixture."""

    world_id: str
    world_version: str
    schema_version: str
    source_id: str
    official_url: str
    license: str
    release: str
    retrieval_at: str
    measurement_sha256: str
    raw_source_sha256: str
    raw_source_bytes: int
    source_commit: str
    row_count: int
    assay: str
    statistic: str
    threshold: float
    tuning_split: str
    evaluation_split: str
    source_kind: str
    provenance_note: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> FixtureMetadata:
        required = {
            "world_id",
            "world_version",
            "schema_version",
            "source_id",
            "official_url",
            "license",
            "release",
            "retrieval_at",
            "measurement_sha256",
            "row_count",
            "assay",
            "statistic",
            "threshold",
            "tuning_split",
            "evaluation_split",
            "source_kind",
            "provenance_note",
            "raw_source_sha256",
            "raw_source_bytes",
            "source_commit",
        }
        missing = sorted(required - set(raw))
        if missing:
            raise ArcVCCIntegrityError(f"metadata missing required fields: {missing}")
        row_count = raw["row_count"]
        if (
            isinstance(row_count, bool)
            or not isinstance(row_count, int)
            or row_count < 1
        ):
            raise ArcVCCIntegrityError("row_count must be a positive integer")
        raw_source_bytes = raw["raw_source_bytes"]
        if (
            isinstance(raw_source_bytes, bool)
            or not isinstance(raw_source_bytes, int)
            or raw_source_bytes < 1
        ):
            raise ArcVCCIntegrityError("raw_source_bytes must be a positive integer")
        metadata = cls(
            world_id=_require_text(raw["world_id"], "world_id"),
            world_version=_require_text(raw["world_version"], "world_version"),
            schema_version=_require_text(raw["schema_version"], "schema_version"),
            source_id=_require_text(raw["source_id"], "source_id"),
            official_url=_require_text(raw["official_url"], "official_url"),
            license=_require_text(raw["license"], "license"),
            release=_require_text(raw["release"], "release"),
            retrieval_at=_require_text(raw["retrieval_at"], "retrieval_at"),
            measurement_sha256=_require_sha(
                raw["measurement_sha256"], "measurement_sha256"
            ),
            raw_source_sha256=_require_sha(
                raw["raw_source_sha256"], "raw_source_sha256"
            ),
            raw_source_bytes=raw_source_bytes,
            source_commit=_require_text(raw["source_commit"], "source_commit"),
            row_count=row_count,
            assay=_require_text(raw["assay"], "assay"),
            statistic=_require_text(raw["statistic"], "statistic"),
            threshold=_finite_number(raw["threshold"], "threshold"),
            tuning_split=_require_text(raw["tuning_split"], "tuning_split"),
            evaluation_split=_require_text(raw["evaluation_split"], "evaluation_split"),
            source_kind=_require_text(raw["source_kind"], "source_kind"),
            provenance_note=_require_text(raw["provenance_note"], "provenance_note"),
        )
        if metadata.official_url != ARC_VCC_OFFICIAL_URL:
            raise ArcVCCIntegrityError(
                "fixture source URL is not the registered Arc VCC release"
            )
        if metadata.source_id != ARC_VCC_SOURCE_ID:
            raise ArcVCCIntegrityError(
                "fixture source identity is not the registered Arc VCC release"
            )
        if metadata.license != "MIT":
            raise ArcVCCIntegrityError(
                "Arc fixture requires the source repository's MIT license"
            )
        if metadata.schema_version != _FIXTURE_SCHEMA_VERSION:
            raise ArcVCCIntegrityError("unsupported Arc fixture schema version")
        if metadata.source_kind != "official_real_subset":
            raise ArcVCCIntegrityError("unsupported Arc fixture source kind")
        if metadata.source_commit != ARC_VCC_SOURCE_COMMIT:
            raise ArcVCCIntegrityError(
                "Arc fixture source commit is not the registered release"
            )
        if (
            metadata.tuning_split not in _SPLITS
            or metadata.evaluation_split not in _SPLITS
        ):
            raise ArcVCCIntegrityError("metadata declares an unknown split")
        if metadata.tuning_split == metadata.evaluation_split:
            raise ArcVCCIntegrityError("tuning and evaluation splits must differ")
        if metadata.threshold < 0:
            raise ArcVCCIntegrityError("threshold must be non-negative")
        return metadata

    def as_dict(self) -> dict[str, Any]:
        return {
            "world_id": self.world_id,
            "world_version": self.world_version,
            "schema_version": self.schema_version,
            "source_id": self.source_id,
            "official_url": self.official_url,
            "license": self.license,
            "release": self.release,
            "retrieval_at": self.retrieval_at,
            "measurement_sha256": self.measurement_sha256,
            "raw_source_sha256": self.raw_source_sha256,
            "raw_source_bytes": self.raw_source_bytes,
            "source_commit": self.source_commit,
            "row_count": self.row_count,
            "assay": self.assay,
            "statistic": self.statistic,
            "threshold": self.threshold,
            "tuning_split": self.tuning_split,
            "evaluation_split": self.evaluation_split,
            "source_kind": self.source_kind,
            "provenance_note": self.provenance_note,
        }


@dataclass(frozen=True, slots=True)
class Measurement:
    measurement_id: str
    perturbed_gene: str
    response_gene: str
    assay: str
    split: str
    summary_statistic: str
    value: float
    direction: Direction
    source_row: str
    perturbed_cells: int
    control_cells: int

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any], *, threshold: float) -> Measurement:
        required = {
            "measurement_id",
            "perturbed_gene",
            "response_gene",
            "assay",
            "split",
            "summary_statistic",
            "value",
            "direction",
            "source_row",
            "perturbed_cells",
            "control_cells",
        }
        missing = sorted(required - set(raw))
        if missing:
            raise ArcVCCIntegrityError(
                f"measurement missing required fields: {missing}"
            )
        perturbed_cells = raw["perturbed_cells"]
        control_cells = raw["control_cells"]
        for value, field in (
            (perturbed_cells, "perturbed_cells"),
            (control_cells, "control_cells"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 2:
                raise ArcVCCIntegrityError(f"{field} must be an integer of at least 2")
        measurement = cls(
            measurement_id=_require_text(raw["measurement_id"], "measurement_id"),
            perturbed_gene=_require_text(raw["perturbed_gene"], "perturbed_gene"),
            response_gene=_require_text(raw["response_gene"], "response_gene"),
            assay=_require_text(raw["assay"], "assay"),
            split=_require_text(raw["split"], "split"),
            summary_statistic=_require_text(
                raw["summary_statistic"], "summary_statistic"
            ),
            value=_finite_number(raw["value"], "value"),
            direction=_direction(raw["direction"]),
            source_row=_require_text(raw["source_row"], "source_row"),
            perturbed_cells=perturbed_cells,
            control_cells=control_cells,
        )
        derived: Direction = (
            "increases"
            if measurement.value > threshold
            else "decreases"
            if measurement.value < -threshold
            else "null"
        )
        if measurement.direction != derived:
            raise ArcVCCIntegrityError(
                f"measurement {measurement.measurement_id!r} has an inconsistent direction"
            )
        if measurement.split not in _SPLITS:
            raise ArcVCCIntegrityError(
                f"measurement {measurement.measurement_id!r} has an unknown split"
            )
        return measurement

    def as_dict(self) -> dict[str, Any]:
        return {
            "measurement_id": self.measurement_id,
            "perturbed_gene": self.perturbed_gene,
            "response_gene": self.response_gene,
            "assay": self.assay,
            "split": self.split,
            "summary_statistic": self.summary_statistic,
            "value": self.value,
            "direction": self.direction,
            "source_row": self.source_row,
            "perturbed_cells": self.perturbed_cells,
            "control_cells": self.control_cells,
        }


@dataclass(frozen=True, slots=True)
class ArcVCCClaim:
    perturbed_gene: str
    response_gene: str
    summary_statistic: str
    direction: Direction
    threshold: float
    assay: str
    split: str
    world_id: str = ARC_VCC_WORLD_ID
    world_version: str = ARC_VCC_WORLD_VERSION

    @classmethod
    def from_mapping(
        cls,
        raw: Mapping[str, Any],
        *,
        expected_world_id: str = ARC_VCC_WORLD_ID,
        expected_world_version: str = ARC_VCC_WORLD_VERSION,
    ) -> ArcVCCClaim:
        if not isinstance(raw, Mapping):
            raise TypeError("Arc VCC claim must be an object")
        required = {
            "perturbed_gene",
            "response_gene",
            "summary_statistic",
            "direction",
            "threshold",
            "assay",
            "split",
        }
        missing = sorted(required - set(raw))
        if missing:
            raise ValueError(f"Arc VCC claim missing required fields: {missing}")
        world_id = raw.get("world_id", expected_world_id)
        world_version = raw.get("world_version", expected_world_version)
        if world_id != expected_world_id or world_version != expected_world_version:
            raise ArcVCCIntegrityError(
                "claim world identity does not match the selected Arc VCC fixture"
            )
        split = _require_text(raw["split"], "split")
        if split not in _SPLITS:
            raise ValueError(f"unsupported split {split!r}")
        return cls(
            perturbed_gene=_require_text(raw["perturbed_gene"], "perturbed_gene"),
            response_gene=_require_text(raw["response_gene"], "response_gene"),
            summary_statistic=_require_text(
                raw["summary_statistic"], "summary_statistic"
            ),
            direction=_direction(raw["direction"]),
            threshold=_finite_number(raw["threshold"], "threshold"),
            assay=_require_text(raw["assay"], "assay"),
            split=split,
            world_id=world_id,
            world_version=world_version,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "world_id": self.world_id,
            "world_version": self.world_version,
            "perturbed_gene": self.perturbed_gene,
            "response_gene": self.response_gene,
            "summary_statistic": self.summary_statistic,
            "direction": self.direction,
            "threshold": self.threshold,
            "assay": self.assay,
            "split": self.split,
        }


@dataclass(frozen=True, slots=True)
class ArcVCCResult:
    outcome: Outcome
    claim: dict[str, Any] | None
    evidence: dict[str, Any] | None
    reason: str
    winning_rule: dict[str, str] | None
    world_id: str
    world_version: str
    source_hashes: dict[str, str]
    receipt: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.outcome,
            "claim": self.claim,
            "evidence": self.evidence,
            "reason": self.reason,
            "winning_rule": self.winning_rule,
            "world_id": self.world_id,
            "world_version": self.world_version,
            "source_hashes": dict(self.source_hashes),
            "receipt": self.receipt,
        }


@dataclass(frozen=True, slots=True)
class _Fixture:
    metadata: FixtureMetadata
    measurements: tuple[Measurement, ...]
    source_hashes: dict[str, str]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArcVCCIntegrityError(
            f"cannot read JSON fixture file {path}: {exc}"
        ) from exc


def _read_measurements(path: Path, *, threshold: float) -> tuple[Measurement, ...]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ArcVCCIntegrityError(
            f"cannot read measurement ledger {path}: {exc}"
        ) from exc
    rows: list[Measurement] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ArcVCCIntegrityError(
                f"malformed measurement JSON at line {line_number}"
            ) from exc
        if not isinstance(raw, Mapping):
            raise ArcVCCIntegrityError(
                f"measurement line {line_number} is not an object"
            )
        rows.append(Measurement.from_mapping(raw, threshold=threshold))
    return tuple(rows)


def _validate_rows(metadata: FixtureMetadata, rows: tuple[Measurement, ...]) -> None:
    if len(rows) != metadata.row_count:
        raise ArcVCCIntegrityError(
            f"metadata row_count={metadata.row_count} but ledger has {len(rows)} rows"
        )
    ids = [row.measurement_id for row in rows]
    if len(set(ids)) != len(ids):
        raise ArcVCCIntegrityError("measurement ids must be unique")
    keys: dict[tuple[str, str, str, str], str] = {}
    for row in rows:
        key = (row.perturbed_gene, row.response_gene, row.assay, row.summary_statistic)
        previous = keys.get(key)
        if previous is not None and previous != row.split:
            raise ArcVCCIntegrityError(f"split leakage for measurement key {key!r}")
        keys[key] = row.split
        if row.assay != metadata.assay or row.summary_statistic != metadata.statistic:
            raise ArcVCCIntegrityError(
                "fixture contains an assay/statistic outside its declared scope"
            )


def load_fixture(root: Path) -> _Fixture:
    """Load a compact Arc fixture and verify every retained byte and row."""
    root = Path(root)
    metadata_path = root / "metadata.json"
    measurements_path = root / "measurements.jsonl"
    if not metadata_path.is_file() or not measurements_path.is_file():
        raise ArcVCCIntegrityError(f"Arc fixture is incomplete under {root}")
    raw_metadata = _read_json(metadata_path)
    if not isinstance(raw_metadata, Mapping):
        raise ArcVCCIntegrityError("metadata.json must contain an object")
    metadata = FixtureMetadata.from_mapping(raw_metadata)
    actual_measurement_sha = _sha256(measurements_path)
    if actual_measurement_sha != metadata.measurement_sha256:
        raise ArcVCCIntegrityError(
            "measurement ledger hash does not match fixture metadata"
        )
    rows = _read_measurements(measurements_path, threshold=metadata.threshold)
    _validate_rows(metadata, rows)
    source_hashes = {
        metadata.source_id: metadata.raw_source_sha256,
        "arc-vcc-derived-ledger": actual_measurement_sha,
    }
    bundle_digest = hashlib.sha256(
        _canonical_json(
            {
                "measurement_sha256": actual_measurement_sha,
                "metadata_sha256": _sha256(metadata_path),
            }
        )
    ).hexdigest()
    try:
        validate_world_artifacts(
            get_world(ARC_VCC_WORLD_ID, ARC_VCC_WORLD_VERSION),
            {"arc-vcc-fixture-bundle": bundle_digest},
        )
    except WorldRegistryError as exc:
        raise ArcVCCIntegrityError(str(exc)) from exc
    return _Fixture(metadata=metadata, measurements=rows, source_hashes=source_hashes)


def validate_fixture(root: Path) -> dict[str, Any]:
    """Return deterministic fixture provenance, or raise on any mismatch."""
    fixture = load_fixture(root)
    return {
        "world_id": fixture.metadata.world_id,
        "world_version": fixture.metadata.world_version,
        "schema_version": fixture.metadata.schema_version,
        "row_count": len(fixture.measurements),
        "source_hashes": dict(sorted(fixture.source_hashes.items())),
        "raw_source_bytes": fixture.metadata.raw_source_bytes,
        "source_commit": fixture.metadata.source_commit,
        "license": fixture.metadata.license,
        "official_url": fixture.metadata.official_url,
        "split_counts": {
            split: sum(row.split == split for row in fixture.measurements)
            for split in sorted(_SPLITS)
        },
    }


class ArcVCCAdapter:
    """Bounded deterministic checker for one explicitly selected Arc fixture."""

    def __init__(self, fixture: _Fixture, *, checker_version: str = "0.1.0") -> None:
        if (
            fixture.metadata.world_id != ARC_VCC_WORLD_ID
            or fixture.metadata.world_version != ARC_VCC_WORLD_VERSION
        ):
            raise ArcVCCIntegrityError(
                "fixture world identity is not the registered Arc VCC H1 world"
            )
        self._fixture = fixture
        self.checker_version = checker_version

    @classmethod
    def from_path(cls, root: Path, *, checker_version: str = "0.1.0") -> ArcVCCAdapter:
        return cls(load_fixture(root), checker_version=checker_version)

    @property
    def metadata(self) -> FixtureMetadata:
        return self._fixture.metadata

    @property
    def source_hashes(self) -> dict[str, str]:
        return dict(self._fixture.source_hashes)

    def check(self, claim: ArcVCCClaim | Mapping[str, Any]) -> ArcVCCResult:
        """Check a claim; malformed identity/corrupt fixture always fails closed."""
        try:
            normalized = (
                claim
                if isinstance(claim, ArcVCCClaim)
                else ArcVCCClaim.from_mapping(claim)
            )
            if (
                normalized.world_id != self.metadata.world_id
                or normalized.world_version != self.metadata.world_version
            ):
                raise ArcVCCIntegrityError(
                    "claim world identity does not match fixture"
                )
            return self._evaluate(normalized)
        except ArcVCCIntegrityError as exc:
            return self._result("CHECKER_ERROR", None, None, str(exc), None)
        except (TypeError, ValueError) as exc:
            return self._result("INCONCLUSIVE", None, None, str(exc), None)

    def _evaluate(self, claim: ArcVCCClaim) -> ArcVCCResult:
        if (
            claim.assay != self.metadata.assay
            or claim.summary_statistic != self.metadata.statistic
        ):
            return self._result(
                "INCONCLUSIVE",
                claim,
                None,
                "claim is outside the frozen Arc H1 assay/statistic scope",
                None,
            )
        if not math.isclose(
            claim.threshold, self.metadata.threshold, rel_tol=0.0, abs_tol=1e-12
        ):
            return self._result(
                "INCONCLUSIVE",
                claim,
                None,
                "threshold is not the preregistered frozen decision threshold",
                None,
            )
        matches = tuple(
            row
            for row in self._fixture.measurements
            if row.perturbed_gene == claim.perturbed_gene
            and row.response_gene == claim.response_gene
            and row.assay == claim.assay
            and row.summary_statistic == claim.summary_statistic
            and row.split == claim.split
        )
        if not matches:
            return self._result(
                "INCONCLUSIVE",
                claim,
                None,
                "no measurement exists in the requested Arc H1 split",
                None,
            )
        if len(matches) != 1:
            return self._result(
                "CHECKER_ERROR",
                claim,
                None,
                "fixture has multiple measurements for the exact claim key",
                None,
            )
        row = matches[0]
        evidence = {
            "record_id": row.measurement_id,
            "source_row": row.source_row,
            "observed_direction": row.direction,
            "summary_statistic": row.summary_statistic,
            "value": row.value,
            "threshold": self.metadata.threshold,
            "assay": row.assay,
            "split": row.split,
            "source": self.metadata.source_id,
            "perturbed_cells": row.perturbed_cells,
            "control_cells": row.control_cells,
        }
        if claim.direction == row.direction:
            return self._result(
                "ACCEPTED",
                claim,
                evidence,
                "frozen measurement supports the asserted direction",
                {"id": "ARC-H1-001", "title": "Declared H1 direction matches record"},
            )
        if row.direction == "null":
            return self._result(
                "REJECTED",
                claim,
                evidence,
                "measurement is below the frozen threshold and has no directional response",
                {"id": "ARC-H1-003", "title": "H1 threshold yields null response"},
            )
        return self._result(
            "REJECTED",
            claim,
            evidence,
            "frozen measurement reports the opposite direction",
            {"id": "ARC-H1-002", "title": "Declared H1 direction conflicts"},
        )

    def _result(
        self,
        outcome: Outcome,
        claim: ArcVCCClaim | None,
        evidence: dict[str, Any] | None,
        reason: str,
        winning_rule: dict[str, str] | None,
    ) -> ArcVCCResult:
        claim_dict = claim.as_dict() if claim is not None else None
        payload = {
            "receipt_version": "2",
            "world_id": self.metadata.world_id,
            "world_version": self.metadata.world_version,
            "world_digest": _world_digest(self._fixture.source_hashes),
            "source_hashes": dict(sorted(self._fixture.source_hashes.items())),
            "claim": claim_dict,
            "evidence": evidence,
            "outcome": outcome,
            "reason": reason,
            "winning_rule": winning_rule,
            "checker_version": self.checker_version,
            "rule_version": ARC_VCC_RULE_VERSION,
            "schema_version": ARC_VCC_SCHEMA_VERSION,
        }
        receipt_id = hashlib.sha256(_canonical_json(payload)).hexdigest()
        receipt = {
            "receipt_version": "2",
            "receipt_id": receipt_id,
            "canonical_payload": payload,
        }
        return ArcVCCResult(
            outcome,
            claim_dict,
            evidence,
            reason,
            winning_rule,
            self.metadata.world_id,
            self.metadata.world_version,
            dict(sorted(self._fixture.source_hashes.items())),
            receipt,
        )


def check_arc_vcc_claim(
    root: Path,
    claim: ArcVCCClaim | Mapping[str, Any],
    *,
    checker_version: str = "0.1.0",
) -> ArcVCCResult:
    """Convenience function for callers that keep fixture custody outside git."""
    try:
        return ArcVCCAdapter.from_path(root, checker_version=checker_version).check(
            claim
        )
    except ArcVCCIntegrityError as exc:
        # A receipt-compatible error is useful to batch callers, even when the
        # fixture cannot be loaded far enough to establish its source hashes.
        payload = {
            "receipt_version": "2",
            "world_id": ARC_VCC_WORLD_ID,
            "world_version": ARC_VCC_WORLD_VERSION,
            "source_hashes": {},
            "claim": dict(claim) if isinstance(claim, Mapping) else None,
            "evidence": None,
            "outcome": "CHECKER_ERROR",
            "reason": str(exc),
            "winning_rule": None,
            "checker_version": checker_version,
            "rule_version": ARC_VCC_RULE_VERSION,
            "schema_version": ARC_VCC_SCHEMA_VERSION,
        }
        receipt_id = hashlib.sha256(_canonical_json(payload)).hexdigest()
        receipt = {
            "receipt_version": "2",
            "receipt_id": receipt_id,
            "canonical_payload": payload,
        }
        return ArcVCCResult(
            "CHECKER_ERROR",
            None,
            None,
            str(exc),
            None,
            ARC_VCC_WORLD_ID,
            ARC_VCC_WORLD_VERSION,
            {},
            receipt,
        )


__all__ = [
    "ARC_VCC_OFFICIAL_URL",
    "ARC_VCC_RULE_VERSION",
    "ARC_VCC_SCHEMA_VERSION",
    "ARC_VCC_SOURCE_COMMIT",
    "ARC_VCC_SOURCE_ID",
    "ArcVCCAdapter",
    "ArcVCCClaim",
    "ArcVCCIntegrityError",
    "ArcVCCResult",
    "FixtureMetadata",
    "Measurement",
    "check_arc_vcc_claim",
    "load_fixture",
    "validate_fixture",
]
