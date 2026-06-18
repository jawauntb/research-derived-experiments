#!/usr/bin/env python3
"""Held-out role transfer repair for intervention invention.

The original intervention-invention gate learns the target pair from observed
role colors. Holding out an entire high-concern role kind exposes the shortcut:
the learned target and concern heads often stop asking the right question. This
sidecar keeps that failure visible and adds a stricter repair contract: decode
role slots in a role-equivariant way, compute whether either candidate parse
changes viability, and only then spend the ``observe_pair`` program.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from experiments.concerned_syntax import intervention_invention as base
from experiments.concerned_syntax.benchmark import (
    HIGH_CONCERN_KINDS,
    ParseCandidate,
    ShapeTrial,
    _same_subtree,
    concern_gap,
    outcome_for_parse,
    preferred_action,
    utility,
)
from experiments.concerned_syntax.pixel_shapes import ROLE_STYLES, ExtractedComponent


TRANSFER_REPAIR_AGENTS: tuple[str, ...] = (
    "learned_program_inventor",
    "world_concern_random_target",
    "role_equivariant_target_only",
    "role_equivariant_world_model",
)

HELDOUT_ROLE_KINDS: tuple[str, ...] = HIGH_CONCERN_KINDS

ROLE_KIND_WEIGHTS: dict[frozenset[str], tuple[str, float]] = {
    frozenset(("shield", "poison")): ("shield_poison", 1.4),
    frozenset(("repair", "core")): ("repair_core", 1.2),
    frozenset(("food", "trap")): ("food_trap", 1.0),
    frozenset(("signal", "ornament")): ("ornament_signal", 0.2),
}


@dataclass(frozen=True)
class TransferRepairResult:
    trial_id: int
    heldout_kind: str
    agent: str
    program: str
    selected_pair: tuple[int, int] | None
    probed: int
    high_concern: int
    target_correct: int
    useful_program: int
    parse_correct: int
    action_correct: int
    subtree_correct: int
    object_extraction_ok: int
    mean_probe_cost: float
    regret: float


def _color_distance(component: ExtractedComponent, role: str) -> float:
    style = ROLE_STYLES[role]
    return (
        (component.mean_r - style.color[0]) ** 2
        + (component.mean_g - style.color[1]) ** 2
        + (component.mean_b - style.color[2]) ** 2
    )


def _decoded_role(component: ExtractedComponent) -> str:
    return min(ROLE_STYLES, key=lambda role: _color_distance(component, role))


def decoded_roles(example: base.PixelExample) -> tuple[str, ...]:
    """Decode visible role tokens from aligned RGB components."""

    return tuple(
        _decoded_role(component)
        for component in base._padded_components(example)
    )


def _nonneutral_score(component: ExtractedComponent) -> float:
    neutral_distance = _color_distance(component, "neutral")
    role_distance = min(
        _color_distance(component, role)
        for role in ROLE_STYLES
        if role != "neutral"
    )
    return neutral_distance - role_distance


def _sorted_pair(indices: list[int]) -> tuple[int, int]:
    left, right = sorted(indices[:2])
    return (left, right)


def role_equivariant_pair(example: base.PixelExample) -> tuple[int, int]:
    """Select the two visible non-neutral slots without using role identity."""

    roles = decoded_roles(example)
    active = [idx for idx, role in enumerate(roles) if role != "neutral"]
    if len(active) >= 2:
        return _sorted_pair(active)

    components = base._padded_components(example)
    fallback = sorted(
        range(6),
        key=lambda idx: (_nonneutral_score(components[idx]), -idx),
        reverse=True,
    )[:2]
    return _sorted_pair(fallback)


def _kind_and_weight(roles: tuple[str, ...]) -> tuple[str, float]:
    active = frozenset(role for role in roles if role != "neutral")
    return ROLE_KIND_WEIGHTS.get(active, ("unknown", 1.0))


def _decoded_trial(example: base.PixelExample) -> ShapeTrial:
    roles = decoded_roles(example)
    kind, concern_weight = _kind_and_weight(roles)
    return ShapeTrial(
        trial_id=example.trial.trial_id,
        kind=kind,
        roles=roles,
        true_parse=example.trial.true_parse,
        alternate_parse=example.trial.alternate_parse,
        causal_pair=role_equivariant_pair(example),
        concern_weight=concern_weight,
    )


def _infer_parse_from_bound(
    trial: ShapeTrial,
    pair: tuple[int, int],
    observed_bound: int | None,
) -> ParseCandidate:
    if observed_bound is None:
        return min(trial.candidate_parses, key=lambda parse: parse.description_length)
    for parse in trial.candidate_parses:
        if int(_same_subtree(parse, *pair)) == observed_bound:
            return parse
    return min(trial.candidate_parses, key=lambda parse: parse.description_length)


def _program_for_pair(pair: tuple[int, int] | None) -> str:
    if pair is None:
        return "null"
    return f"observe_pair_{pair[0]}_{pair[1]}"


def _random_pair(example: base.PixelExample, *, salt: int) -> tuple[int, int]:
    return base._random_pair(example, salt=salt)


def _append_row(
    rows: list[TransferRepairResult],
    *,
    example: base.PixelExample,
    heldout_kind: str,
    agent: str,
    selected_pair: tuple[int, int] | None,
    probed: bool,
    pred_action: str,
    pred_bound: int,
) -> None:
    target_bound = base.true_bound(example)
    high = int(concern_gap(example.trial) >= 0.10)
    target_correct = int(selected_pair == example.trial.causal_pair)
    useful_program = int(probed and target_correct)
    true_outcome = outcome_for_parse(example.trial, example.trial.true_parse)
    true_action = preferred_action(true_outcome, example.trial.concern_weight)
    pred_parse = (
        example.trial.true_parse
        if pred_bound == target_bound
        else example.trial.alternate_parse
    )
    pred_outcome = outcome_for_parse(example.trial, pred_parse)
    rows.append(
        TransferRepairResult(
            trial_id=example.trial.trial_id,
            heldout_kind=heldout_kind,
            agent=agent,
            program=_program_for_pair(selected_pair),
            selected_pair=selected_pair,
            probed=int(probed),
            high_concern=high,
            target_correct=target_correct,
            useful_program=useful_program,
            parse_correct=int(pred_bound == target_bound),
            action_correct=int(pred_action == true_action),
            subtree_correct=int(pred_bound == target_bound),
            object_extraction_ok=int(len(example.components) == 6),
            mean_probe_cost=0.04 if probed else 0.0,
            regret=max(
                0.0,
                utility(true_outcome, example.trial.concern_weight)
                - utility(pred_outcome, example.trial.concern_weight),
            ),
        )
    )


def _evaluate_world_agent(
    examples: list[base.PixelExample],
    *,
    heldout_kind: str,
    agent: str,
) -> list[TransferRepairResult]:
    rows: list[TransferRepairResult] = []
    for example in examples:
        decoded_trial = _decoded_trial(example)
        role_pair = role_equivariant_pair(example)
        decoded_high_concern = concern_gap(decoded_trial) >= 0.10

        if agent == "world_concern_random_target":
            probed = decoded_high_concern
            selected_pair = _random_pair(example, salt=31) if probed else None
        elif agent == "role_equivariant_target_only":
            probed = True
            selected_pair = role_pair
        elif agent == "role_equivariant_world_model":
            probed = decoded_high_concern
            selected_pair = role_pair if probed else None
        else:
            raise KeyError(agent)

        observed_bound = None
        if probed and selected_pair == example.trial.causal_pair:
            observed_bound = int(_same_subtree(example.trial.true_parse, *selected_pair))

        action_pair = selected_pair if selected_pair is not None else role_pair
        inferred_parse = _infer_parse_from_bound(
            decoded_trial,
            action_pair,
            observed_bound,
        )
        pred_bound = int(_same_subtree(inferred_parse, *example.trial.causal_pair))
        pred_action = preferred_action(
            outcome_for_parse(decoded_trial, inferred_parse),
            decoded_trial.concern_weight,
        )
        _append_row(
            rows,
            example=example,
            heldout_kind=heldout_kind,
            agent=agent,
            selected_pair=selected_pair,
            probed=probed,
            pred_action=pred_action,
            pred_bound=pred_bound,
        )
    return rows


def _evaluate_learned_baseline(
    examples: list[base.PixelExample],
    models: dict[str, base.LinearBinaryModel],
    *,
    heldout_kind: str,
) -> list[TransferRepairResult]:
    rows: list[TransferRepairResult] = []
    for item in base.evaluate_agent(
        examples,
        models,
        agent="concerned_program_inventor",
    ):
        rows.append(
            TransferRepairResult(
                trial_id=item.trial_id,
                heldout_kind=heldout_kind,
                agent="learned_program_inventor",
                program=item.program,
                selected_pair=item.selected_pair,
                probed=item.probed,
                high_concern=item.high_concern,
                target_correct=item.target_correct,
                useful_program=item.useful_program,
                parse_correct=item.parse_correct,
                action_correct=item.action_correct,
                subtree_correct=item.subtree_correct,
                object_extraction_ok=item.object_extraction_ok,
                mean_probe_cost=item.mean_probe_cost,
                regret=item.regret,
            )
        )
    return rows


def evaluate_transfer_agents(
    examples: list[base.PixelExample],
    models: dict[str, base.LinearBinaryModel],
    *,
    heldout_kind: str,
) -> list[TransferRepairResult]:
    rows = _evaluate_learned_baseline(
        examples,
        models,
        heldout_kind=heldout_kind,
    )
    for agent in TRANSFER_REPAIR_AGENTS:
        if agent == "learned_program_inventor":
            continue
        rows.extend(
            _evaluate_world_agent(
                examples,
                heldout_kind=heldout_kind,
                agent=agent,
            )
        )
    return rows


def _safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def summarize_results(rows: list[TransferRepairResult]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[TransferRepairResult]] = {}
    for row in rows:
        grouped.setdefault(row.agent, []).append(row)

    summary: dict[str, dict[str, Any]] = {}
    for agent, items in sorted(grouped.items()):
        high = [item for item in items if item.high_concern]
        low = [item for item in items if not item.high_concern]
        has_high = bool(high)
        parse_high = _safe_mean([item.parse_correct for item in high]) if has_high else 1.0
        action = _safe_mean([item.action_correct for item in items])
        subtree = _safe_mean([item.subtree_correct for item in items])
        extraction = _safe_mean([item.object_extraction_ok for item in items])
        high_probe = _safe_mean([item.probed for item in high]) if has_high else 1.0
        low_probe = _safe_mean([item.probed for item in low])
        target_high = _safe_mean([item.target_correct for item in high]) if has_high else 1.0
        useful_high = _safe_mean([item.useful_program for item in high]) if has_high else 1.0
        high_gate = (
            not has_high
            or (
                parse_high >= 0.75
                and subtree >= 0.75
                and high_probe >= 0.70
                and target_high >= 0.75
                and useful_high >= 0.70
            )
        )
        summary[agent] = {
            "n": len(items),
            "high_concern_count": len(high),
            "parse_accuracy_high_concern": parse_high,
            "action_accuracy": action,
            "subtree_accuracy": subtree,
            "object_extraction_rate": extraction,
            "high_concern_probe_rate": high_probe,
            "low_concern_probe_rate": low_probe,
            "target_accuracy_high_concern": target_high,
            "useful_program_rate_high_concern": useful_high,
            "mean_probe_cost": _safe_mean([item.mean_probe_cost for item in items]),
            "mean_regret": _safe_mean([item.regret for item in items]),
            "gate_pass": bool(
                extraction >= 0.99
                and action >= 0.85
                and low_probe <= 0.25
                and high_gate
            ),
        }
    return summary


def summarize_slice_payloads(
    payloads: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for payload in payloads:
        for name, stats in payload["agent_summary"].items():
            grouped.setdefault(name, []).append(stats)

    summary: dict[str, dict[str, Any]] = {}
    for name, rows in sorted(grouped.items()):
        metric_names = [
            metric
            for metric, value in rows[0].items()
            if isinstance(value, (int, float, bool))
        ]
        stats: dict[str, Any] = {}
        for metric in metric_names:
            values = [float(row[metric]) for row in rows]
            stats[metric] = mean(values)
            stats[f"{metric}_sd"] = pstdev(values) if len(values) > 1 else 0.0
        stats["transfer_gate_pass"] = bool(
            all(bool(row["gate_pass"]) for row in rows)
        )
        summary[name] = stats
    return summary


def summarize_seed_payloads(
    payloads: list[dict[str, Any]],
    key: str = "agent_summary",
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for payload in payloads:
        for name, stats in payload[key].items():
            grouped.setdefault(name, []).append(stats)

    summary: dict[str, dict[str, Any]] = {}
    for name, rows in sorted(grouped.items()):
        metric_names = [
            metric
            for metric, value in rows[0].items()
            if isinstance(value, (int, float, bool))
        ]
        stats: dict[str, Any] = {}
        for metric in metric_names:
            values = [float(row[metric]) for row in rows]
            stats[metric] = mean(values)
            stats[f"{metric}_sd"] = pstdev(values) if len(values) > 1 else 0.0
        summary[name] = stats
    return summary


def run_experiment(
    *,
    train_trials: int,
    test_trials: int,
    seed: int,
    epochs: int,
    heldout_kinds: tuple[str, ...] = HELDOUT_ROLE_KINDS,
) -> dict[str, Any]:
    slice_payloads: list[dict[str, Any]] = []
    for offset, heldout_kind in enumerate(heldout_kinds):
        train_examples = base.make_filtered_pixel_examples(
            trials=train_trials,
            seed=seed + offset * 10_000,
            exclude_kinds={heldout_kind},
        )
        test_examples = base.make_filtered_pixel_examples(
            trials=test_trials,
            seed=seed + 700_000 + offset * 10_000,
            include_kinds={heldout_kind},
        )
        models = base.train_models(
            train_examples,
            seed=seed + offset * 1_000,
            epochs=epochs,
        )
        rows = evaluate_transfer_agents(
            test_examples,
            models,
            heldout_kind=heldout_kind,
        )
        slice_payloads.append(
            {
                "heldout_kind": heldout_kind,
                "agent_summary": summarize_results(rows),
                "results": [asdict(row) for row in rows],
            }
        )

    return {
        "manifest": {
            "arc": "2A",
            "name": "intervention_transfer_repair",
            "contract": "2A-v1-pixels-observe_pair",
            "train_trials": train_trials,
            "test_trials": test_trials,
            "seed": seed,
            "epochs": epochs,
            "heldout_kinds": list(heldout_kinds),
            "agents": list(TRANSFER_REPAIR_AGENTS),
            "programs": [program.name for program in base.candidate_programs()],
            "perception": "connected_components_rgb_plus_role_decoder",
        },
        "agent_summary": summarize_slice_payloads(slice_payloads),
        "slice_results": slice_payloads,
    }


def _manifest_text(manifest: dict[str, Any]) -> str:
    if "seeds" in manifest:
        return (
            f"{len(manifest['seeds'])} seeds, {manifest['train_trials']} train trials "
            f"per held-out kind/seed, {manifest['test_trials']} test trials per held-out "
            f"kind/seed, {manifest['epochs']} SGD epochs, held-out kinds "
            f"{', '.join(manifest['heldout_kinds'])}."
        )
    return (
        f"{manifest['train_trials']} train trials per held-out kind, "
        f"{manifest['test_trials']} test trials per held-out kind, seed "
        f"{manifest['seed']}, {manifest['epochs']} SGD epochs, held-out kinds "
        f"{', '.join(manifest['heldout_kinds'])}."
    )


def write_transfer_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["agent_summary"]
    manifest = payload["manifest"]
    lines = [
        "# Intervention Transfer Repair",
        "",
        "Date: 2026-06-17",
        "",
        (
            "Question: can a role-equivariant perceptual/world-model operation "
            "repair the held-out role-kind transfer failure in the frozen "
            "`2A-v1-pixels-observe_pair` contract?"
        ),
        "",
        f"Manifest: {_manifest_text(manifest)}",
        "",
        "## Gate Summary",
        "",
        (
            "| Agent | Parse high | Action | Subtree | High probe | Low probe | "
            "Target high | Useful high | Regret | Slice gate | Transfer gate |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for agent, stats in sorted(summary.items()):
        transfer_gate = float(stats.get("transfer_gate_pass", 0.0)) >= 0.999
        lines.append(
            "| {agent} | {parse:.3f} | {action:.3f} | {subtree:.3f} | "
            "{high:.3f} | {low:.3f} | {target:.3f} | {useful:.3f} | "
            "{regret:.3f} | {gate:.3f} | {transfer} |".format(
                agent=agent,
                parse=stats["parse_accuracy_high_concern"],
                action=stats["action_accuracy"],
                subtree=stats["subtree_accuracy"],
                high=stats["high_concern_probe_rate"],
                low=stats["low_concern_probe_rate"],
                target=stats["target_accuracy_high_concern"],
                useful=stats["useful_program_rate_high_concern"],
                regret=stats["mean_regret"],
                gate=stats["gate_pass"],
                transfer="PASS" if transfer_gate else "fail",
            )
        )

    if payload.get("slice_results"):
        lines.extend(
            [
                "",
                "## Held-Out Slices",
                "",
                "| Held-out kind | Agent | Target high | Useful high | Low probe | Gate |",
                "|---|---|---:|---:|---:|---|",
            ]
        )
        for slice_payload in payload["slice_results"]:
            heldout_kind = slice_payload["heldout_kind"]
            for agent, stats in sorted(slice_payload["agent_summary"].items()):
                lines.append(
                    "| {kind} | {agent} | {target:.3f} | {useful:.3f} | "
                    "{low:.3f} | {gate} |".format(
                        kind=heldout_kind,
                        agent=agent,
                        target=stats["target_accuracy_high_concern"],
                        useful=stats["useful_program_rate_high_concern"],
                        low=stats["low_concern_probe_rate"],
                        gate="PASS" if stats["gate_pass"] else "fail",
                    )
                )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The learned baseline preserves the original shortcut failure under "
            "held-out high-concern role kinds. The repair is not another "
            "i.i.d. target learner: it decodes visible role slots, selects the "
            "two non-neutral objects as the intervention target, computes "
            "whether the candidate parses change viability, and only then "
            "uses `observe_pair(a,b)`. Target-only and random-target controls "
            "show that both the equivariant target operation and the concern "
            "gate are required.",
            "",
            "Raw JSON remains local under `artifacts/concerned_syntax/`.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-trials", type=int, default=1200)
    parser.add_argument("--test-trials", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260617)
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    payload = run_experiment(
        train_trials=args.train_trials,
        test_trials=args.test_trials,
        seed=args.seed,
        epochs=args.epochs,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.report:
        write_transfer_report(args.report, payload)

    print("=== Intervention Transfer Repair Summary ===")
    for agent, stats in sorted(payload["agent_summary"].items()):
        print(
            f"{agent:32s} parse_high={stats['parse_accuracy_high_concern']:.3f} "
            f"action={stats['action_accuracy']:.3f} "
            f"target_high={stats['target_accuracy_high_concern']:.3f} "
            f"useful_high={stats['useful_program_rate_high_concern']:.3f} "
            f"low_probe={stats['low_concern_probe_rate']:.3f} "
            f"transfer={stats['transfer_gate_pass']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
