"""Teacher-free reward search for Suite C adaptive inquiry.

This module keeps the Suite C simulator and gates fixed, but removes the direct
teacher-trace supervision used by ``suite_c_neural_transfer``. The learned
policy is a small linear probe head selected by cross-entropy method (CEM) on
downstream recovery, selectivity, reopenability, cost, and anti-cheat controls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import numpy as np

from experiments.world_responds.suite_c_contract import DEFAULT_CONFIG, SuiteCConfig
from experiments.world_responds.suite_c_neural_transfer import (
    FEATURE_NAMES,
    _existing_control_row,
    _mean,
    _rate,
    _sigmoid,
    _simulate,
)

TEACHER_FREE_CONDITION = "teacher_free_reward_policy"
STALE_CONTROL_CONDITION = "teacher_free_stale_signal"
WRONG_CONTROL_CONDITION = "teacher_free_wrong_signal"
SUPPRESSION_CONTROL_CONDITION = "teacher_free_signal_suppression"
MATCHED_RANDOM_CONDITION = "matched_random_teacher_free_budget"
RECOVERY_ONLY_PROXY_CONDITION = "recovery_only_proxy_policy"
COST_ONLY_PROXY_CONDITION = "cost_only_proxy_policy"

TEACHER_FREE_CONTROL_CONDITIONS = (
    STALE_CONTROL_CONDITION,
    WRONG_CONTROL_CONDITION,
    SUPPRESSION_CONTROL_CONDITION,
)
TEACHER_FREE_CONDITIONS = (
    "p22_learned_current_replay",
    "scheduled_null_anchor",
    "oracle_source",
    TEACHER_FREE_CONDITION,
    *TEACHER_FREE_CONTROL_CONDITIONS,
    RECOVERY_ONLY_PROXY_CONDITION,
    COST_ONLY_PROXY_CONDITION,
    MATCHED_RANDOM_CONDITION,
)

INITIAL_WEIGHT_MEAN = (
    1.50,
    1.40,
    2.50,
    2.30,
    -0.45,
    -0.70,
    0.10,
    -0.80,
    1.80,
    0.00,
)
INITIAL_WEIGHT_SCALE = (
    1.00,
    1.00,
    1.50,
    1.50,
    0.50,
    0.50,
    0.40,
    0.40,
    1.00,
    0.40,
)


@dataclass(frozen=True)
class LinearProbePolicy:
    """Serializable teacher-free linear inquiry policy."""

    weights: tuple[float, ...]
    bias: float
    threshold: float = 0.50

    def probability(self, features: np.ndarray) -> float:
        logit = float(np.dot(np.asarray(self.weights, dtype=float), features) + self.bias)
        return float(_sigmoid(logit))

    def with_threshold(self, threshold: float) -> "LinearProbePolicy":
        return LinearProbePolicy(
            weights=self.weights,
            bias=self.bias,
            threshold=float(threshold),
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "policy_class": "linear_probe_policy",
            "feature_names": list(FEATURE_NAMES),
            "weights": list(self.weights),
            "bias": self.bias,
            "threshold": self.threshold,
        }

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "LinearProbePolicy":
        return cls(
            weights=tuple(float(v) for v in record["weights"]),
            bias=float(record["bias"]),
            threshold=float(record["threshold"]),
        )


def _policy_from_vector(vector: np.ndarray) -> LinearProbePolicy:
    return LinearProbePolicy(
        weights=tuple(float(v) for v in vector[:-1]),
        bias=float(vector[-1]),
    )


def _run_policy_trial(
    condition: str,
    seed: int,
    *,
    policy: LinearProbePolicy,
    target_probe_count: int | None = None,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
) -> dict[str, Any]:
    control = "normal"
    sim_condition = condition
    if condition == STALE_CONTROL_CONDITION:
        control = "stale_signal"
        sim_condition = condition
    elif condition == WRONG_CONTROL_CONDITION:
        control = "wrong_signal"
        sim_condition = condition
    elif condition == SUPPRESSION_CONTROL_CONDITION:
        control = "signal_suppression"
        sim_condition = "signal_suppression_head"
    elif condition == MATCHED_RANDOM_CONDITION:
        sim_condition = "matched_random_learned_budget"
    elif condition not in {
        TEACHER_FREE_CONDITION,
        RECOVERY_ONLY_PROXY_CONDITION,
        COST_ONLY_PROXY_CONDITION,
    }:
        raise ValueError(f"unknown teacher-free Suite C condition: {condition}")

    row, _features, _labels = _simulate(
        condition=sim_condition,
        seed=seed,
        cfg=cfg,
        head=cast(Any, policy),
        control=control,
        target_probe_count=target_probe_count,
    )
    row["condition"] = condition
    row["training_regime"] = "teacher_free_reward_cem"
    row["teacher_labels_used"] = False
    row["teacher_actions_used"] = False
    row["teacher_probabilities_used"] = False
    return row


def _recovery_only_policy() -> LinearProbePolicy:
    return LinearProbePolicy(
        weights=(2.0, 2.0, 3.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        bias=-1.05,
    )


def _cost_only_policy() -> LinearProbePolicy:
    return LinearProbePolicy(weights=(0.0,) * len(FEATURE_NAMES), bias=-12.0)


def _evaluation_rows(
    seeds: list[int],
    policy: LinearProbePolicy,
    *,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
    include_proxies: bool = True,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    learned_budgets: dict[int, int] = {}
    for seed in seeds:
        for condition in ("p22_learned_current_replay", "scheduled_null_anchor", "oracle_source"):
            row = _existing_control_row(condition, seed, cfg)
            row["training_regime"] = "fixed_control"
            row["teacher_labels_used"] = False
            row["teacher_actions_used"] = False
            row["teacher_probabilities_used"] = False
            rows.append(row)

        learned = _run_policy_trial(TEACHER_FREE_CONDITION, seed, policy=policy, cfg=cfg)
        rows.append(learned)
        learned_budgets[seed] = int(learned["total_probes"])
        for condition in TEACHER_FREE_CONTROL_CONDITIONS:
            rows.append(_run_policy_trial(condition, seed, policy=policy, cfg=cfg))

        if include_proxies:
            rows.append(
                _run_policy_trial(
                    RECOVERY_ONLY_PROXY_CONDITION,
                    seed,
                    policy=_recovery_only_policy(),
                    cfg=cfg,
                )
            )
            rows.append(
                _run_policy_trial(
                    COST_ONLY_PROXY_CONDITION,
                    seed,
                    policy=_cost_only_policy(),
                    cfg=cfg,
                )
            )

    for seed in seeds:
        rows.append(
            _run_policy_trial(
                MATCHED_RANDOM_CONDITION,
                seed,
                policy=policy,
                target_probe_count=learned_budgets[seed],
                cfg=cfg,
            )
        )
    return rows


def condition_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["condition"]), []).append(row)
    unknown = sorted(set(grouped) - set(TEACHER_FREE_CONDITIONS))
    if unknown:
        raise ValueError(f"unknown teacher-free Suite C conditions: {unknown}")

    summaries: list[dict[str, Any]] = []
    for condition in TEACHER_FREE_CONDITIONS:
        condition_rows = grouped.get(condition, [])
        if not condition_rows:
            continue
        summaries.append(
            {
                "condition": condition,
                "n": len(condition_rows),
                "total_probes": _mean(condition_rows, "total_probes"),
                "affected_post_shift_density": _mean(
                    condition_rows, "affected_probe_density_post_shift"
                ),
                "unaffected_post_shift_density": _mean(
                    condition_rows, "unaffected_probe_density_post_shift"
                ),
                "first_reengagement_ratio": _mean(condition_rows, "first_reengagement_ratio"),
                "first_selectivity_ratio": _mean(condition_rows, "first_selectivity_ratio"),
                "second_reopen_ratio": _mean(condition_rows, "second_reopen_ratio"),
                "final_component_mae": _mean(condition_rows, "final_component_mae"),
                "post1_mae_auc": _mean(condition_rows, "post1_mae_auc"),
                "post2_mae_auc": _mean(condition_rows, "post2_mae_auc"),
                "probe_drop_fraction": _mean(condition_rows, "probe_drop_fraction"),
                "mae_drop_fraction": _mean(condition_rows, "mae_drop_fraction"),
                "surprise_drop_fraction": _mean(condition_rows, "surprise_drop_fraction"),
                "no_false_calm_rate": _rate(condition_rows, "no_false_calm"),
                "recovery_rate": _rate(condition_rows, "recovery_pass"),
                "reengagement_rate": _rate(condition_rows, "reengagement_pass"),
                "reopen_rate": _rate(condition_rows, "reopen_pass"),
                "terminal_pass_rate": _rate(condition_rows, "candidate_terminal_pass"),
                "cost_adjusted_score": _mean(condition_rows, "cost_adjusted_score"),
            }
        )
    return summaries


def summarize_teacher_free_records(
    rows: list[dict[str, Any]],
    *,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
) -> dict[str, Any]:
    by_condition = condition_summaries(rows)
    by_name = {row["condition"]: row for row in by_condition}
    missing = sorted(set(TEACHER_FREE_CONDITIONS) - set(by_name))
    if missing:
        raise ValueError(f"missing teacher-free Suite C conditions: {missing}")

    baseline = by_name["p22_learned_current_replay"]
    learned = by_name[TEACHER_FREE_CONDITION]
    stale = by_name[STALE_CONTROL_CONDITION]
    wrong = by_name[WRONG_CONTROL_CONDITION]
    suppressed = by_name[SUPPRESSION_CONTROL_CONDITION]
    scheduled = by_name["scheduled_null_anchor"]
    oracle = by_name["oracle_source"]
    matched = by_name[MATCHED_RANDOM_CONDITION]

    c1 = baseline["affected_post_shift_density"] <= 0.035
    c2 = (
        learned["first_reengagement_ratio"] >= cfg.reengagement_floor
        and learned["first_selectivity_ratio"] >= cfg.selectivity_floor
    )
    c3 = learned["recovery_rate"] >= 0.60
    c4 = learned["no_false_calm_rate"] >= 0.60 and (
        suppressed["no_false_calm_rate"] <= 0.34
        or suppressed["final_component_mae"] > cfg.recovery_threshold * 2.0
    )
    c5 = (
        learned["total_probes"] < scheduled["total_probes"]
        and learned["total_probes"] < oracle["total_probes"]
        and learned["final_component_mae"] <= cfg.recovery_threshold
        and matched["first_selectivity_ratio"] < learned["first_selectivity_ratio"]
    )
    c6 = learned["second_reopen_ratio"] >= cfg.reopen_floor
    t1 = all(
        not bool(row.get("teacher_labels_used"))
        and not bool(row.get("teacher_actions_used"))
        and not bool(row.get("teacher_probabilities_used"))
        for row in rows
    )
    stale_control = (
        stale["recovery_rate"] <= 0.50
        or stale["first_reengagement_ratio"] < cfg.reengagement_floor
    )
    wrong_control = wrong["first_selectivity_ratio"] < cfg.selectivity_floor
    suppression_control = (
        suppressed["no_false_calm_rate"] <= 0.34
        or suppressed["final_component_mae"] > cfg.recovery_threshold * 2.0
    )
    n1 = stale_control and wrong_control and suppression_control
    gates = {
        "C1_silence_replication": {
            "pass": c1,
            "baseline_post_shift_density": baseline["affected_post_shift_density"],
        },
        "C2_reengagement": {
            "pass": c2,
            "first_reengagement_ratio": learned["first_reengagement_ratio"],
            "first_selectivity_ratio": learned["first_selectivity_ratio"],
        },
        "C3_recovery": {
            "pass": c3,
            "recovery_rate": learned["recovery_rate"],
            "final_component_mae": learned["final_component_mae"],
        },
        "C4_no_false_calm": {
            "pass": c4,
            "learned_no_false_calm_rate": learned["no_false_calm_rate"],
            "suppressed_no_false_calm_rate": suppressed["no_false_calm_rate"],
            "suppressed_final_component_mae": suppressed["final_component_mae"],
        },
        "C5_cost_aware_inquiry": {
            "pass": c5,
            "learned_total_probes": learned["total_probes"],
            "scheduled_total_probes": scheduled["total_probes"],
            "oracle_total_probes": oracle["total_probes"],
            "matched_selectivity_ratio": matched["first_selectivity_ratio"],
        },
        "C6_reopenability": {
            "pass": c6,
            "second_reopen_ratio": learned["second_reopen_ratio"],
        },
        "T1_teacher_free_training": {
            "pass": t1,
            "teacher_labels_used": False,
            "teacher_actions_used": False,
            "teacher_probabilities_used": False,
        },
        "N1_learned_signal_controls": {
            "pass": n1,
            "stale_control_failed": stale_control,
            "wrong_signal_control_failed": wrong_control,
            "suppression_control_failed": suppression_control,
        },
    }
    gates["suite_pass"] = {"pass": all(bool(gate["pass"]) for gate in gates.values())}
    return {
        "n_rows": len(rows),
        "conditions": list(TEACHER_FREE_CONDITIONS),
        "candidate_condition": TEACHER_FREE_CONDITION,
        "control_conditions": list(TEACHER_FREE_CONTROL_CONDITIONS),
        "headline_condition": TEACHER_FREE_CONDITION,
        "by_condition": by_condition,
        "gates": gates,
    }


def _threshold_score(summary: dict[str, Any]) -> float:
    by_name = {row["condition"]: row for row in summary["by_condition"]}
    learned = by_name[TEACHER_FREE_CONDITION]
    gates = summary["gates"]
    gate_score = sum(
        float(bool(gates[name]["pass"]))
        for name in (
            "C2_reengagement",
            "C3_recovery",
            "C4_no_false_calm",
            "C5_cost_aware_inquiry",
            "C6_reopenability",
            "N1_learned_signal_controls",
        )
    )
    return (
        gate_score * 10.0
        + learned["cost_adjusted_score"]
        + learned["recovery_rate"]
        - 0.015 * max(0.0, learned["total_probes"] - 28.0)
    )


def _teacher_free_reward(summary: dict[str, Any]) -> float:
    by_name = {row["condition"]: row for row in summary["by_condition"]}
    learned = by_name[TEACHER_FREE_CONDITION]
    stale = by_name[STALE_CONTROL_CONDITION]
    wrong = by_name[WRONG_CONTROL_CONDITION]
    suppressed = by_name[SUPPRESSION_CONTROL_CONDITION]
    matched = by_name[MATCHED_RANDOM_CONDITION]
    gates = summary["gates"]
    reward = (
        2.0 * learned["recovery_rate"]
        + min(learned["first_selectivity_ratio"] / 5.0, 1.0)
        + min(learned["second_reopen_ratio"] / 2.0, 1.0)
        + 0.5 * learned["no_false_calm_rate"]
        - 0.004 * learned["total_probes"]
        - 1.5 * (1.0 - learned["no_false_calm_rate"])
    )
    if not (
        stale["recovery_rate"] <= 0.50
        or stale["first_reengagement_ratio"] < DEFAULT_CONFIG.reengagement_floor
    ):
        reward -= 6.0
    reward -= 4.0 * max(0.0, stale["recovery_rate"] - 0.50)
    reward -= 0.25 * max(0.0, stale["first_reengagement_ratio"] - DEFAULT_CONFIG.reengagement_floor)
    if wrong["first_selectivity_ratio"] >= DEFAULT_CONFIG.selectivity_floor:
        reward -= 3.0
    if not (
        suppressed["no_false_calm_rate"] <= 0.34
        or suppressed["final_component_mae"] > DEFAULT_CONFIG.recovery_threshold * 2.0
    ):
        reward -= 3.0
    if matched["first_selectivity_ratio"] >= learned["first_selectivity_ratio"]:
        reward -= 0.8
    reward += sum(float(bool(gate["pass"])) for gate in gates.values() if "pass" in gate)
    return float(reward)


def train_teacher_free_policy(
    seeds: list[int],
    *,
    base_seed: int = 20260706,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
    iterations: int = 5,
    population_size: int = 36,
    elite_count: int = 8,
) -> tuple[LinearProbePolicy, dict[str, Any]]:
    """Select a policy by CEM on downstream Suite C outcomes only."""

    if population_size < elite_count:
        raise ValueError("population_size must be >= elite_count")
    rng = np.random.default_rng(base_seed)
    mean = np.asarray((*INITIAL_WEIGHT_MEAN, -1.55), dtype=float)
    scale = np.asarray((*INITIAL_WEIGHT_SCALE, 0.80), dtype=float)
    trace: list[dict[str, Any]] = []
    best: tuple[float, np.ndarray, dict[str, Any]] | None = None

    for iteration in range(iterations):
        candidates: list[tuple[float, np.ndarray, dict[str, Any]]] = []
        for _idx in range(population_size):
            vector = rng.normal(mean, scale)
            policy = _policy_from_vector(vector)
            rows = _evaluation_rows(seeds, policy, cfg=cfg, include_proxies=True)
            summary = summarize_teacher_free_records(rows, cfg=cfg)
            score = _teacher_free_reward(summary)
            candidates.append((score, vector, summary))
        candidates.sort(key=lambda item: item[0], reverse=True)
        elites = candidates[:elite_count]
        elite_vectors = np.vstack([item[1] for item in elites])
        mean = elite_vectors.mean(axis=0)
        scale = np.maximum(elite_vectors.std(axis=0) * 0.85, 0.03)
        if best is None or elites[0][0] > best[0]:
            best = elites[0]
        trace.append(
            {
                "iteration": iteration,
                "best_reward": float(elites[0][0]),
                "best_suite_pass": bool(elites[0][2]["gates"]["suite_pass"]["pass"]),
                "elite_mean_reward": float(np.mean([item[0] for item in elites])),
            }
        )

    if best is None:
        raise ValueError("teacher-free CEM produced no candidates")
    policy = _policy_from_vector(best[1])
    training = {
        "training_regime": "teacher_free_reward_cem",
        "teacher_labels_used": False,
        "teacher_actions_used": False,
        "teacher_probabilities_used": False,
        "objective": "downstream Suite C reward over recovery, selectivity, reopenability, cost, and controls",
        "train_seeds": seeds,
        "iterations": iterations,
        "population_size": population_size,
        "elite_count": elite_count,
        "best_train_reward": float(best[0]),
        "best_train_suite_pass": bool(best[2]["gates"]["suite_pass"]["pass"]),
        "trace": trace,
    }
    return policy, training


def calibrate_threshold(
    policy: LinearProbePolicy,
    seeds: list[int],
    *,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
    thresholds: tuple[float, ...] = (0.40, 0.45, 0.50, 0.55, 0.60, 0.65),
) -> tuple[LinearProbePolicy, dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for threshold in thresholds:
        candidate = policy.with_threshold(threshold)
        rows = _evaluation_rows(seeds, candidate, cfg=cfg, include_proxies=True)
        summary = summarize_teacher_free_records(rows, cfg=cfg)
        candidates.append(
            {
                "threshold": float(threshold),
                "score": _threshold_score(summary),
                "suite_pass": bool(summary["gates"]["suite_pass"]["pass"]),
                "summary": summary,
            }
        )
    best = max(candidates, key=lambda item: (item["suite_pass"], item["score"]))
    return policy.with_threshold(float(best["threshold"])), {
        "selected_threshold": float(best["threshold"]),
        "candidate_thresholds": [
            {
                "threshold": float(item["threshold"]),
                "score": float(item["score"]),
                "suite_pass": bool(item["suite_pass"]),
            }
            for item in candidates
        ],
    }


def run_teacher_free_suite(
    *,
    train_seeds: list[int] | None = None,
    calibration_seeds: list[int] | None = None,
    eval_seeds: list[int] | None = None,
    base_seed: int = 20260706,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
) -> dict[str, Any]:
    if train_seeds is None:
        train_seeds = [base_seed + 71_000 + i * 997 for i in range(5)]
    if calibration_seeds is None:
        calibration_seeds = [base_seed + 81_000 + i * 997 for i in range(8)]
    if eval_seeds is None:
        eval_seeds = [base_seed + 91_000 + i * 997 for i in range(8)]
    overlap = (set(train_seeds) & set(calibration_seeds)) | (set(train_seeds) & set(eval_seeds))
    overlap |= set(calibration_seeds) & set(eval_seeds)
    if overlap:
        raise ValueError(f"train/calibration/eval seeds must be disjoint: {sorted(overlap)}")

    policy, training = train_teacher_free_policy(train_seeds, base_seed=base_seed, cfg=cfg)
    policy, calibration = calibrate_threshold(policy, calibration_seeds, cfg=cfg)
    rows = _evaluation_rows(eval_seeds, policy, cfg=cfg, include_proxies=True)
    summary = summarize_teacher_free_records(rows, cfg=cfg)
    return {
        "kind": "world_responds_suite_c_teacher_free_inquiry",
        "manifest": {
            "suite": "Suite C teacher-free inquiry",
            "claim_level": "reward-trained finite-policy diagnostic",
            "conditions": list(TEACHER_FREE_CONDITIONS),
            "candidate_condition": TEACHER_FREE_CONDITION,
            "control_conditions": list(TEACHER_FREE_CONTROL_CONDITIONS),
            "train_seeds": train_seeds,
            "calibration_seeds": calibration_seeds,
            "eval_seeds": eval_seeds,
            "steps": cfg.steps,
            "first_shift": cfg.first_shift,
            "second_shift": cfg.second_shift,
            "feature_names": list(FEATURE_NAMES),
            "matched_budget_source": f"{TEACHER_FREE_CONDITION} total probes per eval seed",
            "matched_budget_condition": TEACHER_FREE_CONDITION,
        },
        "model": policy.to_record(),
        "training": training,
        "calibration": calibration,
        "rows": rows,
        "summary": summary,
    }
