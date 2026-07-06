"""Artifact builders for Suite C teacher-free inquiry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from experiments.world_responds.suite_c_teacher_free import (
    COST_ONLY_PROXY_CONDITION,
    MATCHED_RANDOM_CONDITION,
    RECOVERY_ONLY_PROXY_CONDITION,
    SUPPRESSION_CONTROL_CONDITION,
    STALE_CONTROL_CONDITION,
    TEACHER_FREE_CONDITION,
    TEACHER_FREE_CONDITIONS,
    WRONG_CONTROL_CONDITION,
    run_teacher_free_suite,
    summarize_teacher_free_records,
)

REPORT_MD = Path("experiments/world_responds/results/suite_c_teacher_free_inquiry_2026_07_06.md")
PUBLIC_SUMMARY_JSON = Path(
    "experiments/world_responds/results/suite_c_teacher_free_inquiry_2026_07_06.json"
)
ROWS_JSONL = Path(
    "experiments/world_responds/results/suite_c_teacher_free_inquiry_rows_2026_07_06.jsonl"
)


def _fmt(value: Any, digits: int = 3) -> str:
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _fmt_evidence(key: str, value: Any) -> str:
    if key.startswith("teacher_") and isinstance(value, bool):
        return str(value).lower()
    return _fmt(value)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _rows_by_condition(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["condition"]: row for row in payload["summary"]["by_condition"]}


def validate_payload(payload: dict[str, Any]) -> None:
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Suite C teacher-free payload must include non-empty rows")
    manifest = payload.get("manifest", {})
    eval_seeds = [int(seed) for seed in manifest.get("eval_seeds", [])]
    if not eval_seeds:
        raise ValueError("Suite C teacher-free manifest must include eval_seeds")
    if tuple(manifest.get("conditions", ())) != TEACHER_FREE_CONDITIONS:
        raise ValueError("Suite C teacher-free manifest conditions do not match contract")

    expected_pairs = {(condition, seed) for condition in TEACHER_FREE_CONDITIONS for seed in eval_seeds}
    actual_counts: dict[tuple[str, int], int] = {}
    for row in rows:
        pair = (str(row["condition"]), int(row["seed"]))
        actual_counts[pair] = actual_counts.get(pair, 0) + 1
        if row.get("teacher_labels_used") or row.get("teacher_actions_used") or row.get(
            "teacher_probabilities_used"
        ):
            raise ValueError(f"teacher-free row used teacher supervision: {pair}")
    bad_pairs = sorted(pair for pair, count in actual_counts.items() if count != 1)
    if bad_pairs:
        raise ValueError(f"Suite C teacher-free payload has duplicate row pairs: {bad_pairs[:5]}")
    actual_pairs = set(actual_counts)
    if actual_pairs != expected_pairs:
        missing = sorted(expected_pairs - actual_pairs)
        extra = sorted(actual_pairs - expected_pairs)
        raise ValueError(
            "Suite C teacher-free payload grid mismatch: "
            f"missing={missing[:5]} extra={extra[:5]}"
        )

    recomputed = summarize_teacher_free_records(rows)
    if _canonical(recomputed) != _canonical(payload.get("summary")):
        raise ValueError("Suite C teacher-free payload summary does not match rows")

    learned_budget_by_seed = {
        int(row["seed"]): int(row["total_probes"])
        for row in rows
        if row["condition"] == TEACHER_FREE_CONDITION
    }
    for row in rows:
        if row["condition"] != MATCHED_RANDOM_CONDITION:
            continue
        seed = int(row["seed"])
        if int(row["target_probe_count"]) != learned_budget_by_seed[seed]:
            raise ValueError(
                "Suite C teacher-free matched-random row has stale budget: "
                f"seed={seed} target={row['target_probe_count']} "
                f"learned={learned_budget_by_seed[seed]}"
            )


def build_public_summary(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload["summary"]
    manifest = payload["manifest"]
    rows = _rows_by_condition(payload)
    learned = rows[TEACHER_FREE_CONDITION]
    stale = rows[STALE_CONTROL_CONDITION]
    wrong = rows[WRONG_CONTROL_CONDITION]
    suppressed = rows[SUPPRESSION_CONTROL_CONDITION]
    matched = rows[MATCHED_RANDOM_CONDITION]
    reward_only = rows[RECOVERY_ONLY_PROXY_CONDITION]
    cost_only = rows[COST_ONLY_PROXY_CONDITION]
    scheduled = rows["scheduled_null_anchor"]
    oracle = rows["oracle_source"]
    gates = summary["gates"]
    report_ref = str(REPORT_MD)
    return {
        "benchmark": {
            "name": "Causally Grounded Finite Agents Benchmark",
            "version": "2026-07-06",
            "charter": "Evaluate finite agents by requiring behavior plus structure-specific gates and anti-cheat controls.",
        },
        "suite": {
            "id": "suite_c_teacher_free_inquiry",
            "name": "Suite C Teacher-Free Inquiry",
            "axis_coverage": ["behavior", "attribution", "inquiry", "teacher_free_training", "anti_cheat"],
            "status": "strong" if gates["suite_pass"]["pass"] else "negative",
        },
        "run": {
            "run_id": "suite_c_teacher_free_inquiry_2026_07_06",
            "date": "2026-07-06",
            "command": "python -m experiments.world_responds.summarize_suite_c_teacher_free --out-root .",
            "rows": int(summary["n_rows"]),
            "models": ["linear_probe_policy"],
            "providers": ["local_numpy"],
        },
        "minimum_pass_rule": {
            "behavior_passed": bool(gates["C3_recovery"]["pass"]),
            "structure_gate_passed": bool(
                gates["C2_reengagement"]["pass"] and gates["C6_reopenability"]["pass"]
            ),
            "anti_cheat_controls_passed": bool(
                gates["T1_teacher_free_training"]["pass"]
                and gates["N1_learned_signal_controls"]["pass"]
                and gates["C4_no_false_calm"]["pass"]
            ),
            "passed": bool(gates["suite_pass"]["pass"]),
            "notes": (
                "Teacher-free reward/CEM policy passes C1-C6 plus T1/N1 on held-out "
                "seeds without teacher labels, actions, or probabilities."
            ),
        },
        "score_axes": {
            "behavior": {
                "headline_condition": TEACHER_FREE_CONDITION,
                "final_component_mae": learned["final_component_mae"],
                "recovery_rate": learned["recovery_rate"],
            },
            "inquiry": {
                "first_selectivity_ratio": learned["first_selectivity_ratio"],
                "second_reopen_ratio": learned["second_reopen_ratio"],
                "learned_total_probes": learned["total_probes"],
                "matched_random_total_probes": matched["total_probes"],
                "matched_random_selectivity_ratio": matched["first_selectivity_ratio"],
            },
            "anti_cheat": {
                "stale_recovery_rate": stale["recovery_rate"],
                "wrong_signal_selectivity_ratio": wrong["first_selectivity_ratio"],
                "suppressed_final_component_mae": suppressed["final_component_mae"],
                "teacher_free_gate": bool(gates["T1_teacher_free_training"]["pass"]),
            },
        },
        "gates": [
            {
                "gate_id": name.split("_", 1)[0],
                "name": name,
                "passed": bool(gate["pass"]),
                "evidence_ref": report_ref,
            }
            for name, gate in gates.items()
        ],
        "baselines": [
            {
                "name": "scheduled_null_anchor",
                "kind": "upper",
                "result": f"{_fmt(scheduled['total_probes'], 1)} probes, final MAE {_fmt(scheduled['final_component_mae'])}",
                "evidence_ref": report_ref,
            },
            {
                "name": "oracle_source",
                "kind": "upper",
                "result": f"{_fmt(oracle['total_probes'], 1)} probes, final MAE {_fmt(oracle['final_component_mae'])}",
                "evidence_ref": report_ref,
            },
            {
                "name": MATCHED_RANDOM_CONDITION,
                "kind": "control",
                "result": f"equal-budget random selectivity {_fmt(matched['first_selectivity_ratio'])}",
                "evidence_ref": report_ref,
            },
            {
                "name": RECOVERY_ONLY_PROXY_CONDITION,
                "kind": "proxy",
                "result": f"recovery-only proxy uses {_fmt(reward_only['total_probes'], 1)} probes",
                "evidence_ref": report_ref,
            },
            {
                "name": COST_ONLY_PROXY_CONDITION,
                "kind": "proxy",
                "result": f"cost-only proxy recovery rate {_fmt(cost_only['recovery_rate'])}",
                "evidence_ref": report_ref,
            },
        ],
        "artifacts": {
            "rows_jsonl": str(ROWS_JSONL),
            "summary_json": str(PUBLIC_SUMMARY_JSON),
            "report_md": str(REPORT_MD),
        },
        "allowed_claim": (
            "In a controlled finite benchmark, a linear inquiry policy selected by "
            "teacher-free downstream reward search can pass Suite C C1-C6 and the "
            "T1/N1 anti-cheat gates on held-out seeds."
        ),
        "non_claims": [
            "Not evidence of open-ended agency.",
            "Not a foundation-model or API-agent result.",
            "Not human or biological validation.",
            "Not a production reliability certificate.",
            "Not a consciousness test.",
        ],
        "training": {
            "train_seeds": manifest["train_seeds"],
            "calibration_seeds": manifest["calibration_seeds"],
            "eval_seeds": manifest["eval_seeds"],
            "teacher_labels_used": False,
            "teacher_actions_used": False,
            "teacher_probabilities_used": False,
            "training_regime": payload["training"]["training_regime"],
            "iterations": payload["training"]["iterations"],
            "population_size": payload["training"]["population_size"],
        },
    }


def write_rows_jsonl(payload: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as handle:
        for row in payload["rows"]:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_report(payload: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    rows = _rows_by_condition(payload)
    learned = rows[TEACHER_FREE_CONDITION]
    stale = rows[STALE_CONTROL_CONDITION]
    wrong = rows[WRONG_CONTROL_CONDITION]
    suppressed = rows[SUPPRESSION_CONTROL_CONDITION]
    matched = rows[MATCHED_RANDOM_CONDITION]
    lines = [
        "# Suite C Teacher-Free Inquiry",
        "",
        "Date: 2026-07-06",
        "",
        "## Discovery-Regime Audit",
        "",
        "Question: can Suite C re-engagement be learned without direct teacher labels, actions, or probabilities?",
        "",
        "Current regime:",
        "- Artifact types: finite Suite C rows, learned-policy summaries, public JSONL rows, public summary JSON, and gate report.",
        "- Operations: CEM reward search over a linear probe policy, threshold calibration, held-out finite simulator evaluation.",
        "- Gates/verifiers: C1-C6 Suite C gates, T1 teacher-free audit, N1 stale/wrong/suppressed signal controls, matched random budget.",
        "- Known limitations: finite NumPy simulator; no open-agent, API-agent, biological, or consciousness claim.",
        "",
        "Action class:",
        "- Retrieval/search/discovery: bounded discovery-level transition.",
        "- Why: the operation changes from teacher-trace imitation to downstream reward search while preserving the old Suite C gates.",
        "",
        "Experiment:",
        f"- Train seeds: `{payload['manifest']['train_seeds']}`.",
        f"- Calibration seeds: `{payload['manifest']['calibration_seeds']}`.",
        f"- Held-out eval seeds: `{payload['manifest']['eval_seeds']}`.",
        f"- Selected threshold: `{payload['model']['threshold']:.3f}`.",
        "- Positive target: reward/CEM policy passes C1-C6 with lower probe cost than scheduled/oracle controls.",
        "- Negative controls: stale signal, wrong signal, signal suppression, equal-budget random, recovery-only proxy, cost-only proxy.",
        "",
        "Gate:",
        "- Acceptance rule: C1-C6, T1, and N1 pass on held-out seeds with public-safe rows and summary.",
        "- Withheld/rejected rule: stale/wrong/suppressed controls passing, random budget matching selectivity, or teacher supervision would make the result negative.",
        "",
        "## Gate Results",
        "",
        "| Gate | Pass? | Evidence |",
        "| --- | --- | --- |",
    ]
    for name, gate in summary["gates"].items():
        evidence = ", ".join(
            f"{key}={_fmt_evidence(key, value)}"
            for key, value in gate.items()
            if key != "pass"
        )
        lines.append(f"| {name} | {_fmt(bool(gate['pass']))} | {evidence} |")
    lines.extend(
        [
            "",
            "## Headline",
            "",
            f"The teacher-free policy reaches final affected MAE {_fmt(learned['final_component_mae'])}, recovery rate {_fmt(learned['recovery_rate'])}, first-shift selectivity {_fmt(learned['first_selectivity_ratio'])}, second-shift reopenability {_fmt(learned['second_reopen_ratio'])}, and {_fmt(learned['total_probes'], 1)} probes.",
            "",
            f"Matched random at the same budget reaches selectivity {_fmt(matched['first_selectivity_ratio'])}. Stale-signal recovery rate is {_fmt(stale['recovery_rate'])}; wrong-signal selectivity is {_fmt(wrong['first_selectivity_ratio'])}; suppressed-signal final MAE is {_fmt(suppressed['final_component_mae'])}.",
            "",
            "## Condition Summary",
            "",
            "| Condition | N | Probes | Final MAE | Selectivity | Reopen | No false calm | Recovery |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["by_condition"]:
        lines.append(
            f"| `{row['condition']}` | {row['n']} | {_fmt(row['total_probes'], 1)} | "
            f"{_fmt(row['final_component_mae'])} | {_fmt(row['first_selectivity_ratio'])} | "
            f"{_fmt(row['second_reopen_ratio'])} | {_fmt(row['no_false_calm_rate'])} | "
            f"{_fmt(row['recovery_rate'])} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is stronger than the teacher-trained probe head on the specific reviewer objection it targets: the training loss never consumes hand-policy actions, teacher labels, or teacher probabilities. It is still not an open-agent result; it is a finite diagnostic showing that Suite C can be learned from downstream world-response reward in this harness.",
            "",
            "## Artifact Ledger",
            "",
            f"- Public rows JSONL: `{ROWS_JSONL}`",
            f"- Public summary JSON: `{PUBLIC_SUMMARY_JSON}`",
            f"- Report: `{REPORT_MD}`",
        ]
    )
    out.write_text("\n".join(lines) + "\n")


def build_artifacts(payload: dict[str, Any], out_root: Path) -> list[Path]:
    validate_payload(payload)
    rows_jsonl = out_root / ROWS_JSONL
    public_summary = out_root / PUBLIC_SUMMARY_JSON
    report = out_root / REPORT_MD
    write_rows_jsonl(payload, rows_jsonl)
    write_report(payload, report)
    public_summary.parent.mkdir(parents=True, exist_ok=True)
    public_summary.write_text(json.dumps(build_public_summary(payload), indent=2, sort_keys=True) + "\n")
    return [rows_jsonl, public_summary, report]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", type=Path, default=Path("."))
    parser.add_argument("--payload-out", type=Path, default=None)
    args = parser.parse_args()
    payload = run_teacher_free_suite()
    if args.payload_out is not None:
        args.payload_out.parent.mkdir(parents=True, exist_ok=True)
        args.payload_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    paths = build_artifacts(payload, args.out_root)
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
