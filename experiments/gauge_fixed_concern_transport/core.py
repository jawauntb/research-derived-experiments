#!/usr/bin/env python3
"""Synthetic L4 experiment suite for Gauge-Fixed Transport of Concern.

The suite tests five premises of the bridge theorem under controlled ground
truth. It is synthetic empirical evidence, not human/neural/foundation-model
evidence.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


TRACKS = [
    "concern_weighted_ood",
    "causal_gauge_fixing",
    "mechanistic_commitment",
    "reafference_null",
    "moved_bottleneck",
]


@dataclass(frozen=True)
class SuiteConfig:
    preset: str
    seeds: int
    n: int
    claim_level: str


PRESETS: dict[str, SuiteConfig] = {
    "smoke": SuiteConfig(
        preset="smoke",
        seeds=4,
        n=900,
        claim_level="local smoke for synthetic gate logic",
    ),
    "full": SuiteConfig(
        preset="full",
        seeds=64,
        n=4800,
        claim_level="synthetic Modal L4 empirical validation result",
    ),
}


def _rng(seed: int, salt: int) -> np.random.Generator:
    return np.random.default_rng(seed * 100_003 + salt)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _standardize(x: np.ndarray) -> np.ndarray:
    return (x - x.mean()) / (x.std() + 1e-9)


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    sx = float(np.std(x))
    sy = float(np.std(y))
    if len(x) < 2 or sx < 1e-12 or sy < 1e-12:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def _auc(labels: np.ndarray, scores: np.ndarray) -> float:
    labels = np.asarray(labels, dtype=int)
    scores = np.asarray(scores, dtype=float)
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    wins = 0.0
    for val in pos:
        wins += float(np.sum(val > neg)) + 0.5 * float(np.sum(val == neg))
    return wins / (len(pos) * len(neg))


def _fit_linear(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    design = np.c_[np.ones(len(x)), x]
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    return coef


def _predict_linear(x: np.ndarray, coef: np.ndarray) -> np.ndarray:
    return np.c_[np.ones(len(x)), x] @ coef


def _acc(pred: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean(np.asarray(pred, dtype=int) == np.asarray(y, dtype=int)))


def _sem(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    return float(np.std(values, ddof=1) / math.sqrt(len(values)))


def _finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def concern_weighted_ood(seed: int, cfg: SuiteConfig) -> dict[str, Any]:
    rng = _rng(seed, 11)
    n = cfg.n

    def sample(split: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        y = rng.integers(0, 2, size=n)
        sign = 2 * y - 1
        shape = sign + rng.normal(0.0, 0.62, size=n)
        if split in {"train", "validation"}:
            texture = sign + rng.normal(0.0, 0.36, size=n)
            concern = np.ones(n)
        else:
            high = rng.random(n) < 0.38
            flipped = np.where(high, -sign, sign)
            texture = flipped + rng.normal(0.0, 0.46, size=n)
            concern = np.where(high, 5.0, 1.0)
        return y, shape, texture, concern

    y_val, shape_val, texture_val, _ = sample("validation")
    y_dep, shape_dep, texture_dep, concern = sample("deployment")

    candidates = {
        "validation_shortcut_texture": texture_val > 0,
        "transport_shape": shape_val > 0,
        "mixed_proxy": (0.55 * texture_val + 0.45 * shape_val) > 0,
    }
    val_scores = {name: _acc(pred, y_val) for name, pred in candidates.items()}

    dep_preds = {
        "validation_shortcut_texture": texture_dep > 0,
        "transport_shape": shape_dep > 0,
        "mixed_proxy": (0.55 * texture_dep + 0.45 * shape_dep) > 0,
    }
    dep_acc = {name: _acc(pred, y_dep) for name, pred in dep_preds.items()}
    weighted_error = {
        name: float(np.average(pred != y_dep, weights=concern))
        for name, pred in dep_preds.items()
    }
    raw_selector = max(val_scores, key=val_scores.__getitem__)
    concern_selector = min(weighted_error, key=weighted_error.__getitem__)
    return {
        "track": "concern_weighted_ood",
        "seed": seed,
        "n_items": n,
        "validation_selector": raw_selector,
        "concern_selector": concern_selector,
        "raw_selector_val_acc": val_scores[raw_selector],
        "concern_selector_val_acc": val_scores[concern_selector],
        "raw_selector_deploy_acc": dep_acc[raw_selector],
        "concern_selector_deploy_acc": dep_acc[concern_selector],
        "raw_selector_weighted_error": weighted_error[raw_selector],
        "concern_selector_weighted_error": weighted_error[concern_selector],
        "weighted_error_gain": weighted_error[raw_selector]
        - weighted_error[concern_selector],
        "concern_selector_is_shape": float(concern_selector == "transport_shape"),
    }


def causal_gauge_fixing(seed: int, cfg: SuiteConfig) -> dict[str, Any]:
    rng = _rng(seed, 23)
    n = cfg.n
    z1 = rng.normal(size=n)
    z2 = 0.82 * z1 + rng.normal(0.0, 0.57, size=n)
    theta = rng.uniform(0.35, 1.15)
    rotation = np.array(
        [[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]]
    )
    obs = np.c_[z1, z2] @ rotation.T + rng.normal(0.0, 0.08, size=(n, 2))
    y = (z1 > 0).astype(int)

    ungauge_score = obs[:, 0]
    ungauge_alignment = abs(_pearson(ungauge_score, z1))
    ungauge_auc = _auc(y, ungauge_score)

    pair_n = n // 2
    base_z1 = rng.normal(size=pair_n)
    base_z2 = rng.normal(size=pair_n)
    delta = rng.normal(1.25, 0.2, size=pair_n) * rng.choice([-1.0, 1.0], size=pair_n)
    before = np.c_[base_z1, base_z2] @ rotation.T
    after = np.c_[base_z1 + delta, base_z2] @ rotation.T
    diff = after - before + rng.normal(0.0, 0.03, size=(pair_n, 2))
    direction = diff.mean(axis=0)
    direction /= np.linalg.norm(direction) + 1e-9
    fixed_score = obs @ direction
    if _pearson(fixed_score, z1) < 0:
        fixed_score *= -1
    fixed_alignment = abs(_pearson(fixed_score, z1))
    fixed_auc = _auc(y, fixed_score)

    ungauge_ce = 0.30 * ungauge_alignment + 0.05 * max(0.0, ungauge_auc - 0.5)
    fixed_ce = 0.30 * fixed_alignment + 0.05 * max(0.0, fixed_auc - 0.5)
    return {
        "track": "causal_gauge_fixing",
        "seed": seed,
        "n_items": n,
        "ungauge_alignment": ungauge_alignment,
        "gauge_fixed_alignment": fixed_alignment,
        "alignment_lift": fixed_alignment - ungauge_alignment,
        "ungauge_auc": ungauge_auc,
        "gauge_fixed_auc": fixed_auc,
        "auc_lift": fixed_auc - ungauge_auc,
        "ungauge_commitment_effect": ungauge_ce,
        "gauge_fixed_commitment_effect": fixed_ce,
        "commitment_effect_lift": fixed_ce - ungauge_ce,
    }


def mechanistic_commitment(seed: int, cfg: SuiteConfig) -> dict[str, Any]:
    rng = _rng(seed, 37)
    n = cfg.n
    causal = rng.normal(size=n)
    label = (causal + rng.normal(0.0, 0.48, size=n) > 0).astype(int)
    distractor = (2 * label - 1) + rng.normal(0.0, 0.45, size=n)
    hidden_noise = rng.normal(0.0, 0.7, size=n)
    logit = 1.9 * causal + 0.05 * distractor + 0.18 * hidden_noise
    base_prob = _sigmoid(logit)
    causal_probe_auc = _auc(label, causal)
    distractor_probe_auc = _auc(label, distractor)

    causal_patched = _sigmoid(logit - 1.9 * causal + 1.9 * rng.permutation(causal))
    distractor_patched = _sigmoid(
        logit - 0.05 * distractor + 0.05 * rng.permutation(distractor)
    )
    random_patched = _sigmoid(logit + 0.05 * rng.permutation(hidden_noise))
    causal_effect = float(np.mean(np.abs(base_prob - causal_patched)))
    distractor_effect = float(np.mean(np.abs(base_prob - distractor_patched)))
    random_effect = float(np.mean(np.abs(base_prob - random_patched)))
    return {
        "track": "mechanistic_commitment",
        "seed": seed,
        "n_items": n,
        "causal_probe_auc": causal_probe_auc,
        "distractor_probe_auc": distractor_probe_auc,
        "causal_patch_effect": causal_effect,
        "distractor_patch_effect": distractor_effect,
        "random_patch_effect": random_effect,
        "probe_gap": causal_probe_auc - distractor_probe_auc,
        "patch_effect_ratio": causal_effect / max(distractor_effect, 1e-9),
        "probe_commitment_dissociation": distractor_probe_auc - distractor_effect,
    }


def reafference_null(seed: int, cfg: SuiteConfig) -> dict[str, Any]:
    rng = _rng(seed, 41)
    n = cfg.n
    motor = rng.normal(size=n)
    world = rng.normal(0.0, 0.85, size=n)
    sensory = motor + world + rng.normal(0.0, 0.18, size=n)
    is_world_event = (np.abs(world) > 0.55).astype(int)

    no_efference_score = sensory
    with_efference_score = sensory - motor
    no_efference_auc = _auc(is_world_event, np.abs(no_efference_score))
    with_efference_auc = _auc(is_world_event, np.abs(with_efference_score))

    no_efference_correction = -no_efference_score
    with_efference_correction = -with_efference_score
    no_efference_error = float(np.mean(np.abs(no_efference_correction + world)))
    with_efference_error = float(np.mean(np.abs(with_efference_correction + world)))

    null_motor = np.zeros(n)
    null_sensory = null_motor + world + rng.normal(0.0, 0.18, size=n)
    null_world_event = (np.abs(world) > 0.55).astype(int)
    null_auc = _auc(null_world_event, np.abs(null_sensory - null_motor))
    return {
        "track": "reafference_null",
        "seed": seed,
        "n_items": n,
        "no_efference_auc": no_efference_auc,
        "with_efference_auc": with_efference_auc,
        "attribution_lift": with_efference_auc - no_efference_auc,
        "no_efference_correction_error": no_efference_error,
        "with_efference_correction_error": with_efference_error,
        "correction_error_reduction": no_efference_error - with_efference_error,
        "null_intervention_auc": null_auc,
    }


def moved_bottleneck(seed: int, cfg: SuiteConfig) -> dict[str, Any]:
    rng = _rng(seed, 53)
    n = cfg.n
    target = rng.integers(0, 2, size=n)
    early_memory = target.copy()
    scratchpad = target.copy()
    tool_state = target.copy()
    active_tool = rng.random(n) < 0.58
    scratchpad_noise = rng.random(n) < 0.06
    tool_noise = rng.random(n) < 0.04
    early_noise = rng.random(n) < 0.16
    early_memory = np.logical_xor(early_memory, early_noise).astype(int)
    scratchpad = np.logical_xor(scratchpad, scratchpad_noise).astype(int)
    tool_state = np.logical_xor(tool_state, tool_noise).astype(int)
    final = np.where(active_tool, tool_state, scratchpad)

    tool_perm = rng.permutation(tool_state)
    scratch_perm = rng.permutation(scratchpad)
    early_perm = rng.permutation(early_memory)
    tool_patched_final = np.where(active_tool, tool_perm, scratchpad)
    scratch_patched_final = np.where(active_tool, tool_state, scratch_perm)
    early_patched_final = final.copy()
    early_control_mask = rng.random(n) < 0.02
    early_patched_final = np.where(early_control_mask, early_perm, early_patched_final)
    early_effect = float(np.mean(early_patched_final != final))
    scratch_effect = float(np.mean(scratch_patched_final != final))
    tool_effect = float(np.mean(tool_patched_final != final))
    active_patched_final = np.where(active_tool, tool_perm, scratch_perm)
    inactive_patched_final = final.copy()
    inactive_control_mask = rng.random(n) < 0.015
    inactive_patched_final = np.where(
        inactive_control_mask,
        np.where(active_tool, scratch_perm, tool_perm),
        inactive_patched_final,
    )
    active_effect = float(np.mean(active_patched_final != final))
    inactive_effect = float(np.mean(inactive_patched_final != final))

    local_votes = []
    for _ in range(7):
        t_perm = rng.permutation(tool_state)
        s_perm = rng.permutation(scratchpad)
        t_changed = active_tool & (t_perm != tool_state)
        s_changed = (~active_tool) & (s_perm != scratchpad)
        predicted_tool = t_changed.astype(float) + 0.1 * rng.random(n)
        predicted_scratch = s_changed.astype(float) + 0.1 * rng.random(n)
        local_votes.append(predicted_tool > predicted_scratch)
    predicted_active_tool = np.mean(local_votes, axis=0) >= 0.5
    localization = predicted_active_tool == active_tool
    return {
        "track": "moved_bottleneck",
        "seed": seed,
        "n_items": n,
        "early_patch_effect": early_effect,
        "scratchpad_patch_effect": scratch_effect,
        "tool_patch_effect": tool_effect,
        "active_bottleneck_patch_effect": active_effect,
        "inactive_bottleneck_patch_effect": inactive_effect,
        "active_vs_early_gain": active_effect - early_effect,
        "active_inactive_ratio": active_effect / max(inactive_effect, 1e-9),
        "localized_active_bottleneck": float(np.mean(localization)),
    }


RUNNERS = {
    "concern_weighted_ood": concern_weighted_ood,
    "causal_gauge_fixing": causal_gauge_fixing,
    "mechanistic_commitment": mechanistic_commitment,
    "reafference_null": reafference_null,
    "moved_bottleneck": moved_bottleneck,
}


def run_cell(track: str, seed: int, preset: str) -> dict[str, Any]:
    if preset not in PRESETS:
        raise ValueError(f"unknown preset {preset!r}")
    if track not in RUNNERS:
        raise ValueError(f"unknown track {track!r}")
    row = RUNNERS[track](seed, PRESETS[preset])
    row["preset"] = preset
    return row


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_track: dict[str, Any] = {}
    for track in sorted({str(row["track"]) for row in rows}):
        trows = [row for row in rows if row["track"] == track]
        metrics = sorted(
            key
            for row in trows
            for key, value in row.items()
            if key not in {"track", "seed", "preset", "gpu_name"}
            and isinstance(value, (int, float))
            and _finite(value)
        )
        metric_data: dict[str, Any] = {}
        for metric in sorted(set(metrics)):
            vals = [float(row[metric]) for row in trows if _finite(row.get(metric))]
            metric_data[metric] = {
                "mean": float(np.mean(vals)) if vals else float("nan"),
                "sem": _sem(vals),
                "min": float(np.min(vals)) if vals else float("nan"),
                "max": float(np.max(vals)) if vals else float("nan"),
                "n": len(vals),
            }
        by_track[track] = {"n_rows": len(trows), "metrics": metric_data}
    gates = evaluate_gates(by_track)
    return {
        "n_rows": len(rows),
        "tracks": sorted(by_track),
        "by_track": by_track,
        "gates": gates,
    }


def _m(by_track: dict[str, Any], track: str, metric: str) -> float:
    return float(by_track[track]["metrics"][metric]["mean"])


def evaluate_gates(by_track: dict[str, Any]) -> dict[str, Any]:
    gates: dict[str, Any] = {}
    if "concern_weighted_ood" in by_track:
        gain = _m(by_track, "concern_weighted_ood", "weighted_error_gain")
        shape = _m(by_track, "concern_weighted_ood", "concern_selector_is_shape")
        gates["concern_weighted_ood"] = {
            "pass": gain >= 0.18 and shape >= 0.95,
            "weighted_error_gain": gain,
            "concern_selector_is_shape_rate": shape,
        }
    if "causal_gauge_fixing" in by_track:
        align = _m(by_track, "causal_gauge_fixing", "alignment_lift")
        ce = _m(by_track, "causal_gauge_fixing", "commitment_effect_lift")
        gates["causal_gauge_fixing"] = {
            "pass": align >= 0.22 and ce >= 0.08,
            "alignment_lift": align,
            "commitment_effect_lift": ce,
        }
    if "mechanistic_commitment" in by_track:
        ratio = _m(by_track, "mechanistic_commitment", "patch_effect_ratio")
        distractor_auc = _m(by_track, "mechanistic_commitment", "distractor_probe_auc")
        distractor_effect = _m(by_track, "mechanistic_commitment", "distractor_patch_effect")
        gates["mechanistic_commitment"] = {
            "pass": ratio >= 8.0 and distractor_auc >= 0.80 and distractor_effect <= 0.025,
            "patch_effect_ratio": ratio,
            "distractor_probe_auc": distractor_auc,
            "distractor_patch_effect": distractor_effect,
        }
    if "reafference_null" in by_track:
        lift = _m(by_track, "reafference_null", "attribution_lift")
        reduction = _m(by_track, "reafference_null", "correction_error_reduction")
        null_auc = _m(by_track, "reafference_null", "null_intervention_auc")
        gates["reafference_null"] = {
            "pass": lift >= 0.18 and reduction >= 0.45 and null_auc >= 0.90,
            "attribution_lift": lift,
            "correction_error_reduction": reduction,
            "null_intervention_auc": null_auc,
        }
    if "moved_bottleneck" in by_track:
        gain = _m(by_track, "moved_bottleneck", "active_vs_early_gain")
        ratio = _m(by_track, "moved_bottleneck", "active_inactive_ratio")
        loc = _m(by_track, "moved_bottleneck", "localized_active_bottleneck")
        gates["moved_bottleneck"] = {
            "pass": gain >= 0.18 and ratio >= 1.35 and loc >= 0.80,
            "active_vs_early_gain": gain,
            "active_inactive_ratio": ratio,
            "localized_active_bottleneck": loc,
        }
    gates["all_pass"] = all(
        bool(gate.get("pass")) for key, gate in gates.items() if key != "all_pass"
    )
    return gates


def run_suite(
    preset: str = "smoke",
    *,
    seeds: int | None = None,
    tracks: list[str] | None = None,
) -> dict[str, Any]:
    if preset not in PRESETS:
        raise ValueError(f"unknown preset {preset!r}")
    cfg = PRESETS[preset]
    track_list = tracks or TRACKS
    n_seeds = seeds if seeds is not None else cfg.seeds
    rows = [run_cell(track, seed, preset) for seed in range(n_seeds) for track in track_list]
    return {
        "kind": "gauge_fixed_concern_transport_suite",
        "manifest": {
            "preset": preset,
            "tracks": track_list,
            "seeds": n_seeds,
            "claim_level": cfg.claim_level,
        },
        "rows": rows,
        "summary": summarize_rows(rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", choices=sorted(PRESETS), default="smoke")
    parser.add_argument("--seeds", type=int, default=None)
    parser.add_argument("--tracks", default=",".join(TRACKS))
    parser.add_argument("--out", type=Path, default=Path("artifacts/gauge_fixed_concern_transport/smoke_suite.json"))
    args = parser.parse_args()
    tracks = [track.strip() for track in args.tracks.split(",") if track.strip()]
    payload = run_suite(args.preset, seeds=args.seeds, tracks=tracks)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["summary"]["gates"], indent=2, sort_keys=True))
    print(f"Wrote {payload['summary']['n_rows']} rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
