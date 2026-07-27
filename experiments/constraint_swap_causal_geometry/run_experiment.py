#!/usr/bin/env python3
"""Run the registered Constraint-Swap experiment and publish compact results."""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import torch

from .analysis import analyze_seed, summarize_registered_rows
from .core import ExperimentConfig, GridTopology
from .model import train_model
from .summarize import write_summary


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW = ROOT / "artifacts" / "constraint_swap_causal_geometry" / "registered_run.json"
DEFAULT_ROWS = (
    ROOT
    / "experiments"
    / "constraint_swap_causal_geometry"
    / "results"
    / "registered_seed_rows.jsonl"
)
DEFAULT_SUMMARY_JSON = (
    ROOT
    / "experiments"
    / "constraint_swap_causal_geometry"
    / "results"
    / "summary.json"
)
DEFAULT_SUMMARY_MD = (
    ROOT
    / "experiments"
    / "constraint_swap_causal_geometry"
    / "results"
    / "summary.md"
)


def _run_one(
    seed: int,
    config: ExperimentConfig,
    checkpoint_dir: str,
) -> dict[str, Any]:
    topology = GridTopology("torus", 6, 6)
    model, training = train_model(seed=seed, config=config, topology=topology)
    row = analyze_seed(model, seed=seed, config=config)
    checkpoint_path = Path(checkpoint_dir) / f"seed_{seed:02d}.pt"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "seed": seed,
            "training": training,
            "model_state_dict": model.state_dict(),
        },
        checkpoint_path,
    )
    row["training"] = training
    row["checkpoint"] = str(checkpoint_path.relative_to(ROOT))
    return row


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run(
    *,
    seeds: list[int],
    workers: int,
    raw_path: Path,
    rows_path: Path,
    summary_json: Path,
    summary_md: Path,
) -> dict[str, Any]:
    config = ExperimentConfig.registered()
    if sorted(seeds) != list(config.confirmatory_seeds):
        raise ValueError("registered adjudication requires exactly unique seeds 0 through 31")
    for path in (raw_path, rows_path, summary_json, summary_md):
        try:
            path.resolve().relative_to(ROOT)
        except ValueError as exc:
            raise ValueError(f"output path must remain inside repository: {path}") from exc
    checkpoint_dir = raw_path.parent / "checkpoints"
    rows: list[dict[str, Any]] = []
    if workers == 1:
        for seed in seeds:
            print(f"[constraint-swap] seed {seed} starting", flush=True)
            rows.append(_run_one(seed, config, str(checkpoint_dir)))
            print(f"[constraint-swap] seed {seed} complete", flush=True)
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_run_one, seed, config, str(checkpoint_dir)): seed
                for seed in seeds
            }
            for future in as_completed(futures):
                seed = futures[future]
                rows.append(future.result())
                print(f"[constraint-swap] seed {seed} complete", flush=True)
    rows.sort(key=lambda row: int(row["seed"]))
    summary = summarize_registered_rows(
        rows,
        bootstrap_samples=config.bootstrap_resamples,
        seed=20260727,
    )
    raw_payload = {
        "artifact_contract": "constraint-swap-causal-geometry-run/v1",
        "seeds": seeds,
        "rows": rows,
        "summary": summary,
    }
    _write_json(raw_path, raw_payload)
    rows_path.parent.mkdir(parents=True, exist_ok=True)
    rows_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    public_payload = {
        "artifact_contract": "constraint-swap-causal-geometry-summary/v1",
        "raw_run_path": str(raw_path.relative_to(ROOT)),
        "rows_path": str(rows_path.relative_to(ROOT)),
        "summary": summary,
    }
    _write_json(summary_json, public_payload)
    write_summary(public_payload, summary_md)
    return public_payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--rows", type=Path, default=DEFAULT_ROWS)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--summary-md", type=Path, default=DEFAULT_SUMMARY_MD)
    args = parser.parse_args()
    config = ExperimentConfig.registered()
    if args.seeds != len(config.confirmatory_seeds):
        raise SystemExit("--seeds must be 32 for registered adjudication")
    if not 1 <= args.workers <= 8:
        raise SystemExit("--workers must lie between 1 and 8")
    selected = list(config.confirmatory_seeds[: args.seeds])
    payload = run(
        seeds=selected,
        workers=args.workers,
        raw_path=args.raw,
        rows_path=args.rows,
        summary_json=args.summary_json,
        summary_md=args.summary_md,
    )
    print(
        f"[constraint-swap] decision={payload['summary']['verdict']['decision']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
