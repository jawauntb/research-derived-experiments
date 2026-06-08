#!/usr/bin/env python3
"""Report whether useful experiment environment variables are present.

This script never prints secret values.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from typing import Iterable


REQUIRED_FOR_MODEL_APIS = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
)

OPTIONAL_MODEL_APIS = (
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
    "HUGGINGFACE_TOKEN",
    "HF_TOKEN",
)

MODAL_KEYS = (
    "MODAL_TOKEN_ID",
    "MODAL_TOKEN_SECRET",
    "MODAL_WORKSPACE",
    "MODAL_ENVIRONMENT",
    "MODAL_DEFAULT_GPU",
)


@dataclass(frozen=True)
class EnvStatus:
    name: str
    present: bool
    length: int


def status_for(names: Iterable[str]) -> list[EnvStatus]:
    statuses: list[EnvStatus] = []
    for name in names:
        value = os.environ.get(name, "")
        statuses.append(EnvStatus(name=name, present=bool(value), length=len(value)))
    return statuses


def print_table(title: str, statuses: list[EnvStatus]) -> None:
    print(title)
    print("-" * len(title))
    for item in statuses:
        marker = "yes" if item.present else "no"
        length = item.length if item.present else 0
        print(f"{item.name:24} present={marker:3} length={length}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Emit machine-readable status JSON.")
    args = parser.parse_args()

    groups = {
        "required_model_apis": status_for(REQUIRED_FOR_MODEL_APIS),
        "optional_model_apis": status_for(OPTIONAL_MODEL_APIS),
        "modal": status_for(MODAL_KEYS),
    }

    if args.json:
        print(json.dumps({key: [asdict(item) for item in value] for key, value in groups.items()}, indent=2))
        return 0

    print_table("Required model APIs", groups["required_model_apis"])
    print_table("Optional model APIs", groups["optional_model_apis"])
    print_table("Modal", groups["modal"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

