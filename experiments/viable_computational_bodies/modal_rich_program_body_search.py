#!/usr/bin/env python3
"""Modal sweep for rich program-body search against the 2A-v2 contract."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").add_local_python_source(
    "experiments"
)
app = modal.App(name="research-derived-rich-program-body-search")


@app.function(image=IMAGE, timeout=3600, cpu=1, memory=1024)
def run_seed(
    seed: int,
    generations: int,
    population: int,
    train_trials: int,
    test_trials: int,
    epochs: int,
    formal_mode: str,
) -> dict[str, Any]:
    from experiments.viable_computational_bodies.rich_program_body_search import (
        RICH_BODY_STRATEGIES,
        run_coupled_sweep,
    )

    payload = run_coupled_sweep(
        strategies=RICH_BODY_STRATEGIES,
        seeds=1,
        generations=generations,
        population=population,
        train_trials=train_trials,
        test_trials=test_trials,
        epochs=epochs,
        base_seed=seed,
        formal_mode=formal_mode,
    )
    return {
        "seed": seed,
        "summary": payload["summary"],
        "results": payload["results"],
        "empirical_payloads": payload["empirical_payloads"],
    }


@app.local_entrypoint()
def main(
    generations: int = 18,
    population: int = 18,
    train_trials: int = 1200,
    test_trials: int = 500,
    epochs: int = 60,
    formal_mode: str = "auto",
) -> None:
    from experiments.viable_computational_bodies.rich_program_body_search import (
        RICH_BODY_STRATEGIES,
        RichBodyEvaluation,
        summarize_rich_bodies,
        write_coupled_report,
    )

    seeds = [20260618, 1729, 4242, 8675309, 314159]
    seed_payloads = list(
        run_seed.starmap(
            [
                (seed, generations, population, train_trials, test_trials, epochs)
                + (formal_mode,)
                for seed in seeds
            ]
        )
    )

    rows = [
        RichBodyEvaluation(
            architecture=row["architecture"],
            strategy=row["strategy"],
            seed=row["seed"],
            generation=row["generation"],
            empirical_agent=row["empirical_agent"],
            train_return=row["train_return"],
            parse_accuracy_high_concern=row["parse_accuracy_high_concern"],
            action_accuracy=row["action_accuracy"],
            subtree_accuracy=row["subtree_accuracy"],
            high_concern_program_rate=row["high_concern_program_rate"],
            low_concern_program_rate=row["low_concern_program_rate"],
            family_accuracy_high_concern=row["family_accuracy_high_concern"],
            target_accuracy_high_concern=row["target_accuracy_high_concern"],
            useful_program_rate_high_concern=row["useful_program_rate_high_concern"],
            rich_program_rate_high_concern=row["rich_program_rate_high_concern"],
            object_extraction_rate=row["object_extraction_rate"],
            empirical_gate_pass=row["empirical_gate_pass"],
            formal_valid=row["formal_valid"],
            formal_source=row["formal_source"],
            resource_cost=row["resource_cost"],
            body_gate=row["body_gate"],
            violations=tuple(row["violations"]),
        )
        for payload in seed_payloads
        for row in payload["results"]
    ]

    payload = {
        "manifest": {
            "arc": "2A/2B",
            "name": "rich_program_body_search_modal",
            "contract": "2A-v2-pixels-rich_programs",
            "strategies": list(RICH_BODY_STRATEGIES),
            "seeds": len(seeds),
            "seed_values": seeds,
            "generations": generations,
            "population": population,
            "train_trials": train_trials,
            "test_trials": test_trials,
            "epochs": epochs,
            "base_seed": seeds[0],
            "formal_mode": formal_mode,
        },
        "summary": summarize_rich_bodies(rows),
        "seed_payloads": seed_payloads,
        "results": [row.__dict__ for row in rows],
    }
    out = Path("artifacts/viable_computational_bodies/rich_program_body_search_modal.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out}")

    report = Path(
        "experiments/viable_computational_bodies/results/"
        "rich_program_body_search_modal_2026_06_18.md"
    )
    write_coupled_report(report, payload)
    print(f"Wrote {report}")
