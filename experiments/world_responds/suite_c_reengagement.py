"""Suite C re-engagement benchmark under world change.

This module is intentionally small and deterministic. It does not replace the
older neural world-responds sweeps; it packages the Suite C gate as a finite
benchmark harness with explicit controls for silence, anxiety, false calm, cost,
and second-shift re-openability.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from experiments.world_responds.suite_c_contract import (
    AFFECTED_BUCKETS,
    BUCKETS,
    CANDIDATE_CONDITIONS,
    CONDITIONS,
    CONTROL_CONDITIONS,
    DEFAULT_CONFIG,
    FULL_SUITE_C_MECHANISMS,
    UNAFFECTED_BUCKETS,
    SuiteCConfig,
    SuiteCMechanisms,
)


def _bucket_indices(names: tuple[str, ...]) -> list[int]:
    return [BUCKETS.index(name) for name in names]


AFFECTED_IDX = _bucket_indices(AFFECTED_BUCKETS)
UNAFFECTED_IDX = _bucket_indices(UNAFFECTED_BUCKETS)


def _window_density(
    probe_history: dict[tuple[int, int], int],
    window: range,
    bucket_indices: list[int],
) -> float:
    slots = max(len(window) * len(bucket_indices), 1)
    count = sum(probe_history.get((t, b), 0) for t in window for b in bucket_indices)
    return float(count / slots)


def _window_mean(
    series: list[np.ndarray],
    window: range,
    bucket_indices: list[int],
) -> float:
    if not series:
        return 0.0
    values = []
    for t in window:
        if 0 <= t < len(series):
            values.extend(float(series[t][b]) for b in bucket_indices)
    if not values:
        return 0.0
    return float(np.mean(values))


def _safe_ratio(num: float, den: float, eps: float = 0.02) -> float:
    return float(num / max(den, eps))


def _drop_fraction(early: float, late: float) -> float:
    return float(max(0.0, early - late) / max(early, 1e-9))


def _learn_rate(condition: str) -> float:
    rates = {
        "p22_learned_current_replay": 0.12,
        "two_timescale_plus_prediction_error": 0.16,
        "fixed_surprise_decrement": 0.055,
        "scheduled_null_anchor": 0.34,
        "oracle_source": 0.35,
        "decision_refractory": 0.38,
        "burst_then_refractory": 0.43,
        "learned_cooldown_head": 0.40,
        "matched_random_time_budget": 0.18,
    }
    return rates[condition]


def _passive_rate(condition: str) -> float:
    rates = {
        "p22_learned_current_replay": 0.004,
        "two_timescale_plus_prediction_error": 0.010,
        "fixed_surprise_decrement": 0.002,
        "scheduled_null_anchor": 0.014,
        "oracle_source": 0.016,
        "decision_refractory": 0.018,
        "burst_then_refractory": 0.017,
        "learned_cooldown_head": 0.020,
        "matched_random_time_budget": 0.007,
    }
    return rates[condition]


def _make_matched_slots(
    rng: np.random.Generator,
    target_probe_count: int,
    cfg: SuiteCConfig,
) -> set[tuple[int, int]]:
    slots = [(t, b) for t in range(cfg.steps) for b in range(len(BUCKETS))]
    budget = min(max(target_probe_count, 0), len(slots))
    if budget == 0:
        return set()
    choices = rng.choice(len(slots), size=budget, replace=False)
    return {slots[int(i)] for i in choices}


def _condition_takes_probe(
    *,
    condition: str,
    rng: np.random.Generator,
    t: int,
    b: int,
    error: np.ndarray,
    surprise: np.ndarray,
    effort: np.ndarray,
    improvement: np.ndarray,
    burst_remaining: np.ndarray,
    cooldown_remaining: np.ndarray,
    matched_slots: set[tuple[int, int]],
    cfg: SuiteCConfig,
    mechanisms: SuiteCMechanisms,
) -> bool:
    affected = b in AFFECTED_IDX
    score_noise = float(rng.normal(0.0, 0.018))
    base_score = float(0.72 * surprise[b] + 0.38 * error[b] + score_noise)

    if condition == "matched_random_time_budget":
        return (t, b) in matched_slots

    if condition == "scheduled_null_anchor":
        return (t + b) % 3 == 0

    if condition == "oracle_source":
        shift_window = (
            cfg.first_shift <= t < cfg.post_first_end
            or cfg.second_shift <= t < cfg.post_second_end
        )
        if affected and (shift_window or error[b] > 0.12):
            return bool(rng.random() < 0.66)
        if t < cfg.first_shift and error[b] > 0.18:
            return bool(rng.random() < 0.28)
        return bool(rng.random() < 0.08)

    if condition == "p22_learned_current_replay":
        if t < cfg.first_shift:
            return base_score > 0.29 and bool(rng.random() < 0.72)
        return affected and bool(rng.random() < 0.012)

    if condition == "two_timescale_plus_prediction_error":
        anxious_bonus = 0.10 if t >= cfg.first_shift else 0.0
        return base_score + anxious_bonus > 0.22

    if condition == "fixed_surprise_decrement":
        return base_score > 0.24

    if condition == "decision_refractory":
        if t < cfg.first_shift and error[b] > 0.18:
            return base_score > 0.25 + 0.12 * float(effort[b])
        threshold = 0.27 + 0.18 * float(effort[b])
        if affected and t in range(cfg.first_shift, cfg.first_shift + 5):
            threshold -= 0.035
        if affected and t in range(cfg.second_shift, cfg.second_shift + 5):
            threshold -= 0.035
        return base_score > threshold

    if condition == "burst_then_refractory":
        if t < cfg.first_shift and error[b] > 0.18:
            return (t + b) % 5 == 0
        if mechanisms.cool and cooldown_remaining[b] > 0:
            return False
        if not mechanisms.reopen and affected and t >= cfg.second_shift:
            # Detection remains live in error/surprise state, but the second
            # intervention cannot reopen the probe-action commitment.
            return False
        shift_window = (
            cfg.first_shift <= t < cfg.post_first_end
            or cfg.second_shift <= t < cfg.post_second_end
        )
        allocated = affected or not mechanisms.allocate
        if allocated and shift_window and burst_remaining[b] > 0 and error[b] > 0.10:
            return True
        return base_score > 0.36 + 0.16 * float(effort[b])

    if condition == "learned_cooldown_head":
        if t < cfg.first_shift and error[b] > 0.18:
            return base_score > 0.24 + 0.11 * float(effort[b])
        recovered_bonus = 0.11 * float(improvement[b])
        threshold = 0.25 + 0.17 * float(effort[b]) + recovered_bonus
        if affected and t in range(cfg.first_shift, cfg.first_shift + 6):
            threshold -= 0.045
        if affected and t in range(cfg.second_shift, cfg.second_shift + 6):
            threshold -= 0.045
        return base_score > threshold

    raise ValueError(f"unknown Suite C condition: {condition}")


def run_trial(
    condition: str,
    seed: int,
    *,
    target_probe_count: int | None = None,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
    mechanisms: SuiteCMechanisms = FULL_SUITE_C_MECHANISMS,
) -> dict[str, Any]:
    """Run one deterministic Suite C cell and return a JSON-compatible row."""

    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition {condition!r}")
    if condition != "burst_then_refractory" and mechanisms != FULL_SUITE_C_MECHANISMS:
        raise ValueError("Suite C mechanism interventions apply only to burst_then_refractory")
    rng = np.random.default_rng(seed)
    n_buckets = len(BUCKETS)
    error = rng.normal(0.26, 0.025, size=n_buckets).clip(0.16, 0.34)
    surprise = (error + rng.normal(0.0, 0.018, size=n_buckets)).clip(0.04, None)
    effort = np.zeros(n_buckets, dtype=float)
    improvement = np.zeros(n_buckets, dtype=float)
    burst_remaining = np.zeros(n_buckets, dtype=float)
    cooldown_remaining = np.zeros(n_buckets, dtype=float)
    probe_history: dict[tuple[int, int], int] = {}
    error_history: list[np.ndarray] = []
    surprise_history: list[np.ndarray] = []
    matched_slots = _make_matched_slots(
        rng,
        target_probe_count if target_probe_count is not None else 58,
        cfg,
    )

    for t in range(cfg.steps):
        if t in {cfg.first_shift, cfg.second_shift}:
            for b in AFFECTED_IDX:
                error[b] += float(rng.normal(0.56, 0.035))
                surprise[b] += float(rng.normal(0.47, 0.025))
                if condition == "burst_then_refractory":
                    should_rearm = t == cfg.first_shift or mechanisms.reopen
                    allocated = b in AFFECTED_IDX or not mechanisms.allocate
                    if should_rearm and allocated:
                        burst_remaining[b] = 8.0
                        cooldown_remaining[b] = 0.0
            if condition == "burst_then_refractory" and not mechanisms.allocate:
                should_rearm = t == cfg.first_shift or mechanisms.reopen
                if should_rearm:
                    for b in UNAFFECTED_IDX:
                        burst_remaining[b] = 8.0
                        cooldown_remaining[b] = 0.0

        effort *= 0.72
        cooldown_remaining = np.maximum(0.0, cooldown_remaining - 1.0)

        for b in range(n_buckets):
            take_probe = _condition_takes_probe(
                condition=condition,
                rng=rng,
                t=t,
                b=b,
                error=error,
                surprise=surprise,
                effort=effort,
                improvement=improvement,
                burst_remaining=burst_remaining,
                cooldown_remaining=cooldown_remaining,
                matched_slots=matched_slots,
                cfg=cfg,
                mechanisms=mechanisms,
            )
            before = float(error[b])
            if take_probe:
                probe_history[(t, b)] = 1
                rate = _learn_rate(condition)
                stochastic_gain = float(rng.normal(0.0, 0.012))
                error[b] = max(0.012, error[b] * (1.0 - rate - stochastic_gain))
                improvement[b] = 0.70 * improvement[b] + 0.30 * max(0.0, before - error[b])
                effort[b] += 1.0
                if condition == "fixed_surprise_decrement":
                    surprise[b] = max(0.01, surprise[b] - 0.50)
                else:
                    surprise[b] = max(0.012, 0.68 * surprise[b] + 0.24 * error[b])
                if condition == "burst_then_refractory" and (
                    b in AFFECTED_IDX or not mechanisms.allocate
                ):
                    burst_remaining[b] = max(0.0, burst_remaining[b] - 1.0)
                    if burst_remaining[b] == 0.0 and mechanisms.cool:
                        cooldown_remaining[b] = 3.0
            else:
                drift = 0.004 if b in AFFECTED_IDX else 0.0015
                passive = _passive_rate(condition)
                error[b] = max(0.010, error[b] * (1.0 - passive) + drift)
                if condition == "fixed_surprise_decrement":
                    surprise[b] = max(0.010, 0.90 * surprise[b] + 0.04 * error[b])
                else:
                    surprise[b] = max(
                        0.010,
                        0.82 * surprise[b]
                        + 0.15 * error[b]
                        + float(rng.normal(0.0, 0.006)),
                    )

        error_history.append(error.copy())
        surprise_history.append(surprise.copy())

    pre1 = range(cfg.pre_first_start, cfg.first_shift)
    post1 = range(cfg.first_shift, cfg.post_first_end)
    post1_late = range(cfg.late_first_start, cfg.second_shift)
    pre2 = range(cfg.pre_second_start, cfg.second_shift)
    post2 = range(cfg.second_shift, cfg.post_second_end)
    final_window = range(cfg.final_start, cfg.steps)

    affected_pre1_density = _window_density(probe_history, pre1, AFFECTED_IDX)
    affected_post1_density = _window_density(probe_history, post1, AFFECTED_IDX)
    unaffected_post1_density = _window_density(probe_history, post1, UNAFFECTED_IDX)
    affected_pre2_density = _window_density(probe_history, pre2, AFFECTED_IDX)
    affected_post2_density = _window_density(probe_history, post2, AFFECTED_IDX)
    early_probe_density = _window_density(probe_history, range(cfg.first_shift, cfg.first_shift + 6), AFFECTED_IDX)
    late_probe_density = _window_density(probe_history, post1_late, AFFECTED_IDX)
    early_mae = _window_mean(error_history, range(cfg.first_shift, cfg.first_shift + 6), AFFECTED_IDX)
    late_mae = _window_mean(error_history, post1_late, AFFECTED_IDX)
    early_surprise = _window_mean(surprise_history, range(cfg.first_shift, cfg.first_shift + 6), AFFECTED_IDX)
    late_surprise = _window_mean(surprise_history, post1_late, AFFECTED_IDX)
    final_component_mae = _window_mean(error_history, final_window, AFFECTED_IDX)
    post1_mae_auc = _window_mean(error_history, post1, AFFECTED_IDX)
    post2_mae_auc = _window_mean(error_history, post2, AFFECTED_IDX)
    total_probes = int(sum(probe_history.values()))
    affected_total_probes = int(
        sum(v for (t, b), v in probe_history.items() if b in AFFECTED_IDX)
    )
    unaffected_total_probes = total_probes - affected_total_probes
    probe_drop_fraction = _drop_fraction(early_probe_density, late_probe_density)
    mae_drop_fraction = _drop_fraction(early_mae, late_mae)
    surprise_drop_fraction = _drop_fraction(early_surprise, late_surprise)
    no_false_calm = (
        (condition != "fixed_surprise_decrement" and final_component_mae <= cfg.recovery_threshold)
        or probe_drop_fraction <= 0.05
        or (
            surprise_drop_fraction >= 0.5 * probe_drop_fraction
            and mae_drop_fraction >= 0.33 * probe_drop_fraction
            and final_component_mae <= 0.16
            and condition != "fixed_surprise_decrement"
        )
    )

    first_reengagement_ratio = _safe_ratio(affected_post1_density, affected_pre1_density)
    first_selectivity_ratio = _safe_ratio(affected_post1_density, unaffected_post1_density)
    second_reopen_ratio = _safe_ratio(affected_post2_density, affected_pre2_density)
    recovery_pass = final_component_mae <= cfg.recovery_threshold
    reengagement_pass = (
        first_reengagement_ratio >= cfg.reengagement_floor
        and first_selectivity_ratio >= cfg.selectivity_floor
    )
    reopen_pass = second_reopen_ratio >= cfg.reopen_floor
    candidate_terminal_pass = (
        condition in CANDIDATE_CONDITIONS
        and reengagement_pass
        and recovery_pass
        and no_false_calm
        and reopen_pass
    )
    cost_adjusted_score = (
        (1.0 - min(final_component_mae, 1.0))
        + min(first_selectivity_ratio / 5.0, 1.0)
        + min(second_reopen_ratio / 2.0, 1.0)
        - total_probes / 250.0
    )

    return {
        "condition": condition,
        "seed": seed,
        "steps": cfg.steps,
        "target_probe_count": target_probe_count,
        "total_probes": total_probes,
        "affected_total_probes": affected_total_probes,
        "unaffected_total_probes": unaffected_total_probes,
        "affected_probe_density_pre_shift": affected_pre1_density,
        "affected_probe_density_post_shift": affected_post1_density,
        "unaffected_probe_density_post_shift": unaffected_post1_density,
        "affected_probe_density_pre_second_shift": affected_pre2_density,
        "affected_probe_density_post_second_shift": affected_post2_density,
        "first_reengagement_ratio": first_reengagement_ratio,
        "first_selectivity_ratio": first_selectivity_ratio,
        "second_reopen_ratio": second_reopen_ratio,
        "early_probe_density": early_probe_density,
        "late_probe_density": late_probe_density,
        "early_mae": early_mae,
        "late_mae": late_mae,
        "early_surprise": early_surprise,
        "late_surprise": late_surprise,
        "probe_drop_fraction": probe_drop_fraction,
        "mae_drop_fraction": mae_drop_fraction,
        "surprise_drop_fraction": surprise_drop_fraction,
        "final_component_mae": final_component_mae,
        "post1_mae_auc": post1_mae_auc,
        "post2_mae_auc": post2_mae_auc,
        "no_false_calm": no_false_calm,
        "recovery_pass": recovery_pass,
        "reengagement_pass": reengagement_pass,
        "reopen_pass": reopen_pass,
        "candidate_terminal_pass": candidate_terminal_pass,
        "cost_adjusted_score": cost_adjusted_score,
    }


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row[key]) for row in rows if key in row and row[key] is not None]
    if not values:
        return 0.0
    return float(np.mean(values))


def _rate(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    return float(sum(bool(row.get(key, False)) for row in rows) / len(rows))


def _condition_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["condition"])].append(row)

    by_condition: list[dict[str, Any]] = []
    for condition in CONDITIONS:
        condition_rows = grouped.get(condition, [])
        if not condition_rows:
            continue
        by_condition.append(
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
    return by_condition


def _select_headline_candidate(by_name: dict[str, dict[str, Any]]) -> dict[str, Any]:
    candidate_rows = [by_name[c] for c in CANDIDATE_CONDITIONS if c in by_name]
    if not candidate_rows:
        raise ValueError("Suite C summary requires at least one candidate condition")
    return max(
        candidate_rows,
        key=lambda row: (row["terminal_pass_rate"], row["cost_adjusted_score"]),
    )


def select_headline_condition(rows: list[dict[str, Any]]) -> str:
    by_name = {row["condition"]: row for row in _condition_summaries(rows)}
    return str(_select_headline_candidate(by_name)["condition"])


def summarize_records(rows: list[dict[str, Any]], cfg: SuiteCConfig = DEFAULT_CONFIG) -> dict[str, Any]:
    by_condition = _condition_summaries(rows)
    by_name = {row["condition"]: row for row in by_condition}
    candidate_rows = [by_name[c] for c in CANDIDATE_CONDITIONS if c in by_name]
    headline = _select_headline_candidate(by_name)
    baseline = by_name["p22_learned_current_replay"]
    fixed = by_name["fixed_surprise_decrement"]
    scheduled = by_name["scheduled_null_anchor"]
    oracle = by_name["oracle_source"]
    matched = by_name["matched_random_time_budget"]

    c1 = baseline["affected_post_shift_density"] <= 0.035
    c2 = (
        headline["first_reengagement_ratio"] >= cfg.reengagement_floor
        and headline["first_selectivity_ratio"] >= cfg.selectivity_floor
    )
    c3 = headline["recovery_rate"] >= 0.60
    c4 = headline["no_false_calm_rate"] >= 0.60 and fixed["no_false_calm_rate"] <= 0.34
    c5 = (
        headline["total_probes"] < scheduled["total_probes"]
        and headline["total_probes"] < oracle["total_probes"]
        and headline["final_component_mae"] <= cfg.recovery_threshold
        and matched["first_selectivity_ratio"] < headline["first_selectivity_ratio"]
    )
    c6 = headline["second_reopen_ratio"] >= cfg.reopen_floor
    gates = {
        "C1_silence_replication": {
            "pass": c1,
            "baseline_post_shift_density": baseline["affected_post_shift_density"],
        },
        "C2_reengagement": {
            "pass": c2,
            "headline_condition": headline["condition"],
            "first_reengagement_ratio": headline["first_reengagement_ratio"],
            "first_selectivity_ratio": headline["first_selectivity_ratio"],
        },
        "C3_recovery": {
            "pass": c3,
            "recovery_rate": headline["recovery_rate"],
            "final_component_mae": headline["final_component_mae"],
        },
        "C4_no_false_calm": {
            "pass": c4,
            "headline_no_false_calm_rate": headline["no_false_calm_rate"],
            "fixed_surprise_no_false_calm_rate": fixed["no_false_calm_rate"],
            "fixed_final_component_mae": fixed["final_component_mae"],
        },
        "C5_cost_aware_inquiry": {
            "pass": c5,
            "headline_total_probes": headline["total_probes"],
            "scheduled_total_probes": scheduled["total_probes"],
            "oracle_total_probes": oracle["total_probes"],
            "matched_selectivity_ratio": matched["first_selectivity_ratio"],
        },
        "C6_reopenability": {
            "pass": c6,
            "second_reopen_ratio": headline["second_reopen_ratio"],
        },
    }
    gates["suite_pass"] = {"pass": all(bool(gate["pass"]) for gate in gates.values())}
    ranking = sorted(
        candidate_rows,
        key=lambda row: (row["terminal_pass_rate"], row["cost_adjusted_score"]),
        reverse=True,
    )
    return {
        "n_rows": len(rows),
        "conditions": list(CONDITIONS),
        "candidate_conditions": list(CANDIDATE_CONDITIONS),
        "headline_condition": headline["condition"],
        "by_condition": by_condition,
        "candidate_ranking": ranking,
        "gates": gates,
    }


def run_suite(
    *,
    seeds: list[int] | None = None,
    base_seed: int = 20260706,
    n_seeds: int = 8,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
) -> dict[str, Any]:
    if seeds is None:
        seeds = [base_seed + i * 1_003 for i in range(n_seeds)]
    rows: list[dict[str, Any]] = []
    first_pass_conditions = [c for c in CONDITIONS if c != "matched_random_time_budget"]
    candidate_budgets: dict[str, dict[int, int]] = {condition: {} for condition in CANDIDATE_CONDITIONS}
    for seed in seeds:
        for condition in first_pass_conditions:
            row = run_trial(condition, seed, cfg=cfg)
            rows.append(row)
            if condition in candidate_budgets:
                candidate_budgets[condition][seed] = int(row["total_probes"])
    headline_condition = select_headline_condition(rows)
    headline_budgets = candidate_budgets[headline_condition]
    for seed in seeds:
        rows.append(
            run_trial(
                "matched_random_time_budget",
                seed,
                target_probe_count=headline_budgets[seed],
                cfg=cfg,
            )
        )
    summary = summarize_records(rows, cfg)
    return {
        "kind": "world_responds_suite_c_reengagement",
        "manifest": {
            "suite": "Suite C re-engagement under world change",
            "claim_level": "diagnostic",
            "conditions": list(CONDITIONS),
            "candidate_conditions": list(CANDIDATE_CONDITIONS),
            "seeds": seeds,
            "steps": cfg.steps,
            "first_shift": cfg.first_shift,
            "second_shift": cfg.second_shift,
            "affected_buckets": list(AFFECTED_BUCKETS),
            "unaffected_buckets": list(UNAFFECTED_BUCKETS),
            "matched_budget_source": f"{headline_condition} total probes per seed",
            "matched_budget_condition": headline_condition,
        },
        "rows": rows,
        "summary": summary,
    }


def write_rows_jsonl(payload: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(row, sort_keys=True) for row in payload["rows"]]
    out.write_text("\n".join(lines) + "\n")


def write_summary_json(payload: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload["summary"], indent=2, sort_keys=True) + "\n")
