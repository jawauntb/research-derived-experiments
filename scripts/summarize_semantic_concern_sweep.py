#!/usr/bin/env python3
"""Summarize the Modal semantic-concern geometry sweep."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


def _finite(vals: list[float]) -> list[float]:
    return [float(v) for v in vals if math.isfinite(float(v))]


def boot_stat(vals: list[float], n_boot: int = 5000, seed: int = 0) -> dict[str, Any]:
    import numpy as np

    arr = np.asarray(_finite(vals), dtype=float)
    if arr.size == 0:
        return {"mean": math.nan, "se": math.nan, "ci95": [math.nan, math.nan], "n": 0}
    if arr.size == 1:
        val = float(arr[0])
        return {"mean": val, "se": math.nan, "ci95": [val, val], "n": 1}
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot)
    for i in range(n_boot):
        boot[i] = arr[rng.integers(0, arr.size, arr.size)].mean()
    return {
        "mean": float(arr.mean()),
        "se": float(boot.std(ddof=1)),
        "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
        "n": int(arr.size),
    }


def balanced_boot_stat(groups: dict[str, list[float]], n_boot: int = 5000, seed: int = 0) -> dict[str, Any]:
    import numpy as np

    clean = {k: np.asarray(_finite(v), dtype=float) for k, v in groups.items()}
    clean = {k: v for k, v in clean.items() if v.size}
    if not clean:
        return {"mean": math.nan, "se": math.nan, "ci95": [math.nan, math.nan], "n": 0}
    keys = sorted(clean)
    family_means = [float(clean[k].mean()) for k in keys]
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot)
    for i in range(n_boot):
        vals = []
        for key in keys:
            arr = clean[key]
            vals.append(float(arr[rng.integers(0, arr.size, arr.size)].mean()))
        boot[i] = float(np.mean(vals))
    return {
        "mean": float(np.mean(family_means)),
        "se": float(boot.std(ddof=1)),
        "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
        "n": int(sum(v.size for v in clean.values())),
    }


def family_key(row: dict[str, Any]) -> str:
    return f"{row['model_slug']}::{row['objective']}"


def family_label(key: str) -> str:
    model, objective = key.split("::", 1)
    model = model.replace("sentence_transformers__", "").replace("__", "/").replace("_", "-")
    objective_label = "JEPA-like" if objective == "jepa" else "classifier"
    return f"{model} / {objective_label}"


def paired_effects(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    uniform = {
        (family_key(r), int(r["seed"]), r["target"]): r
        for r in rows
        if r["condition"] == "uniform"
    }
    random = {
        (family_key(r), int(r["seed"]), r["target"]): r
        for r in rows
        if r["condition"] == "random_matched"
    }
    effects = []
    for row in rows:
        if row["condition"] != "concern":
            continue
        key = (family_key(row), int(row["seed"]), row["target"])
        u = uniform.get(key)
        rnd = random.get(key)
        if not u or not rnd:
            continue
        effects.append({
            **row,
            "family": key[0],
            "margin_lift_vs_uniform": row["target_margin_z"] - u["target_margin_z"],
            "margin_lift_vs_random": row["target_margin_z"] - rnd["target_margin_z"],
            "centroid_lift_vs_uniform": row["target_centroid_margin_z"] - u["target_centroid_margin_z"],
            "knn_purity_lift_vs_uniform": row["target_knn_purity_z"] - u["target_knn_purity_z"],
            "effective_rank_lift_vs_uniform": row["target_effective_rank_z"] - u["target_effective_rank_z"],
            "target_f1_lift_vs_uniform": row["target_f1"] - u["target_f1"],
            "accuracy_lift_vs_uniform": row["accuracy"] - u["accuracy"],
            "random_margin_z": rnd["target_margin_z"],
            "uniform_margin_z": u["target_margin_z"],
        })
    return effects


def summarize(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["rows"]
    manifest = payload.get("manifest", {})
    target_se = float(manifest.get("target_bootstrap_se", 0.02))
    effects = paired_effects(rows)
    families = sorted({e["family"] for e in effects})
    rows_by_family = defaultdict(list)
    for row in rows:
        rows_by_family[family_key(row)].append(row)
    out: dict[str, Any] = {
        "target_bootstrap_se": target_se,
        "n_rows": len(rows),
        "n_effects": len(effects),
        "families": {},
        "pooled_family_balanced": {},
        "dataset_kinds": sorted({r.get("dataset_kind", "unknown") for r in rows}),
    }
    grouped = defaultdict(list)
    for effect in effects:
        grouped[effect["family"]].append(effect)

    balanced_primary: dict[str, dict[str, list[float]]] = defaultdict(dict)
    for family in families:
        items = grouped[family]
        stats = {
            "margin_lift_vs_uniform": boot_stat([e["margin_lift_vs_uniform"] for e in items]),
            "margin_lift_vs_random": boot_stat([e["margin_lift_vs_random"] for e in items], seed=1),
            "specificity_z": boot_stat([e["specificity_z"] for e in items], seed=2),
            "target_rank_percentile": boot_stat([e["target_rank_percentile"] for e in items], seed=3),
            "centroid_lift_vs_uniform": boot_stat([e["centroid_lift_vs_uniform"] for e in items], seed=4),
            "knn_purity_lift_vs_uniform": boot_stat([e["knn_purity_lift_vs_uniform"] for e in items], seed=5),
            "effective_rank_lift_vs_uniform": boot_stat([e["effective_rank_lift_vs_uniform"] for e in items], seed=6),
            "target_f1_lift_vs_uniform": boot_stat([e["target_f1_lift_vs_uniform"] for e in items], seed=7),
            "accuracy_lift_vs_uniform": boot_stat([e["accuracy_lift_vs_uniform"] for e in items], seed=8),
            "targets": {},
        }
        for target in sorted({e["target"] for e in items}):
            target_items = [e for e in items if e["target"] == target]
            stats["targets"][target] = {
                "margin_lift_vs_uniform": boot_stat([e["margin_lift_vs_uniform"] for e in target_items]),
                "margin_lift_vs_random": boot_stat([e["margin_lift_vs_random"] for e in target_items], seed=11),
                "specificity_z": boot_stat([e["specificity_z"] for e in target_items], seed=12),
                "n": len(target_items),
            }
        real_dataset = set(r.get("dataset_kind") for r in rows_by_family[family]) == {"20newsgroups"}
        gate = {
            "uniform_lift_positive": stats["margin_lift_vs_uniform"]["ci95"][0] > 0,
            "random_lift_positive": stats["margin_lift_vs_random"]["ci95"][0] > 0,
            "specificity_positive": stats["specificity_z"]["ci95"][0] > 0,
            "uniform_lift_se_le_target": stats["margin_lift_vs_uniform"]["se"] <= target_se,
            "random_lift_se_le_target": stats["margin_lift_vs_random"]["se"] <= target_se,
            "rank_above_chance": stats["target_rank_percentile"]["mean"] > 0.5,
            "real_20newsgroups": real_dataset,
        }
        gate["pass"] = all(gate.values())
        stats["gate"] = gate
        stats["n_effects"] = len(items)
        out["families"][family] = stats
        balanced_primary["margin_lift_vs_uniform"][family] = [
            e["margin_lift_vs_uniform"] for e in items
        ]
        balanced_primary["margin_lift_vs_random"][family] = [
            e["margin_lift_vs_random"] for e in items
        ]
        balanced_primary["specificity_z"][family] = [e["specificity_z"] for e in items]
        balanced_primary["target_rank_percentile"][family] = [
            e["target_rank_percentile"] for e in items
        ]

    pooled = {
        metric: balanced_boot_stat(groups, seed=20 + i)
        for i, (metric, vals) in enumerate(balanced_primary.items())
        for groups in [vals]
    }
    pooled_gate = {
        "uniform_lift_positive": pooled["margin_lift_vs_uniform"]["ci95"][0] > 0,
        "random_lift_positive": pooled["margin_lift_vs_random"]["ci95"][0] > 0,
        "specificity_positive": pooled["specificity_z"]["ci95"][0] > 0,
        "uniform_lift_se_le_target": pooled["margin_lift_vs_uniform"]["se"] <= target_se,
        "random_lift_se_le_target": pooled["margin_lift_vs_random"]["se"] <= target_se,
        "rank_above_chance": pooled["target_rank_percentile"]["mean"] > 0.5,
        "real_20newsgroups": out["dataset_kinds"] == ["20newsgroups"],
    }
    pooled_gate["pass"] = all(pooled_gate.values())
    pooled["gate"] = pooled_gate
    out["pooled_family_balanced"] = pooled
    return out


def fmt_stat(stat: dict[str, Any], digits: int = 3) -> str:
    return (
        f"{stat['mean']:+.{digits}f} "
        f"[{stat['ci95'][0]:+.{digits}f}, {stat['ci95'][1]:+.{digits}f}], "
        f"SE {stat['se']:.3f}"
    )


def report_markdown(payload: dict[str, Any], summary: dict[str, Any]) -> str:
    manifest = payload.get("manifest", {})
    input_payloads = manifest.get("input_payloads", [])
    input_manifests = manifest.get("input_manifests", [manifest])
    lines = [
        "# Semantic Concern Geometry Sweep -- Modal Results (2026-07-02)",
        "",
        "Pre-registration: [papers/semantic_concern_geometry/preregistration.md]"
        "(../../../papers/semantic_concern_geometry/preregistration.md).",
        "",
        "## Discovery-Regime Audit",
        "",
        "Question: Does a non-spatial semantic loss-weight intervention move a learned "
        "representation-geometry deformation to the upweighted class in pretrained transformers?",
        "",
        "Current regime:",
        "- Artifact types: Modal sweep JSON, paired effect rows, bootstrap summary, result report, PDF paper.",
        "- Operations: 20 Newsgroups sampling, pretrained transformer fine-tuning, JEPA-like predictive latent training, geometry probes.",
        "- Gates/verifiers: preregistered 2% bootstrap-SE gate, semantic random-matched control, real-dataset requirement.",
        "- Known limitations: four-topic text classification, small fine-tuned encoders, JEPA-like objective rather than official I-JEPA.",
        "",
        "Action class:",
        "- Search/discovery: search inside the Paper B metric-deformation schema, with a new non-spatial semantic artifact class.",
        "",
        "## Manifest",
        "",
        f"- Models: {', '.join(manifest.get('models', []))}",
        f"- Objectives: {', '.join(manifest.get('objectives', []))}",
        f"- Registered categories: {', '.join(manifest.get('registered_categories', []))}",
        f"- Seeds per family: {manifest.get('seeds')}",
        f"- Steps per trained cell: {manifest.get('steps')}",
        f"- Batch size: {manifest.get('batch_size')}",
        f"- Concern weight: {manifest.get('concern_weight')}",
        f"- Target bootstrap SE: {manifest.get('target_bootstrap_se')}",
        f"- Dataset kinds observed: {', '.join(summary['dataset_kinds'])}",
        f"- Rows: {summary['n_rows']}; paired concern effects: {summary['n_effects']}",
        f"- Merged payloads: {len(input_payloads) if input_payloads else 1}",
        "",
        "Run command(s):",
        "",
        "```bash",
    ]
    for idx, run_manifest in enumerate(input_manifests):
        out_path = input_payloads[idx] if idx < len(input_payloads) else "artifacts/semantic_concern_geometry/semantic_concern_sweep_2026_07_02.json"
        lines += [
            "doppler --scope /Users/jawaun/superoptimizers run -- \\",
            "  uvx --python 3.12 --from modal modal run \\",
            "    experiments/semantic_concern_geometry/modal_semantic_concern_sweep.py \\",
            f"    --seeds {run_manifest.get('seeds')} --base-seed {run_manifest.get('base_seed')} "
            f"--steps {run_manifest.get('steps')} --batch-size {run_manifest.get('batch_size')} "
            f"--target-se {run_manifest.get('target_bootstrap_se')} \\",
            f"    --out {out_path}",
            "",
        ]
    lines += [
        "```",
        "",
        "## Gate Summary",
        "",
        "| Family | lift vs uniform | lift vs random | specificity | rank | gate |",
        "| --- | ---: | ---: | ---: | ---: | :--: |",
    ]
    for family, stats in summary["families"].items():
        lines.append(
            f"| {family_label(family)} | {fmt_stat(stats['margin_lift_vs_uniform'])} | "
            f"{fmt_stat(stats['margin_lift_vs_random'])} | {fmt_stat(stats['specificity_z'])} | "
            f"{stats['target_rank_percentile']['mean']:.3f} | "
            f"{'PASS' if stats['gate']['pass'] else 'FAIL'} |"
        )
    pooled = summary["pooled_family_balanced"]
    lines += [
        "",
        "Architecture-balanced pooled result:",
        "",
        f"- Lift vs uniform: {fmt_stat(pooled['margin_lift_vs_uniform'])}",
        f"- Lift vs random matched: {fmt_stat(pooled['margin_lift_vs_random'])}",
        f"- Specificity: {fmt_stat(pooled['specificity_z'])}",
        f"- Rank percentile: {pooled['target_rank_percentile']['mean']:.3f}",
        f"- Pooled gate: {'PASS' if pooled['gate']['pass'] else 'FAIL'}",
        "",
        "## Companion Metrics",
        "",
        "| Family | centroid lift | kNN-purity lift | eff-rank lift | target-F1 lift | accuracy lift |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for family, stats in summary["families"].items():
        lines.append(
            f"| {family_label(family)} | {fmt_stat(stats['centroid_lift_vs_uniform'])} | "
            f"{fmt_stat(stats['knn_purity_lift_vs_uniform'])} | "
            f"{fmt_stat(stats['effective_rank_lift_vs_uniform'])} | "
            f"{fmt_stat(stats['target_f1_lift_vs_uniform'])} | "
            f"{fmt_stat(stats['accuracy_lift_vs_uniform'])} |"
        )
    lines += [
        "",
        "## Target Audit",
        "",
        "Per-target effects are retained so a single class cannot silently carry the claim.",
        "",
    ]
    for family, stats in summary["families"].items():
        lines += [f"### {family_label(family)}", ""]
        lines += [
            "| Target | n | lift vs uniform | lift vs random | specificity |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
        for target, target_stats in stats["targets"].items():
            lines.append(
                f"| {target} | {target_stats['n']} | "
                f"{fmt_stat(target_stats['margin_lift_vs_uniform'])} | "
                f"{fmt_stat(target_stats['margin_lift_vs_random'])} | "
                f"{fmt_stat(target_stats['specificity_z'])} |"
            )
        lines.append("")
    lines += [
        "## Interpretation Rules",
        "",
        "- Passing families support the bounded claim: semantic loss weighting can causally and specifically deform a learned text-representation metric.",
        "- Failed families remain failed; the pooled result must not hide a family-level failure.",
        "- Behavioral gains alone do not count as metric deformation.",
        "- Synthetic-fallback runs are smoke tests only and do not address the externality limitation.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        nargs="+",
        default=["artifacts/semantic_concern_geometry/semantic_concern_sweep_2026_07_02.json"],
    )
    parser.add_argument("--summary-json", default="artifacts/semantic_concern_geometry/semantic_concern_summary_2026_07_02.json")
    parser.add_argument("--report", default="experiments/semantic_concern_geometry/results/semantic_concern_sweep_2026_07_02.md")
    args = parser.parse_args()

    payloads = [json.loads(Path(p).read_text()) for p in args.input]
    payload = dict(payloads[0])
    payload["rows"] = [row for p in payloads for row in p["rows"]]
    manifest = dict(payload.get("manifest", {}))
    manifest["input_payloads"] = args.input
    manifest["input_manifests"] = [p.get("manifest", {}) for p in payloads]
    if all("manifest" in p and "seeds" in p["manifest"] for p in payloads):
        manifest["seeds"] = sum(int(p["manifest"]["seeds"]) for p in payloads)
    payload["manifest"] = manifest
    summary = summarize(payload)
    summary_path = Path(args.summary_json)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, default=float) + "\n")
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_markdown(payload, summary) + "\n")
    print(f"[semantic-concern] wrote {summary_path}")
    print(f"[semantic-concern] wrote {report_path}")
    pooled = summary["pooled_family_balanced"]
    print(
        "[semantic-concern] pooled "
        f"lift_vs_uniform={pooled['margin_lift_vs_uniform']['mean']:+.4f} "
        f"SE={pooled['margin_lift_vs_uniform']['se']:.4f}; "
        f"lift_vs_random={pooled['margin_lift_vs_random']['mean']:+.4f} "
        f"SE={pooled['margin_lift_vs_random']['se']:.4f}; "
        f"pass={pooled['gate']['pass']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
