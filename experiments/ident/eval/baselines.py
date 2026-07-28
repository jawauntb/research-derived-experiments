"""Trivial and oracle baselines for IDENT."""

from __future__ import annotations

import random
from typing import Any

from experiments.ident.equivalence import information_gain
from experiments.ident.schemas import IdentItem
from experiments.ident.scoring import ModelAction
from experiments.ident.separators import (
    outcome_for,
    separates,
    update_live_after_intervention,
    weakest_identifying_separators,
)


def answer_now(item: IdentItem, rng: random.Random) -> tuple[ModelAction, str]:
    """Predict a latent mechanism without intervention (uniform over live class)."""
    live = list(item.equivalence_class_before)
    guess = rng.choice(live)
    action = ModelAction(
        action_type="answer",
        answer=guess,
        identifiable_now=True,
        live_hypotheses=tuple(live),
        confidence=1.0 / len(live) if live else 0.0,
        brief_reason="Answer from passive observations only.",
    )
    return action, guess


def random_intervention(item: IdentItem, rng: random.Random) -> tuple[ModelAction, str]:
    g = rng.choice(item.candidate_interventions)
    action = ModelAction(
        action_type="intervene",
        intervention_id=g.id,
        identifiable_now=False,
        live_hypotheses=tuple(item.equivalence_class_before),
        confidence=0.5,
        brief_reason="Random candidate intervention.",
    )
    outcome = outcome_for(item.true_hypothesis, g.id, item.response_table)
    live = update_live_after_intervention(
        item.equivalence_class_before, g.id, outcome, item.response_table
    )
    final = live[0] if len(live) == 1 else rng.choice(live or item.hypotheses)
    return action, final


def max_output_variance(item: IdentItem, rng: random.Random) -> tuple[ModelAction, str]:
    """Pick the intervention with the largest number of distinct live outcomes."""
    live = list(item.equivalence_class_before)
    best_score = -1
    best_ids: list[str] = []
    for g in item.candidate_interventions:
        n_out = len({item.response_table[h][g.id] for h in live})
        if n_out > best_score:
            best_score = n_out
            best_ids = [g.id]
        elif n_out == best_score:
            best_ids.append(g.id)
    gid = rng.choice(sorted(best_ids))
    action = ModelAction(
        action_type="intervene",
        intervention_id=gid,
        identifiable_now=False,
        live_hypotheses=tuple(live),
        confidence=0.6,
        brief_reason="Maximize distinct outcomes among live hypotheses.",
    )
    outcome = outcome_for(item.true_hypothesis, gid, item.response_table)
    updated = update_live_after_intervention(live, gid, outcome, item.response_table)
    final = updated[0] if len(updated) == 1 else rng.choice(updated or live)
    return action, final


def expected_information_gain(
    item: IdentItem, rng: random.Random
) -> tuple[ModelAction, str]:
    live = list(item.equivalence_class_before)
    scored = [
        (information_gain(live, g.id, item.response_table), -g.cost, g.id)
        for g in item.candidate_interventions
    ]
    scored.sort(reverse=True)
    best_gain = scored[0][0]
    top = [gid for gain, _neg_cost, gid in scored if abs(gain - best_gain) < 1e-12]
    # Among equal IG, prefer lower cost (already in sort via -cost), keep stable.
    top_sorted = sorted(
        top,
        key=lambda gid: (
            next(g.cost for g in item.candidate_interventions if g.id == gid),
            gid,
        ),
    )
    gid = top_sorted[0]
    if best_gain <= 0:
        # No informative intervention: abstain-style answer-now at chance.
        return answer_now(item, rng)
    action = ModelAction(
        action_type="intervene",
        intervention_id=gid,
        identifiable_now=False,
        live_hypotheses=tuple(live),
        confidence=0.7,
        brief_reason="Maximize expected information gain under uniform prior.",
    )
    outcome = outcome_for(item.true_hypothesis, gid, item.response_table)
    updated = update_live_after_intervention(live, gid, outcome, item.response_table)
    final = updated[0] if len(updated) == 1 else rng.choice(updated or live)
    return action, final


def oracle_weakest_separator(
    item: IdentItem, rng: random.Random
) -> tuple[ModelAction, str]:
    live = list(item.equivalence_class_before)
    mins = weakest_identifying_separators(
        live,
        item.candidate_interventions,
        item.response_table,
        item.true_hypothesis,
    )
    if not mins:
        return answer_now(item, rng)
    g = rng.choice(mins)
    action = ModelAction(
        action_type="intervene",
        intervention_id=g.id,
        identifiable_now=False,
        live_hypotheses=tuple(live),
        confidence=1.0,
        brief_reason="Oracle minimum-cost separator.",
    )
    outcome = outcome_for(item.true_hypothesis, g.id, item.response_table)
    updated = update_live_after_intervention(live, g.id, outcome, item.response_table)
    assert len(updated) >= 1
    # If not unique, oracle still picks among remaining consistently.
    final = sorted(updated)[0] if item.true_hypothesis not in updated else item.true_hypothesis
    # Prefer true hypothesis when still live (should be).
    if item.true_hypothesis in updated:
        final = item.true_hypothesis
    return action, final


BASELINES: dict[str, Any] = {
    "answer_now": answer_now,
    "random_intervention": random_intervention,
    "max_output_variance": max_output_variance,
    "expected_information_gain": expected_information_gain,
    "oracle_weakest_separator": oracle_weakest_separator,
}


def run_baseline_on_item(
    name: str, item: IdentItem, *, seed: int
) -> tuple[ModelAction, str]:
    if name not in BASELINES:
        raise KeyError(name)
    # Verify separator helper available for sanity in oracle path.
    _ = separates
    return BASELINES[name](item, random.Random(seed))
