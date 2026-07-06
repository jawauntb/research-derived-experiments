#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal L4 runner for the virtual-governor stress-signal diagnostic."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

GPU = "L4"
TIMEOUT_SECONDS = 900
MAX_CONTAINERS = 24
GPU_RATE_PER_SECOND = 0.000222
CONDITIONS = (
    "reward_only",
    "local_state",
    "stale_governor",
    "wrong_governor",
    "virtual_governor",
)


def _image() -> Any:
    return (
        modal.Image.debian_slim(python_version="3.12")
        .apt_install("git")
        .pip_install(
            "markdown-pdf>=1.7,<2",
            "matplotlib>=3.8,<4.0",
            "numpy>=1.26,<2.2",
            "pytest>=8,<10",
            "ruff>=0.8,<1.0",
            "scipy>=1.13,<2",
            "torch>=2.5,<2.8",
            "ty",
            "uv>=0.7,<1.0",
        )
        .add_local_dir(".", remote_path="/root/project")
    )


IMAGE = _image()
app = modal.App(name="research-derived-virtual-governor-stress")


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=TIMEOUT_SECONDS,
    cpu=4,
    memory=8192,
    max_containers=MAX_CONTAINERS,
    single_use_containers=True,
    retries=1,
)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import sys

    sys.path.insert(0, "/root/project")
    from experiments.virtual_governor_stress_signal.core import run_trial

    row = run_trial(
        condition=str(arg["condition"]),
        seed=int(arg["seed"]),
        device="cuda",
        train_episodes=int(arg["train_episodes"]),
        train_steps=int(arg["train_steps"]),
        eval_episodes=int(arg["eval_episodes"]),
        eval_steps=int(arg["eval_steps"]),
        shift_period=int(arg["shift_period"]),
        post_shift_window=int(arg["post_shift_window"]),
        epochs=int(arg["epochs"]),
    )
    return row.to_record()


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=1200,
    cpu=4,
    memory=8192,
    single_use_containers=True,
)
def artifact_cell(payload_text: str) -> list[dict[str, str]]:
    import base64
    import subprocess
    import sys
    import tempfile

    sys.path.insert(0, "/root/project")
    sys.path.insert(0, "/root/project/scripts")
    from experiments.virtual_governor_stress_signal.summarize import build_artifacts

    payload = json.loads(payload_text)
    with tempfile.TemporaryDirectory() as tmp:
        out_root = Path(tmp)
        paths = build_artifacts(payload, out_root)
        paper_dir = out_root / "papers/virtual_governor_stress_signal"
        pdf_path = paper_dir / "paper.pdf"
        subprocess.run(
            [
                "python",
                "/root/project/scripts/render_paper_pdf.py",
                "--in",
                str(paper_dir / "paper.md"),
                "--out",
                str(pdf_path),
                "--title",
                "Virtual-Governor Stress Signals for Local Action Recovery",
                "--author",
                "Jawaun Brown",
            ],
            check=True,
            cwd="/root/project",
        )
        paths.append(pdf_path)
        artifacts = []
        for path in paths:
            rel_path = path.relative_to(out_root)
            artifacts.append(
                {
                    "path": str(rel_path),
                    "data_b64": base64.b64encode(path.read_bytes()).decode("ascii"),
                }
            )
        return artifacts


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=1800,
    cpu=4,
    memory=8192,
    single_use_containers=True,
)
def quality_cell() -> dict[str, Any]:
    from pathlib import Path
    import subprocess
    import sys

    sys.path.insert(0, "/root/project")
    git_probe = subprocess.run(
        ["git", "ls-files"],
        cwd="/root/project",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if git_probe.returncode != 0:
        git_path = Path("/root/project/.git")
        if git_path.is_file():
            git_path.unlink()
        subprocess.run(["git", "init"], cwd="/root/project", check=True)
        subprocess.run(["git", "add", "-A"], cwd="/root/project", check=True)
    commands = [
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_virtual_governor_stress_signal.py",
        ],
        [
            sys.executable,
            "-m",
            "compileall",
            "experiments/virtual_governor_stress_signal",
            "tests/test_virtual_governor_stress_signal.py",
            "scripts/modal_lineage_paper_tasks.py",
        ],
        [sys.executable, "scripts/publication_guard.py"],
        ["ruff", "check", "."],
        ["ty", "check", "scripts", "experiments", "tests"],
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
        results.append(
            {
                "cmd": cmd,
                "returncode": proc.returncode,
                "output_tail": proc.stdout[-6000:],
            }
        )
        if proc.returncode != 0:
            return {"ok": False, "results": results}
    return {"ok": True, "results": results}


def _estimate_cost(cells: int, budget_usd: float) -> dict[str, Any]:
    conservative = cells * TIMEOUT_SECONDS * GPU_RATE_PER_SECOND
    return {
        "gpu": GPU,
        "cells": cells,
        "timeout_seconds": TIMEOUT_SECONDS,
        "gpu_rate_per_second": GPU_RATE_PER_SECOND,
        "conservative_cost_usd": conservative,
        "budget_usd": budget_usd,
        "within_budget": conservative <= budget_usd,
    }


@app.local_entrypoint()
def main(
    seeds: int = 8,
    base_seed: int = 20260706,
    train_episodes: int = 96,
    train_steps: int = 56,
    eval_episodes: int = 96,
    eval_steps: int = 72,
    shift_period: int = 18,
    post_shift_window: int = 16,
    epochs: int = 180,
    budget_usd: float = 50.0,
    out: str = "artifacts/virtual_governor_stress_signal/l4_sweep.json",
    dry_run_budget: bool = False,
    artifacts_only: bool = False,
    artifact_input: str = "artifacts/virtual_governor_stress_signal/l4_sweep.json",
    quality_only: bool = False,
) -> None:
    if quality_only:
        result = quality_cell.remote()
        print(json.dumps(result, indent=2, sort_keys=True))
        if not result["ok"]:
            raise SystemExit("Modal quality checks failed")
        return

    if artifacts_only:
        import base64

        payload_text = Path(artifact_input).read_text()
        artifacts = artifact_cell.remote(payload_text)
        for artifact in artifacts:
            path = Path(artifact["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(base64.b64decode(artifact["data_b64"]))
            print(f"Wrote {path}")
        return

    cells = []
    for condition in CONDITIONS:
        for seed_idx in range(seeds):
            cells.append(
                {
                    "condition": condition,
                    "seed": base_seed + seed_idx * 1_003,
                    "train_episodes": train_episodes,
                    "train_steps": train_steps,
                    "eval_episodes": eval_episodes,
                    "eval_steps": eval_steps,
                    "shift_period": shift_period,
                    "post_shift_window": post_shift_window,
                    "epochs": epochs,
                }
            )
    estimate = _estimate_cost(len(cells), budget_usd)
    manifest = {
        "suite": "virtual governor stress-signal diagnostic",
        "conditions": list(CONDITIONS),
        "seeds_per_condition": seeds,
        "base_seed": base_seed,
        "train_episodes": train_episodes,
        "train_steps": train_steps,
        "eval_episodes": eval_episodes,
        "eval_steps": eval_steps,
        "shift_period": shift_period,
        "post_shift_window": post_shift_window,
        "epochs": epochs,
        "gpu": GPU,
        "max_containers": MAX_CONTAINERS,
        "budget_estimate": estimate,
    }
    print(json.dumps({"kind": "dry-run manifest", "manifest": manifest}, indent=2))
    if not estimate["within_budget"]:
        raise SystemExit(
            "Refusing to dispatch: conservative timeout-based Modal cost "
            f"${estimate['conservative_cost_usd']:.2f} exceeds budget ${budget_usd:.2f}."
        )
    if dry_run_budget:
        return

    rows = list(run_cell.map(cells))
    payload = {
        "kind": "virtual governor stress-signal L4 suite",
        "manifest": manifest,
        "rows": rows,
    }
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    out_path.write_text(payload_text)
    print(f"Wrote {len(rows)} rows to {out_path}")

    import base64

    artifacts = artifact_cell.remote(payload_text)
    for artifact in artifacts:
        path = Path(artifact["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(artifact["data_b64"]))
        print(f"Wrote {path}")
