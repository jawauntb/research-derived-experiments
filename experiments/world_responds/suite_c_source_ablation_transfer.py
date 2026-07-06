"""Suite C source-estimate ablation and finite tool-call transfer.

The prior teacher-free policy used the simulator's privileged
``source_is_affected`` feature. This module replaces that feature with an
estimate computed from observable error/surprise jumps, then tests whether the
same learned inquiry law survives a simple JSON-like tool-call action surface.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, cast

import numpy as np

from experiments.world_responds.suite_c_contract import DEFAULT_CONFIG, SuiteCConfig
from experiments.world_responds.suite_c_neural_transfer import (
    FEATURE_NAMES,
    _existing_control_row,
    _mean,
    _rate,
)
from experiments.world_responds.suite_c_teacher_free import (
    COST_ONLY_PROXY_CONDITION,
    INITIAL_WEIGHT_MEAN,
    INITIAL_WEIGHT_SCALE,
    MATCHED_RANDOM_CONDITION,
    RECOVERY_ONLY_PROXY_CONDITION,
    STALE_CONTROL_CONDITION,
    SUPPRESSION_CONTROL_CONDITION,
    TEACHER_FREE_CONDITION,
    TEACHER_FREE_CONTROL_CONDITIONS,
    WRONG_CONTROL_CONDITION,
    LinearProbePolicy,
    _evaluation_rows,
    _policy_from_vector,
    _run_policy_trial,
    _teacher_free_reward,
    _threshold_score,
    summarize_teacher_free_records,
)

SOURCE_ESTIMATE_CONDITION = "teacher_free_estimated_source_policy"
SOURCE_ESTIMATE_STALE_CONDITION = "estimated_source_stale_signal"
SOURCE_ESTIMATE_WRONG_CONDITION = "estimated_source_wrong_signal"
SOURCE_ESTIMATE_SUPPRESSION_CONDITION = "estimated_source_signal_suppression"
SOURCE_ESTIMATE_MATCHED_RANDOM_CONDITION = "matched_random_estimated_source_budget"
TOOL_TRANSFER_CONDITION = "estimated_source_tool_transfer"
TOOL_TRANSFER_MALFORMED_CONDITION = "estimated_source_tool_malformed_control"
TOOL_TRANSFER_MATCHED_RANDOM_CONDITION = "matched_random_tool_transfer_budget"

SOURCE_ABLATION_JSON = Path(
    "experiments/world_responds/results/"
    "suite_c_source_ablation_transfer_2026_07_06.json"
)
SOURCE_ABLATION_MD = Path(
    "experiments/world_responds/results/"
    "suite_c_source_ablation_transfer_2026_07_06.md"
)
SOURCE_ABLATION_ROWS_JSONL = Path(
    "experiments/world_responds/results/"
    "suite_c_source_ablation_transfer_rows_2026_07_06.jsonl"
)

SOURCE_FEATURE_INDEX = FEATURE_NAMES.index("source_is_affected")


def estimate_source_is_affected(features: np.ndarray) -> float:
    """Estimate affected-source status without reading the privileged bit."""

    perceived_error = float(features[0])
    perceived_surprise = float(features[1])
    error_jump = max(float(features[2]), 0.0)
    surprise_jump = max(float(features[3]), 0.0)
    recent_probe_rate = float(features[7])
    raw = (
        2.8 * perceived_error
        + 2.4 * perceived_surprise
        + 5.2 * error_jump
        + 4.4 * surprise_jump
        - 0.6 * recent_probe_rate
        - 1.35
    )
    return float(1.0 / (1.0 + np.exp(-np.clip(raw, -40.0, 40.0))))


@dataclass
class EstimatedSourcePolicy:
    base_policy: LinearProbePolicy
    tool_surface: bool = False
    malformed_rate: float = 0.0
    tool_calls: int = 0
    invalid_tool_calls: int = 0

    @property
    def threshold(self) -> float:
        return self.base_policy.threshold

    def adjusted_features(self, features: np.ndarray) -> np.ndarray:
        adjusted = np.asarray(features, dtype=float).copy()
        adjusted[SOURCE_FEATURE_INDEX] = estimate_source_is_affected(adjusted)
        return adjusted

    def _is_malformed(self, adjusted: np.ndarray, probability: float) -> bool:
        if not self.tool_surface or probability < self.threshold or self.malformed_rate <= 0.0:
            return False
        key = abs(float(np.dot(adjusted, np.arange(1, len(adjusted) + 1))))
        pseudo = (int(key * 1_000_000) % 10_000) / 10_000.0
        return pseudo < self.malformed_rate

    def probability(self, features: np.ndarray) -> float:
        adjusted = self.adjusted_features(features)
        probability = self.base_policy.probability(adjusted)
        if self.tool_surface and probability >= self.threshold:
            self.tool_calls += 1
        if self._is_malformed(adjusted, probability):
            self.invalid_tool_calls += 1
            return 0.0
        return probability

    def to_record(self) -> dict[str, Any]:
        return {
            "policy_class": "estimated_source_policy",
            "source_identity_feature_used": False,
            "source_feature_replacement": "observable_error_surprise_jump_estimate",
            "tool_surface": self.tool_surface,
            "malformed_rate": self.malformed_rate,
            "base_policy": self.base_policy.to_record(),
        }


def _wrapped(policy: LinearProbePolicy) -> EstimatedSourcePolicy:
    return EstimatedSourcePolicy(policy)


def train_estimated_source_policy(
    seeds: list[int],
    *,
    base_seed: int = 20260706,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
    iterations: int = 5,
    population_size: int = 36,
    elite_count: int = 8,
) -> tuple[LinearProbePolicy, dict[str, Any]]:
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
            rows = _evaluation_rows(
                seeds,
                cast(Any, _wrapped(policy)),
                cfg=cfg,
                include_proxies=True,
            )
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
        raise ValueError("estimated-source CEM produced no candidates")
    policy = _policy_from_vector(best[1])
    return policy, {
        "training_regime": "teacher_free_reward_cem_estimated_source",
        "teacher_labels_used": False,
        "teacher_actions_used": False,
        "teacher_probabilities_used": False,
        "privileged_source_identity_used": False,
        "objective": "downstream Suite C reward with source feature replaced by observable estimate",
        "train_seeds": seeds,
        "iterations": iterations,
        "population_size": population_size,
        "elite_count": elite_count,
        "best_train_reward": float(best[0]),
        "best_train_suite_pass": bool(best[2]["gates"]["suite_pass"]["pass"]),
        "trace": trace,
    }


def calibrate_estimated_source_threshold(
    policy: LinearProbePolicy,
    seeds: list[int],
    *,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
    thresholds: tuple[float, ...] = (0.40, 0.45, 0.50, 0.55, 0.60, 0.65),
) -> tuple[LinearProbePolicy, dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for threshold in thresholds:
        candidate = policy.with_threshold(threshold)
        rows = _evaluation_rows(
            seeds,
            cast(Any, _wrapped(candidate)),
            cfg=cfg,
            include_proxies=True,
        )
        summary = summarize_teacher_free_records(rows, cfg=cfg)
        candidates.append(
            {
                "threshold": float(threshold),
                "score": _threshold_score(summary),
                "suite_pass": bool(summary["gates"]["suite_pass"]["pass"]),
            }
        )
    best = max(candidates, key=lambda item: (item["suite_pass"], item["score"]))
    return policy.with_threshold(float(best["threshold"])), {
        "selected_threshold": float(best["threshold"]),
        "candidate_thresholds": candidates,
    }


def _rename_rows(rows: list[dict[str, Any]], mapping: dict[str, str]) -> list[dict[str, Any]]:
    renamed = []
    for row in rows:
        new_row = dict(row)
        new_row["condition"] = mapping.get(str(row["condition"]), str(row["condition"]))
        renamed.append(new_row)
    return renamed


def _map_for_teacher_free_summary(
    rows: list[dict[str, Any]],
    *,
    candidate: str,
    stale: str,
    wrong: str,
    suppressed: str,
    matched: str,
) -> list[dict[str, Any]]:
    mapping = {
        candidate: TEACHER_FREE_CONDITION,
        stale: STALE_CONTROL_CONDITION,
        wrong: WRONG_CONTROL_CONDITION,
        suppressed: SUPPRESSION_CONTROL_CONDITION,
        matched: MATCHED_RANDOM_CONDITION,
    }
    return _rename_rows(rows, mapping)


def _generic_condition_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["condition"]), []).append(row)
    out = []
    for condition, group in sorted(grouped.items()):
        out.append(
            {
                "condition": condition,
                "n": len(group),
                "total_probes": _mean(group, "total_probes"),
                "first_selectivity_ratio": _mean(group, "first_selectivity_ratio"),
                "second_reopen_ratio": _mean(group, "second_reopen_ratio"),
                "final_component_mae": _mean(group, "final_component_mae"),
                "no_false_calm_rate": _rate(group, "no_false_calm"),
                "recovery_rate": _rate(group, "recovery_pass"),
                "reopen_rate": _rate(group, "reopen_pass"),
            }
        )
    return out


def _estimated_rows(
    seeds: list[int],
    policy: LinearProbePolicy,
    *,
    cfg: SuiteCConfig,
    tool_surface: bool = False,
    malformed_rate: float = 0.0,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    wrapped = EstimatedSourcePolicy(
        policy,
        tool_surface=tool_surface,
        malformed_rate=malformed_rate,
    )
    rows = _evaluation_rows(seeds, cast(Any, wrapped), cfg=cfg, include_proxies=True)
    return rows, {
        "tool_calls": wrapped.tool_calls,
        "invalid_tool_calls": wrapped.invalid_tool_calls,
    }


def run_source_ablation_transfer(
    *,
    train_seeds: list[int] | None = None,
    calibration_seeds: list[int] | None = None,
    eval_seeds: list[int] | None = None,
    base_seed: int = 20260706,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
    iterations: int = 5,
    population_size: int = 36,
    elite_count: int = 8,
) -> dict[str, Any]:
    if train_seeds is None:
        train_seeds = [base_seed + 171_000 + i * 997 for i in range(5)]
    if calibration_seeds is None:
        calibration_seeds = [base_seed + 181_000 + i * 997 for i in range(8)]
    if eval_seeds is None:
        eval_seeds = [base_seed + 191_000 + i * 997 for i in range(8)]
    overlap = (set(train_seeds) & set(calibration_seeds)) | (set(train_seeds) & set(eval_seeds))
    overlap |= set(calibration_seeds) & set(eval_seeds)
    if overlap:
        raise ValueError(f"train/calibration/eval seeds must be disjoint: {sorted(overlap)}")

    policy, training = train_estimated_source_policy(
        train_seeds,
        base_seed=base_seed,
        cfg=cfg,
        iterations=iterations,
        population_size=population_size,
        elite_count=elite_count,
    )
    policy, calibration = calibrate_estimated_source_threshold(policy, calibration_seeds, cfg=cfg)

    estimated_base_rows, _base_counters = _estimated_rows(eval_seeds, policy, cfg=cfg)
    estimated_mapping = {
        TEACHER_FREE_CONDITION: SOURCE_ESTIMATE_CONDITION,
        STALE_CONTROL_CONDITION: SOURCE_ESTIMATE_STALE_CONDITION,
        WRONG_CONTROL_CONDITION: SOURCE_ESTIMATE_WRONG_CONDITION,
        SUPPRESSION_CONTROL_CONDITION: SOURCE_ESTIMATE_SUPPRESSION_CONDITION,
        MATCHED_RANDOM_CONDITION: SOURCE_ESTIMATE_MATCHED_RANDOM_CONDITION,
    }
    estimated_rows = _rename_rows(estimated_base_rows, estimated_mapping)
    estimated_summary = summarize_teacher_free_records(
        _map_for_teacher_free_summary(
            estimated_rows,
            candidate=SOURCE_ESTIMATE_CONDITION,
            stale=SOURCE_ESTIMATE_STALE_CONDITION,
            wrong=SOURCE_ESTIMATE_WRONG_CONDITION,
            suppressed=SOURCE_ESTIMATE_SUPPRESSION_CONDITION,
            matched=SOURCE_ESTIMATE_MATCHED_RANDOM_CONDITION,
        ),
        cfg=cfg,
    )

    tool_base_rows, tool_counters = _estimated_rows(
        eval_seeds,
        policy,
        cfg=cfg,
        tool_surface=True,
    )
    tool_mapping = {
        TEACHER_FREE_CONDITION: TOOL_TRANSFER_CONDITION,
        STALE_CONTROL_CONDITION: SOURCE_ESTIMATE_STALE_CONDITION,
        WRONG_CONTROL_CONDITION: SOURCE_ESTIMATE_WRONG_CONDITION,
        SUPPRESSION_CONTROL_CONDITION: SOURCE_ESTIMATE_SUPPRESSION_CONDITION,
        MATCHED_RANDOM_CONDITION: TOOL_TRANSFER_MATCHED_RANDOM_CONDITION,
    }
    tool_rows = _rename_rows(tool_base_rows, tool_mapping)
    tool_summary = summarize_teacher_free_records(
        _map_for_teacher_free_summary(
            tool_rows,
            candidate=TOOL_TRANSFER_CONDITION,
            stale=SOURCE_ESTIMATE_STALE_CONDITION,
            wrong=SOURCE_ESTIMATE_WRONG_CONDITION,
            suppressed=SOURCE_ESTIMATE_SUPPRESSION_CONDITION,
            matched=TOOL_TRANSFER_MATCHED_RANDOM_CONDITION,
        ),
        cfg=cfg,
    )

    malformed_rows: list[dict[str, Any]] = []
    malformed_policy = EstimatedSourcePolicy(
        policy,
        tool_surface=True,
        malformed_rate=0.75,
    )
    for seed in eval_seeds:
        row = _run_policy_trial(
            TEACHER_FREE_CONDITION,
            seed,
            policy=cast(Any, malformed_policy),
            cfg=cfg,
        )
        row["condition"] = TOOL_TRANSFER_MALFORMED_CONDITION
        row["training_regime"] = "teacher_free_reward_cem_estimated_source_tool_malformed"
        row["privileged_source_identity_used"] = False
        malformed_rows.append(row)
    malformed_summary = _generic_condition_summaries(malformed_rows)[0]
    tool_candidate = {
        row["condition"]: row for row in _generic_condition_summaries(tool_rows)
    }[TOOL_TRANSFER_CONDITION]
    malformed_control_pass = (
        malformed_summary["recovery_rate"] <= 0.50
        or malformed_summary["final_component_mae"] > tool_candidate["final_component_mae"] * 1.35
    )

    all_rows = estimated_rows + tool_rows + malformed_rows
    return {
        "kind": "world_responds_suite_c_source_ablation_transfer",
        "manifest": {
            "suite": "Suite C source-estimate ablation and finite tool-call transfer",
            "claim_level": "finite diagnostic ablation",
            "train_seeds": train_seeds,
            "calibration_seeds": calibration_seeds,
            "eval_seeds": eval_seeds,
            "feature_names": list(FEATURE_NAMES),
            "source_identity_feature_used": False,
            "tool_transfer_type": "local JSON-like probe tool adapter, not external API-agent",
        },
        "model": EstimatedSourcePolicy(policy).to_record(),
        "training": training,
        "calibration": calibration,
        "rows": all_rows,
        "summaries": {
            "estimated_source": estimated_summary,
            "tool_transfer": tool_summary,
            "malformed_tool_control": malformed_summary,
        },
        "gates": {
            "estimated_source_suite_pass": estimated_summary["gates"]["suite_pass"],
            "tool_transfer_suite_pass": tool_summary["gates"]["suite_pass"],
            "malformed_tool_control_fails": {
                "pass": malformed_control_pass,
                "malformed_recovery_rate": malformed_summary["recovery_rate"],
                "malformed_final_component_mae": malformed_summary["final_component_mae"],
                "tool_final_component_mae": tool_candidate["final_component_mae"],
            },
            "suite_pass": {
                "pass": bool(
                    estimated_summary["gates"]["suite_pass"]["pass"]
                    and tool_summary["gates"]["suite_pass"]["pass"]
                    and malformed_control_pass
                )
            },
        },
        "tool_counters": {
            "valid_tool_transfer": tool_counters,
            "malformed_tool_control": {
                "tool_calls": malformed_policy.tool_calls,
                "invalid_tool_calls": malformed_policy.invalid_tool_calls,
            },
        },
        "non_claims": [
            "Not an external open-model or API-agent run.",
            "Not production reliability.",
            "Not consciousness or biological validation.",
        ],
    }


def write_artifacts(payload: dict[str, Any], out_root: Path = Path(".")) -> list[Path]:
    json_path = out_root / SOURCE_ABLATION_JSON
    md_path = out_root / SOURCE_ABLATION_MD
    rows_path = out_root / SOURCE_ABLATION_ROWS_JSONL
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with rows_path.open("w") as f:
        for row in payload["rows"]:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    est = payload["summaries"]["estimated_source"]["gates"]["suite_pass"]["pass"]
    tool = payload["summaries"]["tool_transfer"]["gates"]["suite_pass"]["pass"]
    malformed = payload["gates"]["malformed_tool_control_fails"]["pass"]
    lines = [
        "# Suite C Source-Estimate Ablation and Tool Transfer",
        "",
        "Date: 2026-07-06",
        "",
        "## Gate Status",
        "",
        f"- Estimated-source Suite C pass: {'PASS' if est else 'FAIL'}",
        f"- Tool-transfer Suite C pass: {'PASS' if tool else 'FAIL'}",
        f"- Malformed-tool control fails: {'PASS' if malformed else 'FAIL'}",
        f"- Combined finite gate: {'PASS' if payload['gates']['suite_pass']['pass'] else 'FAIL'}",
        "",
        "## Artifacts",
        "",
        f"- Summary JSON: `{SOURCE_ABLATION_JSON.as_posix()}`",
        f"- Rows JSONL: `{SOURCE_ABLATION_ROWS_JSONL.as_posix()}`",
        "",
        "## Claim Boundary",
        "",
        "This removes the privileged source-identity feature and routes the policy "
        "through a local JSON-like tool adapter. It is not an external open-model "
        "or API-agent result.",
    ]
    md_path.write_text("\n".join(lines) + "\n")
    return [json_path, md_path, rows_path]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", type=Path, default=Path("."))
    parser.add_argument("--eval-seeds", type=int, default=8)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--population-size", type=int, default=36)
    parser.add_argument("--elite-count", type=int, default=8)
    args = parser.parse_args()
    base_seed = 20260706
    payload = run_source_ablation_transfer(
        eval_seeds=[base_seed + 191_000 + i * 997 for i in range(args.eval_seeds)],
        iterations=args.iterations,
        population_size=args.population_size,
        elite_count=args.elite_count,
    )
    for path in write_artifacts(payload, args.out_root):
        print(path)


if __name__ == "__main__":
    main()
