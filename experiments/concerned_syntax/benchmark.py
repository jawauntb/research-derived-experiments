#!/usr/bin/env python3
"""Arc 2A: concerned-syntax benchmark.

The benchmark adapts the logic of geometric constituency tests to a minimal
concern setting. A surface shape has six visible parts, but two candidate parse
trees can organize those parts differently. Causal roles interact only when
they belong to the same constituent. A selector succeeds when it invents or
chooses a costly probe only when that probe can reveal a viability-relevant
parse distinction.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any


@dataclass(frozen=True)
class ParseCandidate:
    name: str
    groups: tuple[tuple[int, ...], tuple[int, ...]]
    description_length: int


PARSES: tuple[ParseCandidate, ...] = (
    ParseCandidate("repeat_concat", ((0, 1, 2), (3, 4, 5)), 4),
    ParseCandidate("hooked_repeat", ((0, 1, 3), (2, 4, 5)), 5),
    ParseCandidate("alternating_bind", ((0, 2, 4), (1, 3, 5)), 6),
    ParseCandidate("edge_core", ((0, 4, 5), (1, 2, 3)), 5),
)

HIGH_CONCERN_KINDS = ("shield_poison", "repair_core", "food_trap")
LOW_CONCERN_KINDS = ("ornament_signal",)
SELECTORS = (
    "null_policy",
    "flat_valence",
    "compression_proxy",
    "uncertainty_only",
    "concerned_syntax",
)


@dataclass(frozen=True)
class ShapeTrial:
    trial_id: int
    kind: str
    roles: tuple[str, ...]
    true_parse: ParseCandidate
    alternate_parse: ParseCandidate
    causal_pair: tuple[int, int]
    concern_weight: float

    @property
    def candidate_parses(self) -> tuple[ParseCandidate, ParseCandidate]:
        return (self.true_parse, self.alternate_parse)


@dataclass(frozen=True)
class Intervention:
    name: str
    kind: str
    cost: float
    pair: tuple[int, int] | None = None
    anchor: int | None = None


@dataclass(frozen=True)
class SelectorResult:
    trial_id: int
    kind: str
    selector: str
    intervention: str
    concern_gap: float
    high_concern: int
    informative_probe: int
    probed: int
    parse_correct: int
    action_correct: int
    subtree_correct: int
    movement_correct: int
    regret: float


def _same_subtree(parse: ParseCandidate, a: int, b: int) -> bool:
    return any(a in group and b in group for group in parse.groups)


def _group_containing(parse: ParseCandidate, anchor: int) -> tuple[int, ...]:
    for group in parse.groups:
        if anchor in group:
            return group
    raise ValueError(f"anchor {anchor} absent from parse {parse.name}")


def _role_positions(roles: tuple[str, ...]) -> dict[str, int]:
    return {role: idx for idx, role in enumerate(roles) if role != "neutral"}


def outcome_for_parse(trial: ShapeTrial, parse: ParseCandidate) -> tuple[float, float]:
    """Return viability deltas as (energy_delta, damage_delta)."""

    roles = _role_positions(trial.roles)
    energy = 0.0
    damage = 0.05

    if "food" in roles:
        energy += 0.45
    if "trap" in roles:
        damage += 0.20
    if "poison" in roles:
        damage += 0.45
    if "repair" in roles:
        energy -= 0.08

    if {"shield", "poison"} <= roles.keys() and _same_subtree(
        parse, roles["shield"], roles["poison"]
    ):
        damage -= 0.32
    if {"repair", "core"} <= roles.keys() and _same_subtree(
        parse, roles["repair"], roles["core"]
    ):
        damage -= 0.25
    if {"food", "trap"} <= roles.keys() and _same_subtree(
        parse, roles["food"], roles["trap"]
    ):
        energy -= 0.25
        damage += 0.10

    return (energy, max(0.0, damage))


def flat_outcome(trial: ShapeTrial) -> tuple[float, float]:
    """A flat valence map sees roles but not causal constituency."""

    roles = set(trial.roles)
    energy = 0.45 if "food" in roles else 0.0
    if "repair" in roles:
        energy -= 0.08
    damage = 0.05
    if "trap" in roles:
        damage += 0.20
    if "poison" in roles:
        damage += 0.45
    return (energy, damage)


def utility(outcome: tuple[float, float], concern_weight: float) -> float:
    energy, damage = outcome
    return energy - concern_weight * damage


def preferred_action(outcome: tuple[float, float], concern_weight: float) -> str:
    return "consume" if utility(outcome, concern_weight) > 0.0 else "skip"


def concern_gap(trial: ShapeTrial) -> float:
    values = [
        utility(outcome_for_parse(trial, parse), trial.concern_weight)
        for parse in trial.candidate_parses
    ]
    return abs(values[0] - values[1])


def intervention_options(trial: ShapeTrial, rng: random.Random) -> list[Intervention]:
    causal_a, causal_b = trial.causal_pair
    noninformative_pairs = [
        (a, b)
        for a in range(6)
        for b in range(a + 1, 6)
        if (a, b) != trial.causal_pair
        and _same_subtree(trial.true_parse, a, b)
        == _same_subtree(trial.alternate_parse, a, b)
    ]
    distractor_pair = rng.choice(noninformative_pairs) if noninformative_pairs else (0, 5)
    return [
        Intervention("null", "null", 0.0),
        Intervention("pair_probe", "pair_probe", 0.04, pair=(causal_a, causal_b)),
        Intervention(
            "distractor_pair_probe",
            "pair_probe",
            0.03,
            pair=distractor_pair,
        ),
        Intervention("high_constituent_move", "move", 0.09, anchor=causal_a),
        Intervention("role_ablation", "ablate", 0.08, pair=(causal_a, causal_b)),
    ]


def observation(
    trial: ShapeTrial,
    parse: ParseCandidate,
    intervention: Intervention,
) -> tuple[Any, ...]:
    if intervention.kind == "null":
        return ("none",)
    if intervention.kind == "pair_probe":
        assert intervention.pair is not None
        return ("bound", _same_subtree(parse, *intervention.pair))
    if intervention.kind == "move":
        assert intervention.anchor is not None
        return ("moved_group", _group_containing(parse, intervention.anchor))
    if intervention.kind == "ablate":
        return ("ablate_outcome", tuple(round(v, 3) for v in outcome_for_parse(trial, parse)))
    raise ValueError(f"unknown intervention kind: {intervention.kind}")


def information_gain(trial: ShapeTrial, intervention: Intervention) -> float:
    observations = {
        observation(trial, parse, intervention) for parse in trial.candidate_parses
    }
    return math.log2(len(observations))


def choose_intervention(
    trial: ShapeTrial,
    selector: str,
    rng: random.Random,
) -> Intervention:
    options = intervention_options(trial, rng)
    if selector in {"null_policy", "flat_valence", "compression_proxy"}:
        return options[0]
    if selector == "uncertainty_only":
        return max(options, key=lambda option: (information_gain(trial, option) - option.cost, -option.cost))
    if selector == "concerned_syntax":
        gap = concern_gap(trial)
        if gap < 0.10:
            return options[0]
        return max(
            options,
            key=lambda option: (
                information_gain(trial, option) * gap - option.cost,
                -option.cost,
            ),
        )
    raise KeyError(f"unknown selector: {selector}")


def infer_parse_after_intervention(
    trial: ShapeTrial,
    intervention: Intervention,
    selector: str,
) -> ParseCandidate | None:
    if selector == "flat_valence":
        return None
    if intervention.kind != "null" and information_gain(trial, intervention) > 0:
        true_obs = observation(trial, trial.true_parse, intervention)
        for parse in trial.candidate_parses:
            if observation(trial, parse, intervention) == true_obs:
                return parse
    return min(trial.candidate_parses, key=lambda parse: parse.description_length)


def _trial_pair_for_parses(
    parse_a: ParseCandidate,
    parse_b: ParseCandidate,
    rng: random.Random,
) -> tuple[int, int]:
    pairs = [
        (i, j)
        for i in range(6)
        for j in range(i + 1, 6)
        if _same_subtree(parse_a, i, j) != _same_subtree(parse_b, i, j)
    ]
    return rng.choice(pairs)


def make_trial(trial_id: int, rng: random.Random) -> ShapeTrial:
    true_parse, alternate_parse = rng.sample(PARSES, 2)
    pair = _trial_pair_for_parses(true_parse, alternate_parse, rng)
    high_concern = rng.random() < 0.75
    kind = rng.choice(HIGH_CONCERN_KINDS if high_concern else LOW_CONCERN_KINDS)

    roles = ["neutral"] * 6
    if kind == "shield_poison":
        role_pair = ("shield", "poison")
        concern_weight = 1.4
    elif kind == "repair_core":
        role_pair = ("repair", "core")
        concern_weight = 1.2
    elif kind == "food_trap":
        role_pair = ("food", "trap")
        concern_weight = 1.0
    elif kind == "ornament_signal":
        role_pair = ("signal", "ornament")
        concern_weight = 0.2
    else:
        raise ValueError(f"unknown kind: {kind}")

    roles[pair[0]] = role_pair[0]
    roles[pair[1]] = role_pair[1]

    return ShapeTrial(
        trial_id=trial_id,
        kind=kind,
        roles=tuple(roles),
        true_parse=true_parse,
        alternate_parse=alternate_parse,
        causal_pair=pair,
        concern_weight=concern_weight,
    )


def run_trial(trial: ShapeTrial, rng: random.Random) -> list[SelectorResult]:
    true_outcome = outcome_for_parse(trial, trial.true_parse)
    true_action = preferred_action(true_outcome, trial.concern_weight)
    true_subtree = _same_subtree(trial.true_parse, *trial.causal_pair)
    gap = concern_gap(trial)
    high_concern = int(gap >= 0.10)

    rows: list[SelectorResult] = []
    for selector in SELECTORS:
        intervention = choose_intervention(trial, selector, rng)
        inferred = infer_parse_after_intervention(trial, intervention, selector)
        if inferred is None:
            pred_outcome = flat_outcome(trial)
            pred_subtree = False
        else:
            pred_outcome = outcome_for_parse(trial, inferred)
            pred_subtree = _same_subtree(inferred, *trial.causal_pair)
        pred_action = preferred_action(pred_outcome, trial.concern_weight)
        best_value = utility(true_outcome, trial.concern_weight)
        pred_value = utility(pred_outcome, trial.concern_weight)
        informative = int(information_gain(trial, intervention) > 0.0)
        if inferred is None:
            movement_correct = 0
        else:
            movement_correct = int(
                inferred == trial.true_parse
                and observation(
                    trial,
                    inferred,
                    Intervention(
                        "high_constituent_move",
                        "move",
                        0.09,
                        anchor=trial.causal_pair[0],
                    ),
                )
                == observation(
                    trial,
                    trial.true_parse,
                    Intervention(
                        "high_constituent_move",
                        "move",
                        0.09,
                        anchor=trial.causal_pair[0],
                    ),
                )
            )
        rows.append(
            SelectorResult(
                trial_id=trial.trial_id,
                kind=trial.kind,
                selector=selector,
                intervention=intervention.name,
                concern_gap=gap,
                high_concern=high_concern,
                informative_probe=informative,
                probed=int(intervention.kind != "null"),
                parse_correct=int(inferred == trial.true_parse),
                action_correct=int(pred_action == true_action),
                subtree_correct=int(pred_subtree == true_subtree),
                movement_correct=movement_correct,
                regret=max(0.0, best_value - pred_value),
            )
        )
    return rows


def run_trials(*, trials: int, seed: int) -> list[SelectorResult]:
    rng = random.Random(seed)
    rows: list[SelectorResult] = []
    for trial_id in range(trials):
        trial = make_trial(trial_id, rng)
        rows.extend(run_trial(trial, rng))
    return rows


def _safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def summarize(rows: list[SelectorResult]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[SelectorResult]] = {}
    for row in rows:
        grouped.setdefault(row.selector, []).append(row)

    summary: dict[str, dict[str, Any]] = {}
    for selector, items in grouped.items():
        high = [item for item in items if item.high_concern]
        low = [item for item in items if not item.high_concern]
        high_probe_rate = _safe_mean([item.probed for item in high])
        low_probe_rate = _safe_mean([item.probed for item in low])
        summary[selector] = {
            "n": len(items),
            "parse_accuracy": _safe_mean([item.parse_correct for item in items]),
            "parse_accuracy_high_concern": _safe_mean([item.parse_correct for item in high]),
            "action_accuracy": _safe_mean([item.action_correct for item in items]),
            "subtree_accuracy": _safe_mean([item.subtree_correct for item in items]),
            "movement_accuracy": _safe_mean([item.movement_correct for item in items]),
            "high_concern_probe_rate": high_probe_rate,
            "low_concern_probe_rate": low_probe_rate,
            "informative_probe_rate_high_concern": _safe_mean(
                [item.informative_probe for item in high if item.probed]
            ),
            "mean_regret": _safe_mean([item.regret for item in items]),
            "gate_pass": bool(
                _safe_mean([item.parse_correct for item in high]) >= 0.75
                and _safe_mean([item.action_correct for item in items]) >= 0.85
                and high_probe_rate >= 0.70
                and low_probe_rate <= 0.25
                and _safe_mean([item.subtree_correct for item in items]) >= 0.75
            ),
        }
    return summary


def write_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Concerned Syntax Pilot",
        "",
        "Date: 2026-06-16",
        "",
        "Question: can a selector use costly interventions to reveal causal constituency only when the hidden parse matters for viability?",
        "",
        "## Gate Summary",
        "",
        "| Selector | Parse high | Action | Subtree | High probe | Low probe | Mean regret | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for selector, stats in sorted(summary.items()):
        lines.append(
            "| {selector} | {parse_high:.3f} | {action:.3f} | {subtree:.3f} | "
            "{high_probe:.3f} | {low_probe:.3f} | {regret:.3f} | {gate} |".format(
                selector=selector,
                parse_high=stats["parse_accuracy_high_concern"],
                action=stats["action_accuracy"],
                subtree=stats["subtree_accuracy"],
                high_probe=stats["high_concern_probe_rate"],
                low_probe=stats["low_concern_probe_rate"],
                regret=stats["mean_regret"],
                gate="PASS" if stats["gate_pass"] else "fail",
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The pilot is a design-gate run, not a claim about neural agents. It checks whether the task surface separates flat valence, compression-only parsing, uncertainty-only probing, and concern-weighted causal constituency. The accepted pattern is specific: high-concern ambiguous shapes should trigger informative probes, while low-concern ambiguity should not become restless inquiry.",
            "",
            "Raw JSON remains local under `artifacts/concerned_syntax/`.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260616)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    rows = run_trials(trials=args.trials, seed=args.seed)
    payload = {
        "manifest": {
            "arc": "2A",
            "name": "concerned_syntax",
            "trials": args.trials,
            "seed": args.seed,
            "selectors": list(SELECTORS),
        },
        "summary": summarize(rows),
        "results": [asdict(row) for row in rows],
    }

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.report:
        write_report(args.report, payload)

    print("=== Concerned Syntax Summary ===")
    for selector, stats in sorted(payload["summary"].items()):
        print(
            f"{selector:20s} parse_high={stats['parse_accuracy_high_concern']:.3f} "
            f"action={stats['action_accuracy']:.3f} "
            f"high_probe={stats['high_concern_probe_rate']:.3f} "
            f"low_probe={stats['low_concern_probe_rate']:.3f} "
            f"gate={stats['gate_pass']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
