#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal/local entrypoint for grounded-harness credentialed live smoke.

Prefer the local path with Doppler-injected keys. Remote Modal execution requires
a Modal secret named `grounded-harness-live` containing provider API keys.

    GROUNDED_HARNESS_LIVE=1 \
    GROUNDED_HARNESS_PROVIDER=openai \
    GROUNDED_HARNESS_MODEL=gpt-4.1-mini \
    doppler run --config dev -- \
      python3 -m experiments.grounded_statecharts.run_live_credentialed_smoke

    GROUNDED_HARNESS_LIVE=1 \
    GROUNDED_HARNESS_PROVIDER=openai \
    GROUNDED_HARNESS_MODEL=gpt-4.1-mini \
    doppler run --config dev -- \
      modal run experiments/grounded_statecharts/modal_live_credentialed_smoke.py
"""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

for parent in Path(__file__).resolve().parents:
    if (parent / "experiments").exists():
        sys.path.insert(0, str(parent))
        break

modal = importlib.import_module("modal")

IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("uv>=0.7,<1.0")
    .add_local_dir(".", remote_path="/root/project")
)
app = modal.App(name="research-derived-grounded-harness-live-smoke")


@app.function(
    image=IMAGE,
    timeout=900,
    cpu=2,
    memory=4096,
    secrets=[modal.Secret.from_name("grounded-harness-live")],
)
def run_smoke_remote(
    provider: str,
    model: str,
) -> dict[str, Any]:
    sys.path.insert(0, "/root/project")
    os.environ["GROUNDED_HARNESS_LIVE"] = "1"
    os.environ["GROUNDED_HARNESS_PROVIDER"] = provider
    os.environ["GROUNDED_HARNESS_MODEL"] = model
    from experiments.grounded_statecharts.run_live_credentialed_smoke import (
        DEFAULT_OUTPUT,
        generate_results,
    )

    summary = generate_results(DEFAULT_OUTPUT)
    return {
        "episode_count": summary["episode_count"],
        "publishable_rows": summary["publishable_rows"],
        "provider_id": summary["provider_id"],
        "model_id": summary["model_id"],
        "output_dir": str(DEFAULT_OUTPUT),
    }


@app.local_entrypoint()
def main(*, remote: bool = False) -> None:
    if os.environ.get("GROUNDED_HARNESS_LIVE", "").strip() != "1":
        raise SystemExit("set GROUNDED_HARNESS_LIVE=1 before running")
    provider = os.environ.get("GROUNDED_HARNESS_PROVIDER", "").strip()
    model = os.environ.get("GROUNDED_HARNESS_MODEL", "").strip()
    if not provider or not model:
        raise SystemExit("set GROUNDED_HARNESS_PROVIDER and GROUNDED_HARNESS_MODEL")

    if not remote:
        from experiments.grounded_statecharts.run_live_credentialed_smoke import (
            DEFAULT_OUTPUT,
            generate_results,
        )

        summary = generate_results(DEFAULT_OUTPUT)
        print(json.dumps({
            "mode": "local",
            "episode_count": summary["episode_count"],
            "publishable_rows": summary["publishable_rows"],
            "provider_id": summary["provider_id"],
            "model_id": summary["model_id"],
            "output_dir": str(DEFAULT_OUTPUT),
        }, indent=2, sort_keys=True))
        return

    print(json.dumps({"mode": "remote", **run_smoke_remote.remote(provider, model)}, indent=2, sort_keys=True))
