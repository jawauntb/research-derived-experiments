"""Deterministic commitment-level memory influence and lifecycle runtime."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Self, cast


class MemoryStatus(str, Enum):
    ACTIVE = "active"
    QUARANTINED = "quarantined"
    RETIRED = "retired"
    REVALIDATING = "revalidating"


LEGAL_TRANSITIONS = {
    MemoryStatus.ACTIVE: {MemoryStatus.QUARANTINED},
    MemoryStatus.QUARANTINED: {MemoryStatus.REVALIDATING},
    MemoryStatus.REVALIDATING: {MemoryStatus.ACTIVE, MemoryStatus.RETIRED},
    MemoryStatus.RETIRED: {MemoryStatus.REVALIDATING},
}


@dataclass(frozen=True)
class MemoryItem:
    memory_id: str
    kind: str
    content_action: str | None
    provenance: tuple[str, ...]
    valid_regimes: tuple[str, ...]
    descendant_ids: tuple[str, ...]
    status: MemoryStatus = MemoryStatus.ACTIVE

    def __post_init__(self) -> None:
        if not self.memory_id or not self.kind:
            raise ValueError("memory identifiers and kind must be non-empty")
        if not self.provenance or not self.valid_regimes:
            raise ValueError("memory requires provenance and a declared valid scope")
        if len(self.descendant_ids) != len(set(self.descendant_ids)):
            raise ValueError("memory descendant IDs must be unique")
        if self.memory_id in self.descendant_ids:
            raise ValueError("memory cannot be its own descendant")

    @classmethod
    def from_dict(cls, raw: object) -> Self:
        if not isinstance(raw, dict):
            raise ValueError("memory item must be an object")
        expected = {
            "memory_id",
            "kind",
            "content_action",
            "provenance",
            "valid_regimes",
            "descendant_ids",
        }
        if set(raw) != expected:
            raise ValueError(f"memory fields must be exactly {sorted(expected)}")
        memory_id = raw.get("memory_id")
        kind = raw.get("kind")
        action = raw.get("content_action")
        provenance = raw.get("provenance")
        valid_regimes = raw.get("valid_regimes")
        descendant_ids = raw.get("descendant_ids")
        if not isinstance(memory_id, str) or not isinstance(kind, str):
            raise ValueError("memory identifiers must be strings")
        if action is not None and not isinstance(action, str):
            raise ValueError("memory content_action must be a string or null")
        lists = (provenance, valid_regimes, descendant_ids)
        if not all(
            isinstance(values, list)
            and all(isinstance(value, str) and value for value in values)
            for values in lists
        ):
            raise ValueError("memory provenance, scope, and descendants must be string lists")
        assert isinstance(provenance, list)
        assert isinstance(valid_regimes, list)
        assert isinstance(descendant_ids, list)
        return cls(
            memory_id=memory_id,
            kind=kind,
            content_action=action,
            provenance=tuple(cast(str, value) for value in provenance),
            valid_regimes=tuple(cast(str, value) for value in valid_regimes),
            descendant_ids=tuple(cast(str, value) for value in descendant_ids),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "memory_id": self.memory_id,
            "kind": self.kind,
            "content_action": self.content_action,
            "provenance": list(self.provenance),
            "valid_regimes": list(self.valid_regimes),
            "descendant_ids": list(self.descendant_ids),
            "status": self.status.value,
        }


@dataclass(frozen=True)
class Regime:
    regime_id: str
    default_action: str
    required_action: str

    def __post_init__(self) -> None:
        if not self.regime_id or not self.default_action or not self.required_action:
            raise ValueError("regime fields must be non-empty")


@dataclass(frozen=True)
class MemoryEvent:
    event_index: int
    memory_id: str
    status_before: MemoryStatus
    status_after: MemoryStatus
    reason: str
    evidence_ref: str
    timestamp_logical: int

    def to_dict(self) -> dict[str, object]:
        return {
            "event_index": self.event_index,
            "memory_id": self.memory_id,
            "status_before": self.status_before.value,
            "status_after": self.status_after.value,
            "reason": self.reason,
            "evidence_ref": self.evidence_ref,
            "timestamp_logical": self.timestamp_logical,
        }


@dataclass(frozen=True)
class MemoryLedger:
    items: tuple[MemoryItem, ...]
    events: tuple[MemoryEvent, ...] = ()

    def __post_init__(self) -> None:
        ids = [item.memory_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("memory ledger IDs must be unique")
        known = set(ids)
        for item in self.items:
            missing = set(item.descendant_ids) - known
            if missing:
                raise ValueError(f"memory descendants are unresolved: {sorted(missing)}")
        for index, event in enumerate(self.events):
            if event.event_index != index or event.timestamp_logical != index:
                raise ValueError("memory events must have contiguous index and logical time")

    @classmethod
    def load(cls, path: Path) -> tuple[Self, dict[str, Regime]]:
        raw = json.loads(path.read_text())
        if not isinstance(raw, dict) or set(raw) != {
            "schema_version",
            "memory_items",
            "regimes",
        }:
            raise ValueError("unlearning fixture has an invalid root shape")
        if raw["schema_version"] != "1.0":
            raise ValueError("unlearning fixture has an unsupported schema")
        raw_items = raw["memory_items"]
        raw_regimes = raw["regimes"]
        if not isinstance(raw_items, list) or not isinstance(raw_regimes, dict):
            raise ValueError("unlearning fixture items/regimes have invalid types")
        ledger = cls(tuple(MemoryItem.from_dict(item) for item in raw_items))
        regimes: dict[str, Regime] = {}
        for regime_id, value in raw_regimes.items():
            if not isinstance(regime_id, str) or not isinstance(value, dict):
                raise ValueError("regime entries must be named objects")
            if set(value) != {"default_action", "required_action"}:
                raise ValueError("regime requires default_action and required_action")
            default_action = value.get("default_action")
            required_action = value.get("required_action")
            if not isinstance(default_action, str) or not isinstance(required_action, str):
                raise ValueError("regime actions must be strings")
            regimes[regime_id] = Regime(regime_id, default_action, required_action)
        return ledger, regimes

    def item(self, memory_id: str) -> MemoryItem:
        try:
            return next(item for item in self.items if item.memory_id == memory_id)
        except StopIteration as exc:
            raise ValueError(f"unknown memory item: {memory_id}") from exc

    def family_ids(self, memory_id: str) -> frozenset[str]:
        discovered = {memory_id}
        frontier = [memory_id]
        while frontier:
            current = self.item(frontier.pop())
            for descendant_id in current.descendant_ids:
                if descendant_id not in discovered:
                    discovered.add(descendant_id)
                    frontier.append(descendant_id)
        return frozenset(discovered)

    def transition_family(
        self,
        memory_id: str,
        status_after: MemoryStatus,
        *,
        reason: str,
        evidence_ref: str,
    ) -> Self:
        if not reason or not evidence_ref:
            raise ValueError("memory transition requires reason and evidence")
        family = self.family_ids(memory_id)
        updated: list[MemoryItem] = []
        events = list(self.events)
        for item in self.items:
            if item.memory_id not in family:
                updated.append(item)
                continue
            if status_after not in LEGAL_TRANSITIONS[item.status]:
                raise ValueError(
                    f"illegal memory transition: {item.status.value}->{status_after.value}"
                )
            events.append(
                MemoryEvent(
                    event_index=len(events),
                    memory_id=item.memory_id,
                    status_before=item.status,
                    status_after=status_after,
                    reason=reason,
                    evidence_ref=evidence_ref,
                    timestamp_logical=len(events),
                )
            )
            updated.append(replace(item, status=status_after))
        return type(self)(tuple(updated), tuple(events))

    def to_dict(self) -> dict[str, object]:
        return {
            "items": [item.to_dict() for item in self.items],
            "events": [event.to_dict() for event in self.events],
        }


@dataclass(frozen=True)
class CommitmentOutcome:
    regime_id: str
    action: str
    required_action: str
    retrieved_memory_ids: tuple[str, ...]
    task_success: bool
    critical_violation: bool
    joint_success: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "regime_id": self.regime_id,
            "action": self.action,
            "required_action": self.required_action,
            "retrieved_memory_ids": list(self.retrieved_memory_ids),
            "task_success": self.task_success,
            "critical_violation": self.critical_violation,
            "joint_success": self.joint_success,
        }


class MemoryCommitHarness:
    def commit(
        self,
        ledger: MemoryLedger,
        regime: Regime,
        *,
        suppressed_ids: frozenset[str] = frozenset(),
        probe: bool = False,
    ) -> CommitmentOutcome:
        eligible_status = MemoryStatus.REVALIDATING if probe else MemoryStatus.ACTIVE
        retrieved = tuple(
            item
            for item in ledger.items
            if item.status is eligible_status
            and item.memory_id not in suppressed_ids
            and item.content_action is not None
        )
        actions = {item.content_action for item in retrieved}
        if len(actions) > 1:
            raise RuntimeError("fixture retrieved conflicting memory actions")
        action = cast(str, next(iter(actions))) if actions else regime.default_action
        task_success = action == regime.required_action
        return CommitmentOutcome(
            regime_id=regime.regime_id,
            action=action,
            required_action=regime.required_action,
            retrieved_memory_ids=tuple(item.memory_id for item in retrieved),
            task_success=task_success,
            critical_violation=not task_success,
            joint_success=task_success,
        )


@dataclass(frozen=True)
class CausalUseGate:
    observed: CommitmentOutcome
    target_only_suppressed: CommitmentOutcome
    target_family_suppressed: CommitmentOutcome
    placebo_suppressed: CommitmentOutcome
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "observed": self.observed.to_dict(),
            "target_only_suppressed": self.target_only_suppressed.to_dict(),
            "target_family_suppressed": self.target_family_suppressed.to_dict(),
            "placebo_suppressed": self.placebo_suppressed.to_dict(),
            "target_effect": int(self.target_family_suppressed.joint_success)
            - int(self.observed.joint_success),
            "placebo_effect": int(self.placebo_suppressed.joint_success)
            - int(self.observed.joint_success),
            "descendant_leak_detected": not self.target_only_suppressed.joint_success,
            "passed": self.passed,
        }


def evaluate_causal_use(
    ledger: MemoryLedger,
    regime: Regime,
    *,
    target_memory_id: str,
    placebo_memory_id: str,
) -> CausalUseGate:
    harness = MemoryCommitHarness()
    observed = harness.commit(ledger, regime)
    target_only = harness.commit(
        ledger,
        regime,
        suppressed_ids=frozenset({target_memory_id}),
    )
    target_family = harness.commit(
        ledger,
        regime,
        suppressed_ids=ledger.family_ids(target_memory_id),
    )
    placebo = harness.commit(
        ledger,
        regime,
        suppressed_ids=frozenset({placebo_memory_id}),
    )
    passed = (
        not observed.joint_success
        and not target_only.joint_success
        and target_family.joint_success
        and placebo == observed
    )
    return CausalUseGate(observed, target_only, target_family, placebo, passed)
