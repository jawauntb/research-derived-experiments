from __future__ import annotations

from experiments.world_responds.suite_c_teacher_free import run_teacher_free_suite
from experiments.world_responds.suite_c_teacher_free_wide_stats import (
    bootstrap_metrics,
    build_wide_stats,
)


def test_teacher_free_bootstrap_metrics_are_deterministic() -> None:
    payload = run_teacher_free_suite(
        train_seeds=[11, 22, 33],
        calibration_seeds=[44, 55, 66, 77],
        eval_seeds=[88, 99, 111, 122],
        base_seed=20260706,
    )

    first = bootstrap_metrics(payload["rows"], reps=25, seed=1234)
    second = bootstrap_metrics(payload["rows"], reps=25, seed=1234)

    assert first == second
    assert first["learned_final_component_mae"]["ci95_high"] < 0.13
    assert first["selectivity_lift_vs_matched_random"]["ci95_low"] > 0.0


def test_teacher_free_wide_stats_small_run_passes() -> None:
    stats = build_wide_stats(eval_seed_count=4, bootstrap_reps=25)

    assert stats["summary"]["gates"]["suite_pass"]["pass"]
    assert stats["point_metrics"]["learned_recovery_rate"] >= 0.75
    assert stats["point_metrics"]["stale_signal_recovery_rate"] == 0.0
