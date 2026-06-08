#!/usr/bin/env python3
"""Summaries for matched-context patching replication payloads."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_payloads(paths: list[Path]) -> list[dict[str, Any]]:
    payloads = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            payloads.append(json.load(handle))
    return payloads


def replication_rows(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for payload in payloads:
        manifest = payload["manifest"]
        for row in payload["specificity_rows"]:
            rows.append(
                {
                    "model_id": manifest["model_id"],
                    "context_variant_index": manifest["context_variant_index"],
                    "seed": manifest["seed"],
                    "role": row["role"],
                    "layer": row["layer"],
                    "kind": row["kind"],
                    "pair": row["pair"],
                    "target_mean_target_margin_delta": row[
                        "target_mean_target_margin_delta"
                    ],
                    "target_advantage_over_best_control": row[
                        "target_advantage_over_best_control"
                    ],
                    "target_robust_pass": row["target_robust_pass"],
                    "specific_target_pass": row["specific_target_pass"],
                    "best_control_mode": row["best_control_mode"],
                    "best_control_mean_target_margin_delta": row[
                        "best_control_mean_target_margin_delta"
                    ],
                }
            )
    return sorted(
        rows,
        key=lambda row: (
            str(row["model_id"]),
            int(row["context_variant_index"]),
            int(row["seed"]),
            int(row["layer"]),
            str(row["kind"]),
            str(row["pair"]),
        ),
    )


def _mean(values: list[float]) -> float:
    if not values:
        raise ValueError("Cannot take mean of an empty list")
    return sum(values) / len(values)


def summarize_by_layer_pair(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            row["model_id"],
            row["layer"],
            row["kind"],
            row["pair"],
        )
        grouped[key].append(row)

    summaries = []
    for (model_id, layer, kind, pair), group in grouped.items():
        summaries.append(
            {
                "model_id": model_id,
                "layer": layer,
                "kind": kind,
                "pair": pair,
                "specific_pass_count": sum(
                    1 for row in group if row["specific_target_pass"]
                ),
                "robust_pass_count": sum(1 for row in group if row["target_robust_pass"]),
                "total": len(group),
                "mean_target_margin_delta": _mean(
                    [float(row["target_mean_target_margin_delta"]) for row in group]
                ),
                "mean_target_advantage_over_best_control": _mean(
                    [
                        float(row["target_advantage_over_best_control"])
                        for row in group
                    ]
                ),
            }
        )
    return sorted(
        summaries,
        key=lambda row: (
            str(row["model_id"]),
            int(row["layer"]),
            str(row["kind"]),
            str(row["pair"]),
        ),
    )


def summarize_by_variant_pair(
    rows: list[dict[str, Any]],
    *,
    layer: int,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if int(row["layer"]) != layer:
            continue
        key = (
            row["model_id"],
            row["context_variant_index"],
            row["kind"],
            row["pair"],
        )
        grouped[key].append(row)

    summaries = []
    for (model_id, variant, kind, pair), group in grouped.items():
        summaries.append(
            {
                "model_id": model_id,
                "context_variant_index": variant,
                "layer": layer,
                "kind": kind,
                "pair": pair,
                "specific_pass_count": sum(
                    1 for row in group if row["specific_target_pass"]
                ),
                "total": len(group),
                "mean_target_margin_delta": _mean(
                    [float(row["target_mean_target_margin_delta"]) for row in group]
                ),
                "mean_target_advantage_over_best_control": _mean(
                    [
                        float(row["target_advantage_over_best_control"])
                        for row in group
                    ]
                ),
            }
        )
    return sorted(
        summaries,
        key=lambda row: (
            str(row["model_id"]),
            int(row["context_variant_index"]),
            str(row["kind"]),
            str(row["pair"]),
        ),
    )


def max_abs_source_noop_delta(payloads: list[dict[str, Any]]) -> float:
    deltas = [
        abs(float(row["mean_target_margin_delta"]))
        for payload in payloads
        for row in payload["aggregate_rows"]
        if row["patch_mode"] == "source_noop"
    ]
    return max(deltas) if deltas else 0.0


def public_summary(payloads: list[dict[str, Any]], *, variant_layer: int) -> dict[str, Any]:
    rows = replication_rows(payloads)
    return {
        "payload_count": len(payloads),
        "max_abs_source_noop_delta": max_abs_source_noop_delta(payloads),
        "by_layer_pair": summarize_by_layer_pair(rows),
        "by_variant_pair": summarize_by_variant_pair(rows, layer=variant_layer),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payloads", nargs="+", type=Path)
    parser.add_argument("--variant-layer", type=int, default=5)
    args = parser.parse_args()

    payloads = load_payloads(args.payloads)
    print(
        json.dumps(
            public_summary(payloads, variant_layer=args.variant_layer),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
