"""M5 trigger-only Suite C reopen/reset comparison.

The implementation follows the pre-run repair contract frozen on 2026-07-14.
It intentionally keeps raw trigger/probe traces in the ignored payload while
publishing only aggregate summaries.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from experiments.world_responds.suite_c_contract import (
    AFFECTED_BUCKETS,
    BUCKETS,
    DEFAULT_CONFIG,
    UNAFFECTED_BUCKETS,
    SuiteCConfig,
    SuiteCMechanisms,
)
from experiments.world_responds.suite_c_factorial_ablation import (
    _reference_control_gate,
)
from experiments.world_responds.suite_c_reengagement import (
    AFFECTED_IDX,
    UNAFFECTED_IDX,
    _condition_takes_probe,
    _drop_fraction,
    _learn_rate,
    _make_matched_slots,
    _passive_rate,
    _safe_ratio,
    _window_density,
    _window_mean,
    run_suite,
    run_trial,
)


ARMS = ("T_commit", "T_util", "T_norm", "T_periodic", "T_none")
INTERNAL_ARMS = ("T_util", "T_norm", "T_periodic")
DEFAULT_SEEDS = (
    20260709,
    20261712,
    20262715,
    20263718,
    20264721,
    20265724,
    20266727,
    20267730,
)
BOOTSTRAP_SAMPLES = 10_000
BOOTSTRAP_SEED = 20260713
PERIODIC_TRIGGER_PERIOD = 24
OPEN_DURATION = 8
SOURCE_REVISION = "9e5e218a2efbcd726d0d9555d34c2292e886f72a"
SOURCE_CONDITION = "burst_then_refractory__allocate_0_cool_0_reopen_1"
FROZEN_CALIBRATION_RECEIPT_SHA256 = (
    "741efa930978a0de622b4fbea4deed82e250535b0b0b37ecaf3f9043136d992b"
)
FROZEN_CALIBRATION_FILE_SHA256 = (
    "7e62142b8a8efdd57176c6d5255ee6439941d951b4d9a5a20825d9198c3d58b9"
)
INTEGRITY_FLOAT_DECIMALS = 12
FROZEN_INTEGRITY_MANIFEST_SHA256 = (
    "15db53ff84127acac2738b0102f2e8ad6af8f2ae51d5fff2b752b64620950d92"
)
INVALIDATED_RAW_PAYLOAD_SHA256 = (
    "cf6f640da6d2b37154d0371255730f9f8d28a39a2cad63de61826f4dd02818c1",
    "bd94aedab53b51d0a67668efeaca0ca610a9b0cbbf45459f341813c862bfb0e0",
)
SUPERSEDED_PORTABILITY_RAW_PAYLOAD_SHA256 = (
    "ec666ddb098579897974765c2f5431e0a0c636092f928f63102be85cca2899cc",
)
PREREGISTRATION = Path(
    "experiments/world_responds/"
    "suite_c_reopen_reset_trigger_preregistration_2026-07-13.md"
)
IMPLEMENTATION_CONTRACT = Path(
    "experiments/world_responds/"
    "suite_c_reopen_reset_trigger_implementation_contract_2026-07-14.md"
)
CALIBRATION_RECEIPT = Path(
    "experiments/world_responds/"
    "suite_c_reopen_reset_trigger_calibration_2026_07_14.json"
)
INTEGRITY_MANIFEST = Path(
    "experiments/world_responds/"
    "suite_c_reopen_reset_trigger_integrity_manifest_2026_07_14.json"
)
RAW_PAYLOAD = Path(
    "artifacts/world_responds/m5_suite_c_reopen_reset_trigger_2026_07_14.json"
)
PUBLIC_SUMMARY_JSON = Path(
    "experiments/commitment_surface/results/"
    "m5_suite_c_reopen_reset_trigger_2026_07_14.json"
)
PUBLIC_SUMMARY_MD = Path(
    "experiments/commitment_surface/results/"
    "m5_suite_c_reopen_reset_trigger_2026_07_14.md"
)
M5_MECHANISMS = SuiteCMechanisms(allocate=False, cool=False, reopen=True)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _canonicalize_for_integrity(value: Any) -> Any:
    """Normalize sub-precision float noise before cross-platform hashing."""

    if isinstance(value, (float, np.floating)):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("integrity payloads require finite floats")
        rounded = round(number, INTEGRITY_FLOAT_DECIMALS)
        return 0.0 if rounded == 0.0 else rounded
    if isinstance(value, dict):
        return {key: _canonicalize_for_integrity(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonicalize_for_integrity(item) for item in value]
    return value


def _integrity_sha256(value: Any) -> str:
    return _sha256(_canonicalize_for_integrity(value))


def _calibration_receipt_is_valid(calibration: dict[str, Any]) -> bool:
    core = {key: value for key, value in calibration.items() if key != "receipt_sha256"}
    return bool(
        calibration.get("receipt_sha256") == _sha256(core)
        and calibration.get("receipt_sha256") == FROZEN_CALIBRATION_RECEIPT_SHA256
        and calibration.get("source_revision") == SOURCE_REVISION
        and calibration.get("source_condition") == SOURCE_CONDITION
        and tuple(calibration.get("seeds", ())) == DEFAULT_SEEDS
    )


def _integrity_manifest_is_valid(
    rows: list[dict[str, Any]],
    reference_suite: dict[str, Any],
    calibration: dict[str, Any],
    seeds: tuple[int, ...],
    cfg: SuiteCConfig,
) -> bool:
    try:
        manifest = json.loads(INTEGRITY_MANIFEST.read_text())
    except (OSError, json.JSONDecodeError):
        return False
    observed_plans: dict[str, dict[str, Any]] = {}
    for seed in seeds:
        seed_rows = [row for row in rows if int(row["seed"]) == seed]
        plan_ids = {str(row["plan_id"]) for row in seed_rows}
        budgets = {int(row["probe_budget"]) for row in seed_rows}
        if len(plan_ids) != 1 or len(budgets) != 1:
            return False
        observed_plans[str(seed)] = {
            "plan_id": plan_ids.pop(),
            "budget": budgets.pop(),
        }
    rows_sorted = sorted(rows, key=lambda row: (int(row["seed"]), str(row["arm"])))
    return bool(
        _sha256(manifest) == FROZEN_INTEGRITY_MANIFEST_SHA256
        and manifest.get("hash_canonicalization")
        == {
            "float_decimals": INTEGRITY_FLOAT_DECIMALS,
            "row_digest": "exact-json-v1",
            "semantic_scopes": ["random_schedule", "reference_suite"],
            "version": "json-rounded-v1",
        }
        and manifest.get("source_revision") == SOURCE_REVISION
        and manifest.get("seeds") == list(seeds)
        and manifest.get("config") == asdict(cfg)
        and manifest.get("calibration_receipt_sha256")
        == calibration.get("receipt_sha256")
        and manifest.get("probe_plans") == observed_plans
        and manifest.get("reference_suite_sha256")
        == _integrity_sha256(reference_suite)
        and manifest.get("rows_sha256") == _sha256(rows_sorted)
    )


def _subseed(seed: int, arm: str, stream: str) -> int:
    payload = f"{seed}:{arm}:{stream}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _closed_fallback(seed: int, step: int, bucket: str) -> str:
    payload = f"{seed}:m5:closed-fallback:{step}:{bucket}".encode()
    index = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return UNAFFECTED_BUCKETS[index % len(UNAFFECTED_BUCKETS)]


def build_probe_plan(seed: int, cfg: SuiteCConfig = DEFAULT_CONFIG) -> dict[str, Any]:
    """Freeze the common actual-probe plan from the immutable M4 cell."""

    reference = run_trial(
        "burst_then_refractory",
        int(seed),
        cfg=cfg,
        mechanisms=M5_MECHANISMS,
        include_probe_trace=True,
    )
    raw_slots = list(reference["probe_trace"])
    slots = [
        {
            "step": int(slot["step"]),
            "reference_bucket": str(slot["bucket"]),
            "closed_fallback": _closed_fallback(
                int(seed), int(slot["step"]), str(slot["bucket"])
            ),
        }
        for slot in raw_slots
    ]
    core = {
        "seed": int(seed),
        "source_revision": SOURCE_REVISION,
        "source_condition": SOURCE_CONDITION,
        "budget": int(reference["total_probes"]),
        "slots": slots,
    }
    if len(slots) != core["budget"]:
        raise RuntimeError("M4 probe trace does not match its actual probe budget")
    return {**core, "plan_id": _sha256(core)}


def _initial_reference_state(
    seed: int, cfg: SuiteCConfig
) -> tuple[np.random.Generator, dict[str, Any]]:
    rng = np.random.default_rng(seed)
    n_buckets = len(BUCKETS)
    error = rng.normal(0.26, 0.025, size=n_buckets).clip(0.16, 0.34)
    surprise = (error + rng.normal(0.0, 0.018, size=n_buckets)).clip(0.04, None)
    state: dict[str, Any] = {
        "error": error,
        "surprise": surprise,
        "effort": np.zeros(n_buckets, dtype=float),
        "improvement": np.zeros(n_buckets, dtype=float),
        "burst": np.zeros(n_buckets, dtype=float),
        "cooldown": np.zeros(n_buckets, dtype=float),
        "matched_slots": _make_matched_slots(rng, 58, cfg),
        "utility": np.zeros(n_buckets, dtype=float),
        "age": np.zeros(n_buckets, dtype=float),
    }
    return rng, state


def _advance_reference_calibration_step(
    rng: np.random.Generator,
    state: dict[str, Any],
    t: int,
    cfg: SuiteCConfig,
) -> None:
    error = state["error"]
    surprise = state["surprise"]
    effort = state["effort"]
    improvement = state["improvement"]
    burst = state["burst"]
    cooldown = state["cooldown"]
    utility = state["utility"]
    age = state["age"]
    effort *= 0.72
    cooldown[:] = np.maximum(0.0, cooldown - 1.0)

    for b in range(len(BUCKETS)):
        take_probe = _condition_takes_probe(
            condition="burst_then_refractory",
            rng=rng,
            t=t,
            b=b,
            error=error,
            surprise=surprise,
            effort=effort,
            improvement=improvement,
            burst_remaining=burst,
            cooldown_remaining=cooldown,
            matched_slots=state["matched_slots"],
            cfg=cfg,
            mechanisms=M5_MECHANISMS,
        )
        before = float(error[b])
        if take_probe:
            stochastic_gain = float(rng.normal(0.0, 0.012))
            error[b] = max(
                0.012,
                error[b]
                * (1.0 - _learn_rate("burst_then_refractory") - stochastic_gain),
            )
            gain = max(0.0, before - float(error[b]))
            improvement[b] = 0.70 * improvement[b] + 0.30 * gain
            effort[b] += 1.0
            surprise[b] = max(0.012, 0.68 * surprise[b] + 0.24 * error[b])
            q = gain / max(before, 1e-12)
            utility[b] = 0.95 * utility[b] + 0.05 * q
            age[b] = 0.0
        else:
            drift = 0.004 if b in AFFECTED_IDX else 0.0015
            error[b] = max(
                0.010,
                error[b] * (1.0 - _passive_rate("burst_then_refractory")) + drift,
            )
            surprise[b] = max(
                0.010,
                0.82 * surprise[b] + 0.15 * error[b] + float(rng.normal(0.0, 0.006)),
            )
            utility[b] *= 0.95
            age[b] += 1.0


def calibrate_trigger_thresholds(
    seeds: Iterable[int] = DEFAULT_SEEDS,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
) -> dict[str, Any]:
    """Fit the frozen internal-trigger thresholds without observing a shift."""

    seed_tuple = tuple(int(seed) for seed in seeds)
    if not seed_tuple or len(set(seed_tuple)) != len(seed_tuple):
        raise ValueError("calibration seeds must be non-empty and unique")
    snapshots: list[dict[str, Any]] = []
    activation_values: dict[int, list[float]] = defaultdict(list)
    maximum_utility = 0.0
    for seed in seed_tuple:
        rng, state = _initial_reference_state(seed, cfg)
        for t in range(cfg.first_shift):
            if cfg.pre_first_start <= t < cfg.first_shift:
                activation = 0.72 * state["surprise"] + 0.38 * state["error"]
                snapshots.append(
                    {
                        "seed": seed,
                        "step": t,
                        "activation": activation.copy(),
                        "utility": state["utility"].copy(),
                        "age": state["age"].copy(),
                    }
                )
                for b, value in enumerate(activation):
                    activation_values[b].append(float(value))
                maximum_utility = max(maximum_utility, float(np.max(state["utility"])))
            _advance_reference_calibration_step(rng, state, t, cfg)

    u_scale = max(maximum_utility, 1e-12)
    medians = np.array(
        [np.median(activation_values[b]) for b in range(len(BUCKETS))],
        dtype=float,
    )
    scales = np.array(
        [
            max(
                1e-6,
                1.4826
                * float(
                    np.median(
                        np.abs(
                            np.asarray(activation_values[b], dtype=float) - medians[b]
                        )
                    )
                ),
            )
            for b in range(len(BUCKETS))
        ],
        dtype=float,
    )
    util_scores = [
        float(np.max(row["age"] * (1.0 - row["utility"] / u_scale)))
        for row in snapshots
    ]
    norm_scores = [
        float(np.max(np.abs(row["activation"] - medians) / scales)) for row in snapshots
    ]
    max_scores = {
        "T_util": max(util_scores),
        "T_norm": max(norm_scores),
    }
    thresholds = {
        name: float(np.nextafter(value, math.inf)) for name, value in max_scores.items()
    }
    core = {
        "kind": "m5_suite_c_trigger_calibration",
        "source": "m4_full_on_reference_pre_first_shift",
        "source_revision": SOURCE_REVISION,
        "source_condition": SOURCE_CONDITION,
        "seeds": list(seed_tuple),
        "window": [cfg.pre_first_start, cfg.first_shift - 1],
        "utility_scale": u_scale,
        "norm_medians": medians.tolist(),
        "norm_scales": scales.tolist(),
        "max_scores": max_scores,
        "thresholds": thresholds,
    }
    return {**core, "receipt_sha256": _sha256(core)}


def _trigger_score(
    arm: str,
    state: dict[str, Any],
    calibration: dict[str, Any],
    norm_medians: np.ndarray,
    norm_scales: np.ndarray,
) -> float:
    if arm == "T_util":
        scale = float(calibration["utility_scale"])
        return float(np.max(state["age"] * (1.0 - state["utility"] / scale)))
    if arm == "T_norm":
        activation = 0.72 * state["surprise"] + 0.38 * state["error"]
        return float(np.max(np.abs(activation - norm_medians) / norm_scales))
    return 0.0


def _trigger_fires(
    arm: str,
    t: int,
    *,
    real_second_shift: bool,
    score: float,
    previous_score: float,
    calibration: dict[str, Any],
    cfg: SuiteCConfig,
) -> bool:
    if arm == "T_commit":
        return bool(t == cfg.second_shift and real_second_shift)
    if arm == "T_periodic":
        return bool(t > 0 and t % PERIODIC_TRIGGER_PERIOD == 0)
    if arm == "T_none":
        return False
    threshold = float(calibration["thresholds"][arm])
    return bool(t > cfg.first_shift and score > threshold >= previous_score)


def _route_tokens(slots: list[dict[str, Any]], *, commitment_open: bool) -> list[str]:
    routed = []
    for slot in slots:
        bucket = str(slot["reference_bucket"])
        if bucket in AFFECTED_BUCKETS and not commitment_open:
            bucket = str(slot["closed_fallback"])
        routed.append(bucket)
    return routed


def _random_schedule(
    seed: int,
    arm: str,
    plan: dict[str, Any],
    cfg: SuiteCConfig,
) -> dict[str, Any]:
    """Pre-index all variates so outcome/no-change branches stay coupled."""

    initial_rng = np.random.default_rng(_subseed(seed, arm, "initial"))
    shift_rng = np.random.default_rng(_subseed(seed, arm, "shift"))
    dynamics_rng = np.random.default_rng(_subseed(seed, arm, "dynamics"))
    initial_error = initial_rng.normal(0.26, 0.025, size=len(BUCKETS)).clip(0.16, 0.34)
    initial_surprise = (
        initial_error + initial_rng.normal(0.0, 0.018, size=len(BUCKETS))
    ).clip(0.04, None)
    shift_error = shift_rng.normal(0.56, 0.035, size=(2, len(AFFECTED_IDX)))
    shift_surprise = shift_rng.normal(0.47, 0.025, size=(2, len(AFFECTED_IDX)))
    probe_noise = dynamics_rng.normal(0.0, 0.012, size=len(plan["slots"]))
    drift_noise = dynamics_rng.normal(0.0, 0.006, size=(cfg.steps, len(BUCKETS)))
    core = {
        "initial_error": initial_error.tolist(),
        "initial_surprise": initial_surprise.tolist(),
        "shift_error": shift_error.tolist(),
        "shift_surprise": shift_surprise.tolist(),
        "probe_noise": probe_noise.tolist(),
        "drift_noise": drift_noise.tolist(),
    }
    return {**core, "schedule_id": _integrity_sha256(core)}


def _simulate_arm(
    seed: int,
    arm: str,
    plan: dict[str, Any],
    calibration: dict[str, Any],
    *,
    apply_second_shift: bool,
    cfg: SuiteCConfig,
) -> dict[str, Any]:
    if arm not in ARMS:
        raise ValueError(f"unknown M5 arm {arm!r}")
    schedule = _random_schedule(seed, arm, plan, cfg)
    n_buckets = len(BUCKETS)
    error = np.asarray(schedule["initial_error"], dtype=float)
    surprise = np.asarray(schedule["initial_surprise"], dtype=float)
    effort = np.zeros(n_buckets, dtype=float)
    improvement = np.zeros(n_buckets, dtype=float)
    utility = np.zeros(n_buckets, dtype=float)
    age = np.zeros(n_buckets, dtype=float)
    state = {
        "error": error,
        "surprise": surprise,
        "utility": utility,
        "age": age,
    }
    norm_medians = np.asarray(calibration["norm_medians"], dtype=float)
    norm_scales = np.asarray(calibration["norm_scales"], dtype=float)
    slots_by_step: dict[int, list[tuple[dict[str, Any], float]]] = defaultdict(list)
    for slot, noise in zip(plan["slots"], schedule["probe_noise"], strict=True):
        slots_by_step[int(slot["step"])].append((slot, float(noise)))
    probe_history: dict[tuple[int, int], int] = {}
    probe_trace: list[dict[str, Any]] = []
    error_history: list[np.ndarray] = []
    surprise_history: list[np.ndarray] = []
    trigger_events: list[int] = []
    open_steps: list[int] = []
    open_through = -1
    previous_score = _trigger_score(arm, state, calibration, norm_medians, norm_scales)

    for t in range(cfg.steps):
        real_second_shift = bool(t == cfg.second_shift and apply_second_shift)
        if t in {cfg.first_shift, cfg.second_shift}:
            shift_index = 0 if t == cfg.first_shift else 1
            for affected_index, b in enumerate(AFFECTED_IDX):
                error_jump = float(schedule["shift_error"][shift_index][affected_index])
                surprise_jump = float(
                    schedule["shift_surprise"][shift_index][affected_index]
                )
                if t == cfg.first_shift or real_second_shift:
                    error[b] += error_jump
                    surprise[b] += surprise_jump
        if t == cfg.first_shift:
            open_through = t + OPEN_DURATION - 1

        score = _trigger_score(arm, state, calibration, norm_medians, norm_scales)
        fires = _trigger_fires(
            arm,
            t,
            real_second_shift=real_second_shift,
            score=score,
            previous_score=previous_score,
            calibration=calibration,
            cfg=cfg,
        )
        if fires and t > open_through:
            open_through = t + OPEN_DURATION - 1
            trigger_events.append(t)
        commitment_open = t <= open_through
        if commitment_open:
            open_steps.append(t)
        previous_score = score

        effort *= 0.72
        step_slots = slots_by_step.get(t, [])
        routed = _route_tokens(
            [slot for slot, _ in step_slots], commitment_open=commitment_open
        )
        probe_noise_by_bucket: dict[str, list[float]] = defaultdict(list)
        for bucket, (_, noise) in zip(routed, step_slots, strict=True):
            probe_noise_by_bucket[bucket].append(noise)
        for b, bucket in enumerate(BUCKETS):
            bucket_noises = probe_noise_by_bucket.get(bucket, [])
            if bucket_noises:
                for stochastic_gain in bucket_noises:
                    before = float(error[b])
                    error[b] = max(
                        0.012,
                        error[b]
                        * (
                            1.0 - _learn_rate("burst_then_refractory") - stochastic_gain
                        ),
                    )
                    gain = max(0.0, before - float(error[b]))
                    improvement[b] = 0.70 * improvement[b] + 0.30 * gain
                    effort[b] += 1.0
                    surprise[b] = max(0.012, 0.68 * surprise[b] + 0.24 * error[b])
                    utility[b] = 0.95 * utility[b] + 0.05 * (gain / max(before, 1e-12))
                    age[b] = 0.0
                    probe_history[(t, b)] = probe_history.get((t, b), 0) + 1
                    probe_trace.append(
                        {
                            "step": t,
                            "bucket": bucket,
                            "commitment_open": commitment_open,
                        }
                    )
            else:
                drift = 0.004 if b in AFFECTED_IDX else 0.0015
                error[b] = max(
                    0.010,
                    error[b] * (1.0 - _passive_rate("burst_then_refractory")) + drift,
                )
                surprise[b] = max(
                    0.010,
                    0.82 * surprise[b]
                    + 0.15 * error[b]
                    + float(schedule["drift_noise"][t][b]),
                )
                utility[b] *= 0.95
                age[b] += 1.0
        error_history.append(error.copy())
        surprise_history.append(surprise.copy())

    pre1 = range(cfg.pre_first_start, cfg.first_shift)
    post1 = range(cfg.first_shift, cfg.post_first_end)
    post1_late = range(cfg.late_first_start, cfg.second_shift)
    pre2 = range(cfg.pre_second_start, cfg.second_shift)
    post2 = range(cfg.second_shift, cfg.post_second_end)
    final_window = range(cfg.final_start, cfg.steps)
    affected_pre1 = _window_density(probe_history, pre1, AFFECTED_IDX)
    affected_post1 = _window_density(probe_history, post1, AFFECTED_IDX)
    unaffected_post1 = _window_density(probe_history, post1, UNAFFECTED_IDX)
    affected_pre2 = _window_density(probe_history, pre2, AFFECTED_IDX)
    affected_post2 = _window_density(probe_history, post2, AFFECTED_IDX)
    early_density = _window_density(
        probe_history, range(cfg.first_shift, cfg.first_shift + 6), AFFECTED_IDX
    )
    late_density = _window_density(probe_history, post1_late, AFFECTED_IDX)
    early_mae = _window_mean(
        error_history, range(cfg.first_shift, cfg.first_shift + 6), AFFECTED_IDX
    )
    late_mae = _window_mean(error_history, post1_late, AFFECTED_IDX)
    early_surprise = _window_mean(
        surprise_history,
        range(cfg.first_shift, cfg.first_shift + 6),
        AFFECTED_IDX,
    )
    late_surprise = _window_mean(surprise_history, post1_late, AFFECTED_IDX)
    final_mae = _window_mean(error_history, final_window, AFFECTED_IDX)
    probe_drop = _drop_fraction(early_density, late_density)
    mae_drop = _drop_fraction(early_mae, late_mae)
    surprise_drop = _drop_fraction(early_surprise, late_surprise)
    no_false_calm = bool(
        final_mae <= cfg.recovery_threshold
        or probe_drop <= 0.05
        or (
            surprise_drop >= 0.5 * probe_drop
            and mae_drop >= 0.33 * probe_drop
            and final_mae <= 0.16
        )
    )
    reengagement_ratio = _safe_ratio(affected_post1, affected_pre1)
    selectivity = _safe_ratio(affected_post1, unaffected_post1)
    reopen_ratio = _safe_ratio(affected_post2, affected_pre2)
    recovery_pass = final_mae <= cfg.recovery_threshold
    reengagement_pass = bool(
        reengagement_ratio >= cfg.reengagement_floor
        and selectivity >= cfg.selectivity_floor
    )
    reopen_pass = reopen_ratio >= cfg.reopen_floor
    terminal_pass = bool(
        reengagement_pass and recovery_pass and no_false_calm and reopen_pass
    )
    affected_post2_steps = sorted(
        {
            int(item["step"])
            for item in probe_trace
            if item["bucket"] in AFFECTED_BUCKETS
            and cfg.second_shift <= int(item["step"]) < cfg.post_second_end
        }
    )
    latency = (
        affected_post2_steps[0] - cfg.second_shift
        if affected_post2_steps
        else cfg.post_second_end - cfg.second_shift
    )
    return {
        "seed": int(seed),
        "arm": arm,
        "scenario": "outcome" if apply_second_shift else "false_calm",
        "plan_id": plan["plan_id"],
        "probe_budget": int(plan["budget"]),
        "total_probes": len(probe_trace),
        "affected_post_second_probes": sum(
            1
            for item in probe_trace
            if item["bucket"] in AFFECTED_BUCKETS
            and cfg.second_shift <= int(item["step"]) < cfg.post_second_end
        ),
        "latency": int(latency),
        "selectivity": float(selectivity),
        "reopen_ratio": float(reopen_ratio),
        "final_mae": float(final_mae),
        "reengagement_ratio": float(reengagement_ratio),
        "no_false_calm": no_false_calm,
        "recovery_pass": bool(recovery_pass),
        "reengagement_pass": reengagement_pass,
        "reopen_pass": bool(reopen_pass),
        "terminal_pass": terminal_pass,
        "trigger_events": trigger_events,
        "open_steps": open_steps,
        "probe_trace": probe_trace,
        "random_schedule_id": schedule["schedule_id"],
    }


def run_m5_trial(
    seed: int,
    arm: str,
    calibration: dict[str, Any],
    cfg: SuiteCConfig = DEFAULT_CONFIG,
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if plan is None:
        plan = build_probe_plan(seed, cfg)
    outcome = _simulate_arm(
        seed,
        arm,
        plan,
        calibration,
        apply_second_shift=True,
        cfg=cfg,
    )
    false_calm = _simulate_arm(
        seed,
        arm,
        plan,
        calibration,
        apply_second_shift=False,
        cfg=cfg,
    )
    if outcome["random_schedule_id"] != false_calm["random_schedule_id"]:
        raise RuntimeError("outcome and false-calm runs lost their random coupling")
    window = set(range(cfg.second_shift, cfg.post_second_end))
    false_open = len(window.intersection(false_calm["open_steps"]))
    outcome["false_reopen_rate"] = float(false_open / len(window))
    outcome["false_calm_trigger_events"] = false_calm["trigger_events"]
    outcome["false_calm_open_steps"] = sorted(
        window.intersection(false_calm["open_steps"])
    )
    outcome["false_calm_probe_trace"] = false_calm["probe_trace"]
    outcome["false_calm_random_schedule_id"] = false_calm["random_schedule_id"]
    outcome["coupled_random_schedule"] = True
    return outcome


def _bootstrap_summary(
    rows: list[dict[str, Any]], seeds: tuple[int, ...]
) -> list[dict[str, Any]]:
    by_arm_seed = {(row["arm"], int(row["seed"])): row for row in rows}
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    indices = rng.integers(0, len(seeds), size=(BOOTSTRAP_SAMPLES, len(seeds)))
    metrics = {
        "terminal_pass_rate": ("terminal_pass", np.mean),
        "latency": ("latency", np.median),
        "selectivity": ("selectivity", np.mean),
        "reopen_ratio": ("reopen_ratio", np.mean),
        "final_mae": ("final_mae", np.mean),
        "probe_cost": ("total_probes", np.mean),
        "false_reopen_rate": ("false_reopen_rate", np.mean),
    }
    summaries = []
    for arm in ARMS:
        item: dict[str, Any] = {"arm": arm}
        for public_name, (row_name, reduce) in metrics.items():
            values = np.asarray(
                [float(by_arm_seed[(arm, seed)][row_name]) for seed in seeds]
            )
            point = float(reduce(values))
            samples = reduce(values[indices], axis=1)
            item[public_name] = {
                "point": point,
                "ci95_low": float(np.percentile(samples, 2.5)),
                "ci95_high": float(np.percentile(samples, 97.5)),
            }
        summaries.append(item)
    return summaries


def evaluate_gates(
    rows: list[dict[str, Any]],
    reference_suite: dict[str, Any],
    seeds: Iterable[int],
    calibration: dict[str, Any],
    *,
    deterministic_replay: bool,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
) -> dict[str, Any]:
    seed_tuple = tuple(int(seed) for seed in seeds)
    expected = {(seed, arm) for seed in seed_tuple for arm in ARMS}
    observed = {(int(row["seed"]), str(row["arm"])) for row in rows}
    complete_grid = observed == expected and len(rows) == len(expected)
    frozen_seed_grid = seed_tuple == DEFAULT_SEEDS
    frozen_config = cfg == DEFAULT_CONFIG
    by_seed: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_seed[int(row["seed"])].append(row)
    matched_actual = all(
        len({int(row["total_probes"]) for row in seed_rows}) == 1
        and all(
            int(row["total_probes"]) == int(row["probe_budget"]) for row in seed_rows
        )
        and len({str(row["plan_id"]) for row in seed_rows}) == 1
        for seed_rows in by_seed.values()
    )
    coupled_random_schedule = all(
        bool(row.get("coupled_random_schedule"))
        and row.get("random_schedule_id") == row.get("false_calm_random_schedule_id")
        for row in rows
    )
    integrity_manifest_valid = _integrity_manifest_is_valid(
        rows, reference_suite, calibration, seed_tuple, cfg
    )
    transported, transported_checks = _reference_control_gate(reference_suite)
    calibration_valid = _calibration_receipt_is_valid(calibration)
    f0 = bool(
        complete_grid
        and frozen_seed_grid
        and frozen_config
        and matched_actual
        and coupled_random_schedule
        and integrity_manifest_valid
        and transported
        and deterministic_replay
        and calibration_valid
    )
    f0_gate = {
        "pass": f0,
        "complete_grid": complete_grid,
        "frozen_seed_grid": frozen_seed_grid,
        "frozen_config": frozen_config,
        "matched_actual_probes": matched_actual,
        "coupled_random_schedule": coupled_random_schedule,
        "integrity_manifest_valid": integrity_manifest_valid,
        "transported_controls_pass": transported,
        "transported_controls": transported_checks,
        "deterministic_replay": deterministic_replay,
        "calibration_receipt_valid": calibration_valid,
    }
    if not complete_grid:
        not_evaluated = {
            "pass": False,
            "evaluated": False,
            "reason": "not evaluated because the F0 arm/seed grid is incomplete",
        }
        gates = {
            "F0_integrity": f0_gate,
            "F1_commit_8_of_8": dict(not_evaluated),
            "F2_latency_dominance": dict(not_evaluated),
            "F3_specificity": dict(not_evaluated),
            "F4_joint_non_domination": dict(not_evaluated),
            "F5_none_floor": dict(not_evaluated),
        }
        return {
            "kind": "m5_suite_c_reopen_reset_trigger_summary",
            "strict_verdict": "FAIL",
            "claim_level": "failed diagnostic gate; trigger superiority remains a hypothesis",
            "seeds": list(seed_tuple),
            "arms": list(ARMS),
            "n_rows": len(rows),
            "calibration": calibration,
            "arm_summaries": [],
            "gates": gates,
            "preregistration_repair": str(IMPLEMENTATION_CONTRACT),
            "rejected_alternatives": [
                "post-outcome trigger threshold tuning",
                "unequal actual probe counts",
                "filler probes into closed affected buckets",
                "impulse-count false-reopen metric",
                "aggregate-only unpaired contrasts",
            ],
        }
    lookup = {(int(row["seed"]), str(row["arm"])): row for row in rows}
    commit_rows = [lookup[(seed, "T_commit")] for seed in seed_tuple]
    f1 = all(bool(row["terminal_pass"]) for row in commit_rows)
    latency_contrasts: dict[str, dict[str, Any]] = {}
    for arm in INTERNAL_ARMS:
        deltas = [
            int(lookup[(seed, arm)]["latency"])
            - int(lookup[(seed, "T_commit")]["latency"])
            for seed in seed_tuple
        ]
        median_delta = float(np.median(deltas))
        latency_contrasts[arm] = {
            "paired_deltas": deltas,
            "median_internal_minus_commit": median_delta,
            "pass": bool(median_delta >= 1.0),
        }
    f2 = all(item["pass"] for item in latency_contrasts.values())
    specificity: dict[str, dict[str, Any]] = {}
    commit_false = float(
        np.mean([float(row["false_reopen_rate"]) for row in commit_rows])
    )
    for arm in INTERNAL_ARMS:
        internal_false = float(
            np.mean(
                [float(lookup[(seed, arm)]["false_reopen_rate"]) for seed in seed_tuple]
            )
        )
        margin = internal_false - commit_false
        specificity[arm] = {
            "commit": commit_false,
            "internal": internal_false,
            "internal_minus_commit": margin,
            "pass": bool(margin >= 0.10 and internal_false > commit_false),
        }
    f3 = all(item["pass"] for item in specificity.values())
    commit_latency = float(np.median([int(row["latency"]) for row in commit_rows]))
    domination: dict[str, dict[str, Any]] = {}
    for arm in INTERNAL_ARMS:
        arm_rows = [lookup[(seed, arm)] for seed in seed_tuple]
        arm_latency = float(np.median([int(row["latency"]) for row in arm_rows]))
        arm_false = float(
            np.mean([float(row["false_reopen_rate"]) for row in arm_rows])
        )
        dominates = arm_latency <= commit_latency and arm_false <= commit_false
        domination[arm] = {
            "median_latency": arm_latency,
            "mean_false_reopen_rate": arm_false,
            "dominates_commit": bool(dominates),
        }
    f4 = not any(item["dominates_commit"] for item in domination.values())
    none_rows = [lookup[(seed, "T_none")] for seed in seed_tuple]
    none_passes = sum(bool(row["terminal_pass"]) for row in none_rows)
    f5 = none_passes == 0
    gates = {
        "F0_integrity": {
            **f0_gate,
        },
        "F1_commit_8_of_8": {
            "pass": f1,
            "passes": sum(bool(row["terminal_pass"]) for row in commit_rows),
            "required": len(DEFAULT_SEEDS),
        },
        "F2_latency_dominance": {"pass": f2, "contrasts": latency_contrasts},
        "F3_specificity": {"pass": f3, "contrasts": specificity},
        "F4_joint_non_domination": {"pass": f4, "arms": domination},
        "F5_none_floor": {
            "pass": f5,
            "passes": none_passes,
            "required": 0,
        },
    }
    strict_pass = all(bool(gate["pass"]) for gate in gates.values())
    return {
        "kind": "m5_suite_c_reopen_reset_trigger_summary",
        "strict_verdict": "PASS" if strict_pass else "FAIL",
        "claim_level": (
            "diagnostic finite-harness trigger comparison"
            if strict_pass
            else "failed diagnostic gate; trigger superiority remains a hypothesis"
        ),
        "seeds": list(seed_tuple),
        "arms": list(ARMS),
        "n_rows": len(rows),
        "calibration": calibration,
        "arm_summaries": _bootstrap_summary(rows, seed_tuple),
        "gates": gates,
        "preregistration_repair": str(IMPLEMENTATION_CONTRACT),
        "rejected_alternatives": [
            "post-outcome trigger threshold tuning",
            "unequal actual probe counts",
            "filler probes into closed affected buckets",
            "impulse-count false-reopen metric",
            "aggregate-only unpaired contrasts",
        ],
    }


def run_m5_suite(
    *,
    seeds: Iterable[int] = DEFAULT_SEEDS,
    calibration: dict[str, Any] | None = None,
    arms: tuple[str, ...] = ARMS,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
    out: Path = RAW_PAYLOAD,
    summary_json: Path = PUBLIC_SUMMARY_JSON,
    summary_md: Path = PUBLIC_SUMMARY_MD,
) -> dict[str, Any]:
    seed_tuple = tuple(int(seed) for seed in seeds)
    if not seed_tuple or len(set(seed_tuple)) != len(seed_tuple):
        raise ValueError("paired seeds must be non-empty and unique")
    if set(arms) != set(ARMS) or len(arms) != len(ARMS):
        raise ValueError("M5 execution requires each frozen arm exactly once")
    if calibration is None:
        calibration = load_calibration_receipt()
    reference = run_suite(seeds=list(seed_tuple), cfg=cfg)
    plans = {seed: build_probe_plan(seed, cfg) for seed in seed_tuple}
    rows = [
        run_m5_trial(seed, arm, calibration, cfg, plans[seed])
        for seed in seed_tuple
        for arm in arms
    ]
    rows_sorted = sorted(rows, key=lambda row: (int(row["seed"]), str(row["arm"])))
    replay_reference = run_suite(seeds=list(seed_tuple), cfg=cfg)
    replay_plans = {seed: build_probe_plan(seed, cfg) for seed in seed_tuple}
    deterministic_replay = (
        reference == replay_reference
        and plans == replay_plans
        and all(
            row
            == run_m5_trial(
                int(row["seed"]),
                str(row["arm"]),
                calibration,
                cfg,
                replay_plans[int(row["seed"])],
            )
            for row in rows_sorted
        )
    )
    summary = evaluate_gates(
        rows,
        reference,
        seed_tuple,
        calibration,
        deterministic_replay=deterministic_replay,
        cfg=cfg,
    )
    summary["integrity_history"] = {
        "invalidated_raw_payload_sha256": list(INVALIDATED_RAW_PAYLOAD_SHA256),
        "superseded_portability_raw_payload_sha256": list(
            SUPERSEDED_PORTABILITY_RAW_PAYLOAD_SHA256
        ),
        "reason": (
            "post-run review found eight T_commit steps where fallback collisions "
            "changed sequential RNG consumption across the coupled no-change run"
        ),
        "replacement": (
            "pre-index initial, shift, probe-token, and drift variates; retain the "
            "frozen arms, seeds, calibration, probe budgets, and F0-F5 gates"
        ),
        "portability_repair": (
            "use frozen 12-decimal semantic digests only for random schedules and "
            "the transported reference while retaining an exact final-row digest; "
            "all plans, point estimates, and F0-F5 dispositions are unchanged"
        ),
    }
    command = (
        "uvx --python 3.12 --with numpy python -m "
        "experiments.world_responds.suite_c_reopen_reset_trigger "
        f"--seeds {','.join(str(seed) for seed in seed_tuple)} "
        f"--out {out} --summary-json {summary_json} "
        f"--summary-md {summary_md}"
    )
    summary["run_config"] = {
        "command": command,
        "steps": cfg.steps,
        "first_shift": cfg.first_shift,
        "second_shift": cfg.second_shift,
        "period": PERIODIC_TRIGGER_PERIOD,
        "open_duration": OPEN_DURATION,
        "latency_censor": cfg.post_second_end - cfg.second_shift,
        "bootstrap_samples": BOOTSTRAP_SAMPLES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "source_revision": SOURCE_REVISION,
    }
    return {
        "kind": "m5_suite_c_reopen_reset_trigger",
        "manifest": summary["run_config"],
        "calibration": calibration,
        "probe_plans": [plans[seed] for seed in seed_tuple],
        "rows": rows,
        "reference_suite": reference,
        "summary": summary,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    invalidated = ", ".join(
        summary["integrity_history"]["invalidated_raw_payload_sha256"]
    )
    superseded_portability = ", ".join(
        summary["integrity_history"]["superseded_portability_raw_payload_sha256"]
    )
    lines = [
        "# M5 Suite C Reopen/Reset Trigger Comparison (2026-07-14)",
        "",
        f"**Strict gate verdict: {summary['strict_verdict']}.**",
        f"Claim level: {summary['claim_level']}.",
        "",
        "The 2026-07-14 pre-run implementation contract transparently repaired",
        "underspecified trigger, budget-routing, latency, and false-calm details",
        "before any M5 outcome cell was executed.",
        "",
        "## Exact run config",
        "",
        "```bash",
        summary["run_config"]["command"],
        "```",
        "",
        f"Paired seeds: `{summary['seeds']}`.",
        f"Calibration receipt: `{summary['calibration']['receipt_sha256']}`.",
        f"Ignored raw payload SHA-256: `{summary['raw_payload_sha256']}`.",
        f"Pre-registration: `{PREREGISTRATION}`.",
        f"Implementation contract: `{IMPLEMENTATION_CONTRACT}`.",
        "",
        "## Integrity replacement",
        "",
        "Two pre-fix raw payloads were invalidated after review found branch-dependent",
        "RNG consumption in the coupled no-change run:",
        f"`{invalidated}`.",
        "The replacement pre-indexes every variate; it does not change the frozen",
        "arms, seeds, thresholds, probe budgets, or F0–F5 gates.",
        "A later Linux CI replay superseded the first corrected raw receipt",
        f"`{superseded_portability}` because exact raw-float hashes were platform-sensitive.",
        "The manifest now uses 12-decimal semantic hashes only for schedules and",
        "the transported reference; its final-row digest remains exact. Plans, point",
        "estimates, and every F0–F5 disposition remain unchanged.",
        "",
        "## Arm summaries",
        "",
        "| arm | pass | latency | false reopen | selectivity | reopen ratio | final MAE | probes |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for arm in summary["arm_summaries"]:
        lines.append(
            f"| {arm['arm']} | {arm['terminal_pass_rate']['point']:.3f} | "
            f"{arm['latency']['point']:.3f} | "
            f"{arm['false_reopen_rate']['point']:.3f} | "
            f"{arm['selectivity']['point']:.3f} | "
            f"{arm['reopen_ratio']['point']:.3f} | "
            f"{arm['final_mae']['point']:.3f} | "
            f"{arm['probe_cost']['point']:.1f} |"
        )
    lines.extend(["", "## Frozen gates", ""])
    for name, gate in summary["gates"].items():
        lines.append(f"- **{name}: {'PASS' if gate['pass'] else 'FAIL'}.**")
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "The strict verdict is determined only by F0–F5. Failures are not",
            "upgraded by directional metrics. This finite Suite C diagnostic does",
            "not establish a neural continual-learning result.",
            "",
            "## Rejected alternatives",
            "",
        ]
    )
    lines.extend(f"- {item}." for item in summary["rejected_alternatives"])
    return "\n".join(lines) + "\n"


def _write_if_changed(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == content:
        return
    path.write_text(content)


def write_calibration_receipt(
    calibration: dict[str, Any], path: Path = CALIBRATION_RECEIPT
) -> None:
    content = json.dumps(calibration, indent=2, sort_keys=True) + "\n"
    if not _calibration_receipt_is_valid(calibration):
        raise RuntimeError("calibration does not match the frozen M5 receipt")
    if hashlib.sha256(content.encode()).hexdigest() != FROZEN_CALIBRATION_FILE_SHA256:
        raise RuntimeError(
            "calibration serialization does not match the frozen M5 file"
        )
    if path.exists() and path.read_text() != content:
        raise RuntimeError(
            "refusing to overwrite a different frozen calibration receipt"
        )
    _write_if_changed(path, content)


def load_calibration_receipt(path: Path = CALIBRATION_RECEIPT) -> dict[str, Any]:
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != FROZEN_CALIBRATION_FILE_SHA256:
        raise RuntimeError("calibration file does not match the frozen M5 receipt")
    calibration = json.loads(content)
    if not _calibration_receipt_is_valid(calibration):
        raise RuntimeError("calibration payload does not match the frozen M5 receipt")
    return calibration


def write_artifacts(
    payload: dict[str, Any],
    *,
    out: Path = RAW_PAYLOAD,
    summary_json: Path = PUBLIC_SUMMARY_JSON,
    summary_md: Path = PUBLIC_SUMMARY_MD,
) -> None:
    raw_content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    public_summary = {
        **payload["summary"],
        "raw_payload_sha256": hashlib.sha256(raw_content.encode()).hexdigest(),
    }
    _write_if_changed(out, raw_content)
    _write_if_changed(
        summary_json,
        json.dumps(public_summary, indent=2, sort_keys=True) + "\n",
    )
    _write_if_changed(summary_md, render_markdown(public_summary))


def _parse_seeds(value: str) -> tuple[int, ...]:
    return tuple(int(part.strip()) for part in value.split(",") if part.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds", default=",".join(str(seed) for seed in DEFAULT_SEEDS)
    )
    parser.add_argument("--calibration-only", action="store_true")
    parser.add_argument("--calibration-json", type=Path, default=CALIBRATION_RECEIPT)
    parser.add_argument("--out", type=Path, default=RAW_PAYLOAD)
    parser.add_argument("--summary-json", type=Path, default=PUBLIC_SUMMARY_JSON)
    parser.add_argument("--summary-md", type=Path, default=PUBLIC_SUMMARY_MD)
    args = parser.parse_args()
    if args.calibration_only:
        calibration = calibrate_trigger_thresholds(DEFAULT_SEEDS)
        write_calibration_receipt(calibration, args.calibration_json)
        print(json.dumps(calibration, indent=2, sort_keys=True))
        return
    calibration = load_calibration_receipt(args.calibration_json)
    payload = run_m5_suite(
        seeds=_parse_seeds(args.seeds),
        calibration=calibration,
        out=args.out,
        summary_json=args.summary_json,
        summary_md=args.summary_md,
    )
    write_artifacts(
        payload,
        out=args.out,
        summary_json=args.summary_json,
        summary_md=args.summary_md,
    )
    print(
        json.dumps(
            {
                "strict_verdict": payload["summary"]["strict_verdict"],
                "gates": {
                    name: gate["pass"]
                    for name, gate in payload["summary"]["gates"].items()
                },
                "calibration_receipt": str(args.calibration_json),
                "summary_json": str(args.summary_json),
                "summary_md": str(args.summary_md),
                "raw_payload": str(args.out),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
