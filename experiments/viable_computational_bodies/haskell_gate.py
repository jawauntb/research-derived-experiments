#!/usr/bin/env python3
"""Python bridge for the Haskell Arc 2B ontology gate."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable, Iterable


class HaskellGateUnavailable(RuntimeError):
    """Raised when the local Haskell checker cannot be executed."""


class HaskellGateError(RuntimeError):
    """Raised when the Haskell checker runs but returns invalid output."""


@dataclass(frozen=True)
class HaskellVerdict:
    formal_valid: bool
    resource_cost: int
    violations: tuple[str, ...]
    formal_source: str = "haskell"

    @classmethod
    def from_payload(cls, payload: dict[str, object]) -> HaskellVerdict:
        raw_formal_valid = payload.get("formal_valid")
        if not isinstance(raw_formal_valid, bool):
            raise HaskellGateError("verdict formal_valid must be a bool")
        raw_resource_cost = payload.get("resource_cost")
        if not isinstance(raw_resource_cost, int) or isinstance(raw_resource_cost, bool):
            raise HaskellGateError("verdict resource_cost must be an int")
        raw_violations = payload.get("violations", ())
        if not isinstance(raw_violations, list):
            raise HaskellGateError("verdict violations must be a list")
        return cls(
            formal_valid=raw_formal_valid,
            resource_cost=raw_resource_cost,
            violations=tuple(str(item) for item in raw_violations),
        )


Runner = Callable[[tuple[str, ...]], str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ontology_dir() -> Path:
    return _repo_root() / "formal" / "ontology-hs"


def _run_ontology_check(body_names: tuple[str, ...]) -> str:
    ontology_dir = _ontology_dir()
    if not ontology_dir.exists():
        raise HaskellGateUnavailable(f"missing Haskell ontology dir: {ontology_dir}")
    if shutil.which("cabal") is None:
        raise HaskellGateUnavailable("cabal is not available")

    try:
        completed = subprocess.run(
            ["cabal", "run", "ontology-check", "--", *body_names],
            cwd=ontology_dir,
            check=True,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise HaskellGateUnavailable("cabal is not available") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip()
        raise HaskellGateError(f"ontology-check failed: {detail}") from exc
    return completed.stdout


def parse_named_verdicts(output: str) -> dict[str, HaskellVerdict]:
    verdicts: dict[str, HaskellVerdict] = {}
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped or not stripped.startswith("{"):
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise HaskellGateError(f"invalid ontology JSON: {stripped}") from exc
        body_name = payload.get("body")
        if not isinstance(body_name, str):
            raise HaskellGateError("ontology JSON is missing string field 'body'")
        verdicts[body_name] = HaskellVerdict.from_payload(payload)
    if not verdicts:
        raise HaskellGateError("ontology-check emitted no named verdicts")
    return verdicts


def load_body_verdicts(
    body_names: Iterable[str],
    *,
    runner: Runner | None = None,
) -> dict[str, HaskellVerdict]:
    names = tuple(sorted(set(body_names)))
    if not names:
        return {}
    if runner is not None:
        return parse_named_verdicts(runner(names))
    return dict(_cached_body_verdicts(names))


def try_body_verdicts(body_names: Iterable[str]) -> dict[str, HaskellVerdict] | None:
    try:
        return load_body_verdicts(body_names)
    except HaskellGateUnavailable:
        return None


@lru_cache(maxsize=16)
def _cached_body_verdicts(names: tuple[str, ...]) -> tuple[tuple[str, HaskellVerdict], ...]:
    return tuple(
        sorted(
            parse_named_verdicts(_run_ontology_check(names)).items(),
            key=lambda item: item[0],
        )
    )
