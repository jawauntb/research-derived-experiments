"""Draft multi-shift extension of the deterministic Harness Unlearning fixture."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from experiments.grounded_statecharts.harness_unlearning import (
    MemoryCommitHarness,
    MemoryLedger,
    MemoryStatus,
    Regime,
    evaluate_causal_use,
)

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "results" / "unlearning_multishift"
TARGET_MEMORY_ID = "mem-tool-v2"
PLACEBO_MEMORY_ID = "mem-color-placebo"


@dataclass(frozen=True)
class ShiftCase:
    """A named semantic-shift family, deliberately not a live-model condition."""

    case_id: str
    shift_family: str
    prior_regime: Regime
    shifted_regime: Regime
    semantics_changed: bool
    mechanism: str

    def __post_init__(self) -> None:
        if not self.case_id or not self.shift_family or not self.mechanism:
            raise ValueError("shift case labels must be non-empty")
        observed_change = (
            self.prior_regime.required_action != self.shifted_regime.required_action
        )
        if observed_change != self.semantics_changed:
            raise ValueError("semantics_changed must match the required-action shift")

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "shift_family": self.shift_family,
            "prior_regime": self.prior_regime.regime_id,
            "shifted_regime": self.shifted_regime.regime_id,
            "semantics_changed": self.semantics_changed,
            "mechanism": self.mechanism,
        }


def draft_shift_cases() -> tuple[ShiftCase, ...]:
    """Return the three pre-registered fixture-only shift families."""

    prior = Regime("v2", "legacy_name", "legacy_name")
    changed = Regime("v3", "current_name", "current_name")
    identical = Regime("model-v2-same-semantics", "legacy_name", "legacy_name")
    return (
        ShiftCase(
            "tool_schema_v2_to_v3",
            "tool-schema",
            prior,
            changed,
            True,
            "The accepted tool field changes from legacy_name to current_name.",
        ),
        ShiftCase(
            "environment_policy_v2_to_v3",
            "environment-policy",
            prior,
            changed,
            True,
            "A policy-enforced environment now rejects the legacy field.",
        ),
        ShiftCase(
            "model_version_identical_semantics",
            "model/version-identical-semantics",
            prior,
            identical,
            False,
            "The model identifier changes while the required commitment remains identical.",
        ),
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def _row(
    case: ShiftCase,
    phase: str,
    ledger: MemoryLedger,
    *,
    task_success: bool,
    retrieved_memory_ids: tuple[str, ...],
) -> dict[str, object]:
    return {
        **case.to_dict(),
        "phase": phase,
        "target_status": ledger.item(TARGET_MEMORY_ID).status.value,
        "task_success": task_success,
        "joint_success": task_success,
        "retrieved_memory_ids": list(retrieved_memory_ids),
    }


def _run_case(case: ShiftCase) -> tuple[list[dict[str, object]], dict[str, object]]:
    ledger, _ = MemoryLedger.load(PACKAGE_ROOT / "fixtures" / "harness_unlearning.json")
    harness = MemoryCommitHarness()
    rows: list[dict[str, object]] = []

    prior = harness.commit(ledger, case.prior_regime)
    shifted = harness.commit(ledger, case.shifted_regime)
    rows.extend(
        (
            _row(
                case,
                "prior_regime",
                ledger,
                task_success=prior.joint_success,
                retrieved_memory_ids=prior.retrieved_memory_ids,
            ),
            _row(
                case,
                "append_only_shift",
                ledger,
                task_success=shifted.joint_success,
                retrieved_memory_ids=shifted.retrieved_memory_ids,
            ),
        )
    )

    causal_use_passed = False
    lifecycle_applied = False
    if case.semantics_changed:
        causal_use = evaluate_causal_use(
            ledger,
            case.shifted_regime,
            target_memory_id=TARGET_MEMORY_ID,
            placebo_memory_id=PLACEBO_MEMORY_ID,
        )
        causal_use_passed = causal_use.passed
        if not causal_use_passed:
            raise RuntimeError(f"causal-use prerequisite failed for {case.case_id}")
        ledger = ledger.transition_family(
            TARGET_MEMORY_ID,
            MemoryStatus.QUARANTINED,
            reason=f"{case.shift_family} target-family suppression repaired commitment",
            evidence_ref=f"causal-use://{case.case_id}",
        )
        repaired = harness.commit(ledger, case.shifted_regime)
        lifecycle_applied = True
        rows.append(
            _row(
                case,
                "quarantined_shift_recovery",
                ledger,
                task_success=repaired.joint_success,
                retrieved_memory_ids=repaired.retrieved_memory_ids,
            )
        )
        recovered = repaired.joint_success
    else:
        recovered = shifted.joint_success

    return rows, {
        **case.to_dict(),
        "prior_success": prior.joint_success,
        "append_only_shift_success": shifted.joint_success,
        "causal_use_prerequisite": causal_use_passed,
        "lifecycle_applied": lifecycle_applied,
        "post_lifecycle_success": recovered,
        "false_forgetting": case.semantics_changed is False and lifecycle_applied,
    }


def generate_results(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    """Generate public-safe draft rows without providers, credentials, or network."""

    case_rows: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    for case in draft_shift_cases():
        rows, result = _run_case(case)
        case_rows.extend(rows)
        summaries.append(result)
    changed = [result for result in summaries if bool(result["semantics_changed"])]
    unchanged = [result for result in summaries if not bool(result["semantics_changed"])]
    gates = {
        "three_shift_families_registered": len(summaries) == 3,
        "changed_semantics_fail_append_only": all(
            not bool(result["append_only_shift_success"]) for result in changed
        ),
        "changed_semantics_pass_causal_use": all(
            bool(result["causal_use_prerequisite"]) for result in changed
        ),
        "changed_semantics_recover_after_quarantine": all(
            bool(result["post_lifecycle_success"]) for result in changed
        ),
        "identical_semantics_preserves_use": all(
            bool(result["append_only_shift_success"])
            and not bool(result["lifecycle_applied"])
            for result in unchanged
        ),
        "no_live_calls": True,
    }
    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": "unlearning_multishift_draft_fixture_2026_07_20",
        "tier": "deterministic-draft-scaffold",
        "cases": summaries,
        "gates": gates,
        "allowed_claim": (
            "These three deterministic draft cases exercise the existing memory "
            "ledger's causal-use and quarantine mechanics under two semantic shifts "
            "and one identical-semantics negative control. They are not live, OOD, "
            "stochastic, or neural-unlearning evidence."
        ),
        "next_best_test": (
            "Freeze independently generated shift instances and evaluate matched "
            "live agents only after pre-registering false-forgetting and recovery gates."
        ),
    }
    if not all(gates.values()):
        raise RuntimeError("multi-shift draft gates failed")
    _write_json(output_dir / "summary.json", summary)
    _write_jsonl(output_dir / "rows.jsonl", case_rows)
    return summary
