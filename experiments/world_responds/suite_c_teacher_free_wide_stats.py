"""Wider held-out seed and bootstrap report for Suite C teacher-free inquiry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np

from experiments.world_responds.suite_c_teacher_free import (
    MATCHED_RANDOM_CONDITION,
    SUPPRESSION_CONTROL_CONDITION,
    STALE_CONTROL_CONDITION,
    TEACHER_FREE_CONDITION,
    WRONG_CONTROL_CONDITION,
    run_teacher_free_suite,
    summarize_teacher_free_records,
)

WIDE_STATS_JSON = Path(
    "experiments/world_responds/results/suite_c_teacher_free_wide_stats_2026_07_06.json"
)
WIDE_STATS_MD = Path(
    "experiments/world_responds/results/suite_c_teacher_free_wide_stats_2026_07_06.md"
)

MetricFn = Callable[[dict[str, dict[str, Any]], dict[str, Any]], float]


def _fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def _by_condition(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["condition"]: row for row in summary["by_condition"]}


def _metric_fns() -> dict[str, MetricFn]:
    return {
        "learned_final_component_mae": lambda c, _s: float(
            c[TEACHER_FREE_CONDITION]["final_component_mae"]
        ),
        "learned_recovery_rate": lambda c, _s: float(c[TEACHER_FREE_CONDITION]["recovery_rate"]),
        "learned_first_selectivity_ratio": lambda c, _s: float(
            c[TEACHER_FREE_CONDITION]["first_selectivity_ratio"]
        ),
        "learned_second_reopen_ratio": lambda c, _s: float(
            c[TEACHER_FREE_CONDITION]["second_reopen_ratio"]
        ),
        "learned_total_probes": lambda c, _s: float(c[TEACHER_FREE_CONDITION]["total_probes"]),
        "matched_random_selectivity_ratio": lambda c, _s: float(
            c[MATCHED_RANDOM_CONDITION]["first_selectivity_ratio"]
        ),
        "selectivity_lift_vs_matched_random": lambda c, _s: float(
            c[TEACHER_FREE_CONDITION]["first_selectivity_ratio"]
            - c[MATCHED_RANDOM_CONDITION]["first_selectivity_ratio"]
        ),
        "final_mae_gain_vs_matched_random": lambda c, _s: float(
            c[MATCHED_RANDOM_CONDITION]["final_component_mae"]
            - c[TEACHER_FREE_CONDITION]["final_component_mae"]
        ),
        "stale_signal_recovery_rate": lambda c, _s: float(
            c[STALE_CONTROL_CONDITION]["recovery_rate"]
        ),
        "wrong_signal_selectivity_ratio": lambda c, _s: float(
            c[WRONG_CONTROL_CONDITION]["first_selectivity_ratio"]
        ),
        "suppressed_signal_final_component_mae": lambda c, _s: float(
            c[SUPPRESSION_CONTROL_CONDITION]["final_component_mae"]
        ),
        "suite_pass_rate": lambda _c, s: float(bool(s["gates"]["suite_pass"]["pass"])),
    }


def _seed_groups(rows: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    groups: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(int(row["seed"]), []).append(row)
    return groups


def _summarize_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    summary = summarize_teacher_free_records(rows)
    by_condition = _by_condition(summary)
    return {name: fn(by_condition, summary) for name, fn in _metric_fns().items()}


def bootstrap_metrics(
    rows: list[dict[str, Any]],
    *,
    reps: int = 1000,
    seed: int = 20260706,
) -> dict[str, Any]:
    groups = _seed_groups(rows)
    seed_ids = sorted(groups)
    rng = np.random.default_rng(seed)
    metric_values: dict[str, list[float]] = {name: [] for name in _metric_fns()}
    for _rep in range(reps):
        sampled = rng.choice(seed_ids, size=len(seed_ids), replace=True)
        sampled_rows = [row for seed_id in sampled for row in groups[int(seed_id)]]
        values = _summarize_metrics(sampled_rows)
        for name, value in values.items():
            metric_values[name].append(float(value))
    return {
        name: {
            "mean": float(np.mean(values)),
            "ci95_low": float(np.percentile(values, 2.5)),
            "ci95_high": float(np.percentile(values, 97.5)),
        }
        for name, values in metric_values.items()
    }


def build_wide_stats(
    *,
    base_seed: int = 20260706,
    eval_seed_count: int = 64,
    bootstrap_reps: int = 1000,
) -> dict[str, Any]:
    eval_seeds = [base_seed + 151_000 + i * 997 for i in range(eval_seed_count)]
    payload = run_teacher_free_suite(base_seed=base_seed, eval_seeds=eval_seeds)
    point_metrics = _summarize_metrics(payload["rows"])
    ci = bootstrap_metrics(payload["rows"], reps=bootstrap_reps, seed=base_seed + 404)
    return {
        "run_id": "suite_c_teacher_free_wide_stats_2026_07_06",
        "base_seed": base_seed,
        "eval_seed_count": eval_seed_count,
        "bootstrap_reps": bootstrap_reps,
        "train_seeds": payload["manifest"]["train_seeds"],
        "calibration_seeds": payload["manifest"]["calibration_seeds"],
        "eval_seeds": eval_seeds,
        "summary": payload["summary"],
        "point_metrics": point_metrics,
        "bootstrap_ci95": ci,
        "allowed_claim": (
            "Across a wider held-out finite Suite C seed panel, the teacher-free "
            "reward/CEM policy preserves the original C1-C6 and T1/N1 pass while "
            "matched-random, stale, wrong, and suppressed-signal controls remain "
            "separated."
        ),
        "non_claims": [
            "Not an open-agent or API-agent result.",
            "Not biological or human validation.",
            "Not a production reliability certificate.",
            "Not a consciousness test.",
        ],
    }


def write_report(stats: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    ci = stats["bootstrap_ci95"]
    point = stats["point_metrics"]
    gates = stats["summary"]["gates"]
    lines = [
        "# Suite C Teacher-Free Wide-Seed Bootstrap",
        "",
        "Date: 2026-07-06",
        "",
        "## Setup",
        "",
        f"- Held-out eval seeds: {stats['eval_seed_count']}",
        f"- Bootstrap reps over eval seeds: {stats['bootstrap_reps']}",
        "- Training regime: teacher-free reward/CEM linear probe policy.",
        "- Units: eval seed clusters; each bootstrap sample resamples full per-seed condition rows.",
        "",
        "## Gate Status",
        "",
        "| Gate | Pass? |",
        "| --- | --- |",
    ]
    for name, gate in gates.items():
        lines.append(f"| {name} | {'PASS' if gate['pass'] else 'FAIL'} |")
    lines.extend(
        [
            "",
            "## Bootstrap Metrics",
            "",
            "| Metric | Point | 95% CI |",
            "| --- | ---: | ---: |",
        ]
    )
    for name in [
        "learned_final_component_mae",
        "learned_recovery_rate",
        "learned_first_selectivity_ratio",
        "learned_second_reopen_ratio",
        "learned_total_probes",
        "matched_random_selectivity_ratio",
        "selectivity_lift_vs_matched_random",
        "final_mae_gain_vs_matched_random",
        "stale_signal_recovery_rate",
        "wrong_signal_selectivity_ratio",
        "suppressed_signal_final_component_mae",
        "suite_pass_rate",
    ]:
        entry = ci[name]
        lines.append(
            f"| `{name}` | {_fmt(point[name])} | "
            f"[{_fmt(entry['ci95_low'])}, {_fmt(entry['ci95_high'])}] |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            stats["allowed_claim"],
            "",
            "The interval is still finite-harness evidence, not an open-agent claim. "
            "The next paper-grade step is an ablation that replaces the privileged "
            "source-is-affected feature with a learned or noisy source estimate.",
        ]
    )
    out.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", type=Path, default=Path("."))
    parser.add_argument("--eval-seeds", type=int, default=64)
    parser.add_argument("--bootstrap-reps", type=int, default=1000)
    args = parser.parse_args()
    stats = build_wide_stats(eval_seed_count=args.eval_seeds, bootstrap_reps=args.bootstrap_reps)
    json_path = args.out_root / WIDE_STATS_JSON
    md_path = args.out_root / WIDE_STATS_MD
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n")
    write_report(stats, md_path)
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
