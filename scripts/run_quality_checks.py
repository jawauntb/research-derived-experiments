#!/usr/bin/env python3
"""Run the repo's reproducible local quality checks.

The system Python on some macOS installs is 3.9, while this repo uses Python
3.12 features such as ``zip(..., strict=True)``. This wrapper syncs the locked
quality dependency group once, then runs every gate from that environment.
Set ``QUALITY_PYTEST_WORKERS=auto`` (or a positive integer) to enable bounded
pytest-xdist scheduling; local runs remain serial by default.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Mapping


UV_PYTHON = ["uv", "run", "--no-sync", "python"]
UV_TOOL = ["uv", "run", "--no-sync"]
THREAD_LIMIT_VARIABLES = (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)


def run(cmd: list[str], *, env: Mapping[str, str] | None = None) -> None:
    print(f"\n$ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True, env=env)


def available_worker_count() -> int:
    """Return the process's usable CPU count, respecting Linux affinity."""
    if hasattr(os, "sched_getaffinity"):
        return len(os.sched_getaffinity(0))
    return os.cpu_count() or 1


def requested_pytest_workers(environ: Mapping[str, str]) -> int | None:
    """Parse the opt-in worker setting and cap automatic scheduling at four."""
    requested = environ.get("QUALITY_PYTEST_WORKERS")
    if requested is None or not requested.strip():
        return None
    if requested == "auto":
        return min(4, max(1, available_worker_count()))
    workers = int(requested)
    if workers < 1 or workers > 4:
        raise ValueError("QUALITY_PYTEST_WORKERS must be 'auto' or an integer from 1 to 4")
    return workers


def quality_steps(
    environ: Mapping[str, str] | None = None,
) -> list[tuple[list[str], Mapping[str, str] | None]]:
    """Build the ordered, fail-fast root quality execution steps."""
    active_environ = os.environ if environ is None else environ
    pytest_command = UV_PYTHON + ["-m", "pytest", "-q"]
    workers = requested_pytest_workers(active_environ)
    if workers is not None:
        pytest_command += [
            "-n",
            str(workers),
            "--dist",
            "loadscope",
            "--max-worker-restart=0",
        ]
    pytest_command.append("tests")
    pytest_environment = parallel_test_environment(active_environ) if workers else None

    return [
        (
            ["uv", "sync", "--locked", "--only-group", "quality", "--python", "3.12"],
            None,
        ),
        (pytest_command, pytest_environment),
        (UV_PYTHON + ["-m", "compileall", "scripts", "experiments", "tests"], None),
        (UV_PYTHON + ["scripts/publication_guard.py"], None),
        (UV_PYTHON + ["scripts/validate_evidence_registry.py"], None),
        (UV_PYTHON + ["scripts/validate_claim_registry.py"], None),
        (UV_PYTHON + ["scripts/validate_experiment_manifest.py"], None),
        (UV_PYTHON + ["scripts/validate_gate_verdict.py"], None),
        (UV_PYTHON + ["scripts/check_primer_metadata.py"], None),
        (UV_PYTHON + ["scripts/gen_provenance.py", "--check"], None),
        (UV_TOOL + ["ruff", "check", "."], None),
        (UV_TOOL + ["ty", "check", "scripts", "experiments", "tests"], None),
    ]


def parallel_test_environment(environ: Mapping[str, str]) -> dict[str, str]:
    """Prevent native math libraries from oversubscribing xdist workers."""
    child_environ = dict(environ)
    for variable in THREAD_LIMIT_VARIABLES:
        child_environ[variable] = "1"
    return child_environ


def main() -> int:
    for command, env in quality_steps():
        run(command, env=env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
