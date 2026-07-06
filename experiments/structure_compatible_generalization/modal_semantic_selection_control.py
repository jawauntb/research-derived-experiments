#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal L4 runner for SCG semantic selection-control."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

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
            "matplotlib>=3.8,<4.0",
            "numpy>=1.26,<2.2",
            "pytest>=8,<10",
            "reportlab>=4.0,<5.0",
            "ruff>=0.8,<1.0",
            "sentence-transformers>=3.0,<6",
            "torch>=2.5,<2.8",
            "uv>=0.7,<1.0",
        )
        .add_local_dir(".", remote_path="/root/project")
    )


IMAGE = _image()
app = modal.App(name="research-derived-scg-semantic-selection-control")


def _parse_encoder_keys(raw: str) -> tuple[str, ...]:
    values = tuple(part.strip() for part in raw.split(",") if part.strip())
    if not values:
        raise ValueError("at least one encoder is required")
    return values


def _parse_thresholds(raw: str) -> tuple[float, ...]:
    values = tuple(float(part.strip()) for part in raw.split(",") if part.strip())
    if not values:
        raise ValueError("at least one threshold is required")
    return values


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
def run_encoder_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import sys

    sys.path.insert(0, "/root/project")
    from experiments.structure_compatible_generalization.core import summarize_rows
    from experiments.structure_compatible_generalization.semantic_selection_control import (
        run_encoder_selection_control_sweep,
        selection_records,
        summarize_selection_records,
    )

    rows = run_encoder_selection_control_sweep(
        encoder_keys=(str(arg["encoder_key"]),),
        thresholds=tuple(float(value) for value in arg["thresholds"]),
        n_zoos=int(arg["n_zoos"]),
        configs_per_zoo=int(arg["configs_per_zoo"]),
        base_seed=int(arg["base_seed"]),
    )
    records = selection_records(rows)
    return {
        "cell": {
            "kind": "semantic_selection_control",
            "encoder_key": str(arg["encoder_key"]),
            "n_zoos": int(arg["n_zoos"]),
            "configs_per_zoo": int(arg["configs_per_zoo"]),
            "thresholds": list(arg["thresholds"]),
            "gpu": GPU,
        },
        "summary": summarize_rows(rows),
        "selection_summary": summarize_selection_records(records),
        "selection_records": [record.to_record() for record in records],
        "rows": [row.to_record() for row in rows],
    }


@app.function(image=IMAGE, gpu=GPU, timeout=1800, cpu=4, memory=8192, single_use_containers=True)
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
        [sys.executable, "-m", "pytest", "tests/test_structure_compatible_generalization.py"],
        [
            sys.executable,
            "-m",
            "compileall",
            "experiments/structure_compatible_generalization",
            "scripts/build_structure_compatible_semantic_selection_pdf.py",
            "tests/test_structure_compatible_generalization.py",
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
        results.append({"cmd": cmd, "returncode": proc.returncode, "output_tail": proc.stdout[-4000:]})
        if proc.returncode != 0:
            return {"ok": False, "results": results}
    return {"ok": True, "results": results}


@app.function(image=IMAGE, gpu=GPU, timeout=1200, cpu=4, memory=8192, single_use_containers=True)
def artifact_cell(payload_text: str) -> list[dict[str, str]]:
    import base64
    import sys

    sys.path.insert(0, "/root/project")
    sys.path.insert(0, "/root/project/scripts")

    payload = json.loads(payload_text)
    out_root = Path("/tmp/semantic_selection_artifacts")
    report_out = (
        out_root
        / "experiments/structure_compatible_generalization/results/"
        "semantic_selection_control_2026_07_06.md"
    )
    paper_dir = out_root / "papers/structure_compatible_generalization"
    payload_path = out_root / "semantic_selection_control.json"
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    payload_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    from experiments.structure_compatible_generalization.semantic_selection_control import (
        selection_records_from_dicts,
    )
    from experiments.structure_compatible_generalization.summarize_semantic_selection_control import (
        semantic_selection_summary,
        write_figures,
        write_paper_markdown,
        write_report,
    )
    from scripts.build_structure_compatible_semantic_selection_pdf import build

    records = selection_records_from_dicts(payload["selection_records"])
    summary = semantic_selection_summary(payload)
    payload["semantic_selection_summary"] = summary
    figures = write_figures(records, summary, paper_dir / "figures")
    write_report(payload, summary, report_out)
    write_paper_markdown(payload, summary, paper_dir, figures)
    build(payload_path, paper_dir / "semantic_selection_control.pdf", paper_dir / "figures")

    rel_paths = [
        "experiments/structure_compatible_generalization/results/semantic_selection_control_2026_07_06.md",
        "papers/structure_compatible_generalization/semantic_selection_control.md",
        "papers/structure_compatible_generalization/semantic_selection_control.pdf",
        "papers/structure_compatible_generalization/figures/fig11_semantic_selection_ood.png",
        "papers/structure_compatible_generalization/figures/fig12_semantic_selection_regret.png",
    ]
    artifacts = []
    for rel_path in rel_paths:
        raw = (out_root / rel_path).read_bytes()
        artifacts.append({"path": rel_path, "data_b64": base64.b64encode(raw).decode("ascii")})
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


@app.local_entrypoint()
def main(
    encoder_keys: str = "all_minilm_l6_v2,bge_small_en_v1_5",
    thresholds: str = "0.50,0.56,0.62,0.68,0.74",
    n_zoos: int = 12,
    configs_per_zoo: int = 12,
    base_seed: int = 20260706,
    budget_usd: float = 30.0,
    out: str = "artifacts/structure_compatible_generalization/semantic_selection_control.json",
    artifacts_only: bool = False,
    artifact_input: str = "artifacts/structure_compatible_generalization/semantic_selection_control.json",
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

    encoders = _parse_encoder_keys(encoder_keys)
    parsed_thresholds = _parse_thresholds(thresholds)
    cells = [
        {
            "encoder_key": encoder,
            "thresholds": list(parsed_thresholds),
            "n_zoos": n_zoos,
            "configs_per_zoo": configs_per_zoo,
            "base_seed": base_seed + idx * 1_000_003,
        }
        for idx, encoder in enumerate(encoders)
    ]
    estimate = _estimate_cost(len(cells), budget_usd)
    manifest = {
        "suite": "semantic selection control",
        "encoder_keys": list(encoders),
        "thresholds": list(parsed_thresholds),
        "n_zoos": n_zoos,
        "configs_per_zoo": configs_per_zoo,
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

    payloads = list(run_encoder_cell.map(cells))
    rows: list[dict[str, Any]] = []
    for payload in payloads:
        rows.extend(payload["rows"])

    selection_record_dicts: list[dict[str, Any]] = []
    for payload in payloads:
        selection_record_dicts.extend(payload["selection_records"])
    final_payload = {
        "kind": "structure-compatible semantic selection-control L4 suite",
        "manifest": manifest,
        "cells": [p["cell"] for p in payloads],
        "cell_summaries": [p["summary"] for p in payloads],
        "cell_selection_summaries": [p["selection_summary"] for p in payloads],
        "selection_records": selection_record_dicts,
        "rows": rows,
    }
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(final_payload, indent=2, sort_keys=True) + "\n")
    print(
        f"Wrote {len(rows)} diagnostic rows and {len(selection_record_dicts)} "
        "selection records "
        f"to {out_path}"
    )
