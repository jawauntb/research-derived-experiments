#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal L4 runner for SCG language/template substitution.

Run:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/structure_compatible_generalization/modal_language_template_substitution.py \\
        --shards 4 --n-configs 96 --epochs 260 --budget-usd 40 \\
        --out artifacts/structure_compatible_generalization/language_template_substitution.json
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

GPU = "L4"
TIMEOUT_SECONDS = 3600
MAX_CONTAINERS = 16
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
app = modal.App(name="research-derived-structure-compatible-language-template")


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
def run_language_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import sys

    sys.path.insert(0, "/root/project")
    from experiments.structure_compatible_generalization.core import summarize_rows
    from experiments.structure_compatible_generalization.template_language_domain import (
        run_language_template_sweep,
    )

    rows = run_language_template_sweep(
        n_configs=int(arg["n_configs"]),
        epochs=int(arg["epochs"]),
        base_seed=int(arg["base_seed"]),
        device="cuda",
        regularization_values=tuple(float(v) for v in arg["regularization_values"]),
        include_exact=bool(arg.get("include_exact", False)),
        max_transforms=int(arg["max_transforms"]),
    )
    return {
        "cell": {
            "kind": "language_template",
            "shard_id": int(arg["shard_id"]),
            "n_configs": int(arg["n_configs"]),
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
            "scipy",
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
    out_root = Path("/tmp/language_template_artifacts")
    report_out = (
        out_root
        / "experiments/structure_compatible_generalization/results/"
        "language_template_substitution_2026_07_06.md"
    )
    paper_dir = out_root / "papers/structure_compatible_generalization"
    payload_path = out_root / "language_template_substitution.json"
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    payload_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    from experiments.structure_compatible_generalization.core import rows_from_records
    from experiments.structure_compatible_generalization.summarize_language_templates import (
        language_template_summary,
        write_figures,
        write_paper_markdown,
        write_report,
    )
    from scripts.build_structure_compatible_language_pdf import build

    rows = rows_from_records(payload["rows"])
    language_summary = language_template_summary(payload)
    payload["language_template_summary"] = language_summary
    figure_paths = write_figures(rows, language_summary, paper_dir / "figures")
    write_report(payload, language_summary, report_out)
    write_paper_markdown(payload, language_summary, paper_dir, figure_paths)
    build(
        payload_path,
        paper_dir / "language_template_substitution.pdf",
        paper_dir / "figures",
    )

    rel_paths = [
        "experiments/structure_compatible_generalization/results/"
        "language_template_substitution_2026_07_06.md",
        "papers/structure_compatible_generalization/"
        "language_template_substitution.md",
        "papers/structure_compatible_generalization/"
        "language_template_substitution.pdf",
        "papers/structure_compatible_generalization/figures/"
        "fig7_language_template_predictors.png",
        "papers/structure_compatible_generalization/figures/"
        "fig8_language_template_intervention.png",
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
    max_transforms: int,
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
                "max_transforms": max_transforms,
            }
        )
    return cells


@app.local_entrypoint()
def main(
    shards: int = 4,
    n_configs: int = 96,
    epochs: int = 260,
    regularization_values: str = "0,0.05,0.2,0.5",
    max_transforms: int = 24,
    base_seed: int = 20260706,
    budget_usd: float = 40.0,
    out: str = "artifacts/structure_compatible_generalization/language_template_substitution.json",
    artifacts_only: bool = False,
    artifact_input: str = "artifacts/structure_compatible_generalization/language_template_substitution.json",
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
        max_transforms=max_transforms,
    )
    estimate = _estimate_cost(len(cells), budget_usd)
    manifest = {
        "suite": "language template substitution generator",
        "shards": shards,
        "n_configs": n_configs,
        "epochs": epochs,
        "regularization_values": list(reg_values),
        "max_transforms": max_transforms,
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

    cell_payloads = list(run_language_cell.map(cells))
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
        "kind": "structure-compatible language-template L4 suite",
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
