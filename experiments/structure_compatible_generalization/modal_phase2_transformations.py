#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal L4 runner for inferred transformations and intervention sweeps.

Run:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/structure_compatible_generalization/modal_phase2_transformations.py \\
        --shards 6 --n-configs 180 --epochs 450 --budget-usd 50 \\
        --out artifacts/structure_compatible_generalization/phase2_transformations.json
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

GPU = "L4"
TIMEOUT_SECONDS = 3600
MAX_CONTAINERS = 24
GPU_RATE_PER_SECOND = 0.000222


def _image() -> Any:
    image = modal.Image.debian_slim(python_version="3.12").apt_install("git").pip_install(
        "torch>=2.5,<2.8",
        "numpy>=1.26,<2.2",
        "scipy>=1.11,<2.0",
        "matplotlib>=3.8,<4.0",
        "reportlab>=4.0,<5.0",
        "pytest>=8,<10",
        "ruff>=0.8,<1.0",
        "uv>=0.7,<1.0",
    )
    return image.add_local_dir(".", remote_path="/root/project")


IMAGE = _image()
app = modal.App(name="research-derived-structure-compatible-phase2")


def _split_count(total: int, shards: int, shard: int) -> int:
    base = total // shards
    extra = total % shards
    return base + int(shard < extra)


def _parse_regularization_values(raw: str) -> tuple[float, ...]:
    values = tuple(float(part.strip()) for part in raw.split(",") if part.strip())
    if not values:
        raise ValueError("at least one regularization value is required")
    return values


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
    from experiments.structure_compatible_generalization.modular_domain import (
        run_intervention_sweep,
    )
    from experiments.structure_compatible_generalization.core import summarize_rows

    rows = run_intervention_sweep(
        n_configs=int(arg["n_configs"]),
        epochs=int(arg["epochs"]),
        base_seed=int(arg["base_seed"]),
        device="cuda",
        regularization_values=tuple(float(v) for v in arg["regularization_values"]),
        include_exact=bool(arg.get("include_exact", False)),
    )
    return {
        "cell": {
            "shard_id": int(arg["shard_id"]),
            "n_configs": int(arg["n_configs"]),
            "regularization_values": list(arg["regularization_values"]),
            "include_exact": bool(arg.get("include_exact", False)),
            "gpu": GPU,
        },
        "summary": summarize_rows(rows),
        "rows": [row.to_record() for row in rows],
    }


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
            "tests/test_structure_compatible_generalization.py",
        ],
        [
            sys.executable,
            "-m",
            "compileall",
            "scripts",
            "experiments",
            "tests",
        ],
        [sys.executable, "scripts/publication_guard.py"],
        ["ruff", "check", "."],
        [
            "uvx",
            "--with",
            "torch",
            "--with",
            "pytest",
            "--with",
            "numpy",
            "--with",
            "scikit-learn",
            "--with",
            "matplotlib",
            "--with",
            "reportlab",
            "ty",
            "check",
            "scripts",
            "experiments",
            "tests",
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
        results.append(
            {
                "cmd": cmd,
                "returncode": proc.returncode,
                "output_tail": proc.stdout[-4000:],
            }
        )
        if proc.returncode != 0:
            return {"ok": False, "results": results}
    return {"ok": True, "results": results}


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=1800,
    cpu=4,
    memory=8192,
    single_use_containers=True,
)
def artifact_cell(payload_text: str) -> list[dict[str, str]]:
    import base64
    import sys

    sys.path.insert(0, "/root/project")
    sys.path.insert(0, "/root/project/scripts")

    payload = json.loads(payload_text)
    out_root = Path("/tmp/phase2_artifacts")
    report_out = (
        out_root
        / "experiments/structure_compatible_generalization/results/"
        "phase2_transformations_2026_07_06.md"
    )
    paper_dir = out_root / "papers/structure_compatible_generalization"
    payload_path = out_root / "phase2_transformations.json"
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    payload_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    from experiments.structure_compatible_generalization.core import rows_from_records
    from experiments.structure_compatible_generalization.summarize_phase2 import (
        _summary,
        phase2_summary,
        write_figures,
        write_paper_markdown,
        write_report,
    )
    from scripts.build_structure_compatible_phase2_pdf import build

    rows = rows_from_records(payload["rows"])
    summary = _summary(payload)
    phase2 = phase2_summary(payload)
    payload["summary"] = summary
    payload["phase2_summary"] = phase2
    figure_paths = write_figures(rows, phase2, paper_dir / "figures")
    write_report(payload, phase2, report_out)
    write_paper_markdown(payload, phase2, paper_dir, figure_paths)
    build(
        payload_path,
        paper_dir / "inferred_transformations_intervention.pdf",
        paper_dir / "figures",
    )

    rel_paths = [
        "experiments/structure_compatible_generalization/results/"
        "phase2_transformations_2026_07_06.md",
        "papers/structure_compatible_generalization/"
        "inferred_transformations_intervention.md",
        "papers/structure_compatible_generalization/"
        "inferred_transformations_intervention.pdf",
        "papers/structure_compatible_generalization/figures/"
        "fig3_discovered_vs_oracle.png",
        "papers/structure_compatible_generalization/figures/"
        "fig4_regularization_intervention.png",
    ]
    artifacts = []
    for rel_path in rel_paths:
        raw = (out_root / rel_path).read_bytes()
        artifacts.append(
            {
                "path": rel_path,
                "data_b64": base64.b64encode(raw).decode("ascii"),
            }
        )
    return artifacts


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


def _make_cells(
    *,
    shards: int,
    n_configs: int,
    epochs: int,
    regularization_values: tuple[float, ...],
    base_seed: int,
) -> list[dict[str, Any]]:
    cells = []
    for shard in range(shards):
        count = _split_count(n_configs, shards, shard)
        if count <= 0:
            continue
        cells.append(
            {
                "shard_id": shard,
                "n_configs": count,
                "epochs": epochs,
                "regularization_values": regularization_values,
                "base_seed": base_seed + shard * 100_003,
                "include_exact": shard == 0,
            }
        )
    return cells


@app.local_entrypoint()
def main(
    shards: int = 6,
    n_configs: int = 180,
    epochs: int = 450,
    regularization_values: str = "0,0.05,0.2",
    base_seed: int = 20260706,
    budget_usd: float = 50.0,
    out: str = "artifacts/structure_compatible_generalization/phase2_transformations.json",
    artifacts_only: bool = False,
    artifact_input: str = "artifacts/structure_compatible_generalization/phase2_transformations.json",
    dry_run_budget: bool = False,
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

    reg_values = _parse_regularization_values(regularization_values)
    cells = _make_cells(
        shards=shards,
        n_configs=n_configs,
        epochs=epochs,
        regularization_values=reg_values,
        base_seed=base_seed,
    )
    estimate = _estimate_cost(len(cells), budget_usd)
    manifest = {
        "suite": "phase2 inferred transformations and intervention",
        "shards": shards,
        "n_configs": n_configs,
        "epochs": epochs,
        "regularization_values": list(reg_values),
        "base_seed": base_seed,
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

    cell_payloads = list(run_cell.map(cells))
    rows: list[dict[str, Any]] = []
    for payload in cell_payloads:
        rows.extend(payload["rows"])

    import sys

    sys.path.insert(0, ".")
    from experiments.structure_compatible_generalization.core import (
        rows_from_records,
        summarize_rows,
    )

    payload = {
        "kind": "structure-compatible phase2 inferred transformations L4 suite",
        "manifest": manifest,
        "cells": [p["cell"] for p in cell_payloads],
        "cell_summaries": [p["summary"] for p in cell_payloads],
        "summary": summarize_rows(rows_from_records(rows)),
        "rows": rows,
    }
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {len(rows)} diagnostic rows to {out_path}")
