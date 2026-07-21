"""Name-free / harness-enforced sensitivity smoke for the live D2 contract.

Writes only under artifacts/. Requires GROUNDED_HARNESS_LIVE=1 and
GROUNDED_HARNESS_WEAK_PROMPT=1 (name-free prompt is also the live default).
Rejects labeled-prompt diagnostic mode.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path
from statistics import fmean

from experiments.grounded_statecharts.adapters.live import (
    LIVE_LABELED_PROMPT_ENV,
    LIVE_OPT_IN_ENV,
    LIVE_WEAK_PROMPT_ENV,
    LiveExecutor,
)
from experiments.grounded_statecharts.budgets import DEFAULT_PILOT_BUDGET
from experiments.grounded_statecharts.d2_tasks import load_d2_held_out_tasks
from experiments.grounded_statecharts.evaluation import (
    LiveEpisode,
    harness_digest_for,
    run_episode,
)
from experiments.grounded_statecharts.runtime import canonical_json, digest

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "grounded_statecharts" / "weak_prompt_ablation"


def _effect(
    rows: list[dict[str, object]],
    *,
    family: str,
    metric: str,
    treatment: str,
    control: str,
) -> tuple[float | None, int]:
    by_task: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row["family"] != family or row["condition"] not in {treatment, control}:
            continue
        value = row[metric]
        if isinstance(value, bool):
            numeric = float(value)
        elif isinstance(value, int | float):
            numeric = float(value)
        else:
            raise ValueError(f"metric {metric} must be numeric or boolean")
        by_task[str(row["task_id"])][str(row["condition"])].append(numeric)
    effects = []
    for conditions in by_task.values():
        if treatment in conditions and control in conditions:
            effects.append(fmean(conditions[treatment]) - fmean(conditions[control]))
    return (fmean(effects) if effects else None), len(effects)


def generate_results(
    *,
    output_dir: Path,
    tasks_per_family: int = 4,
) -> dict[str, object]:
    if os.environ.get(LIVE_OPT_IN_ENV, "").strip() != "1":
        raise RuntimeError(f"set {LIVE_OPT_IN_ENV}=1")
    if os.environ.get(LIVE_WEAK_PROMPT_ENV, "").strip() != "1":
        raise RuntimeError(f"set {LIVE_WEAK_PROMPT_ENV}=1 for this ablation")
    if os.environ.get(LIVE_LABELED_PROMPT_ENV, "").strip() == "1":
        raise RuntimeError(
            f"unset {LIVE_LABELED_PROMPT_ENV}; this ablation requires name-free prompts"
        )
    if "results" in output_dir.parts:
        raise RuntimeError("refusing to write ablation under results/")

    executor = LiveExecutor.from_env()
    tasks = list(load_d2_held_out_tasks())
    selected = (
        [task for task in tasks if task.family == "artifact_completion"][:tasks_per_family]
        + [
            task
            for task in tasks
            if task.family == "recursive_constrained_tool_use"
        ][:tasks_per_family]
    )
    conditions = {
        "artifact_completion": ("statechart_g0", "statechart_g3"),
        "recursive_constrained_tool_use": (
            "envelope_only",
            "envelope_external_guards",
        ),
    }
    results = []
    failures: list[dict[str, object]] = []
    for task in selected:
        for condition in conditions[task.family]:
            episode = LiveEpisode(
                episode_id=f"weak:{task.task_id}:{condition}:r0",
                run_id="weak-prompt-ablation",
                task=task,
                condition=condition,
                repeat_index=0,
                model_id=executor.model_id,
                provider_id=executor.provider_id,
                adapter_id="live",
                harness_digest=harness_digest_for(condition),
                budget=DEFAULT_PILOT_BUDGET,
                seed=int(digest(f"weak:{task.task_id}:{condition}")[:8], 16),
            )
            try:
                results.append(run_episode(episode, executor=executor))
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    {
                        "episode_id": episode.episode_id,
                        "error_type": type(exc).__name__,
                        "error": str(exc)[:500],
                    }
                )

    rows = [result.public_row for result in results if result.integrity.publishable]
    fc = _effect(
        rows,
        family="artifact_completion",
        metric="false_completion",
        treatment="statechart_g3",
        control="statechart_g0",
    )
    js = _effect(
        rows,
        family="recursive_constrained_tool_use",
        metric="joint_success",
        treatment="envelope_external_guards",
        control="envelope_only",
    )
    summary = {
        "weak_prompt": True,
        "n_rows": len(rows),
        "failures": failures,
        "false_completion_g3_minus_g0": {
            "point_estimate": fc[0],
            "task_count": fc[1],
        },
        "joint_success_external_minus_envelope": {
            "point_estimate": js[0],
            "task_count": js[1],
        },
        "allowed_claim": (
            "Weaker-instruction ablation checks whether D2 directional effects "
            "survive without condition labels in the prompt. Not a D3 result."
        ),
        "escalate_constraint_if": (
            "joint_success point estimate remains >= 0.15 with task_count >= 4"
        ),
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
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--tasks-per-family", type=int, default=4)
    args = parser.parse_args()
    summary = generate_results(
        output_dir=args.output_dir,
        tasks_per_family=args.tasks_per_family,
    )
    failures = summary["failures"]
    failure_count = len(failures) if isinstance(failures, list) else 0
    print(
        json.dumps(
            {
                "n_rows": summary["n_rows"],
                "failures": failure_count,
                "false_completion_g3_minus_g0": summary[
                    "false_completion_g3_minus_g0"
                ],
                "joint_success_external_minus_envelope": summary[
                    "joint_success_external_minus_envelope"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
