#!/usr/bin/env python3
"""Phase 6 real-model validation suite.

Phase 5 used proxy harnesses to decide whether the next expensive tier was worth
running. Phase 6 replaces those proxies with actual public open language models
and frozen sentence encoders. The local core remains dependency-light so tests
can exercise gate logic without downloading model weights; `real_models.py` and
`modal_l4_suite.py` perform the actual Hugging Face work.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TRACKS = [
    "open_lm_action_coupling",
    "frozen_encoder_metric_deformation",
]

OPEN_LM_MODELS: dict[str, dict[str, Any]] = {
    "distilgpt2": {
        "model_id": "distilgpt2",
        "family": "decoder_lm",
        "chat_template": False,
    },
    "pythia_70m": {
        "model_id": "EleutherAI/pythia-70m-deduped",
        "family": "decoder_lm",
        "chat_template": False,
    },
    "qwen2_0_5b_instruct": {
        "model_id": "Qwen/Qwen2.5-0.5B-Instruct",
        "family": "instruction_decoder_lm",
        "chat_template": True,
    },
}

FROZEN_ENCODER_MODELS: dict[str, dict[str, Any]] = {
    "all_minilm_l6_v2": {
        "model_id": "sentence-transformers/all-MiniLM-L6-v2",
        "family": "sentence_transformer",
    },
    "bge_small_en_v1_5": {
        "model_id": "BAAI/bge-small-en-v1.5",
        "family": "sentence_transformer",
    },
}


@dataclass(frozen=True)
class Phase6Config:
    preset: str
    lm_models: tuple[str, ...]
    encoder_models: tuple[str, ...]
    claim_level: str


PRESETS: dict[str, Phase6Config] = {
    "smoke": Phase6Config(
        preset="smoke",
        lm_models=("distilgpt2", "pythia_70m"),
        encoder_models=("all_minilm_l6_v2", "bge_small_en_v1_5"),
        claim_level="fixture smoke for gate logic",
    ),
    "full": Phase6Config(
        preset="full",
        lm_models=("distilgpt2", "pythia_70m", "qwen2_0_5b_instruct"),
        encoder_models=("all_minilm_l6_v2", "bge_small_en_v1_5"),
        claim_level="actual open-LM and frozen-encoder validation result",
    ),
}


def _finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    vals = [float(r[key]) for r in rows if _finite(r.get(key))]
    return sum(vals) / len(vals) if vals else float("nan")


def _std(rows: list[dict[str, Any]], key: str) -> float:
    vals = [float(r[key]) for r in rows if _finite(r.get(key))]
    if len(vals) <= 1:
        return 0.0
    mean = sum(vals) / len(vals)
    var = sum((val - mean) ** 2 for val in vals) / (len(vals) - 1)
    return math.sqrt(var)


def _pearson(x: Any, y: Any) -> float:
    import numpy as np

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size < 2 or y.size < 2:
        return float("nan")
    sx = float(np.std(x))
    sy = float(np.std(y))
    if sx < 1e-12 or sy < 1e-12:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def rank_auc(labels: Any, scores: Any) -> float:
    import numpy as np

    y = np.asarray(labels, dtype=int)
    s = np.asarray(scores, dtype=float)
    pos = s[y == 1]
    neg = s[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    wins = 0.0
    total = 0
    for p in pos:
        wins += float(np.sum(p > neg)) + 0.5 * float(np.sum(p == neg))
        total += len(neg)
    return wins / max(total, 1)


def zscore(values: Any) -> Any:
    import numpy as np

    values = np.asarray(values, dtype=float)
    return (values - values.mean()) / (values.std() + 1e-9)


def fixture_rows() -> list[dict[str, Any]]:
    """Small deterministic rows used for local gate and report tests."""
    return [
        {
            "track": "open_lm_action_coupling",
            "condition": "fixture_base_lm",
            "model_id": "fixture/base-open-lm",
            "ok": 1,
            "n_items": 16,
            "geometry_action_r": 0.18,
            "label_geometry_gap": 0.12,
            "label_margin_lift": 0.15,
            "margin_auc": 0.69,
            "targeted_cue_lift": 0.09,
            "matched_control_lift": 0.02,
            "random_control_lift": 0.01,
            "neutral_cue_drift": 0.02,
            "cue_specificity": 0.07,
            "elapsed_seconds": 1.0,
        },
        {
            "track": "open_lm_action_coupling",
            "condition": "fixture_instruction_lm",
            "model_id": "fixture/instruction-open-lm",
            "ok": 1,
            "n_items": 16,
            "geometry_action_r": 0.31,
            "label_geometry_gap": 0.19,
            "label_margin_lift": 0.24,
            "margin_auc": 0.78,
            "targeted_cue_lift": 0.13,
            "matched_control_lift": 0.03,
            "random_control_lift": 0.01,
            "neutral_cue_drift": 0.03,
            "cue_specificity": 0.10,
            "elapsed_seconds": 1.0,
        },
        {
            "track": "frozen_encoder_metric_deformation",
            "condition": "fixture_minilm_encoder",
            "model_id": "fixture/minilm",
            "ok": 1,
            "n_items": 32,
            "raw_neighbor_precision": 0.46,
            "deformed_neighbor_precision": 0.68,
            "random_neighbor_precision": 0.49,
            "raw_value_margin": 0.08,
            "deformed_value_margin": 0.31,
            "random_value_margin": 0.11,
            "deformed_precision_lift": 0.22,
            "random_precision_lift": 0.03,
            "deformed_margin_lift": 0.23,
            "random_margin_lift": 0.03,
            "template_transfer_auc": 0.74,
            "off_target_drift": 0.04,
            "collapse_index": 0.07,
            "elapsed_seconds": 1.0,
        },
        {
            "track": "frozen_encoder_metric_deformation",
            "condition": "fixture_bge_encoder",
            "model_id": "fixture/bge-small",
            "ok": 1,
            "n_items": 32,
            "raw_neighbor_precision": 0.43,
            "deformed_neighbor_precision": 0.70,
            "random_neighbor_precision": 0.46,
            "raw_value_margin": 0.05,
            "deformed_value_margin": 0.34,
            "random_value_margin": 0.08,
            "deformed_precision_lift": 0.27,
            "random_precision_lift": 0.03,
            "deformed_margin_lift": 0.29,
            "random_margin_lift": 0.03,
            "template_transfer_auc": 0.78,
            "off_target_drift": 0.04,
            "collapse_index": 0.08,
            "elapsed_seconds": 1.0,
        },
    ]


def failed_row(track: str, condition: str, model_id: str, error: str) -> dict[str, Any]:
    return {
        "track": track,
        "condition": condition,
        "model_id": model_id,
        "ok": 0,
        "error": error[-500:],
    }


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_track: dict[str, dict[str, Any]] = {}
    for track in sorted({r["track"] for r in rows}):
        trows = [r for r in rows if r["track"] == track]
        conditions: dict[str, Any] = {}
        for condition in sorted({r["condition"] for r in trows}):
            crows = [r for r in trows if r["condition"] == condition]
            metrics = sorted(
                k
                for row in crows
                for k, v in row.items()
                if k not in {"track", "condition", "model_id", "error"}
                and isinstance(v, (int, float))
            )
            conditions[condition] = {
                "n": len(crows),
                "model_id": crows[0].get("model_id", condition),
                "ok": bool(_mean(crows, "ok") >= 0.5),
                "error": crows[0].get("error"),
                "metrics": {
                    metric: {"mean": _mean(crows, metric), "std": _std(crows, metric)}
                    for metric in sorted(set(metrics))
                },
            }
        by_track[track] = {"n_rows": len(trows), "conditions": conditions}
    gates = evaluate_gates(by_track)
    return {"n_rows": len(rows), "by_track": by_track, "gates": gates}


def _metric(by_track: dict[str, Any], track: str, condition: str, metric: str) -> float:
    return float(by_track[track]["conditions"][condition]["metrics"][metric]["mean"])


def _ok_conditions(by_track: dict[str, Any], track: str) -> list[str]:
    if track not in by_track:
        return []
    return [
        condition
        for condition, data in by_track[track]["conditions"].items()
        if bool(data.get("ok"))
    ]


def _mean_across(by_track: dict[str, Any], track: str, conditions: list[str], metric: str) -> float:
    vals = [
        _metric(by_track, track, condition, metric)
        for condition in conditions
        if metric in by_track[track]["conditions"][condition]["metrics"]
        and _finite(by_track[track]["conditions"][condition]["metrics"][metric]["mean"])
    ]
    return sum(vals) / len(vals) if vals else float("nan")


def _max_across(by_track: dict[str, Any], track: str, conditions: list[str], metric: str) -> float:
    vals = [
        _metric(by_track, track, condition, metric)
        for condition in conditions
        if metric in by_track[track]["conditions"][condition]["metrics"]
        and _finite(by_track[track]["conditions"][condition]["metrics"][metric]["mean"])
    ]
    return max(vals) if vals else float("nan")


def evaluate_gates(by_track: dict[str, Any]) -> dict[str, Any]:
    gates: dict[str, Any] = {}

    lm = "open_lm_action_coupling"
    if lm in by_track:
        ok = _ok_conditions(by_track, lm)
        mean_r = _mean_across(by_track, lm, ok, "geometry_action_r")
        mean_gap = _mean_across(by_track, lm, ok, "label_geometry_gap")
        mean_lift = _mean_across(by_track, lm, ok, "label_margin_lift")
        mean_auc = _mean_across(by_track, lm, ok, "margin_auc")
        max_specificity = _max_across(by_track, lm, ok, "cue_specificity")
        signal_count = sum(
            [
                _finite(mean_r) and mean_r >= 0.05,
                _finite(mean_gap) and mean_gap >= 0.05,
                _finite(mean_lift) and mean_lift >= 0.05,
                _finite(mean_auc) and mean_auc >= 0.60,
                _finite(max_specificity) and max_specificity >= 0.02,
            ]
        )
        gates[lm] = {
            "pass": len(ok) >= 2 and signal_count >= 3,
            "criteria": "at least two open LMs run; at least three signal tests clear weak positive thresholds",
            "ok_models": len(ok),
            "geometry_action_r": mean_r,
            "label_geometry_gap": mean_gap,
            "label_margin_lift": mean_lift,
            "margin_auc": mean_auc,
            "max_cue_specificity": max_specificity,
            "signal_count": signal_count,
            "claim": "actual open LMs show measured concern/action transport signals without proxy weights",
        }

    enc = "frozen_encoder_metric_deformation"
    if enc in by_track:
        ok = _ok_conditions(by_track, enc)
        margin_lift = _mean_across(by_track, enc, ok, "deformed_margin_lift")
        random_margin_lift = _mean_across(by_track, enc, ok, "random_margin_lift")
        precision_lift = _mean_across(by_track, enc, ok, "deformed_precision_lift")
        raw_precision = _mean_across(by_track, enc, ok, "raw_neighbor_precision")
        deformed_precision = _mean_across(by_track, enc, ok, "deformed_neighbor_precision")
        auc = _mean_across(by_track, enc, ok, "template_transfer_auc")
        drift = _mean_across(by_track, enc, ok, "off_target_drift")
        collapse = _mean_across(by_track, enc, ok, "collapse_index")
        gates[enc] = {
            "pass": (
                len(ok) >= 2
                and _finite(margin_lift)
                and margin_lift >= 0.12
                and _finite(random_margin_lift)
                and random_margin_lift <= max(0.06, margin_lift * 0.50)
                and _finite(deformed_precision)
                and _finite(raw_precision)
                and deformed_precision >= raw_precision - 0.01
                and _finite(auc)
                and auc >= 0.62
                and _finite(drift)
                and drift <= 0.10
                and _finite(collapse)
                and collapse <= 0.18
            ),
            "criteria": "two frozen encoders; value metric lifts held-out value margin, random labels stay low, transfer AUC positive, no collapse",
            "ok_models": len(ok),
            "deformed_margin_lift": margin_lift,
            "random_margin_lift": random_margin_lift,
            "deformed_precision_lift": precision_lift,
            "raw_neighbor_precision": raw_precision,
            "deformed_neighbor_precision": deformed_precision,
            "template_transfer_auc": auc,
            "off_target_drift": drift,
            "collapse_index": collapse,
            "claim": "a value-weighted metric deformation transports across actual frozen text encoders",
        }

    gates["all_pass"] = bool(gates) and all(v["pass"] for v in gates.values() if isinstance(v, dict))
    return gates


def run_suite(preset: str = "smoke", tracks: list[str] | None = None) -> dict[str, Any]:
    if preset not in PRESETS:
        raise ValueError(f"unknown preset {preset!r}")
    cfg = PRESETS[preset]
    track_list = tracks or TRACKS
    rows = [row for row in fixture_rows() if row["track"] in track_list]
    summary = summarize_rows(rows)
    return {
        "kind": "phase6_real_model_validation_fixture_suite",
        "manifest": {
            "preset": preset,
            "tracks": track_list,
            "lm_models": list(cfg.lm_models),
            "encoder_models": list(cfg.encoder_models),
            "claim_level": cfg.claim_level,
            "note": "Local fixture payload. Actual model payloads are produced by modal_l4_suite.py.",
        },
        "rows": rows,
        "summary": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", choices=sorted(PRESETS), default="smoke")
    parser.add_argument("--tracks", default=",".join(TRACKS))
    parser.add_argument("--out", type=Path, default=Path("artifacts/phase6_real_model_validation/smoke_suite.json"))
    args = parser.parse_args()
    tracks = [t.strip() for t in args.tracks.split(",") if t.strip()]
    payload = run_suite(args.preset, tracks=tracks)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["summary"]["gates"], indent=2, sort_keys=True))
    print(f"Wrote {payload['summary']['n_rows']} rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
