from __future__ import annotations

import pytest

from scripts import run_quality_checks


def test_quality_commands_sync_once_and_reuse_locked_environment() -> None:
    steps = run_quality_checks.quality_steps({})
    commands = [command for command, _environment in steps]

    assert commands[0] == [
        "uv",
        "sync",
        "--locked",
        "--only-group",
        "quality",
        "--python",
        "3.12",
    ]
    assert commands[1] == [
        "uv",
        "run",
        "--no-sync",
        "python",
        "-m",
        "pytest",
        "-q",
        "tests",
    ]
    assert all(command[:3] == ["uv", "run", "--no-sync"] for command in commands[1:])
    assert not any("uvx" in command for command in commands)


def test_quality_commands_use_bounded_scope_distribution_when_requested() -> None:
    steps = run_quality_checks.quality_steps({"QUALITY_PYTEST_WORKERS": "4"})
    commands = [command for command, _environment in steps]

    assert commands[1][-6:] == [
        "-n",
        "4",
        "--dist",
        "loadscope",
        "--max-worker-restart=0",
        "tests",
    ]


def test_automatic_workers_are_capped_at_four(monkeypatch) -> None:
    monkeypatch.setattr(run_quality_checks, "available_worker_count", lambda: 64)

    assert run_quality_checks.requested_pytest_workers(
        {"QUALITY_PYTEST_WORKERS": "auto"}
    ) == 4


def test_parallel_environment_caps_native_math_threads() -> None:
    environment = run_quality_checks.parallel_test_environment(
        {"PATH": "/bin", "OMP_NUM_THREADS": "8"}
    )

    assert environment["PATH"] == "/bin"
    assert all(environment[name] == "1" for name in run_quality_checks.THREAD_LIMIT_VARIABLES)


def test_main_stops_after_the_first_failed_gate(monkeypatch) -> None:
    attempted: list[list[str]] = []

    def fail_first(command: list[str], **_kwargs) -> None:
        attempted.append(command)
        raise RuntimeError("gate failed")

    monkeypatch.setattr(run_quality_checks, "run", fail_first)

    with pytest.raises(RuntimeError) as exc_info:
        run_quality_checks.main()

    assert str(exc_info.value) == "gate failed"
    assert attempted == [run_quality_checks.quality_steps()[0][0]]
