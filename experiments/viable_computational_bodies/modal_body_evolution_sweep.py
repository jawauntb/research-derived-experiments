#!/usr/bin/env python3
"""Modal sweep for Arc 2B viable computational bodies."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").add_local_python_source(
    "experiments"
)
app = modal.App(name="research-derived-viable-computational-bodies")


@app.function(image=IMAGE, timeout=1800, cpu=1, memory=1024)
def run_strategy_seed(
    strategy: str,
    seed: int,
    generations: int,
    population: int,
) -> dict[str, Any]:
    from experiments.viable_computational_bodies.search import run_search

    rows = run_search(
        strategy=strategy,
        seed=seed,
        generations=generations,
        population=population,
    )
    final = rows[-1]
    return {
        "strategy": strategy,
        "seed": seed,
        "final": final.__dict__,
    }


@app.local_entrypoint()
def main(generations: int = 32, population: int = 32) -> None:
    from experiments.viable_computational_bodies.modal_report import write_modal_report

    strategies = ["accuracy_only", "novelty_only", "viability_guided"]
    seeds = [20260616, 1729, 4242, 8675309, 314159, 271828]
    calls = [(strategy, seed) for strategy in strategies for seed in seeds]
    results = list(
        run_strategy_seed.starmap(
            [(strategy, seed, generations, population) for strategy, seed in calls]
        )
    )
    payload = {
        "manifest": {
            "arc": "2B",
            "name": "viable_computational_bodies_modal_sweep",
            "strategies": strategies,
            "seeds": seeds,
            "generations": generations,
            "population": population,
        },
        "results": results,
    }
    out = Path("artifacts/viable_computational_bodies/modal_sweep.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    report = Path(
        "experiments/viable_computational_bodies/results/modal_sweep_2026_06_16.md"
    )
    write_modal_report(report, payload)
    print(f"Wrote {report}")
