#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal L4 runner for Phase 6 actual open-model validation.

Dry-run budget:

    doppler --scope /Users/jawaun/superoptimizers run -- \
        uvx --python 3.12 --from modal modal run \
        experiments/phase6_real_model_validation/modal_l4_suite.py \
        --preset full --budget-usd 1000 --dry-run-budget

Full dispatch:

    doppler --scope /Users/jawaun/superoptimizers run -- \
        uvx --python 3.12 --from modal modal run \
        experiments/phase6_real_model_validation/modal_l4_suite.py \
        --preset full --budget-usd 1000 \
        --out artifacts/phase6_real_model_validation/l4_full_suite.json
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, "/root/project")
for parent in Path(__file__).resolve().parents:
    if (parent / "experiments").exists():
        sys.path.insert(0, str(parent))
        break

from experiments.phase6_real_model_validation.budget import estimate_modal_cost  # noqa: E402
from experiments.phase6_real_model_validation.core import (  # noqa: E402
    FROZEN_ENCODER_MODELS,
    OPEN_LM_MODELS,
    PRESETS,
)

modal = importlib.import_module("modal")

GPU = "L4"
TIMEOUT_SECONDS = 1800
MAX_CONTAINERS = 8
GPU_RATE_PER_SECOND = 0.000222


def _image() -> Any:
    return (
        modal.Image.debian_slim(python_version="3.12")
        .apt_install("git")
        .pip_install(
            "accelerate>=0.33,<2",
            "numpy>=1.26,<2.2",
            "pytest>=8,<10",
            "ruff>=0.8,<1.0",
            "sentence-transformers>=3.0,<6",
            "torch>=2.3,<2.8",
            "transformers>=4.45,<4.57",
            "uv>=0.7,<1.0",
        )
        .add_local_dir(".", remote_path="/root/project")
    )


IMAGE = _image()
app = modal.App(name="research-derived-phase6-real-model-validation")


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=TIMEOUT_SECONDS,
    cpu=4,
    memory=16384,
    max_containers=MAX_CONTAINERS,
    single_use_containers=True,
    retries=1,
)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import sys

    sys.path.insert(0, "/root/project")
    from experiments.phase6_real_model_validation.real_models import (
        run_frozen_encoder_model,
        run_open_lm_model,
    )

    track = str(arg["track"])
    model_key = str(arg["model_key"])
    if track == "open_lm_action_coupling":
        row = run_open_lm_model(model_key)
    elif track == "frozen_encoder_metric_deformation":
        row = run_frozen_encoder_model(model_key)
    else:
        raise ValueError(f"unknown track {track!r}")
    return {
        "cell": {"track": track, "model_key": model_key, "preset": arg["preset"], "gpu": GPU},
        "rows": [row],
    }


@app.function(image=IMAGE, gpu=GPU, timeout=1200, cpu=2, memory=4096, single_use_containers=True)
def quality_cell() -> dict[str, Any]:
    import subprocess
    import sys

    commands = [
        [sys.executable, "-m", "pytest", "tests/test_phase6_real_model_validation.py"],
        [
            sys.executable,
            "-m",
            "compileall",
            "experiments/phase6_real_model_validation",
            "scripts/build_phase6_real_model_validation_pdf.py",
        ],
        [
            "ruff",
            "check",
            "experiments/phase6_real_model_validation",
            "scripts/build_phase6_real_model_validation_pdf.py",
            "tests/test_phase6_real_model_validation.py",
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


@app.function(image=IMAGE, timeout=1200, cpu=2, memory=4096, single_use_containers=True)
def summarize_cell(rows: list[dict[str, Any]]) -> dict[str, Any]:
    import sys

    sys.path.insert(0, "/root/project")
    from experiments.phase6_real_model_validation.core import summarize_rows

    return summarize_rows(rows)


def _build_cells(preset: str, tracks: list[str], model_keys: list[str] | None) -> list[dict[str, str]]:
    cfg = PRESETS[preset]
    selected = set(model_keys or [])
    cells: list[dict[str, str]] = []
    if "open_lm_action_coupling" in tracks:
        for model_key in cfg.lm_models:
            if not selected or model_key in selected:
                cells.append({"track": "open_lm_action_coupling", "model_key": model_key, "preset": preset})
    if "frozen_encoder_metric_deformation" in tracks:
        for model_key in cfg.encoder_models:
            if not selected or model_key in selected:
                cells.append({"track": "frozen_encoder_metric_deformation", "model_key": model_key, "preset": preset})
    return cells


@app.local_entrypoint()
def main(
    preset: str = "full",
    tracks: str = "open_lm_action_coupling,frozen_encoder_metric_deformation",
    models: str = "",
    budget_usd: float = 1000.0,
    out: str = "artifacts/phase6_real_model_validation/l4_full_suite.json",
    dry_run_budget: bool = False,
    quality_only: bool = False,
) -> None:
    if quality_only:
        result = quality_cell.remote()
        print(json.dumps(result, indent=2, sort_keys=True))
        if not result["ok"]:
            raise SystemExit("Modal quality checks failed")
        return

    if preset not in PRESETS:
        raise SystemExit(f"unknown preset {preset!r}")
    track_list = [t.strip() for t in tracks.split(",") if t.strip()]
    model_list = [m.strip() for m in models.split(",") if m.strip()] or None
    known = set(OPEN_LM_MODELS) | set(FROZEN_ENCODER_MODELS)
    unknown = sorted(set(model_list or []) - known)
    if unknown:
        raise SystemExit(f"unknown model keys: {unknown}")
    cells = _build_cells(preset, track_list, model_list)
    estimate = estimate_modal_cost(
        len(cells),
        budget_usd,
        gpu=GPU,
        timeout_seconds=TIMEOUT_SECONDS,
        max_containers=MAX_CONTAINERS,
        gpu_rate_per_second=GPU_RATE_PER_SECOND,
    )
    manifest = {
        "kind": "phase6_real_model_validation_l4_manifest",
        "preset": preset,
        "tracks": track_list,
        "models": [cell["model_key"] for cell in cells],
        "gpu": GPU,
        "max_containers": MAX_CONTAINERS,
        "budget_estimate": estimate,
        "claim_level": PRESETS[preset].claim_level,
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
        "kind": "phase6_real_model_validation_l4_suite",
        "manifest": manifest,
        "cells": [p["cell"] for p in payloads],
        "rows": rows,
        "summary": summarize_cell.remote(rows),
    }
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(final_payload, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {len(rows)} rows to {out_path}")
