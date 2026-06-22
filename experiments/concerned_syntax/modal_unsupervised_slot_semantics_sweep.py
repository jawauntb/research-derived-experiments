#!/usr/bin/env python3
"""Modal sweep for unsupervised slot-semantics transfer repair."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").add_local_python_source(
    "experiments"
)
app = modal.App(name="research-derived-unsupervised-slot-semantics")


@app.function(image=IMAGE, timeout=3600, cpu=1, memory=1024)
def run_slice_seed(
    base_seed: int,
    axis: str,
    heldout: str,
    slice_seed: int,
    train_trials: int,
    test_trials: int,
    epochs: int,
    induction_calibration_trials: int,
) -> dict[str, Any]:
    from experiments.concerned_syntax import rich_program_language as rich
    from experiments.concerned_syntax.unsupervised_slot_semantics import (
        induce_unsupervised_slot_semantics,
        run_slice,
    )

    calibration_examples = rich.make_filtered_pixel_examples(
        trials=induction_calibration_trials,
        seed=base_seed + 2_700_000,
    )
    inducer = induce_unsupervised_slot_semantics(
        calibration_examples,
        seed=base_seed + 2_900_000,
        epochs=max(20, epochs),
    )
    payload = run_slice(
        axis=axis,
        heldout=heldout,
        train_trials=train_trials,
        test_trials=test_trials,
        seed=slice_seed,
        epochs=epochs,
        inducer=inducer,
    )
    payload.pop("results", None)
    return {
        "seed": base_seed,
        "axis": axis,
        "heldout": heldout,
        "slice": payload,
    }


@app.local_entrypoint()
def main(
    train_trials: int = 3000,
    test_trials: int = 1200,
    epochs: int = 90,
    induction_calibration_trials: int = 1200,
) -> None:
    from experiments.concerned_syntax.unsupervised_slot_semantics import (
        HELDOUT_ROLE_KINDS,
        HELDOUT_TRUE_PARSES,
        UNSUPERVISED_SEMANTIC_AGENTS,
        summarize_modal_slice_results,
        summarize_seed_payloads,
        summarize_slice_payloads,
        write_unsupervised_report,
    )

    seeds = [20260618, 1729, 4242, 8675309, 314159]
    tasks: list[tuple[int, str, str, int, int, int, int, int]] = []
    for seed in seeds:
        for offset, heldout_kind in enumerate(HELDOUT_ROLE_KINDS):
            tasks.append(
                (
                    seed,
                    "role_kind",
                    heldout_kind,
                    seed + offset * 10_000,
                    train_trials,
                    test_trials,
                    epochs,
                    induction_calibration_trials,
                )
            )
        for offset, heldout_parse in enumerate(HELDOUT_TRUE_PARSES):
            tasks.append(
                (
                    seed,
                    "true_parse",
                    heldout_parse,
                    seed + 80_000 + offset * 10_000,
                    train_trials,
                    test_trials,
                    epochs,
                    induction_calibration_trials,
                )
            )

    slice_rows = list(run_slice_seed.starmap(tasks))
    results = []
    for seed in seeds:
        slice_payloads = [
            row["slice"]
            for row in slice_rows
            if int(row["seed"]) == seed
        ]
        results.append(
            {
                "seed": seed,
                "agent_summary": summarize_slice_payloads(slice_payloads),
                "semantic_summary": summarize_seed_payloads(
                    slice_payloads,
                    "semantic_summary",
                ),
                "slice_results": slice_payloads,
            }
        )
    payload = {
        "manifest": {
            "arc": "2A",
            "name": "unsupervised_slot_semantics_transfer_modal_sweep",
            "contract": "2A-v2-pixels-rich_programs-transfer",
            "seeds": seeds,
            "train_trials": train_trials,
            "test_trials": test_trials,
            "induction_calibration_trials": induction_calibration_trials,
            "epochs": epochs,
            "heldout_kinds": list(HELDOUT_ROLE_KINDS),
            "heldout_parses": list(HELDOUT_TRUE_PARSES),
            "agents": list(UNSUPERVISED_SEMANTIC_AGENTS),
            "perception": "connected_components_rgb_plus_unsupervised_slot_induction",
            "semantic_induction": (
                "label_free_connected_component_clusters_with_rich_program_feedback"
            ),
            "provided_induction_priors": [
                "semantic kind profile table",
                "program family by semantic profile",
            ],
            "allowed_induction_feedback": [
                "synthetic rich-program success",
                "action consistency",
                "viability regret",
            ],
            "forbidden_induction_labels": [
                "visible role tokens",
                "example.trial.roles",
            ],
        },
        "results": results,
        "semantic_summary": summarize_seed_payloads(results, "semantic_summary"),
        "agent_summary": summarize_seed_payloads(results, "agent_summary"),
        "slice_results": summarize_modal_slice_results(results),
    }
    out = Path("artifacts/concerned_syntax/unsupervised_slot_semantics_modal_sweep.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out}")

    report = Path(
        "experiments/concerned_syntax/results/"
        "unsupervised_slot_semantics_modal_2026_06_18.md"
    )
    write_unsupervised_report(report, payload)
    print(f"Wrote {report}")
