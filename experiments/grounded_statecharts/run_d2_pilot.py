"""Run the held-out grounded-harness D2 pilot matrix.

Default adapter is fixture for clean-clone mechanics. Credentialed live runs
require GROUNDED_HARNESS_LIVE=1 and write under artifacts/ unless --publish-dir
points at a temporary directory. Never overwrite committed results/ from live.

Example (fixture dry path):

    python3 -m experiments.grounded_statecharts.run_d2_pilot --adapter fixture

Example (live, artifacts only):

    GROUNDED_HARNESS_LIVE=1 \
    GROUNDED_HARNESS_PROVIDER=openai \
    GROUNDED_HARNESS_MODEL=gpt-4.1-mini \
    doppler run --config dev -- \
      python3 -m experiments.grounded_statecharts.run_d2_pilot --adapter live
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from experiments.grounded_statecharts.adapters import build_executor
from experiments.grounded_statecharts.budgets import DEFAULT_PILOT_BUDGET
from experiments.grounded_statecharts.d2_tasks import load_d2_held_out_tasks
from experiments.grounded_statecharts.evaluation import (
    CORE_CONDITIONS,
    LiveEpisode,
    bootstrap_paired_effect,
    harness_digest_for,
    public_rows,
    run_episode,
)
from experiments.grounded_statecharts.runtime import canonical_json, digest

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LIVE_OUTPUT = (
    REPO_ROOT / "artifacts" / "grounded_statecharts" / "d2_pilot"
)
DEFAULT_FIXTURE_OUTPUT = (
    Path(__file__).resolve().parent / "results" / "d2_pilot_fixture"
)
REPEATS = 3


def generate_results(
    *,
    adapter_id: str,
    output_dir: Path,
    repeats: int = REPEATS,
) -> dict[str, object]:
    if adapter_id == "live":
        if os.environ.get("GROUNDED_HARNESS_LIVE", "").strip() != "1":
            raise RuntimeError("live D2 pilot requires GROUNDED_HARNESS_LIVE=1")
        if "results" in output_dir.parts and "artifacts" not in output_dir.parts:
            raise RuntimeError("refusing to write live D2 rows under results/")
    executor = build_executor(adapter_id)
    results = []
    failures: list[dict[str, object]] = []
    tasks = load_d2_held_out_tasks()
    for task in tasks:
        for condition in CORE_CONDITIONS:
            for repeat_index in range(repeats):
                episode = LiveEpisode(
                    episode_id=f"d2:{task.task_id}:{condition}:r{repeat_index}",
                    run_id=f"d2-pilot-{adapter_id}",
                    task=task,
                    condition=condition,
                    repeat_index=repeat_index,
                    model_id=executor.model_id,
                    provider_id=executor.provider_id,
                    adapter_id=adapter_id,
                    harness_digest=harness_digest_for(condition),
                    budget=DEFAULT_PILOT_BUDGET,
                    seed=int(
                        digest(f"{task.task_id}:{condition}:{repeat_index}")[:8],
                        16,
                    ),
                )
                try:
                    results.append(
                        run_episode(episode, executor=executor, planned_calls=1)
                    )
                except Exception as exc:  # noqa: BLE001
                    failures.append(
                        {
                            "episode_id": episode.episode_id,
                            "error_type": type(exc).__name__,
                            "error": str(exc)[:500],
                        }
                    )

    publishable = [result for result in results if result.integrity.publishable]
    rows = public_rows(publishable) if publishable else []
    artifact_rows = [row for row in rows if row["family"] == "artifact_completion"]
    constraint_rows = [
        row for row in rows if row["family"] == "recursive_constrained_tool_use"
    ]
    bootstrap = {}
    if len({row["task_id"] for row in artifact_rows}) >= 2:
        bootstrap["false_completion_g3_minus_g0"] = bootstrap_paired_effect(
            artifact_rows,
            treatment="statechart_g3",
            control="statechart_g0",
            metric="false_completion",
            bootstrap_samples=500,
            seed=20260720,
        ).to_dict()
    if len({row["task_id"] for row in constraint_rows}) >= 2:
        bootstrap["joint_success_external_minus_envelope"] = bootstrap_paired_effect(
            constraint_rows,
            treatment="envelope_external_guards",
            control="envelope_only",
            metric="joint_success",
            bootstrap_samples=500,
            seed=20260720,
        ).to_dict()

    summary = {
        "adapter_id": adapter_id,
        "provider_id": executor.provider_id,
        "model_id": executor.model_id,
        "task_count": len(tasks),
        "episode_count": len(results),
        "publishable_rows": len(rows),
        "repeats": repeats,
        "conditions": list(CORE_CONDITIONS),
        "bootstrap": bootstrap,
        "provider_failures": failures,
        "gates": {
            "held_out_only": all(task.held_out for task in tasks),
            "all_publishable": bool(results) and len(rows) == len(results),
            "budget_ok": all(r.budget_receipt.ok for r in results) if results else False,
            "provider_failures": len(failures),
        },
        "allowed_claim": (
            "Fixture D2 matrix validates held-out task wiring and paired "
            "bootstrap plumbing only."
            if adapter_id == "fixture"
            else (
                "Live D2 pilot rows are exploratory internal evidence pending "
                "integrity review; smoke outcomes remain excluded."
            )
        ),
        "non_claims": [
            "Not a confirmatory D3 study.",
            "Not a commercial usefulness claim.",
            "Credentialed smoke rows are not mixed into this held-out set.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    (output_dir / "rows.jsonl").write_text(
        "\n".join(canonical_json(row) for row in rows) + ("\n" if rows else "")
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", choices=("fixture", "live"), default="fixture")
    parser.add_argument("--repeats", type=int, default=REPEATS)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    output = args.output_dir or (
        DEFAULT_LIVE_OUTPUT if args.adapter == "live" else DEFAULT_FIXTURE_OUTPUT
    )
    summary = generate_results(
        adapter_id=args.adapter,
        output_dir=output,
        repeats=args.repeats,
    )
    print(
        json.dumps(
            {
                "output_dir": str(output),
                "adapter_id": summary["adapter_id"],
                "episode_count": summary["episode_count"],
                "publishable_rows": summary["publishable_rows"],
                "provider_failures": summary["gates"]["provider_failures"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
