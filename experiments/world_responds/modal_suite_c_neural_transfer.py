#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal L4 runner for Suite C neural probe transfer.

Dry-run budget:

    doppler --scope /Users/jawaun/superoptimizers run -- \
        uvx --python 3.12 --from modal modal run \
        experiments/world_responds/modal_suite_c_neural_transfer.py \
        --dry-run-budget

Full dispatch:

    doppler --scope /Users/jawaun/superoptimizers run -- \
        uvx --python 3.12 --from modal modal run \
        experiments/world_responds/modal_suite_c_neural_transfer.py \
        --out artifacts/world_responds/suite_c_neural_transfer_payload.json
"""

from __future__ import annotations

import base64
import importlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, "/root/project")

modal = importlib.import_module("modal")

GPU = "L4"
BENCHMARK_TIMEOUT_SECONDS = 1800
ARTIFACT_TIMEOUT_SECONDS = 1200
QUALITY_TIMEOUT_SECONDS = 1800
MAX_CONTAINERS = 8
GPU_RATE_PER_SECOND = 0.000222


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
            "ty",
            "uv>=0.7,<1.0",
        )
        .add_local_dir(".", remote_path="/root/project")
    )


IMAGE = _image()
app = modal.App(name="research-derived-suite-c-neural-transfer")


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=BENCHMARK_TIMEOUT_SECONDS,
    cpu=2,
    memory=4096,
    max_containers=MAX_CONTAINERS,
    single_use_containers=True,
    retries=1,
)
def benchmark_cell(args: dict[str, Any]) -> dict[str, Any]:
    import sys

    sys.path.insert(0, "/root/project")
    from experiments.world_responds.suite_c_neural_transfer import run_neural_transfer_suite

    base_seed = int(args.get("base_seed", 20260706))
    train_count = int(args.get("train_seeds", 16))
    calibration_count = int(args.get("calibration_seeds", 6))
    eval_count = int(args.get("eval_seeds", 8))
    train_seeds = [base_seed + 11_000 + i * 997 for i in range(train_count)]
    calibration_seeds = [base_seed + 31_000 + i * 1_003 for i in range(calibration_count)]
    eval_seeds = [base_seed + 51_000 + i * 1_003 for i in range(eval_count)]
    return run_neural_transfer_suite(
        train_seeds=train_seeds,
        calibration_seeds=calibration_seeds,
        eval_seeds=eval_seeds,
        base_seed=base_seed,
    )


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=ARTIFACT_TIMEOUT_SECONDS,
    cpu=2,
    memory=4096,
    single_use_containers=True,
)
def artifact_cell(payload_text: str) -> list[dict[str, str]]:
    import subprocess
    import sys
    import tempfile

    sys.path.insert(0, "/root/project")
    from experiments.world_responds.summarize_suite_c_neural_transfer import build_artifacts

    payload = json.loads(payload_text)
    with tempfile.TemporaryDirectory() as tmp:
        out_root = Path(tmp)
        paths = build_artifacts(payload, out_root)
        paper_dir = out_root / "papers/habituated_reengagement"
        pdf_path = paper_dir / "suite_c_neural_probe_transfer.pdf"
        subprocess.run(
            [
                "python",
                "/root/project/scripts/render_paper_pdf.py",
                "--in",
                str(paper_dir / "suite_c_neural_probe_transfer.md"),
                "--out",
                str(pdf_path),
                "--title",
                "Suite C Neural Probe Transfer",
                "--author",
                "Jawaun Brown",
            ],
            check=True,
            cwd="/root/project",
        )
        fitz = importlib.import_module("fitz")
        with fitz.open(pdf_path) as doc:
            if doc.page_count <= 0 or pdf_path.stat().st_size < 10_000:
                raise RuntimeError("Rendered Suite C neural-transfer PDF failed validation")
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
    timeout=QUALITY_TIMEOUT_SECONDS,
    cpu=2,
    memory=4096,
    single_use_containers=True,
)
def quality_cell() -> dict[str, Any]:
    import subprocess
    import sys
    from pathlib import Path

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

    commands = quality_commands(sys.executable)
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
        results.append({"cmd": cmd, "returncode": proc.returncode, "output_tail": proc.stdout[-6000:]})
        if proc.returncode != 0:
            return {"ok": False, "results": results}
    return {"ok": True, "results": results}


def quality_commands(python_executable: str = "python") -> list[list[str]]:
    return [
        [python_executable, "-m", "pytest", "tests/test_world_responds_suite_c_neural_transfer.py"],
        [
            python_executable,
            "-m",
            "compileall",
            "experiments/world_responds",
            "tests/test_world_responds_suite_c_neural_transfer.py",
        ],
        [
            python_executable,
            "-m",
            "json.tool",
            "experiments/world_responds/results/suite_c_neural_transfer_2026_07_06.json",
        ],
        [
            python_executable,
            "-m",
            "experiments.world_responds.validate_suite_c_neural_transfer_release",
        ],
        [
            python_executable,
            "-c",
            "from pathlib import Path; import fitz; p=Path('papers/habituated_reengagement/suite_c_neural_probe_transfer.pdf'); doc=fitz.open(p); assert doc.page_count > 0 and p.stat().st_size > 10000; doc.close()",
        ],
        [python_executable, "scripts/publication_guard.py"],
        [
            "ruff",
            "check",
            "experiments/world_responds/suite_c_neural_transfer.py",
            "experiments/world_responds/summarize_suite_c_neural_transfer.py",
            "experiments/world_responds/validate_suite_c_neural_transfer_release.py",
            "experiments/world_responds/modal_suite_c_neural_transfer.py",
            "tests/test_world_responds_suite_c_neural_transfer.py",
        ],
        [
            "ty",
            "check",
            "experiments/world_responds/suite_c_neural_transfer.py",
            "experiments/world_responds/summarize_suite_c_neural_transfer.py",
            "experiments/world_responds/validate_suite_c_neural_transfer_release.py",
            "tests/test_world_responds_suite_c_neural_transfer.py",
        ],
    ]


def _estimate_cost(cells: int, timeout_seconds: int, budget_usd: float) -> dict[str, Any]:
    conservative = cells * timeout_seconds * GPU_RATE_PER_SECOND
    return {
        "gpu": GPU,
        "cells": cells,
        "timeout_seconds": timeout_seconds,
        "max_containers": MAX_CONTAINERS,
        "gpu_rate_per_second": GPU_RATE_PER_SECOND,
        "conservative_cost_usd": conservative,
        "budget_usd": budget_usd,
        "within_budget": conservative <= budget_usd,
    }


@app.local_entrypoint()
def main(
    base_seed: int = 20260706,
    train_seeds: int = 16,
    calibration_seeds: int = 6,
    eval_seeds: int = 8,
    budget_usd: float = 75.0,
    out: str = "artifacts/world_responds/suite_c_neural_transfer_payload.json",
    dry_run_budget: bool = False,
    artifacts_only: bool = False,
    artifact_input: str = "artifacts/world_responds/suite_c_neural_transfer_payload.json",
    quality_only: bool = False,
) -> None:
    if quality_only:
        result = quality_cell.remote()
        print(json.dumps(result, indent=2, sort_keys=True))
        if not result["ok"]:
            raise SystemExit("Modal Suite C neural-transfer quality checks failed")
        return

    if artifacts_only:
        payload_text = Path(artifact_input).read_text()
        artifacts = artifact_cell.remote(payload_text)
        for artifact in artifacts:
            path = Path(artifact["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(base64.b64decode(artifact["data_b64"]))
            print(f"Wrote {path}")
        return

    estimate = _estimate_cost(2, BENCHMARK_TIMEOUT_SECONDS, budget_usd)
    manifest = {
        "suite": "Suite C neural probe transfer",
        "claim_level": "learned-policy diagnostic",
        "base_seed": base_seed,
        "train_seeds": train_seeds,
        "calibration_seeds": calibration_seeds,
        "eval_seeds": eval_seeds,
        "gpu": GPU,
        "budget_estimate": estimate,
        "command": (
            "doppler --scope /Users/jawaun/superoptimizers run -- "
            "uvx --python 3.12 --from modal modal run "
            "experiments/world_responds/modal_suite_c_neural_transfer.py "
            f"--base-seed {base_seed} --train-seeds {train_seeds} "
            f"--calibration-seeds {calibration_seeds} --eval-seeds {eval_seeds} "
            f"--budget-usd {budget_usd:g} --out {out}"
        ),
    }
    print(json.dumps({"kind": "dry-run manifest", "manifest": manifest}, indent=2, sort_keys=True))
    if not estimate["within_budget"]:
        raise SystemExit(
            "Refusing to dispatch: conservative timeout-based Modal cost "
            f"${estimate['conservative_cost_usd']:.2f} exceeds budget ${budget_usd:.2f}."
        )
    if dry_run_budget:
        return

    payload = benchmark_cell.remote(
        {
            "base_seed": base_seed,
            "train_seeds": train_seeds,
            "calibration_seeds": calibration_seeds,
            "eval_seeds": eval_seeds,
        }
    )
    payload["manifest"]["command"] = manifest["command"]
    payload["manifest"]["gpu"] = GPU
    payload["manifest"]["budget_estimate"] = estimate
    payload_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    artifacts = artifact_cell.remote(payload_text)

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(payload_text)
    rows_jsonl = Path("artifacts/world_responds/suite_c_neural_transfer_rows.jsonl")
    rows_jsonl.parent.mkdir(parents=True, exist_ok=True)
    rows_jsonl.write_text("\n".join(json.dumps(row, sort_keys=True) for row in payload["rows"]) + "\n")
    summary_json = Path("artifacts/world_responds/suite_c_neural_transfer_summary.json")
    summary_json.write_text(json.dumps(payload["summary"], indent=2, sort_keys=True) + "\n")
    print(f"Wrote {len(payload['rows'])} rows to {out_path}")
    print("Wrote artifacts/world_responds/suite_c_neural_transfer_rows.jsonl")
    print("Wrote artifacts/world_responds/suite_c_neural_transfer_summary.json")

    for artifact in artifacts:
        path = Path(artifact["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(artifact["data_b64"]))
        print(f"Wrote {path}")
