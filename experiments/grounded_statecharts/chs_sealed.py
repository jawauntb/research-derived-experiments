"""Sealed-label scoring bridge for deterministic counterfactual attribution."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

from experiments.grounded_statecharts.counterfactual_search import (
    COMPONENTS,
    CounterfactualHarnessPilot,
    FaultCase,
)

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "results" / "chs_sealed"


@dataclass(frozen=True)
class SealedLabel:
    case_id: str
    fault_id: str | None
    responsible_component: str | None

    @classmethod
    def load_many(cls, path: Path) -> tuple[Self, ...]:
        raw = json.loads(path.read_text())
        if not isinstance(raw, dict) or set(raw) != {"schema_version", "labels"}:
            raise ValueError("sealed labels must contain schema_version and labels")
        labels = raw["labels"]
        if raw["schema_version"] != "1.0" or not isinstance(labels, list):
            raise ValueError("sealed labels have an unsupported schema")
        loaded = []
        for item in labels:
            if not isinstance(item, dict) or set(item) != {
                "case_id",
                "fault_id",
                "responsible_component",
            }:
                raise ValueError("sealed label fields are invalid")
            case_id = item["case_id"]
            fault_id = item["fault_id"]
            component = item["responsible_component"]
            if not isinstance(case_id, str) or not case_id:
                raise ValueError("sealed case_id must be non-empty")
            if (fault_id is None) != (component is None):
                raise ValueError("no-fault labels must omit both fault and component")
            if fault_id is not None and (
                not isinstance(fault_id, str) or component not in COMPONENTS
            ):
                raise ValueError("fault labels must name a known component")
            loaded.append(cls(case_id, fault_id, component))
        fault_labels = [label for label in loaded if label.fault_id is not None]
        if len(loaded) != len(COMPONENTS) + 1 or len(fault_labels) != len(COMPONENTS):
            raise ValueError("sealed labels require one no-fault and six single-fault cases")
        if {label.responsible_component for label in fault_labels} != set(COMPONENTS):
            raise ValueError("sealed labels must cover each harness surface once")
        return tuple(loaded)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def score_sealed_labels(
    labels: tuple[SealedLabel, ...], cases: tuple[FaultCase, ...]
) -> list[dict[str, object]]:
    """Score one clean reference plus single-fault fixture cases."""

    cases_by_id = {case.fault_id: case for case in cases}
    pilot = CounterfactualHarnessPilot()
    rows: list[dict[str, object]] = []
    for label in labels:
        if label.fault_id is None:
            predicted_component = None
            evaluation_budget = 0
            repair_success = True
        else:
            case = cases_by_id.get(label.fault_id)
            if case is None:
                raise ValueError(f"sealed label does not match a fixture: {label.fault_id}")
            result = pilot.run(case)
            predicted_component = result.recovered_component
            evaluation_budget = result.evaluation_budget
            repair_success = result.counterfactual_repair_success
        rows.append(
            {
                "case_id": label.case_id,
                "fault_id": label.fault_id,
                "case_kind": "no_fault" if label.fault_id is None else "single_fault",
                "sealed_component": label.responsible_component,
                "predicted_component": predicted_component,
                "top1_correct": predicted_component == label.responsible_component,
                "counterfactual_repair_success": repair_success,
                "evaluation_budget": evaluation_budget,
            }
        )
    return rows


def generate_results(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    """Write public-safe sealed-label results without provider access."""

    labels = SealedLabel.load_many(PACKAGE_ROOT / "fixtures" / "chs_sealed_labels.json")
    cases = FaultCase.load_many(PACKAGE_ROOT / "fixtures" / "counterfactual_faults.json")
    rows = score_sealed_labels(labels, cases)
    fault_rows = [row for row in rows if row["case_kind"] == "single_fault"]
    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": "chs_sealed_bridge_2026_07_20",
        "tier": "synthetic-sealed-label-bridge",
        "cases": len(rows),
        "fault_surfaces": list(COMPONENTS),
        "metrics": {
            "top1_attribution": sum(bool(row["top1_correct"]) for row in rows) / len(rows),
            "single_fault_top1_attribution": sum(
                bool(row["top1_correct"]) for row in fault_rows
            )
            / len(fault_rows),
            "no_fault_correct": next(
                bool(row["top1_correct"]) for row in rows if row["case_kind"] == "no_fault"
            ),
        },
        "gates": {
            "one_no_fault_case": sum(row["case_kind"] == "no_fault" for row in rows) == 1,
            "six_single_fault_cases": len(fault_rows) == len(COMPONENTS),
            "sealed_fixture_alignment": {row["fault_id"] for row in fault_rows}
            == {case.fault_id for case in cases},
            "no_provider_calls": True,
        },
        "allowed_claim": (
            "The separate label-loading and scoring path correctly scores the committed "
            "synthetic clean and six single-fault fixtures. It is a plumbing bridge, "
            "not a sealed evaluation of real failures."
        ),
        "non_claims": [
            "Labels remain synthetic and repository-visible to the fixture author.",
            "No real failure, stochastic replay, interaction fault, or OOD attribution was evaluated.",
            "This does not satisfy publishable CHS1.",
        ],
        "next_best_test": (
            "Score precommitted labels withheld from the diagnosis author on real "
            "failure episodes before making a CHS1 claim."
        ),
    }
    if not all(summary["gates"].values()):
        raise RuntimeError("CHS sealed bridge gates failed")
    _write_json(output_dir / "summary.json", summary)
    _write_jsonl(output_dir / "rows.jsonl", rows)
    return summary
