#!/usr/bin/env python3
"""Modal sweep for program-body search against the 2A-v1 contract."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").add_local_python_source(
    "experiments"
)
app = modal.App(name="research-derived-program-body-search")


@app.function(image=IMAGE, timeout=2400, cpu=1, memory=1024)
def run_seed(
    seed: int,
    generations: int,
    population: int,
    train_trials: int,
    test_trials: int,
    epochs: int,
) -> dict[str, Any]:
    from experiments.viable_computational_bodies.program_body_search import (
        PROGRAM_BODY_STRATEGIES,
        run_coupled_sweep,
    )

    payload = run_coupled_sweep(
        strategies=PROGRAM_BODY_STRATEGIES,
        seeds=1,
        generations=generations,
        population=population,
        train_trials=train_trials,
        test_trials=test_trials,
        epochs=epochs,
        base_seed=seed,
        role_transfer_kind=None,
    )
    return {
        "seed": seed,
        "summary": payload["summary"],
    }


@app.local_entrypoint()
def main(
    generations: int = 18,
    population: int = 18,
    train_trials: int = 1200,
    test_trials: int = 500,
    epochs: int = 60,
) -> None:
    from experiments.viable_computational_bodies.program_body_search import (
        PROGRAM_BODY_STRATEGIES,
        summarize_program_bodies,
        write_coupled_report,
    )

    seeds = [20260616, 1729, 4242, 8675309, 314159]
    seed_payloads = list(
        run_seed.starmap(
            [
                (seed, generations, population, train_trials, test_trials, epochs)
                for seed in seeds
            ]
        )
    )

    # Rehydrate one final row per strategy/seed from the per-seed summaries so
    # the report uses the same summary writer as local runs.
    from experiments.viable_computational_bodies.program_body_search import (
        ProgramBodyEvaluation,
    )

    rows: list[ProgramBodyEvaluation] = []
    for payload in seed_payloads:
        seed = payload["seed"]
        for strategy, stats in payload["summary"].items():
            rows.append(
                ProgramBodyEvaluation(
                    architecture=stats["best_architecture"],
                    strategy=strategy,
                    seed=seed,
                    generation=generations - 1,
                    empirical_agent=stats["best_empirical_agent"],
                    train_return=stats["train_return"],
                    parse_accuracy_high_concern=0.0,
                    action_accuracy=0.0,
                    subtree_accuracy=0.0,
                    high_concern_probe_rate=0.0,
                    low_concern_probe_rate=stats["low_concern_probe_rate"],
                    target_accuracy_high_concern=stats["target_accuracy_high_concern"],
                    useful_program_rate_high_concern=stats["useful_program_rate_high_concern"],
                    object_extraction_rate=1.0,
                    empirical_gate_pass=int(stats["empirical_gate_rate"] >= 0.999),
                    formal_valid=int(stats["formal_valid_rate"] >= 0.999),
                    resource_cost=int(round(stats["resource_cost"])),
                    body_gate=int(stats["body_gate_rate"] >= 0.999),
                    violations=(),
                )
            )

    payload = {
        "manifest": {
            "arc": "2A/2B",
            "name": "program_body_search_modal",
            "contract": "2A-v1-pixels-observe_pair",
            "strategies": list(PROGRAM_BODY_STRATEGIES),
            "seeds": len(seeds),
            "generations": generations,
            "population": population,
            "train_trials": train_trials,
            "test_trials": test_trials,
            "epochs": epochs,
            "base_seed": seeds[0],
            "role_transfer_kind": None,
        },
        "summary": summarize_program_bodies(rows),
        "role_transfer_summary": None,
        "seed_payloads": seed_payloads,
        "results": [row.__dict__ for row in rows],
    }
    out = Path("artifacts/viable_computational_bodies/program_body_search_modal.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out}")

    report = Path(
        "experiments/viable_computational_bodies/results/"
        "program_body_search_modal_2026_06_16.md"
    )
    write_coupled_report(report, payload)
    print(f"Wrote {report}")

