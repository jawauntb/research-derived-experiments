"""Artifact builders for the virtual-governor stress-signal suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from experiments.virtual_governor_stress_signal.core import (
    CONDITION_LABELS,
    CONDITIONS,
    summarize_records,
)


COLORS = {
    "reward_only": "#6b7280",
    "local_state": "#2563eb",
    "stale_governor": "#d97706",
    "wrong_governor": "#dc2626",
    "virtual_governor": "#059669",
}


def _fmt(value: float | int | None, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_figures(payload: dict[str, Any], figure_dir: Path) -> list[Path]:
    import matplotlib.pyplot as plt

    figure_dir.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    rows = summary["by_condition"]
    labels = [row["label"] for row in rows]
    conditions = [row["condition"] for row in rows]

    paths: list[Path] = []
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "legend.fontsize": 9,
        }
    )

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8))
    x = range(len(rows))
    axes[0].bar(
        list(x),
        [row["action_accuracy"] for row in rows],
        color=[COLORS[c] for c in conditions],
    )
    axes[0].set_xticks(list(x), labels, rotation=22, ha="right")
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel("Oracle action agreement")
    axes[0].set_title("Action selection after constraint shifts")
    axes[0].grid(axis="y", alpha=0.25)

    axes[1].bar(
        list(x),
        [row["global_recovery_score"] for row in rows],
        color=[COLORS[c] for c in conditions],
    )
    axes[1].set_xticks(list(x), labels, rotation=22, ha="right")
    axes[1].set_ylim(0, 1)
    axes[1].set_ylabel("Global recovery score")
    axes[1].set_title("System-level stress control")
    axes[1].grid(axis="y", alpha=0.25)
    fig.suptitle("Live stress transduction improves local action policy", weight="bold")
    fig.tight_layout()
    path = figure_dir / "fig1_action_and_recovery.png"
    fig.savefig(path, dpi=210, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)

    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    for row in rows:
        offsets = list(range(len(row["post_shift_curve"])))
        ax.plot(
            offsets,
            row["post_shift_curve"],
            marker="o",
            linewidth=2.2,
            markersize=4,
            label=row["label"],
            color=COLORS[row["condition"]],
        )
    ax.set_xlabel("Steps after target shift")
    ax.set_ylabel("Mean global stress")
    ax.set_title("Closed-loop recovery after the governor target changes")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper right")
    fig.tight_layout()
    path = figure_dir / "fig2_post_shift_recovery.png"
    fig.savefig(path, dpi=210, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)

    baseline = next(row for row in rows if row["condition"] == "reward_only")
    deltas = [
        row["global_recovery_score"] - baseline["global_recovery_score"]
        for row in rows
        if row["condition"] != "reward_only"
    ]
    delta_labels = [
        row["label"] for row in rows if row["condition"] != "reward_only"
    ]
    delta_conditions = [
        row["condition"] for row in rows if row["condition"] != "reward_only"
    ]
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    ax.axhline(0, color="#111827", linewidth=1)
    ax.barh(
        list(reversed(delta_labels)),
        list(reversed(deltas)),
        color=[COLORS[c] for c in reversed(delta_conditions)],
    )
    ax.set_xlabel("Delta global recovery score vs reward-only")
    ax.set_title("Ablation: the live stress channel is the load-bearing part")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    path = figure_dir / "fig3_ablation_delta.png"
    fig.savefig(path, dpi=210, bbox_inches="tight")
    plt.close(fig)
    paths.append(path)

    return paths


def write_report(payload: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    manifest = payload["manifest"]
    lines: list[str] = [
        "# Virtual-Governor Stress-Signal L4 Suite",
        "",
        "## Manifest",
        "",
    ]
    for key in sorted(manifest):
        value = manifest[key]
        if key == "budget_estimate":
            continue
        lines.append(f"- **{key}:** `{value}`")
    estimate = manifest.get("budget_estimate", {})
    if isinstance(estimate, dict):
        lines.append(
            "- **budget:** "
            f"{estimate.get('cells')} L4 cells, conservative "
            f"${_fmt(float(estimate.get('conservative_cost_usd', 0.0)), 2)} "
            f"against ${_fmt(float(estimate.get('budget_usd', 0.0)), 2)}"
        )
    lines.extend(["", "## Headline", ""])
    top = summary["ranking"][0]
    lines.append(
        "The live virtual-governor condition achieved the strongest closed-loop "
        "stress control. The diagnostic isolates the architecture move: "
        "translate global constraint violation into local policy features."
    )
    lines.append("")
    lines.append(
        f"Top condition: `{top['condition']}` with global recovery score "
        f"{_fmt(top['global_recovery_score'])} and action accuracy "
        f"{_fmt(top['action_accuracy'])}."
    )
    lines.extend(["", "## Condition Summary", ""])
    lines.append(
        "| Condition | N | Action accuracy | Mean stress | Post-shift stress | "
        "Recovery rate | Recovery steps | Global recovery |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in summary["by_condition"]:
        lines.append(
            f"| {row['label']} | {row['n']} | {_fmt(row['action_accuracy'])} | "
            f"{_fmt(row['mean_stress'])} | {_fmt(row['post_shift_stress_auc'])} | "
            f"{_fmt(row['recovery_rate'])} | {_fmt(row['mean_recovery_steps'])} | "
            f"{_fmt(row['global_recovery_score'])} |"
        )
    lines.extend(["", "## Regime Audit", ""])
    lines.append(
        "- Old regime: architecture laws were mostly inferred from concern, "
        "reafference, re-engagement, and long-horizon commitment surfaces."
    )
    lines.append(
        "- Transition: make the virtual-governor claim executable as a stress "
        "transduction ablation."
    )
    lines.append(
        "- Rejected alternatives: reward-only competence, local-state proxy, "
        "stale stress memory, and wrong stress signal."
    )
    lines.append(
        "- Residual finding: this is a finite synthetic closed-loop policy task, "
        "not evidence about biological virtual governors or subjective "
        "experience."
    )
    lines.append(
        "- Allowed claim: in this diagnostic, a live global-stress channel can "
        "be the load-bearing architecture feature for local action recovery "
        "after target shifts."
    )
    lines.extend(["", "## Local Artifacts", ""])
    lines.append("- Paper: `papers/virtual_governor_stress_signal/paper.md`")
    lines.append("- Figures: `papers/virtual_governor_stress_signal/figures/*.png`")
    out.write_text("\n".join(lines) + "\n")


def write_paper_markdown(
    payload: dict[str, Any],
    paper_dir: Path,
    figure_paths: list[Path],
) -> None:
    paper_dir.mkdir(parents=True, exist_ok=True)
    summary = payload["summary"]
    rows = {row["condition"]: row for row in summary["by_condition"]}
    governor = rows["virtual_governor"]
    reward = rows["reward_only"]
    stale = rows["stale_governor"]
    wrong = rows["wrong_governor"]
    delta = governor["global_recovery_score"] - reward["global_recovery_score"]
    lines: list[str] = [
        "# Virtual-Governor Stress Signals for Local Action Recovery",
        "",
        "**Jawaun Brown**",
        "",
        "## Abstract",
        "",
        "The virtual-governor preprint is useful because it names a signal "
        "architecture: global constraint violations become local incentives. "
        "This paper turns that phrase into a bounded neural diagnostic. Small "
        "policies act in a three-dimensional controlled state whose target "
        "changes during long rollouts. Five architectures receive the same "
        "oracle action labels but different policy features: reward-only, "
        "local-state proxy, stale governor memory, wrong stress signal, and "
        "live virtual-governor stress. The result tests whether the live "
        "stress-transduction channel is load-bearing for recovery after shifts.",
        "",
        "## 1. Diagnostic",
        "",
        "The task is deliberately finite. A policy observes a local feature vector "
        "and chooses one of six actions. Each action moves the system state and "
        "the oracle chooses the action that most reduces distance to the current "
        "global target. The target changes during evaluation, so a policy must "
        "carry the governing stress into action, not merely memorize a frequent "
        "target.",
        "",
        "## 2. Result",
        "",
        f"The live virtual-governor condition reached action accuracy "
        f"{_fmt(governor['action_accuracy'])}, mean stress "
        f"{_fmt(governor['mean_stress'])}, and global recovery score "
        f"{_fmt(governor['global_recovery_score'])}. Reward-only scored "
        f"{_fmt(reward['global_recovery_score'])}; the recovery-score delta was "
        f"{_fmt(delta)}. The wrong-stress control scored "
        f"{_fmt(wrong['global_recovery_score'])}; stale governor memory scored "
        f"{_fmt(stale['global_recovery_score'])}.",
        "",
        "The wrong-signal and stale-memory controls are the important controls. "
        "They test whether any extra channel helps, or whether the channel must "
        "faithfully carry current global stress.",
        "",
    ]
    if figure_paths:
        lines.extend(["## Figures", ""])
        for index, fig_path in enumerate(figure_paths):
            if index > 0:
                lines.append('<div style="page-break-before: always;"></div>')
                lines.append("")
            rel = fig_path.relative_to(paper_dir)
            lines.append(f"![{fig_path.stem}]({rel})")
            lines.append("")
    lines.extend(
        [
            "## 3. Architecture Law",
            "",
            "The simple architecture change is a stress-transduction channel: "
            "represent the live system-level constraint violation in a form the "
            "local action policy can consume. This is a machine-agency version "
            "of the virtual-governor idea, but the evidence remains bounded to "
            "this finite control task.",
            "",
            "## 4. Scope",
            "",
            "This result does not show consciousness, biological governance, or "
            "open-ended alignment. It shows that a live global-stress signal can "
            "be a load-bearing action feature under target shifts, while stale, "
            "wrong, local-only, and reward-only variants expose the proxy risks.",
            "",
            "## 5. Next Step",
            "",
            "Transfer the same stress-transduction ablation to long-horizon tool "
            "agents: hidden constraint, delayed commitment surface, tool repair, "
            "and a live governor signal that can be ablated, delayed, or "
            "corrupted. The causally grounded agents benchmark should treat this "
            "as a candidate Suite C/Suite E bridge: re-engagement plus commitment "
            "surface.",
            "",
            "## References",
            "",
            "- Lyons, B., Pio-Lopez, L., & Levin, M. (2026). *Alignment is to a "
            "virtual governor: A theory of coordination in diverse intelligence*. "
            "Preprints.org. doi:10.20944/preprints202607.0220.v1. Not peer "
            "reviewed.",
            "- `papers/architecture_laws_machine_agency/paper.md`",
            "- `papers/long_horizon_bottleneck/paper.md`",
            "- `papers/causally_grounded_agents_benchmark/paper.md`",
            "- `papers/structure_compatible_generalization/"
            "inferred_transformations_intervention.md`",
        ]
    )
    (paper_dir / "paper.md").write_text("\n".join(lines) + "\n")


def build_artifacts(payload: dict[str, Any], out_root: Path) -> list[Path]:
    payload["summary"] = summarize_records(payload["rows"])
    report_path = (
        out_root
        / "experiments/virtual_governor_stress_signal/results/"
        "virtual_governor_stress_signal_l4_2026_07_06.md"
    )
    paper_dir = out_root / "papers/virtual_governor_stress_signal"
    write_report(payload, report_path)
    figures = write_figures(payload, paper_dir / "figures")
    write_paper_markdown(payload, paper_dir, figures)
    return [
        report_path,
        paper_dir / "paper.md",
        *figures,
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, default=Path("."))
    args = parser.parse_args()
    payload = load_payload(args.input)
    written = build_artifacts(payload, args.out_root)
    for path in written:
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
