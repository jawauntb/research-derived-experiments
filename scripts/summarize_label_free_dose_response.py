#!/usr/bin/env python3
"""Summarize label-free dose-response payloads as public-safe Markdown tables."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any


JsonRow = dict[str, Any]


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def fmt_number(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


def fmt_rate(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def artifact_label(path: Path, manifest: JsonRow) -> str:
    seed = manifest.get("seed")
    return f"seed {seed}" if seed is not None else path.stem


def load_payload(path: Path) -> JsonRow:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object payload in {path}")
    return payload


def manifest_rows(payloads: list[tuple[Path, JsonRow]]) -> list[JsonRow]:
    rows = []
    for path, payload in payloads:
        manifest = payload["manifest"]
        rows.append(
            {
                "artifact": artifact_label(path, manifest),
                "model": manifest["model_id"],
                "seed": manifest["seed"],
                "surface": manifest.get("patch_vector_surface", "hidden_state"),
                "injection_layers": ",".join(map(str, manifest["injection_layers"])),
                "readout_layers": ",".join(map(str, manifest["readout_layers"])),
                "alphas": ",".join(map(str, manifest["patch_alphas"])),
                "regimes": ",".join(manifest["patch_text_regimes"]),
                "pair_set": manifest["pair_set"],
                "baseline_n": manifest["baseline_sample_count"],
                "pairs": len(manifest["pairs"]),
            }
        )
    return rows


def source_noop_rows(payloads: list[tuple[Path, JsonRow]]) -> list[JsonRow]:
    grouped: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    for path, payload in payloads:
        manifest = payload["manifest"]
        label = artifact_label(path, manifest)
        for row in payload["aggregate_rows"]:
            if row["patch_text_regime"] != "definition":
                continue
            if row["patch_mode"] != "source_noop":
                continue
            key = (
                label,
                row.get("patch_vector_surface", "hidden_state"),
                row["injection_layer"],
                row["readout_layer"],
                row.get("patch_alpha", 1.0),
            )
            grouped[key].append(abs(float(row["mean_target_margin_delta"])))

    rows = []
    for (label, surface, injection, readout, alpha), values in sorted(grouped.items()):
        rows.append(
            {
                "artifact": label,
                "surface": surface,
                "cell": f"{injection} -> {readout}",
                "alpha": alpha,
                "rows": len(values),
                "max_abs_delta": max(values),
                "mean_abs_delta": mean(values),
            }
        )
    return rows


def all_pair_rows(payloads: list[tuple[Path, JsonRow]], regime: str) -> list[JsonRow]:
    grouped: dict[tuple[Any, ...], list[JsonRow]] = defaultdict(list)
    for path, payload in payloads:
        manifest = payload["manifest"]
        label = artifact_label(path, manifest)
        for row in payload["specificity_rows"]:
            if row["patch_text_regime"] != regime:
                continue
            key = (
                label,
                row["injection_layer"],
                row["readout_layer"],
                row.get("patch_alpha", 1.0),
            )
            grouped[key].append(row)

    rows = []
    for (label, injection, readout, alpha), group in sorted(grouped.items()):
        deltas = [float(row["target_mean_target_margin_delta"]) for row in group]
        advantages = [
            float(row["target_advantage_over_best_control"]) for row in group
        ]
        passes = sum(1 for row in group if row["specific_target_pass"])
        rows.append(
            {
                "artifact": label,
                "cell": f"{injection} -> {readout}",
                "alpha": alpha,
                "passes": passes,
                "total": len(group),
                "pass_rate": passes / len(group),
                "mean_delta": mean(deltas),
                "median_delta": median(deltas),
                "mean_advantage": mean(advantages),
                "median_advantage": median(advantages),
            }
        )
    return rows


def by_kind_rows(payloads: list[tuple[Path, JsonRow]], regime: str) -> list[JsonRow]:
    keep_kinds = {
        "positive",
        "source_family",
        "generic_control",
        "baseline_same_category",
        "baseline_cross_category",
    }
    rows = []
    for path, payload in payloads:
        manifest = payload["manifest"]
        label = artifact_label(path, manifest)
        for row in payload.get("dose_response_summaries", []):
            if row["patch_text_regime"] != regime:
                continue
            if row["kind"] not in keep_kinds:
                continue
            rows.append(
                {
                    "artifact": label,
                    "kind": row["kind"],
                    "cell": f"{row['injection_layer']} -> {row['readout_layer']}",
                    "alpha": row["patch_alpha"],
                    "passes": row["specific_pass_count"],
                    "total": row["count"],
                    "pass_rate": row["specific_pass_rate"],
                    "mean_delta": row["mean_target_margin_delta"],
                    "mean_advantage": row["mean_advantage_over_best_control"],
                }
            )
    return sorted(
        rows,
        key=lambda row: (
            row["artifact"],
            row["cell"],
            float(row["alpha"]),
            row["kind"],
        ),
    )


def baseline_percentile_rows(
    payloads: list[tuple[Path, JsonRow]],
    regime: str,
) -> list[JsonRow]:
    rows = []
    for path, payload in payloads:
        manifest = payload["manifest"]
        label = artifact_label(path, manifest)
        for row in payload.get("transfer_baseline_summaries", []):
            if row["patch_text_regime"] != regime:
                continue
            rows.append(
                {
                    "artifact": label,
                    "kind": row["kind"],
                    "count": row["count"],
                    "passes": row["specific_pass_count"],
                    "pass_rate": row["specific_pass_rate"],
                    "mean_delta": row["mean_target_margin_delta"],
                    "mean_advantage": row["mean_advantage_over_best_control"],
                    "median_advantage": row.get("median_advantage_over_best_control"),
                    "mean_percentile": row.get(
                        "mean_advantage_percentile_vs_baseline"
                    ),
                    "max_percentile": row.get(
                        "max_advantage_percentile_vs_baseline"
                    ),
                }
            )
    return rows


def table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def render_manifest(rows: list[JsonRow]) -> str:
    return table(
        [
            "Artifact",
            "Model",
            "Seed",
            "Surface",
            "Injection layers",
            "Readout",
            "Alphas",
            "Regimes",
            "Baseline N",
            "Pairs",
        ],
        [
            [
                row["artifact"],
                row["model"],
                str(row["seed"]),
                row["surface"],
                row["injection_layers"],
                row["readout_layers"],
                row["alphas"],
                row["regimes"],
                str(row["baseline_n"]),
                str(row["pairs"]),
            ]
            for row in rows
        ],
    )


def render_source_noop(rows: list[JsonRow]) -> str:
    return table(
        [
            "Artifact",
            "Surface",
            "Cell",
            "Alpha",
            "Rows",
            "Max abs source-noop delta",
            "Mean abs source-noop delta",
        ],
        [
            [
                row["artifact"],
                row["surface"],
                row["cell"],
                fmt_number(float(row["alpha"])),
                str(row["rows"]),
                fmt_number(row["max_abs_delta"]),
                fmt_number(row["mean_abs_delta"]),
            ]
            for row in rows
        ],
    )


def render_all_pair(rows: list[JsonRow]) -> str:
    return table(
        [
            "Artifact",
            "Cell",
            "Alpha",
            "Specific passes",
            "Pass rate",
            "Mean delta",
            "Median delta",
            "Mean advantage",
            "Median advantage",
        ],
        [
            [
                row["artifact"],
                row["cell"],
                fmt_number(float(row["alpha"])),
                f"{row['passes']}/{row['total']}",
                fmt_rate(row["pass_rate"]),
                fmt_number(row["mean_delta"]),
                fmt_number(row["median_delta"]),
                fmt_number(row["mean_advantage"]),
                fmt_number(row["median_advantage"]),
            ]
            for row in rows
        ],
    )


def render_by_kind(rows: list[JsonRow]) -> str:
    return table(
        [
            "Artifact",
            "Cell",
            "Alpha",
            "Kind",
            "Specific passes",
            "Pass rate",
            "Mean delta",
            "Mean advantage",
        ],
        [
            [
                row["artifact"],
                row["cell"],
                fmt_number(float(row["alpha"])),
                row["kind"],
                f"{row['passes']}/{row['total']}",
                fmt_rate(row["pass_rate"]),
                fmt_number(row["mean_delta"]),
                fmt_number(row["mean_advantage"]),
            ]
            for row in rows
        ],
    )


def render_baseline_percentiles(rows: list[JsonRow]) -> str:
    return table(
        [
            "Artifact",
            "Kind",
            "Count",
            "Specific passes",
            "Pass rate",
            "Mean delta",
            "Mean advantage",
            "Median advantage",
            "Mean advantage percentile",
            "Max advantage percentile",
        ],
        [
            [
                row["artifact"],
                row["kind"],
                str(row["count"]),
                f"{row['passes']}/{row['count']}",
                fmt_rate(row["pass_rate"]),
                fmt_number(row["mean_delta"]),
                fmt_number(row["mean_advantage"]),
                fmt_number(row["median_advantage"]),
                fmt_rate(row["mean_percentile"]),
                fmt_rate(row["max_percentile"]),
            ]
            for row in rows
        ],
    )


def render_markdown(paths: list[Path]) -> str:
    payloads = [(path, load_payload(path)) for path in paths]
    sections = [
        ("Manifest Sanity", render_manifest(manifest_rows(payloads))),
        ("Source-Noop Identity Gate", render_source_noop(source_noop_rows(payloads))),
        (
            "All-Pair Definition Dose Response",
            render_all_pair(all_pair_rows(payloads, "definition")),
        ),
        (
            "All-Pair Neutral Dose Response",
            render_all_pair(all_pair_rows(payloads, "neutral")),
        ),
        (
            "By-Kind Definition Dose Response",
            render_by_kind(by_kind_rows(payloads, "definition")),
        ),
        (
            "Definition Focus-vs-Baseline Percentiles",
            render_baseline_percentiles(
                baseline_percentile_rows(payloads, "definition")
            ),
        ),
    ]
    return "\n\n".join(f"## {title}\n\n{body}" for title, body in sections)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", nargs="+", type=Path)
    args = parser.parse_args()
    print(render_markdown(args.payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
