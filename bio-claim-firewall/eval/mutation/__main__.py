"""Enables `python -m eval.mutation` (as opposed to `python -m eval.mutation.cli`)."""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
