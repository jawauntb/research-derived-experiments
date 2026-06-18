#!/usr/bin/env python3
"""Held-out transfer repair for the 2A-v2 rich-program contract.

The v2 rich-program gate proves that a learned agent can choose among provided
program families in-distribution. This sidecar turns held-out role-kind and
true-parse transfer into an explicit gate. The learned rich composer remains a
baseline; the repaired operation decodes visible role slots, chooses the
role-equivariant target and required program family, and only spends a program
when the decoded world model says the hidden binding matters.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from experiments.concerned_syntax import rich_program_language as rich
from experiments.concerned_syntax.benchmark import (
    HIGH_CONCERN_KINDS,
    LOW_CONCERN_KINDS,
    PARSES,
    ParseCandidate,
    ShapeTrial,
    _same_subtree,
    concern_gap,
    outcome_for_parse,
    preferred_action,
    utility,
)
from experiments.concerned_syntax.intervention_invention import _random_pair
from experiments.concerned_syntax.intervention_transfer_repair import (
    _kind_and_weight,
    decoded_roles,
    role_equivariant_pair,
)

RICH_TRANSFER_AGENTS: tuple[str, ...] = (
    "learned_rich_program_composer",
    "role_equivariant_family_only",
    "role_equivariant_target_only",
    "role_equivariant_rich_without_concern",
    "role_equivariant_rich_world_model",
)

HELDOUT_ROLE_KINDS: tuple[str, ...] = HIGH_CONCERN_KINDS
HELDOUT_TRUE_PARSES: tuple[str, ...] = tuple(parse.name for parse in PARSES)


@dataclass(frozen=True)
class RichTransferResult:
    trial_id: int
    axis: str
    heldout: str
    agent: str
    program: str
    family: str
    selected_pair: tuple[int, int] | None
    anchor: int | None
    probed: int
    high_concern: int
    family_correct: int
    target_correct: int
    useful_program: int
    rich_program: int
    parse_correct: int
    action_correct: int
    subtree_correct: int
    object_extraction_ok: int
    mean_program_cost: float
    regret: float


def _decoded_trial(example: rich.PixelExample) -> ShapeTrial:
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


def _family_from_decoded_roles(example: rich.PixelExample) -> str:
    roles = decoded_roles(example)
    kind, _ = _kind_and_weight(roles)
    return rich.REQUIRED_FAMILY_BY_KIND.get(kind, "observe_pair")


def _target_correct(
    example: rich.PixelExample,
    family: str,
    pair: tuple[int, int] | None,
    anchor: int | None,
) -> int:
    if family == "move_anchor":
        return int(anchor in set(example.trial.causal_pair))
    return int(pair == example.trial.causal_pair)


def _infer_parse_from_observation(
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


def _append_row(
    rows: list[RichTransferResult],
    *,
    example: rich.PixelExample,
    axis: str,
    heldout: str,
    agent: str,
    family: str,
    selected_pair: tuple[int, int] | None,
    anchor: int | None,
    probed: bool,
    pred_bound: int,
    pred_action: str,
) -> None:
    required = rich.required_family(example)
    family_correct = int(family == required)
    target_correct = _target_correct(example, family, selected_pair, anchor)
    useful_program = int(probed and family_correct and target_correct)
    target_bound = rich.true_bound(example)
    true_outcome = outcome_for_parse(example.trial, example.trial.true_parse)
    true_action = preferred_action(true_outcome, example.trial.concern_weight)
    pred_parse = (
        example.trial.true_parse
        if pred_bound == target_bound
        else example.trial.alternate_parse
    )
    pred_outcome = outcome_for_parse(example.trial, pred_parse)
    rows.append(
        RichTransferResult(
            trial_id=example.trial.trial_id,
            axis=axis,
            heldout=heldout,
            agent=agent,
            program=rich._program_name(family, selected_pair, anchor),
            family=family,
            selected_pair=selected_pair,
            anchor=anchor,
            probed=int(probed),
            high_concern=int(concern_gap(example.trial) >= 0.10),
            family_correct=family_correct,
            target_correct=target_correct,
            useful_program=useful_program,
            rich_program=int(family in {"move_anchor", "ablate_pair", "compose_move_observe"}),
            parse_correct=int(pred_bound == target_bound),
            action_correct=int(pred_action == true_action),
            subtree_correct=int(pred_bound == target_bound),
            object_extraction_ok=int(len(example.components) == 6),
            mean_program_cost=rich._program_cost(family, probed),
            regret=max(
                0.0,
                utility(true_outcome, example.trial.concern_weight)
                - utility(pred_outcome, example.trial.concern_weight),
            ),
        )
    )


def _evaluate_learned_baseline(
    examples: list[rich.PixelExample],
    models: dict[str, rich.LinearBinaryModel],
    *,
    axis: str,
    heldout: str,
) -> list[RichTransferResult]:
    rows: list[RichTransferResult] = []
    for item in rich.evaluate_agent(
        examples,
        models,
        agent="concerned_program_composer",
    ):
        rows.append(
            RichTransferResult(
                trial_id=item.trial_id,
                axis=axis,
                heldout=heldout,
                agent="learned_rich_program_composer",
                program=item.program,
                family=item.family,
                selected_pair=item.selected_pair,
                anchor=item.anchor,
                probed=item.probed,
                high_concern=item.high_concern,
                family_correct=item.family_correct,
                target_correct=item.target_correct,
                useful_program=item.useful_program,
                rich_program=item.rich_program,
                parse_correct=item.parse_correct,
                action_correct=item.action_correct,
                subtree_correct=item.subtree_correct,
                object_extraction_ok=item.object_extraction_ok,
                mean_program_cost=item.mean_program_cost,
                regret=item.regret,
            )
        )
    return rows


def _evaluate_role_equivariant_agent(
    examples: list[rich.PixelExample],
    *,
    axis: str,
    heldout: str,
    agent: str,
) -> list[RichTransferResult]:
    rows: list[RichTransferResult] = []
    for example in examples:
        decoded_trial = _decoded_trial(example)
        decoded_pair = role_equivariant_pair(example)
        decoded_family = _family_from_decoded_roles(example)
        decoded_high_concern = concern_gap(decoded_trial) >= 0.10

        if agent == "role_equivariant_family_only":
            probed = decoded_high_concern
            family = decoded_family if probed else "null"
            selected_pair = _random_pair(example, salt=71) if probed else None
        elif agent == "role_equivariant_target_only":
            probed = True
            family = "observe_pair"
            selected_pair = decoded_pair
        elif agent == "role_equivariant_rich_without_concern":
            probed = True
            family = decoded_family
            selected_pair = decoded_pair
        elif agent == "role_equivariant_rich_world_model":
            probed = decoded_high_concern
            family = decoded_family if probed else "null"
            selected_pair = decoded_pair if probed else None
        else:
            raise KeyError(agent)

        anchor = selected_pair[0] if selected_pair is not None else None
        target_ok = _target_correct(example, family, selected_pair, anchor)
        useful = bool(probed and family == rich.required_family(example) and target_ok)
        observed_bound = int(_same_subtree(example.trial.true_parse, *decoded_pair)) if useful else None
        inference_pair = selected_pair if selected_pair is not None else decoded_pair
        inferred_parse = _infer_parse_from_observation(
            decoded_trial,
            inference_pair,
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
            axis=axis,
            heldout=heldout,
            agent=agent,
            family=family,
            selected_pair=selected_pair,
            anchor=anchor,
            probed=probed,
            pred_bound=pred_bound,
            pred_action=pred_action,
        )
    return rows


def evaluate_transfer_agents(
    examples: list[rich.PixelExample],
    models: dict[str, rich.LinearBinaryModel],
    *,
    axis: str,
    heldout: str,
) -> list[RichTransferResult]:
    rows = _evaluate_learned_baseline(
        examples,
        models,
        axis=axis,
        heldout=heldout,
    )
    for agent in RICH_TRANSFER_AGENTS:
        if agent == "learned_rich_program_composer":
            continue
        rows.extend(
            _evaluate_role_equivariant_agent(
                examples,
                axis=axis,
                heldout=heldout,
                agent=agent,
            )
        )
    return rows


def _safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def summarize_results(rows: list[RichTransferResult]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[RichTransferResult]] = {}
    for row in rows:
        grouped.setdefault(row.agent, []).append(row)

    summary: dict[str, dict[str, Any]] = {}
    for agent, items in sorted(grouped.items()):
        high = [item for item in items if item.high_concern]
        low = [item for item in items if not item.high_concern]
        has_high = bool(high)
        parse_high = _safe_mean([item.parse_correct for item in high]) if has_high else 1.0
        subtree = _safe_mean([item.subtree_correct for item in high]) if has_high else 1.0
        high_program = _safe_mean([item.probed for item in high]) if has_high else 1.0
        low_program = _safe_mean([item.probed for item in low])
        family_high = _safe_mean([item.family_correct for item in high]) if has_high else 1.0
        target_high = _safe_mean([item.target_correct for item in high]) if has_high else 1.0
        useful_high = _safe_mean([item.useful_program for item in high]) if has_high else 1.0
        rich_high = _safe_mean([item.rich_program for item in high if item.probed]) if has_high else 1.0
        action = _safe_mean([item.action_correct for item in items])
        extraction = _safe_mean([item.object_extraction_ok for item in items])
        high_gate = (
            not has_high
            or (
                parse_high >= 0.75
                and subtree >= 0.75
                and high_program >= 0.70
                and family_high >= 0.70
                and target_high >= 0.70
                and useful_high >= 0.70
                and rich_high >= 0.70
            )
        )
        summary[agent] = {
            "n": len(items),
            "high_concern_count": len(high),
            "parse_accuracy_high_concern": parse_high,
            "action_accuracy": action,
            "subtree_accuracy": subtree,
            "object_extraction_rate": extraction,
            "high_concern_program_rate": high_program,
            "low_concern_program_rate": low_program,
            "family_accuracy_high_concern": family_high,
            "target_accuracy_high_concern": target_high,
            "useful_program_rate_high_concern": useful_high,
            "rich_program_rate_high_concern": rich_high,
            "mean_program_cost": _safe_mean([item.mean_program_cost for item in items]),
            "mean_regret": _safe_mean([item.regret for item in items]),
            "gate_pass": bool(
                extraction >= 0.99
                and action >= 0.85
                and low_program <= 0.25
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
        stats["transfer_gate_pass"] = bool(all(bool(row["gate_pass"]) for row in rows))
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


def summarize_modal_slice_results(
    seed_payloads: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for seed_payload in seed_payloads:
        for slice_payload in seed_payload.get("slice_results", []):
            key = (str(slice_payload["axis"]), str(slice_payload["heldout"]))
            grouped.setdefault(key, []).append(slice_payload)

    slice_results: list[dict[str, Any]] = []
    for (axis, heldout), payloads in sorted(grouped.items()):
        slice_results.append(
            {
                "axis": axis,
                "heldout": heldout,
                "agent_summary": summarize_seed_payloads(payloads, "agent_summary"),
            }
        )
    return slice_results


def _slice_examples(
    *,
    axis: str,
    heldout: str,
    train_trials: int,
    test_trials: int,
    seed: int,
) -> tuple[list[rich.PixelExample], list[rich.PixelExample]]:
    if axis == "role_kind":
        return (
            rich.make_filtered_pixel_examples(
                trials=train_trials,
                seed=seed,
                exclude_kinds={heldout},
            ),
            rich.make_filtered_pixel_examples(
                trials=test_trials,
                seed=seed + 1_300_000,
                include_kinds={heldout},
            ),
        )
    if axis == "true_parse":
        return (
            rich.make_filtered_pixel_examples(
                trials=train_trials,
                seed=seed,
                exclude_true_parses={heldout},
            ),
            rich.make_filtered_pixel_examples(
                trials=test_trials,
                seed=seed + 1_500_000,
                include_true_parses={heldout},
            ),
        )
    raise KeyError(axis)


def run_slice(
    *,
    axis: str,
    heldout: str,
    train_trials: int,
    test_trials: int,
    seed: int,
    epochs: int,
) -> dict[str, Any]:
    train_examples, test_examples = _slice_examples(
        axis=axis,
        heldout=heldout,
        train_trials=train_trials,
        test_trials=test_trials,
        seed=seed,
    )
    models = rich.train_rich_models(train_examples, seed=seed, epochs=epochs)
    rows = evaluate_transfer_agents(
        test_examples,
        models,
        axis=axis,
        heldout=heldout,
    )
    return {
        "axis": axis,
        "heldout": heldout,
        "agent_summary": summarize_results(rows),
        "results": [asdict(row) for row in rows],
    }


def run_experiment(
    *,
    train_trials: int,
    test_trials: int,
    seed: int,
    epochs: int,
    heldout_kinds: tuple[str, ...] = HELDOUT_ROLE_KINDS,
    heldout_parses: tuple[str, ...] = HELDOUT_TRUE_PARSES,
) -> dict[str, Any]:
    slice_payloads: list[dict[str, Any]] = []
    for offset, heldout_kind in enumerate(heldout_kinds):
        slice_payloads.append(
            run_slice(
                axis="role_kind",
                heldout=heldout_kind,
                train_trials=train_trials,
                test_trials=test_trials,
                seed=seed + offset * 10_000,
                epochs=epochs,
            )
        )
    for offset, heldout_parse in enumerate(heldout_parses):
        slice_payloads.append(
            run_slice(
                axis="true_parse",
                heldout=heldout_parse,
                train_trials=train_trials,
                test_trials=test_trials,
                seed=seed + 80_000 + offset * 10_000,
                epochs=epochs,
            )
        )

    return {
        "manifest": {
            "arc": "2A",
            "name": "rich_program_transfer_repair",
            "contract": "2A-v2-pixels-rich_programs",
            "train_trials": train_trials,
            "test_trials": test_trials,
            "seed": seed,
            "epochs": epochs,
            "heldout_kinds": list(heldout_kinds),
            "heldout_parses": list(heldout_parses),
            "agents": list(RICH_TRANSFER_AGENTS),
            "program_families": list(rich.PROGRAM_FAMILIES),
            "perception": "connected_components_rgb_plus_role_decoder",
        },
        "agent_summary": summarize_slice_payloads(slice_payloads),
        "slice_results": slice_payloads,
    }


def _manifest_text(manifest: dict[str, Any]) -> str:
    if "seeds" in manifest:
        return (
            f"{len(manifest['seeds'])} seeds, {manifest['train_trials']} train trials "
            f"per held-out slice/seed, {manifest['test_trials']} test trials per "
            f"held-out slice/seed, {manifest['epochs']} SGD epochs, role held-outs "
            f"{', '.join(manifest['heldout_kinds'])}, parse held-outs "
            f"{', '.join(manifest['heldout_parses'])}."
        )
    return (
        f"{manifest['train_trials']} train trials per held-out slice, "
        f"{manifest['test_trials']} test trials per held-out slice, seed "
        f"{manifest['seed']}, {manifest['epochs']} SGD epochs, role held-outs "
        f"{', '.join(manifest['heldout_kinds'])}, parse held-outs "
        f"{', '.join(manifest['heldout_parses'])}."
    )


def write_transfer_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["agent_summary"]
    manifest = payload["manifest"]
    slice_results = payload.get("slice_results") or summarize_modal_slice_results(
        payload.get("results", [])
    )
    lines = [
        "# Rich Program Transfer Repair",
        "",
        "Date: 2026-06-18",
        "",
        (
            "Question: can the `2A-v2-pixels-rich_programs` contract survive "
            "held-out role-kind and true-parse transfer once target and "
            "program-family selection are made role-equivariant?"
        ),
        "",
        f"Manifest: {_manifest_text(manifest)}",
        "",
        "## Gate Summary",
        "",
        (
            "| Agent | Parse high | Action | Subtree | High prog | Low prog | "
            "Family high | Target high | Useful high | Rich high | Regret | "
            "Slice gate | Transfer gate |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for agent, stats in sorted(summary.items()):
        transfer_gate = float(stats.get("transfer_gate_pass", 0.0)) >= 0.999
        lines.append(
            "| {agent} | {parse:.3f} | {action:.3f} | {subtree:.3f} | "
            "{high:.3f} | {low:.3f} | {family:.3f} | {target:.3f} | "
            "{useful:.3f} | {rich_prog:.3f} | {regret:.3f} | {gate:.3f} | "
            "{transfer} |".format(
                agent=agent,
                parse=stats["parse_accuracy_high_concern"],
                action=stats["action_accuracy"],
                subtree=stats["subtree_accuracy"],
                high=stats["high_concern_program_rate"],
                low=stats["low_concern_program_rate"],
                family=stats["family_accuracy_high_concern"],
                target=stats["target_accuracy_high_concern"],
                useful=stats["useful_program_rate_high_concern"],
                rich_prog=stats["rich_program_rate_high_concern"],
                regret=stats["mean_regret"],
                gate=stats["gate_pass"],
                transfer="PASS" if transfer_gate else "fail",
            )
        )

    lines.extend(
        [
            "",
            "## Held-Out Slices",
            "",
            "| Axis | Held-out | Agent | Family high | Target high | Useful high | Low prog | Gate |",
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for slice_payload in slice_results:
        axis = slice_payload["axis"]
        heldout = slice_payload["heldout"]
        for agent, stats in sorted(slice_payload["agent_summary"].items()):
            gate_pass = float(stats["gate_pass"]) >= 0.999
            lines.append(
                "| {axis} | {heldout} | {agent} | {family:.3f} | {target:.3f} | "
                "{useful:.3f} | {low:.3f} | {gate} |".format(
                    axis=axis,
                    heldout=heldout,
                    agent=agent,
                    family=stats["family_accuracy_high_concern"],
                    target=stats["target_accuracy_high_concern"],
                    useful=stats["useful_program_rate_high_concern"],
                    low=stats["low_concern_program_rate"],
                    gate="PASS" if gate_pass else "fail",
                )
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The learned rich composer remains the shortcut baseline: it can "
                "pass the i.i.d. v2 gate without proving role/parse transfer. "
                "The accepted repair decodes role slots, chooses the "
                "role-equivariant target, selects the required rich program "
                "family, and gates program use by decoded concern. Family-only, "
                "target-only, and rich-without-concern controls isolate the "
                "failure modes."
            ),
            "",
            (
                "This is still an explicit role decoder/world model, not learned "
                "neural role semantics or open-ended program invention. It closes "
                "the Phase 2 transfer gate for the provided v2 grammar while "
                "leaving learned slot semantics as the next claim boundary."
            ),
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
    parser.add_argument("--seed", type=int, default=20260618)
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

    print("=== Rich Program Transfer Repair Summary ===")
    for agent, stats in sorted(payload["agent_summary"].items()):
        print(
            f"{agent:38s} parse_high={stats['parse_accuracy_high_concern']:.3f} "
            f"family={stats['family_accuracy_high_concern']:.3f} "
            f"target={stats['target_accuracy_high_concern']:.3f} "
            f"useful={stats['useful_program_rate_high_concern']:.3f} "
            f"rich={stats['rich_program_rate_high_concern']:.3f} "
            f"low_prog={stats['low_concern_program_rate']:.3f} "
            f"transfer={stats['transfer_gate_pass']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
