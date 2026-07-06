"""Tie-break stress tests for Phase 6 semantic selection."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np

from experiments.structure_compatible_generalization.core import (
    DiagnosticRow,
    row_predictor_values,
    rows_from_records,
)
from experiments.structure_compatible_generalization.semantic_selection_control import (
    SELECTION_PREDICTORS,
    id_equivalent_candidates,
    zoo_key,
)

TIEBREAK_JSON = Path(
    "experiments/structure_compatible_generalization/results/"
    "semantic_selection_tiebreak_stress_2026_07_06.json"
)
TIEBREAK_MD = Path(
    "experiments/structure_compatible_generalization/results/"
    "semantic_selection_tiebreak_stress_2026_07_06.md"
)

SELECTORS = ("random_candidate", "ood_oracle", *SELECTION_PREDICTORS)
MetricFn = Callable[[dict[str, dict[str, float]]], float]


def _fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def _best_by_metric(candidates: list[DiagnosticRow], metric: str) -> list[DiagnosticRow]:
    if metric == "ood_accuracy":
        best = max(row.ood_accuracy for row in candidates)
        return [row for row in candidates if row.ood_accuracy == best]
    scored: list[tuple[float, DiagnosticRow]] = []
    for row in candidates:
        values = row_predictor_values(row)
        if metric not in values:
            continue
        value = values[metric]
        if math.isfinite(value):
            scored.append((value, row))
    if not scored:
        return []
    best = max(value for value, _row in scored)
    return [row for value, row in scored if value == best]


def _candidate_groups(rows: list[DiagnosticRow]) -> dict[str, list[DiagnosticRow]]:
    groups: dict[str, list[DiagnosticRow]] = {}
    for row in rows:
        if row.domain != "semantic_retrieval_frozen_encoder":
            continue
        groups.setdefault(zoo_key(row), []).append(row)
    return {
        zoo_id: candidates
        for zoo_id, zoo_rows in sorted(groups.items())
        if (
            candidates := id_equivalent_candidates(
                zoo_rows,
                train_floor=0.95,
                id_band=0.02,
                min_candidates=3,
            )
        )
    }


def _selected_rows(candidates: list[DiagnosticRow], selector: str) -> list[DiagnosticRow]:
    if selector == "random_candidate":
        return candidates
    if selector == "ood_oracle":
        return _best_by_metric(candidates, "ood_accuracy")
    return _best_by_metric(candidates, selector)


def _selected_ood(
    selected: list[DiagnosticRow],
    *,
    mode: str,
    rng: np.random.Generator,
) -> float:
    if not selected:
        return float("nan")
    values = [row.ood_accuracy for row in selected]
    if mode == "mean_ties":
        return float(mean(values))
    if mode == "worst_tie":
        return float(min(values))
    if mode == "random_tie":
        return float(values[int(rng.integers(0, len(values)))])
    raise ValueError(f"unknown tie-break mode: {mode}")


def selector_rows_for_mode(
    rows: list[DiagnosticRow],
    *,
    mode: str,
    seed: int = 20260706,
) -> list[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    out: list[dict[str, Any]] = []
    for zoo_id, candidates in _candidate_groups(rows).items():
        oracle_ood = max(row.ood_accuracy for row in candidates)
        random_mean_ood = mean(row.ood_accuracy for row in candidates)
        encoder_key = str(candidates[0].metadata.get("encoder_key", "unknown"))
        threshold = float(candidates[0].metadata.get("config", {}).get("discovered_threshold", 0.0))
        for selector in SELECTORS:
            selected = _selected_rows(candidates, selector)
            if not selected:
                continue
            selected_ood = _selected_ood(selected, mode=mode, rng=rng)
            out.append(
                {
                    "zoo_id": zoo_id,
                    "selector": selector,
                    "tie_mode": mode,
                    "encoder_key": encoder_key,
                    "discovered_threshold": threshold,
                    "n_candidates": len(candidates),
                    "tied_count": len(selected),
                    "selected_ood": selected_ood,
                    "oracle_ood": oracle_ood,
                    "random_mean_ood": random_mean_ood,
                    "regret": oracle_ood - selected_ood,
                    "lift_vs_random": selected_ood - random_mean_ood,
                }
            )
    return out


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["selector"]), []).append(row)
    by_selector = []
    for selector, group in sorted(grouped.items()):
        by_selector.append(
            {
                "selector": selector,
                "n_zoos": len(group),
                "mean_candidates": mean(float(row["n_candidates"]) for row in group),
                "mean_tied_count": mean(float(row["tied_count"]) for row in group),
                "mean_selected_ood": mean(float(row["selected_ood"]) for row in group),
                "mean_regret": mean(float(row["regret"]) for row in group),
                "mean_lift_vs_random": mean(float(row["lift_vs_random"]) for row in group),
            }
        )
    lookup = {row["selector"]: row for row in by_selector}
    learned = lookup.get("compatibility_discovered", {})
    random_row = lookup.get("random_candidate", {})
    id_row = lookup.get("id_validation_accuracy", {})
    train_row = lookup.get("train_accuracy", {})
    wrong_row = lookup.get("compatibility_wrong", {})
    gates = {
        "min_zoo_count": bool(float(learned.get("n_zoos", 0.0)) >= 20.0),
        "beats_random_candidate": bool(
            learned
            and random_row
            and float(learned["mean_selected_ood"])
            > float(random_row["mean_selected_ood"]) + 0.05
        ),
        "beats_id_validation": bool(
            learned
            and id_row
            and float(learned["mean_selected_ood"])
            > float(id_row["mean_selected_ood"]) + 0.05
        ),
        "beats_train_accuracy": bool(
            learned
            and train_row
            and float(learned["mean_selected_ood"])
            > float(train_row["mean_selected_ood"]) + 0.05
        ),
        "wrong_control_fails": bool(
            wrong_row
            and random_row
            and float(wrong_row["mean_selected_ood"])
            <= float(random_row["mean_selected_ood"]) + 0.02
        ),
    }
    gates["accepted"] = all(gates.values())
    return {"by_selector": by_selector, "gates": gates}


def _metric_fns() -> dict[str, MetricFn]:
    def selected(selector: str) -> MetricFn:
        return lambda lookup: float(lookup[selector]["mean_selected_ood"])

    return {
        "learned_selected_ood": selected("compatibility_discovered"),
        "random_selected_ood": selected("random_candidate"),
        "id_selected_ood": selected("id_validation_accuracy"),
        "wrong_selected_ood": selected("compatibility_wrong"),
        "learned_regret": lambda lookup: float(lookup["compatibility_discovered"]["mean_regret"]),
        "learned_lift_vs_random": lambda lookup: float(
            lookup["compatibility_discovered"]["mean_selected_ood"]
            - lookup["random_candidate"]["mean_selected_ood"]
        ),
        "learned_lift_vs_id": lambda lookup: float(
            lookup["compatibility_discovered"]["mean_selected_ood"]
            - lookup["id_validation_accuracy"]["mean_selected_ood"]
        ),
        "learned_lift_vs_wrong": lambda lookup: float(
            lookup["compatibility_discovered"]["mean_selected_ood"]
            - lookup["compatibility_wrong"]["mean_selected_ood"]
        ),
    }


def _metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    summary = _summary(rows)
    lookup = {row["selector"]: row for row in summary["by_selector"]}
    metrics = {
        name: fn(lookup)
        for name, fn in _metric_fns().items()
        if name != "accepted"
    }
    metrics["accepted"] = float(bool(summary["gates"]["accepted"]))
    return metrics


def _bootstrap_rows(
    mode_rows: list[dict[str, Any]],
    *,
    reps: int,
    seed: int,
) -> dict[str, dict[str, float]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in mode_rows:
        groups.setdefault(str(row["zoo_id"]), []).append(row)
    zoo_ids = sorted(groups)
    rng = np.random.default_rng(seed)
    values: dict[str, list[float]] = {name: [] for name in _metrics(mode_rows)}
    for _rep in range(reps):
        sampled = rng.choice(zoo_ids, size=len(zoo_ids), replace=True)
        rows = [row for zoo_id in sampled for row in groups[str(zoo_id)]]
        metrics = _metrics(rows)
        for name, value in metrics.items():
            values[name].append(float(value))
    return {
        name: {
            "mean": float(np.mean(metric_values)),
            "ci95_low": float(np.percentile(metric_values, 2.5)),
            "ci95_high": float(np.percentile(metric_values, 97.5)),
        }
        for name, metric_values in values.items()
    }


def build_tiebreak_report(
    payload: dict[str, Any],
    *,
    reps: int = 1000,
    seed: int = 20260706,
) -> dict[str, Any]:
    rows = rows_from_records(payload["rows"])
    mode_reports: dict[str, Any] = {}
    for offset, mode in enumerate(("mean_ties", "worst_tie", "random_tie")):
        mode_rows = selector_rows_for_mode(rows, mode=mode, seed=seed + offset)
        mode_reports[mode] = {
            "summary": _summary(mode_rows),
            "point_metrics": _metrics(mode_rows),
            "bootstrap_ci95": _bootstrap_rows(
                mode_rows,
                reps=reps,
                seed=seed + 1000 + offset,
            ),
        }
    return {
        "run_id": "semantic_selection_tiebreak_stress_2026_07_06",
        "bootstrap_reps": reps,
        "bootstrap_unit": "selection_zoo",
        "tie_modes": sorted(mode_reports),
        "manifest": payload.get("manifest", {}),
        "modes": mode_reports,
        "allowed_claim": (
            "Phase 6 learned compatibility remains stress-tested under mean-tie, "
            "worst-tie, and random-tie selector interpretations."
        ),
        "non_claims": [
            "Not a replacement for publishing row-level payloads.",
            "Not universal OOD certification.",
        ],
    }


def write_report(report: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 6 Semantic Selection Tie-Break Stress",
        "",
        "Date: 2026-07-06",
        "",
        f"- Bootstrap unit: `{report['bootstrap_unit']}`",
        f"- Bootstrap reps: {report['bootstrap_reps']}",
        "",
        "| Tie mode | Learned OOD | Learned-random | Learned-ID | Learned-wrong | Accepted? |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for mode in ("mean_ties", "worst_tie", "random_tie"):
        metrics = report["modes"][mode]["point_metrics"]
        ci = report["modes"][mode]["bootstrap_ci95"]
        lines.append(
            f"| `{mode}` | {_fmt(metrics['learned_selected_ood'])} "
            f"[{_fmt(ci['learned_selected_ood']['ci95_low'])}, "
            f"{_fmt(ci['learned_selected_ood']['ci95_high'])}] | "
            f"{_fmt(metrics['learned_lift_vs_random'])} "
            f"[{_fmt(ci['learned_lift_vs_random']['ci95_low'])}, "
            f"{_fmt(ci['learned_lift_vs_random']['ci95_high'])}] | "
            f"{_fmt(metrics['learned_lift_vs_id'])} "
            f"[{_fmt(ci['learned_lift_vs_id']['ci95_low'])}, "
            f"{_fmt(ci['learned_lift_vs_id']['ci95_high'])}] | "
            f"{_fmt(metrics['learned_lift_vs_wrong'])} "
            f"[{_fmt(ci['learned_lift_vs_wrong']['ci95_low'])}, "
            f"{_fmt(ci['learned_lift_vs_wrong']['ci95_high'])}] | "
            f"{'PASS' if metrics['accepted'] else 'FAIL'} |"
        )
    lines.extend(["", "## Interpretation", "", report["allowed_claim"]])
    out.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", type=Path)
    parser.add_argument("--out-root", type=Path, default=Path("."))
    parser.add_argument("--bootstrap-reps", type=int, default=1000)
    args = parser.parse_args()
    payload = json.loads(args.payload.read_text())
    report = build_tiebreak_report(payload, reps=args.bootstrap_reps)
    json_path = args.out_root / TIEBREAK_JSON
    md_path = args.out_root / TIEBREAK_MD
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_report(report, md_path)
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
