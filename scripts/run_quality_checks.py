#!/usr/bin/env python3
"""Run the repo's reproducible local quality checks.

The system Python on some macOS installs is 3.9, while this repo now uses
Python 3.12 features such as ``zip(..., strict=True)``. This wrapper keeps the
documented checks honest by running tests under an ephemeral uvx Python 3.12
environment with the lightweight scientific dependencies required by tests.
"""

from __future__ import annotations

import subprocess


def run(cmd: list[str]) -> None:
    print(f"\n$ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True)


def main() -> int:
    test_python = [
        "uvx",
        "--python",
        "3.12",
        "--with",
        "torch",
        "--with",
        "numpy",
        "--with",
        "scikit-learn",
        "--with",
        "matplotlib",
        "--with",
        "reportlab",
        "--with",
        "pytest",
        "python",
    ]
    plain_python = ["uvx", "--python", "3.12", "python"]
    ty_check = [
        "uvx",
        "--python",
        "3.12",
        "--with",
        "numpy",
        "--with",
        "torch",
        "--with",
        "scikit-learn",
        "--with",
        "scipy",
        "--with",
        "matplotlib",
        "--with",
        "pytest",
        "ty",
        "check",
        "scripts",
        "experiments",
        "tests",
    ]

    run(test_python + ["-m", "pytest", "-q", "tests"])
    run(plain_python + ["-m", "compileall", "scripts", "experiments", "tests"])
    run(["python3", "scripts/publication_guard.py"])
    run(["python3", "scripts/validate_evidence_registry.py"])
    run(["python3", "scripts/validate_claim_registry.py"])
    run(["python3", "scripts/validate_experiment_manifest.py"])
    run(["python3", "scripts/validate_gate_verdict.py"])
    run(["python3", "scripts/check_primer_metadata.py"])
    run(["python3", "scripts/gen_provenance.py", "--check"])
    run(["uvx", "ruff", "check", "."])
    run(ty_check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
