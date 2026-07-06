"""Bootstrap CIs for Phase 6 semantic model-selection records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np

from experiments.structure_compatible_generalization.semantic_selection_control import (
    SelectionRecord,
    selection_records_from_dicts,
    summarize_selection_records,
)

BOOTSTRAP_JSON = Path(
    "experiments/structure_compatible_generalization/results/"
    "semantic_selection_bootstrap_2026_07_06.json"
)
BOOTSTRAP_MD = Path(
    "experiments/structure_compatible_generalization/results/"
    "semantic_selection_bootstrap_2026_07_06.md"
)
BOOTSTRAP_FIGURE = Path(
    "papers/structure_compatible_generalization/figures/"
    "fig13_semantic_selection_bootstrap_ci.png"
)

MetricFn = Callable[[dict[str, dict[str, Any]], dict[str, Any]], float]


def _fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def _lookup(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["selector"]: row for row in summary["by_selector"]}


def _metric_fns() -> dict[str, MetricFn]:
    def selected(selector: str) -> MetricFn:
        return lambda lookup, _summary: float(lookup[selector]["mean_selected_ood"])

    return {
        "learned_selected_ood": selected("compatibility_discovered"),
        "random_selected_ood": selected("random_candidate"),
        "id_selected_ood": selected("id_validation_accuracy"),
        "train_selected_ood": selected("train_accuracy"),
        "wrong_selected_ood": selected("compatibility_wrong"),
        "true_selected_ood": selected("compatibility_true"),
        "learned_regret": lambda lookup, _s: float(
            lookup["compatibility_discovered"]["mean_regret"]
        ),
        "learned_lift_vs_random": lambda lookup, _s: float(
            lookup["compatibility_discovered"]["mean_selected_ood"]
            - lookup["random_candidate"]["mean_selected_ood"]
        ),
        "learned_lift_vs_id": lambda lookup, _s: float(
            lookup["compatibility_discovered"]["mean_selected_ood"]
            - lookup["id_validation_accuracy"]["mean_selected_ood"]
        ),
        "learned_lift_vs_wrong": lambda lookup, _s: float(
            lookup["compatibility_discovered"]["mean_selected_ood"]
            - lookup["compatibility_wrong"]["mean_selected_ood"]
        ),
        "accepted_rate": lambda _lookup, summary: float(bool(summary["gates"]["accepted"])),
    }


def _metrics(records: list[SelectionRecord]) -> dict[str, float]:
    summary = summarize_selection_records(records)
    lookup = _lookup(summary)
    return {name: fn(lookup, summary) for name, fn in _metric_fns().items()}


def _groups_by_zoo(records: list[SelectionRecord]) -> dict[str, list[SelectionRecord]]:
    groups: dict[str, list[SelectionRecord]] = {}
    for record in records:
        groups.setdefault(record.zoo_id, []).append(record)
    return groups


def bootstrap_selection_records(
    records: list[SelectionRecord],
    *,
    reps: int = 1000,
    seed: int = 20260706,
) -> dict[str, Any]:
    groups = _groups_by_zoo(records)
    zoo_ids = sorted(groups)
    rng = np.random.default_rng(seed)
    values: dict[str, list[float]] = {name: [] for name in _metric_fns()}
    for _rep in range(reps):
        sampled = rng.choice(zoo_ids, size=len(zoo_ids), replace=True)
        sample_records = [record for zoo_id in sampled for record in groups[str(zoo_id)]]
        sample_values = _metrics(sample_records)
        for name, value in sample_values.items():
            values[name].append(float(value))
    return {
        name: {
            "mean": float(np.mean(metric_values)),
            "ci95_low": float(np.percentile(metric_values, 2.5)),
            "ci95_high": float(np.percentile(metric_values, 97.5)),
        }
        for name, metric_values in values.items()
    }


def build_bootstrap_report(
    payload: dict[str, Any],
    *,
    reps: int = 1000,
    seed: int = 20260706,
) -> dict[str, Any]:
    records = selection_records_from_dicts(payload["selection_records"])
    point_summary = summarize_selection_records(records)
    point_metrics = _metrics(records)
    ci = bootstrap_selection_records(records, reps=reps, seed=seed)
    return {
        "run_id": "semantic_selection_bootstrap_2026_07_06",
        "bootstrap_reps": reps,
        "bootstrap_unit": "selection_zoo",
        "n_zoos": len(_groups_by_zoo(records)),
        "n_records": len(records),
        "manifest": payload.get("manifest", {}),
        "point_summary": point_summary,
        "point_metrics": point_metrics,
        "bootstrap_ci95": ci,
        "allowed_claim": (
            "For the regenerated Phase 6 semantic-selection payload, learned "
            "compatibility selects higher OOD candidates than random, train, ID, "
            "and wrong-compatibility selectors under a zoo-level bootstrap."
        ),
        "non_claims": [
            "Not universal OOD certification.",
            "Not open-world semantic robustness.",
            "Not a replacement for rerunning all earlier SCG phases.",
        ],
    }


def write_report(report: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    ci = report["bootstrap_ci95"]
    point = report["point_metrics"]
    lines = [
        "# Phase 6 Semantic Selection Bootstrap",
        "",
        "Date: 2026-07-06",
        "",
        "## Setup",
        "",
        f"- Bootstrap unit: `{report['bootstrap_unit']}`",
        f"- Zoos: {report['n_zoos']}",
        f"- Selection records: {report['n_records']}",
        f"- Bootstrap reps: {report['bootstrap_reps']}",
        "",
        "## Metrics",
        "",
        "| Metric | Point | 95% CI |",
        "| --- | ---: | ---: |",
    ]
    for name in [
        "learned_selected_ood",
        "random_selected_ood",
        "id_selected_ood",
        "train_selected_ood",
        "wrong_selected_ood",
        "true_selected_ood",
        "learned_regret",
        "learned_lift_vs_random",
        "learned_lift_vs_id",
        "learned_lift_vs_wrong",
        "accepted_rate",
    ]:
        entry = ci[name]
        lines.append(
            f"| `{name}` | {_fmt(point[name])} | "
            f"[{_fmt(entry['ci95_low'])}, {_fmt(entry['ci95_high'])}] |"
        )
    lines.extend(["", "## Interpretation", "", report["allowed_claim"]])
    out.write_text("\n".join(lines) + "\n")


def write_figure(report: dict[str, Any], out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: PLC0415

    metric_names = [
        "wrong_selected_ood",
        "random_selected_ood",
        "id_selected_ood",
        "learned_selected_ood",
        "true_selected_ood",
    ]
    labels = [
        "Wrong",
        "Random",
        "ID",
        "Learned",
        "True",
    ]
    colors = ["#9a3412", "#475569", "#64748b", "#0f766e", "#2563eb"]
    point = report["point_metrics"]
    ci = report["bootstrap_ci95"]
    y_positions = np.arange(len(metric_names))
    values = np.array([point[name] for name in metric_names], dtype=float)
    lower = np.array([ci[name]["ci95_low"] for name in metric_names], dtype=float)
    upper = np.array([ci[name]["ci95_high"] for name in metric_names], dtype=float)
    xerr = np.vstack([values - lower, upper - values])

    out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5.6, 2.7))
    ax.errorbar(
        values,
        y_positions,
        xerr=xerr,
        fmt="o",
        markersize=5.5,
        linewidth=1.4,
        capsize=3,
        color="#111827",
        ecolor="#334155",
    )
    for y, value, color in zip(y_positions, values, colors, strict=True):
        ax.scatter(value, y, s=48, color=color, zorder=3)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels)
    ax.set_xlim(0.72, 1.01)
    ax.set_xlabel("Selected OOD accuracy")
    ax.set_title("Phase 6 semantic selection, zoo-bootstrap 95% CI")
    ax.grid(axis="x", color="#d1d5db", linewidth=0.8, alpha=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", type=Path)
    parser.add_argument("--out-root", type=Path, default=Path("."))
    parser.add_argument("--bootstrap-reps", type=int, default=1000)
    args = parser.parse_args()
    payload = json.loads(args.payload.read_text())
    report = build_bootstrap_report(payload, reps=args.bootstrap_reps)
    json_path = args.out_root / BOOTSTRAP_JSON
    md_path = args.out_root / BOOTSTRAP_MD
    figure_path = args.out_root / BOOTSTRAP_FIGURE
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_report(report, md_path)
    write_figure(report, figure_path)
    print(json_path)
    print(md_path)
    print(figure_path)


if __name__ == "__main__":
    main()
