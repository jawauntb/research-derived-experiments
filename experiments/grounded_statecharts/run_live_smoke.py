"""Regenerate the clean-clone-safe live-evaluation smoke bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.grounded_statecharts.budgets import DEFAULT_PILOT_BUDGET
from experiments.grounded_statecharts.evaluation import (
    bootstrap_paired_effect,
    public_rows,
    run_smoke_matrix,
)
from experiments.grounded_statecharts.runtime import canonical_json

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "results" / "live_evaluation"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(canonical_json(row) for row in rows) + "\n")


def generate_results(output_dir: Path) -> dict[str, object]:
    results = run_smoke_matrix(
        run_id="live-eval-smoke",
        repeats=2,
        budget=DEFAULT_PILOT_BUDGET,
        adapter_id="fixture",
    )
    rows = public_rows(results)
    if any(not result.integrity.publishable for result in results):
        raise RuntimeError("refusing to publish live smoke bundle with failed integrity gates")

    artifact_rows = [row for row in rows if row["family"] == "artifact_completion"]
    constraint_rows = [
        row for row in rows if row["family"] == "recursive_constrained_tool_use"
    ]
    false_completion = bootstrap_paired_effect(
        artifact_rows,
        treatment="statechart_g3",
        control="statechart_g0",
        metric="false_completion",
        bootstrap_samples=500,
        seed=20260720,
    )
    joint_success = bootstrap_paired_effect(
        constraint_rows,
        treatment="envelope_external_guards",
        control="envelope_only",
        metric="joint_success",
        bootstrap_samples=500,
        seed=20260720,
    )
    summary = {
        "adapter_id": "fixture",
        "allowed_claim": (
            "Clean-clone smoke confirms the shared live-evaluation contract: "
            "normalized rows, matched budgets, sanitization, fixture replay "
            "integrity, and task-clustered bootstrap utilities. This is not a "
            "live-agent D2 pilot result."
        ),
        "non_claims": [
            "No live provider was contacted.",
            "Smoke tasks are mechanics checks, not held-out D2 evidence.",
            "No commercial usefulness or confirmatory CT/CHS claim is authorized.",
        ],
        "episode_count": len(rows),
        "publishable_rows": len(rows),
        "gates": {
            "all_publishable": True,
            "adapter_is_fixture": True,
            "budget_ok": all(result.budget_receipt.ok for result in results),
            "sanitized": all(result.sanitization.ok for result in results),
            "replay_ok": all(result.integrity.replay_ok for result in results),
        },
        "bootstrap": {
            "false_completion_g3_minus_g0": false_completion.to_dict(),
            "joint_success_external_minus_envelope": joint_success.to_dict(),
        },
    }
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "rows.jsonl", rows)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = generate_results(args.output_dir)
    print(json.dumps({"output_dir": str(args.output_dir), "episode_count": summary["episode_count"]}))


if __name__ == "__main__":
    main()
