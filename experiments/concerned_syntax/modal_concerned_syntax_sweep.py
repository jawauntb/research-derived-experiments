#!/usr/bin/env python3
"""Modal sweep for Arc 2A concerned syntax.

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \
      uvx --python 3.12 --from modal modal run \
      experiments/concerned_syntax/modal_concerned_syntax_sweep.py
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12")
app = modal.App(name="research-derived-concerned-syntax")


@app.function(image=IMAGE, timeout=1800, cpu=1, memory=1024)
def run_seed(seed: int, trials: int) -> dict[str, Any]:
    from experiments.concerned_syntax.benchmark import run_trials, summarize

    rows = run_trials(trials=trials, seed=seed)
    return {
        "seed": seed,
        "trials": trials,
        "summary": summarize(rows),
    }


@app.local_entrypoint()
def main(trials: int = 1000) -> None:
    seeds = [20260616, 1729, 4242, 8675309, 314159]
    results = list(run_seed.map(seeds, kwargs={"trials": trials}))
    payload = {
        "manifest": {
            "arc": "2A",
            "name": "concerned_syntax_modal_sweep",
            "seeds": seeds,
            "trials_per_seed": trials,
        },
        "results": results,
    }
    out = Path("artifacts/concerned_syntax/modal_sweep.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out}")

