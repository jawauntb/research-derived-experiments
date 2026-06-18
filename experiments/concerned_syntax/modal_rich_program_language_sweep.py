#!/usr/bin/env python3
"""Modal sweep for richer concerned intervention programs."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").add_local_python_source(
    "experiments"
)
app = modal.App(name="research-derived-rich-program-language")


@app.function(image=IMAGE, timeout=1800, cpu=1, memory=1024)
def run_seed(seed: int, train_trials: int, test_trials: int, epochs: int) -> dict[str, Any]:
    from experiments.concerned_syntax.rich_program_language import run_experiment

    payload = run_experiment(
        train_trials=train_trials,
        test_trials=test_trials,
        seed=seed,
        epochs=epochs,
    )
    return {
        "seed": seed,
        "agent_summary": payload["agent_summary"],
    }


@app.local_entrypoint()
def main(train_trials: int = 3000, test_trials: int = 1200, epochs: int = 90) -> None:
    from experiments.concerned_syntax.rich_program_language import (
        IMAGE_SIZE,
        PROGRAM_FAMILIES,
        candidate_programs,
        summarize_seed_payloads,
        write_agent_report,
    )

    seeds = [20260617, 1729, 4242, 8675309, 314159]
    results = list(
        run_seed.starmap(
            [(seed, train_trials, test_trials, epochs) for seed in seeds]
        )
    )
    payload = {
        "manifest": {
            "arc": "2A",
            "name": "rich_program_language_modal_sweep",
            "contract": "2A-v2-pixels-rich_programs",
            "seeds": seeds,
            "train_trials": train_trials,
            "test_trials": test_trials,
            "epochs": epochs,
            "programs": [program.name for program in candidate_programs()],
            "program_families": list(PROGRAM_FAMILIES),
            "image_size": IMAGE_SIZE,
            "perception": "connected_components_rgb",
        },
        "results": results,
        "agent_summary": summarize_seed_payloads(results),
    }
    out = Path("artifacts/concerned_syntax/rich_program_language_modal_sweep.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out}")

    agent_report = Path(
        "experiments/concerned_syntax/results/rich_program_language_modal_2026_06_17.md"
    )
    write_agent_report(agent_report, payload)
    print(f"Wrote {agent_report}")
