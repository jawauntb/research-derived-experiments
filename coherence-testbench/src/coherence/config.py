"""Typed config loaders for kill-criterion and phase-0 run configs.

The kill-criterion is pre-registered and read-only after commit — the loader
computes a stable content hash and stamps it into every run manifest so any
post-hoc threshold edit is detectable in the artifact.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class GoThresholds:
    lso_balanced_accuracy_min: float
    bits_per_second_min: float
    generalization_gap_max: float
    seed_min_bacc: float
    n_seeds: int


@dataclass(frozen=True)
class KillThresholds:
    lso_balanced_accuracy_max: float
    bits_per_second_max: float


@dataclass(frozen=True)
class KillCriterion:
    version: str
    committed_at: str
    committed_by: str
    primary_task_name: str
    chance_level: float
    go: GoThresholds
    kill: KillThresholds
    confounds: list[dict[str, Any]]
    required_report_sections: list[str]
    content_hash: str
    source_path: Path

    def verdict(self, lso_bacc: float, bits_per_s: float, gen_gap: float,
                per_seed_baccs: list[float]) -> str:
        """Apply the pre-registered thresholds. Returns GO / KILL / INCONCLUSIVE."""
        seed_floor_ok = (
            len(per_seed_baccs) >= self.go.n_seeds
            and all(b >= self.go.seed_min_bacc for b in per_seed_baccs)
        )
        if (
            lso_bacc >= self.go.lso_balanced_accuracy_min
            and bits_per_s >= self.go.bits_per_second_min
            and gen_gap <= self.go.generalization_gap_max
            and seed_floor_ok
        ):
            return "GO"
        if (
            lso_bacc <= self.kill.lso_balanced_accuracy_max
            and bits_per_s <= self.kill.bits_per_second_max
        ):
            return "KILL"
        return "INCONCLUSIVE"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_kill_criterion(path: str | Path) -> KillCriterion:
    p = Path(path)
    data = yaml.safe_load(p.read_text())
    go = data["thresholds"]["go"]
    kill = data["thresholds"]["kill"]
    return KillCriterion(
        version=data["version"],
        committed_at=str(data["committed_at"]),
        committed_by=data["committed_by"],
        primary_task_name=data["primary_task"]["name"],
        chance_level=float(data["primary_task"]["chance_level"]),
        go=GoThresholds(
            lso_balanced_accuracy_min=float(go["lso_balanced_accuracy_min"]),
            bits_per_second_min=float(go["bits_per_second_min"]),
            generalization_gap_max=float(go["generalization_gap_max"]),
            seed_min_bacc=float(go["stability"]["seed_min_bacc"]),
            n_seeds=int(go["stability"]["n_seeds"]),
        ),
        kill=KillThresholds(
            lso_balanced_accuracy_max=float(kill["lso_balanced_accuracy_max"]),
            bits_per_second_max=float(kill["bits_per_second_max"]),
        ),
        confounds=list(data.get("confounds_to_control", [])),
        required_report_sections=list(data["reporting"]["required_sections"]),
        content_hash=_sha256(p),
        source_path=p.resolve(),
    )


@dataclass(frozen=True)
class Phase0Config:
    kill_criterion_path: Path
    data: dict[str, Any]
    preprocess: dict[str, Any]
    decoders: dict[str, Any]
    evaluate: dict[str, Any]
    output: dict[str, Any]
    raw: dict[str, Any] = field(default_factory=dict)


def load_phase0(path: str | Path) -> Phase0Config:
    p = Path(path)
    data = yaml.safe_load(p.read_text())
    return Phase0Config(
        kill_criterion_path=(p.parent.parent / data["kill_criterion"]).resolve()
        if not Path(data["kill_criterion"]).is_absolute()
        else Path(data["kill_criterion"]),
        data=data["data"],
        preprocess=data["preprocess"],
        decoders=data["decoders"],
        evaluate=data["evaluate"],
        output=data["output"],
        raw=data,
    )
