#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal L4 runner for structure-compatible generalization.

Run:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/structure_compatible_generalization/modal_l4_suite.py \\
        --shards-per-domain 4 --symbolic-models 128 --vision-models 96 \\
        --modular-models 128 --budget-usd 50 \\
        --out artifacts/structure_compatible_generalization/l4_suite.json

Quality-only:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/structure_compatible_generalization/modal_l4_suite.py \\
        --quality-only
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
    # Mount the checkout so quality gates can inspect tracked files with git.
    image = image.add_local_dir(".", remote_path="/root/project")
    return image


IMAGE = _image()
app = modal.App(name="research-derived-structure-compatible-generalization")


def _split_count(total: int, shards: int, shard: int) -> int:
    base = total // shards
    extra = total % shards
    return base + int(shard < extra)


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
    from experiments.structure_compatible_generalization.run_suite import run_suite

    domain = str(arg["domain"])
    n_models = int(arg["n_models"])
    shard_id = int(arg["shard_id"])
    include_exact = bool(arg.get("include_exact", False))
    payload = run_suite(
        domains=[domain],
        symbolic_models=n_models if domain == "symbolic" else 0,
        vision_models=n_models if domain == "vision" else 0,
        modular_models=n_models if domain == "modular" else 0,
        symbolic_epochs=int(arg["symbolic_epochs"]),
        vision_epochs=int(arg["vision_epochs"]),
        modular_epochs=int(arg["modular_epochs"]),
        base_seed=int(arg["base_seed"]) + shard_id * 100_003,
        device="cuda",
        include_exact=include_exact,
    )
    payload["cell"] = {
        "domain": domain,
        "shard_id": shard_id,
        "n_models": n_models,
        "include_exact": include_exact,
        "gpu": GPU,
    }
    return payload


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
    domains: list[str],
    shards_per_domain: int,
    symbolic_models: int,
    vision_models: int,
    modular_models: int,
    symbolic_epochs: int,
    vision_epochs: int,
    modular_epochs: int,
    base_seed: int,
) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for domain, total in [
        ("symbolic", symbolic_models),
        ("vision", vision_models),
        ("modular", modular_models),
    ]:
        if domain not in domains or total <= 0:
            continue
        for shard in range(shards_per_domain):
            n_models = _split_count(total, shards_per_domain, shard)
            if n_models <= 0:
                continue
            cells.append(
                {
                    "domain": domain,
                    "shard_id": len(cells),
                    "domain_shard": shard,
                    "n_models": n_models,
                    "include_exact": domain == "modular" and shard == 0,
                    "symbolic_epochs": symbolic_epochs,
                    "vision_epochs": vision_epochs,
                    "modular_epochs": modular_epochs,
                    "base_seed": base_seed,
                }
            )
    return cells


@app.local_entrypoint()
def main(
    domains: str = "symbolic,vision,modular",
    shards_per_domain: int = 4,
    symbolic_models: int = 128,
    vision_models: int = 96,
    modular_models: int = 128,
    symbolic_epochs: int = 1200,
    vision_epochs: int = 160,
    modular_epochs: int = 500,
    base_seed: int = 20260706,
    budget_usd: float = 50.0,
    out: str = "artifacts/structure_compatible_generalization/l4_suite.json",
    dry_run_budget: bool = False,
    quality_only: bool = False,
) -> None:
    if quality_only:
        result = quality_cell.remote()
        print(json.dumps(result, indent=2, sort_keys=True))
        if not result["ok"]:
            raise SystemExit("Modal quality checks failed")
        return

    domain_list = [d.strip() for d in domains.split(",") if d.strip()]
    cells = _make_cells(
        domains=domain_list,
        shards_per_domain=shards_per_domain,
        symbolic_models=symbolic_models,
        vision_models=vision_models,
        modular_models=modular_models,
        symbolic_epochs=symbolic_epochs,
        vision_epochs=vision_epochs,
        modular_epochs=modular_epochs,
        base_seed=base_seed,
    )
    estimate = _estimate_cost(len(cells), budget_usd)
    manifest = {
        "domains": domain_list,
        "shards_per_domain": shards_per_domain,
        "symbolic_models": symbolic_models,
        "vision_models": vision_models,
        "modular_models": modular_models,
        "symbolic_epochs": symbolic_epochs,
        "vision_epochs": vision_epochs,
        "modular_epochs": modular_epochs,
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

    summary = summarize_rows(rows_from_records(rows))
    payload = {
        "kind": "structure-compatible generalization L4 suite",
        "manifest": manifest,
        "cells": [p["cell"] for p in cell_payloads],
        "cell_summaries": [p["summary"] for p in cell_payloads],
        "summary": summary,
        "rows": rows,
    }
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {len(rows)} diagnostic rows to {out_path}")
