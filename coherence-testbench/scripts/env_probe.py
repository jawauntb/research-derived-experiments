#!/usr/bin/env python3
"""Report whether coherence-testbench's expected env vars are present.

Never prints secret values. Mirrors ../scripts/env_probe.py from the parent
repo so both bench and parent can be probed the same way.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from typing import Iterable


MODAL_KEYS = (
    "MODAL_TOKEN_ID",
    "MODAL_TOKEN_SECRET",
    "MODAL_WORKSPACE",
    "MODAL_ENVIRONMENT",
    "MODAL_DEFAULT_GPU",
)

SUPABASE_KEYS = (
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
)

OBS_KEYS = (
    "LOGFIRE_TOKEN",
    "POSTHOG_API_KEY",
    "POSTHOG_HOST",
)

BENCH_KEYS = (
    "BBBD_CACHE_DIR",
    "COHERENCE_ARTIFACT_ROOT",
)

INHERITED_MODEL_APIS = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
)


@dataclass(frozen=True)
class EnvStatus:
    name: str
    present: bool
    length: int


def status_for(names: Iterable[str]) -> list[EnvStatus]:
    out: list[EnvStatus] = []
    for name in names:
        value = os.environ.get(name, "")
        out.append(EnvStatus(name=name, present=bool(value), length=len(value)))
    return out


def print_table(title: str, statuses: list[EnvStatus]) -> None:
    print(title)
    print("-" * len(title))
    for item in statuses:
        marker = "yes" if item.present else "no"
        length = item.length if item.present else 0
        print(f"{item.name:32} present={marker:3} length={length}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    groups = {
        "modal": status_for(MODAL_KEYS),
        "supabase": status_for(SUPABASE_KEYS),
        "observability": status_for(OBS_KEYS),
        "bench": status_for(BENCH_KEYS),
        "inherited_model_apis": status_for(INHERITED_MODEL_APIS),
    }

    if args.json:
        print(json.dumps(
            {k: [asdict(i) for i in v] for k, v in groups.items()},
            indent=2,
        ))
        return 0

    print_table("Modal", groups["modal"])
    print_table("Supabase", groups["supabase"])
    print_table("Observability", groups["observability"])
    print_table("Bench-specific", groups["bench"])
    print_table("Inherited model APIs", groups["inherited_model_apis"])

    missing_critical = [
        s.name for s in groups["modal"] + groups["bench"]
        if not s.present and s.name in {"MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET", "BBBD_CACHE_DIR"}
    ]
    if missing_critical:
        print("WARNING: missing critical vars for a full Phase-0 run:",
              ", ".join(missing_critical))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
