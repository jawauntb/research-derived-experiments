"""Dependency-free grounded statechart and deterministic replay runtime.

The fixture runtime intentionally models only the first portfolio exit gate:
Observe -> Act -> Verify -> Commit/Repair. It keeps the executor deterministic
so replay differences can be attributed to one declared harness component.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Self


def canonical_json(value: object) -> str:
    """Serialize public records in the stable representation used for hashes."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


class State(str, Enum):
    OBSERVE = "observe"
    ACT = "act"
    VERIFY = "verify"
    COMMIT = "commit"
    REPAIR = "repair"


@dataclass(frozen=True)
class GuardResult:
    guard: str
    guard_version: str
    independence_level: str
    passed: bool
    evidence_refs: tuple[str, ...]
    explanation: str

    def __post_init__(self) -> None:
        if not self.guard or not self.guard_version or not self.explanation:
            raise ValueError("guard result strings must be non-empty")
        if self.independence_level not in {f"G{level}" for level in range(6)}:
            raise ValueError("independence_level must be G0 through G5")
        if not isinstance(self.passed, bool):
            raise ValueError("guard passed must be boolean")
        if not all(isinstance(ref, str) and ref for ref in self.evidence_refs):
            raise ValueError("guard evidence references must be non-empty strings")

    def to_dict(self) -> dict[str, object]:
        return {
            "guard": self.guard,
            "guard_version": self.guard_version,
            "independence_level": self.independence_level,
            "passed": self.passed,
            "evidence_refs": list(self.evidence_refs),
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class Intervention:
    component: str
    original_digest: str
    replacement_digest: str
    reason: str

    def __post_init__(self) -> None:
        if self.component != "guard" or not self.reason:
            raise ValueError("the fixture intervention must name the guard and a reason")
        for value in (self.original_digest, self.replacement_digest):
            if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
                raise ValueError("intervention digests must be lowercase SHA-256 values")

    def to_dict(self) -> dict[str, str]:
        return {
            "component": self.component,
            "original_digest": self.original_digest,
            "replacement_digest": self.replacement_digest,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class Event:
    run_id: str
    episode_id: str
    event_index: int
    state_before: str
    proposed_transition: str
    actor: str
    event_type: str
    evidence_refs: tuple[str, ...]
    constraint_refs: tuple[str, ...]
    guard_results: tuple[GuardResult, ...]
    intervention: Intervention | None
    state_after: str
    timestamp_logical: int

    def __post_init__(self) -> None:
        string_fields = (
            self.run_id,
            self.episode_id,
            self.actor,
            self.event_type,
        )
        if not all(isinstance(value, str) and value for value in string_fields):
            raise ValueError("event identifiers and labels must be non-empty strings")
        if not isinstance(self.event_index, int) or self.event_index < 0:
            raise ValueError("event_index must be a non-negative integer")
        if not isinstance(self.timestamp_logical, int) or self.timestamp_logical < 0:
            raise ValueError("timestamp_logical must be a non-negative integer")
        states = {state.value for state in State}
        if self.state_before not in states or self.state_after not in states:
            raise ValueError("event state is outside the minimal chart")
        expected_transition = f"{self.state_before}->{self.state_after}"
        if self.proposed_transition != expected_transition:
            raise ValueError("proposed_transition must match the before/after states")
        for refs in (self.evidence_refs, self.constraint_refs):
            if not all(isinstance(ref, str) and ref for ref in refs):
                raise ValueError("event references must be non-empty strings")
        if not all(isinstance(result, GuardResult) for result in self.guard_results):
            raise ValueError("guard_results must contain GuardResult records")
        if self.intervention is not None and not isinstance(self.intervention, Intervention):
            raise ValueError("intervention must be an Intervention record or null")

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "episode_id": self.episode_id,
            "event_index": self.event_index,
            "state_before": self.state_before,
            "proposed_transition": self.proposed_transition,
            "actor": self.actor,
            "event_type": self.event_type,
            "evidence_refs": list(self.evidence_refs),
            "constraint_refs": list(self.constraint_refs),
            "guard_results": [result.to_dict() for result in self.guard_results],
            "intervention": self.intervention.to_dict() if self.intervention else None,
            "state_after": self.state_after,
            "timestamp_logical": self.timestamp_logical,
        }


@dataclass(frozen=True)
class HarnessManifest:
    manifest_id: str
    version: str
    chart: dict[str, tuple[str, ...]]
    guard: dict[str, str]
    repair: dict[str, str]

    def __post_init__(self) -> None:
        self._validate()

    @classmethod
    def load(cls, path: Path) -> Self:
        raw = json.loads(path.read_text())
        required = {"manifest_id", "version", "chart", "guard", "repair"}
        if set(raw) != required:
            raise ValueError(f"manifest fields must be exactly {sorted(required)}")
        chart = raw["chart"]
        guard = raw["guard"]
        repair = raw["repair"]
        if not isinstance(chart, dict) or not all(
            isinstance(state, str)
            and isinstance(targets, list)
            and all(isinstance(target, str) for target in targets)
            for state, targets in chart.items()
        ):
            raise ValueError("chart must map state names to target-state lists")
        if not isinstance(guard, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in guard.items()
        ):
            raise ValueError("guard must be a string map")
        if not isinstance(repair, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in repair.items()
        ):
            raise ValueError("repair must be a string map")
        return cls(
            manifest_id=str(raw["manifest_id"]),
            version=str(raw["version"]),
            chart={state: tuple(targets) for state, targets in chart.items()},
            guard=dict(guard),
            repair=dict(repair),
        )

    def _validate(self) -> None:
        if not self.manifest_id or not self.version:
            raise ValueError("manifest_id and version must be non-empty")
        if not isinstance(self.chart, dict) or not all(
            isinstance(state, str)
            and isinstance(targets, tuple)
            and all(isinstance(target, str) for target in targets)
            for state, targets in self.chart.items()
        ):
            raise ValueError("chart must map state names to target-state tuples")
        for label, values in (("guard", self.guard), ("repair", self.repair)):
            if not isinstance(values, dict) or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in values.items()
            ):
                raise ValueError(f"{label} must be a string map")
        required_states = {state.value for state in State}
        if set(self.chart) != required_states:
            raise ValueError(f"chart states must be exactly {sorted(required_states)}")
        for state, targets in self.chart.items():
            unknown = set(targets) - required_states
            if unknown:
                raise ValueError(f"unknown targets from {state}: {sorted(unknown)}")
        required_edges = {
            ("observe", "act"),
            ("act", "verify"),
            ("verify", "commit"),
            ("verify", "repair"),
            ("repair", "act"),
        }
        actual_edges = {
            (source, target) for source, targets in self.chart.items() for target in targets
        }
        if actual_edges != required_edges:
            raise ValueError("fixture chart must contain only the minimal grounded lifecycle")
        required_guard_fields = {"name", "kind", "version", "independence_level"}
        if set(self.guard) != required_guard_fields:
            raise ValueError(f"guard fields must be exactly {sorted(required_guard_fields)}")
        if self.guard["kind"] not in {"self_report", "artifact_sha256"}:
            raise ValueError(f"unsupported guard kind: {self.guard['kind']}")
        if set(self.repair) != {"kind"} or self.repair["kind"] != "write_expected_artifact":
            raise ValueError("fixture repair must write the expected artifact")

    def to_dict(self) -> dict[str, object]:
        return {
            "manifest_id": self.manifest_id,
            "version": self.version,
            "chart": {state: list(targets) for state, targets in self.chart.items()},
            "guard": dict(self.guard),
            "repair": dict(self.repair),
        }

    @property
    def manifest_digest(self) -> str:
        return digest(self.to_dict())

    @property
    def guard_digest(self) -> str:
        return digest(self.guard)

    def changed_components(self, replacement: HarnessManifest) -> tuple[str, ...]:
        original = self.to_dict()
        changed = [key for key in original if original[key] != replacement.to_dict()[key]]
        return tuple(sorted(changed))


@dataclass(frozen=True)
class Fixture:
    episode_id: str
    task: str
    tool_report: str
    artifact_path: str
    artifact_content: str
    constraint_ref: str

    @classmethod
    def load(cls, path: Path) -> Self:
        raw = json.loads(path.read_text())
        required = {
            "episode_id",
            "task",
            "tool_report",
            "artifact_path",
            "artifact_content",
            "constraint_ref",
        }
        if set(raw) != required or not all(isinstance(raw[key], str) for key in required):
            raise ValueError(f"fixture fields must be exactly {sorted(required)} strings")
        artifact_path = PurePosixPath(raw["artifact_path"])
        if artifact_path.is_absolute() or ".." in artifact_path.parts:
            raise ValueError("artifact_path must be a safe relative path")
        if raw["tool_report"] not in {"success", "failure"}:
            raise ValueError("tool_report must be success or failure")
        return cls(**{key: raw[key] for key in required})

    @property
    def expected_artifact_digest(self) -> str:
        return hashlib.sha256(self.artifact_content.encode()).hexdigest()


class DeterministicWorkspace:
    """Small serializable environment used by checkpoint and replay tests."""

    def __init__(self, files: dict[str, str] | None = None) -> None:
        self._files = dict(files or {})

    def write(self, path: str, content: str) -> None:
        self._files[path] = content

    def sha256(self, path: str) -> str | None:
        content = self._files.get(path)
        return hashlib.sha256(content.encode()).hexdigest() if content is not None else None

    def snapshot(self) -> dict[str, str]:
        return dict(sorted(self._files.items()))


@dataclass(frozen=True)
class Checkpoint:
    run_id: str
    episode_id: str
    event_prefix: tuple[Event, ...]
    workspace_snapshot: dict[str, str]

    def __post_init__(self) -> None:
        if not self.event_prefix:
            raise ValueError("checkpoint requires a non-empty event prefix")
        for expected_index, event in enumerate(self.event_prefix):
            if event.run_id != self.run_id or event.episode_id != self.episode_id:
                raise ValueError("checkpoint event identity does not match the checkpoint")
            if event.event_index != expected_index or event.timestamp_logical != expected_index:
                raise ValueError("checkpoint prefix indices and logical time must be contiguous")
        if not all(
            isinstance(path, str)
            and path
            and isinstance(content, str)
            for path, content in self.workspace_snapshot.items()
        ):
            raise ValueError("checkpoint workspace must be a string map")

    @property
    def state(self) -> State:
        return State(self.event_prefix[-1].state_after)

    @property
    def next_event_index(self) -> int:
        return len(self.event_prefix)

    @property
    def next_logical_timestamp(self) -> int:
        return self.event_prefix[-1].timestamp_logical + 1

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "episode_id": self.episode_id,
            "state": self.state.value,
            "next_event_index": self.next_event_index,
            "next_logical_timestamp": self.next_logical_timestamp,
            "event_prefix": [event.to_dict() for event in self.event_prefix],
            "workspace_snapshot": dict(sorted(self.workspace_snapshot.items())),
        }

    @property
    def checkpoint_digest(self) -> str:
        return digest(self.to_dict())


@dataclass(frozen=True)
class EpisodeOutcome:
    events: tuple[Event, ...]
    terminal_state: State
    task_success: bool
    false_completion: bool
    repair_count: int
    artifact_digest: str | None

    @property
    def event_digest(self) -> str:
        return digest([event.to_dict() for event in self.events])

    def to_dict(self) -> dict[str, object]:
        return {
            "event_digest": self.event_digest,
            "event_count": len(self.events),
            "terminal_state": self.terminal_state.value,
            "task_success": self.task_success,
            "false_completion": self.false_completion,
            "repair_count": self.repair_count,
            "artifact_digest": self.artifact_digest,
        }


class ReplayEngine:
    """Run the minimal chart and replay from its pre-commit checkpoint."""

    def checkpoint_before_verification(
        self,
        fixture: Fixture,
        manifest: HarnessManifest,
    ) -> Checkpoint:
        run_id = f"{fixture.episode_id}:{manifest.manifest_id}:{manifest.version}"
        workspace = DeterministicWorkspace()
        events: list[Event] = []
        events.append(
            self._event(
                fixture=fixture,
                manifest=manifest,
                run_id=run_id,
                event_index=0,
                logical_timestamp=0,
                state_before=State.OBSERVE,
                state_after=State.ACT,
                actor="executor",
                event_type="task_loaded",
                evidence_refs=(f"task://{fixture.episode_id}",),
            )
        )
        events.append(
            self._event(
                fixture=fixture,
                manifest=manifest,
                run_id=run_id,
                event_index=1,
                logical_timestamp=1,
                state_before=State.ACT,
                state_after=State.VERIFY,
                actor="fixture_tool",
                event_type="tool_reported_success",
                evidence_refs=(f"tool-report://{fixture.tool_report}",),
            )
        )
        return Checkpoint(
            run_id=run_id,
            episode_id=fixture.episode_id,
            event_prefix=tuple(events),
            workspace_snapshot=workspace.snapshot(),
        )

    def replay(
        self,
        checkpoint: Checkpoint,
        fixture: Fixture,
        original_manifest: HarnessManifest,
        replacement_manifest: HarnessManifest | None = None,
    ) -> EpisodeOutcome:
        if checkpoint.episode_id != fixture.episode_id or checkpoint.state is not State.VERIFY:
            raise ValueError("checkpoint does not restore this fixture at verify")
        manifest = replacement_manifest or original_manifest
        intervention = None
        if replacement_manifest is not None:
            changed = original_manifest.changed_components(replacement_manifest)
            if changed != ("guard",):
                raise ValueError(
                    "counterfactual replay requires exactly one changed component: guard"
                )
            intervention = Intervention(
                component="guard",
                original_digest=original_manifest.guard_digest,
                replacement_digest=replacement_manifest.guard_digest,
                reason="replace generator self-report with independent artifact evidence",
            )
        workspace = DeterministicWorkspace(checkpoint.workspace_snapshot)
        events = list(checkpoint.event_prefix)
        event_index = checkpoint.next_event_index
        logical_timestamp = checkpoint.next_logical_timestamp
        repair_count = 0

        guard_result = self._evaluate_guard(fixture, manifest, workspace)
        if guard_result.passed:
            events.append(
                self._event(
                    fixture=fixture,
                    manifest=manifest,
                    run_id=checkpoint.run_id,
                    event_index=event_index,
                    logical_timestamp=logical_timestamp,
                    state_before=State.VERIFY,
                    state_after=State.COMMIT,
                    actor="transition_arbiter",
                    event_type="transition_authorized",
                    evidence_refs=guard_result.evidence_refs,
                    guard_results=(guard_result,),
                    intervention=intervention,
                )
            )
        else:
            events.append(
                self._event(
                    fixture=fixture,
                    manifest=manifest,
                    run_id=checkpoint.run_id,
                    event_index=event_index,
                    logical_timestamp=logical_timestamp,
                    state_before=State.VERIFY,
                    state_after=State.REPAIR,
                    actor="transition_arbiter",
                    event_type="transition_rejected",
                    evidence_refs=guard_result.evidence_refs,
                    guard_results=(guard_result,),
                    intervention=intervention,
                )
            )
            event_index += 1
            logical_timestamp += 1
            repair_count += 1
            workspace.write(fixture.artifact_path, fixture.artifact_content)
            events.append(
                self._event(
                    fixture=fixture,
                    manifest=manifest,
                    run_id=checkpoint.run_id,
                    event_index=event_index,
                    logical_timestamp=logical_timestamp,
                    state_before=State.REPAIR,
                    state_after=State.ACT,
                    actor="repair_executor",
                    event_type="repair_applied",
                    evidence_refs=(f"artifact://{fixture.artifact_path}",),
                    intervention=intervention,
                )
            )
            event_index += 1
            logical_timestamp += 1
            events.append(
                self._event(
                    fixture=fixture,
                    manifest=manifest,
                    run_id=checkpoint.run_id,
                    event_index=event_index,
                    logical_timestamp=logical_timestamp,
                    state_before=State.ACT,
                    state_after=State.VERIFY,
                    actor="repair_executor",
                    event_type="artifact_emitted",
                    evidence_refs=(f"artifact://{fixture.artifact_path}",),
                    intervention=intervention,
                )
            )
            event_index += 1
            logical_timestamp += 1
            repaired_guard_result = self._evaluate_guard(fixture, manifest, workspace)
            if not repaired_guard_result.passed:
                raise RuntimeError("deterministic repair failed its declared guard")
            events.append(
                self._event(
                    fixture=fixture,
                    manifest=manifest,
                    run_id=checkpoint.run_id,
                    event_index=event_index,
                    logical_timestamp=logical_timestamp,
                    state_before=State.VERIFY,
                    state_after=State.COMMIT,
                    actor="transition_arbiter",
                    event_type="transition_authorized",
                    evidence_refs=repaired_guard_result.evidence_refs,
                    guard_results=(repaired_guard_result,),
                    intervention=intervention,
                )
            )

        artifact_digest = workspace.sha256(fixture.artifact_path)
        task_success = artifact_digest == fixture.expected_artifact_digest
        terminal_state = State.COMMIT
        return EpisodeOutcome(
            events=tuple(events),
            terminal_state=terminal_state,
            task_success=task_success,
            false_completion=terminal_state is State.COMMIT and not task_success,
            repair_count=repair_count,
            artifact_digest=artifact_digest,
        )

    def _evaluate_guard(
        self,
        fixture: Fixture,
        manifest: HarnessManifest,
        workspace: DeterministicWorkspace,
    ) -> GuardResult:
        guard = manifest.guard
        if guard["kind"] == "self_report":
            passed = fixture.tool_report == "success"
            refs = (f"tool-report://{fixture.tool_report}",)
            explanation = "generator tool report claimed success"
        elif guard["kind"] == "artifact_sha256":
            actual_digest = workspace.sha256(fixture.artifact_path)
            passed = actual_digest == fixture.expected_artifact_digest
            suffix = actual_digest if actual_digest is not None else "missing"
            refs = (f"artifact://{fixture.artifact_path}#{suffix}",)
            explanation = (
                "artifact digest matched the task receipt"
                if passed
                else "required artifact was missing or had the wrong digest"
            )
        else:
            raise ValueError(f"unsupported guard kind: {guard['kind']}")
        return GuardResult(
            guard=guard["name"],
            guard_version=guard["version"],
            independence_level=guard["independence_level"],
            passed=passed,
            evidence_refs=refs,
            explanation=explanation,
        )

    def _event(
        self,
        *,
        fixture: Fixture,
        manifest: HarnessManifest,
        run_id: str,
        event_index: int,
        logical_timestamp: int,
        state_before: State,
        state_after: State,
        actor: str,
        event_type: str,
        evidence_refs: tuple[str, ...],
        guard_results: tuple[GuardResult, ...] = (),
        intervention: Intervention | None = None,
    ) -> Event:
        if state_after.value not in manifest.chart[state_before.value]:
            raise ValueError(f"illegal transition: {state_before.value}->{state_after.value}")
        return Event(
            run_id=run_id,
            episode_id=fixture.episode_id,
            event_index=event_index,
            state_before=state_before.value,
            proposed_transition=f"{state_before.value}->{state_after.value}",
            actor=actor,
            event_type=event_type,
            evidence_refs=evidence_refs,
            constraint_refs=(fixture.constraint_ref,),
            guard_results=guard_results,
            intervention=intervention,
            state_after=state_after.value,
            timestamp_logical=logical_timestamp,
        )
