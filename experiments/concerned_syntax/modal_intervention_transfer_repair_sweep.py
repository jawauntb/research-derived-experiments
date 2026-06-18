#!/usr/bin/env python3
"""Modal sweep for held-out intervention transfer repair."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").add_local_python_source(
    "experiments"
)
app = modal.App(name="research-derived-transfer-repair")


@app.function(image=IMAGE, timeout=2400, cpu=1, memory=1024)
def run_seed(seed: int, train_trials: int, test_trials: int, epochs: int) -> dict[str, Any]:
    from experiments.concerned_syntax.intervention_transfer_repair import run_experiment

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
    from experiments.concerned_syntax.intervention_transfer_repair import (
        HELDOUT_ROLE_KINDS,
        TRANSFER_REPAIR_AGENTS,
        summarize_seed_payloads,
        write_transfer_report,
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
            "name": "intervention_transfer_repair_modal_sweep",
            "contract": "2A-v1-pixels-observe_pair",
            "seeds": seeds,
            "train_trials": train_trials,
            "test_trials": test_trials,
            "epochs": epochs,
            "heldout_kinds": list(HELDOUT_ROLE_KINDS),
            "agents": list(TRANSFER_REPAIR_AGENTS),
            "perception": "connected_components_rgb_plus_role_decoder",
        },
        "results": results,
        "agent_summary": summarize_seed_payloads(results, "agent_summary"),
    }
    out = Path("artifacts/concerned_syntax/intervention_transfer_repair_modal_sweep.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out}")

    report = Path(
        "experiments/concerned_syntax/results/intervention_transfer_repair_modal_2026_06_17.md"
    )
    write_transfer_report(report, payload)
    print(f"Wrote {report}")
