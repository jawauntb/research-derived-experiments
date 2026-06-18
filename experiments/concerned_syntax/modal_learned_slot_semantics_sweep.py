#!/usr/bin/env python3
"""Modal sweep for learned slot-semantics transfer repair."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").add_local_python_source(
    "experiments"
)
app = modal.App(name="research-derived-learned-slot-semantics")


@app.function(image=IMAGE, timeout=3600, cpu=1, memory=1024)
def run_seed(
    seed: int,
    train_trials: int,
    test_trials: int,
    epochs: int,
    semantic_calibration_trials: int,
) -> dict[str, Any]:
    from experiments.concerned_syntax.learned_slot_semantics import run_experiment

    payload = run_experiment(
        train_trials=train_trials,
        test_trials=test_trials,
        seed=seed,
        epochs=epochs,
        semantic_calibration_trials=semantic_calibration_trials,
    )
    return {
        "seed": seed,
        "agent_summary": payload["agent_summary"],
        "semantic_summary": payload["semantic_summary"],
        "slice_results": payload["slice_results"],
    }


@app.local_entrypoint()
def main(
    train_trials: int = 3000,
    test_trials: int = 1200,
    epochs: int = 90,
    semantic_calibration_trials: int = 1200,
) -> None:
    from experiments.concerned_syntax.learned_slot_semantics import (
        HELDOUT_ROLE_KINDS,
        HELDOUT_TRUE_PARSES,
        LEARNED_SEMANTIC_AGENTS,
        summarize_modal_slice_results,
        summarize_seed_payloads,
        write_semantic_report,
    )

    seeds = [20260618, 1729, 4242, 8675309, 314159]
    results = list(
        run_seed.starmap(
            [
                (
                    seed,
                    train_trials,
                    test_trials,
                    epochs,
                    semantic_calibration_trials,
                )
                for seed in seeds
            ]
        )
    )
    payload = {
        "manifest": {
            "arc": "2A",
            "name": "learned_slot_semantics_transfer_modal_sweep",
            "contract": "2A-v2-pixels-rich_programs-transfer",
            "seeds": seeds,
            "train_trials": train_trials,
            "test_trials": test_trials,
            "semantic_calibration_trials": semantic_calibration_trials,
            "epochs": epochs,
            "heldout_kinds": list(HELDOUT_ROLE_KINDS),
            "heldout_parses": list(HELDOUT_TRUE_PARSES),
            "agents": list(LEARNED_SEMANTIC_AGENTS),
            "perception": "connected_components_rgb_plus_learned_slot_semantics",
            "semantic_calibration": "supervised_visible_role_token_prototypes",
        },
        "results": results,
        "semantic_summary": summarize_seed_payloads(results, "semantic_summary"),
        "agent_summary": summarize_seed_payloads(results, "agent_summary"),
        "slice_results": summarize_modal_slice_results(results),
    }
    out = Path("artifacts/concerned_syntax/learned_slot_semantics_modal_sweep.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out}")

    report = Path(
        "experiments/concerned_syntax/results/"
        "learned_slot_semantics_modal_2026_06_18.md"
    )
    write_semantic_report(report, payload)
    print(f"Wrote {report}")
