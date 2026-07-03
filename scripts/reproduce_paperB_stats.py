#!/usr/bin/env python3
"""Recompute Paper B aggregate statistics from committed CSV snapshots."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.summarize_reward_location_sweep import summarize as summarize_spatial
from scripts.summarize_semantic_concern_sweep import summarize as summarize_semantic

SPATIAL_CSV = Path("data/paper_b/reward_location_sweep_2026_07_02_rows.csv")
SEMANTIC_CSV = Path("data/paper_b/semantic_concern_sweep_2026_07_02_rows.csv")
OUT_JSON = Path("artifacts/paper_b/reproduced_stats_from_csv.json")

SPATIAL_FLOATS = {
    "reward_x",
    "reward_y",
    "final_loss",
    "coverage",
    "reward_z",
    "wrong_z_mean",
    "specificity_z",
    "reward_rank_percentile",
    "peak_error",
    "top10_com_error",
    "spatial_corr_reward_log_metric",
    "area_reward_z",
    "area_wrong_z_mean",
    "area_specificity_z",
    "area_reward_rank_percentile",
    "area_peak_error",
    "area_top10_com_error",
    "area_spatial_corr_reward_log_metric",
    "mean_area",
    "mean_stretch",
}
SPATIAL_INTS = {"seed", "side", "Ng"}

SEMANTIC_FLOATS = {
    "concern_weight",
    "final_loss",
    "target_margin",
    "target_margin_z",
    "specificity_z",
    "target_rank_percentile",
    "target_centroid_margin_z",
    "target_knn_purity_z",
    "target_effective_rank_z",
    "target_knn_purity",
    "target_f1",
    "accuracy",
}
SEMANTIC_INTS = {
    "seed",
    "target_idx",
    "train_per_class",
    "test_per_class",
    "steps",
    "batch_size",
    "geom_dim",
}


def _to_float(value: str) -> float:
    if value == "":
        return math.nan
    return float(value)


def _to_int(value: str) -> int:
    return int(float(value))


def load_spatial_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            parsed: dict[str, Any] = {}
            for key, value in row.items():
                if key in SPATIAL_FLOATS:
                    parsed[key] = _to_float(value)
                elif key in SPATIAL_INTS:
                    parsed[key] = _to_int(value)
                else:
                    parsed[key] = value
            parsed["reward_xy"] = [parsed.pop("reward_x"), parsed.pop("reward_y")]
            rows.append(parsed)
    return rows


def load_semantic_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            parsed: dict[str, Any] = {}
            for key, value in row.items():
                if key in SEMANTIC_FLOATS:
                    parsed[key] = _to_float(value)
                elif key in SEMANTIC_INTS:
                    parsed[key] = _to_int(value)
                else:
                    parsed[key] = value
            rows.append(parsed)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spatial-csv", type=Path, default=SPATIAL_CSV)
    parser.add_argument("--semantic-csv", type=Path, default=SEMANTIC_CSV)
    parser.add_argument("--out", type=Path, default=OUT_JSON)
    parser.add_argument("--target-se", type=float, default=0.02)
    args = parser.parse_args()

    spatial_rows = load_spatial_csv(args.spatial_csv)
    semantic_rows = load_semantic_csv(args.semantic_csv)
    spatial = summarize_spatial(spatial_rows, args.target_se)
    semantic = summarize_semantic({
        "manifest": {"target_bootstrap_se": args.target_se},
        "rows": semantic_rows,
    })

    payload = {
        "kind": "paper_b_reproduced_from_committed_csv",
        "spatial_csv": str(args.spatial_csv),
        "semantic_csv": str(args.semantic_csv),
        "spatial_summary": spatial,
        "semantic_summary": semantic,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, default=float) + "\n", encoding="utf-8")

    pooled_spatial = spatial["pooled_architecture_balanced"]
    pooled_semantic = semantic["pooled_family_balanced"]
    print(f"[paper-b-repro] wrote {args.out}")
    print(
        "[paper-b-repro] spatial pooled lift "
        f"{pooled_spatial['control_subtracted_lift_z']['mean']:+.4f}, "
        f"specificity {pooled_spatial['specificity_z']['mean']:+.4f}"
    )
    print(
        "[paper-b-repro] semantic pooled lift vs uniform "
        f"{pooled_semantic['margin_lift_vs_uniform']['mean']:+.4f}, "
        f"vs random {pooled_semantic['margin_lift_vs_random']['mean']:+.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
