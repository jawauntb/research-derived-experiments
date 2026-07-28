"""Experiment objects: passive observations and candidate interventions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from experiments.ident.schemas import InterventionSpec, ObservationValue, PriorObservation


@dataclass(frozen=True)
class ExperimentFamily:
    """A named family of interventions with shared payload constructors."""

    family_id: str
    interventions: tuple[InterventionSpec, ...]

    def by_id(self) -> dict[str, InterventionSpec]:
        return {spec.id: spec for spec in self.interventions}


def make_prior_observation(
    *,
    experiment_id: str,
    description: str,
    outcome: ObservationValue,
    payload: dict[str, Any] | None = None,
) -> PriorObservation:
    return PriorObservation(
        experiment_id=experiment_id,
        description=description,
        outcome=outcome,
        payload=dict(payload or {}),
    )


def make_intervention(
    *,
    intervention_id: str,
    description: str,
    cost: float,
    payload: dict[str, Any] | None = None,
) -> InterventionSpec:
    if cost < 0:
        raise ValueError(f"intervention cost must be >= 0, got {cost}")
    return InterventionSpec(
        id=intervention_id,
        description=description,
        cost=float(cost),
        payload=dict(payload or {}),
    )
