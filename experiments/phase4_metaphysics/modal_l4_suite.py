#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal L4 runner for Phase 4 Metaphysics diagnostics.

Dry-run budget:

    doppler --scope /Users/jawaun/superoptimizers run -- \
        uvx --python 3.12 --from modal modal run \
        experiments/phase4_metaphysics/modal_l4_suite.py \
        --preset full --budget-usd 1000 --dry-run-budget

Full dispatch:

    doppler --scope /Users/jawaun/superoptimizers run -- \
        uvx --python 3.12 --from modal modal run \
        experiments/phase4_metaphysics/modal_l4_suite.py \
        --preset full --budget-usd 1000 \
        --out artifacts/phase4_metaphysics/l4_full_suite.json
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

GPU = "L4"
TIMEOUT_SECONDS = 900
MAX_CONTAINERS = 64
GPU_RATE_PER_SECOND = 0.000222


def _image() -> Any:
    return (
        modal.Image.debian_slim(python_version="3.12")
        .apt_install("git")
        .pip_install("numpy>=1.26,<2.2", "pytest>=8,<10", "ruff>=0.8,<1.0", "uv>=0.7,<1.0")
        .add_local_dir(".", remote_path="/root/project")
    )


IMAGE = _image()
app = modal.App(name="research-derived-phase4-metaphysics")


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
    from experiments.phase4_metaphysics.core import run_cell as run_phase4_cell

    track = str(arg["track"])
    seed = int(arg["seed"])
    preset = str(arg["preset"])
    rows = run_phase4_cell(track, seed, preset)
    return {
        "cell": {"track": track, "seed": seed, "preset": preset, "gpu": GPU},
        "rows": rows,
    }


@app.function(image=IMAGE, gpu=GPU, timeout=1200, cpu=2, memory=4096, single_use_containers=True)
def quality_cell() -> dict[str, Any]:
    import subprocess
    import sys

    commands = [
        [sys.executable, "-m", "pytest", "tests/test_phase4_metaphysics.py"],
        [sys.executable, "-m", "compileall", "experiments/phase4_metaphysics", "scripts/build_phase4_metaphysics_pdf.py"],
        ["ruff", "check", "experiments/phase4_metaphysics", "scripts/build_phase4_metaphysics_pdf.py", "tests/test_phase4_metaphysics.py"],
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


@app.function(image=IMAGE, timeout=1200, cpu=2, memory=4096, single_use_containers=True)
def summarize_cell(rows: list[dict[str, Any]]) -> dict[str, Any]:
    import sys

    sys.path.insert(0, "/root/project")
    from experiments.phase4_metaphysics.core import summarize_rows

    return summarize_rows(rows)


def _estimate_cost(cells: int, budget_usd: float) -> dict[str, Any]:
    conservative = cells * TIMEOUT_SECONDS * GPU_RATE_PER_SECOND
    return {
        "gpu": GPU,
        "cells": cells,
        "timeout_seconds": TIMEOUT_SECONDS,
        "max_containers": MAX_CONTAINERS,
        "gpu_rate_per_second": GPU_RATE_PER_SECOND,
        "conservative_cost_usd": conservative,
        "budget_usd": budget_usd,
        "within_budget": conservative <= budget_usd,
    }


@app.local_entrypoint()
def main(
    preset: str = "full",
    tracks: str = "language_scale,neural_symmetry,learned_regimes,probe_value,beyond_ceiling,semantic_metric,topology_mediation",
    seeds: int = 48,
    budget_usd: float = 1000.0,
    out: str = "artifacts/phase4_metaphysics/l4_full_suite.json",
    dry_run_budget: bool = False,
    quality_only: bool = False,
) -> None:
    if quality_only:
        result = quality_cell.remote()
        print(json.dumps(result, indent=2, sort_keys=True))
        if not result["ok"]:
            raise SystemExit("Modal quality checks failed")
        return

    track_list = [t.strip() for t in tracks.split(",") if t.strip()]
    cells = [
        {"track": track, "seed": seed, "preset": preset}
        for seed in range(seeds)
        for track in track_list
    ]
    estimate = _estimate_cost(len(cells), budget_usd)
    manifest = {
        "kind": "phase4_metaphysics_l4_manifest",
        "preset": preset,
        "tracks": track_list,
        "seeds": seeds,
        "gpu": GPU,
        "max_containers": MAX_CONTAINERS,
        "budget_estimate": estimate,
        "claim_level": "diagnostic controlled-harness result",
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
        "kind": "phase4_metaphysics_l4_suite",
        "manifest": manifest,
        "cells": [p["cell"] for p in payloads],
        "rows": rows,
        "summary": summarize_cell.remote(rows),
    }
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(final_payload, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {len(rows)} rows to {out_path}")
