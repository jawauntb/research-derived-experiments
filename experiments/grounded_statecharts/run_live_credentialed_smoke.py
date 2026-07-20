"""Opt-in credentialed live smoke outside the tracked fixture path.

Writes only under gitignored artifacts/. Never publishes scientific claims.
Smoke outcomes must be discarded from later held-out D2 pilots.

Example:

    GROUNDED_HARNESS_LIVE=1 \
    GROUNDED_HARNESS_PROVIDER=openai \
    GROUNDED_HARNESS_MODEL=gpt-4.1-mini \
    doppler run --config dev -- \
      python3 -m experiments.grounded_statecharts.run_live_credentialed_smoke
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from experiments.grounded_statecharts.adapters.live import (
    LIVE_MODEL_ENV,
    LIVE_OPT_IN_ENV,
    LIVE_PROVIDER_ENV,
    LiveExecutor,
)
from experiments.grounded_statecharts.budgets import DEFAULT_PILOT_BUDGET
from experiments.grounded_statecharts.evaluation import (
    LiveEpisode,
    harness_digest_for,
    run_episode,
    smoke_tasks,
)
from experiments.grounded_statecharts.runtime import canonical_json, digest

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "grounded_statecharts" / "live_credentialed_smoke"

# Mechanics smoke: two tasks/family, two repeats, six conditions.
SMOKE_CONDITIONS = (
    "direct_self_report",
    "statechart_g0",
    "statechart_g3",
    "envelope_only",
    "envelope_external_guards",
    "wrong_edge_guard",
)


def _selected_tasks():
    by_family: dict[str, list] = {}
    for task in smoke_tasks():
        by_family.setdefault(task.family, []).append(task)
    selected = []
    for family in ("artifact_completion", "recursive_constrained_tool_use"):
        selected.extend(by_family[family][:2])
    return tuple(selected)


def generate_results(output_dir: Path) -> dict[str, object]:
    if os.environ.get(LIVE_OPT_IN_ENV, "").strip() != "1":
        raise RuntimeError(f"set {LIVE_OPT_IN_ENV}=1 for credentialed smoke")
    executor = LiveExecutor.from_env()
    results = []
    failures: list[dict[str, object]] = []
    for task in _selected_tasks():
        for condition in SMOKE_CONDITIONS:
            for repeat_index in range(2):
                episode = LiveEpisode(
                    episode_id=(
                        f"cred-smoke:{task.task_id}:{condition}:r{repeat_index}"
                    ),
                    run_id="live-credentialed-smoke",
                    task=task,
                    condition=condition,
                    repeat_index=repeat_index,
                    model_id=executor.model_id,
                    provider_id=executor.provider_id,
                    adapter_id="live",
                    harness_digest=harness_digest_for(condition),
                    budget=DEFAULT_PILOT_BUDGET,
                    seed=int(digest(f"{task.task_id}:{condition}:{repeat_index}")[:8], 16),
                )
                try:
                    results.append(
                        run_episode(episode, executor=executor, planned_calls=1)
                    )
                except Exception as exc:  # noqa: BLE001 - smoke must finish matrix
                    failures.append(
                        {
                            "episode_id": episode.episode_id,
                            "error_type": type(exc).__name__,
                            "error": str(exc)[:500],
                        }
                    )

    rows = []
    for result in results:
        if result.sanitization.ok and result.public_row:
            rows.append(result.public_row)
    rows = sorted(rows, key=lambda row: canonical_json(row))

    summary = {
        "adapter_id": "live",
        "provider_id": executor.provider_id,
        "model_id": executor.model_id,
        "episode_count": len(results),
        "publishable_rows": len(rows),
        "allowed_claim": (
            "Credentialed smoke validates live-adapter mechanics only. "
            "Outcomes are discarded from held-out D2 pilots and authorize no "
            "scientific or commercial claim."
        ),
        "non_claims": [
            "Not a D2 pilot.",
            "Not a confirmatory CT/CHS/HU result.",
            "Raw provider transcripts remain outside public results/.",
        ],
        "gates": {
            "opt_in": True,
            "writes_to_artifacts_only": True,
            "all_publishable": bool(results) and len(rows) == len(results),
            "budget_ok": all(result.budget_receipt.ok for result in results) if results else False,
            "provider_failures": len(failures),
        },
        "provider_failures": failures,
        "integrity_failures": [
            result.episode.episode_id
            for result in results
            if not result.integrity.publishable
        ],
        "env": {
            "provider_env": os.environ.get(LIVE_PROVIDER_ENV),
            "model_env": os.environ.get(LIVE_MODEL_ENV),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    (output_dir / "rows.jsonl").write_text(
        "\n".join(canonical_json(row) for row in rows) + ("\n" if rows else "")
    )
    # Private diagnostics only under artifacts/
    private = [
        {
            "episode_id": result.episode.episode_id,
            "publishable": result.integrity.publishable,
            "action_scores": {
                "false_completion": result.false_completion,
                "task_success": result.task_success,
                "joint_success": result.joint_success,
                "refusal": result.refusal,
            },
            "usage": result.budget_receipt.usage.to_dict(),
        }
        for result in results
    ]
    (output_dir / "private_diagnostics.jsonl").write_text(
        "\n".join(canonical_json(row) for row in private) + "\n"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if "results" in args.output_dir.parts:
        raise SystemExit("refusing to write credentialed smoke under results/")
    summary = generate_results(args.output_dir)
    print(json.dumps({"output_dir": str(args.output_dir), **{
        k: summary[k] for k in ("episode_count", "publishable_rows", "provider_id", "model_id")
    }}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
