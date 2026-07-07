#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal L4 runner for Gauge-Fixed Concern Transport synthetic gates.

Dry-run budget:

    doppler --scope /Users/jawaun/superoptimizers run -- \
        uvx --python 3.12 --from modal modal run \
        experiments/gauge_fixed_concern_transport/modal_l4_suite.py \
        --preset full --seeds 64 --budget-usd 250 --dry-run-budget

Full dispatch:

    doppler --scope /Users/jawaun/superoptimizers run -- \
        uvx --python 3.12 --from modal modal run \
        experiments/gauge_fixed_concern_transport/modal_l4_suite.py \
        --preset full --seeds 64 --budget-usd 250 \
        --out artifacts/gauge_fixed_concern_transport/l4_full_suite.json
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, "/root/project")
for parent in Path(__file__).resolve().parents:
    if (parent / "experiments").exists():
        sys.path.insert(0, str(parent))
        break

from experiments.gauge_fixed_concern_transport.budget import estimate_modal_cost  # noqa: E402

modal = importlib.import_module("modal")

GPU = "L4"
TIMEOUT_SECONDS = 900
MAX_CONTAINERS = 64
GPU_RATE_PER_SECOND = 0.000222
TRACKS = [
    "concern_weighted_ood",
    "causal_gauge_fixing",
    "mechanistic_commitment",
    "reafference_null",
    "moved_bottleneck",
]
CLAIM_LEVELS = {
    "smoke": "local smoke for synthetic gate logic",
    "full": "synthetic Modal L4 empirical validation result",
}


def _image() -> Any:
    return (
        modal.Image.debian_slim(python_version="3.12")
        .apt_install("git")
        .pip_install("numpy>=1.26,<2.2", "pytest>=8,<10", "ruff>=0.8,<1.0")
        .add_local_dir(".", remote_path="/root/project")
    )


IMAGE = _image()
app = modal.App(name="research-derived-gfc-transport")


def _gpu_name() -> str:
    proc = subprocess.run(
        ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if proc.returncode != 0:
        return "unavailable"
    return proc.stdout.strip().splitlines()[0]


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=TIMEOUT_SECONDS,
    cpu=2,
    memory=4096,
    max_containers=MAX_CONTAINERS,
    single_use_containers=True,
    retries=1,
)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import sys

    sys.path.insert(0, "/root/project")
    from experiments.gauge_fixed_concern_transport.core import run_cell as run_suite_cell

    row = run_suite_cell(str(arg["track"]), int(arg["seed"]), str(arg["preset"]))
    row["gpu_name"] = _gpu_name()
    return {
        "cell": {
            "track": arg["track"],
            "seed": arg["seed"],
            "preset": arg["preset"],
            "gpu": GPU,
            "gpu_name": row["gpu_name"],
        },
        "rows": [row],
    }


@app.function(image=IMAGE, gpu=GPU, timeout=1200, cpu=2, memory=4096, single_use_containers=True)
def quality_cell() -> dict[str, Any]:
    import subprocess
    import sys

    commands = [
        [sys.executable, "-m", "pytest", "tests/test_gauge_fixed_concern_transport_experiments.py"],
        [
            sys.executable,
            "-m",
            "compileall",
            "experiments/gauge_fixed_concern_transport",
            "scripts/make_gauge_fixed_concern_transport_figures.py",
            "scripts/build_gauge_fixed_concern_transport_pdf.py",
        ],
        [
            "ruff",
            "check",
            "experiments/gauge_fixed_concern_transport",
            "scripts/make_gauge_fixed_concern_transport_figures.py",
            "scripts/build_gauge_fixed_concern_transport_pdf.py",
            "tests/test_gauge_fixed_concern_transport_experiments.py",
        ],
    ]
    results = []
    for cmd in commands:
        proc = subprocess.run(
            cmd,
            cwd="/root/project",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        results.append({"cmd": cmd, "returncode": proc.returncode, "output_tail": proc.stdout[-4000:]})
        if proc.returncode != 0:
            return {"ok": False, "results": results}
    return {"ok": True, "results": results}


@app.function(image=IMAGE, timeout=600, cpu=2, memory=4096, single_use_containers=True)
def summarize_cell(rows: list[dict[str, Any]]) -> dict[str, Any]:
    import sys

    sys.path.insert(0, "/root/project")
    from experiments.gauge_fixed_concern_transport.core import summarize_rows

    return summarize_rows(rows)


@app.local_entrypoint()
def main(
    preset: str = "full",
    tracks: str = ",".join(TRACKS),
    seeds: int = 64,
    budget_usd: float = 250.0,
    out: str = "artifacts/gauge_fixed_concern_transport/l4_full_suite.json",
    dry_run_budget: bool = False,
    quality_only: bool = False,
) -> None:
    if quality_only:
        result = quality_cell.remote()
        print(json.dumps(result, indent=2, sort_keys=True))
        if not result["ok"]:
            raise SystemExit("Modal quality checks failed")
        return

    if preset not in CLAIM_LEVELS:
        raise SystemExit(f"unknown preset {preset!r}")
    track_list = [track.strip() for track in tracks.split(",") if track.strip()]
    unknown_tracks = sorted(set(track_list) - set(TRACKS))
    if unknown_tracks:
        raise SystemExit(f"unknown tracks: {unknown_tracks}")
    cells = [
        {"track": track, "seed": seed, "preset": preset}
        for seed in range(seeds)
        for track in track_list
    ]
    estimate = estimate_modal_cost(
        len(cells),
        budget_usd,
        gpu=GPU,
        timeout_seconds=TIMEOUT_SECONDS,
        max_containers=MAX_CONTAINERS,
        gpu_rate_per_second=GPU_RATE_PER_SECOND,
    )
    manifest = {
        "kind": "gauge_fixed_concern_transport_l4_manifest",
        "preset": preset,
        "tracks": track_list,
        "seeds": seeds,
        "gpu": GPU,
        "max_containers": MAX_CONTAINERS,
        "budget_estimate": estimate,
        "claim_level": CLAIM_LEVELS[preset],
    }
    print(json.dumps({"kind": "dry-run manifest", "manifest": manifest}, indent=2, sort_keys=True))
    if not estimate["within_budget"]:
        raise SystemExit(
            "Refusing to dispatch: conservative timeout-based Modal cost "
            f"${estimate['conservative_cost_usd']:.2f} exceeds budget ${budget_usd:.2f}."
        )
    if dry_run_budget:
        return

    payloads = list(run_cell.map(cells))
    rows: list[dict[str, Any]] = []
    for payload in payloads:
        rows.extend(payload["rows"])
    final_payload = {
        "kind": "gauge_fixed_concern_transport_l4_suite",
        "manifest": manifest,
        "cells": [payload["cell"] for payload in payloads],
        "rows": rows,
        "summary": summarize_cell.remote(rows),
    }
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(final_payload, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {len(rows)} rows to {out_path}")
