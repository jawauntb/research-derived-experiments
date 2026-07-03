#!/usr/bin/env python3
"""Combine Modal reward-location shards and write the Paper B result report."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


def boot_stat(vals: list[float], n_boot: int = 5000) -> dict[str, Any]:
    arr = np.array([v for v in vals if np.isfinite(v)], dtype=float)
    if arr.size == 0:
        return {"mean": float("nan"), "se": float("nan"), "ci95": [float("nan"), float("nan")], "n": 0}
    if arr.size == 1:
        val = float(arr[0])
        return {"mean": val, "se": float("nan"), "ci95": [val, val], "n": 1}
    rng = np.random.default_rng(0)
    idx = rng.integers(0, arr.size, size=(n_boot, arr.size))
    means = arr[idx].mean(axis=1)
    return {
        "mean": float(arr.mean()),
        "se": float(means.std(ddof=1)),
        "ci95": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))],
        "n": int(arr.size),
    }


def balanced_arch_stat(groups: dict[str, list[float]], n_boot: int = 5000) -> dict[str, Any]:
    clean = {k: np.array([v for v in vals if np.isfinite(v)], dtype=float) for k, vals in groups.items()}
    clean = {k: v for k, v in clean.items() if v.size > 0}
    if not clean:
        return {"mean": float("nan"), "se": float("nan"), "ci95": [float("nan"), float("nan")], "n": 0}
    rng = np.random.default_rng(1)
    keys = sorted(clean)
    means = [float(clean[k].mean()) for k in keys]
    boot = np.empty(n_boot)
    for i in range(n_boot):
        arch_means = []
        for key in keys:
            vals = clean[key]
            arch_means.append(float(vals[rng.integers(0, vals.size, vals.size)].mean()))
        boot[i] = float(np.mean(arch_means))
    return {
        "mean": float(np.mean(means)),
        "se": float(boot.std(ddof=1)),
        "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
        "n": int(sum(v.size for v in clean.values())),
    }


def loc_key(xy: list[float]) -> str:
    return f"{xy[0]:.3f},{xy[1]:.3f}"


def add_control_subtraction(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    controls = {
        (r["arch"], r["seed"], loc_key(r["reward_xy"])): r
        for r in rows
        if r["condition"] == "control"
    }
    reward_rows = [dict(r) for r in rows if r["condition"] == "reward"]
    for row in reward_rows:
        ctrl = controls.get((row["arch"], row["seed"], loc_key(row["reward_xy"])))
        row["control_reward_z"] = ctrl["reward_z"] if ctrl else float("nan")
        row["control_subtracted_lift_z"] = row["reward_z"] - row["control_reward_z"]
        row["area_control_reward_z"] = ctrl["area_reward_z"] if ctrl else float("nan")
        row["area_control_subtracted_lift_z"] = row["area_reward_z"] - row["area_control_reward_z"]
    return reward_rows


def summarize(rows: list[dict[str, Any]], target_se: float) -> dict[str, Any]:
    reward_rows = add_control_subtraction(rows)
    summary: dict[str, Any] = {
        "target_bootstrap_se": target_se,
        "rows_reward": len(reward_rows),
        "rows_control": len(rows) - len(reward_rows),
        "architectures": {},
        "pooled_architecture_balanced": {},
    }
    lift_by_arch: dict[str, list[float]] = {}
    spec_by_arch: dict[str, list[float]] = {}
    for arch in sorted({r["arch"] for r in reward_rows}):
        ars = [r for r in reward_rows if r["arch"] == arch]
        lift = [r["control_subtracted_lift_z"] for r in ars]
        spec = [r["specificity_z"] for r in ars]
        lift_by_arch[arch] = lift
        spec_by_arch[arch] = spec
        arch_summary: dict[str, Any] = {
            "seeds_observed": len({r["seed"] for r in ars}),
            "control_subtracted_lift_z": boot_stat(lift),
            "specificity_z": boot_stat(spec),
            "reward_rank_percentile": boot_stat([r["reward_rank_percentile"] for r in ars]),
            "spatial_corr_reward_log_metric": boot_stat([r["spatial_corr_reward_log_metric"] for r in ars]),
            "peak_error": boot_stat([r["peak_error"] for r in ars]),
            "top10_com_error": boot_stat([r["top10_com_error"] for r in ars]),
            "area_control_subtracted_lift_z": boot_stat([r["area_control_subtracted_lift_z"] for r in ars]),
            "area_specificity_z": boot_stat([r["area_specificity_z"] for r in ars]),
            "area_reward_rank_percentile": boot_stat([r["area_reward_rank_percentile"] for r in ars]),
            "coverage": boot_stat([r["coverage"] for r in ars]),
            "final_loss": boot_stat([r["final_loss"] for r in ars]),
            "locations": {},
        }
        lift_stat = arch_summary["control_subtracted_lift_z"]
        spec_stat = arch_summary["specificity_z"]
        rank_stat = arch_summary["reward_rank_percentile"]
        arch_summary["gate"] = {
            "lift_positive": lift_stat["ci95"][0] > 0,
            "specificity_positive": spec_stat["ci95"][0] > 0,
            "lift_se_le_target": lift_stat["se"] <= target_se,
            "specificity_se_le_target": spec_stat["se"] <= target_se,
            "rank_above_chance": rank_stat["mean"] > 0.5,
        }
        arch_summary["gate"]["pass"] = all(arch_summary["gate"].values())
        for loc in sorted({loc_key(r["reward_xy"]) for r in ars}):
            lrs = [r for r in ars if loc_key(r["reward_xy"]) == loc]
            arch_summary["locations"][loc] = {
                "control_subtracted_lift_z": boot_stat([r["control_subtracted_lift_z"] for r in lrs]),
                "specificity_z": boot_stat([r["specificity_z"] for r in lrs]),
                "reward_rank_percentile": boot_stat([r["reward_rank_percentile"] for r in lrs]),
                "peak_error": boot_stat([r["peak_error"] for r in lrs]),
            }
        summary["architectures"][arch] = arch_summary

    pooled_lift = balanced_arch_stat(lift_by_arch)
    pooled_spec = balanced_arch_stat(spec_by_arch)
    summary["pooled_architecture_balanced"] = {
        "control_subtracted_lift_z": pooled_lift,
        "specificity_z": pooled_spec,
        "gate": {
            "lift_positive": pooled_lift["ci95"][0] > 0,
            "specificity_positive": pooled_spec["ci95"][0] > 0,
            "lift_se_le_target": pooled_lift["se"] <= target_se,
            "specificity_se_le_target": pooled_spec["se"] <= target_se,
        },
    }
    summary["pooled_architecture_balanced"]["gate"]["pass"] = all(
        summary["pooled_architecture_balanced"]["gate"].values()
    )
    return summary


def fmt_stat(stat: dict[str, Any]) -> str:
    return (
        f"{stat['mean']:+.4f} [{stat['ci95'][0]:+.4f}, {stat['ci95'][1]:+.4f}], "
        f"SE={stat['se']:.4f}, n={stat['n']}"
    )


def write_report(payload: dict[str, Any], out: Path) -> None:
    summary = payload["summary"]
    manifest = payload["manifest"]
    target_se = float(summary["target_bootstrap_se"])
    strict_se = 0.01

    def precision_pass(item: dict[str, Any], se: float) -> bool:
        return (
            item["control_subtracted_lift_z"]["ci95"][0] > 0
            and item["specificity_z"]["ci95"][0] > 0
            and item["control_subtracted_lift_z"]["se"] <= se
            and item["specificity_z"]["se"] <= se
            and item["reward_rank_percentile"]["mean"] > 0.5
        )

    arch_seed_counts = ", ".join(
        f"{arch}={item['seeds_observed']}"
        for arch, item in summary["architectures"].items()
    )
    lines = [
        "# Paper B Moved-Location Metric-Deformation Sweep — Modal Results (2026-07-02)",
        "",
        "Pre-registration: [papers/grid_cell_weakness/preregistration.md](../../../papers/grid_cell_weakness/preregistration.md),",
        'frozen addendum "Paper B Moved-Location Metric-Deformation Gate" (2026-07-02). Runner:',
        "`experiments/grid_cell_weakness/modal_reward_location_sweep.py`. Backend: Modal",
        "H200/H100 workers. Raw JSON is gitignored; combined artifact:",
        f"`{payload['combined_artifact']}`.",
        "",
        (
            f"Manifest: {len(manifest['architectures'])} architectures × {len(manifest['locations'])} "
            f"reward locations. Observed seed counts by architecture: {arch_seed_counts}. "
            "Each seed shard trains one matched uniform-control model and one reward model per "
            "registered location for each architecture present in that shard."
        ),
        "",
        "## Primary Gate Verdict",
        "",
        (
            f"Report precision target: bootstrap SE <= {target_se:.2f}. The frozen pre-registration "
            f"also recorded a stricter adaptive target of <= {strict_se:.2f}; that stricter audit is "
            "reported below rather than silently relabeled."
        ),
        "",
        "| Architecture | lift z | specificity z | rank | peak error | Gate |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for arch, item in summary["architectures"].items():
        lift = item["control_subtracted_lift_z"]
        spec = item["specificity_z"]
        rank = item["reward_rank_percentile"]
        peak = item["peak_error"]
        lines.append(
            f"| {arch} | {fmt_stat(lift)} | {fmt_stat(spec)} | "
            f"{rank['mean']:.3f} | {peak['mean']:.3f} | "
            f"{'met' if item['gate']['pass'] else 'not met'} |"
        )
    pooled = summary["pooled_architecture_balanced"]
    lines += [
        "",
        "Architecture-balanced pooled lift: "
        f"{fmt_stat(pooled['control_subtracted_lift_z'])}.",
        "Architecture-balanced pooled specificity: "
        f"{fmt_stat(pooled['specificity_z'])}.",
        "",
        "## Strict 1% Precision Audit",
        "",
        "| Architecture | <=1% lift SE | <=1% specificity SE | Directional CIs positive | Strict 1% audit |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for arch, item in summary["architectures"].items():
        lift = item["control_subtracted_lift_z"]
        spec = item["specificity_z"]
        directional = lift["ci95"][0] > 0 and spec["ci95"][0] > 0
        lines.append(
            f"| {arch} | {lift['se'] <= strict_se} | {spec['se'] <= strict_se} | "
            f"{directional} | {'met' if precision_pass(item, strict_se) else 'not met'} |"
        )
    lines += [
        "",
        "## Companion Area-Density Diagnostics",
        "",
        "| Architecture | area lift z | area specificity z | area rank |",
        "| --- | ---: | ---: | ---: |",
    ]
    for arch, item in summary["architectures"].items():
        lines.append(
            f"| {arch} | {fmt_stat(item['area_control_subtracted_lift_z'])} | "
            f"{fmt_stat(item['area_specificity_z'])} | "
            f"{item['area_reward_rank_percentile']['mean']:.3f} |"
        )
    lines += [
        "",
        "## Reading",
        "",
        "The Paper B primary observable is the original neighbor-stretch metric density: mean latent",
        "displacement per unit physical displacement. Area density is reported only as a companion",
        "rate-distortion diagnostic.",
        "",
        "Interpret the claim exactly as preregistered: architectures meet the report threshold only when the bootstrap",
        "intervals for both control-subtracted lift and moved-location specificity exclude zero on",
        f"the positive side, the primary standard errors are at or below the stated report target "
        f"({target_se:.2f} here), and the reward-location rank is above chance. The frozen stricter",
        "1% precision audit is retained separately because the 2% threshold was accepted after the",
        "first-wave results were visible. Families that do not meet an audit must remain non-meeting in the paper.",
        "",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def load_shards(pattern: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paths = sorted(Path().glob(pattern))
    if not paths:
        raise SystemExit(f"no shard files match {pattern!r}")
    rows: list[dict[str, Any]] = []
    manifests = []
    for path in paths:
        data = json.loads(path.read_text())
        rows.extend(data["rows"])
        manifests.append(data["manifest"])
    seeds = sorted({r["seed"] for r in rows if r["condition"] == "reward"})
    archs = sorted({r["arch"] for r in rows})
    locations = sorted({loc_key(r["reward_xy"]) for r in rows if r.get("reward_xy") is not None})
    manifest = {
        **manifests[0],
        "architectures": archs,
        "locations": locations,
        "seeds_observed": len(seeds),
        "seed_values_observed": seeds,
        "shards": len(paths),
    }
    return rows, manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pattern", default="artifacts/grid_cell_weakness/reward_location_sweep_2026_07_02_hopper_seed*.json")
    parser.add_argument("--combined", default="artifacts/grid_cell_weakness/reward_location_sweep_2026_07_02_combined.json")
    parser.add_argument("--report", default="experiments/grid_cell_weakness/results/reward_location_sweep_2026_07_02.md")
    parser.add_argument("--target-se", type=float, default=0.01)
    args = parser.parse_args()

    rows, manifest = load_shards(args.pattern)
    summary = summarize(rows, args.target_se)
    payload = {
        "kind": "combined moved-location reward-deformation sweep",
        "combined_artifact": args.combined,
        "manifest": manifest,
        "summary": summary,
        "rows": rows,
    }
    combined = Path(args.combined)
    combined.parent.mkdir(parents=True, exist_ok=True)
    combined.write_text(json.dumps(payload, indent=2, default=float) + "\n", encoding="utf-8")
    write_report(payload, Path(args.report))
    print(f"[reward-location-summary] wrote {combined}")
    print(f"[reward-location-summary] wrote {args.report}")
    for arch, item in summary["architectures"].items():
        lift = item["control_subtracted_lift_z"]
        spec = item["specificity_z"]
        print(
            f"  {arch:12s} lift={lift['mean']:+.4f} SE={lift['se']:.4f} "
            f"spec={spec['mean']:+.4f} SE={spec['se']:.4f} pass={item['gate']['pass']}"
        )


if __name__ == "__main__":
    main()
