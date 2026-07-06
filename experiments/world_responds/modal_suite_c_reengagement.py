#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal L4 runner for Suite C re-engagement under world change.

Dry-run budget:

    doppler --scope /Users/jawaun/superoptimizers run -- \
        uvx --python 3.12 --from modal modal run \
        experiments/world_responds/modal_suite_c_reengagement.py \
        --seeds 8 --budget-usd 75 --dry-run-budget

Full dispatch:

    doppler --scope /Users/jawaun/superoptimizers run -- \
        uvx --python 3.12 --from modal modal run \
        experiments/world_responds/modal_suite_c_reengagement.py \
        --seeds 8 --budget-usd 75 \
        --out artifacts/world_responds/suite_c_reengagement_payload.json
"""

from __future__ import annotations

import base64
import importlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, "/root/project")
from experiments.world_responds.suite_c_contract import (
    AFFECTED_BUCKETS,
    CANDIDATE_CONDITIONS,
    CONDITIONS,
    DEFAULT_CONFIG,
    UNAFFECTED_BUCKETS,
)

modal = importlib.import_module("modal")

GPU = "L4"
TIMEOUT_SECONDS = 900
MAX_CONTAINERS = 32
GPU_RATE_PER_SECOND = 0.000222
STEPS = DEFAULT_CONFIG.steps
FIRST_SHIFT = DEFAULT_CONFIG.first_shift
SECOND_SHIFT = DEFAULT_CONFIG.second_shift


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
app = modal.App(name="research-derived-suite-c-reengagement")


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
    from experiments.world_responds.suite_c_reengagement import run_trial

    return run_trial(
        str(arg["condition"]),
        int(arg["seed"]),
        target_probe_count=arg.get("target_probe_count"),
    )


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=1200,
    cpu=2,
    memory=4096,
    single_use_containers=True,
)
def artifact_cell(payload_text: str) -> list[dict[str, str]]:
    import subprocess
    import sys
    import tempfile

    sys.path.insert(0, "/root/project")
    sys.path.insert(0, "/root/project/scripts")
    from experiments.world_responds.summarize_suite_c import build_artifacts

    payload = json.loads(payload_text)
    with tempfile.TemporaryDirectory() as tmp:
        out_root = Path(tmp)
        paths = build_artifacts(payload, out_root)
        paper_dir = out_root / "papers/habituated_reengagement"
        pdf_path = paper_dir / "suite_c_reengagement_under_world_change.pdf"
        subprocess.run(
            [
                "python",
                "/root/project/scripts/render_paper_pdf.py",
                "--in",
                str(paper_dir / "suite_c_reengagement_under_world_change.md"),
                "--out",
                str(pdf_path),
                "--title",
                "Suite C Re-Engagement Under World Change",
                "--author",
                "Jawaun Brown",
            ],
            check=True,
            cwd="/root/project",
        )
        fitz = importlib.import_module("fitz")
        with fitz.open(pdf_path) as doc:
            if doc.page_count <= 0 or pdf_path.stat().st_size < 10_000:
                raise RuntimeError("Rendered Suite C PDF failed validation")
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
    timeout=600,
    cpu=2,
    memory=4096,
    single_use_containers=True,
)
def summarize_cell(rows: list[dict[str, Any]]) -> dict[str, Any]:
    import sys

    sys.path.insert(0, "/root/project")
    from experiments.world_responds.suite_c_reengagement import summarize_records

    return summarize_records(rows)


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=600,
    cpu=2,
    memory=4096,
    single_use_containers=True,
)
def headline_cell(rows: list[dict[str, Any]]) -> str:
    import sys

    sys.path.insert(0, "/root/project")
    from experiments.world_responds.suite_c_reengagement import select_headline_condition

    return select_headline_condition(rows)


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=1800,
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

    commands = [
        [sys.executable, "-m", "pytest", "tests/test_world_responds_suite_c.py"],
        [
            sys.executable,
            "-m",
            "compileall",
            "experiments/world_responds",
            "tests/test_world_responds_suite_c.py",
        ],
        [
            sys.executable,
            "-m",
            "json.tool",
            "experiments/world_responds/results/suite_c_reengagement_2026_07_06.json",
        ],
        [
            sys.executable,
            "-c",
            "from pathlib import Path; import fitz; p=Path('papers/habituated_reengagement/suite_c_reengagement_under_world_change.pdf'); doc=fitz.open(p); assert doc.page_count > 0 and p.stat().st_size > 10000; doc.close()",
        ],
        [sys.executable, "scripts/publication_guard.py"],
        [
            "ruff",
            "check",
            "experiments/world_responds/suite_c_contract.py",
            "experiments/world_responds/suite_c_reengagement.py",
            "experiments/world_responds/summarize_suite_c.py",
            "experiments/world_responds/modal_suite_c_reengagement.py",
            "tests/test_world_responds_suite_c.py",
        ],
        ["ty", "check", "experiments/world_responds", "tests/test_world_responds_suite_c.py"],
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
        results.append({"cmd": cmd, "returncode": proc.returncode, "output_tail": proc.stdout[-6000:]})
        if proc.returncode != 0:
            return {"ok": False, "results": results}
    return {"ok": True, "results": results}


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
    seeds: int = 8,
    base_seed: int = 20260706,
    budget_usd: float = 75.0,
    out: str = "artifacts/world_responds/suite_c_reengagement_payload.json",
    dry_run_budget: bool = False,
    artifacts_only: bool = False,
    artifact_input: str = "artifacts/world_responds/suite_c_reengagement_payload.json",
    quality_only: bool = False,
) -> None:
    if quality_only:
        result = quality_cell.remote()
        print(json.dumps(result, indent=2, sort_keys=True))
        if not result["ok"]:
            raise SystemExit("Modal quality checks failed")
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

    seed_list = [base_seed + i * 1_003 for i in range(seeds)]
    pass1_conditions = [c for c in CONDITIONS if c != "matched_random_time_budget"]
    pass1_cells = [
        {"condition": condition, "seed": seed}
        for seed in seed_list
        for condition in pass1_conditions
    ]
    pass2_cells = len(seed_list)
    estimate = _estimate_cost(len(pass1_cells) + pass2_cells, budget_usd)
    manifest = {
        "suite": "Suite C re-engagement under world change",
        "claim_level": "diagnostic",
        "conditions": list(CONDITIONS),
        "candidate_conditions": list(CANDIDATE_CONDITIONS),
        "seeds": seed_list,
        "steps": STEPS,
        "first_shift": FIRST_SHIFT,
        "second_shift": SECOND_SHIFT,
        "affected_buckets": list(AFFECTED_BUCKETS),
        "unaffected_buckets": list(UNAFFECTED_BUCKETS),
        "command": (
            "doppler --scope /Users/jawaun/superoptimizers run -- "
            "uvx --python 3.12 --from modal modal run "
            "experiments/world_responds/modal_suite_c_reengagement.py "
            f"--seeds {seeds} --base-seed {base_seed} --budget-usd {budget_usd:g} --out {out}"
        ),
        "matched_budget_source": "selected headline total probes per seed",
        "gpu": GPU,
        "max_containers": MAX_CONTAINERS,
        "budget_estimate": estimate,
    }
    print(json.dumps({"kind": "dry-run manifest", "manifest": manifest}, indent=2, sort_keys=True))
    if not estimate["within_budget"]:
        raise SystemExit(
            "Refusing to dispatch: conservative timeout-based Modal cost "
            f"${estimate['conservative_cost_usd']:.2f} exceeds budget ${budget_usd:.2f}."
        )
    if dry_run_budget:
        return

    pass1_rows = list(run_cell.map(pass1_cells))
    headline_condition = headline_cell.remote(pass1_rows)
    headline_budgets = {
        int(row["seed"]): int(row["total_probes"])
        for row in pass1_rows
        if row["condition"] == headline_condition
    }
    manifest["matched_budget_source"] = f"{headline_condition} total probes per seed"
    manifest["matched_budget_condition"] = headline_condition
    pass2_args = [
        {
            "condition": "matched_random_time_budget",
            "seed": seed,
            "target_probe_count": headline_budgets[seed],
        }
        for seed in seed_list
    ]
    pass2_rows = list(run_cell.map(pass2_args))
    rows = pass1_rows + pass2_rows
    payload = {
        "kind": "world_responds_suite_c_reengagement",
        "manifest": manifest,
        "rows": rows,
        "summary": summarize_cell.remote(rows),
    }
    payload_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    artifacts = artifact_cell.remote(payload_text)

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(payload_text)
    rows_jsonl = Path("artifacts/world_responds/suite_c_reengagement_rows.jsonl")
    rows_jsonl.parent.mkdir(parents=True, exist_ok=True)
    rows_jsonl.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n")
    summary_json = Path("artifacts/world_responds/suite_c_reengagement_summary.json")
    summary_json.write_text(json.dumps(payload["summary"], indent=2, sort_keys=True) + "\n")
    print(f"Wrote {len(rows)} rows to {out_path}")
    print("Wrote artifacts/world_responds/suite_c_reengagement_rows.jsonl")
    print("Wrote artifacts/world_responds/suite_c_reengagement_summary.json")

    for artifact in artifacts:
        path = Path(artifact["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(artifact["data_b64"]))
        print(f"Wrote {path}")
