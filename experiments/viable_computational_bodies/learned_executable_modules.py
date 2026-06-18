#!/usr/bin/env python3
"""Executable module-body gate over the 2A-v2 transfer contract.

The rich program-body search maps symbolic motif sets to empirical controls.
This module adds a smaller but stricter executable-body validation: candidate
bodies are evaluated against the held-out `2A-v2-pixels-rich_programs`
transfer summary, and a body passes only if its executable modules support
concern gating, target binding, program-family routing, rich composition, and
held-out transfer together.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from experiments.concerned_syntax.rich_program_transfer_repair import run_experiment

REQUIRED_EXECUTABLE_MODULES: frozenset[str] = frozenset(
    {
        "pixel_slot_encoder",
        "concern_gate",
        "target_binder",
        "program_family_router",
        "rich_program_composer",
        "world_model",
        "formal_guard",
    }
)

EXECUTABLE_BODY_SPECS: dict[str, dict[str, Any]] = {
    "learned_composer_body": {
        "agent": "learned_rich_program_composer",
        "modules": frozenset(
            {
                "pixel_slot_encoder",
                "learned_concern_policy",
                "learned_target_head",
                "learned_program_family_head",
                "learned_rich_composer",
                "action_head",
            }
        ),
        "resource_cost": 13,
    },
    "family_router_body": {
        "agent": "role_equivariant_family_only",
        "modules": frozenset(
            {
                "pixel_slot_encoder",
                "concern_gate",
                "program_family_router",
                "formal_guard",
            }
        ),
        "resource_cost": 9,
    },
    "target_binder_body": {
        "agent": "role_equivariant_target_only",
        "modules": frozenset(
            {
                "pixel_slot_encoder",
                "target_binder",
                "world_model",
            }
        ),
        "resource_cost": 8,
    },
    "ungated_rich_body": {
        "agent": "role_equivariant_rich_without_concern",
        "modules": frozenset(
            {
                "pixel_slot_encoder",
                "target_binder",
                "program_family_router",
                "rich_program_composer",
                "world_model",
            }
        ),
        "resource_cost": 13,
    },
    "transfer_repaired_executable_body": {
        "agent": "role_equivariant_rich_world_model",
        "modules": frozenset(
            {
                "pixel_slot_encoder",
                "role_slot_decoder",
                "concern_gate",
                "target_binder",
                "program_family_router",
                "rich_program_composer",
                "world_model",
                "formal_guard",
                "action_head",
            }
        ),
        "resource_cost": 16,
    },
}


@dataclass(frozen=True)
class ExecutableBodyEvaluation:
    body: str
    empirical_agent: str
    transfer_gate_pass: int
    parse_accuracy_high_concern: float
    action_accuracy: float
    family_accuracy_high_concern: float
    target_accuracy_high_concern: float
    useful_program_rate_high_concern: float
    rich_program_rate_high_concern: float
    low_concern_program_rate: float
    module_coverage: float
    executable_module_gate: int
    resource_cost: int
    missing_modules: tuple[str, ...]


def evaluate_executable_bodies(
    agent_summary: dict[str, dict[str, Any]],
) -> list[ExecutableBodyEvaluation]:
    rows: list[ExecutableBodyEvaluation] = []
    for body, spec in sorted(EXECUTABLE_BODY_SPECS.items()):
        agent = str(spec["agent"])
        stats = agent_summary[agent]
        modules = set(spec["modules"])
        missing = tuple(sorted(REQUIRED_EXECUTABLE_MODULES - modules))
        coverage = 1.0 - (len(missing) / len(REQUIRED_EXECUTABLE_MODULES))
        transfer_pass = int(bool(stats.get("transfer_gate_pass", False)))
        gate = int(
            transfer_pass
            and not missing
            and int(spec["resource_cost"]) <= 18
            and float(stats["action_accuracy"]) >= 0.85
            and float(stats["low_concern_program_rate"]) <= 0.25
            and float(stats["family_accuracy_high_concern"]) >= 0.70
            and float(stats["target_accuracy_high_concern"]) >= 0.70
            and float(stats["useful_program_rate_high_concern"]) >= 0.70
            and float(stats["rich_program_rate_high_concern"]) >= 0.70
        )
        rows.append(
            ExecutableBodyEvaluation(
                body=body,
                empirical_agent=agent,
                transfer_gate_pass=transfer_pass,
                parse_accuracy_high_concern=float(stats["parse_accuracy_high_concern"]),
                action_accuracy=float(stats["action_accuracy"]),
                family_accuracy_high_concern=float(stats["family_accuracy_high_concern"]),
                target_accuracy_high_concern=float(stats["target_accuracy_high_concern"]),
                useful_program_rate_high_concern=float(
                    stats["useful_program_rate_high_concern"]
                ),
                rich_program_rate_high_concern=float(stats["rich_program_rate_high_concern"]),
                low_concern_program_rate=float(stats["low_concern_program_rate"]),
                module_coverage=coverage,
                executable_module_gate=gate,
                resource_cost=int(spec["resource_cost"]),
                missing_modules=missing,
            )
        )
    return rows


def summarize_body_payloads(
    payloads: list[dict[str, Any]],
    key: str = "body_summary",
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
        stats["empirical_agent"] = rows[0].get("empirical_agent", "")
        stats["missing_modules"] = rows[0].get("missing_modules", [])
        summary[name] = stats
    return summary


def run_body_gate(
    *,
    train_trials: int,
    test_trials: int,
    seed: int,
    epochs: int,
) -> dict[str, Any]:
    transfer_payload = run_experiment(
        train_trials=train_trials,
        test_trials=test_trials,
        seed=seed,
        epochs=epochs,
    )
    rows = evaluate_executable_bodies(transfer_payload["agent_summary"])
    body_summary = {row.body: asdict(row) for row in rows}
    return {
        "manifest": {
            "arc": "2A/2B",
            "name": "learned_executable_modules_v2_transfer",
            "contract": "2A-v2-pixels-rich_programs-transfer",
            "train_trials": train_trials,
            "test_trials": test_trials,
            "seed": seed,
            "epochs": epochs,
            "required_modules": sorted(REQUIRED_EXECUTABLE_MODULES),
        },
        "agent_summary": transfer_payload["agent_summary"],
        "body_summary": body_summary,
        "transfer_payload": transfer_payload,
    }


def _manifest_text(manifest: dict[str, Any]) -> str:
    if "seeds" in manifest:
        return (
            f"{len(manifest['seeds'])} seeds, {manifest['train_trials']} train trials "
            f"per held-out slice/seed, {manifest['test_trials']} test trials per "
            f"held-out slice/seed, {manifest['epochs']} epochs."
        )
    return (
        f"{manifest['train_trials']} train trials per held-out slice, "
        f"{manifest['test_trials']} test trials per held-out slice, seed "
        f"{manifest['seed']}, {manifest['epochs']} epochs."
    )


def write_body_report(path: Path, payload: dict[str, Any]) -> None:
    manifest = payload["manifest"]
    body_summary = payload["body_summary"]
    lines = [
        "# Learned Executable Modules Against 2A-v2 Transfer",
        "",
        "Date: 2026-06-18",
        "",
        (
            "Question: can executable module bodies consume the held-out "
            "`2A-v2-pixels-rich_programs` transfer contract rather than only "
            "mapping symbolic motifs to in-distribution controls?"
        ),
        "",
        f"Manifest: {_manifest_text(manifest)}",
        "",
        "## Body Gate Summary",
        "",
        (
            "| Body | Agent | Transfer | Modules | Family | Target | Useful | "
            "Rich | Low prog | Cost | Missing | Gate |"
        ),
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for body, stats in sorted(body_summary.items()):
        missing = stats.get("missing_modules", [])
        lines.append(
            "| {body} | `{agent}` | {transfer:.3f} | {coverage:.3f} | "
            "{family:.3f} | {target:.3f} | {useful:.3f} | {rich:.3f} | "
            "{low:.3f} | {cost:.0f} | {missing} | {gate} |".format(
                body=body,
                agent=stats["empirical_agent"],
                transfer=stats["transfer_gate_pass"],
                coverage=stats["module_coverage"],
                family=stats["family_accuracy_high_concern"],
                target=stats["target_accuracy_high_concern"],
                useful=stats["useful_program_rate_high_concern"],
                rich=stats["rich_program_rate_high_concern"],
                low=stats["low_concern_program_rate"],
                cost=stats["resource_cost"],
                missing=", ".join(missing) if missing else "none",
                gate="PASS" if stats["executable_module_gate"] else "fail",
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The accepted body is not allowed to pass by target selection, "
                "family routing, or rich composition alone. It must expose all "
                "required executable modules and inherit the transfer gate from "
                "the repaired 2A-v2 world-model agent."
            ),
            "",
            (
                "This is still a compact executable-module validation, not full "
                "neural architecture search. The role-slot decoder is explicit; "
                "replacing it with learned neural role semantics remains the "
                "next Phase 3-facing boundary."
            ),
            "",
            "Raw JSON remains local under `artifacts/viable_computational_bodies/`.",
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

    payload = run_body_gate(
        train_trials=args.train_trials,
        test_trials=args.test_trials,
        seed=args.seed,
        epochs=args.epochs,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.report:
        write_body_report(args.report, payload)

    print("=== Learned Executable Modules Against 2A-v2 Transfer ===")
    for body, stats in sorted(payload["body_summary"].items()):
        print(
            f"{body:34s} transfer={stats['transfer_gate_pass']:.3f} "
            f"modules={stats['module_coverage']:.3f} "
            f"family={stats['family_accuracy_high_concern']:.3f} "
            f"target={stats['target_accuracy_high_concern']:.3f} "
            f"low_prog={stats['low_concern_program_rate']:.3f} "
            f"gate={bool(stats['executable_module_gate'])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
