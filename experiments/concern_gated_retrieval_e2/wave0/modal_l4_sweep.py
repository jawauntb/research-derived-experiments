#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal L4 fan-out for the Concern-Gated Retrieval Wave 0 calibration.

Wave 0 operating rule: L4 GPUs only, deploy before spawn, cost ceiling at
or below 35% of the equivalent H100 rate (Modal L4 at ``$0.80/hr`` is
~23% of Modal H100 at ``$3.40/hr``). Doppler scope is
``/Users/jawaun/superoptimizers``. The build brief pins
``max_containers=10``, ``single_use_containers=True``, ``retries=1``,
``cpu=4``, ``memory=16384``, and ``timeout=1800``; those knobs are
locked here and must not be relaxed without a Wave 0 redesign.

Dispatch is done outside this module by
``scripts/deploy_and_run_cogr_wave0.sh`` — first ``modal deploy`` this
file, then ``modal run --preset calibration --out
artifacts/cogr_wave0/calibration.json``. The local entrypoint prints the
plan and refuses to fan out if the conservative cost estimate exceeds
``$10.0``, per the build brief.

Wave 0 boundary. This module fans out the calibration orchestrator in
:mod:`.calibrate`; it does not test learned memory geometry, concern
recovery, semantic meaning, or selfhood. See
``docs/concern_gated_retrieval_research_program.md`` for the claim
ladder.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any


# Extend ``sys.path`` for two runtimes:
#   * inside the Modal container the repo lives at ``/root/project`` (see
#     :func:`_image` below);
#   * locally (dry-run, ``modal deploy``) the repo root is
#     ``file.parent.parent.parent.parent``.
sys.path.insert(0, "/root/project")
for parent in Path(__file__).resolve().parents:
    if (parent / "experiments").exists():
        sys.path.insert(0, str(parent))
        break


# Import after the ``sys.path`` shims so the two runtimes agree on the
# module identity.
from experiments.concern_gated_retrieval_e2.wave0.calibrate import (  # noqa: E402
    CELL_TIMEOUT_SECONDS,
    DEFAULT_SUMMARY_PATH,
    CellPlan,
    L4_GPU_RATE_PER_SECOND,
    MAX_CONTAINERS,
    build_cells,
    estimate_cost_usd,
    merge_payloads,
    slim_public_summary,
    write_calibration_summary,
)


modal = importlib.import_module("modal")


APP_NAME = "research-derived-cogr-wave0-calibration"
GPU = "L4"
TIMEOUT_SECONDS = CELL_TIMEOUT_SECONDS
CPU = 4
MEMORY_MB = 16_384
CONTAINER_CEILING = MAX_CONTAINERS
GPU_RATE_PER_SECOND = L4_GPU_RATE_PER_SECOND
HARD_CAP_USD = 10.0


def _image() -> Any:
    """Return the Modal image the L4 workers run inside.

    Pattern follows ``experiments/phase6_real_model_validation/modal_l4_suite.py``:
    ``debian_slim`` + Python 3.12, pip installs ``torch``,
    ``sentence-transformers``, ``numpy``, and ``uv`` so the Wave 0
    baseline slate (which optionally uses ``sentence-transformers`` for
    the ``embedding_similarity`` baseline) can execute inside the
    container without a network fetch at run time. ``add_local_dir(".")``
    ships the local project into ``/root/project``.
    """
    return (
        modal.Image.debian_slim(python_version="3.12")
        .apt_install("git")
        .pip_install(
            "numpy>=1.26,<2.2",
            "pytest>=8,<10",
            "ruff>=0.8,<1.0",
            "sentence-transformers>=3.0,<6",
            "torch>=2.3,<2.8",
            "uv>=0.7,<1.0",
        )
        .add_local_dir(
            ".",
            remote_path="/root/project",
            ignore=[
                ".git",
                ".worktrees",
                ".venv",
                "__pycache__",
                "*.pyc",
                "artifacts",
                "references/papers",
                "references/text",
                "references/html",
                "tmp",
                "output",
                "papers/*/paper.pdf",
                "papers/pdf",
                "**/*.png",
            ],
        )
    )


IMAGE = _image()
app = modal.App(name=APP_NAME)


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=TIMEOUT_SECONDS,
    cpu=CPU,
    memory=MEMORY_MB,
    max_containers=CONTAINER_CEILING,
    single_use_containers=True,
    retries=1,
)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    """Run one Wave 0 calibration cell inside an L4 worker.

    ``arg`` is a plain dict shaped by :meth:`CellPlan.to_dict`. Returns
    ``{"cell": {...}, "rows": [...], "coverage": {...}, "wall_seconds":
    ...}``. The container re-imports the orchestrator locally so the
    Modal deploy step and the fan-out step exchange only plain dicts.
    """
    # Re-add ``/root/project`` at cell scope so the container has the
    # local project on its path even when Modal serializes the function
    # without re-running module-level shims.
    import sys as _sys

    _sys.path.insert(0, "/root/project")
    from experiments.concern_gated_retrieval_e2.wave0.calibrate import (
        execute_cell as _execute_cell,
    )

    return _execute_cell(arg)


def _preset_cells(preset: str, seeds_per_cell: int) -> tuple[CellPlan, ...]:
    if preset == "calibration":
        return build_cells(seeds_per_cell=seeds_per_cell)
    if preset == "smoke":
        return build_cells(
            families=("delayed_commitments",),
            density_levels=("light",),
            budgets=(2,),
            epsilons=(0.05,),
            seeds_per_cell=min(seeds_per_cell, 4),
        )
    raise SystemExit(f"unknown preset {preset!r}")


@app.local_entrypoint()
def main(
    preset: str = "calibration",
    seeds_per_cell: int = 24,
    out: str = "artifacts/cogr_wave0/calibration.json",
    hard_cap_usd: float = HARD_CAP_USD,
    dry_run_budget: bool = False,
) -> None:
    """Modal local entrypoint. Fans out over cells and writes the summary.

    Steps:

    1. Build the cell plan for ``preset``.
    2. Estimate cost. Refuse if conservative timeout-based cost exceeds
       ``hard_cap_usd`` (Wave 0 build brief: ``$10.0``).
    3. If ``dry_run_budget`` is truthy, print the plan and return.
    4. Fan out :func:`run_cell` across the cell list using ``.map`` and
       merge the per-cell payloads via :func:`merge_payloads`.
    5. Write the JSON receipt to ``out`` (a raw-artifacts path per
       ``AGENTS.md``; the committed public summary lives at
       ``experiments/concern_gated_retrieval_e2/wave0/results/calibration_summary.json``
       and is produced by the local :mod:`.calibrate` CLI, not by Modal).
    """
    cells = _preset_cells(preset, seeds_per_cell)
    estimate = estimate_cost_usd(
        len(cells),
        hard_cap_usd=hard_cap_usd,
        max_containers=CONTAINER_CEILING,
        cell_timeout_seconds=TIMEOUT_SECONDS,
        gpu_rate_per_second=GPU_RATE_PER_SECOND,
    )
    manifest = {
        "kind": "cogr_wave0_modal_manifest",
        "app": APP_NAME,
        "preset": preset,
        "gpu": GPU,
        "cpu": CPU,
        "memory_mb": MEMORY_MB,
        "max_containers": CONTAINER_CEILING,
        "timeout_seconds": TIMEOUT_SECONDS,
        "gpu_rate_per_second": GPU_RATE_PER_SECOND,
        "n_cells": len(cells),
        "seeds_per_cell": seeds_per_cell,
        "hard_cap_usd": hard_cap_usd,
        "estimate": {
            "conservative_cost_usd": estimate.conservative_cost_usd,
            "wallclock_upper_bound_cost_usd": (
                estimate.wallclock_upper_bound_cost_usd
            ),
            "wallclock_upper_bound_seconds": (
                estimate.wallclock_upper_bound_seconds
            ),
            "within_hard_cap": estimate.within_hard_cap,
        },
    }
    print(json.dumps({"kind": "dry-run manifest", "manifest": manifest}, indent=2, sort_keys=True))

    if not estimate.within_hard_cap:
        raise SystemExit(
            "Refusing to dispatch: conservative timeout-based Modal cost "
            f"${estimate.conservative_cost_usd:.2f} exceeds hard cap "
            f"${hard_cap_usd:.2f}."
        )
    if dry_run_budget:
        return

    cell_args = [cell.to_dict() for cell in cells]
    payloads = list(run_cell.map(cell_args))
    merged = merge_payloads(payloads)
    merged["manifest"] = manifest

    # Raw run receipt (per-row baseline data) lives under gitignored
    # ``artifacts/`` per ``AGENTS.md``. The committed public summary
    # (slim: cells + summary + manifest, no per-row data) lives under
    # ``experiments/concern_gated_retrieval_e2/wave0/results/``.
    raw_out_path = Path(out)
    write_calibration_summary(merged, raw_out_path)
    print(f"Wrote raw calibration receipt to {raw_out_path}")

    slim_out_path = DEFAULT_SUMMARY_PATH
    write_calibration_summary(slim_public_summary(merged), slim_out_path)
    print(f"Wrote slim public summary to {slim_out_path}")


__all__ = [
    "APP_NAME",
    "CONTAINER_CEILING",
    "CPU",
    "GPU",
    "GPU_RATE_PER_SECOND",
    "HARD_CAP_USD",
    "IMAGE",
    "MEMORY_MB",
    "TIMEOUT_SECONDS",
    "app",
    "main",
    "run_cell",
]
