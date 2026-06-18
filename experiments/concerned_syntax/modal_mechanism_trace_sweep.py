#!/usr/bin/env python3
"""Modal sweep for intervention mechanism traces."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").add_local_python_source(
    "experiments"
)
app = modal.App(name="research-derived-mechanism-trace")


@app.function(image=IMAGE, timeout=1800, cpu=1, memory=1024)
def run_seed(seed: int, train_trials: int, test_trials: int, epochs: int) -> dict[str, Any]:
    from experiments.concerned_syntax.mechanism_trace import run_experiment

    payload = run_experiment(
        train_trials=train_trials,
        test_trials=test_trials,
        seed=seed,
        epochs=epochs,
    )
    return {
        "seed": seed,
        "trace_summary": payload["trace_summary"],
        "trace_examples": payload["trace_examples"],
    }


@app.local_entrypoint()
def main(train_trials: int = 3000, test_trials: int = 1200, epochs: int = 90) -> None:
    from experiments.concerned_syntax.mechanism_trace import (
        TRACE_AGENTS,
        summarize_trace_payloads,
        write_trace_report,
    )
    from experiments.concerned_syntax.intervention_invention import IMAGE_SIZE

    seeds = [20260617, 1729, 4242, 8675309, 314159]
    results = list(
        run_seed.starmap(
            [(seed, train_trials, test_trials, epochs) for seed in seeds]
        )
    )
    payload = {
        "manifest": {
            "arc": "2A",
            "name": "mechanism_trace_modal_sweep",
            "contract": "2A-v1-pixels-observe_pair",
            "seeds": seeds,
            "train_trials": train_trials,
            "test_trials": test_trials,
            "epochs": epochs,
            "agents": list(TRACE_AGENTS),
            "image_size": IMAGE_SIZE,
            "perception": "connected_components_rgb",
        },
        "results": results,
        "trace_summary": summarize_trace_payloads(results, "trace_summary"),
    }
    out = Path("artifacts/concerned_syntax/mechanism_trace_modal_sweep.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out}")

    trace_report = Path(
        "experiments/concerned_syntax/results/mechanism_trace_modal_2026_06_17.md"
    )
    write_trace_report(trace_report, payload)
    print(f"Wrote {trace_report}")
