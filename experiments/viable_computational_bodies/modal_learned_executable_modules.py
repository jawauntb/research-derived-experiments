#!/usr/bin/env python3
"""Modal sweep for learned executable module bodies against 2A-v2 transfer."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").add_local_python_source(
    "experiments"
)
app = modal.App(name="research-derived-learned-executable-modules")


@app.function(image=IMAGE, timeout=3600, cpu=1, memory=1024)
def run_seed(seed: int, train_trials: int, test_trials: int, epochs: int) -> dict[str, Any]:
    from experiments.viable_computational_bodies.learned_executable_modules import (
        run_body_gate,
    )

    payload = run_body_gate(
        train_trials=train_trials,
        test_trials=test_trials,
        seed=seed,
        epochs=epochs,
    )
    return {
        "seed": seed,
        "body_summary": payload["body_summary"],
        "agent_summary": payload["agent_summary"],
    }


@app.local_entrypoint()
def main(train_trials: int = 3000, test_trials: int = 1200, epochs: int = 90) -> None:
    from experiments.viable_computational_bodies.learned_executable_modules import (
        REQUIRED_EXECUTABLE_MODULES,
        summarize_body_payloads,
        write_body_report,
    )

    seeds = [20260618, 1729, 4242, 8675309, 314159]
    results = list(
        run_seed.starmap(
            [(seed, train_trials, test_trials, epochs) for seed in seeds]
        )
    )
    payload = {
        "manifest": {
            "arc": "2A/2B",
            "name": "learned_executable_modules_v2_transfer_modal",
            "contract": "2A-v2-pixels-rich_programs-transfer",
            "seeds": seeds,
            "train_trials": train_trials,
            "test_trials": test_trials,
            "epochs": epochs,
            "required_modules": sorted(REQUIRED_EXECUTABLE_MODULES),
        },
        "results": results,
        "body_summary": summarize_body_payloads(results, "body_summary"),
    }
    out = Path("artifacts/viable_computational_bodies/learned_executable_modules_modal.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out}")

    report = Path(
        "experiments/viable_computational_bodies/results/"
        "learned_executable_modules_modal_2026_06_18.md"
    )
    write_body_report(report, payload)
    print(f"Wrote {report}")
