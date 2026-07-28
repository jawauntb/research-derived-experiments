"""Hidden mechanisms and response functions for IDENT."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from experiments.ident.schemas import ObservationValue


class Mechanism(Protocol):
    mechanism_id: str
    description: str

    def respond(self, intervention_payload: dict[str, Any]) -> ObservationValue: ...


@dataclass(frozen=True)
class CallableMechanism:
    mechanism_id: str
    description: str
    _fn: Callable[[dict[str, Any]], ObservationValue]

    def respond(self, intervention_payload: dict[str, Any]) -> ObservationValue:
        return self._fn(intervention_payload)


def response_table(
    mechanisms: list[Mechanism],
    interventions: list[tuple[str, dict[str, Any]]],
) -> dict[str, dict[str, ObservationValue]]:
    table: dict[str, dict[str, ObservationValue]] = {}
    for mechanism in mechanisms:
        row: dict[str, ObservationValue] = {}
        for intervention_id, payload in interventions:
            row[intervention_id] = mechanism.respond(payload)
        table[mechanism.mechanism_id] = row
    return table
