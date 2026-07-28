"""Primary IDENT metrics and transcript scoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from experiments.ident.schemas import IdentItem
from experiments.ident.separators import (
    separates,
    update_live_after_intervention,
    weakness_regret,
)

ActionType = Literal["intervene", "answer"]


@dataclass(frozen=True)
class ModelAction:
    action_type: ActionType
    intervention_id: str | None = None
    answer: str | None = None
    identifiable_now: bool | None = None
    live_hypotheses: tuple[str, ...] = ()
    confidence: float | None = None
    brief_reason: str = ""


@dataclass(frozen=True)
class ItemScore:
    item_id: str
    domain: str
    chose_intervention: bool
    separator_correct: bool
    weakness_regret: float | None
    false_certainty: bool
    post_intervention_correct: bool | None
    final_correct: bool
    efficiency: float | None
    passive_chance_bound: float
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AggregateScores:
    n_items: int
    separator_accuracy: float
    mean_weakness_regret: float | None
    false_certainty_rate: float
    post_intervention_identification: float | None
    mean_efficiency: float | None
    final_accuracy: float
    gates: dict[str, bool]
    by_domain: dict[str, dict[str, float | None]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_model_action(payload: dict[str, Any]) -> ModelAction:
    action = payload.get("action") or {}
    action_type = action.get("type")
    if action_type not in {"intervene", "answer"}:
        raise ValueError(f"invalid action.type: {action_type!r}")
    return ModelAction(
        action_type=action_type,
        intervention_id=action.get("intervention_id"),
        answer=action.get("answer"),
        identifiable_now=payload.get("identifiable_now"),
        live_hypotheses=tuple(payload.get("live_hypotheses") or ()),
        confidence=payload.get("confidence"),
        brief_reason=str(payload.get("brief_reason") or ""),
    )


def score_item(
    item: IdentItem,
    first_action: ModelAction,
    *,
    final_answer: str | None = None,
) -> ItemScore:
    live = list(item.equivalence_class_before)
    underdetermined = len(live) >= 2
    chose_intervention = first_action.action_type == "intervene"
    separator_correct = False
    regret: float | None = None
    efficiency: float | None = None
    post_correct: bool | None = None
    false_certainty = False

    if chose_intervention:
        gid = first_action.intervention_id
        if gid is None:
            separator_correct = False
        else:
            separator_correct = separates(gid, live, item.response_table)
            regret = weakness_regret(
                gid, live, item.candidate_interventions, item.response_table
            )
            if separator_correct and gid in item.response_table[item.true_hypothesis]:
                outcome = item.response_table[item.true_hypothesis][gid]
                updated = update_live_after_intervention(
                    live, gid, outcome, item.response_table
                )
                # Final answer after intervention.
                ans = final_answer if final_answer is not None else (
                    updated[0] if len(updated) == 1 else None
                )
                post_correct = ans == item.answer if ans is not None else False
                cost = next(
                    g.cost for g in item.candidate_interventions if g.id == gid
                )
                gain = 1.0 if post_correct else 0.0
                efficiency = gain / cost if cost > 0 else None
    else:
        # Answered without intervention.
        false_certainty = underdetermined and (
            first_action.identifiable_now is True
            or first_action.confidence is not None
            and first_action.confidence >= 0.8
            or first_action.identifiable_now is None
        )
        ans = first_action.answer if final_answer is None else final_answer
        post_correct = None

    if final_answer is not None:
        final_correct = final_answer == item.answer
    elif first_action.action_type == "answer":
        final_correct = first_action.answer == item.answer
    else:
        final_correct = bool(post_correct)

    return ItemScore(
        item_id=item.item_id,
        domain=item.domain,
        chose_intervention=chose_intervention,
        separator_correct=separator_correct,
        weakness_regret=regret if (regret is not None and separator_correct) else (
            regret if chose_intervention else None
        ),
        false_certainty=false_certainty,
        post_intervention_correct=post_correct,
        final_correct=final_correct,
        efficiency=efficiency,
        passive_chance_bound=item.passive_chance_bound,
        details={
            "identifiable_now": first_action.identifiable_now,
            "confidence": first_action.confidence,
            "chosen_intervention": first_action.intervention_id,
            "first_answer": first_action.answer,
            "final_answer": final_answer,
        },
    )


def aggregate_scores(scores: list[ItemScore]) -> AggregateScores:
    n = len(scores)
    if n == 0:
        return AggregateScores(
            n_items=0,
            separator_accuracy=0.0,
            mean_weakness_regret=None,
            false_certainty_rate=0.0,
            post_intervention_identification=None,
            mean_efficiency=None,
            final_accuracy=0.0,
            gates={},
            by_domain={},
        )

    intervened = [s for s in scores if s.chose_intervention]
    sep_acc = (
        sum(1 for s in intervened if s.separator_correct) / len(intervened)
        if intervened
        else 0.0
    )
    regrets = [s.weakness_regret for s in intervened if s.weakness_regret is not None]
    mean_regret = sum(regrets) / len(regrets) if regrets else None
    false_cert = sum(1 for s in scores if s.false_certainty) / n
    post = [s.post_intervention_correct for s in intervened if s.post_intervention_correct is not None]
    post_acc = sum(1 for x in post if x) / len(post) if post else None
    effs = [s.efficiency for s in intervened if s.efficiency is not None]
    mean_eff = sum(effs) / len(effs) if effs else None
    final_acc = sum(1 for s in scores if s.final_correct) / n

    by_domain: dict[str, dict[str, float | None]] = {}
    domains = sorted({s.domain for s in scores})
    for domain in domains:
        subset = [s for s in scores if s.domain == domain]
        sub_int = [s for s in subset if s.chose_intervention]
        by_domain[domain] = {
            "n": float(len(subset)),
            "separator_accuracy": (
                sum(1 for s in sub_int if s.separator_correct) / len(sub_int)
                if sub_int
                else 0.0
            ),
            "false_certainty_rate": sum(1 for s in subset if s.false_certainty)
            / len(subset),
            "final_accuracy": sum(1 for s in subset if s.final_correct) / len(subset),
        }

    return AggregateScores(
        n_items=n,
        separator_accuracy=sep_acc,
        mean_weakness_regret=mean_regret,
        false_certainty_rate=false_cert,
        post_intervention_identification=post_acc,
        mean_efficiency=mean_eff,
        final_accuracy=final_acc,
        gates={},
        by_domain=by_domain,
    )
