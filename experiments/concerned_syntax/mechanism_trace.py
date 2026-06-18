#!/usr/bin/env python3
"""Mechanism trace audit for pixel intervention invention.

This verifier records the trajectory that the aggregate 2A-v1 gate implies:
visible state, selected program, observation, posterior binding belief, and
final action. The goal is to make shortcut failures trace-visible instead of
only visible as final metric gaps.
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
    _same_subtree,
    concern_gap,
    outcome_for_parse,
    preferred_action,
    utility,
)
from experiments.concerned_syntax.learned_agents import LinearBinaryModel
from experiments.concerned_syntax.pixel_shapes import (
    IMAGE_SIZE,
    PixelExample,
    action_features,
    pixel_surface_features,
    true_bound,
)

TRACE_AGENTS: tuple[str, ...] = base.PROGRAM_AGENTS


@dataclass(frozen=True)
class MechanismTrace:
    trial_id: int
    agent: str
    trial_kind: str
    high_concern: int
    concern_margin: float
    roles: tuple[str, ...]
    prior_bound: int
    program: str
    selected_pair: tuple[int, int] | None
    selected_pair_observation: int | None
    posterior_bound: int
    posterior_changed: int
    action_rule: str
    action: str
    true_action: str
    target_correct: int
    useful_observation: int
    posterior_correct: int
    action_correct: int
    trace_complete: int
    low_concern_trace_violation: int
    regret: float


def _selected_pair_for_agent(
    example: PixelExample,
    models: dict[str, LinearBinaryModel],
    *,
    agent: str,
) -> tuple[bool, tuple[int, int] | None, str]:
    learned_pair = base._select_target_pair(example, models)
    if agent == "surface_program_shortcut":
        return False, None, "shortcut_action"
    if agent == "random_program_probe":
        return True, base._random_pair(example, salt=11), "bound_action"
    if agent == "concern_without_target":
        policy_probe = bool(models["policy"].predict(pixel_surface_features(example)))
        probed = policy_probe or base._calibration_probe(example)
        return (
            probed,
            base._random_pair(example, salt=23) if probed else None,
            "bound_action",
        )
    if agent == "target_without_concern":
        return True, learned_pair, "bound_action"
    if agent == "concerned_program_inventor":
        policy_probe = bool(models["policy"].predict(pixel_surface_features(example)))
        probed = policy_probe or base._calibration_probe(example)
        return probed, learned_pair if probed else None, "bound_action"
    raise KeyError(agent)


def evaluate_trace_agent(
    examples: list[PixelExample],
    models: dict[str, LinearBinaryModel],
    *,
    agent: str,
) -> list[MechanismTrace]:
    traces: list[MechanismTrace] = []
    for example in examples:
        margin = concern_gap(example.trial)
        high = int(margin >= 0.10)
        probed, selected_pair, action_rule = _selected_pair_for_agent(
            example,
            models,
            agent=agent,
        )
        prior_bound = base._predict_bound_from_program(
            example,
            models,
            probed=False,
            selected_pair=None,
        )
        active_pair = selected_pair if probed else None
        posterior_bound = base._predict_bound_from_program(
            example,
            models,
            probed=probed,
            selected_pair=active_pair,
        )
        if action_rule == "shortcut_action":
            action_label = models["shortcut_action"].predict(pixel_surface_features(example))
        else:
            action_label = models["action_bound"].predict(
                action_features(example, bound=posterior_bound)
            )

        observation = None
        if active_pair is not None:
            observation = int(_same_subtree(example.trial.true_parse, *active_pair))

        true_outcome = outcome_for_parse(example.trial, example.trial.true_parse)
        true_action = preferred_action(true_outcome, example.trial.concern_weight)
        action = "consume" if action_label else "skip"
        target_correct = int(active_pair == example.trial.causal_pair)
        useful_observation = int(probed and target_correct)
        posterior_correct = int(posterior_bound == true_bound(example))
        action_correct = int(action == true_action)
        trace_complete = int(
            bool(
                high
                and useful_observation
                and posterior_correct
                and action_rule == "bound_action"
                and action_correct
            )
        )
        low_violation = int(not high and probed)
        traces.append(
            MechanismTrace(
                trial_id=example.trial.trial_id,
                agent=agent,
                trial_kind=example.trial.kind,
                high_concern=high,
                concern_margin=margin,
                roles=example.trial.roles,
                prior_bound=prior_bound,
                program=base._program_for_pair(active_pair),
                selected_pair=active_pair,
                selected_pair_observation=observation,
                posterior_bound=posterior_bound,
                posterior_changed=int(posterior_bound != prior_bound),
                action_rule=action_rule,
                action=action,
                true_action=true_action,
                target_correct=target_correct,
                useful_observation=useful_observation,
                posterior_correct=posterior_correct,
                action_correct=action_correct,
                trace_complete=trace_complete,
                low_concern_trace_violation=low_violation,
                regret=max(
                    0.0,
                    utility(true_outcome, example.trial.concern_weight)
                    - base._value_for_bound(example, posterior_bound),
                ),
            )
        )
    return traces


def evaluate_traces(
    examples: list[PixelExample],
    models: dict[str, LinearBinaryModel],
) -> list[MechanismTrace]:
    traces: list[MechanismTrace] = []
    for agent in TRACE_AGENTS:
        traces.extend(evaluate_trace_agent(examples, models, agent=agent))
    return traces


def _safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def summarize_traces(rows: list[MechanismTrace]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[MechanismTrace]] = {}
    for row in rows:
        grouped.setdefault(row.agent, []).append(row)

    summary: dict[str, dict[str, Any]] = {}
    for agent, items in grouped.items():
        high = [item for item in items if item.high_concern]
        low = [item for item in items if not item.high_concern]
        high_trace = _safe_mean([item.trace_complete for item in high])
        high_observation = _safe_mean([item.useful_observation for item in high])
        high_posterior = _safe_mean([item.posterior_correct for item in high])
        high_target = _safe_mean([item.target_correct for item in high])
        low_violation = _safe_mean([item.low_concern_trace_violation for item in low])
        action = _safe_mean([item.action_correct for item in items])
        summary[agent] = {
            "n": len(items),
            "high_trace_complete_rate": high_trace,
            "high_useful_observation_rate": high_observation,
            "high_posterior_correct_rate": high_posterior,
            "target_accuracy_high_concern": high_target,
            "action_accuracy": action,
            "low_concern_trace_violation_rate": low_violation,
            "mean_regret": _safe_mean([item.regret for item in items]),
            "gate_pass": bool(
                high_trace >= 0.75
                and high_observation >= 0.70
                and high_posterior >= 0.75
                and high_target >= 0.75
                and action >= 0.85
                and low_violation <= 0.25
            ),
        }
    return summary


def run_experiment(
    *,
    train_trials: int,
    test_trials: int,
    seed: int,
    epochs: int,
    max_traces_per_agent: int = 12,
) -> dict[str, Any]:
    train_examples = base.make_pixel_examples(trials=train_trials, seed=seed)
    test_examples = base.make_pixel_examples(trials=test_trials, seed=seed + 900_000)
    models = base.train_models(train_examples, seed=seed, epochs=epochs)
    traces = evaluate_traces(test_examples, models)
    examples_by_agent: dict[str, list[dict[str, Any]]] = {}
    for trace in traces:
        if len(examples_by_agent.setdefault(trace.agent, [])) < max_traces_per_agent:
            examples_by_agent[trace.agent].append(asdict(trace))
    return {
        "manifest": {
            "arc": "2A",
            "name": "intervention_mechanism_trace",
            "contract": "2A-v1-pixels-observe_pair",
            "train_trials": train_trials,
            "test_trials": test_trials,
            "seed": seed,
            "epochs": epochs,
            "agents": list(TRACE_AGENTS),
            "image_size": IMAGE_SIZE,
            "perception": "connected_components_rgb",
        },
        "trace_summary": summarize_traces(traces),
        "trace_examples": examples_by_agent,
    }


def summarize_trace_payloads(
    payloads: list[dict[str, Any]],
    key: str = "trace_summary",
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


def _manifest_text(manifest: dict[str, Any]) -> str:
    if "seed" in manifest:
        return (
            f"{manifest['train_trials']} train trials, "
            f"{manifest['test_trials']} test trials, seed {manifest['seed']}, "
            f"{manifest['epochs']} SGD epochs."
        )
    seeds = manifest.get("seeds", [])
    return (
        f"{len(seeds)} seeds, {manifest['train_trials']} train trials per seed, "
        f"{manifest['test_trials']} test trials per seed, "
        f"{manifest['epochs']} SGD epochs."
    )


def write_trace_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["trace_summary"]
    manifest = payload["manifest"]
    lines = [
        "# Intervention Mechanism Trace Gate",
        "",
        "Date: 2026-06-17",
        "",
        (
            "Question: does the accepted 2A-v1 intervention policy expose a "
            "faithful program -> observation -> belief update -> action trace, "
            "while shortcuts fail for visible trace reasons?"
        ),
        "",
        f"Manifest: {_manifest_text(manifest)}",
        "",
        "## Trace Gate Summary",
        "",
        (
            "| Agent | Trace high | Useful obs high | Posterior high | Action | "
            "Low trace violation | Target high | Regret | Gate |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for agent, stats in sorted(summary.items()):
        gate_pass = float(stats["gate_pass"]) >= 0.999
        lines.append(
            "| {agent} | {trace:.3f} | {obs:.3f} | {post:.3f} | "
            "{action:.3f} | {low:.3f} | {target:.3f} | {regret:.3f} | "
            "{gate} |".format(
                agent=agent,
                trace=stats["high_trace_complete_rate"],
                obs=stats["high_useful_observation_rate"],
                post=stats["high_posterior_correct_rate"],
                action=stats["action_accuracy"],
                low=stats["low_concern_trace_violation_rate"],
                target=stats["target_accuracy_high_concern"],
                regret=stats["mean_regret"],
                gate="PASS" if gate_pass else "fail",
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "This is a verifier upgrade over the aggregate intervention-"
                "invention table. A passing trace must select a useful program "
                "on high-concern trials, receive an observation tied to that "
                "program, update the hidden-binding belief correctly, and act "
                "from the posterior while keeping low-concern trace violations "
                "under the no-restless cap."
            ),
            "",
            (
                "`target_without_concern` can produce high-quality high-concern "
                "traces but fails by tracing/probing low-concern cases. "
                "`concern_without_target` has the concern gate but asks the "
                "wrong question. Surface and random controls fail before a "
                "faithful observation -> belief -> action chain exists."
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
    parser.add_argument("--seed", type=int, default=20260617)
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--trace-report", type=Path)
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
    if args.trace_report:
        write_trace_report(args.trace_report, payload)

    print("=== Intervention Mechanism Trace Summary ===")
    for agent, stats in sorted(payload["trace_summary"].items()):
        print(
            f"{agent:28s} trace={stats['high_trace_complete_rate']:.3f} "
            f"obs={stats['high_useful_observation_rate']:.3f} "
            f"posterior={stats['high_posterior_correct_rate']:.3f} "
            f"low_violation={stats['low_concern_trace_violation_rate']:.3f} "
            f"gate={stats['gate_pass']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
