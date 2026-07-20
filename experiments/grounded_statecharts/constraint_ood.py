"""Draft OOD probe specifications for Constraint Transport D2."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from experiments.grounded_statecharts.constraint_transport import TransportTask

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "results" / "constraint_ood"


@dataclass(frozen=True)
class ConstraintOODProbe:
    """A planned perturbation of the committed transport task interface."""

    probe_id: str
    perturbation: str
    source_task_families: tuple[str, ...]
    planned_depths: tuple[int, ...]
    execution_status: str
    prediction: str
    kill_criterion: str

    def __post_init__(self) -> None:
        if not all(
            (
                self.probe_id,
                self.perturbation,
                self.source_task_families,
                self.planned_depths,
                self.prediction,
                self.kill_criterion,
            )
        ):
            raise ValueError("OOD probe fields must be non-empty")
        if self.execution_status != "planned":
            raise ValueError("draft OOD probes must remain planned")
        if any(depth < 1 for depth in self.planned_depths):
            raise ValueError("planned delegation depths must be positive")

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_id": self.probe_id,
            "perturbation": self.perturbation,
            "source_task_families": list(self.source_task_families),
            "planned_depths": list(self.planned_depths),
            "execution_status": self.execution_status,
            "prediction": self.prediction,
            "kill_criterion": self.kill_criterion,
        }


def draft_probe_specs(tasks: tuple[TransportTask, ...]) -> tuple[ConstraintOODProbe, ...]:
    """Bind the two draft probes to the committed two-family task bank."""

    families = tuple(task.family for task in tasks)
    return (
        ConstraintOODProbe(
            "held_out_wording",
            "Replace surface wording while preserving the typed constraint fields.",
            families,
            (1, 2, 3, 4),
            "planned",
            "Typed lineage preserves constraints despite held-out instruction wording.",
            "Kill transport interpretation if task scoring or constraint identity changes with wording.",
        ),
        ConstraintOODProbe(
            "deeper_delegation_depth",
            "Extend matched typed/prose delegation beyond the committed depth-1..4 fixture.",
            families,
            (5, 6),
            "planned",
            "Typed lineage remains valid and constraint survival does not degrade solely from depth.",
            "Kill depth-transport interpretation if a typed chain loses lineage or constraints at depth 5 or 6.",
        ),
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def generate_results(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    """Write a preregistered OOD matrix; this scaffold executes no probe."""

    tasks = TransportTask.load_many(PACKAGE_ROOT / "fixtures" / "constraint_transport.json")
    probes = draft_probe_specs(tasks)
    rows = [
        {
            **probe.to_dict(),
            "source_task_count": len(tasks),
            "source_conditions": ["lossy_prompt", "typed_guarded"],
            "observed": False,
        }
        for probe in probes
    ]
    gates = {
        "two_ood_probes_registered": len(probes) == 2,
        "two_source_families_bound": len({task.family for task in tasks}) == 2,
        "held_out_wording_uses_committed_depth_range": probes[0].planned_depths
        == (1, 2, 3, 4),
        "deeper_probe_exceeds_committed_depth_range": min(probes[1].planned_depths) > 4,
        "all_probes_planned_not_observed": all(
            probe.execution_status == "planned" for probe in probes
        ),
        "no_live_calls": True,
    }
    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": "constraint_ood_draft_specs_2026_07_20",
        "tier": "preregistered-stub",
        "committed_fixture_depth_range": [1, 2, 3, 4],
        "probes": rows,
        "gates": gates,
        "allowed_claim": (
            "This artifact freezes two OOD probe contracts against the existing "
            "Constraint Transport task machinery. It reports no OOD execution, "
            "effect, or live-agent result."
        ),
        "next_best_test": (
            "Implement matched held-out wording and depth-5/6 fixture mechanics, "
            "then run all conditions with the registered lineage and scoring checks."
        ),
    }
    if not all(gates.values()):
        raise RuntimeError("constraint OOD draft gates failed")
    _write_json(output_dir / "summary.json", summary)
    _write_jsonl(output_dir / "rows.jsonl", rows)
    return summary
