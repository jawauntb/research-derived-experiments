#!/usr/bin/env python3
"""Modal sweep for searched pixel program policies."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").add_local_python_source(
    "experiments"
)
app = modal.App(name="research-derived-searched-program-policy")


@app.function(image=IMAGE, timeout=1800, cpu=1, memory=1024)
def run_seed(
    seed: int,
    train_trials: int,
    test_trials: int,
    epochs: int,
    search_trials: int,
) -> dict[str, Any]:
    from experiments.concerned_syntax.searched_program_policy import run_experiment

    payload = run_experiment(
        train_trials=train_trials,
        test_trials=test_trials,
        seed=seed,
        epochs=epochs,
        search_trials=search_trials,
    )
    return {
        "seed": seed,
        "agent_summary": payload["agent_summary"],
        "search_records": payload["search_records"],
    }


@app.local_entrypoint()
def main(
    train_trials: int = 3000,
    test_trials: int = 1200,
    epochs: int = 90,
    search_trials: int = 600,
) -> None:
    from experiments.concerned_syntax.searched_program_policy import (
        SEARCH_AGENTS,
        candidate_recipes,
        summarize_search_payloads,
        write_agent_report,
    )
    from experiments.concerned_syntax.intervention_invention import (
        IMAGE_SIZE,
        candidate_programs,
    )

    seeds = [20260617, 1729, 4242, 8675309, 314159]
    results = list(
        run_seed.starmap(
            [
                (seed, train_trials, test_trials, epochs, search_trials)
                for seed in seeds
            ]
        )
    )
    payload = {
        "manifest": {
            "arc": "2A",
            "name": "searched_program_policy_modal_sweep",
            "contract": "2A-v1-pixels-observe_pair",
            "seeds": seeds,
            "train_trials": train_trials,
            "test_trials": test_trials,
            "epochs": epochs,
            "search_trials": search_trials,
            "strategies": list(SEARCH_AGENTS),
            "candidate_recipes": len(candidate_recipes()),
            "programs": [program.name for program in candidate_programs()],
            "image_size": IMAGE_SIZE,
            "perception": "connected_components_rgb",
        },
        "results": results,
        "agent_summary": summarize_search_payloads(results, "agent_summary"),
    }
    out = Path("artifacts/concerned_syntax/searched_program_policy_modal_sweep.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out}")

    agent_report = Path(
        "experiments/concerned_syntax/results/searched_program_policy_modal_2026_06_17.md"
    )
    write_agent_report(agent_report, payload)
    print(f"Wrote {agent_report}")
