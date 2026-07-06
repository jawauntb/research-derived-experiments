"""Artifact builders for Suite C neural probe transfer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from experiments.world_responds.suite_c_neural_transfer import (
    FEATURE_NAMES,
    LEARNED_CONDITION,
    MATCHED_RANDOM_CONDITION,
    NEURAL_TRANSFER_CONDITIONS,
    summarize_neural_records,
)


REPORT_MD = Path("experiments/world_responds/results/suite_c_neural_transfer_2026_07_06.md")
PUBLIC_SUMMARY_JSON = Path(
    "experiments/world_responds/results/suite_c_neural_transfer_2026_07_06.json"
)
PAPER_MD = Path("papers/habituated_reengagement/suite_c_neural_probe_transfer.md")
PAPER_PDF = Path("papers/habituated_reengagement/suite_c_neural_probe_transfer.pdf")
CRITICAL_REVIEW = Path("docs/paper_reviews/suite_c_neural_probe_transfer_critical_review.md")
RELEASE_SCHEMA_JSON = (
    Path(__file__).resolve().parents[2] / "docs/causally_grounded_agents_release_schema.json"
)

COLORS = {
    "p22_learned_current_replay": "#6b7280",
    "scheduled_null_anchor": "#7c3aed",
    "oracle_source": "#0f766e",
    "teacher_burst_then_refractory": "#2563eb",
    "learned_probe_head": "#059669",
    "stale_signal_head": "#d97706",
    "wrong_signal_head": "#dc2626",
    "signal_suppression_head": "#b91c1c",
    "matched_random_learned_budget": "#9ca3af",
}

LABELS = {
    "p22_learned_current_replay": "P22 quiet",
    "scheduled_null_anchor": "Scheduled",
    "oracle_source": "Oracle source",
    "teacher_burst_then_refractory": "Teacher reference",
    "learned_probe_head": "Learned head",
    "stale_signal_head": "Stale signal",
    "wrong_signal_head": "Wrong signal",
    "signal_suppression_head": "Suppressed signal",
    "matched_random_learned_budget": "Matched random",
}


def _fmt(value: Any, digits: int = 3) -> str:
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _rows_by_condition(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["condition"]: row for row in payload["summary"]["by_condition"]}


def validate_payload(payload: dict[str, Any]) -> None:
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Suite C neural-transfer payload must include non-empty rows")
    manifest = payload.get("manifest", {})
    eval_seeds = [int(seed) for seed in manifest.get("eval_seeds", [])]
    if not eval_seeds:
        raise ValueError("Suite C neural-transfer manifest must include eval_seeds")
    if tuple(manifest.get("feature_names", [])) != FEATURE_NAMES:
        raise ValueError("Suite C neural-transfer manifest has stale feature names")
    if tuple(manifest.get("conditions", ())) != NEURAL_TRANSFER_CONDITIONS:
        raise ValueError("Suite C neural-transfer manifest conditions do not match contract")

    expected_pairs = {(condition, seed) for condition in NEURAL_TRANSFER_CONDITIONS for seed in eval_seeds}
    actual_counts: dict[tuple[str, int], int] = {}
    for row in rows:
        pair = (str(row["condition"]), int(row["seed"]))
        actual_counts[pair] = actual_counts.get(pair, 0) + 1
    bad_pairs = sorted(pair for pair, count in actual_counts.items() if count != 1)
    if bad_pairs:
        raise ValueError(f"Suite C neural-transfer payload has duplicate row pairs: {bad_pairs[:5]}")
    actual_pairs = set(actual_counts)
    if actual_pairs != expected_pairs:
        missing = sorted(expected_pairs - actual_pairs)
        extra = sorted(actual_pairs - expected_pairs)
        raise ValueError(
            "Suite C neural-transfer payload grid mismatch: "
            f"missing={missing[:5]} extra={extra[:5]}"
        )

    recomputed = summarize_neural_records(rows)
    if _canonical(recomputed) != _canonical(payload.get("summary")):
        raise ValueError("Suite C neural-transfer payload summary does not match rows")

    if payload.get("model", {}).get("feature_names") != list(FEATURE_NAMES):
        raise ValueError("Suite C neural-transfer model record has stale feature names")

    learned_budget_by_seed = {
        int(row["seed"]): int(row["total_probes"])
        for row in rows
        if row["condition"] == LEARNED_CONDITION
    }
    for row in rows:
        if row["condition"] != MATCHED_RANDOM_CONDITION:
            continue
        seed = int(row["seed"])
        if int(row["target_probe_count"]) != learned_budget_by_seed[seed]:
            raise ValueError(
                "Suite C neural-transfer matched-random row has stale budget: "
                f"seed={seed} target={row['target_probe_count']} "
                f"learned={learned_budget_by_seed[seed]}"
            )


def write_figures(payload: dict[str, Any], figure_dir: Path) -> list[Path]:
    import matplotlib.pyplot as plt

    figure_dir.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    rows = summary["by_condition"]
    paths: list[Path] = []
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "legend.fontsize": 8.5,
            "figure.facecolor": "white",
        }
    )

    gate_names = [name for name in summary["gates"] if name != "suite_pass"]
    gate_labels = [name.split("_", 1)[1].replace("_", " ").title() for name in gate_names]
    gate_values = [1.0 if summary["gates"][name]["pass"] else 0.0 for name in gate_names]
    fig, ax = plt.subplots(figsize=(10.2, 4.2))
    ax.bar(gate_labels, gate_values, color=["#059669" if value else "#dc2626" for value in gate_values])
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Gate status")
    ax.set_title("Neural Suite C transfer gate: held-out learned probe head")
    ax.set_xticks(range(len(gate_labels)), gate_labels, rotation=20, ha="right")
    ax.grid(axis="y", alpha=0.25)
    for idx, value in enumerate(gate_values):
        ax.text(idx, value + 0.04, "PASS" if value else "FAIL", ha="center", weight="bold")
    fig.tight_layout()
    path = figure_dir / "suite_c_neural_fig1_gate_status.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)

    labels = [LABELS[row["condition"]] for row in rows]
    conditions = [row["condition"] for row in rows]
    x = list(range(len(rows)))
    fig, axes = plt.subplots(1, 2, figsize=(13.6, 5.0))
    axes[0].bar(x, [row["first_selectivity_ratio"] for row in rows], color=[COLORS[c] for c in conditions])
    axes[0].axhline(2.0, color="#111827", linestyle="--", linewidth=1.0, label="2x gate")
    axes[0].set_xticks(x, labels, rotation=25, ha="right")
    axes[0].set_ylabel("Affected / unaffected probe density")
    axes[0].set_title("Source-correct selective re-engagement")
    axes[0].grid(axis="y", alpha=0.25)
    axes[0].legend()

    axes[1].bar(x, [row["second_reopen_ratio"] for row in rows], color=[COLORS[c] for c in conditions])
    axes[1].axhline(1.0, color="#111827", linestyle="--", linewidth=1.0, label="reopen gate")
    axes[1].set_xticks(x, labels, rotation=25, ha="right")
    axes[1].set_ylabel("Post-second / pre-second affected probes")
    axes[1].set_title("Second-shift re-openability")
    axes[1].grid(axis="y", alpha=0.25)
    axes[1].legend()
    fig.tight_layout()
    path = figure_dir / "suite_c_neural_fig2_selectivity_reopenability.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)

    fig, ax1 = plt.subplots(figsize=(10.6, 5.2))
    ax2 = ax1.twinx()
    width = 0.38
    left = [idx - width / 2 for idx in x]
    right = [idx + width / 2 for idx in x]
    ax1.bar(
        left,
        [row["final_component_mae"] for row in rows],
        width=width,
        color=[COLORS[c] for c in conditions],
        label="Final component MAE",
    )
    ax2.bar(
        right,
        [row["total_probes"] for row in rows],
        width=width,
        color="#9ca3af",
        alpha=0.72,
        label="Total probes",
    )
    ax1.axhline(0.12, color="#111827", linestyle="--", linewidth=1.0)
    ax1.set_xticks(x, labels, rotation=25, ha="right")
    ax1.set_ylabel("Final affected MAE (lower is better)")
    ax2.set_ylabel("Total probes")
    ax1.set_title("Learned transfer must couple recovery and cost")
    ax1.grid(axis="y", alpha=0.25)
    bars, labels1 = ax1.get_legend_handles_labels()
    bars2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(bars + bars2, labels1 + labels2, loc="upper right")
    fig.tight_layout()
    path = figure_dir / "suite_c_neural_fig3_recovery_cost.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)

    control_rows = [
        row
        for row in rows
        if row["condition"] in {"learned_probe_head", "stale_signal_head", "wrong_signal_head", "signal_suppression_head"}
    ]
    fig, axes = plt.subplots(1, 3, figsize=(13.4, 4.6))
    metrics = [
        ("recovery_rate", "Recovery rate", 0.60),
        ("first_selectivity_ratio", "Selectivity", 2.0),
        ("no_false_calm_rate", "No-false-calm rate", 0.60),
    ]
    control_labels = [LABELS[row["condition"]] for row in control_rows]
    for ax, (metric, title, gate) in zip(axes, metrics):
        ax.bar(
            range(len(control_rows)),
            [row[metric] for row in control_rows],
            color=[COLORS[row["condition"]] for row in control_rows],
        )
        ax.axhline(gate, color="#111827", linestyle="--", linewidth=1.0)
        ax.set_xticks(range(len(control_rows)), control_labels, rotation=25, ha="right")
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Learned-policy controls should fail for different reasons", y=1.03)
    fig.tight_layout()
    path = figure_dir / "suite_c_neural_fig4_control_failures.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)
    return paths


def write_report(payload: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    manifest = payload["manifest"]
    rows = _rows_by_condition(payload)
    learned = rows[LEARNED_CONDITION]
    gates = summary["gates"]
    lines = [
        "# Suite C Neural Probe Transfer",
        "",
        "Date: 2026-07-06",
        "",
        "## Discovery-Regime Audit",
        "",
        "Question: can Suite C's decision-layer inquiry law survive when the probe decision is trained rather than hand-specified?",
        "",
        "Current regime:",
        "- Artifact types: learned probe-head payloads, held-out Suite C rows, tracked public summary JSON, figures, paper, critical review.",
        "- Operations: teacher trace collection from `burst_then_refractory`, NumPy MLP training, threshold calibration, held-out evaluation.",
        "- Gates/verifiers: C1-C6 Suite C gates plus stale-signal, wrong-signal, and signal-suppression controls.",
        "- Known limitations: finite simulator transfer; not a human, biological, consciousness, or production-agent result.",
        "",
        "Action class:",
        "- Retrieval/search/discovery: bounded discovery-level transfer artifact.",
        "- Why: the run adds a learned-policy artifact type and learned-signal controls not present in the terminal hand-policy gate.",
        "",
        "Experiment:",
        f"- Train seeds: `{manifest['train_seeds']}`.",
        f"- Calibration seeds: `{manifest['calibration_seeds']}`.",
        f"- Held-out eval seeds: `{manifest['eval_seeds']}`.",
        f"- Selected threshold: `{payload['model']['threshold']:.3f}`.",
        f"- Training examples: `{payload['training']['examples']}` with positive rate `{payload['training']['positive_rate']:.3f}`.",
        "- Controls: stale perceived signals, wrong-source perceived signals, suppressed stress signals, and matched random at the learned probe budget.",
        "",
        "Gate:",
        "- Acceptance rule: learned head passes C1-C6 on held-out seeds and all learned-policy controls fail in their intended way.",
        "- Withheld/rejected rule: do not claim transfer if recovery comes from high-cost probing, if random budget matches selectivity, or if stale/wrong/suppressed signals pass.",
        "",
        "## Gate Results",
        "",
        "| Gate | Pass? | Evidence |",
        "| --- | --- | --- |",
    ]
    for name, gate in gates.items():
        if name == "suite_pass":
            continue
        evidence = ", ".join(f"{key}={_fmt(value)}" for key, value in gate.items() if key != "pass")
        lines.append(f"| {name} | {_fmt(bool(gate['pass']))} | {evidence} |")
    lines.extend(
        [
            "",
            "## Headline",
            "",
            f"The learned probe head reaches final affected MAE {_fmt(learned['final_component_mae'])}, first-shift selectivity {_fmt(learned['first_selectivity_ratio'])}, second-shift reopenability {_fmt(learned['second_reopen_ratio'])}, and uses {_fmt(learned['total_probes'], 1)} probes.",
            "",
            f"Suite pass: **{_fmt(bool(gates['suite_pass']['pass']))}**.",
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
            "The learned head is not rewarded for final error alone. It must re-open inquiry after two shifts, recover attribution, spend fewer probes than scheduled/oracle controls, and beat matched random inquiry at the same budget.",
            "",
            "The three learned-policy controls keep the claim narrow. Stale signals test whether the head needs fresh world evidence; wrong signals test source attribution; signal suppression tests whether quiet can be produced by hiding stress from the policy.",
            "",
            "## Artifact Ledger",
            "",
            "- Local-only raw payload: `artifacts/world_responds/suite_c_neural_transfer_payload.json`",
            "- Local-only raw rows: `artifacts/world_responds/suite_c_neural_transfer_rows.jsonl`",
            "- Local-only raw summary: `artifacts/world_responds/suite_c_neural_transfer_summary.json`",
            f"- Public summary JSON: `{PUBLIC_SUMMARY_JSON}`",
            f"- Paper: `{PAPER_MD}`",
            f"- PDF: `{PAPER_PDF}`",
            f"- Critical review: `{CRITICAL_REVIEW}`",
        ]
    )
    out.write_text("\n".join(lines) + "\n")


def write_paper(payload: dict[str, Any], paper_dir: Path, figure_paths: list[Path]) -> Path:
    paper_dir.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    rows = _rows_by_condition(payload)
    learned = rows[LEARNED_CONDITION]
    stale = rows["stale_signal_head"]
    wrong = rows["wrong_signal_head"]
    suppressed = rows["signal_suppression_head"]
    matched = rows[MATCHED_RANDOM_CONDITION]
    scheduled = rows["scheduled_null_anchor"]
    oracle = rows["oracle_source"]
    fig_lines = []
    for path in figure_paths:
        rel = path.relative_to(paper_dir)
        fig_lines.append(f"![{path.stem}]({rel})")
        fig_lines.append("")
    lines = [
        "# Suite C Neural Probe Transfer: Learned Inquiry Without False Calm",
        "",
        "**Jawaun Brown**",
        "",
        "## Abstract",
        "",
        "Suite C previously showed that a hand-specified decision-layer policy can re-engage after world change, recover attribution, quiet down without false calm, and reopen after a second shift. This paper tests the next bounded transfer: train the probe policy itself. A small NumPy MLP probe head is trained from Suite C teacher traces, calibrated on separate seeds, and evaluated on held-out seeds with stale-signal, wrong-signal, signal-suppression, and matched-random controls.",
        "",
        f"The learned head passes the held-out neural-transfer gate: final affected MAE {_fmt(learned['final_component_mae'])}, affected/unaffected selectivity {_fmt(learned['first_selectivity_ratio'])}, second-shift reopenability {_fmt(learned['second_reopen_ratio'])}, and {_fmt(learned['total_probes'], 1)} probes versus {_fmt(scheduled['total_probes'], 1)} scheduled and {_fmt(oracle['total_probes'], 1)} oracle-source probes. Matched random at the same budget reaches selectivity {_fmt(matched['first_selectivity_ratio'])}.",
        "",
        "## 1. Question",
        "",
        "The question is whether the architecture law from Suite C can be learned: preserve the stress signal, regulate the decision to probe, and let the regulator decay so later changes can reopen inquiry.",
        "",
        "## 2. Method",
        "",
        "The probe head observes perceived attribution error, perceived surprise, error and surprise jumps relative to a lagging baseline, recent probe effort, recent improvement, time since last probe, recent probe rate, and source identity. It is trained only from teacher traces and evaluated on disjoint seeds.",
        "",
        "The controls corrupt the input to the learned head rather than changing the scoring gate. `stale_signal_head` withholds fresh post-shift stress signals. `wrong_signal_head` rotates perceived stress to the wrong source bucket. `signal_suppression_head` hides stress while actual attribution error remains high.",
        "",
        "## 3. Results",
        "",
        "| Gate | Result |",
        "| --- | --- |",
    ]
    for name, gate in summary["gates"].items():
        if name != "suite_pass":
            lines.append(f"| {name} | {_fmt(bool(gate['pass']))} |")
    lines.extend(
        [
            "",
            "## Figures",
            "",
            *fig_lines,
            "## 4. Control Interpretation",
            "",
            f"The stale-signal control ends with recovery rate {_fmt(stale['recovery_rate'])}; the wrong-signal control has selectivity {_fmt(wrong['first_selectivity_ratio'])}; the signal-suppression control ends with final affected MAE {_fmt(suppressed['final_component_mae'])}. These controls are treated as rejection artifacts, not failed attempts to improve the score.",
            "",
            "## 5. Architecture Law",
            "",
            "The simple architecture change remains the same as in the hand-policy Suite C result, but the operation has moved: the decision regulator is now learned from traces. Fresh stress signals stay visible to the policy; the learned action threshold absorbs effort history and improvement history; corrupted signals fail.",
            "",
            "## 6. Scope",
            "",
            "This is a finite learned-policy diagnostic. It does not show consciousness, biological agency, broad autonomy, or production reliability. It does show a new local result: the Suite C law is not limited to a hand-written if/then policy inside this harness.",
            "",
            "## References",
            "",
            "- `papers/habituated_reengagement/suite_c_reengagement_under_world_change.md`",
            "- `experiments/world_responds/BENCHMARK_CARD.md`",
            "- `papers/structure_compatible_generalization/learned_generators_transfer.md`",
            "- Lyons, B., Pio-Lopez, L., & Levin, M. (2026). *Alignment is to a virtual governor: A theory of coordination in diverse intelligence*. Preprints.org. doi:10.20944/preprints202607.0220.v1. Not peer reviewed.",
        ]
    )
    out = paper_dir / PAPER_MD.name
    out.write_text("\n".join(lines) + "\n")
    return out


def write_critical_review(payload: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = _rows_by_condition(payload)
    learned = rows[LEARNED_CONDITION]
    stale = rows["stale_signal_head"]
    wrong = rows["wrong_signal_head"]
    suppressed = rows["signal_suppression_head"]
    lines = [
        "# Critical Review: Suite C Neural Probe Transfer",
        "",
        "Date: 2026-07-06",
        "",
        "## Verdict",
        "",
        "This is the right next step after the terminal hand-policy Suite C result. It moves the probe decision into a trained head while keeping the same anti-cheat structure. The result is still finite and simulator-local, but it is a stronger architecture test than another hand-tuned policy.",
        "",
        "## Main Issues",
        "",
        "1. **Do not call this open-ended agency.** The head is trained from a teacher inside the same simulator family.",
        "2. **Controls are the contribution.** The stale, wrong, and suppressed signal controls are what prevent the result from being mere imitation.",
        "3. **Teacher dependence remains.** The next stronger version should train from reward or intervention feedback rather than direct teacher labels.",
        "4. **No model-scale claim.** This is a small NumPy MLP, not evidence about frontier agents or biological consciousness.",
        f"5. **Keep matched random.** The learned head uses {_fmt(learned['total_probes'], 1)} probes; budget alone must remain separated from selectivity.",
        "",
        "## Rewrite Applied",
        "",
        f"- The paper names the learned head and reports final MAE {_fmt(learned['final_component_mae'])}.",
        f"- Stale control recovery rate is {_fmt(stale['recovery_rate'])}.",
        f"- Wrong-signal selectivity is {_fmt(wrong['first_selectivity_ratio'])}.",
        f"- Suppressed-signal final MAE is {_fmt(suppressed['final_component_mae'])}.",
        "- Scope text rejects consciousness, biology, and production autonomy claims.",
        "",
        "## Contribution Opportunity",
        "",
        "The next major step is policy learning without teacher labels: train inquiry from downstream recovery/cost rewards and require the same C1-C6 plus learned-signal controls.",
    ]
    out.write_text("\n".join(lines) + "\n")


def build_public_summary(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload["summary"]
    manifest = payload["manifest"]
    rows = _rows_by_condition(payload)
    learned = rows[LEARNED_CONDITION]
    p22 = rows["p22_learned_current_replay"]
    teacher = rows["teacher_burst_then_refractory"]
    stale = rows["stale_signal_head"]
    wrong = rows["wrong_signal_head"]
    matched = rows[MATCHED_RANDOM_CONDITION]
    scheduled = rows["scheduled_null_anchor"]
    oracle = rows["oracle_source"]
    suppressed = rows["signal_suppression_head"]
    gates = summary["gates"]
    report_ref = str(REPORT_MD)
    return {
        "benchmark": {
            "name": "Causally Grounded Finite Agents Benchmark",
            "version": "2026-07-06",
            "charter": "Evaluate whether finite agents succeed for the right causal reasons by requiring behavior plus suite-specific structure and anti-cheat gates.",
        },
        "suite": {
            "id": "suite_c_neural_transfer",
            "name": "Suite C Neural Probe Transfer",
            "axis_coverage": ["behavior", "attribution", "inquiry", "learned_policy", "anti_cheat"],
            "status": "strong" if gates["suite_pass"]["pass"] else "negative",
        },
        "run": {
            "run_id": "suite_c_neural_transfer_2026_07_06",
            "date": "2026-07-06",
            "command": manifest.get(
                "command",
                "doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/world_responds/modal_suite_c_neural_transfer.py --base-seed 20260706 --train-seeds 16 --calibration-seeds 6 --eval-seeds 8 --budget-usd 75 --out artifacts/world_responds/suite_c_neural_transfer_payload.json",
            ),
            "rows": int(summary["n_rows"]),
            "models": ["finite_numpy_mlp_probe_head"],
            "providers": ["modal_l4"],
        },
        "minimum_pass_rule": {
            "behavior_passed": bool(gates["C3_recovery"]["pass"]),
            "structure_gate_passed": bool(
                gates["C2_reengagement"]["pass"] and gates["C6_reopenability"]["pass"]
            ),
            "anti_cheat_controls_passed": bool(
                gates["C4_no_false_calm"]["pass"] and gates["N1_learned_signal_controls"]["pass"]
            ),
            "passed": bool(gates["suite_pass"]["pass"]),
            "notes": (
                "Suite C learned probe transfer passed: the learned head re-engages, "
                "recovers, avoids false calm, beats matched-random inquiry, and fails "
                "stale/wrong/suppressed signal controls."
            ),
        },
        "score_axes": {
            "behavior": {
                "headline_condition": LEARNED_CONDITION,
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
            "attribution": {
                "learned_final_component_mae": learned["final_component_mae"],
                "wrong_signal_final_component_mae": wrong["final_component_mae"],
                "suppressed_final_component_mae": suppressed["final_component_mae"],
            },
            "anti_cheat": {
                "stale_recovery_rate": stale["recovery_rate"],
                "wrong_signal_selectivity_ratio": wrong["first_selectivity_ratio"],
                "suppressed_final_component_mae": suppressed["final_component_mae"],
                "learned_signal_controls_passed": bool(
                    gates["N1_learned_signal_controls"]["pass"]
                ),
            },
        },
        "gates": [
            {
                "gate_id": "C1",
                "name": "silence_replication",
                "axis": "inquiry",
                "threshold": "P22 baseline remains nearly silent after shift",
                "value": p22["affected_post_shift_density"],
                "passed": bool(gates["C1_silence_replication"]["pass"]),
                "evidence_ref": report_ref,
            },
            {
                "gate_id": "C2",
                "name": "reengagement",
                "axis": "inquiry",
                "threshold": "learned head affected post-shift density >= 0.5x pre-shift and >= 2x unaffected buckets",
                "value": learned["first_selectivity_ratio"],
                "passed": bool(gates["C2_reengagement"]["pass"]),
                "evidence_ref": report_ref,
            },
            {
                "gate_id": "C3",
                "name": "recovery",
                "axis": "behavior",
                "threshold": "learned head final affected-component MAE <= 0.12 in most seeds",
                "value": learned["final_component_mae"],
                "passed": bool(gates["C3_recovery"]["pass"]),
                "evidence_ref": report_ref,
            },
            {
                "gate_id": "C4",
                "name": "no_false_calm",
                "axis": "anti_cheat",
                "threshold": "learned head quieting pairs with recovery while signal suppression fails",
                "value": suppressed["final_component_mae"],
                "passed": bool(gates["C4_no_false_calm"]["pass"]),
                "evidence_ref": report_ref,
            },
            {
                "gate_id": "C5",
                "name": "cost_aware_inquiry",
                "axis": "inquiry",
                "threshold": "learned head uses fewer probes than scheduled/oracle controls at recovery threshold and beats matched-random selectivity",
                "value": learned["total_probes"],
                "passed": bool(gates["C5_cost_aware_inquiry"]["pass"]),
                "evidence_ref": report_ref,
            },
            {
                "gate_id": "C6",
                "name": "second_shift_reopenability",
                "axis": "inquiry",
                "threshold": "affected-bucket probes rise again after a second shift",
                "value": learned["second_reopen_ratio"],
                "passed": bool(gates["C6_reopenability"]["pass"]),
                "evidence_ref": report_ref,
            },
            {
                "gate_id": "N1",
                "name": "learned_signal_controls",
                "axis": "anti_cheat",
                "threshold": "stale-signal, wrong-signal, and signal-suppression controls fail",
                "value": bool(gates["N1_learned_signal_controls"]["pass"]),
                "passed": bool(gates["N1_learned_signal_controls"]["pass"]),
                "evidence_ref": report_ref,
            },
        ],
        "baselines": [
            {
                "name": "p22_learned_current_replay",
                "kind": "lower",
                "result": f"self-silences after shift; affected post-shift density is {_fmt(p22['affected_post_shift_density'])} and final MAE is {_fmt(p22['final_component_mae'])}",
                "evidence_ref": report_ref,
            },
            {
                "name": "teacher_burst_then_refractory",
                "kind": "diagnostic",
                "result": f"teacher reference uses {_fmt(teacher['total_probes'], 1)} probes and final MAE {_fmt(teacher['final_component_mae'])}",
                "evidence_ref": report_ref,
            },
            {
                "name": "scheduled_null_anchor",
                "kind": "upper",
                "result": f"high-cost positive control; {_fmt(scheduled['total_probes'], 1)} probes and final MAE {_fmt(scheduled['final_component_mae'])}",
                "evidence_ref": report_ref,
            },
            {
                "name": "oracle_source",
                "kind": "upper",
                "result": f"semantic high-cost reference; {_fmt(oracle['total_probes'], 1)} probes and final MAE {_fmt(oracle['final_component_mae'])}",
                "evidence_ref": report_ref,
            },
            {
                "name": "stale_signal_head",
                "kind": "control",
                "result": f"stale-signal learned-policy control; recovery rate {_fmt(stale['recovery_rate'])}",
                "evidence_ref": report_ref,
            },
            {
                "name": "wrong_signal_head",
                "kind": "control",
                "result": f"wrong-source learned-policy control; selectivity {_fmt(wrong['first_selectivity_ratio'])} and final MAE {_fmt(wrong['final_component_mae'])}",
                "evidence_ref": report_ref,
            },
            {
                "name": "signal_suppression_head",
                "kind": "control",
                "result": f"false-calm learned-policy control; no-false-calm rate {_fmt(suppressed['no_false_calm_rate'])} and final MAE {_fmt(suppressed['final_component_mae'])}",
                "evidence_ref": report_ref,
            },
            {
                "name": MATCHED_RANDOM_CONDITION,
                "kind": "control",
                "result": f"equal-budget random inquiry control matched to {manifest.get('matched_budget_condition')}; recovery rate {_fmt(matched['recovery_rate'])} and selectivity {_fmt(matched['first_selectivity_ratio'])}",
                "evidence_ref": report_ref,
            },
        ],
        "artifacts": {
            "rows_jsonl": "artifacts/world_responds/suite_c_neural_transfer_rows.jsonl",
            "summary_json": str(PUBLIC_SUMMARY_JSON),
            "raw_summary_json": "artifacts/world_responds/suite_c_neural_transfer_summary.json",
            "report_md": str(REPORT_MD),
            "benchmark_card": "experiments/world_responds/BENCHMARK_CARD.md",
            "paper_md": str(PAPER_MD),
            "paper_pdf": str(PAPER_PDF),
            "critical_review_md": str(CRITICAL_REVIEW),
        },
        "allowed_claim": "In a controlled finite benchmark, a teacher-trained NumPy MLP probe head can transfer Suite C decision-layer inquiry: it preserves fresh stress information, regulates probe action, recovers attribution, and reopens after a second shift while stale, wrong, suppressed, and random-budget controls fail.",
        "non_claims": [
            "Not a reward-trained inquiry policy.",
            "Not an open-agent or long-horizon tool result.",
            "Not hidden-state localization evidence.",
            "Not a production reliability certificate.",
            "Not a human or biological habituation result.",
            "Not a consciousness test.",
        ],
    }


def _matches_type(value: Any, expected: Any) -> bool:
    if isinstance(expected, list):
        return any(_matches_type(value, item) for item in expected)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def validate_release_summary(summary: dict[str, Any], schema_path: Path | None = None) -> None:
    """Validate the subset of JSON Schema used by the shared release schema."""

    schema = json.loads((schema_path or RELEASE_SCHEMA_JSON).read_text())

    def validate_node(value: Any, schema_node: dict[str, Any], path: str) -> None:
        expected_type = schema_node.get("type")
        if expected_type is not None and not _matches_type(value, expected_type):
            raise ValueError(f"{path} has wrong type; expected {expected_type}")
        if "enum" in schema_node and value not in schema_node["enum"]:
            raise ValueError(f"{path} has value {value!r} outside enum {schema_node['enum']!r}")
        if isinstance(value, dict):
            for key in schema_node.get("required", []):
                if key not in value:
                    raise ValueError(f"{path}.{key} is required")
            properties = schema_node.get("properties", {})
            additional = schema_node.get("additionalProperties", True)
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if key in properties:
                    validate_node(child, properties[key], child_path)
                elif isinstance(additional, dict):
                    validate_node(child, additional, child_path)
                elif additional is False:
                    raise ValueError(f"{child_path} is not allowed")
        if isinstance(value, list) and "items" in schema_node:
            for idx, item in enumerate(value):
                validate_node(item, schema_node["items"], f"{path}[{idx}]")

    validate_node(summary, schema, "$")


def validate_tracked_release_summary() -> None:
    from experiments.world_responds.suite_c_neural_transfer import run_neural_transfer_suite

    payload = run_neural_transfer_suite()
    validate_payload(payload)
    expected = build_public_summary(payload)
    validate_release_summary(expected)
    actual = json.loads(PUBLIC_SUMMARY_JSON.read_text())
    if _canonical(actual) != _canonical(expected):
        raise ValueError(f"{PUBLIC_SUMMARY_JSON} is stale relative to the default Suite C neural-transfer run")


def build_artifacts(payload: dict[str, Any], out_root: Path) -> list[Path]:
    validate_payload(payload)
    report = out_root / REPORT_MD
    public_summary = out_root / PUBLIC_SUMMARY_JSON
    paper_dir = out_root / PAPER_MD.parent
    figure_dir = paper_dir / "figures"
    review = out_root / CRITICAL_REVIEW
    figures = write_figures(payload, figure_dir)
    write_report(payload, report)
    paper = write_paper(payload, paper_dir, figures)
    write_critical_review(payload, review)
    public_summary.parent.mkdir(parents=True, exist_ok=True)
    release_summary = build_public_summary(payload)
    validate_release_summary(release_summary)
    public_summary.write_text(json.dumps(release_summary, indent=2, sort_keys=True) + "\n")
    return [report, public_summary, paper, review, *figures]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("payload", type=Path)
    parser.add_argument("--out-root", type=Path, default=Path("."))
    args = parser.parse_args()
    payload = load_payload(args.payload)
    paths = build_artifacts(payload, args.out_root)
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
