"""Canonical IDENT item schemas and serialization helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

DomainName = Literal["boolean_causal", "finite_state", "small_programs"]
ObservationValue = str | int | float | bool | None


@dataclass(frozen=True)
class InterventionSpec:
    id: str
    description: str
    cost: float
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PriorObservation:
    experiment_id: str
    description: str
    outcome: ObservationValue
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IdentItem:
    """One IDENT benchmark item with exact separator annotations."""

    item_id: str
    domain: DomainName
    hypotheses: list[str]
    hypothesis_descriptions: dict[str, str]
    prior_observations: list[PriorObservation]
    equivalence_class_before: list[str]
    candidate_interventions: list[InterventionSpec]
    response_table: dict[str, dict[str, ObservationValue]]
    minimum_separators: list[str]
    true_hypothesis: str
    final_query: str
    answer: str
    passive_chance_bound: float
    distractors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self, *, reveal_truth: bool = False) -> dict[str, Any]:
        """Serialize for prompts/datasets.

        Truth fields are omitted from model-facing views unless reveal_truth=True.
        Oracle annotations needed for scoring remain available when reveal_truth=True.
        """
        payload: dict[str, Any] = {
            "item_id": self.item_id,
            "domain": self.domain,
            "hypotheses": list(self.hypotheses),
            "hypothesis_descriptions": dict(self.hypothesis_descriptions),
            "prior_observations": [asdict(obs) for obs in self.prior_observations],
            "equivalence_class_before": list(self.equivalence_class_before),
            "candidate_interventions": [asdict(g) for g in self.candidate_interventions],
            "final_query": self.final_query,
            "distractors": list(self.distractors),
        }
        if reveal_truth:
            payload.update(
                {
                    "response_table": {
                        h: dict(outcomes) for h, outcomes in self.response_table.items()
                    },
                    "minimum_separators": list(self.minimum_separators),
                    "true_hypothesis": self.true_hypothesis,
                    "answer": self.answer,
                    "passive_chance_bound": self.passive_chance_bound,
                    "metadata": dict(self.metadata),
                }
            )
        return payload

    def to_annotated_dict(self) -> dict[str, Any]:
        return self.to_public_dict(reveal_truth=True)


def item_from_dict(data: dict[str, Any]) -> IdentItem:
    return IdentItem(
        item_id=str(data["item_id"]),
        domain=data["domain"],
        hypotheses=list(data["hypotheses"]),
        hypothesis_descriptions=dict(data.get("hypothesis_descriptions", {})),
        prior_observations=[
            PriorObservation(
                experiment_id=str(obs["experiment_id"]),
                description=str(obs["description"]),
                outcome=obs["outcome"],
                payload=dict(obs.get("payload", {})),
            )
            for obs in data["prior_observations"]
        ],
        equivalence_class_before=list(data["equivalence_class_before"]),
        candidate_interventions=[
            InterventionSpec(
                id=str(g["id"]),
                description=str(g["description"]),
                cost=float(g["cost"]),
                payload=dict(g.get("payload", {})),
            )
            for g in data["candidate_interventions"]
        ],
        response_table={
            str(h): {str(g): outcome for g, outcome in outcomes.items()}
            for h, outcomes in data["response_table"].items()
        },
        minimum_separators=list(data["minimum_separators"]),
        true_hypothesis=str(data["true_hypothesis"]),
        final_query=str(data["final_query"]),
        answer=str(data["answer"]),
        passive_chance_bound=float(data["passive_chance_bound"]),
        distractors=list(data.get("distractors", [])),
        metadata=dict(data.get("metadata", {})),
    )
