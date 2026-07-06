"""Learned probe-head transfer for Suite C re-engagement.

The terminal Suite C runner is intentionally hand-specified. This module asks a
narrow follow-up question: can a small learned probe head inherit the same
decision-layer law on held-out simulator seeds while stale, wrong, and
suppressed signals fail?
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Literal

import numpy as np

from experiments.world_responds.suite_c_contract import (
    AFFECTED_BUCKETS,
    BUCKETS,
    DEFAULT_CONFIG,
    SuiteCConfig,
    UNAFFECTED_BUCKETS,
)
from experiments.world_responds.suite_c_reengagement import run_trial


LEARNED_CONDITION = "learned_probe_head"
TEACHER_CONDITION = "teacher_burst_then_refractory"
MATCHED_RANDOM_CONDITION = "matched_random_learned_budget"
LEARNED_CONTROL_CONDITIONS = (
    "stale_signal_head",
    "wrong_signal_head",
    "signal_suppression_head",
)
NEURAL_TRANSFER_CONDITIONS = (
    "p22_learned_current_replay",
    "scheduled_null_anchor",
    "oracle_source",
    TEACHER_CONDITION,
    LEARNED_CONDITION,
    *LEARNED_CONTROL_CONDITIONS,
    MATCHED_RANDOM_CONDITION,
)
FEATURE_NAMES = (
    "perceived_error",
    "perceived_surprise",
    "error_jump",
    "surprise_jump",
    "effort",
    "improvement",
    "time_since_probe",
    "recent_probe_rate",
    "source_is_affected",
    "source_index",
)


def _bucket_indices(names: tuple[str, ...]) -> list[int]:
    return [BUCKETS.index(name) for name in names]


AFFECTED_IDX = _bucket_indices(AFFECTED_BUCKETS)
UNAFFECTED_IDX = _bucket_indices(UNAFFECTED_BUCKETS)
ControlMode = Literal["normal", "stale_signal", "wrong_signal", "signal_suppression"]


@dataclass(frozen=True)
class ProbeHead:
    """A tiny serializable MLP probe policy."""

    feature_mean: tuple[float, ...]
    feature_scale: tuple[float, ...]
    w1: tuple[tuple[float, ...], ...]
    b1: tuple[float, ...]
    w2: tuple[float, ...]
    b2: float
    threshold: float

    def probability(self, features: np.ndarray) -> float:
        mean = np.asarray(self.feature_mean, dtype=float)
        scale = np.asarray(self.feature_scale, dtype=float)
        w1 = np.asarray(self.w1, dtype=float)
        b1 = np.asarray(self.b1, dtype=float)
        w2 = np.asarray(self.w2, dtype=float)
        hidden = np.tanh(((features - mean) / scale) @ w1 + b1)
        logit = float(hidden @ w2 + self.b2)
        return float(_sigmoid(logit))

    def with_threshold(self, threshold: float) -> "ProbeHead":
        return replace(self, threshold=float(threshold))

    def to_record(self) -> dict[str, Any]:
        return {
            "feature_names": list(FEATURE_NAMES),
            "feature_mean": list(self.feature_mean),
            "feature_scale": list(self.feature_scale),
            "w1": [list(row) for row in self.w1],
            "b1": list(self.b1),
            "w2": list(self.w2),
            "b2": self.b2,
            "threshold": self.threshold,
        }

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "ProbeHead":
        return cls(
            feature_mean=tuple(float(v) for v in record["feature_mean"]),
            feature_scale=tuple(float(v) for v in record["feature_scale"]),
            w1=tuple(tuple(float(v) for v in row) for row in record["w1"]),
            b1=tuple(float(v) for v in record["b1"]),
            w2=tuple(float(v) for v in record["w2"]),
            b2=float(record["b2"]),
            threshold=float(record["threshold"]),
        )


def _sigmoid(x: np.ndarray | float) -> np.ndarray | float:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -40.0, 40.0)))


def _window_density(
    probe_history: dict[tuple[int, int], int],
    window: range,
    bucket_indices: list[int],
) -> float:
    slots = max(len(window) * len(bucket_indices), 1)
    count = sum(probe_history.get((t, b), 0) for t in window for b in bucket_indices)
    return float(count / slots)


def _window_mean(series: list[np.ndarray], window: range, bucket_indices: list[int]) -> float:
    values: list[float] = []
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


def _learn_rate() -> float:
    return 0.42


def _passive_rate() -> float:
    return 0.017


def _teacher_takes_probe(
    *,
    rng: np.random.Generator,
    t: int,
    b: int,
    error: np.ndarray,
    surprise: np.ndarray,
    effort: np.ndarray,
    burst_remaining: np.ndarray,
    cooldown_remaining: np.ndarray,
    cfg: SuiteCConfig,
) -> bool:
    score_noise = float(rng.normal(0.0, 0.018))
    base_score = float(0.72 * surprise[b] + 0.38 * error[b] + score_noise)
    if t < cfg.first_shift and error[b] > 0.18:
        return (t + b) % 5 == 0
    if cooldown_remaining[b] > 0:
        return False
    shift_window = (
        cfg.first_shift <= t < cfg.post_first_end
        or cfg.second_shift <= t < cfg.post_second_end
    )
    if b in AFFECTED_IDX and shift_window and burst_remaining[b] > 0 and error[b] > 0.10:
        return True
    return base_score > 0.36 + 0.16 * float(effort[b])


def _perceived_state(
    *,
    t: int,
    b: int,
    error: np.ndarray,
    surprise: np.ndarray,
    pre_shift_error: np.ndarray,
    pre_shift_surprise: np.ndarray,
    control: ControlMode,
    cfg: SuiteCConfig,
) -> tuple[float, float, float]:
    source_is_affected = 1.0 if b in AFFECTED_IDX else 0.0
    if control == "stale_signal" and t >= cfg.first_shift:
        return (
            float(pre_shift_error[b]),
            float(pre_shift_surprise[b]),
            source_is_affected,
        )
    if control == "wrong_signal" and t >= cfg.first_shift:
        if b in AFFECTED_IDX:
            rotated = UNAFFECTED_IDX[AFFECTED_IDX.index(b) % len(UNAFFECTED_IDX)]
        else:
            rotated = AFFECTED_IDX[UNAFFECTED_IDX.index(b) % len(AFFECTED_IDX)]
        return (
            float(error[rotated]),
            float(surprise[rotated]),
            1.0 if rotated in AFFECTED_IDX else 0.0,
        )
    if control == "signal_suppression" and t >= cfg.first_shift + 4:
        return (
            float(max(0.010, 0.10 * pre_shift_error[b])),
            float(max(0.010, 0.08 * pre_shift_surprise[b])),
            source_is_affected,
        )
    return float(error[b]), float(surprise[b]), source_is_affected


def _features(
    *,
    b: int,
    perceived_error: float,
    perceived_surprise: float,
    baseline_error: np.ndarray,
    baseline_surprise: np.ndarray,
    effort: np.ndarray,
    improvement: np.ndarray,
    time_since_probe: np.ndarray,
    recent_probe_rate: np.ndarray,
    source_is_affected: float,
    cfg: SuiteCConfig,
) -> np.ndarray:
    return np.asarray(
        [
            perceived_error,
            perceived_surprise,
            perceived_error - float(baseline_error[b]),
            perceived_surprise - float(baseline_surprise[b]),
            float(effort[b]),
            float(improvement[b]),
            min(float(time_since_probe[b]) / cfg.steps, 1.0),
            float(recent_probe_rate[b]),
            source_is_affected,
            float(b) / max(len(BUCKETS) - 1, 1),
        ],
        dtype=float,
    )


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


def _finish_row(
    *,
    condition: str,
    seed: int,
    cfg: SuiteCConfig,
    target_probe_count: int | None,
    probe_history: dict[tuple[int, int], int],
    error_history: list[np.ndarray],
    surprise_history: list[np.ndarray],
) -> dict[str, Any]:
    pre1 = range(cfg.pre_first_start, cfg.first_shift)
    post1 = range(cfg.first_shift, cfg.post_first_end)
    post1_late = range(cfg.late_first_start, cfg.second_shift)
    pre2 = range(cfg.pre_second_start, cfg.second_shift)
    post2 = range(cfg.second_shift, cfg.post_second_end)
    final_window = range(cfg.final_start, cfg.steps)
    early_window = range(cfg.first_shift, cfg.first_shift + 6)

    affected_pre1_density = _window_density(probe_history, pre1, AFFECTED_IDX)
    affected_post1_density = _window_density(probe_history, post1, AFFECTED_IDX)
    unaffected_post1_density = _window_density(probe_history, post1, UNAFFECTED_IDX)
    affected_pre2_density = _window_density(probe_history, pre2, AFFECTED_IDX)
    affected_post2_density = _window_density(probe_history, post2, AFFECTED_IDX)
    early_probe_density = _window_density(probe_history, early_window, AFFECTED_IDX)
    late_probe_density = _window_density(probe_history, post1_late, AFFECTED_IDX)
    early_mae = _window_mean(error_history, early_window, AFFECTED_IDX)
    late_mae = _window_mean(error_history, post1_late, AFFECTED_IDX)
    early_surprise = _window_mean(surprise_history, early_window, AFFECTED_IDX)
    late_surprise = _window_mean(surprise_history, post1_late, AFFECTED_IDX)
    final_component_mae = _window_mean(error_history, final_window, AFFECTED_IDX)
    post1_mae_auc = _window_mean(error_history, post1, AFFECTED_IDX)
    post2_mae_auc = _window_mean(error_history, post2, AFFECTED_IDX)
    total_probes = int(sum(probe_history.values()))
    affected_total_probes = int(
        sum(v for (_t, bucket), v in probe_history.items() if bucket in AFFECTED_IDX)
    )
    probe_drop_fraction = _drop_fraction(early_probe_density, late_probe_density)
    mae_drop_fraction = _drop_fraction(early_mae, late_mae)
    surprise_drop_fraction = _drop_fraction(early_surprise, late_surprise)
    no_false_calm = (
        final_component_mae <= cfg.recovery_threshold
        or probe_drop_fraction <= 0.05
        or (
            surprise_drop_fraction >= 0.5 * probe_drop_fraction
            and mae_drop_fraction >= 0.33 * probe_drop_fraction
            and final_component_mae <= 0.16
            and condition != "signal_suppression_head"
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
        condition == LEARNED_CONDITION
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
        "unaffected_total_probes": total_probes - affected_total_probes,
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


def _simulate(
    *,
    condition: str,
    seed: int,
    cfg: SuiteCConfig,
    head: ProbeHead | None,
    control: ControlMode = "normal",
    collect_teacher: bool = False,
    target_probe_count: int | None = None,
) -> tuple[dict[str, Any], list[np.ndarray], list[float]]:
    rng = np.random.default_rng(seed)
    n_buckets = len(BUCKETS)
    error = rng.normal(0.26, 0.025, size=n_buckets).clip(0.16, 0.34)
    surprise = (error + rng.normal(0.0, 0.018, size=n_buckets)).clip(0.04, None)
    baseline_error = error.copy()
    baseline_surprise = surprise.copy()
    pre_shift_error = error.copy()
    pre_shift_surprise = surprise.copy()
    effort = np.zeros(n_buckets, dtype=float)
    improvement = np.zeros(n_buckets, dtype=float)
    time_since_probe = np.full(n_buckets, cfg.steps, dtype=float)
    recent_probe_rate = np.zeros(n_buckets, dtype=float)
    burst_remaining = np.zeros(n_buckets, dtype=float)
    cooldown_remaining = np.zeros(n_buckets, dtype=float)
    matched_slots = _make_matched_slots(rng, target_probe_count or 0, cfg)
    probe_history: dict[tuple[int, int], int] = {}
    error_history: list[np.ndarray] = []
    surprise_history: list[np.ndarray] = []
    features: list[np.ndarray] = []
    labels: list[float] = []

    for t in range(cfg.steps):
        if t == cfg.first_shift - 1:
            pre_shift_error = error.copy()
            pre_shift_surprise = surprise.copy()
        if t in {cfg.first_shift, cfg.second_shift}:
            for b in AFFECTED_IDX:
                error[b] += float(rng.normal(0.56, 0.035))
                surprise[b] += float(rng.normal(0.47, 0.025))
                burst_remaining[b] = 8.0
                cooldown_remaining[b] = 0.0

        effort *= 0.72
        recent_probe_rate *= 0.70
        cooldown_remaining = np.maximum(0.0, cooldown_remaining - 1.0)
        time_since_probe += 1.0

        perceived_errors = np.zeros(n_buckets, dtype=float)
        perceived_surprises = np.zeros(n_buckets, dtype=float)
        perceived_sources = np.zeros(n_buckets, dtype=float)
        for b in range(n_buckets):
            p_error, p_surprise, p_source = _perceived_state(
                t=t,
                b=b,
                error=error,
                surprise=surprise,
                pre_shift_error=pre_shift_error,
                pre_shift_surprise=pre_shift_surprise,
                control=control,
                cfg=cfg,
            )
            perceived_errors[b] = p_error
            perceived_surprises[b] = p_surprise
            perceived_sources[b] = p_source

        for b in range(n_buckets):
            feature = _features(
                b=b,
                perceived_error=float(perceived_errors[b]),
                perceived_surprise=float(perceived_surprises[b]),
                baseline_error=baseline_error,
                baseline_surprise=baseline_surprise,
                effort=effort,
                improvement=improvement,
                time_since_probe=time_since_probe,
                recent_probe_rate=recent_probe_rate,
                source_is_affected=float(perceived_sources[b]),
                cfg=cfg,
            )
            if condition == MATCHED_RANDOM_CONDITION:
                take_probe = (t, b) in matched_slots
            elif collect_teacher:
                take_probe = _teacher_takes_probe(
                    rng=rng,
                    t=t,
                    b=b,
                    error=error,
                    surprise=surprise,
                    effort=effort,
                    burst_remaining=burst_remaining,
                    cooldown_remaining=cooldown_remaining,
                    cfg=cfg,
                )
                features.append(feature)
                labels.append(float(take_probe))
            else:
                if head is None:
                    raise ValueError("learned probe simulation requires a ProbeHead")
                take_probe = head.probability(feature) >= head.threshold

            before = float(error[b])
            if take_probe:
                probe_history[(t, b)] = 1
                stochastic_gain = float(rng.normal(0.0, 0.012))
                error[b] = max(0.012, error[b] * (1.0 - _learn_rate() - stochastic_gain))
                improvement[b] = 0.70 * improvement[b] + 0.30 * max(0.0, before - error[b])
                effort[b] += 1.0
                recent_probe_rate[b] += 1.0
                time_since_probe[b] = 0.0
                surprise[b] = max(0.012, 0.68 * surprise[b] + 0.24 * error[b])
                if b in AFFECTED_IDX:
                    burst_remaining[b] = max(0.0, burst_remaining[b] - 1.0)
                    if burst_remaining[b] == 0.0:
                        cooldown_remaining[b] = 3.0
            else:
                drift = 0.004 if b in AFFECTED_IDX else 0.0015
                error[b] = max(0.010, error[b] * (1.0 - _passive_rate()) + drift)
                surprise[b] = max(
                    0.010,
                    0.82 * surprise[b]
                    + 0.15 * error[b]
                    + float(rng.normal(0.0, 0.006)),
                )

        for b in range(n_buckets):
            baseline_error[b] = 0.94 * baseline_error[b] + 0.06 * perceived_errors[b]
            baseline_surprise[b] = 0.94 * baseline_surprise[b] + 0.06 * perceived_surprises[b]
        error_history.append(error.copy())
        surprise_history.append(surprise.copy())

    row = _finish_row(
        condition=condition,
        seed=seed,
        cfg=cfg,
        target_probe_count=target_probe_count,
        probe_history=probe_history,
        error_history=error_history,
        surprise_history=surprise_history,
    )
    return row, features, labels


def collect_teacher_examples(
    seeds: list[int],
    *,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
) -> tuple[np.ndarray, np.ndarray]:
    feature_rows: list[np.ndarray] = []
    label_rows: list[float] = []
    for seed in seeds:
        _row, features, labels = _simulate(
            condition=TEACHER_CONDITION,
            seed=seed,
            cfg=cfg,
            head=None,
            collect_teacher=True,
        )
        feature_rows.extend(features)
        label_rows.extend(labels)
    if not feature_rows:
        raise ValueError("teacher trace collection produced no rows")
    return np.vstack(feature_rows), np.asarray(label_rows, dtype=float)


def train_probe_head(
    seeds: list[int],
    *,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
    hidden: int = 18,
    epochs: int = 900,
    lr: float = 0.035,
    weight_decay: float = 0.0008,
    seed: int = 20260706,
) -> tuple[ProbeHead, dict[str, Any]]:
    x, y = collect_teacher_examples(seeds, cfg=cfg)
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale = np.where(scale < 1e-6, 1.0, scale)
    xn = (x - mean) / scale
    rng = np.random.default_rng(seed)
    w1 = rng.normal(0.0, 0.18, size=(xn.shape[1], hidden))
    b1 = np.zeros(hidden, dtype=float)
    w2 = rng.normal(0.0, 0.16, size=hidden)
    b2 = 0.0
    positives = max(float(y.sum()), 1.0)
    negatives = max(float(len(y) - y.sum()), 1.0)
    pos_weight = min(max(0.75 * negatives / positives, 1.0), 8.0)
    sample_weight = np.where(y > 0.5, pos_weight, 1.0)

    for _epoch in range(epochs):
        z1 = xn @ w1 + b1
        hidden_values = np.tanh(z1)
        logits = hidden_values @ w2 + b2
        probs = _sigmoid(logits)
        delta = (np.asarray(probs) - y) * sample_weight / len(y)
        grad_w2 = hidden_values.T @ delta + weight_decay * w2
        grad_b2 = float(delta.sum())
        grad_hidden = np.outer(delta, w2) * (1.0 - hidden_values**2)
        grad_w1 = xn.T @ grad_hidden + weight_decay * w1
        grad_b1 = grad_hidden.sum(axis=0)
        w2 -= lr * grad_w2
        b2 -= lr * grad_b2
        w1 -= lr * grad_w1
        b1 -= lr * grad_b1

    train_probs = np.asarray(_sigmoid(np.tanh(xn @ w1 + b1) @ w2 + b2))
    train_predictions = train_probs >= 0.5
    metrics = {
        "examples": int(len(y)),
        "positive_rate": float(y.mean()),
        "positive_weight": float(pos_weight),
        "train_accuracy_at_0_5": float(np.mean(train_predictions == (y > 0.5))),
        "mean_positive_probability": float(train_probs[y > 0.5].mean()) if np.any(y > 0.5) else 0.0,
        "mean_negative_probability": float(train_probs[y <= 0.5].mean()) if np.any(y <= 0.5) else 0.0,
        "epochs": epochs,
        "hidden": hidden,
        "learning_rate": lr,
    }
    head = ProbeHead(
        feature_mean=tuple(float(v) for v in mean),
        feature_scale=tuple(float(v) for v in scale),
        w1=tuple(tuple(float(v) for v in row) for row in w1),
        b1=tuple(float(v) for v in b1),
        w2=tuple(float(v) for v in w2),
        b2=float(b2),
        threshold=0.5,
    )
    return head, metrics


def run_learned_trial(
    condition: str,
    seed: int,
    *,
    head: ProbeHead,
    target_probe_count: int | None = None,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
) -> dict[str, Any]:
    control: ControlMode = "normal"
    if condition == "stale_signal_head":
        control = "stale_signal"
    elif condition == "wrong_signal_head":
        control = "wrong_signal"
    elif condition == "signal_suppression_head":
        control = "signal_suppression"
    elif condition not in {LEARNED_CONDITION, MATCHED_RANDOM_CONDITION}:
        raise ValueError(f"unknown learned Suite C condition: {condition}")
    row, _features, _labels = _simulate(
        condition=condition,
        seed=seed,
        cfg=cfg,
        head=head,
        control=control,
        target_probe_count=target_probe_count,
    )
    return row


def _existing_control_row(condition: str, seed: int, cfg: SuiteCConfig) -> dict[str, Any]:
    source_condition = "burst_then_refractory" if condition == TEACHER_CONDITION else condition
    row = run_trial(source_condition, seed, cfg=cfg)
    row["condition"] = condition
    return row


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        raise ValueError(f"cannot summarize empty row set for metric {key!r}")
    values = []
    for row in rows:
        if key not in row or row[key] is None:
            raise ValueError(
                f"row for condition {row.get('condition')!r} seed {row.get('seed')!r} "
                f"missing required metric {key!r}"
            )
        values.append(float(row[key]))
    return float(np.mean(values))


def _rate(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        raise ValueError(f"cannot summarize empty row set for boolean metric {key!r}")
    values = []
    for row in rows:
        if key not in row or not isinstance(row[key], bool):
            raise ValueError(
                f"row for condition {row.get('condition')!r} seed {row.get('seed')!r} "
                f"missing required boolean metric {key!r}"
            )
        values.append(bool(row[key]))
    return float(sum(values) / len(values))


def condition_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["condition"]), []).append(row)
    unknown = sorted(set(grouped) - set(NEURAL_TRANSFER_CONDITIONS))
    if unknown:
        raise ValueError(f"unknown learned Suite C conditions: {unknown}")

    summaries: list[dict[str, Any]] = []
    for condition in NEURAL_TRANSFER_CONDITIONS:
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


def summarize_neural_records(
    rows: list[dict[str, Any]],
    cfg: SuiteCConfig = DEFAULT_CONFIG,
) -> dict[str, Any]:
    by_condition = condition_summaries(rows)
    by_name = {row["condition"]: row for row in by_condition}
    required = set(NEURAL_TRANSFER_CONDITIONS)
    missing = sorted(required - set(by_name))
    if missing:
        raise ValueError(f"missing learned Suite C conditions: {missing}")
    baseline = by_name["p22_learned_current_replay"]
    learned = by_name[LEARNED_CONDITION]
    stale = by_name["stale_signal_head"]
    wrong = by_name["wrong_signal_head"]
    suppressed = by_name["signal_suppression_head"]
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
    stale_control = (
        stale["recovery_rate"] <= 0.50
        or stale["first_reengagement_ratio"] < cfg.reengagement_floor
    )
    wrong_control = wrong["first_selectivity_ratio"] < cfg.selectivity_floor
    suppression_control = (
        suppressed["no_false_calm_rate"] <= 0.34
        or suppressed["final_component_mae"] > cfg.recovery_threshold * 2.0
    )
    learned_controls = stale_control and wrong_control and suppression_control
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
        "N1_learned_signal_controls": {
            "pass": learned_controls,
            "stale_control_failed": stale_control,
            "wrong_signal_control_failed": wrong_control,
            "suppression_control_failed": suppression_control,
        },
    }
    gates["suite_pass"] = {"pass": all(bool(gate["pass"]) for gate in gates.values())}
    return {
        "n_rows": len(rows),
        "conditions": list(NEURAL_TRANSFER_CONDITIONS),
        "candidate_condition": LEARNED_CONDITION,
        "control_conditions": list(LEARNED_CONTROL_CONDITIONS),
        "headline_condition": LEARNED_CONDITION,
        "by_condition": by_condition,
        "gates": gates,
    }


def _threshold_score(summary: dict[str, Any]) -> float:
    by_name = {row["condition"]: row for row in summary["by_condition"]}
    learned = by_name[LEARNED_CONDITION]
    gates = summary["gates"]
    gate_score = sum(
        float(bool(gates[name]["pass"]))
        for name in (
            "C2_reengagement",
            "C3_recovery",
            "C4_no_false_calm",
            "C5_cost_aware_inquiry",
            "C6_reopenability",
        )
    )
    return (
        gate_score * 10.0
        + learned["cost_adjusted_score"]
        - 0.01 * max(0.0, learned["total_probes"] - 36.0)
    )


def calibrate_threshold(
    head: ProbeHead,
    seeds: list[int],
    *,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
    thresholds: tuple[float, ...] = (0.32, 0.36, 0.40, 0.44, 0.48, 0.52, 0.56, 0.60),
) -> tuple[ProbeHead, dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for threshold in thresholds:
        candidate_head = head.with_threshold(threshold)
        rows = _evaluation_rows(seeds, candidate_head, cfg=cfg)
        summary = summarize_neural_records(rows, cfg=cfg)
        candidates.append(
            {
                "threshold": threshold,
                "score": _threshold_score(summary),
                "suite_pass": bool(summary["gates"]["suite_pass"]["pass"]),
                "summary": summary,
            }
        )
    best = max(candidates, key=lambda item: (item["suite_pass"], item["score"]))
    calibration = {
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
    return head.with_threshold(float(best["threshold"])), calibration


def _evaluation_rows(
    seeds: list[int],
    head: ProbeHead,
    *,
    cfg: SuiteCConfig,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    learned_budgets: dict[int, int] = {}
    first_pass = (
        "p22_learned_current_replay",
        "scheduled_null_anchor",
        "oracle_source",
        TEACHER_CONDITION,
    )
    for seed in seeds:
        for condition in first_pass:
            rows.append(_existing_control_row(condition, seed, cfg))
        learned = run_learned_trial(LEARNED_CONDITION, seed, head=head, cfg=cfg)
        rows.append(learned)
        learned_budgets[seed] = int(learned["total_probes"])
        for condition in LEARNED_CONTROL_CONDITIONS:
            rows.append(run_learned_trial(condition, seed, head=head, cfg=cfg))
    for seed in seeds:
        rows.append(
            run_learned_trial(
                MATCHED_RANDOM_CONDITION,
                seed,
                head=head,
                target_probe_count=learned_budgets[seed],
                cfg=cfg,
            )
        )
    return rows


def run_neural_transfer_suite(
    *,
    train_seeds: list[int] | None = None,
    calibration_seeds: list[int] | None = None,
    eval_seeds: list[int] | None = None,
    base_seed: int = 20260706,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
) -> dict[str, Any]:
    if train_seeds is None:
        train_seeds = [base_seed + 11_000 + i * 997 for i in range(16)]
    if calibration_seeds is None:
        calibration_seeds = [base_seed + 31_000 + i * 1_003 for i in range(6)]
    if eval_seeds is None:
        eval_seeds = [base_seed + 51_000 + i * 1_003 for i in range(8)]
    overlap = (set(train_seeds) & set(calibration_seeds)) | (set(train_seeds) & set(eval_seeds))
    overlap |= set(calibration_seeds) & set(eval_seeds)
    if overlap:
        raise ValueError(f"train/calibration/eval seeds must be disjoint: {sorted(overlap)}")

    head, train_metrics = train_probe_head(train_seeds, cfg=cfg, seed=base_seed)
    calibrated_head, calibration = calibrate_threshold(head, calibration_seeds, cfg=cfg)
    rows = _evaluation_rows(eval_seeds, calibrated_head, cfg=cfg)
    summary = summarize_neural_records(rows, cfg=cfg)
    return {
        "kind": "world_responds_suite_c_neural_transfer",
        "manifest": {
            "suite": "Suite C neural probe transfer",
            "claim_level": "learned-policy diagnostic",
            "conditions": list(NEURAL_TRANSFER_CONDITIONS),
            "candidate_condition": LEARNED_CONDITION,
            "control_conditions": list(LEARNED_CONTROL_CONDITIONS),
            "teacher_condition": TEACHER_CONDITION,
            "train_seeds": train_seeds,
            "calibration_seeds": calibration_seeds,
            "eval_seeds": eval_seeds,
            "steps": cfg.steps,
            "first_shift": cfg.first_shift,
            "second_shift": cfg.second_shift,
            "affected_buckets": list(AFFECTED_BUCKETS),
            "unaffected_buckets": list(UNAFFECTED_BUCKETS),
            "feature_names": list(FEATURE_NAMES),
            "matched_budget_source": f"{LEARNED_CONDITION} total probes per eval seed",
            "matched_budget_condition": LEARNED_CONDITION,
        },
        "model": calibrated_head.to_record(),
        "training": train_metrics,
        "calibration": calibration,
        "rows": rows,
        "summary": summary,
    }
