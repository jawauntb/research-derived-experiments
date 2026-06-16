#!/usr/bin/env python3
"""Modal sweep for learned Arc 2A/2B concerned-syntax agents."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").add_local_python_source(
    "experiments"
)
app = modal.App(name="research-derived-learned-concerned-syntax")


@app.function(image=IMAGE, timeout=1800, cpu=1, memory=1024)
def run_seed(seed: int, train_trials: int, test_trials: int, epochs: int) -> dict[str, Any]:
    from experiments.concerned_syntax.learned_agents import run_experiment

    payload = run_experiment(
        train_trials=train_trials,
        test_trials=test_trials,
        seed=seed,
        epochs=epochs,
    )
    return {
        "seed": seed,
        "agent_summary": payload["agent_summary"],
        "body_summary": payload["body_summary"],
    }


@app.local_entrypoint()
def main(train_trials: int = 3000, test_trials: int = 1200, epochs: int = 90) -> None:
    from experiments.concerned_syntax.learned_agents import (
        summarize_seed_payloads,
        write_agent_report,
        write_body_report,
    )

    seeds = [20260616, 1729, 4242, 8675309, 314159]
    results = list(
        run_seed.starmap(
            [(seed, train_trials, test_trials, epochs) for seed in seeds]
        )
    )
    payload = {
        "manifest": {
            "arc": "2A/2B",
            "name": "learned_concerned_syntax_modal_sweep",
            "seeds": seeds,
            "train_trials": train_trials,
            "test_trials": test_trials,
            "epochs": epochs,
        },
        "results": results,
        "agent_summary": summarize_seed_payloads(results, "agent_summary"),
        "body_summary": summarize_seed_payloads(results, "body_summary"),
    }
    out = Path("artifacts/concerned_syntax/learned_agents_modal_sweep.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out}")

    agent_report = Path("experiments/concerned_syntax/results/learned_agents_modal_2026_06_16.md")
    body_report = Path(
        "experiments/viable_computational_bodies/results/"
        "executable_bodies_modal_2026_06_16.md"
    )
    write_agent_report(agent_report, payload)
    write_body_report(body_report, payload)
    print(f"Wrote {agent_report}")
    print(f"Wrote {body_report}")
