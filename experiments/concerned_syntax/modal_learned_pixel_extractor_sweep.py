#!/usr/bin/env python3
"""Modal sweep for learned pixel-object extraction."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").add_local_python_source(
    "experiments"
)
app = modal.App(name="research-derived-learned-pixel-extractor")


@app.function(image=IMAGE, timeout=1800, cpu=1, memory=1024)
def run_seed(
    seed: int,
    train_trials: int,
    test_trials: int,
    epochs: int,
    extractor_samples_per_image: int,
) -> dict[str, Any]:
    from experiments.concerned_syntax.learned_pixel_extractor import run_experiment

    payload = run_experiment(
        train_trials=train_trials,
        test_trials=test_trials,
        seed=seed,
        epochs=epochs,
        extractor_samples_per_image=extractor_samples_per_image,
    )
    return {
        "seed": seed,
        "agent_summary": payload["agent_summary"],
        "extractor_summary": payload["extractor_summary"],
    }


@app.local_entrypoint()
def main(
    train_trials: int = 3000,
    test_trials: int = 1200,
    epochs: int = 90,
    extractor_samples_per_image: int = 96,
) -> None:
    from experiments.concerned_syntax.learned_pixel_extractor import (
        IMAGE_SIZE,
        summarize_seed_payloads,
        write_agent_report,
    )

    seeds = [20260617, 1729, 4242, 8675309, 314159]
    results = list(
        run_seed.starmap(
            [
                (
                    seed,
                    train_trials,
                    test_trials,
                    epochs,
                    extractor_samples_per_image,
                )
                for seed in seeds
            ]
        )
    )
    payload = {
        "manifest": {
            "arc": "2A",
            "name": "learned_pixel_extractor_modal_sweep",
            "seeds": seeds,
            "train_trials": train_trials,
            "test_trials": test_trials,
            "epochs": epochs,
            "extractor_samples_per_image": extractor_samples_per_image,
            "image_size": IMAGE_SIZE,
            "perception": "learned_foreground_slots",
        },
        "results": results,
        "agent_summary": summarize_seed_payloads(results, "agent_summary"),
        "extractor_summary": summarize_seed_payloads(results, "extractor_summary"),
    }
    out = Path("artifacts/concerned_syntax/learned_pixel_extractor_modal_sweep.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out}")

    agent_report = Path(
        "experiments/concerned_syntax/results/"
        "learned_pixel_extractor_modal_2026_06_17.md"
    )
    write_agent_report(agent_report, payload)
    print(f"Wrote {agent_report}")
