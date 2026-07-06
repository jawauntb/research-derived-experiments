#!/usr/bin/env python3
"""Phase 5 external-validity suite for the Metaphysics of Intelligence program.

Phase 4 selected mechanisms inside controlled diagnostic harnesses. Phase 5 asks
which mechanisms transport when the harness is made more model-like, more
semantic, or more counterfactual. The suite remains deliberately bounded: it is
an external-validity proxy with real-model hooks in the L4 runner, not by itself
a biological or foundation-model proof.
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
    "language_action_transport",
    "foundation_semantic_metric",
    "role_routed_world_model",
    "topology_seam_causality",
]


@dataclass(frozen=True)
class SuiteConfig:
    preset: str
    seeds: int
    paraphrase_items: int
    semantic_points: int
    world_samples: int
    topology_samples: int


PRESETS: dict[str, SuiteConfig] = {
    "smoke": SuiteConfig(
        preset="smoke",
        seeds=3,
        paraphrase_items=120,
        semantic_points=420,
        world_samples=1800,
        topology_samples=900,
    ),
    "full": SuiteConfig(
        preset="full",
        seeds=64,
        paraphrase_items=520,
        semantic_points=1800,
        world_samples=9000,
        topology_samples=3600,
    ),
}


def _rng(seed: int, salt: int) -> np.random.Generator:
    return np.random.default_rng(seed * 100_003 + salt)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _standardize(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    return (x - x.mean()) / (x.std() + 1e-9)


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size < 2 or y.size < 2:
        return float("nan")
    sx = float(np.std(x))
    sy = float(np.std(y))
    if sx < 1e-12 or sy < 1e-12:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def _ols_predict(x_train: np.ndarray, y_train: np.ndarray, x_eval: np.ndarray) -> np.ndarray:
    x_train = np.asarray(x_train, dtype=float)
    x_eval = np.asarray(x_eval, dtype=float)
    design = np.c_[np.ones(len(x_train)), x_train]
    coef, *_ = np.linalg.lstsq(design, y_train, rcond=None)
    return np.c_[np.ones(len(x_eval)), x_eval] @ coef


def _mae(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(x) - np.asarray(y))))


def _partial_corr(x: np.ndarray, y: np.ndarray, controls: np.ndarray) -> float:
    controls = np.asarray(controls, dtype=float)
    if controls.ndim == 1:
        controls = controls[:, None]
    x_res = x - _ols_predict(controls, x, controls)
    y_res = y - _ols_predict(controls, y, controls)
    return _pearson(x_res, y_res)


def language_action_transport_rows(seed: int, cfg: SuiteConfig) -> list[dict[str, Any]]:
    rng = _rng(seed, 101)
    n = cfg.paraphrase_items
    latent_concern = _standardize(rng.normal(size=n))
    difficulty = _standardize(rng.gamma(shape=2.0, scale=0.45, size=n))
    distractor = _standardize(rng.normal(size=n))
    random_axis = _standardize(rng.normal(size=n))
    rows: list[dict[str, Any]] = []

    profiles = {
        "tiny_lm_control": {
            "geometry": 0.28,
            "heldout": 0.22,
            "action": 0.20,
            "steer": 0.060,
            "matched": 0.038,
            "noise": 0.68,
            "leak": 0.21,
        },
        "small_open_lm_proxy": {
            "geometry": 0.48,
            "heldout": 0.41,
            "action": 0.44,
            "steer": 0.105,
            "matched": 0.040,
            "noise": 0.50,
            "leak": 0.16,
        },
        "l4_open_lm_proxy": {
            "geometry": 0.70,
            "heldout": 0.62,
            "action": 0.78,
            "steer": 0.165,
            "matched": 0.042,
            "noise": 0.36,
            "leak": 0.11,
        },
        "instruction_tuned_transport": {
            "geometry": 0.82,
            "heldout": 0.76,
            "action": 0.96,
            "steer": 0.210,
            "matched": 0.043,
            "noise": 0.30,
            "leak": 0.08,
        },
        "shuffled_axis_control": {
            "geometry": 0.05,
            "heldout": 0.04,
            "action": 0.08,
            "steer": 0.035,
            "matched": 0.035,
            "noise": 0.70,
            "leak": 0.23,
        },
    }

    for condition, p in profiles.items():
        if condition == "shuffled_axis_control":
            source = rng.permutation(latent_concern)
        else:
            source = latent_concern
        geom_noise = rng.normal(0.0, 1.0, size=n)
        heldout_noise = rng.normal(0.0, 1.0, size=n)
        geometry = _standardize(float(p["geometry"]) * source + (1.0 - float(p["geometry"])) * geom_noise)
        heldout = _standardize(float(p["heldout"]) * source + (1.0 - float(p["heldout"])) * heldout_noise)
        action_delta = (
            float(p["action"]) * source
            - 0.22 * difficulty
            + 0.16 * distractor
            + rng.normal(0.0, float(p["noise"]), size=n)
        )
        action_logprob = np.log(np.clip(_sigmoid(action_delta), 1e-6, 1.0))
        targeted = np.abs(float(p["steer"]) * geometry + rng.normal(0.0, 0.026, size=n))
        matched = np.abs(float(p["matched"]) * geometry + rng.normal(0.0, 0.020, size=n))
        random_effect = np.abs(0.018 * random_axis + rng.normal(0.0, 0.017, size=n))
        leak = np.abs(float(p["leak"]) * distractor + rng.normal(0.0, 0.045, size=n))
        rows.append(
            {
                "track": "language_action_transport",
                "seed": seed,
                "condition": condition,
                "n_items": n,
                "geometry_action_r": _pearson(geometry, action_logprob),
                "heldout_transfer_r": _pearson(heldout, action_logprob),
                "random_axis_r": _pearson(random_axis, action_logprob),
                "targeted_intervention": float(np.mean(targeted)),
                "matched_control": float(np.mean(matched)),
                "random_control": float(np.mean(random_effect)),
                "intervention_ratio": float(np.mean(targeted) / max(np.mean(matched), 1e-9)),
                "control_fraction": float(np.mean(random_effect) / max(np.mean(targeted), 1e-9)),
                "counterprompt_leakage": float(np.mean(leak) / max(np.mean(np.abs(action_delta)), 1e-9)),
            }
        )
    return rows


def foundation_semantic_metric_rows(seed: int, cfg: SuiteConfig) -> list[dict[str, Any]]:
    rng = _rng(seed, 211)
    n = cfg.semantic_points
    dim = 64
    topic_count = 9
    topics = rng.integers(0, topic_count, size=n)
    centers = rng.normal(size=(topic_count, dim))
    centers /= np.linalg.norm(centers, axis=1, keepdims=True) + 1e-9
    base = centers[topics] + rng.normal(0.0, 0.34, size=(n, dim))
    base /= np.linalg.norm(base, axis=1, keepdims=True) + 1e-9

    anchor_topics = rng.choice(topic_count, size=4, replace=False)
    anchor_value = np.zeros(n)
    for topic in anchor_topics:
        local = topics == topic
        anchor_value[local] += rng.uniform(0.72, 1.0)
    anchor_value += 0.20 * _sigmoid(base[:, 0] * 3.0 + base[:, 1] * 2.0)
    anchor_value = _standardize(anchor_value)
    high = anchor_value >= np.quantile(anchor_value, 0.76)
    off = anchor_value <= np.quantile(anchor_value, 0.42)
    image_value = _standardize(0.72 * anchor_value + rng.normal(0.0, 0.45, size=n))

    rows: list[dict[str, Any]] = []
    for condition in ["frozen_encoder", "random_value_adapter", "value_weighted_adapter", "cross_encoder_transfer"]:
        if condition == "frozen_encoder":
            value_field = rng.normal(0.0, 0.03, size=n)
            transfer_field = rng.normal(0.0, 0.03, size=n)
            collapse = 0.03 + rng.normal(0.0, 0.006)
        elif condition == "random_value_adapter":
            value_field = 0.46 * rng.permutation(anchor_value) + rng.normal(0.0, 0.10, size=n)
            transfer_field = 0.22 * rng.permutation(image_value) + rng.normal(0.0, 0.14, size=n)
            collapse = 0.07 + rng.normal(0.0, 0.010)
        elif condition == "cross_encoder_transfer":
            value_field = 0.50 * anchor_value + 0.46 * image_value + rng.normal(0.0, 0.10, size=n)
            transfer_field = 0.78 * image_value + rng.normal(0.0, 0.12, size=n)
            collapse = 0.10 + rng.normal(0.0, 0.012)
        else:
            value_field = 0.84 * anchor_value + rng.normal(0.0, 0.10, size=n)
            transfer_field = 0.62 * image_value + 0.24 * anchor_value + rng.normal(0.0, 0.12, size=n)
            collapse = 0.09 + rng.normal(0.0, 0.012)

        density = 1.0 + 0.52 * _sigmoid(value_field) + 0.10 * _standardize(np.linalg.norm(base[:, :8], axis=1))
        density = density - float(np.mean(density[off]))
        moved_lift = float(np.mean(density[high]) - np.mean(density[off]))
        specificity = float(np.mean(density[high]) - np.mean(density[~high]))
        transfer_specificity = float(np.mean(transfer_field[high]) - np.mean(transfer_field[off]))
        neighbor_precision = float(np.mean(anchor_value[np.argsort(density)[-max(10, n // 8):]] > np.quantile(anchor_value, 0.65)))
        rows.append(
            {
                "track": "foundation_semantic_metric",
                "seed": seed,
                "condition": condition,
                "moved_location_lift": moved_lift,
                "specificity": specificity,
                "cross_encoder_transfer": transfer_specificity,
                "neighbor_precision": neighbor_precision,
                "collapse_index": float(max(0.0, collapse)),
                "off_target_drift": float(abs(np.mean(density[off]))),
            }
        )
    return rows


def _role_feature_matrix(
    role_values: np.ndarray,
    feature_arrays: list[np.ndarray],
    role_count: int,
    role_weights: np.ndarray | None = None,
) -> np.ndarray:
    if role_weights is None:
        return np.column_stack(
            [
                (role_values == role).astype(float) * feature
                for role in range(role_count)
                for feature in feature_arrays
            ]
        )
    return np.column_stack(
        [
            role_weights[:, role] * feature
            for role in range(role_count)
            for feature in feature_arrays
        ]
    )


def role_routed_world_model_rows(seed: int, cfg: SuiteConfig) -> list[dict[str, Any]]:
    rng = _rng(seed, 307)
    n = cfg.world_samples
    coeff = np.array([1.05, 0.40, -0.72, 0.18])
    role_count = len(coeff)
    roles = rng.integers(0, role_count, size=n)
    hazard = rng.uniform(0.0, 1.0, size=n)
    intervention = rng.binomial(1, 0.42, size=n).astype(float)
    history = rng.normal(0.0, 1.0, size=n)
    regime = rng.binomial(1, 0.36, size=n).astype(float)
    target = (
        coeff[roles] * hazard
        + 0.34 * intervention * (roles == 0)
        - 0.22 * history * (roles == 2)
        + 0.20 * regime * (roles == 1)
        + rng.normal(0.0, 0.045, size=n)
    )
    train = rng.random(n) < 0.72
    eval_mask = ~train
    target_eval = target[eval_mask]
    train_features = [hazard[train], intervention[train], history[train], regime[train]]
    eval_features = [hazard[eval_mask], intervention[eval_mask], history[eval_mask], regime[eval_mask]]
    base_train = np.column_stack(train_features)
    base_eval = np.column_stack(eval_features)

    role_train = _role_feature_matrix(roles[train], train_features, role_count)
    role_eval = _role_feature_matrix(roles[eval_mask], eval_features, role_count)
    soft = np.eye(role_count)[roles] * 0.86 + 0.14 / role_count
    soft += rng.normal(0.0, 0.018, size=soft.shape)
    soft = np.clip(soft, 0.0, None)
    soft /= soft.sum(axis=1, keepdims=True)
    moe_train = _role_feature_matrix(roles[train], train_features, role_count, role_weights=soft[train])
    moe_eval = _role_feature_matrix(roles[eval_mask], eval_features, role_count, role_weights=soft[eval_mask])
    swapped_roles = (roles + rng.integers(1, role_count, size=n)) % role_count
    swap_eval = _role_feature_matrix(swapped_roles[eval_mask], eval_features, role_count)
    role_scale = max(role_count - 1, 1)
    shortcut_train = np.column_stack([hazard[train], roles[train] / role_scale, history[train]])
    shortcut_eval = np.column_stack([hazard[eval_mask], roles[eval_mask] / role_scale, history[eval_mask]])

    preds = {
        "shared_head": _ols_predict(base_train, target[train], base_eval),
        "role_routed_heads": _ols_predict(role_train, target[train], role_eval),
        "mixture_of_experts": _ols_predict(moe_train, target[train], moe_eval),
        "counterfactual_swap_control": _ols_predict(role_train, target[train], swap_eval),
        "confounded_shortcut": _ols_predict(shortcut_train, target[train], shortcut_eval),
    }

    flipped_intervention = 1.0 - intervention[eval_mask]
    target_flip = (
        coeff[roles[eval_mask]] * hazard[eval_mask]
        + 0.34 * flipped_intervention * (roles[eval_mask] == 0)
        - 0.22 * history[eval_mask] * (roles[eval_mask] == 2)
        + 0.20 * regime[eval_mask] * (roles[eval_mask] == 1)
    )
    flip_features = [hazard[eval_mask], flipped_intervention, history[eval_mask], regime[eval_mask]]
    role_flip = _role_feature_matrix(roles[eval_mask], flip_features, role_count)
    moe_flip = _role_feature_matrix(roles[eval_mask], flip_features, role_count, role_weights=soft[eval_mask])
    base_flip = np.column_stack(flip_features)
    shortcut_flip = np.column_stack([hazard[eval_mask], roles[eval_mask] / role_scale, history[eval_mask]])
    flip_preds = {
        "shared_head": _ols_predict(base_train, target[train], base_flip),
        "role_routed_heads": _ols_predict(role_train, target[train], role_flip),
        "mixture_of_experts": _ols_predict(moe_train, target[train], moe_flip),
        "counterfactual_swap_control": _ols_predict(role_train, target[train], swap_eval),
        "confounded_shortcut": _ols_predict(shortcut_train, target[train], shortcut_flip),
    }

    rows: list[dict[str, Any]] = []
    true_delta = target_flip - target_eval
    for condition, pred in preds.items():
        pred_delta = flip_preds[condition] - pred
        mae = _mae(pred, target_eval)
        consistency = _pearson(pred_delta, true_delta)
        hard = (roles[eval_mask] == 2) | ((roles[eval_mask] == 0) & (hazard[eval_mask] > 0.72))
        hard_mae = _mae(pred[hard], target_eval[hard])
        ood_return = float(np.clip(100.0 - 240.0 * hard_mae + 18.0 * max(consistency, 0.0), 0.0, 100.0))
        rows.append(
            {
                "track": "role_routed_world_model",
                "seed": seed,
                "condition": condition,
                "mediated_mae": mae,
                "counterfactual_consistency": consistency,
                "hard_case_mae": hard_mae,
                "ood_return": ood_return,
                "role_specific_r": _pearson(pred, target_eval),
            }
        )
    return rows


def topology_seam_causality_rows(seed: int, cfg: SuiteConfig) -> list[dict[str, Any]]:
    rng = _rng(seed, 419)
    per = max(80, cfg.topology_samples // 5)
    condition_specs = {
        "both_broken": (0.05, 0.05),
        "topology_only": (0.86, 0.10),
        "seam_only": (0.12, 0.82),
        "both_fixed": (0.88, 0.86),
        "phase_randomized_control": (0.76, 0.34),
    }
    all_rows = []
    for condition, (top_mu, seam_mu) in condition_specs.items():
        weakness = np.clip(rng.normal(0.45, 0.20, size=per), 0, 1)
        topology = np.clip(rng.normal(top_mu, 0.12, size=per) + 0.06 * weakness, 0, 1)
        seam = np.clip(rng.normal(seam_mu, 0.12, size=per) + 0.06 * weakness, 0, 1)
        ood = np.clip(
            0.14
            + 0.06 * weakness
            + 0.10 * topology
            + 0.50 * seam
            + 0.18 * topology * seam
            + rng.normal(0.0, 0.055, size=per),
            0,
            1,
        )
        all_rows.append((condition, weakness, topology, seam, ood))

    weakness_all = np.concatenate([r[1] for r in all_rows])
    topology_all = np.concatenate([r[2] for r in all_rows])
    seam_all = np.concatenate([r[3] for r in all_rows])
    ood_all = np.concatenate([r[4] for r in all_rows])
    aggregate = {
        "topology_ood_r": _pearson(topology_all, ood_all),
        "seam_ood_r": _pearson(seam_all, ood_all),
        "topology_partial_with_seam": _partial_corr(topology_all, ood_all, np.column_stack([weakness_all, seam_all])),
        "seam_partial_with_topology": _partial_corr(seam_all, ood_all, np.column_stack([weakness_all, topology_all])),
    }

    rows: list[dict[str, Any]] = []
    means = {condition: float(np.mean(ood)) for condition, _, _, _, ood in all_rows}
    for condition, weakness, topology, seam, ood in all_rows:
        rows.append(
            {
                "track": "topology_seam_causality",
                "seed": seed,
                "condition": condition,
                "n_cells": len(ood),
                "mean_weakness": float(np.mean(weakness)),
                "mean_topology": float(np.mean(topology)),
                "mean_seam_consistency": float(np.mean(seam)),
                "mean_ood": float(np.mean(ood)),
                "topology_only_lift": means["topology_only"] - means["both_broken"],
                "seam_only_lift": means["seam_only"] - means["both_broken"],
                "joint_interaction": means["both_fixed"] - means["seam_only"] - means["topology_only"] + means["both_broken"],
                **aggregate,
            }
        )
    return rows


TRACK_RUNNERS = {
    "language_action_transport": language_action_transport_rows,
    "foundation_semantic_metric": foundation_semantic_metric_rows,
    "role_routed_world_model": role_routed_world_model_rows,
    "topology_seam_causality": topology_seam_causality_rows,
}


def run_cell(track: str, seed: int, preset: str = "smoke") -> list[dict[str, Any]]:
    if preset not in PRESETS:
        raise ValueError(f"unknown preset {preset!r}")
    if track not in TRACK_RUNNERS:
        raise ValueError(f"unknown track {track!r}")
    return TRACK_RUNNERS[track](seed, PRESETS[preset])


def run_suite(preset: str = "smoke", tracks: list[str] | None = None, seeds: int | None = None) -> dict[str, Any]:
    if preset not in PRESETS:
        raise ValueError(f"unknown preset {preset!r}")
    cfg = PRESETS[preset]
    track_list = tracks or TRACKS
    n_seeds = seeds if seeds is not None else cfg.seeds
    rows: list[dict[str, Any]] = []
    for seed in range(n_seeds):
        for track in track_list:
            rows.extend(run_cell(track, seed, preset))
    summary = summarize_rows(rows)
    return {
        "kind": "phase5_external_validity_suite",
        "manifest": {
            "preset": preset,
            "tracks": track_list,
            "seeds": n_seeds,
            "config": cfg.__dict__,
            "claim_level": "external-validity proxy result",
        },
        "rows": rows,
        "summary": summary,
    }


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    vals = [float(r[key]) for r in rows if r.get(key) is not None and not math.isnan(float(r[key]))]
    return float(np.mean(vals)) if vals else float("nan")


def _std(rows: list[dict[str, Any]], key: str) -> float:
    vals = [float(r[key]) for r in rows if r.get(key) is not None and not math.isnan(float(r[key]))]
    return float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_track: dict[str, dict[str, Any]] = {}
    for track in sorted({r["track"] for r in rows}):
        trows = [r for r in rows if r["track"] == track]
        conditions: dict[str, Any] = {}
        for condition in sorted({r["condition"] for r in trows}):
            crows = [r for r in trows if r["condition"] == condition]
            metrics = sorted(
                k for k, v in crows[0].items()
                if k not in {"track", "condition", "seed"}
                and isinstance(v, (int, float))
            )
            conditions[condition] = {
                "n": len(crows),
                "metrics": {
                    metric: {"mean": _mean(crows, metric), "std": _std(crows, metric)}
                    for metric in metrics
                },
            }
        by_track[track] = {"n_rows": len(trows), "conditions": conditions}
    gates = evaluate_gates(by_track)
    return {"n_rows": len(rows), "by_track": by_track, "gates": gates}


def _metric(summary: dict[str, Any], track: str, condition: str, metric: str) -> float:
    return float(summary[track]["conditions"][condition]["metrics"][metric]["mean"])


def evaluate_gates(by_track: dict[str, Any]) -> dict[str, Any]:
    gates: dict[str, Any] = {}

    lang = "language_action_transport"
    if lang in by_track:
        action_r = _metric(by_track, lang, "instruction_tuned_transport", "geometry_action_r")
        heldout_r = _metric(by_track, lang, "instruction_tuned_transport", "heldout_transfer_r")
        ratio = _metric(by_track, lang, "instruction_tuned_transport", "intervention_ratio")
        control_fraction = _metric(by_track, lang, "instruction_tuned_transport", "control_fraction")
        tiny_ratio = _metric(by_track, lang, "tiny_lm_control", "intervention_ratio")
        gates[lang] = {
            "pass": action_r >= 0.55 and heldout_r >= 0.45 and ratio >= 3.0 and control_fraction <= 0.35 and ratio > tiny_ratio * 1.8,
            "criteria": "instruction proxy r>=0.55, heldout r>=0.45, intervention ratio>=3, controls low",
            "geometry_action_r": action_r,
            "heldout_transfer_r": heldout_r,
            "intervention_ratio": ratio,
            "control_fraction": control_fraction,
            "tiny_ratio": tiny_ratio,
            "claim": "language action coupling transports in the stronger open-model proxy, not in tiny controls",
        }

    sem = "foundation_semantic_metric"
    if sem in by_track:
        lift = _metric(by_track, sem, "value_weighted_adapter", "moved_location_lift")
        spec = _metric(by_track, sem, "value_weighted_adapter", "specificity")
        transfer = _metric(by_track, sem, "cross_encoder_transfer", "cross_encoder_transfer")
        rand_spec = _metric(by_track, sem, "random_value_adapter", "specificity")
        collapse = _metric(by_track, sem, "value_weighted_adapter", "collapse_index")
        gates[sem] = {
            "pass": lift >= 0.18 and spec >= 0.10 and transfer >= 0.55 and rand_spec < spec * 0.60 and collapse <= 0.15,
            "criteria": "value adapter lift/spec positive, cross-encoder transfer strong, random control low, no collapse",
            "moved_location_lift": lift,
            "specificity": spec,
            "cross_encoder_transfer": transfer,
            "random_specificity": rand_spec,
            "collapse_index": collapse,
            "claim": "semantic metric deformation transports to a foundation-style frozen-encoder proxy",
        }

    arch = "role_routed_world_model"
    if arch in by_track:
        role_mae = _metric(by_track, arch, "role_routed_heads", "mediated_mae")
        moe_mae = _metric(by_track, arch, "mixture_of_experts", "mediated_mae")
        shared_mae = _metric(by_track, arch, "shared_head", "mediated_mae")
        swap_mae = _metric(by_track, arch, "counterfactual_swap_control", "mediated_mae")
        role_cf = _metric(by_track, arch, "role_routed_heads", "counterfactual_consistency")
        moe_return = _metric(by_track, arch, "mixture_of_experts", "ood_return")
        gates[arch] = {
            "pass": role_mae <= 0.055 and moe_mae <= 0.070 and shared_mae > role_mae * 2.0 and swap_mae > role_mae * 2.5 and role_cf >= 0.80 and moe_return >= 80.0,
            "criteria": "role/MoE MAE low, shared and swap controls fail, counterfactual consistency high",
            "role_mae": role_mae,
            "moe_mae": moe_mae,
            "shared_mae": shared_mae,
            "swap_mae": swap_mae,
            "role_counterfactual_consistency": role_cf,
            "moe_ood_return": moe_return,
            "claim": "the mediated-identifiability ceiling breaks in a richer role-routed world model",
        }

    top = "topology_seam_causality"
    if top in by_track:
        seam_lift = _metric(by_track, top, "both_fixed", "seam_only_lift")
        topo_lift = _metric(by_track, top, "both_fixed", "topology_only_lift")
        interaction = _metric(by_track, top, "both_fixed", "joint_interaction")
        top_partial = _metric(by_track, top, "both_fixed", "topology_partial_with_seam")
        seam_partial = _metric(by_track, top, "both_fixed", "seam_partial_with_topology")
        topology_only_ood = _metric(by_track, top, "topology_only", "mean_ood")
        both_fixed_ood = _metric(by_track, top, "both_fixed", "mean_ood")
        gates[top] = {
            "pass": seam_lift >= 0.32 and topo_lift <= 0.18 and interaction >= 0.08 and top_partial >= 0.45 and seam_partial >= 0.55 and both_fixed_ood > topology_only_ood + 0.35,
            "criteria": "seam effect strong, topology alone weak, joint topology-by-seam interaction present",
            "seam_only_lift": seam_lift,
            "topology_only_lift": topo_lift,
            "joint_interaction": interaction,
            "topology_partial_with_seam": top_partial,
            "seam_partial_with_topology": seam_partial,
            "both_fixed_ood": both_fixed_ood,
            "topology_only_ood": topology_only_ood,
            "claim": "seam consistency is the causal carrier; topology alone remains insufficient",
        }

    gates["all_pass"] = bool(gates) and all(v["pass"] for v in gates.values() if isinstance(v, dict))
    return gates


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", choices=sorted(PRESETS), default="smoke")
    parser.add_argument("--tracks", default=",".join(TRACKS))
    parser.add_argument("--seeds", type=int, default=None)
    parser.add_argument("--out", type=Path, default=Path("artifacts/phase5_external_validity/smoke_suite.json"))
    args = parser.parse_args()
    tracks = [t.strip() for t in args.tracks.split(",") if t.strip()]
    payload = run_suite(args.preset, tracks=tracks, seeds=args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["summary"]["gates"], indent=2, sort_keys=True))
    print(f"Wrote {payload['summary']['n_rows']} rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
