#!/usr/bin/env python3
"""Modal sweep for learned object-slot discovered semantic profiles."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").add_local_python_source(
    "experiments"
)
app = modal.App(name="research-derived-learned-object-slots")


@app.function(image=IMAGE, timeout=7200, cpu=1, memory=1024)
def run_seed(
    seed: int,
    train_trials: int,
    test_trials: int,
    epochs: int,
    induction_calibration_trials: int,
    extractor_calibration_trials: int,
    extractor_epochs: int,
    extractor_samples_per_image: int,
) -> dict[str, Any]:
    from experiments.concerned_syntax.learned_object_slots import run_experiment

    payload = run_experiment(
        train_trials=train_trials,
        test_trials=test_trials,
        seed=seed,
        epochs=epochs,
        induction_calibration_trials=induction_calibration_trials,
        extractor_calibration_trials=extractor_calibration_trials,
        extractor_epochs=extractor_epochs,
        extractor_samples_per_image=extractor_samples_per_image,
    )
    for slice_payload in payload["slice_results"]:
        slice_payload.pop("results", None)
    return {
        "seed": seed,
        "agent_summary": payload["agent_summary"],
        "extractor_summary": payload["extractor_summary"],
        "semantic_summary": payload["semantic_summary"],
        "slice_results": payload["slice_results"],
    }


@app.local_entrypoint()
def main(
    train_trials: int = 3000,
    test_trials: int = 1200,
    epochs: int = 90,
    induction_calibration_trials: int = 1200,
    extractor_calibration_trials: int = 1200,
    extractor_epochs: int = 45,
    extractor_samples_per_image: int = 96,
) -> None:
    from experiments.concerned_syntax.learned_object_slots import (
        HELDOUT_ROLE_KINDS,
        HELDOUT_TRUE_PARSES,
        IMAGE_SIZE,
        LEARNED_OBJECT_SLOT_AGENTS,
        summarize_modal_slice_results,
        summarize_seed_payloads,
        write_learned_object_slots_report,
    )

    seeds = [20260622, 1729, 4242, 8675309, 314159]
    results = list(
        run_seed.starmap(
            [
                (
                    seed,
                    train_trials,
                    test_trials,
                    epochs,
                    induction_calibration_trials,
                    extractor_calibration_trials,
                    extractor_epochs,
                    extractor_samples_per_image,
                )
                for seed in seeds
            ]
        )
    )
    payload = {
        "manifest": {
            "arc": "2A",
            "name": "learned_object_slots_discovered_profiles_modal_sweep",
            "contract": "2A-v2-pixels-rich_programs-transfer",
            "seeds": seeds,
            "train_trials": train_trials,
            "test_trials": test_trials,
            "induction_calibration_trials": induction_calibration_trials,
            "extractor_calibration_trials": extractor_calibration_trials,
            "extractor_epochs": extractor_epochs,
            "extractor_samples_per_image": extractor_samples_per_image,
            "epochs": epochs,
            "heldout_kinds": list(HELDOUT_ROLE_KINDS),
            "heldout_parses": list(HELDOUT_TRUE_PARSES),
            "agents": list(LEARNED_OBJECT_SLOT_AGENTS),
            "image_size": IMAGE_SIZE,
            "perception": "learned_foreground_slots_plus_slot_local_center_search",
            "semantic_induction": "discovered_profiles_from_learned_object_slots",
            "provided_perception_priors": [
                "synthetic RGB renderer",
                "fixed six-slot layout",
                "slot-local center search",
            ],
            "removed_perception_priors": [
                "algorithmic connected-component extractor in accepted path",
            ],
            "provided_induction_priors": [
                "generic rich-program family menu",
                "bound/unbound parse alternatives",
            ],
            "removed_induction_priors": [
                "semantic kind profile table",
                "kind-to-family mapping",
                "kind-to-role-pair mapping",
                "kind-to-concern-weight mapping",
            ],
            "forbidden_induction_labels": [
                "visible role tokens",
                "example.trial.kind",
                "example.trial.roles",
                "supplied semantic profile table",
                "connected-component features in accepted path",
            ],
        },
        "results": results,
        "extractor_summary": summarize_seed_payloads(results, "extractor_summary"),
        "semantic_summary": summarize_seed_payloads(results, "semantic_summary"),
        "agent_summary": summarize_seed_payloads(results, "agent_summary"),
        "slice_results": summarize_modal_slice_results(results),
    }
    out = Path("artifacts/concerned_syntax/learned_object_slots_modal_sweep.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out}")

    report = Path(
        "experiments/concerned_syntax/results/"
        "learned_object_slots_modal_2026_06_22.md"
    )
    write_learned_object_slots_report(report, payload)
    print(f"Wrote {report}")
