"""Weakest separating interventions for live equivalence classes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from experiments.ident.equivalence import partition_by_outcome
from experiments.ident.schemas import InterventionSpec, ObservationValue


def separates(
    intervention_id: str,
    live: Sequence[str],
    response_table: Mapping[str, Mapping[str, ObservationValue]],
) -> bool:
    outcomes = {response_table[h][intervention_id] for h in live}
    return len(outcomes) > 1


def separating_interventions(
    live: Sequence[str],
    candidates: Sequence[InterventionSpec],
    response_table: Mapping[str, Mapping[str, ObservationValue]],
) -> list[InterventionSpec]:
    return [g for g in candidates if separates(g.id, live, response_table)]


def weakest_separators(
    live: Sequence[str],
    candidates: Sequence[InterventionSpec],
    response_table: Mapping[str, Mapping[str, ObservationValue]],
) -> list[InterventionSpec]:
    valid = separating_interventions(live, candidates, response_table)
    if not valid:
        return []
    min_cost = min(g.cost for g in valid)
    return sorted([g for g in valid if g.cost == min_cost], key=lambda g: g.id)


def identifies_truth(
    intervention_id: str,
    live: Sequence[str],
    true_hypothesis: str,
    response_table: Mapping[str, Mapping[str, ObservationValue]],
) -> bool:
    """True iff observing the intervention outcome under the true hyp leaves a singleton."""
    if true_hypothesis not in live:
        return False
    outcome = response_table[true_hypothesis][intervention_id]
    updated = update_live_after_intervention(
        live, intervention_id, outcome, response_table
    )
    return updated == [true_hypothesis] or (
        len(updated) == 1 and updated[0] == true_hypothesis
    )


def weakest_identifying_separators(
    live: Sequence[str],
    candidates: Sequence[InterventionSpec],
    response_table: Mapping[str, Mapping[str, ObservationValue]],
    true_hypothesis: str,
) -> list[InterventionSpec]:
    """Minimum-cost interventions that both separate and uniquely identify the truth."""
    valid = [
        g
        for g in candidates
        if separates(g.id, live, response_table)
        and identifies_truth(g.id, live, true_hypothesis, response_table)
    ]
    if not valid:
        return []
    min_cost = min(g.cost for g in valid)
    return sorted([g for g in valid if g.cost == min_cost], key=lambda g: g.id)


def weakness_regret(
    chosen_id: str,
    live: Sequence[str],
    candidates: Sequence[InterventionSpec],
    response_table: Mapping[str, Mapping[str, ObservationValue]],
) -> float | None:
    """Cost(chosen) - cost(minimum valid separator). None if chosen unknown."""
    by_id = {g.id: g for g in candidates}
    if chosen_id not in by_id:
        return None
    mins = weakest_separators(live, candidates, response_table)
    if not mins:
        return None
    return float(by_id[chosen_id].cost - mins[0].cost)


def outcome_for(
    hypothesis_id: str,
    intervention_id: str,
    response_table: Mapping[str, Mapping[str, ObservationValue]],
) -> ObservationValue:
    return response_table[hypothesis_id][intervention_id]


def update_live_after_intervention(
    live: Sequence[str],
    intervention_id: str,
    observed_outcome: ObservationValue,
    response_table: Mapping[str, Mapping[str, ObservationValue]],
) -> list[str]:
    parts = partition_by_outcome(live, intervention_id, response_table)
    return list(parts.get(observed_outcome, []))
