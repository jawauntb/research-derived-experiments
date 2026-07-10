"""Pre-registered 2^3 ablation in the existing Suite C workflow."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from experiments.world_responds.suite_c_contract import (
    DEFAULT_CONFIG,
    FULL_SUITE_C_MECHANISMS,
    SuiteCConfig,
    SuiteCMechanisms,
)
from experiments.world_responds.suite_c_reengagement import run_suite, run_trial

FACTOR_NAMES = ("allocate", "cool", "reopen")
FACTOR_LEVELS: tuple[tuple[bool, bool, bool], ...] = (
    (False, False, False),
    (False, False, True),
    (False, True, False),
    (False, True, True),
    (True, False, False),
    (True, False, True),
    (True, True, False),
    (True, True, True),
)
DEFAULT_SEEDS = (
    20260709,
    20261712,
    20262715,
    20263718,
    20264721,
    20265724,
    20266727,
    20267730,
)
BOOTSTRAP_SEED = 20260709
BOOTSTRAP_SAMPLES = 10_000
PRIMARY_METRIC = "world_change_reengagement_pass"
EFFECT_METRICS = (
    PRIMARY_METRIC,
    "first_reengagement_ratio",
    "first_selectivity_ratio",
    "second_reopen_ratio",
    "final_component_mae",
    "total_probes",
    "no_false_calm",
)
PUBLIC_SUMMARY_JSON = Path(
    "experiments/commitment_surface/results/m4_suite_c_factorial_ablation_2026_07_09.json"
)
PUBLIC_SUMMARY_MD = Path(
    "experiments/commitment_surface/results/m4_suite_c_factorial_ablation_2026_07_09.md"
)
RAW_PAYLOAD = Path("artifacts/world_responds/suite_c_factorial_ablation_2026_07_09.json")
PREREGISTRATION = Path(
    "experiments/world_responds/"
    "suite_c_factorial_ablation_preregistration_2026_07_09.md"
)


def _factor_levels() -> tuple[tuple[bool, bool, bool], ...]:
    return FACTOR_LEVELS


def _cell_name(levels: tuple[bool, bool, bool]) -> str:
    bits = "_".join(
        f"{name}_{int(level)}" for name, level in zip(FACTOR_NAMES, levels, strict=True)
    )
    return f"burst_then_refractory__{bits}"


def _mechanisms(levels: tuple[bool, bool, bool]) -> SuiteCMechanisms:
    return SuiteCMechanisms(**dict(zip(FACTOR_NAMES, levels, strict=True)))


def run_factorial_trial(
    seed: int,
    levels: tuple[bool, bool, bool],
    *,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
) -> dict[str, Any]:
    """Intervene on one real burst/refractory row without replacing its dynamics."""

    mechanisms = _mechanisms(levels)
    row = run_trial("burst_then_refractory", seed, cfg=cfg, mechanisms=mechanisms)
    row["base_condition"] = row["condition"]
    row["condition"] = _cell_name(levels)
    row["mechanisms"] = asdict(mechanisms)
    row["detect"] = True
    row["saturate"] = True
    row[PRIMARY_METRIC] = bool(row["candidate_terminal_pass"])
    return row


def _numeric(row: dict[str, Any], metric: str) -> float:
    value = row[metric]
    return float(value) if not isinstance(value, bool) else float(int(value))


def _cell_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for levels in _factor_levels():
        name = _cell_name(levels)
        cell_rows = [row for row in rows if row["condition"] == name]
        summaries.append(
            {
                "condition": name,
                "mechanisms": asdict(_mechanisms(levels)),
                "n": len(cell_rows),
                "terminal_pass_rate": float(
                    np.mean([_numeric(row, PRIMARY_METRIC) for row in cell_rows])
                ),
                **{
                    metric: float(np.mean([_numeric(row, metric) for row in cell_rows]))
                    for metric in EFFECT_METRICS
                    if metric != PRIMARY_METRIC
                },
            }
        )
    return summaries


def _effect_signs(levels: tuple[bool, bool, bool]) -> dict[str, int]:
    signs = {name: 1 if level else -1 for name, level in zip(FACTOR_NAMES, levels, strict=True)}
    return {
        "allocate": signs["allocate"],
        "cool": signs["cool"],
        "reopen": signs["reopen"],
        "allocate_x_cool": signs["allocate"] * signs["cool"],
        "allocate_x_reopen": signs["allocate"] * signs["reopen"],
        "cool_x_reopen": signs["cool"] * signs["reopen"],
        "allocate_x_cool_x_reopen": signs["allocate"] * signs["cool"] * signs["reopen"],
    }


def _factorial_effects(
    rows: list[dict[str, Any]],
    seeds: tuple[int, ...],
) -> dict[str, dict[str, dict[str, float]]]:
    levels = _factor_levels()
    row_lookup = {
        (int(row["seed"]), row["condition"]): row
        for row in rows
    }
    effect_names = tuple(_effect_signs(levels[0]))
    sign_matrix = np.asarray(
        [[_effect_signs(cell)[name] for name in effect_names] for cell in levels],
        dtype=float,
    )
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    bootstrap_indices = rng.integers(0, len(seeds), size=(BOOTSTRAP_SAMPLES, len(seeds)))
    output: dict[str, dict[str, dict[str, float]]] = {}
    for metric in EFFECT_METRICS:
        values = np.asarray(
            [
                [
                    _numeric(row_lookup[(seed, _cell_name(cell))], metric)
                    for cell in levels
                ]
                for seed in seeds
            ],
            dtype=float,
        )
        seed_effects = 2.0 * np.mean(values[:, :, None] * sign_matrix[None, :, :], axis=1)
        point = np.mean(seed_effects, axis=0)
        boot = np.mean(seed_effects[bootstrap_indices], axis=1)
        output[metric] = {
            name: {
                "effect": float(point[index]),
                "ci95_low": float(np.percentile(boot[:, index], 2.5)),
                "ci95_high": float(np.percentile(boot[:, index], 97.5)),
            }
            for index, name in enumerate(effect_names)
        }
    return output


def _reference_control_gate(reference: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    by_condition = {
        row["condition"]: row for row in reference["summary"]["by_condition"]
    }
    headline = reference["summary"]["headline_condition"]
    fixed = by_condition["fixed_surprise_decrement"]
    matched = by_condition["matched_random_time_budget"]
    headline_row = by_condition[headline]
    headline_budgets = {
        int(row["seed"]): int(row["total_probes"])
        for row in reference["rows"]
        if row["condition"] == headline
    }
    matched_budget_ok = all(
        int(row["target_probe_count"]) == headline_budgets[int(row["seed"])]
        for row in reference["rows"]
        if row["condition"] == "matched_random_time_budget"
    )
    checks = {
        "reference_suite_pass": bool(reference["summary"]["gates"]["suite_pass"]["pass"]),
        "fixed_surprise_no_false_calm_rate": float(fixed["no_false_calm_rate"]),
        "fixed_surprise_rejected": float(fixed["no_false_calm_rate"]) <= 0.34,
        "headline_condition": headline,
        "headline_selectivity_ratio": float(headline_row["first_selectivity_ratio"]),
        "matched_selectivity_ratio": float(matched["first_selectivity_ratio"]),
        "matched_less_selective": float(matched["first_selectivity_ratio"])
        < float(headline_row["first_selectivity_ratio"]),
        "matched_per_seed_budget_exact": matched_budget_ok,
    }
    passed = all(
        (
            checks["reference_suite_pass"],
            checks["fixed_surprise_rejected"],
            checks["matched_less_selective"],
            checks["matched_per_seed_budget_exact"],
        )
    )
    return bool(passed), checks


def summarize_factorial(
    factorial_rows: list[dict[str, Any]],
    reference: dict[str, Any],
    seeds: tuple[int, ...],
    *,
    all_on_matches_reference: bool,
    deterministic_replay: bool,
) -> dict[str, Any]:
    by_cell = _cell_summary(factorial_rows)
    cell_lookup = {row["condition"]: row for row in by_cell}
    effects = _factorial_effects(factorial_rows, seeds)
    primary_effects = effects[PRIMARY_METRIC]
    full_rate = cell_lookup[_cell_name((True, True, True))]["terminal_pass_rate"]

    single_removals: dict[str, dict[str, Any]] = {}
    knockout_levels: dict[str, tuple[bool, bool, bool]] = {
        "allocate": (False, True, True),
        "cool": (True, False, True),
        "reopen": (True, True, False),
    }
    for factor, knockout in knockout_levels.items():
        knockout_rate = cell_lookup[_cell_name(knockout)]["terminal_pass_rate"]
        difference = float(full_rate - knockout_rate)
        single_removals[factor] = {
            "knockout_condition": _cell_name(knockout),
            "knockout_pass_rate": knockout_rate,
            "paired_full_minus_knockout": difference,
            "pass": bool(knockout_rate <= 0.25 and difference >= 0.50),
        }

    expected_conditions = {_cell_name(levels) for levels in _factor_levels()}
    counts = {
        (int(row["seed"]), row["condition"])
        for row in factorial_rows
    }
    balanced = len(factorial_rows) == len(seeds) * 8 and all(
        (seed, condition) in counts for seed in seeds for condition in expected_conditions
    )
    f0 = bool(balanced and all_on_matches_reference and deterministic_replay)
    f1 = bool(full_rate >= 0.75)
    f2 = all(item["pass"] for item in single_removals.values())
    f3_checks = {
        factor: {
            **primary_effects[factor],
            "pass": bool(
                primary_effects[factor]["effect"] >= 0.20
                and primary_effects[factor]["ci95_low"] > 0.0
            ),
        }
        for factor in FACTOR_NAMES
    }
    f3 = all(item["pass"] for item in f3_checks.values())
    interaction_names = (
        "allocate_x_cool",
        "allocate_x_reopen",
        "cool_x_reopen",
        "allocate_x_cool_x_reopen",
    )
    f4_checks = {
        name: {
            **primary_effects[name],
            "finite": bool(np.isfinite(primary_effects[name]["effect"])),
            "nonnegative": bool(primary_effects[name]["effect"] >= 0.0),
        }
        for name in interaction_names
    }
    f4 = all(item["finite"] and item["nonnegative"] for item in f4_checks.values())
    reduced_cells = [
        row for row in by_cell if not all(bool(row["mechanisms"][factor]) for factor in FACTOR_NAMES)
    ]
    f5 = all(float(row["terminal_pass_rate"]) <= 0.25 for row in reduced_cells)
    f6, f6_checks = _reference_control_gate(reference)
    gates = {
        "F0_integrity": {
            "pass": f0,
            "n_rows": len(factorial_rows),
            "balanced": balanced,
            "all_on_matches_reference": all_on_matches_reference,
            "deterministic_replay": deterministic_replay,
        },
        "F1_full_loop_replication": {
            "pass": f1,
            "full_loop_pass_rate": full_rate,
            "required": 0.75,
        },
        "F2_single_removal_necessity": {
            "pass": f2,
            "components": single_removals,
        },
        "F3_main_effects": {
            "pass": f3,
            "required_effect": 0.20,
            "required_ci95_low_strictly_above": 0.0,
            "components": f3_checks,
        },
        "F4_interactions": {
            "pass": f4,
            "required_point_estimate": "finite and nonnegative",
            "interactions": f4_checks,
        },
        "F5_no_interaction_rescue": {
            "pass": f5,
            "maximum_reduced_cell_pass_rate": max(
                float(row["terminal_pass_rate"]) for row in reduced_cells
            ),
            "required_maximum": 0.25,
        },
        "F6_transported_controls": {"pass": f6, **f6_checks},
    }
    strict_pass = all(bool(gate["pass"]) for gate in gates.values())
    return {
        "kind": "world_responds_suite_c_factorial_ablation_summary",
        "preregistration": str(PREREGISTRATION),
        "claim_level": (
            "diagnostic finite-harness causal ablation"
            if strict_pass
            else "failed diagnostic gate; M4 remains a compression hypothesis"
        ),
        "strict_verdict": "PASS" if strict_pass else "FAIL",
        "n_seeds": len(seeds),
        "n_factorial_rows": len(factorial_rows),
        "seeds": list(seeds),
        "frozen_stages": {"detect": True, "saturate": True},
        "factor_names": list(FACTOR_NAMES),
        "by_cell": by_cell,
        "factorial_effects": effects,
        "gates": gates,
        "reference_suite": {
            "headline_condition": reference["summary"]["headline_condition"],
            "gates": reference["summary"]["gates"],
        },
        "rejected_alternatives": [
            "new toy state machine",
            "neural-transfer policy-learning confound",
            "three single knockouts without the remaining factorial cells",
            "aggregate-only unpaired reporting",
            "post-result threshold retuning",
        ],
    }


def run_factorial_suite(
    *,
    seeds: Iterable[int] = DEFAULT_SEEDS,
    cfg: SuiteCConfig = DEFAULT_CONFIG,
) -> dict[str, Any]:
    seed_tuple = tuple(int(seed) for seed in seeds)
    if len(seed_tuple) < 5:
        raise ValueError("pre-registration requires at least five paired seeds")
    if len(set(seed_tuple)) != len(seed_tuple):
        raise ValueError("paired seeds must be unique")

    reference = run_suite(seeds=list(seed_tuple), cfg=cfg)
    rows = [
        run_factorial_trial(seed, levels, cfg=cfg)
        for seed in seed_tuple
        for levels in _factor_levels()
    ]
    replay = [
        run_factorial_trial(seed, levels, cfg=cfg)
        for seed in seed_tuple
        for levels in _factor_levels()
    ]
    reference_all_on = {
        int(row["seed"]): row
        for row in reference["rows"]
        if row["condition"] == "burst_then_refractory"
    }
    added_fields = {
        "base_condition",
        "mechanisms",
        "detect",
        "saturate",
        PRIMARY_METRIC,
    }
    all_on_matches = True
    for row in rows:
        if row["condition"] != _cell_name((True, True, True)):
            continue
        existing_fields = {key: value for key, value in row.items() if key not in added_fields}
        existing_fields["condition"] = "burst_then_refractory"
        all_on_matches &= existing_fields == reference_all_on[int(row["seed"])]

    summary = summarize_factorial(
        rows,
        reference,
        seed_tuple,
        all_on_matches_reference=bool(all_on_matches),
        deterministic_replay=rows == replay,
    )
    command = (
        "python3 -m experiments.world_responds.suite_c_factorial_ablation "
        f"--seeds {','.join(str(seed) for seed in seed_tuple)} "
        f"--out {RAW_PAYLOAD} --summary-json {PUBLIC_SUMMARY_JSON} "
        f"--summary-md {PUBLIC_SUMMARY_MD}"
    )
    summary["run_config"] = {
        "command": command,
        "seeds": list(seed_tuple),
        "base_condition": "burst_then_refractory",
        "factor_levels": [False, True],
        "steps": cfg.steps,
        "first_shift": cfg.first_shift,
        "second_shift": cfg.second_shift,
        "recovery_threshold": cfg.recovery_threshold,
        "reengagement_floor": cfg.reengagement_floor,
        "selectivity_floor": cfg.selectivity_floor,
        "reopen_floor": cfg.reopen_floor,
        "bootstrap_samples": BOOTSTRAP_SAMPLES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "mechanism_default": asdict(FULL_SUITE_C_MECHANISMS),
    }
    return {
        "kind": "world_responds_suite_c_factorial_ablation",
        "manifest": summary["run_config"],
        "factorial_rows": rows,
        "reference_suite": reference,
        "summary": summary,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Suite C Allocate × Cool × Reopen Factorial (2026-07-09)",
        "",
        f"**Strict gate verdict: {summary['strict_verdict']}.**",
        f"Claim level: {summary['claim_level']}.",
        "",
        "## Exact run config",
        "",
        "```bash",
        summary["run_config"]["command"],
        "```",
        "",
        f"Paired seeds: `{summary['seeds']}`. Detect and saturate were frozen on.",
        "The unmodified Suite C controls and per-seed matched-random budgets were rerun.",
        "",
        "## Factorial cells",
        "",
        "| allocate | cool | reopen | terminal pass | re-engage | selectivity | reopen ratio | final MAE | probes |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["by_cell"]:
        mechanisms = row["mechanisms"]
        lines.append(
            "| {allocate:d} | {cool:d} | {reopen:d} | {terminal_pass_rate:.3f} | "
            "{first_reengagement_ratio:.3f} | {first_selectivity_ratio:.3f} | "
            "{second_reopen_ratio:.3f} | {final_component_mae:.3f} | {total_probes:.1f} |".format(
                **{name: int(mechanisms[name]) for name in FACTOR_NAMES},
                **row,
            )
        )
    lines.extend(
        [
            "",
            "## Primary factorial effects (terminal pass)",
            "",
            "| contrast | effect | paired bootstrap 95% CI |",
            "| --- | ---: | ---: |",
        ]
    )
    for name, effect in summary["factorial_effects"][PRIMARY_METRIC].items():
        lines.append(
            f"| {name} | {effect['effect']:+.3f} | "
            f"[{effect['ci95_low']:+.3f}, {effect['ci95_high']:+.3f}] |"
        )
    lines.extend(
        [
            "",
            "## Single-removal necessity",
            "",
            "| removed stage | knockout pass rate | full minus knockout | gate |",
            "| --- | ---: | ---: | :---: |",
        ]
    )
    for factor, item in summary["gates"]["F2_single_removal_necessity"][
        "components"
    ].items():
        lines.append(
            f"| {factor} | {item['knockout_pass_rate']:.3f} | "
            f"{item['paired_full_minus_knockout']:+.3f} | "
            f"{'PASS' if item['pass'] else 'FAIL'} |"
        )
    controls = summary["gates"]["F6_transported_controls"]
    lines.extend(
        [
            "",
            "## Transported controls",
            "",
            f"- Reference C1–C6 suite: {'PASS' if controls['reference_suite_pass'] else 'FAIL'}.",
            f"- False-calm control no-false-calm rate: "
            f"{controls['fixed_surprise_no_false_calm_rate']:.3f} "
            f"({'rejected' if controls['fixed_surprise_rejected'] else 'not rejected'}).",
            f"- Headline vs matched-random selectivity: "
            f"{controls['headline_selectivity_ratio']:.3f} vs "
            f"{controls['matched_selectivity_ratio']:.3f}; per-seed budgets exact: "
            f"{controls['matched_per_seed_budget_exact']}.",
            "",
            "## Frozen gate verdicts",
            "",
        ]
    )
    for name, gate in summary["gates"].items():
        lines.append(f"- **{name}: {'PASS' if gate['pass'] else 'FAIL'}.**")
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            (
                "The strict verdict is determined only by F0–F6. A failure remains a "
                "failure even when the complete policy or some directional contrasts pass."
            ),
            "This is finite-harness diagnostic evidence, not neural or external validation.",
            "",
            "## Rejected alternatives",
            "",
        ]
    )
    lines.extend(f"- {item}." for item in summary["rejected_alternatives"])
    return "\n".join(lines) + "\n"


def _write_if_changed(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == content:
        return
    path.write_text(content)


def write_artifacts(
    payload: dict[str, Any],
    *,
    out: Path = RAW_PAYLOAD,
    summary_json: Path = PUBLIC_SUMMARY_JSON,
    summary_md: Path = PUBLIC_SUMMARY_MD,
) -> None:
    _write_if_changed(out, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    _write_if_changed(
        summary_json,
        json.dumps(payload["summary"], indent=2, sort_keys=True) + "\n",
    )
    _write_if_changed(summary_md, render_markdown(payload["summary"]))


def _parse_seeds(value: str) -> tuple[int, ...]:
    return tuple(int(part.strip()) for part in value.split(",") if part.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds",
        default=",".join(str(seed) for seed in DEFAULT_SEEDS),
        help="comma-separated paired seeds (minimum five)",
    )
    parser.add_argument("--out", type=Path, default=RAW_PAYLOAD)
    parser.add_argument("--summary-json", type=Path, default=PUBLIC_SUMMARY_JSON)
    parser.add_argument("--summary-md", type=Path, default=PUBLIC_SUMMARY_MD)
    args = parser.parse_args()
    payload = run_factorial_suite(seeds=_parse_seeds(args.seeds))
    write_artifacts(
        payload,
        out=args.out,
        summary_json=args.summary_json,
        summary_md=args.summary_md,
    )
    print(json.dumps({
        "strict_verdict": payload["summary"]["strict_verdict"],
        "gates": {
            name: gate["pass"] for name, gate in payload["summary"]["gates"].items()
        },
        "summary_json": str(args.summary_json),
        "summary_md": str(args.summary_md),
        "raw_payload": str(args.out),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
