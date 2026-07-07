#!/usr/bin/env python3
"""Fire-and-forget Phase-0 run on Modal — returns immediately with a call_id.

Use when you don't want the CLI to stay attached (e.g. going offline). The
sweep runs to completion on Modal regardless of what your laptop does; the
report is persisted to the ``phase0-results`` Volume at ``/<run_id>/report.md``
and can be fetched with::

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal volume get phase0-results \\
            /<run_id>/report.md /tmp/report.md

Usage::

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --with pyyaml --from modal python \\
        coherence-testbench/scripts/spawn_phase0.py \\
        --config coherence-testbench/config/phase0.yaml \\
        --run-id 2026-07-06-attempt1

The call_id + Volume location are printed to stdout so you can recover them
after reconnect.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True,
                        help="Path to phase0.yaml")
    parser.add_argument("--run-id", required=True,
                        help="Directory name under phase0-results/ for this run")
    parser.add_argument("--app", default="coherence-testbench-phase0",
                        help="Modal app name")
    parser.add_argument("--function", default="phase0_end_to_end",
                        help="Modal function name on that app")
    args = parser.parse_args()

    # Load config as a string so it can be embedded in the Function call.
    config_text = Path(args.config).read_text()

    modal = importlib.import_module("modal")
    fn = modal.Function.from_name(args.app, args.function)
    call = fn.spawn(config_yaml=config_text, run_id=args.run_id)
    print(f"call_id={call.object_id}")
    print(f"run_id={args.run_id}")
    print(f"results at: phase0-results:/{args.run_id}/report.md")
    print()
    print("To fetch results later:")
    print(f"  modal volume get phase0-results /{args.run_id} /tmp/{args.run_id}")
    print("To poll for completion (blocks; safe to ctrl-C):")
    print(f"  python -c \"import modal; print(modal.FunctionCall.from_id('{call.object_id}').get())\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
