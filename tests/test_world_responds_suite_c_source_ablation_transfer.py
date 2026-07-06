from __future__ import annotations

import numpy as np

from experiments.world_responds.suite_c_teacher_free import LinearProbePolicy
from experiments.world_responds.suite_c_source_ablation_transfer import (
    SOURCE_FEATURE_INDEX,
    EstimatedSourcePolicy,
    run_source_ablation_transfer,
)


def test_estimated_source_policy_ignores_privileged_source_bit() -> None:
    base = LinearProbePolicy(
        weights=(0.0,) * SOURCE_FEATURE_INDEX + (6.0, 0.0),
        bias=-1.0,
    )
    policy = EstimatedSourcePolicy(base)
    features_a = np.asarray([0.7, 0.6, 0.4, 0.3, 0.0, 0.0, 0.2, 0.0, 0.0, 0.5])
    features_b = features_a.copy()
    features_b[SOURCE_FEATURE_INDEX] = 1.0

    assert policy.probability(features_a) == policy.probability(features_b)


def test_source_ablation_small_run_emits_transfer_sections() -> None:
    payload = run_source_ablation_transfer(
        train_seeds=[11, 22],
        calibration_seeds=[33, 44, 55],
        eval_seeds=[66, 77],
        base_seed=20260706,
        iterations=2,
        population_size=8,
        elite_count=3,
    )

    assert not payload["training"]["teacher_labels_used"]
    assert not payload["training"]["privileged_source_identity_used"]
    assert "estimated_source" in payload["summaries"]
    assert "tool_transfer" in payload["summaries"]
    assert "malformed_tool_control" in payload["summaries"]
    assert "suite_pass" in payload["gates"]
