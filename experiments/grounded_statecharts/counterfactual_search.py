"""Deterministic paired-intervention pilot for harness component attribution."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from experiments.grounded_statecharts.runtime import digest


COMPONENTS = ("context", "tools", "generation", "orchestration", "memory", "output")
CRITICAL_SURFACES = {"context", "orchestration", "memory", "output"}
FALSE_COMPLETION_SURFACES = {"orchestration", "output"}


@dataclass(frozen=True)
class FaultCase:
    fault_id: str
    responsible_component: str
    source_episode_id: str
    symptom: str
    task_family: str
    trace_suspect: str

    def __post_init__(self) -> None:
        strings = (
            self.fault_id,
            self.source_episode_id,
            self.symptom,
            self.task_family,
        )
        if not all(isinstance(value, str) and value for value in strings):
            raise ValueError("fault identifiers and labels must be non-empty strings")
        if self.responsible_component not in COMPONENTS:
            raise ValueError("fault responsible_component is not a harness surface")
        if self.trace_suspect not in COMPONENTS:
            raise ValueError("fault trace_suspect is not a harness surface")
        if self.trace_suspect == self.responsible_component:
            raise ValueError("thin-pilot trace suspect must be a non-causal confounder")

    @classmethod
    def load_many(cls, path: Path) -> tuple[Self, ...]:
        raw = json.loads(path.read_text())
        if not isinstance(raw, dict) or set(raw) != {"schema_version", "cases"}:
            raise ValueError("fault fixture must contain schema_version and cases")
        cases = raw["cases"]
        if raw["schema_version"] != "1.0" or not isinstance(cases, list):
            raise ValueError("fault fixture has an unsupported schema")
        expected = {
            "fault_id",
            "responsible_component",
            "source_episode_id",
            "symptom",
            "task_family",
            "trace_suspect",
        }
        loaded = []
        for raw_case in cases:
            if not isinstance(raw_case, dict) or set(raw_case) != expected:
                raise ValueError(f"fault case fields must be exactly {sorted(expected)}")
            values = tuple(raw_case.get(key) for key in sorted(expected))
            if not all(isinstance(value, str) for value in values):
                raise ValueError("fault case fields must be strings")
            loaded.append(
                cls(
                    fault_id=str(raw_case["fault_id"]),
                    responsible_component=str(raw_case["responsible_component"]),
                    source_episode_id=str(raw_case["source_episode_id"]),
                    symptom=str(raw_case["symptom"]),
                    task_family=str(raw_case["task_family"]),
                    trace_suspect=str(raw_case["trace_suspect"]),
                )
            )
        if tuple(sorted(case.responsible_component for case in loaded)) != tuple(
            sorted(COMPONENTS)
        ):
            raise ValueError("fault fixture requires exactly one case per harness surface")
        return tuple(loaded)


@dataclass(frozen=True)
class HarnessConfig:
    components: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        names = tuple(name for name, _ in self.components)
        if names != COMPONENTS:
            raise ValueError("harness config must contain all surfaces in canonical order")
        if not all(value for _, value in self.components):
            raise ValueError("harness component versions must be non-empty")

    @classmethod
    def clean(cls) -> Self:
        return cls(tuple((component, "healthy") for component in COMPONENTS))

    @classmethod
    def faulted(cls, case: FaultCase) -> Self:
        return cls.clean().replace(case.responsible_component, case.fault_id)

    def replace(self, component: str, version: str) -> Self:
        if component not in COMPONENTS or not version:
            raise ValueError("replacement must name a harness surface and version")
        return type(self)(
            tuple((name, version if name == component else value) for name, value in self.components)
        )

    def version(self, component: str) -> str:
        return dict(self.components)[component]

    def to_dict(self) -> dict[str, str]:
        return dict(self.components)

    @property
    def manifest_digest(self) -> str:
        return digest(self.to_dict())


@dataclass(frozen=True)
class OutcomeVector:
    task_success: bool
    critical_violation: bool
    false_completion: bool
    joint_success: bool

    def to_dict(self) -> dict[str, bool]:
        return {
            "task_success": self.task_success,
            "critical_violation": self.critical_violation,
            "false_completion": self.false_completion,
            "joint_success": self.joint_success,
        }


@dataclass(frozen=True)
class InterventionResult:
    intervention_id: str
    kind: str
    target_component: str | None
    cost: int
    outcome: OutcomeVector
    delta: dict[str, int]
    accepted_credit: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "intervention_id": self.intervention_id,
            "kind": self.kind,
            "target_component": self.target_component,
            "cost": self.cost,
            "outcome": self.outcome.to_dict(),
            "delta": dict(sorted(self.delta.items())),
            "accepted_credit": self.accepted_credit,
        }


@dataclass(frozen=True)
class SearchResult:
    fault_id: str
    responsible_component: str
    trace_suspect: str
    recovered_component: str | None
    evaluation_budget: int
    counterfactual_repair_success: bool
    trace_repair_success: bool
    noop_identity: bool
    placebo_credit: bool
    original_outcome: OutcomeVector
    interventions: tuple[InterventionResult, ...]

    @property
    def attribution_correct(self) -> bool:
        return self.recovered_component == self.responsible_component

    def to_dict(self) -> dict[str, object]:
        return {
            "fault_id": self.fault_id,
            "responsible_component": self.responsible_component,
            "trace_suspect": self.trace_suspect,
            "recovered_component": self.recovered_component,
            "evaluation_budget": self.evaluation_budget,
            "attribution_correct": self.attribution_correct,
            "counterfactual_repair_success": self.counterfactual_repair_success,
            "trace_repair_success": self.trace_repair_success,
            "noop_identity": self.noop_identity,
            "placebo_credit": self.placebo_credit,
            "original_outcome": self.original_outcome.to_dict(),
            "interventions": [intervention.to_dict() for intervention in self.interventions],
        }


class DeterministicHarnessEvaluator:
    def evaluate(self, case: FaultCase, config: HarnessConfig) -> OutcomeVector:
        repaired = config.version(case.responsible_component) == "healthy"
        if repaired:
            return OutcomeVector(
                task_success=True,
                critical_violation=False,
                false_completion=False,
                joint_success=True,
            )
        task_success = case.responsible_component in CRITICAL_SURFACES
        critical_violation = case.responsible_component in CRITICAL_SURFACES
        false_completion = case.responsible_component in FALSE_COMPLETION_SURFACES
        return OutcomeVector(
            task_success=task_success,
            critical_violation=critical_violation,
            false_completion=false_completion,
            joint_success=False,
        )


class CounterfactualHarnessPilot:
    """Compare paired component interventions with passive trace diagnosis."""

    evaluation_budget = len(COMPONENTS) + 1

    def __init__(self, evaluator: DeterministicHarnessEvaluator | None = None) -> None:
        self.evaluator = evaluator or DeterministicHarnessEvaluator()

    def run(self, case: FaultCase) -> SearchResult:
        faulted = HarnessConfig.faulted(case)
        original = self.evaluator.evaluate(case, faulted)
        noops = tuple(self.evaluator.evaluate(case, faulted) for _ in range(6))
        noop_identity = all(outcome == original for outcome in noops)

        provisional: list[InterventionResult] = []
        for component in COMPONENTS:
            outcome = self.evaluator.evaluate(case, faulted.replace(component, "healthy"))
            delta = self._delta(original, outcome)
            provisional.append(
                InterventionResult(
                    intervention_id=f"repair:{component}",
                    kind="repair",
                    target_component=component,
                    cost=1,
                    outcome=outcome,
                    delta=delta,
                    accepted_credit=delta["joint_success"] == 1,
                )
            )
        placebo_outcome = self.evaluator.evaluate(case, faulted)
        placebo_delta = self._delta(original, placebo_outcome)
        placebo = InterventionResult(
            intervention_id="placebo:unused_metadata",
            kind="placebo",
            target_component=None,
            cost=1,
            outcome=placebo_outcome,
            delta=placebo_delta,
            accepted_credit=placebo_delta["joint_success"] == 1,
        )
        interventions = (*provisional, placebo)
        credited = [
            result
            for result in provisional
            if result.accepted_credit and not placebo.accepted_credit
        ]
        recovered = credited[0].target_component if len(credited) == 1 else None
        counterfactual_success = len(credited) == 1 and credited[0].outcome.joint_success

        trace_repair = faulted.replace(case.trace_suspect, "healthy")
        trace_outcome = self.evaluator.evaluate(case, trace_repair)
        return SearchResult(
            fault_id=case.fault_id,
            responsible_component=case.responsible_component,
            trace_suspect=case.trace_suspect,
            recovered_component=recovered,
            evaluation_budget=self.evaluation_budget,
            counterfactual_repair_success=counterfactual_success,
            trace_repair_success=trace_outcome.joint_success,
            noop_identity=noop_identity,
            placebo_credit=placebo.accepted_credit,
            original_outcome=original,
            interventions=interventions,
        )

    def run_all(self, cases: tuple[FaultCase, ...]) -> tuple[SearchResult, ...]:
        return tuple(self.run(case) for case in cases)

    @staticmethod
    def _delta(original: OutcomeVector, replay: OutcomeVector) -> dict[str, int]:
        return {
            "critical_violation": int(original.critical_violation)
            - int(replay.critical_violation),
            "false_completion": int(original.false_completion)
            - int(replay.false_completion),
            "joint_success": int(replay.joint_success) - int(original.joint_success),
            "task_success": int(replay.task_success) - int(original.task_success),
        }
