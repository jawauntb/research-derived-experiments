#!/usr/bin/env python3
"""Validate the checked-in Suite C neural-transfer release summary."""

from __future__ import annotations

from experiments.world_responds.summarize_suite_c_neural_transfer import (
    validate_tracked_release_summary,
)


def main() -> int:
    validate_tracked_release_summary()
    print("Suite C neural-transfer release summary is current and schema-valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
