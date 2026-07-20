"""Harvest provisional CHS component candidates from sanitized live D2 rows.

The mapping is a declared symptom heuristic, not an oracle or a sealed label.
It creates an artifact ledger for later independent adjudication.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from experiments.grounded_statecharts.live_replay import DEFAULT_ROWS, load_rows
from experiments.grounded_statecharts.sanitization import sanitize_public_row

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "grounded_statecharts" / "chs_from_live"

HEURISTIC_VERSION = "live-chs-symptom-map-1"
HEURISTIC_RULES = {
    "artifact false completion under G0/direct self-report": "orchestration",
    "wrong-edge invalid transition": "output",
    "constraint joint failure without external guards": "orchestration",
    "explicit refusal without a budget failure": "generation",
    "budget exhaustion": "tools",
}


def _candidate_surface(row: Mapping[str, Any]) -> tuple[str | None, str | None]:
    """Return a provisional surface and declared rule; abstain when ambiguous."""

    if row.get("budget_exhausted") is True:
        return "tools", "budget exhaustion"
    if row.get("invalid_transition") is True:
        return "output", "wrong-edge invalid transition"
    if (
        row.get("family") == "artifact_completion"
        and row.get("false_completion") is True
        and row.get("condition") in {"direct_self_report", "statechart_g0"}
    ):
        return "orchestration", "artifact false completion under G0/direct self-report"
    if (
        row.get("family") == "recursive_constrained_tool_use"
        and row.get("joint_success") is False
        and row.get("condition")
        in {"direct_self_report", "statechart_g0", "envelope_only"}
    ):
        return "orchestration", "constraint joint failure without external guards"
    if row.get("refusal") is True:
        return "generation", "explicit refusal without a budget failure"
    return None, None


def harvest_candidates(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, object]]:
    """Produce a compact, public-metadata-only candidate ledger."""

    candidates = []
    for row in rows:
        receipt = sanitize_public_row(row)
        if not receipt.ok:
            raise ValueError("live CHS harvest requires sanitized public-schema rows")
        component, rule = _candidate_surface(row)
        if component is None or rule is None:
            continue
        candidates.append(
            {
                "candidate_id": f"candidate:{row['result_digest']}",
                "source_episode_id": row["episode_id"],
                "source_result_digest": row["result_digest"],
                "task_id": row["task_id"],
                "family": row["family"],
                "condition": row["condition"],
                "repeat_index": row["repeat_index"],
                "outcome_pattern": {
                    "false_completion": row["false_completion"],
                    "joint_success": row["joint_success"],
                    "refusal": row["refusal"],
                    "invalid_transition": row["invalid_transition"],
                    "budget_exhausted": row["budget_exhausted"],
                },
                "predicted_component": component,
                "heuristic_rule": rule,
                "label_status": "unsealed_candidate",
            }
        )
    return sorted(candidates, key=lambda row: str(row["candidate_id"]))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def generate_results(
    rows_path: Path = DEFAULT_ROWS, output_dir: Path = DEFAULT_OUTPUT
) -> dict[str, Any]:
    """Write an unsealed artifact candidate ledger without provider calls."""

    candidates = harvest_candidates(load_rows(rows_path))
    component_counts = {
        component: sum(candidate["predicted_component"] == component for candidate in candidates)
        for component in ("context", "tools", "generation", "orchestration", "memory", "output")
    }
    summary = {
        "schema_version": "1.0",
        "tier": "live-row-heuristic-harvest",
        "source_rows": str(rows_path),
        "heuristic_version": HEURISTIC_VERSION,
        "heuristic_rules": HEURISTIC_RULES,
        "candidate_count": len(candidates),
        "candidate_counts_by_component": component_counts,
        "gates": {
            "input_rows_are_sanitized_public_schema": True,
            "all_candidates_are_unsealed": all(
                candidate["label_status"] == "unsealed_candidate"
                for candidate in candidates
            ),
            "no_provider_calls": True,
        },
        "allowed_claim": (
            "Declared outcome-pattern heuristics harvested provisional component "
            "candidates from sanitized live rows."
        ),
        "non_claims": [
            "The heuristic is not a causal diagnosis or a sealed label.",
            "No candidate is scored as correct before independent adjudication.",
            "This does not satisfy CHS1.",
        ],
        "next_best_test": (
            "Have an independent scorer seal component labels before comparing "
            "them with this candidate ledger."
        ),
    }
    _write_json(output_dir / "summary.json", summary)
    _write_jsonl(output_dir / "rows.jsonl", candidates)
    return summary
