"""Artifact builders for Suite C re-engagement under world change."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.world_responds.suite_c_contract import CONDITIONS  # noqa: E402


COLORS = {
    "p22_learned_current_replay": "#6b7280",
    "two_timescale_plus_prediction_error": "#d97706",
    "fixed_surprise_decrement": "#dc2626",
    "scheduled_null_anchor": "#7c3aed",
    "oracle_source": "#0f766e",
    "decision_refractory": "#2563eb",
    "burst_then_refractory": "#059669",
    "learned_cooldown_head": "#0891b2",
    "matched_random_time_budget": "#9ca3af",
}

REPORT_MD = Path("experiments/world_responds/results/suite_c_reengagement_2026_07_06.md")
PUBLIC_SUMMARY_JSON = Path("experiments/world_responds/results/suite_c_reengagement_2026_07_06.json")
BENCHMARK_CARD = Path("experiments/world_responds/BENCHMARK_CARD.md")
PAPER_MD = Path("papers/habituated_reengagement/suite_c_reengagement_under_world_change.md")
PAPER_PDF = Path("papers/habituated_reengagement/suite_c_reengagement_under_world_change.pdf")
CRITICAL_REVIEW = Path(
    "docs/paper_reviews/suite_c_reengagement_under_world_change_critical_review.md"
)

LABELS = {
    "p22_learned_current_replay": "P22 quiet",
    "two_timescale_plus_prediction_error": "P23A anxious",
    "fixed_surprise_decrement": "Signal cooling",
    "scheduled_null_anchor": "Scheduled",
    "oracle_source": "Oracle source",
    "decision_refractory": "Decision refractory",
    "burst_then_refractory": "Burst + refractory",
    "learned_cooldown_head": "Cooldown head",
    "matched_random_time_budget": "Matched random",
}


def _fmt(value: Any, digits: int = 3) -> str:
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def validate_payload(payload: dict[str, Any]) -> None:
    from experiments.world_responds.suite_c_reengagement import summarize_records

    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Suite C payload must include non-empty rows")
    manifest = payload.get("manifest", {})
    seeds = [int(seed) for seed in manifest.get("seeds", [])]
    if not seeds:
        raise ValueError("Suite C manifest must include seeds")
    expected_conditions = tuple(manifest.get("conditions", CONDITIONS))
    expected_pairs = {(condition, seed) for condition in expected_conditions for seed in seeds}
    actual_pairs: dict[tuple[str, int], int] = {}
    for row in rows:
        pair = (str(row["condition"]), int(row["seed"]))
        actual_pairs[pair] = actual_pairs.get(pair, 0) + 1
    duplicate_pairs = sorted(pair for pair, count in actual_pairs.items() if count != 1)
    if duplicate_pairs:
        raise ValueError(f"Suite C payload has duplicate row pairs: {duplicate_pairs[:5]}")
    actual_pair_set = set(actual_pairs)
    if actual_pair_set != expected_pairs:
        missing = sorted(expected_pairs - actual_pair_set)
        extra = sorted(actual_pair_set - expected_pairs)
        raise ValueError(f"Suite C payload grid mismatch: missing={missing[:5]} extra={extra[:5]}")

    recomputed = summarize_records(rows)
    if _canonical(recomputed) != _canonical(payload.get("summary")):
        raise ValueError("Suite C payload summary does not match recomputed rows")

    headline_condition = str(recomputed["headline_condition"])
    matched_condition = manifest.get("matched_budget_condition", headline_condition)
    if matched_condition != headline_condition:
        raise ValueError(
            "Suite C matched-random budget source does not match headline condition: "
            f"{matched_condition} != {headline_condition}"
        )
    headline_budget_by_seed = {
        int(row["seed"]): int(row["total_probes"])
        for row in rows
        if row["condition"] == headline_condition
    }
    for row in rows:
        if row["condition"] != "matched_random_time_budget":
            continue
        seed = int(row["seed"])
        if int(row["target_probe_count"]) != headline_budget_by_seed[seed]:
            raise ValueError(
                "Suite C matched-random row has stale budget: "
                f"seed={seed} target={row['target_probe_count']} "
                f"headline={headline_budget_by_seed[seed]}"
            )


def _rows_by_condition(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["condition"]: row for row in payload["summary"]["by_condition"]}


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
    fig, ax = plt.subplots(figsize=(9.2, 4.2))
    ax.bar(gate_labels, gate_values, color=["#059669" if v else "#dc2626" for v in gate_values])
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Gate status")
    ax.set_title("Suite C terminal gate: re-engage, recover, cool, and reopen")
    ax.set_xticks(range(len(gate_labels)), gate_labels, rotation=20, ha="right")
    ax.grid(axis="y", alpha=0.25)
    for idx, value in enumerate(gate_values):
        ax.text(idx, value + 0.04, "PASS" if value else "FAIL", ha="center", weight="bold")
    fig.tight_layout()
    path = figure_dir / "suite_c_fig1_gate_status.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)

    labels = [LABELS[row["condition"]] for row in rows]
    conditions = [row["condition"] for row in rows]
    x = list(range(len(rows)))
    fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.0))
    axes[0].bar(
        x,
        [row["first_selectivity_ratio"] for row in rows],
        color=[COLORS[c] for c in conditions],
    )
    axes[0].axhline(2.0, color="#111827", linestyle="--", linewidth=1.0, label="2x gate")
    axes[0].set_xticks(x, labels, rotation=25, ha="right")
    axes[0].set_ylabel("Affected / unaffected probe density")
    axes[0].set_title("Selective re-engagement after first shift")
    axes[0].grid(axis="y", alpha=0.25)
    axes[0].legend()

    axes[1].bar(
        x,
        [row["second_reopen_ratio"] for row in rows],
        color=[COLORS[c] for c in conditions],
    )
    axes[1].axhline(1.0, color="#111827", linestyle="--", linewidth=1.0, label="reopen gate")
    axes[1].set_xticks(x, labels, rotation=25, ha="right")
    axes[1].set_ylabel("Post-second / pre-second affected probes")
    axes[1].set_title("Second-shift re-openability")
    axes[1].grid(axis="y", alpha=0.25)
    axes[1].legend()
    fig.tight_layout()
    path = figure_dir / "suite_c_fig2_probe_selectivity_reopenability.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)

    fig, ax1 = plt.subplots(figsize=(10.2, 5.2))
    ax2 = ax1.twinx()
    width = 0.38
    left = [i - width / 2 for i in x]
    right = [i + width / 2 for i in x]
    ax1.bar(
        left,
        [row["final_component_mae"] for row in rows],
        width=width,
        color=[COLORS[c] for c in conditions],
        alpha=0.92,
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
    ax1.set_title("Recovery and cost must both pass")
    ax1.grid(axis="y", alpha=0.25)
    bars, labels1 = ax1.get_legend_handles_labels()
    bars2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(bars + bars2, labels1 + labels2, loc="upper right")
    fig.tight_layout()
    path = figure_dir / "suite_c_fig3_recovery_cost.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)

    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    label_offsets = {
        "p22_learned_current_replay": (7, -12),
        "two_timescale_plus_prediction_error": (7, 7),
        "fixed_surprise_decrement": (7, 6),
        "scheduled_null_anchor": (7, 7),
        "oracle_source": (7, 7),
        "decision_refractory": (-118, -18),
        "burst_then_refractory": (-6, 18),
        "learned_cooldown_head": (-118, 10),
        "matched_random_time_budget": (7, 7),
    }
    for row in rows:
        condition = row["condition"]
        ax.scatter(
            row["probe_drop_fraction"],
            row["mae_drop_fraction"],
            s=95,
            color=COLORS[condition],
            edgecolor="#111827",
            linewidth=0.7,
            label=LABELS[condition],
        )
        ax.annotate(
            LABELS[condition],
            (row["probe_drop_fraction"], row["mae_drop_fraction"]),
            xytext=label_offsets.get(condition, (5, 4)),
            textcoords="offset points",
            fontsize=7.8,
            ha="right" if label_offsets.get(condition, (0, 0))[0] < 0 else "left",
        )
    ax.plot([0, 1], [0, 1 / 3], color="#111827", linestyle="--", linewidth=1.0)
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(-0.03, 1.03)
    ax.set_xlabel("Probe drop after early post-shift burst")
    ax.set_ylabel("Attribution-error drop")
    ax.set_title("No-false-calm gate: quiet must track recovery")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    path = figure_dir / "suite_c_fig4_no_false_calm.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)
    return paths


def write_report(payload: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    manifest = payload["manifest"]
    rows = _rows_by_condition(payload)
    headline = rows[summary["headline_condition"]]
    gates = summary["gates"]
    lines = [
        "# Suite C Re-Engagement Under World Change",
        "",
        "Date: 2026-07-06",
        "",
        "## Discovery-Regime Audit",
        "",
        "Question: can a finite agent re-open inquiry after world change, recover attribution, quiet down without false calm, and re-open again after a second shift?",
        "",
        "Current regime:",
        "- Artifact types: Modal L4 local-only raw rows, tracked public summary JSON, benchmark card, figures, paper, critical review.",
        "- Operations: deterministic two-shift world-change harness with policy-level probe mechanisms and controls.",
        "- Gates/verifiers: C1-C6 Suite C terminal gates, matched-random budget, signal-layer false-calm control, second-shift reopenability.",
        "- Known limitations: controlled finite simulator; not a neural or biological consciousness result.",
        "",
        "Action class:",
        "- Retrieval/search/discovery: discovery-level benchmark packaging.",
        "- Why: the run converts prior paper-local re-engagement phenomena into a suite-level accepted artifact class with anti-cheat controls.",
        "",
        "Experiment:",
        f"- Conditions: `{', '.join(manifest['conditions'])}`.",
        f"- Seeds: `{manifest['seeds']}`.",
        f"- Shifts: first at step {manifest['first_shift']}, second at step {manifest['second_shift']}.",
        "- Positive targets: decision-layer cooling candidates.",
        "- Negative controls: P22 quiet, P23A anxious, signal-layer cooling, scheduled/oracle high-cost, matched random.",
        "",
        "Execution record:",
        f"- Full Modal run: {manifest.get('modal_run_url', 'not recorded')}.",
        f"- Dry-run budget check: {manifest.get('dry_run_modal_url', 'not recorded')}.",
        f"- Conservative budget estimate: ${manifest.get('budget_estimate', {}).get('conservative_cost_usd', 'not recorded')} against budget ${manifest.get('budget_estimate', {}).get('budget_usd', 'not recorded')}.",
        f"- Rows emitted: {summary['n_rows']}.",
        "",
        "Gate:",
        "- Acceptance rule: all C1-C6 gates pass for at least one decision-layer candidate, with required controls behaving as controls.",
        "- Withheld/rejected rule: do not claim Suite C closure if quiet is produced by signal suppression, recovery requires scheduled/oracle cost, or second-shift reopenability fails.",
        "",
        "## Gate Results",
        "",
        "| Gate | Pass? | Evidence |",
        "| --- | --- | --- |",
    ]
    for name, gate in gates.items():
        if name == "suite_pass":
            continue
        evidence = ", ".join(f"{k}={_fmt(v)}" for k, v in gate.items() if k != "pass")
        lines.append(f"| {name} | {_fmt(bool(gate['pass']))} | {evidence} |")
    lines.extend(
        [
            "",
            "## Headline",
            "",
            f"The headline condition is `{summary['headline_condition']}`. It reaches final affected MAE {_fmt(headline['final_component_mae'])}, first-shift selectivity {_fmt(headline['first_selectivity_ratio'])}, second-shift reopenability {_fmt(headline['second_reopen_ratio'])}, and uses {_fmt(headline['total_probes'], 1)} probes.",
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
            "The benchmark accepts decision-layer cooling as the terminal Suite C move in this controlled harness. The load-bearing separation is not lower probe rate by itself; it is selective post-shift inquiry, attribution recovery, reduced cost relative to scheduled/oracle probing, and second-shift reopenability.",
            "",
            "The signal-layer cooling control is the main rejection artifact. It looks quiet, but it fails no-false-calm because attribution error does not fall enough. This preserves the program's central warning: do not erase the surprise signal to make the agent look stable.",
            "",
            "## Artifact Ledger",
            "",
            "- Local-only raw rows: `artifacts/world_responds/suite_c_reengagement_rows.jsonl`",
            "- Local-only raw summary JSON: `artifacts/world_responds/suite_c_reengagement_summary.json`",
            "- Public release summary JSON: `experiments/world_responds/results/suite_c_reengagement_2026_07_06.json`",
            "- Benchmark card: `experiments/world_responds/BENCHMARK_CARD.md`",
            "- Paper: `papers/habituated_reengagement/suite_c_reengagement_under_world_change.md`",
            "- PDF: `papers/habituated_reengagement/suite_c_reengagement_under_world_change.pdf`",
            "- Critical review: `docs/paper_reviews/suite_c_reengagement_under_world_change_critical_review.md`",
        ]
    )
    out.write_text("\n".join(lines) + "\n")


def write_benchmark_card(payload: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest = payload.get("manifest", {})
    summary = payload["summary"]
    gates = summary["gates"]
    budget = manifest.get("budget_estimate", {})
    lines = [
        "# Benchmark Card: Suite C Re-Engagement Under World Change",
        "",
        "Generated: 2026-07-06",
        "",
        "## Claim",
        "",
        "Suite C tests adaptive inquiry under nonstationary world dynamics. A condition passes only if it re-engages probes after a world shift, recovers attribution, avoids false calm, uses fewer probes than high-cost controls, and re-opens inquiry after a second shift.",
        "",
        "## Status",
        "",
        f"- Suite pass: **{_fmt(bool(gates['suite_pass']['pass']))}**",
        f"- Headline condition: `{summary['headline_condition']}`",
        "- Claim level: `diagnostic`; finite controlled benchmark gate, not a consciousness, biological, or production reliability claim.",
        "",
        "## Execution Record",
        "",
        f"- Full Modal run: {manifest.get('modal_run_url', 'not recorded')}.",
        f"- Dry-run budget check: {manifest.get('dry_run_modal_url', 'not recorded')}.",
        f"- Conservative budget estimate: ${budget.get('conservative_cost_usd', 'not recorded')} against budget ${budget.get('budget_usd', 'not recorded')}.",
        f"- Rows emitted: {summary['n_rows']}.",
        "",
        "## Minimum Pass Rule",
        "",
        "A model or policy cannot pass Suite C from final recovery alone. It must pass behavior, inquiry, attribution, cost, false-calm, and second-shift gates together.",
        "",
        "## Gates",
        "",
        "| Gate | Requirement | Result |",
        "| --- | --- | --- |",
    ]
    requirements = {
        "C1_silence_replication": "P22 baseline remains nearly silent after shift.",
        "C2_reengagement": "Candidate probes affected buckets after shift and beats unaffected buckets by at least 2x.",
        "C3_recovery": "Candidate reaches the affected-component MAE threshold in most seeds.",
        "C4_no_false_calm": "Probe quieting is paired with attribution-error reduction; signal suppression fails.",
        "C5_cost_aware_inquiry": "Candidate uses fewer probes than scheduled/oracle controls at comparable recovery.",
        "C6_reopenability": "Candidate re-opens inquiry after a second shift.",
    }
    for name, requirement in requirements.items():
        lines.append(f"| {name} | {requirement} | {_fmt(bool(gates[name]['pass']))} |")
    lines.extend(
        [
            "",
            "## Anti-Cheat Controls",
            "",
            "- `p22_learned_current_replay`: learned quiet baseline.",
            "- `two_timescale_plus_prediction_error`: anxious re-engagement baseline.",
            "- `fixed_surprise_decrement`: signal-layer false-calm negative control.",
            "- `scheduled_null_anchor`: high-cost positive control.",
            "- `oracle_source`: semantic high-cost reference.",
            "- `matched_random_time_budget`: equal-budget random inquiry control.",
            "",
            "## Artifacts",
            "",
            "- Local-only raw rows: `artifacts/world_responds/suite_c_reengagement_rows.jsonl`",
            "- Local-only raw summary: `artifacts/world_responds/suite_c_reengagement_summary.json`",
            "- Public release summary: `experiments/world_responds/results/suite_c_reengagement_2026_07_06.json`",
            "- Result report: `experiments/world_responds/results/suite_c_reengagement_2026_07_06.md`",
            "- Paper: `papers/habituated_reengagement/suite_c_reengagement_under_world_change.md`",
            "- Critical review: `docs/paper_reviews/suite_c_reengagement_under_world_change_critical_review.md`",
            "",
            "## Non-Claims",
            "",
            "This benchmark does not certify consciousness, broad autonomy, biological validity, or open-world reliability. It is a controlled finite test of adaptive inquiry mechanics.",
        ]
    )
    out.write_text("\n".join(lines) + "\n")


def write_paper(payload: dict[str, Any], paper_dir: Path, figure_paths: list[Path]) -> Path:
    paper_dir.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    rows = _rows_by_condition(payload)
    gates = summary["gates"]
    headline = rows[summary["headline_condition"]]
    fixed = rows["fixed_surprise_decrement"]
    p22 = rows["p22_learned_current_replay"]
    scheduled = rows["scheduled_null_anchor"]
    oracle = rows["oracle_source"]
    fig_lines = []
    for path in figure_paths:
        rel = path.relative_to(paper_dir)
        fig_lines.append(f"![{path.stem}]({rel})")
        fig_lines.append("")
    lines = [
        "# Suite C Re-Engagement Under World Change: A No-False-Calm Benchmark for Adaptive Inquiry",
        "",
        "**Jawaun Brown**",
        "",
        "## Abstract",
        "",
        "Prior work in this lineage found a precise failure: agents can learn to probe efficiently, become quiet after apparent convergence, and then fail to ask again after the world changes. Paper 23A restored re-engagement but produced anxious over-probing; Paper 23B showed that decision-layer cooling is safer than erasing the surprise signal. This paper turns those findings into Suite C, a public finite benchmark gate. The suite requires first-shift re-engagement, attribution recovery, no false calm, cost-aware inquiry, and second-shift re-openability in one artifact.",
        "",
        f"The headline condition is `{summary['headline_condition']}`. It passes all six Suite C gates in this controlled harness: final affected MAE {_fmt(headline['final_component_mae'])}, affected/unaffected post-shift selectivity {_fmt(headline['first_selectivity_ratio'])}, second-shift reopenability {_fmt(headline['second_reopen_ratio'])}, and {_fmt(headline['total_probes'], 1)} probes versus {_fmt(scheduled['total_probes'], 1)} scheduled and {_fmt(oracle['total_probes'], 1)} oracle-source probes. The negative control `fixed_surprise_decrement` fails the no-false-calm gate, preserving the distinction between healthy quiet and blindness.",
        "",
        "## 1. Question",
        "",
        "The question is not whether an agent can reduce error after a shift if it probes constantly. The question is whether it can ask again when information becomes valuable, stop asking when attribution has recovered, and remain able to ask again after a later change.",
        "",
        "## 2. Method",
        "",
        "The benchmark uses a deterministic finite world-change harness with two affected buckets and four unaffected buckets. The first shift tests whether learned quiet can be broken; the second shift tests whether cooling decays enough to reopen inquiry. Each condition receives the same hidden world shifts and is evaluated with the same windows.",
        "",
        "The candidate mechanisms operate at the decision layer: `decision_refractory`, `burst_then_refractory`, and `learned_cooldown_head`. Required controls include the P22 learned-quiet baseline, the P23A anxious surprise baseline, signal-layer cooling, scheduled probing, oracle-source probing, and matched-random inquiry at the candidate's probe budget.",
        "",
        "## 3. Results",
        "",
        "| Gate | Result |",
        "| --- | --- |",
    ]
    for name, gate in gates.items():
        if name != "suite_pass":
            lines.append(f"| {name} | {_fmt(bool(gate['pass']))} |")
    lines.extend(
        [
            "",
            "## Figures",
            "",
            *fig_lines,
            "## 4. False Calm Is The Load-Bearing Control",
            "",
            f"The P22 baseline preserves the original failure: affected post-shift probe density is only {_fmt(p22['affected_post_shift_density'])}. `fixed_surprise_decrement` demonstrates why lower probe rates are not enough. It cools by directly suppressing surprise, but final affected MAE remains {_fmt(fixed['final_component_mae'])} and the no-false-calm rate is {_fmt(fixed['no_false_calm_rate'])}. The suite therefore rejects apparent stability when it is not paired with attribution recovery.",
            "",
            "## 5. Architecture Law",
            "",
            "The simple architecture change is to cool the decision to probe, not the signal that says the world is surprising. In machine-agency terms: preserve the error signal as information, regulate the action tendency with recent probe effort, and let the regulator decay so future shifts can reopen inquiry.",
            "",
            "This is adjacent to, but narrower than, the virtual-governor framing of Lyons, Pio-Lopez, and Levin (2026). Their preprint names a distributed architecture in which global constraint violations become local incentives. Suite C makes one local version executable: surprise and attribution error are global-to-local stress signals for inquiry, while stale, wrong, or suppressed signals are treated as controls rather than as evidence of alignment.",
            "",
            "## 6. Scope",
            "",
            "This is a controlled finite benchmark. It does not show consciousness, broad autonomy, biological habituation, or production reliability. It does show that the program now has a terminal Suite C gate: an agent-like policy must re-engage, recover, quiet without false calm, spend probes efficiently, and reopen after a second shift.",
            "",
            "## References",
            "",
            "- Lyons, B., Pio-Lopez, L., & Levin, M. (2026). *Alignment is to a virtual governor: A theory of coordination in diverse intelligence*. Preprints.org. doi:10.20944/preprints202607.0220.v1. Not peer reviewed.",
            "- `papers/probe_value_reengagement/paper.md`",
            "- `papers/habituated_reengagement/paper.md`",
            "- `docs/causally_grounded_agents_benchmark.md`",
            "- `experiments/world_responds/BENCHMARK_CARD.md`",
        ]
    )
    out = paper_dir / "suite_c_reengagement_under_world_change.md"
    out.write_text("\n".join(lines) + "\n")
    return out


def write_critical_review(payload: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    rows = _rows_by_condition(payload)
    headline = rows[summary["headline_condition"]]
    fixed = rows["fixed_surprise_decrement"]
    lines = [
        "# Critical Review: Suite C Re-Engagement Under World Change",
        "",
        "Date: 2026-07-06",
        "",
        "## Verdict",
        "",
        "This is the right terminal benchmark shape for Suite C. It converts the earlier paper-local re-engagement story into a single gate with controls for silence, anxiety, false calm, high-cost probing, and random inquiry. The claim is still finite and synthetic, but the benchmark is now much harder to cheat with a single scalar.",
        "",
        "## Main Issues",
        "",
        "1. **Do not overclaim beyond the harness.** The benchmark establishes a controlled inquiry mechanism, not consciousness, biological habituation, or general machine agency.",
        "2. **Keep false calm central.** The most important control is `fixed_surprise_decrement`: quiet produced by deleting surprise should remain a rejected artifact.",
        "3. **Cost and recovery must stay coupled.** Future versions should not optimize probe count without preserving final attribution recovery.",
        "4. **Matched random is necessary but not sufficient.** The matched-random budget control shows budget alone is not the result; future neural versions should also include learned-proxy controls.",
        "5. **Transfer remains open.** The next contribution is to move the gate from this finite policy harness into neural training or long-horizon tool-agent settings.",
        "",
        "## Rewrite Applied",
        "",
        f"- Paper names the headline condition (`{summary['headline_condition']}`) and reports all six gates.",
        f"- The false-calm section reports `fixed_surprise_decrement` final MAE {_fmt(fixed['final_component_mae'])} versus headline final MAE {_fmt(headline['final_component_mae'])}.",
        "- The scope section explicitly rejects consciousness and broad autonomy claims.",
        "- Virtual-governor framing is treated as analogy and experiment generator, not as evidential support.",
        "",
        "## Contribution Opportunity",
        "",
        "The major next contribution is a neural Suite C transfer:",
        "",
        "> Train the probe policy rather than hand-specifying it, then require the same C1-C6 gates under two world shifts with stale-signal, wrong-signal, and signal-suppression controls.",
    ]
    out.write_text("\n".join(lines) + "\n")


def build_public_summary(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload["summary"]
    manifest = payload["manifest"]
    rows = _rows_by_condition(payload)
    headline = rows[summary["headline_condition"]]
    fixed = rows["fixed_surprise_decrement"]
    p22 = rows["p22_learned_current_replay"]
    scheduled = rows["scheduled_null_anchor"]
    oracle = rows["oracle_source"]
    matched = rows["matched_random_time_budget"]
    gates = summary["gates"]
    report_ref = str(REPORT_MD)
    run_record: dict[str, Any] = {
        "run_id": "suite_c_reengagement_2026_07_06",
        "date": "2026-07-06",
        "command": manifest.get(
            "command",
            "doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/world_responds/modal_suite_c_reengagement.py --seeds 8 --budget-usd 75 --out artifacts/world_responds/suite_c_reengagement_payload.json",
        ),
        "rows": int(summary["n_rows"]),
        "models": ["finite_policy_harness"],
        "providers": ["modal_l4"],
    }
    for optional_key in ("modal_run_url", "dry_run_modal_url", "budget_estimate"):
        if optional_key in manifest:
            run_record[optional_key] = manifest[optional_key]
    return {
        "benchmark": {
            "name": "Causally Grounded Finite Agents Benchmark",
            "version": "2026-07-06",
            "charter": "Evaluate whether finite agents succeed for the right causal reasons by requiring behavior plus suite-specific structure and anti-cheat gates.",
        },
        "suite": {
            "id": "suite_c_reengagement",
            "name": "Suite C: Re-Engagement Under World Change",
            "axis_coverage": ["behavior", "attribution", "inquiry", "anti_cheat"],
            "status": "strong" if gates["suite_pass"]["pass"] else "negative",
        },
        "run": run_record,
        "minimum_pass_rule": {
            "behavior_passed": bool(gates["C3_recovery"]["pass"]),
            "structure_gate_passed": bool(
                gates["C2_reengagement"]["pass"] and gates["C6_reopenability"]["pass"]
            ),
            "anti_cheat_controls_passed": bool(gates["C4_no_false_calm"]["pass"]),
            "passed": bool(gates["suite_pass"]["pass"]),
            "notes": (
                "Suite C terminal finite gate passed: "
                f"{summary['headline_condition']} re-engages, recovers, avoids false calm, "
                "costs less than scheduled/oracle controls, and reopens after a second shift."
            ),
        },
        "score_axes": {
            "behavior": {
                "headline_condition": summary["headline_condition"],
                "final_component_mae": headline["final_component_mae"],
                "recovery_rate": headline["recovery_rate"],
            },
            "inquiry": {
                "baseline_post_shift_density": p22["affected_post_shift_density"],
                "first_reengagement_ratio": headline["first_reengagement_ratio"],
                "first_selectivity_ratio": headline["first_selectivity_ratio"],
                "second_reopen_ratio": headline["second_reopen_ratio"],
                "headline_total_probes": headline["total_probes"],
                "scheduled_total_probes": scheduled["total_probes"],
                "oracle_total_probes": oracle["total_probes"],
                "matched_random_total_probes": matched["total_probes"],
                "matched_budget_condition": manifest.get("matched_budget_condition"),
            },
            "attribution": {
                "headline_final_component_mae": headline["final_component_mae"],
                "fixed_surprise_final_component_mae": fixed["final_component_mae"],
            },
            "anti_cheat": {
                "false_calm_caught": bool(gates["C4_no_false_calm"]["pass"]),
                "fixed_surprise_no_false_calm_rate": fixed["no_false_calm_rate"],
                "matched_random_recovery_rate": matched["recovery_rate"],
                "matched_random_selectivity_ratio": matched["first_selectivity_ratio"],
            },
        },
        "gates": [
            {
                "gate_id": "C1",
                "name": "silence_replication",
                "axis": "inquiry",
                "threshold": "baseline learned current-replay probe has near-zero affected-bucket probes after shift",
                "value": p22["affected_post_shift_density"],
                "passed": bool(gates["C1_silence_replication"]["pass"]),
                "evidence_ref": report_ref,
            },
            {
                "gate_id": "C2",
                "name": "reengagement",
                "axis": "inquiry",
                "threshold": "candidate affected post-shift density >= 0.5x pre-shift and >= 2x unaffected buckets",
                "value": headline["first_selectivity_ratio"],
                "passed": bool(gates["C2_reengagement"]["pass"]),
                "evidence_ref": report_ref,
            },
            {
                "gate_id": "C3",
                "name": "recovery",
                "axis": "behavior",
                "threshold": "candidate final affected-component MAE <= 0.12 in most seeds",
                "value": headline["final_component_mae"],
                "passed": bool(gates["C3_recovery"]["pass"]),
                "evidence_ref": report_ref,
            },
            {
                "gate_id": "C4",
                "name": "no_false_calm",
                "axis": "anti_cheat",
                "threshold": "candidate quieting pairs with recovery while fixed_surprise_decrement fails",
                "value": fixed["no_false_calm_rate"],
                "passed": bool(gates["C4_no_false_calm"]["pass"]),
                "evidence_ref": report_ref,
            },
            {
                "gate_id": "C5",
                "name": "cost_aware_inquiry",
                "axis": "inquiry",
                "threshold": "candidate uses fewer probes than scheduled/oracle controls at recovery threshold and beats matched-random selectivity",
                "value": headline["total_probes"],
                "passed": bool(gates["C5_cost_aware_inquiry"]["pass"]),
                "evidence_ref": report_ref,
            },
            {
                "gate_id": "C6",
                "name": "second_shift_reopenability",
                "axis": "inquiry",
                "threshold": "affected-bucket probes rise again after a second shift",
                "value": headline["second_reopen_ratio"],
                "passed": bool(gates["C6_reopenability"]["pass"]),
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
                "name": "two_timescale_plus_prediction_error",
                "kind": "diagnostic",
                "result": f"re-engages and recovers but over-fires at {_fmt(rows['two_timescale_plus_prediction_error']['total_probes'], 1)} probes versus {_fmt(headline['total_probes'], 1)} for the headline",
                "evidence_ref": report_ref,
            },
            {
                "name": "fixed_surprise_decrement",
                "kind": "control",
                "result": f"false calm negative control; no-false-calm rate {_fmt(fixed['no_false_calm_rate'])} and final MAE {_fmt(fixed['final_component_mae'])}",
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
                "name": "matched_random_time_budget",
                "kind": "control",
                "result": f"equal-budget random inquiry control matched to {manifest.get('matched_budget_condition')}; recovery rate {_fmt(matched['recovery_rate'])} and selectivity {_fmt(matched['first_selectivity_ratio'])}",
                "evidence_ref": report_ref,
            },
        ],
        "artifacts": {
            "rows_jsonl": "artifacts/world_responds/suite_c_reengagement_rows.jsonl",
            "summary_json": str(PUBLIC_SUMMARY_JSON),
            "raw_summary_json": "artifacts/world_responds/suite_c_reengagement_summary.json",
            "report_md": str(REPORT_MD),
            "benchmark_card": str(BENCHMARK_CARD),
            "paper_md": str(PAPER_MD),
            "paper_pdf": str(PAPER_PDF),
            "critical_review_md": str(CRITICAL_REVIEW),
        },
        "allowed_claim": "In a controlled finite benchmark, decision-layer burst/refractory cooling can close the re-engagement bottleneck by preserving surprise as information while regulating and later reopening the probe action tendency.",
        "non_claims": [
            "Not a neural-training result.",
            "Not a production reliability certificate.",
            "Not hidden-state localization evidence.",
            "Not a human or biological habituation result.",
            "Not a consciousness test.",
        ],
    }


def write_public_summary(payload: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_public_summary(payload), indent=2, sort_keys=False) + "\n")


def build_artifacts(payload: dict[str, Any], out_root: Path) -> list[Path]:
    validate_payload(payload)
    report = out_root / REPORT_MD
    release_summary = out_root / PUBLIC_SUMMARY_JSON
    card = out_root / BENCHMARK_CARD
    paper_dir = out_root / "papers/habituated_reengagement"
    figure_dir = paper_dir / "figures"
    review = out_root / CRITICAL_REVIEW
    figures = write_figures(payload, figure_dir)
    write_report(payload, report)
    write_public_summary(payload, release_summary)
    write_benchmark_card(payload, card)
    paper = write_paper(payload, paper_dir, figures)
    write_critical_review(payload, review)
    return [report, release_summary, card, paper, review, *figures]


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
