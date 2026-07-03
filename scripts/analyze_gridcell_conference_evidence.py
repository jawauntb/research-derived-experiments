#!/usr/bin/env python3
"""Export conference-review evidence from the Paper A Modal grid-cell sweep.

The input is the raw Modal JSON produced by
`experiments/grid_cell_weakness/modal_grid_cell_weakness_sweep.py`. The script
keeps reviewer-facing statistics out of the PDF generator: it writes per-cell
CSV, aggregate bootstrap CSVs, a within-toroidal analysis CSV, optional topology
robustness summaries when the raw JSON contains them, and a compact Markdown
appendix that the PDF builder can quote.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable


DEFAULT_RAW = Path("artifacts/grid_cell_weakness/grid_cell_weakness_sweep_2026_07_02_seed32.json")
DEFAULT_OUT_DIR = Path("experiments/grid_cell_weakness/results")
DEFAULT_DATE = "2026_07_02"
DEFAULT_BOOTSTRAP_SAMPLES = 5000
BOOTSTRAP_SEED = 20260702

CONDITION_ORDER = ["full_translation", "partial_translation", "random_shift", "none", "wrong_group"]
CONTINUOUS_METRICS = [
    ("weakness_translation", "weakness"),
    ("toroidal_score", "toroidal score"),
    ("fourier_pr", "Fourier PR"),
    ("id_accuracy", "ID accuracy"),
    ("ood_accuracy", "OOD accuracy @max arena"),
    ("final_loss", "final loss"),
    ("coverage", "coverage"),
]


@dataclass(frozen=True)
class OutputPaths:
    raw_cells: Path
    aggregate: Path
    ood: Path
    within_toroidal: Path
    robustness: Path
    report: Path


def _finite_float(value: Any) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return float("nan")
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = q * (len(sorted_values) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_values[lo]
    weight = pos - lo
    return sorted_values[lo] * (1.0 - weight) + sorted_values[hi] * weight


def bootstrap_ci(
    values: Iterable[float],
    *,
    samples: int = DEFAULT_BOOTSTRAP_SAMPLES,
    seed: int = BOOTSTRAP_SEED,
    statistic: Callable[[list[float]], float] = _mean,
) -> tuple[float, float, float]:
    vals = [float(v) for v in values if math.isfinite(float(v))]
    if not vals:
        return float("nan"), float("nan"), float("nan")
    estimate = statistic(vals)
    if len(vals) == 1 or samples <= 0:
        return estimate, estimate, estimate
    rng = random.Random(seed + len(vals) * 1009)
    boot = []
    n = len(vals)
    for _ in range(samples):
        boot.append(statistic([vals[rng.randrange(n)] for _ in range(n)]))
    boot.sort()
    return estimate, _percentile(boot, 0.025), _percentile(boot, 0.975)


def wilson_ci(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float, float]:
    if n <= 0:
        return float("nan"), float("nan"), float("nan")
    p = successes / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return p, max(0.0, center - half), min(1.0, center + half)


def spearman(xs: Iterable[float], ys: Iterable[float]) -> float:
    xvals, yvals = [], []
    for x, y in zip(xs, ys):
        xf, yf = _finite_float(x), _finite_float(y)
        if xf is not None and yf is not None:
            xvals.append(xf)
            yvals.append(yf)
    if len(xvals) < 2:
        return float("nan")

    def rank(vals: list[float]) -> list[float]:
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        ranks = [0.0] * len(vals)
        i = 0
        while i < len(vals):
            j = i
            while j + 1 < len(vals) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            r = (i + j) / 2.0
            for k in range(i, j + 1):
                ranks[order[k]] = r
            i = j + 1
        return ranks

    rx, ry = rank(xvals), rank(yvals)
    mx, my = _mean(rx), _mean(ry)
    dx = [v - mx for v in rx]
    dy = [v - my for v in ry]
    den = math.sqrt(sum(v * v for v in dx) * sum(v * v for v in dy))
    return sum(a * b for a, b in zip(dx, dy)) / den if den else float("nan")


def bootstrap_spearman(
    cells: list[dict[str, Any]],
    x_key: str,
    y_key: str,
    *,
    negate_y: bool = False,
    samples: int = DEFAULT_BOOTSTRAP_SAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float, float]:
    pairs = []
    for cell in cells:
        x = _finite_float(cell.get(x_key))
        y = _finite_float(cell.get(y_key))
        if x is not None and y is not None:
            pairs.append((x, -y if negate_y else y))
    if len(pairs) < 5:
        return float("nan"), float("nan"), float("nan")
    estimate = spearman([p[0] for p in pairs], [p[1] for p in pairs])
    if not math.isfinite(estimate) or samples <= 0:
        return estimate, estimate, estimate
    rng = random.Random(seed + len(pairs) * 9173 + len(x_key) * 37 + len(y_key))
    boot = []
    n = len(pairs)
    for _ in range(samples):
        sample = [pairs[rng.randrange(n)] for _ in range(n)]
        rho = spearman([p[0] for p in sample], [p[1] for p in sample])
        if math.isfinite(rho):
            boot.append(rho)
    if not boot:
        return estimate, float("nan"), float("nan")
    boot.sort()
    return estimate, _percentile(boot, 0.025), _percentile(boot, 0.975)


def load_sweep(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data.get("cells"), list):
        raise ValueError(f"{path} does not look like a Modal sweep JSON: missing cells[]")
    return data


def condition_sort_key(condition: str) -> tuple[int, str]:
    try:
        return CONDITION_ORDER.index(condition), condition
    except ValueError:
        return len(CONDITION_ORDER), condition


def arena_labels(data: dict[str, Any]) -> list[str]:
    manifest = data.get("manifest", {})
    labels = [f"{float(v):g}" for v in manifest.get("decode_arenas", [])]
    if labels:
        return labels
    found = set()
    for cell in data["cells"]:
        found.update(str(k) for k in cell.get("ood_by_arena", {}))
    return sorted(found, key=lambda x: float(x))


def output_paths(out_dir: Path, date: str) -> OutputPaths:
    return OutputPaths(
        raw_cells=out_dir / f"grid_cell_weakness_cells_{date}.csv",
        aggregate=out_dir / f"grid_cell_weakness_bootstrap_{date}.csv",
        ood=out_dir / f"grid_cell_weakness_ood_bootstrap_{date}.csv",
        within_toroidal=out_dir / f"grid_cell_weakness_within_toroidal_{date}.csv",
        robustness=out_dir / f"grid_cell_weakness_topology_robustness_{date}.csv",
        report=out_dir / f"grid_cell_weakness_conference_evidence_{date}.md",
    )


def write_raw_cell_csv(cells: list[dict[str, Any]], arenas: list[str], path: Path) -> None:
    fields = [
        "augment",
        "arch",
        "seed",
        "weakness_translation",
        "weakness_wrong_group",
        "toroidal_score",
        "betti_match_torus",
        "betti1_estimate",
        "h1_top1",
        "h1_top2",
        "h2_top",
        "fourier_pr",
        "id_accuracy",
        "ood_accuracy",
        "final_loss",
        "coverage",
    ] + [f"ood_arena_{label.replace('.', '_')}" for label in arenas]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for cell in sorted(cells, key=lambda c: (condition_sort_key(str(c.get("augment", ""))), c.get("arch", ""), c.get("seed", 0))):
            h1 = cell.get("h1_top2") or []
            row = {field: cell.get(field, "") for field in fields}
            row.update(
                h1_top1=h1[0] if len(h1) > 0 else "",
                h1_top2=h1[1] if len(h1) > 1 else "",
            )
            by_arena = cell.get("ood_by_arena", {})
            for label in arenas:
                row[f"ood_arena_{label.replace('.', '_')}"] = by_arena.get(label, "")
            writer.writerow(row)


def group_by_condition(cells: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cell in cells:
        groups[str(cell.get("augment", ""))].append(cell)
    return dict(sorted(groups.items(), key=lambda item: condition_sort_key(item[0])))


def metric_values(cells: list[dict[str, Any]], key: str) -> list[float]:
    vals = []
    for cell in cells:
        value = _finite_float(cell.get(key))
        if value is not None:
            vals.append(value)
    return vals


def write_aggregate_csv(
    groups: dict[str, list[dict[str, Any]]],
    path: Path,
    *,
    bootstrap_samples: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for condition, cells in groups.items():
        for key, label in CONTINUOUS_METRICS:
            values = metric_values(cells, key)
            if not values:
                continue
            mean, lo, hi = bootstrap_ci(values, samples=bootstrap_samples)
            rows.append(
                dict(
                    condition=condition,
                    n=len(values),
                    metric=key,
                    label=label,
                    estimate=mean,
                    ci_low=lo,
                    ci_high=hi,
                    ci_method="percentile_bootstrap",
                    bootstrap_samples=bootstrap_samples,
                )
            )
        successes = sum(1 for c in cells if bool(c.get("betti_match_torus")))
        mean, lo, hi = wilson_ci(successes, len(cells))
        rows.append(
            dict(
                condition=condition,
                n=len(cells),
                metric="torus_match",
                label="torus match",
                estimate=mean,
                ci_low=lo,
                ci_high=hi,
                ci_method="wilson",
                bootstrap_samples="",
            )
        )
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def write_ood_csv(
    groups: dict[str, list[dict[str, Any]]],
    arenas: list[str],
    path: Path,
    *,
    bootstrap_samples: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for condition, cells in groups.items():
        for arena in arenas:
            values = []
            for cell in cells:
                by_arena = cell.get("ood_by_arena", {})
                value = _finite_float(by_arena.get(arena))
                if value is not None:
                    values.append(value)
            if not values:
                continue
            mean, lo, hi = bootstrap_ci(values, samples=bootstrap_samples, seed=BOOTSTRAP_SEED + int(float(arena) * 100))
            rows.append(
                dict(
                    condition=condition,
                    arena_scale=arena,
                    n=len(values),
                    decode_accuracy=mean,
                    ci_low=lo,
                    ci_high=hi,
                    ci_method="percentile_bootstrap",
                    bootstrap_samples=bootstrap_samples,
                )
            )
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def write_within_toroidal_csv(
    groups: dict[str, list[dict[str, Any]]],
    path: Path,
    *,
    bootstrap_samples: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    all_toroidal = [cell for cells in groups.values() for cell in cells if bool(cell.get("betti_match_torus"))]
    subsets = [("all_conditions", all_toroidal)]
    subsets += [(condition, [cell for cell in cells if bool(cell.get("betti_match_torus"))]) for condition, cells in groups.items()]
    comparisons = [
        ("weakness_translation", "ood_accuracy", False, "rho_weakness_ood"),
        ("weakness_translation", "toroidal_score", False, "rho_weakness_toroidal_score"),
        ("weakness_translation", "fourier_pr", True, "rho_weakness_neg_fourier_pr"),
        ("final_loss", "ood_accuracy", False, "rho_loss_ood"),
    ]
    for subset, cells in subsets:
        if len(cells) < 5:
            rows.append(
                dict(
                    subset=subset,
                    n_toroidal=len(cells),
                    comparison="insufficient_toroidal_cells",
                    estimate="",
                    ci_low="",
                    ci_high="",
                    ci_method="",
                    bootstrap_samples="",
                )
            )
            continue
        for x_key, y_key, negate_y, label in comparisons:
            rho, lo, hi = bootstrap_spearman(
                cells,
                x_key,
                y_key,
                negate_y=negate_y,
                samples=bootstrap_samples,
            )
            rows.append(
                dict(
                    subset=subset,
                    n_toroidal=len(cells),
                    comparison=label,
                    estimate=rho,
                    ci_low=lo,
                    ci_high=hi,
                    ci_method="percentile_bootstrap_spearman",
                    bootstrap_samples=bootstrap_samples,
                )
            )
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def write_robustness_csv(
    groups: dict[str, list[dict[str, Any]]],
    path: Path,
    *,
    bootstrap_samples: int,
) -> list[dict[str, Any]]:
    raw_rows: list[dict[str, Any]] = []
    for condition, cells in groups.items():
        for cell in cells:
            for entry in cell.get("topology_robustness", []) or []:
                row = dict(entry)
                row["condition"] = condition
                row["arch"] = cell.get("arch", "")
                row["seed"] = cell.get("seed", "")
                raw_rows.append(row)
    fields = [
        "condition",
        "bin_count",
        "edge_percentile",
        "empty_policy",
        "max_points",
        "n",
        "toroidal_score",
        "toroidal_score_ci_low",
        "toroidal_score_ci_high",
        "torus_match",
        "torus_match_ci_low",
        "torus_match_ci_high",
        "ci_method",
        "bootstrap_samples",
        "status",
    ]
    if not raw_rows:
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerow(
                dict(
                    status="not_available_in_scalar_2026_07_02_json",
                    ci_method="requires_modal_rerun_with_robustness_true",
                    bootstrap_samples=bootstrap_samples,
                )
            )
        return []

    buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in raw_rows:
        key = (
            row.get("condition"),
            row.get("bin_count"),
            row.get("edge_percentile"),
            row.get("empty_policy"),
            row.get("max_points"),
        )
        buckets[key].append(row)

    rows = []
    for (condition, bin_count, edge_percentile, empty_policy, max_points), bucket in sorted(buckets.items()):
        scores = [v for row in bucket if (v := _finite_float(row.get("toroidal_score"))) is not None]
        score, score_lo, score_hi = bootstrap_ci(scores, samples=bootstrap_samples) if scores else (float("nan"), float("nan"), float("nan"))
        successes = sum(1 for row in bucket if bool(row.get("betti_match_torus")))
        torus, torus_lo, torus_hi = wilson_ci(successes, len(bucket))
        rows.append(
            dict(
                condition=condition,
                bin_count=bin_count,
                edge_percentile=edge_percentile,
                empty_policy=empty_policy,
                max_points=max_points,
                n=len(bucket),
                toroidal_score=score,
                toroidal_score_ci_low=score_lo,
                toroidal_score_ci_high=score_hi,
                torus_match=torus,
                torus_match_ci_low=torus_lo,
                torus_match_ci_high=torus_hi,
                ci_method="bootstrap_score_wilson_match",
                bootstrap_samples=bootstrap_samples,
                status="computed",
            )
        )
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def fmt(x: Any, digits: int = 3) -> str:
    value = _finite_float(x)
    return f"{value:.{digits}f}" if value is not None else "n/a"


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def write_report(
    *,
    data: dict[str, Any],
    source_path: Path,
    paths: OutputPaths,
    aggregate_rows: list[dict[str, Any]],
    ood_rows: list[dict[str, Any]],
    within_rows: list[dict[str, Any]],
    robustness_rows: list[dict[str, Any]],
    bootstrap_samples: int,
) -> None:
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    agg_by_condition_metric = {(r["condition"], r["metric"]): r for r in aggregate_rows}
    condition_rows = []
    for condition in sorted({r["condition"] for r in aggregate_rows}, key=condition_sort_key):
        condition_rows.append(
            [
                condition,
                str(agg_by_condition_metric[(condition, "weakness_translation")]["n"]),
                f'{fmt(agg_by_condition_metric[(condition, "weakness_translation")]["estimate"])} '
                f'[{fmt(agg_by_condition_metric[(condition, "weakness_translation")]["ci_low"])}, '
                f'{fmt(agg_by_condition_metric[(condition, "weakness_translation")]["ci_high"])}]',
                f'{fmt(agg_by_condition_metric[(condition, "toroidal_score")]["estimate"])} '
                f'[{fmt(agg_by_condition_metric[(condition, "toroidal_score")]["ci_low"])}, '
                f'{fmt(agg_by_condition_metric[(condition, "toroidal_score")]["ci_high"])}]',
                f'{fmt(agg_by_condition_metric[(condition, "fourier_pr")]["estimate"])} '
                f'[{fmt(agg_by_condition_metric[(condition, "fourier_pr")]["ci_low"])}, '
                f'{fmt(agg_by_condition_metric[(condition, "fourier_pr")]["ci_high"])}]',
                f'{fmt(agg_by_condition_metric[(condition, "torus_match")]["estimate"])} '
                f'[{fmt(agg_by_condition_metric[(condition, "torus_match")]["ci_low"])}, '
                f'{fmt(agg_by_condition_metric[(condition, "torus_match")]["ci_high"])}]',
            ]
        )

    ood_conditions = sorted({r["condition"] for r in ood_rows}, key=condition_sort_key)
    ood_arenas = sorted({r["arena_scale"] for r in ood_rows}, key=lambda v: float(v))
    ood_lookup = {(r["condition"], r["arena_scale"]): r for r in ood_rows}
    ood_table_rows = []
    for condition in ood_conditions:
        row = [condition]
        for arena in ood_arenas:
            r = ood_lookup[(condition, arena)]
            row.append(f'{fmt(r["decode_accuracy"])} [{fmt(r["ci_low"])}, {fmt(r["ci_high"])}]')
        ood_table_rows.append(row)

    within_table_rows = [
        [
            str(r["subset"]),
            str(r["n_toroidal"]),
            str(r["comparison"]),
            fmt(r["estimate"]),
            f'[{fmt(r["ci_low"])}, {fmt(r["ci_high"])}]' if r["ci_low"] != "" else "",
        ]
        for r in within_rows
        if r["comparison"] != "insufficient_toroidal_cells"
    ]
    insufficient = [r for r in within_rows if r["comparison"] == "insufficient_toroidal_cells"]

    if robustness_rows:
        robustness_text = (
            f"Topology robustness rows were computed for {len(robustness_rows)} condition/configuration buckets "
            f"and written to `{paths.robustness.name}`."
        )
    else:
        robustness_text = (
            "The recovered 2026-07-02 raw JSON stores scalar per-cell metrics but not hidden-state populations "
            "or per-configuration topology sweeps. Robustness over bin counts, Vietoris-Rips edge caps, "
            "empty-bin handling, and sampling density therefore cannot be reconstructed from this artifact. "
            "The Modal runner now has a robustness export path for reruns."
        )

    manifest = data.get("manifest", {})
    report = [
        "# Grid-Cell Weakness Conference Evidence Appendix (2026-07-02)",
        "",
        f"Source raw JSON: `{source_path}`",
        f"SHA-256: `{source_hash}`",
        "",
        f"Manifest: {len(data['cells'])} cells; conditions={manifest.get('conditions')}; "
        f"archs={manifest.get('archs')}; seeds={len(manifest.get('seeds', []))}; "
        f"steps={manifest.get('steps')}; decode_arenas={manifest.get('decode_arenas')}.",
        "",
        "Bootstrap intervals are percentile intervals from resampling cells within condition. "
        f"Continuous metrics use {bootstrap_samples} bootstrap resamples; torus-match intervals use "
        "Wilson 95% intervals for the Boolean `betti_match_torus` fraction.",
        "",
        "## Condition Metrics With 95% Intervals",
        "",
        md_table(
            ["Condition", "n", "weakness", "toroidal score", "Fourier PR", "torus match"],
            condition_rows,
        ),
        "",
        "## OOD Curve With 95% Intervals",
        "",
        md_table(["Condition"] + [f"arena {a}" for a in ood_arenas], ood_table_rows),
        "",
        "## Within-Toroidal Analysis",
        "",
        "These correlations restrict to models that already satisfy the Boolean torus criterion. "
        "They ask whether weakness explains variation after the main topology-formation event has already occurred.",
        "",
        md_table(["Subset", "n", "comparison", "rho", "95% CI"], within_table_rows) if within_table_rows else "No subset had enough already-toroidal cells for correlation analysis.",
    ]
    if insufficient:
        report += [
            "",
            "Insufficient already-toroidal cells: "
            + ", ".join(f"{r['subset']} (n={r['n_toroidal']})" for r in insufficient)
            + ".",
        ]
    report += [
        "",
        "## Topology Robustness Status",
        "",
        robustness_text,
        "",
        "## CSV Outputs",
        "",
        f"- `{paths.raw_cells.name}`: one row per trained Modal cell.",
        f"- `{paths.aggregate.name}`: condition-level means and intervals.",
        f"- `{paths.ood.name}`: OOD curve means and intervals.",
        f"- `{paths.within_toroidal.name}`: already-toroidal within-condition correlations.",
        f"- `{paths.robustness.name}`: robustness summaries when available, otherwise a status row.",
        "",
    ]
    paths.report.write_text("\n".join(report))


def run_analysis(
    raw_json: Path = DEFAULT_RAW,
    out_dir: Path = DEFAULT_OUT_DIR,
    *,
    date: str = DEFAULT_DATE,
    bootstrap_samples: int = DEFAULT_BOOTSTRAP_SAMPLES,
) -> OutputPaths:
    data = load_sweep(raw_json)
    cells = data["cells"]
    arenas = arena_labels(data)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = output_paths(out_dir, date)
    groups = group_by_condition(cells)
    write_raw_cell_csv(cells, arenas, paths.raw_cells)
    aggregate_rows = write_aggregate_csv(groups, paths.aggregate, bootstrap_samples=bootstrap_samples)
    ood_rows = write_ood_csv(groups, arenas, paths.ood, bootstrap_samples=bootstrap_samples)
    within_rows = write_within_toroidal_csv(groups, paths.within_toroidal, bootstrap_samples=bootstrap_samples)
    robustness_rows = write_robustness_csv(groups, paths.robustness, bootstrap_samples=bootstrap_samples)
    write_report(
        data=data,
        source_path=raw_json,
        paths=paths,
        aggregate_rows=aggregate_rows,
        ood_rows=ood_rows,
        within_rows=within_rows,
        robustness_rows=robustness_rows,
        bootstrap_samples=bootstrap_samples,
    )
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-json", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--date", default=DEFAULT_DATE)
    parser.add_argument("--bootstrap-samples", type=int, default=DEFAULT_BOOTSTRAP_SAMPLES)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = run_analysis(
        raw_json=args.raw_json,
        out_dir=args.out_dir,
        date=args.date,
        bootstrap_samples=args.bootstrap_samples,
    )
    for path in paths.__dict__.values():
        print(f"[gridcell-evidence] wrote {path}")


if __name__ == "__main__":
    main()
