#!/usr/bin/env python3
"""Modal sweep for object-slot executable modules against 2A-v2."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").add_local_python_source(
    "experiments"
)
app = modal.App(name="research-derived-object-slot-executable-modules")


@app.function(image=IMAGE, timeout=3600, cpu=1, memory=1024)
def run_seed(
    seed: int,
    generations: int,
    population: int,
    train_trials: int,
    test_trials: int,
    epochs: int,
    induction_calibration_trials: int,
    extractor_calibration_trials: int,
    extractor_epochs: int | None,
) -> dict[str, Any]:
    from experiments.viable_computational_bodies.object_slot_executable_modules import (
        OBJECT_SLOT_EXECUTABLE_STRATEGIES,
        run_seed_search,
    )

    return run_seed_search(
        seed=seed,
        strategies=OBJECT_SLOT_EXECUTABLE_STRATEGIES,
        generations=generations,
        population=population,
        train_trials=train_trials,
        test_trials=test_trials,
        epochs=epochs,
        induction_calibration_trials=induction_calibration_trials,
        extractor_calibration_trials=extractor_calibration_trials,
        extractor_epochs=extractor_epochs,
    )


@app.local_entrypoint()
def main(
    generations: int = 18,
    population: int = 18,
    train_trials: int = 3000,
    test_trials: int = 1200,
    epochs: int = 90,
    induction_calibration_trials: int = 1200,
    extractor_calibration_trials: int = 1200,
    extractor_epochs: int = 45,
) -> None:
    from experiments.viable_computational_bodies.object_slot_executable_modules import (
        OBJECT_SLOT_EXECUTABLE_STRATEGIES,
        object_slot_payload,
        write_object_slot_report,
    )

    seeds = [20260622, 1729, 4242, 8675309, 314159]
    results = list(
        run_seed.starmap(
            [
                (
                    seed,
                    generations,
                    population,
                    train_trials,
                    test_trials,
                    epochs,
                    induction_calibration_trials,
                    extractor_calibration_trials,
                    extractor_epochs,
                )
                for seed in seeds
            ]
        )
    )
    payload = object_slot_payload(
        seed_payloads=results,
        strategies=OBJECT_SLOT_EXECUTABLE_STRATEGIES,
        generations=generations,
        population=population,
        train_trials=train_trials,
        test_trials=test_trials,
        epochs=epochs,
        induction_calibration_trials=induction_calibration_trials,
        extractor_calibration_trials=extractor_calibration_trials,
        extractor_epochs=extractor_epochs,
        seed_values=tuple(seeds),
        base_seed=seeds[0],
    )
    out = Path(
        "artifacts/viable_computational_bodies/"
        "object_slot_executable_modules_modal.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out}")

    report = Path(
        "experiments/viable_computational_bodies/results/"
        "object_slot_executable_modules_modal_2026_06_22.md"
    )
    write_object_slot_report(report, payload)
    print(f"Wrote {report}")
