#!/usr/bin/env python3
"""Executable bridge for the pinned Relative Identifiability Lean gate."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEAN_PACKAGE = ROOT / "formal" / "relative-identifiability"
TOOLCHAIN_PATH = LEAN_PACKAGE / "lean-toolchain"


class LeanGateUnavailable(RuntimeError):
    """Raised when the pinned Lean package cannot be executed locally."""


class LeanGateError(RuntimeError):
    """Raised when the Lean package fails to build."""


@dataclass(frozen=True)
class LeanGateReceipt:
    built: bool
    package: str
    toolchain: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_lean_gate(lake_path: str | None = None) -> LeanGateReceipt:
    """Build the pinned package and return a compact machine-readable receipt."""

    if not LEAN_PACKAGE.is_dir() or not TOOLCHAIN_PATH.is_file():
        raise LeanGateUnavailable(f"missing Lean package: {LEAN_PACKAGE}")
    executable = lake_path or shutil.which("lake")
    if executable is None:
        raise LeanGateUnavailable("lake is not available")

    try:
        completed = subprocess.run(
            [executable, "build"],
            cwd=LEAN_PACKAGE,
            check=False,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as error:
        raise LeanGateUnavailable("lake is not available") from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise LeanGateError(f"lake build failed: {detail}")

    return LeanGateReceipt(
        built=True,
        package=str(LEAN_PACKAGE.relative_to(ROOT)),
        toolchain=TOOLCHAIN_PATH.read_text(encoding="utf-8").strip(),
    )


def main() -> int:
    try:
        receipt = run_lean_gate()
    except (LeanGateUnavailable, LeanGateError) as error:
        print(json.dumps({"built": False, "error": str(error)}, sort_keys=True))
        return 2
    print(json.dumps(receipt.to_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
