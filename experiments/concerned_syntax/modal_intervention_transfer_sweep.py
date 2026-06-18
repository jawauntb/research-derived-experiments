#!/usr/bin/env python3
"""Modal transfer sweep for the 2A-v1 intervention-invention contract."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").add_local_python_source(
    "experiments"
)
app = modal.App(name="research-derived-intervention-transfer")


@app.function(image=IMAGE, timeout=1800, cpu=1, memory=1024)
def run_iid_seed(
    seed: int,
    train_trials: int,
    test_trials: int,
    epochs: int,
) -> dict[str, Any]:
    from experiments.concerned_syntax.intervention_invention import run_experiment

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


@app.function(image=IMAGE, timeout=1800, cpu=1, memory=1024)
def run_transfer_slice(
    seed: int,
    axis: str,
    heldout: str,
    train_trials: int,
    test_trials: int,
    epochs: int,
) -> dict[str, Any]:
    from experiments.concerned_syntax.intervention_invention import (
        run_parse_transfer_experiment,
        run_role_transfer_experiment,
    )

    if axis == "role_kind":
        payload = run_role_transfer_experiment(
            train_trials=train_trials,
            test_trials=test_trials,
            seed=seed,
            epochs=epochs,
            heldout_kind=heldout,
        )
    elif axis == "true_parse":
        payload = run_parse_transfer_experiment(
            train_trials=train_trials,
            test_trials=test_trials,
            seed=seed,
            epochs=epochs,
            heldout_parse=heldout,
        )
    else:
        raise KeyError(axis)
    return {
        "seed": seed,
        "axis": axis,
        "heldout": heldout,
        "manifest": payload["manifest"],
        "agent_summary": payload["agent_summary"],
    }


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@app.local_entrypoint()
def main(
    train_trials: int = 3000,
    test_trials: int = 1200,
    epochs: int = 90,
    heldout_kinds: str = "shield_poison,repair_core,food_trap",
    heldout_parses: str = "repeat_concat,hooked_repeat,alternating_bind,edge_core",
) -> None:
    from experiments.concerned_syntax.intervention_invention import (
        CONTRACT_NAME,
        IMAGE_SIZE,
        PROGRAM_AGENTS,
        candidate_programs,
        summarize_transfer_payloads,
        write_transfer_report,
    )

    seeds = [20260616, 1729, 4242, 8675309, 314159]
    role_kinds = _split_csv(heldout_kinds)
    parse_families = _split_csv(heldout_parses)
    iid_payloads = list(
        run_iid_seed.starmap(
            [(seed, train_trials, test_trials, epochs) for seed in seeds]
        )
    )
    slice_args = [
        (seed, "role_kind", heldout, train_trials, test_trials, epochs)
        for seed in seeds
        for heldout in role_kinds
    ]
    slice_args.extend(
        [
            (seed, "true_parse", heldout, train_trials, test_trials, epochs)
            for seed in seeds
            for heldout in parse_families
        ]
    )
    slice_payloads = list(run_transfer_slice.starmap(slice_args))

    iid_by_seed = {payload["seed"]: payload for payload in iid_payloads}
    slices_by_seed: dict[int, list[dict[str, Any]]] = {seed: [] for seed in seeds}
    for slice_payload in slice_payloads:
        slices_by_seed[slice_payload["seed"]].append(
            {
                "axis": slice_payload["axis"],
                "heldout": slice_payload["heldout"],
                "manifest": slice_payload["manifest"],
                "agent_summary": slice_payload["agent_summary"],
            }
        )
    seed_payloads = [
        {
            "seed": seed,
            "iid_agent_summary": iid_by_seed[seed]["agent_summary"],
            "transfer_slices": slices_by_seed[seed],
        }
        for seed in seeds
    ]
    payload = {
        "manifest": {
            "arc": "2A",
            "name": "intervention_transfer_modal_sweep",
            "contract": CONTRACT_NAME,
            "seeds": seeds,
            "train_trials": train_trials,
            "test_trials": test_trials,
            "epochs": epochs,
            "heldout_kinds": list(role_kinds),
            "heldout_parses": list(parse_families),
            "agents": list(PROGRAM_AGENTS),
            "programs": [program.name for program in candidate_programs()],
            "image_size": IMAGE_SIZE,
            "perception": "connected_components_rgb",
        },
        "seed_payloads": seed_payloads,
        "iid_payloads": iid_payloads,
        "slice_payloads": slice_payloads,
        "iid_agent_summary": seed_payloads[0]["iid_agent_summary"],
        "transfer_slices": seed_payloads[0]["transfer_slices"],
        "summary": summarize_transfer_payloads(seed_payloads),
    }
    out = Path("artifacts/concerned_syntax/intervention_transfer_modal_sweep.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out}")

    report = Path(
        "experiments/concerned_syntax/results/"
        "intervention_transfer_modal_2026_06_16.md"
    )
    write_transfer_report(report, payload)
    print(f"Wrote {report}")
