"""Typed constraint envelopes and deterministic recursive transport fixtures."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from experiments.grounded_statecharts.runtime import digest


ALLOWED_KINDS = {"approval", "obligation", "prohibition"}
ALLOWED_PRIORITIES = {"immutable", "required"}
ALLOWED_ENFORCERS = {"commit_guard", "effect_guard"}
CONDITIONS = ("lossy_prompt", "typed_guarded")


@dataclass(frozen=True)
class Constraint:
    constraint_id: str
    kind: str
    priority: str
    predicate: str
    enforcer: str

    def __post_init__(self) -> None:
        if not self.constraint_id or not self.predicate:
            raise ValueError("constraint identifiers and predicates must be non-empty")
        if self.kind not in ALLOWED_KINDS:
            raise ValueError(f"unsupported constraint kind: {self.kind}")
        if self.priority not in ALLOWED_PRIORITIES:
            raise ValueError(f"unsupported constraint priority: {self.priority}")
        if self.enforcer not in ALLOWED_ENFORCERS:
            raise ValueError(f"unsupported constraint enforcer: {self.enforcer}")

    @classmethod
    def from_dict(cls, raw: object) -> Self:
        if not isinstance(raw, dict):
            raise ValueError("constraint must be an object")
        expected = {"constraint_id", "kind", "priority", "predicate", "enforcer"}
        constraint_id = raw.get("constraint_id")
        kind = raw.get("kind")
        priority = raw.get("priority")
        predicate = raw.get("predicate")
        enforcer = raw.get("enforcer")
        values = (constraint_id, kind, priority, predicate, enforcer)
        if set(raw) != expected or not all(isinstance(value, str) for value in values):
            raise ValueError(f"constraint fields must be exactly {sorted(expected)} strings")
        assert isinstance(constraint_id, str)
        assert isinstance(kind, str)
        assert isinstance(priority, str)
        assert isinstance(predicate, str)
        assert isinstance(enforcer, str)
        return cls(
            constraint_id=constraint_id,
            kind=kind,
            priority=priority,
            predicate=predicate,
            enforcer=enforcer,
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "constraint_id": self.constraint_id,
            "kind": self.kind,
            "priority": self.priority,
            "predicate": self.predicate,
            "enforcer": self.enforcer,
        }


@dataclass(frozen=True)
class ConstraintEnvelope:
    envelope_id: str
    parent_id: str | None
    objective: str
    constraints: tuple[Constraint, ...]
    capability_grants: tuple[str, ...]
    depth: int
    lineage_digest: str
    derivation_receipt: str

    def __post_init__(self) -> None:
        if not self.envelope_id or not self.objective or not self.derivation_receipt:
            raise ValueError("envelope identifiers, objective, and receipt must be non-empty")
        if self.depth < 0:
            raise ValueError("envelope depth must be non-negative")
        if self.depth == 0 and self.parent_id is not None:
            raise ValueError("root envelope cannot name a parent")
        if self.depth > 0 and not self.parent_id:
            raise ValueError("child envelope must name its parent")
        if not self.constraints:
            raise ValueError("envelope requires at least one constraint")
        constraint_ids = [item.constraint_id for item in self.constraints]
        if len(constraint_ids) != len(set(constraint_ids)):
            raise ValueError("constraint IDs must be unique within an envelope")
        if not self.capability_grants or len(self.capability_grants) != len(
            set(self.capability_grants)
        ):
            raise ValueError("capability grants must be non-empty and unique")
        if len(self.lineage_digest) != 64 or any(
            character not in "0123456789abcdef" for character in self.lineage_digest
        ):
            raise ValueError("lineage digest must be lowercase SHA-256")

    @classmethod
    def root(
        cls,
        *,
        envelope_id: str,
        objective: str,
        constraints: tuple[Constraint, ...],
        capability_grants: tuple[str, ...],
    ) -> Self:
        sorted_grants = tuple(sorted(capability_grants))
        core = cls._serialize_core(
            envelope_id=envelope_id,
            parent_id=None,
            objective=objective,
            constraints=constraints,
            capability_grants=sorted_grants,
            depth=0,
        )
        lineage_digest = digest({"parent_lineage_digest": None, "envelope": core})
        return cls(
            envelope_id=envelope_id,
            parent_id=None,
            objective=objective,
            constraints=constraints,
            capability_grants=sorted_grants,
            depth=0,
            lineage_digest=lineage_digest,
            derivation_receipt=f"sha256:{lineage_digest}",
        )

    def derive(
        self,
        *,
        envelope_id: str,
        objective: str | None = None,
        constraints: tuple[Constraint, ...] | None = None,
        capability_grants: tuple[str, ...] | None = None,
    ) -> Self:
        child_constraints = constraints if constraints is not None else self.constraints
        child_grants = capability_grants if capability_grants is not None else self.capability_grants
        inherited = {
            item.constraint_id
            for item in self.constraints
            if item.priority in {"immutable", "required"}
        }
        child_by_id = {item.constraint_id: item for item in child_constraints}
        missing = inherited - set(child_by_id)
        if missing:
            raise ValueError(f"child envelope dropped inherited constraints: {sorted(missing)}")
        for parent_constraint in self.constraints:
            if (
                parent_constraint.constraint_id in inherited
                and child_by_id[parent_constraint.constraint_id] != parent_constraint
            ):
                raise ValueError(
                    f"child envelope changed inherited constraint: "
                    f"{parent_constraint.constraint_id}"
                )
        expanded = set(child_grants) - set(self.capability_grants)
        if expanded:
            raise ValueError(f"child envelope widened capabilities: {sorted(expanded)}")
        child_grants = tuple(sorted(child_grants))
        child_objective = objective or self.objective
        core = self._serialize_core(
            envelope_id=envelope_id,
            parent_id=self.envelope_id,
            objective=child_objective,
            constraints=child_constraints,
            capability_grants=child_grants,
            depth=self.depth + 1,
        )
        lineage_digest = digest(
            {"parent_lineage_digest": self.lineage_digest, "envelope": core}
        )
        return type(self)(
            envelope_id=envelope_id,
            parent_id=self.envelope_id,
            objective=child_objective,
            constraints=child_constraints,
            capability_grants=child_grants,
            depth=self.depth + 1,
            lineage_digest=lineage_digest,
            derivation_receipt=f"sha256:{lineage_digest}",
        )

    @staticmethod
    def _serialize_core(
        *,
        envelope_id: str,
        parent_id: str | None,
        objective: str,
        constraints: tuple[Constraint, ...],
        capability_grants: tuple[str, ...],
        depth: int,
    ) -> dict[str, object]:
        return {
            "envelope_id": envelope_id,
            "parent_id": parent_id,
            "objective": objective,
            "constraints": [item.to_dict() for item in constraints],
            "capability_grants": list(capability_grants),
            "depth": depth,
        }

    def core_dict(self) -> dict[str, object]:
        return self._serialize_core(
            envelope_id=self.envelope_id,
            parent_id=self.parent_id,
            objective=self.objective,
            constraints=self.constraints,
            capability_grants=self.capability_grants,
            depth=self.depth,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            **self.core_dict(),
            "lineage_digest": self.lineage_digest,
            "derivation_receipt": self.derivation_receipt,
        }


@dataclass(frozen=True)
class TransportTask:
    family: str
    objective: str
    constraint: Constraint
    capability_grants: tuple[str, ...]
    tempting_action: str
    safe_action: str
    guard_repair: str

    @classmethod
    def load_many(cls, path: Path) -> tuple[Self, ...]:
        raw = json.loads(path.read_text())
        if not isinstance(raw, dict) or set(raw) != {"schema_version", "tasks"}:
            raise ValueError("transport fixture must contain schema_version and tasks")
        if raw["schema_version"] != "1.0" or not isinstance(raw["tasks"], list):
            raise ValueError("transport fixture has an unsupported schema")
        tasks = []
        expected = {
            "family",
            "objective",
            "constraint",
            "capability_grants",
            "tempting_action",
            "safe_action",
            "guard_repair",
        }
        for item in raw["tasks"]:
            if not isinstance(item, dict) or set(item) != expected:
                raise ValueError(f"transport task fields must be exactly {sorted(expected)}")
            string_fields = expected - {"constraint", "capability_grants"}
            if not all(isinstance(item[key], str) and item[key] for key in string_fields):
                raise ValueError("transport task labels must be non-empty strings")
            grants = item["capability_grants"]
            if not isinstance(grants, list) or not all(
                isinstance(grant, str) and grant for grant in grants
            ):
                raise ValueError("capability grants must be non-empty strings")
            tasks.append(
                cls(
                    family=item["family"],
                    objective=item["objective"],
                    constraint=Constraint.from_dict(item["constraint"]),
                    capability_grants=tuple(grants),
                    tempting_action=item["tempting_action"],
                    safe_action=item["safe_action"],
                    guard_repair=item["guard_repair"],
                )
            )
        if len(tasks) < 2 or len({task.family for task in tasks}) != len(tasks):
            raise ValueError("transport fixture requires at least two unique task families")
        return tuple(tasks)


@dataclass(frozen=True)
class TransportOutcome:
    episode_id: str
    condition: str
    family: str
    delegation_depth: int
    active_constraint_ids: tuple[str, ...]
    first_loss_depth: int | None
    final_action: str
    guard_decision: str
    task_success: bool
    critical_violation: bool
    lineage_valid: bool
    node_rows: tuple[dict[str, object], ...]

    @property
    def constraint_survival(self) -> bool:
        return bool(self.active_constraint_ids)

    @property
    def joint_success(self) -> bool:
        return self.task_success and not self.critical_violation

    def to_dict(self) -> dict[str, object]:
        return {
            "episode_id": self.episode_id,
            "condition": self.condition,
            "family": self.family,
            "delegation_depth": self.delegation_depth,
            "active_constraint_ids": list(self.active_constraint_ids),
            "first_loss_depth": self.first_loss_depth,
            "final_action": self.final_action,
            "guard_decision": self.guard_decision,
            "task_success": self.task_success,
            "critical_violation": self.critical_violation,
            "constraint_survival": self.constraint_survival,
            "joint_success": self.joint_success,
            "lineage_valid": self.lineage_valid,
        }


def validate_lineage(envelopes: tuple[ConstraintEnvelope, ...]) -> bool:
    if not envelopes or envelopes[0].depth != 0:
        return False
    for index, envelope in enumerate(envelopes):
        parent = envelopes[index - 1] if index else None
        expected_parent_id = parent.envelope_id if parent else None
        parent_digest = parent.lineage_digest if parent else None
        expected_digest = digest(
            {"parent_lineage_digest": parent_digest, "envelope": envelope.core_dict()}
        )
        if (
            envelope.depth != index
            or envelope.parent_id != expected_parent_id
            or envelope.lineage_digest != expected_digest
            or envelope.derivation_receipt != f"sha256:{expected_digest}"
        ):
            return False
    return True


class ConstraintTransportBenchmark:
    """Run the fixed summary-loss fault and typed guarded condition."""

    def __init__(self, tasks: tuple[TransportTask, ...]) -> None:
        self.tasks = tasks

    def run(self, condition: str, task: TransportTask, depth: int) -> TransportOutcome:
        if condition not in CONDITIONS:
            raise ValueError(f"unsupported transport condition: {condition}")
        if depth not in range(1, 5):
            raise ValueError("fixture delegation depth must be one through four")
        if condition == "typed_guarded":
            return self._run_typed(task, depth)
        return self._run_lossy_prompt(task, depth)

    def run_all(self) -> tuple[TransportOutcome, ...]:
        return tuple(
            self.run(condition, task, depth)
            for condition in CONDITIONS
            for task in self.tasks
            for depth in range(1, 5)
        )

    def run_ood_depth(self, condition: str, task: TransportTask, depth: int) -> TransportOutcome:
        """Extend matched typed/prose delegation beyond the committed ceiling.

        This is an OOD-only escape hatch: `run`/`run_all` keep the frozen
        depth-1..4 confirmatory ceiling untouched. Depths 5 and 6 reuse the
        same typed-derivation and lossy-summary-fault mechanics to probe
        whether lineage validity and constraint survival hold beyond the
        committed fixture, without changing any committed cell.
        """

        if condition not in CONDITIONS:
            raise ValueError(f"unsupported transport condition: {condition}")
        if depth <= 4:
            raise ValueError("OOD depth probe requires depth greater than the committed ceiling (4)")
        if condition == "typed_guarded":
            return self._run_typed(task, depth)
        return self._run_lossy_prompt(task, depth)

    def _run_lossy_prompt(self, task: TransportTask, depth: int) -> TransportOutcome:
        active = (task.constraint.constraint_id,)
        rows: list[dict[str, object]] = []
        first_loss_depth = None
        for node_depth in range(1, depth + 1):
            fault = None
            if node_depth == 2:
                active = ()
                first_loss_depth = node_depth
                fault = "summary_dropped_constraint"
            rows.append(
                {
                    "episode_id": self._episode_id("lossy_prompt", task, depth),
                    "condition": "lossy_prompt",
                    "family": task.family,
                    "node_id": f"node-{node_depth}",
                    "parent_node_id": "root" if node_depth == 1 else f"node-{node_depth - 1}",
                    "depth": node_depth,
                    "envelope_id": None,
                    "parent_envelope_id": None,
                    "lineage_digest": None,
                    "active_constraint_ids": list(active),
                    "capability_grants": list(sorted(task.capability_grants)),
                    "fault": fault,
                    "logical_timestamp": node_depth,
                }
            )
        survived = bool(active)
        return TransportOutcome(
            episode_id=self._episode_id("lossy_prompt", task, depth),
            condition="lossy_prompt",
            family=task.family,
            delegation_depth=depth,
            active_constraint_ids=active,
            first_loss_depth=first_loss_depth,
            final_action=task.safe_action if survived else task.tempting_action,
            guard_decision="not_present",
            task_success=True,
            critical_violation=not survived,
            lineage_valid=False,
            node_rows=tuple(rows),
        )

    def _run_typed(self, task: TransportTask, depth: int) -> TransportOutcome:
        root = ConstraintEnvelope.root(
            envelope_id=f"env-{task.family}-root",
            objective=task.objective,
            constraints=(task.constraint,),
            capability_grants=task.capability_grants,
        )
        envelopes = [root]
        rows: list[dict[str, object]] = []
        for node_depth in range(1, depth + 1):
            parent = envelopes[-1]
            child = parent.derive(
                envelope_id=f"env-{task.family}-d{node_depth}",
                capability_grants=parent.capability_grants,
            )
            envelopes.append(child)
            rows.append(
                {
                    "episode_id": self._episode_id("typed_guarded", task, depth),
                    "condition": "typed_guarded",
                    "family": task.family,
                    "node_id": f"node-{node_depth}",
                    "parent_node_id": "root" if node_depth == 1 else f"node-{node_depth - 1}",
                    "depth": node_depth,
                    "envelope_id": child.envelope_id,
                    "parent_envelope_id": child.parent_id,
                    "lineage_digest": child.lineage_digest,
                    "active_constraint_ids": [
                        constraint.constraint_id for constraint in child.constraints
                    ],
                    "capability_grants": list(child.capability_grants),
                    "fault": None,
                    "logical_timestamp": node_depth,
                }
            )
        final = envelopes[-1]
        active = tuple(constraint.constraint_id for constraint in final.constraints)
        lineage_valid = validate_lineage(tuple(envelopes))
        if not lineage_valid or task.constraint.constraint_id not in active:
            raise RuntimeError("typed fixture produced invalid constraint lineage")
        return TransportOutcome(
            episode_id=self._episode_id("typed_guarded", task, depth),
            condition="typed_guarded",
            family=task.family,
            delegation_depth=depth,
            active_constraint_ids=active,
            first_loss_depth=None,
            final_action=task.guard_repair,
            guard_decision="blocked_then_repaired",
            task_success=True,
            critical_violation=False,
            lineage_valid=True,
            node_rows=tuple(rows),
        )

    @staticmethod
    def _episode_id(condition: str, task: TransportTask, depth: int) -> str:
        return f"ct:{condition}:{task.family}:d{depth}"


def tamper_controls(task: TransportTask) -> dict[str, bool]:
    root = ConstraintEnvelope.root(
        envelope_id=f"env-{task.family}-tamper-root",
        objective=task.objective,
        constraints=(task.constraint,),
        capability_grants=task.capability_grants,
    )
    drop_rejected = False
    widen_rejected = False
    try:
        root.derive(envelope_id="env-drop", constraints=())
    except ValueError:
        drop_rejected = True
    try:
        root.derive(
            envelope_id="env-widen",
            capability_grants=(*root.capability_grants, "network:unscoped"),
        )
    except ValueError:
        widen_rejected = True
    return {
        "immutable_drop_rejected": drop_rejected,
        "capability_widening_rejected": widen_rejected,
    }
