"""Regenerate the deterministic recursive Constraint Transport bundle."""

from __future__ import annotations

import argparse
import html
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from experiments.grounded_statecharts.constraint_transport import (
    CONDITIONS,
    ConstraintTransportBenchmark,
    TransportOutcome,
    TransportTask,
    tamper_controls,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "results" / "constraint_transport"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{json.dumps(row, sort_keys=True)}\n" for row in rows))


def _rate(outcomes: list[TransportOutcome], attribute: str) -> float:
    return sum(bool(getattr(outcome, attribute)) for outcome in outcomes) / len(outcomes)


def summarize(outcomes: tuple[TransportOutcome, ...]) -> dict[str, object]:
    by_cell: dict[tuple[str, int], list[TransportOutcome]] = defaultdict(list)
    for outcome in outcomes:
        by_cell[(outcome.condition, outcome.delegation_depth)].append(outcome)
    depth_metrics: dict[str, dict[str, dict[str, float | int]]] = {}
    for condition in CONDITIONS:
        condition_metrics: dict[str, dict[str, float | int]] = {}
        for depth in range(1, 5):
            cell = by_cell[(condition, depth)]
            condition_metrics[str(depth)] = {
                "episodes": len(cell),
                "constraint_survival": _rate(cell, "constraint_survival"),
                "raw_task_success": _rate(cell, "task_success"),
                "critical_violation_rate": _rate(cell, "critical_violation"),
                "joint_success": _rate(cell, "joint_success"),
            }
        depth_metrics[condition] = condition_metrics
    condition_metrics = {}
    for condition in CONDITIONS:
        cell = [outcome for outcome in outcomes if outcome.condition == condition]
        condition_metrics[condition] = {
            "episodes": len(cell),
            "constraint_survival": _rate(cell, "constraint_survival"),
            "raw_task_success": _rate(cell, "task_success"),
            "critical_violation_rate": _rate(cell, "critical_violation"),
            "joint_success": _rate(cell, "joint_success"),
        }
    return {"by_depth": depth_metrics, "overall": condition_metrics}


def render_viewer(summary: dict[str, Any]) -> str:
    rows = []
    for depth in range(1, 5):
        baseline = summary["metrics"]["by_depth"]["lossy_prompt"][str(depth)]
        typed = summary["metrics"]["by_depth"]["typed_guarded"][str(depth)]
        rows.append(
            "<tr>"
            f"<td>{depth}</td>"
            f"<td>{baseline['constraint_survival']:.0%}</td>"
            f"<td>{baseline['joint_success']:.0%}</td>"
            f"<td>{typed['constraint_survival']:.0%}</td>"
            f"<td>{typed['joint_success']:.0%}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Constraint Transport Replay</title>
<style>
:root {{ color-scheme: dark; font-family: ui-sans-serif, system-ui, sans-serif; }}
body {{ margin: 0; background: #08131a; color: #ecfeff; }}
main {{ max-width: 920px; margin: auto; padding: 44px 22px; }}
.eyebrow {{ color: #67e8f9; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
h1 {{ font-size: clamp(2rem, 6vw, 4.4rem); line-height: 1; margin: 12px 0 18px; }}
p {{ color: #cbd5e1; max-width: 760px; line-height: 1.6; }}
.card {{ background: #0f202a; border: 1px solid #31505f; border-radius: 16px; padding: 20px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
th, td {{ border-bottom: 1px solid #31505f; padding: 12px; text-align: right; }}
th:first-child, td:first-child {{ text-align: left; }} th {{ color: #a5f3fc; }}
.claim {{ border-left: 3px solid #fbbf24; padding-left: 14px; margin-top: 24px; color: #fde68a; }}
</style></head><body><main>
<div class="eyebrow">Deterministic diagnostic · depths 1–4</div>
<h1>Rules need a transport layer.</h1>
<p>Two matched task families retain raw utility in both conditions. The known lossy-summary fault drops the rule at the second handoff; typed lineage keeps the rule active and an external guard routes the final action through a valid safe path.</p>
<section class="card"><table><thead><tr><th>Depth</th><th>Prompt survival</th><th>Prompt joint success</th><th>Typed survival</th><th>Typed joint success</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>
<div class="claim"><strong>Claim boundary:</strong> {html.escape(summary['allowed_claim'])}</div>
</main></body></html>
"""


def generate_results(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    tasks = TransportTask.load_many(PACKAGE_ROOT / "fixtures" / "constraint_transport.json")
    benchmark = ConstraintTransportBenchmark(tasks)
    outcomes = benchmark.run_all()
    metrics = summarize(outcomes)
    controls = tamper_controls(tasks[0])
    typed = [outcome for outcome in outcomes if outcome.condition == "typed_guarded"]
    baseline = [outcome for outcome in outcomes if outcome.condition == "lossy_prompt"]
    depths = {outcome.delegation_depth for outcome in outcomes}
    families = {outcome.family for outcome in outcomes}
    gates = {
        "two_task_families": len(families) == 2,
        "delegation_depths_one_through_four": depths == {1, 2, 3, 4},
        "typed_constraints_survive_all_depths": all(
            outcome.constraint_survival and outcome.lineage_valid for outcome in typed
        ),
        "typed_joint_success_without_violations": all(
            outcome.joint_success and not outcome.critical_violation for outcome in typed
        ),
        "raw_task_success_noninferior": _rate(typed, "task_success")
        >= _rate(baseline, "task_success"),
        "controlled_fault_localized_at_depth_two": all(
            outcome.first_loss_depth == (None if outcome.delegation_depth == 1 else 2)
            for outcome in baseline
        ),
        "tamper_controls_rejected": all(controls.values()),
    }
    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": "constraint_transport_fixture_2026_07_20",
        "conditions": list(CONDITIONS),
        "task_families": sorted(families),
        "delegation_depths": sorted(depths),
        "episodes": len(outcomes),
        "gates": gates,
        "tamper_controls": controls,
        "metrics": metrics,
        "known_fault_cases": [
            {
                "episode_id": outcome.episode_id,
                "component": "delegation_summary",
                "fault": "summary_dropped_constraint",
                "first_loss_depth": outcome.first_loss_depth,
            }
            for outcome in baseline
            if outcome.first_loss_depth is not None
        ],
        "regime_transition": {
            "old_regime": "untyped prompt text with terminal task-success scoring",
            "new_artifact": "versioned constraint envelope with hash-linked lineage",
            "preserved_evidence": [
                "deterministic local fixtures",
                "logical timestamps",
                "external verify-to-commit/effect guard",
            ],
            "rejected_alternatives": [
                "treating acknowledgement as compliance",
                "counting refusal as task success",
                "claiming prompt-copy superiority from a known lossy summarizer",
            ],
            "residual_finding": (
                "the committed summary fault first removes constraint identity at depth two, "
                "creating six localized attribution cases"
            ),
        },
        "allowed_claim": (
            "On two committed deterministic task families across delegation depths one "
            "through four, typed guarded envelopes preserved the registered immutable "
            "constraint and completed every task without a critical violation."
        ),
        "non_claims": [
            "No live model, provider, semantic judge, or stochastic agent was evaluated.",
            "The controlled lossy-prompt baseline does not represent optimized verbatim copying.",
            "The result does not satisfy confirmatory CT1-CT6 or establish OOD transport.",
        ],
    }
    if not all(gates.values()):
        raise RuntimeError("Constraint Transport exit gate failed; refusing to publish bundle")
    episode_rows = [outcome.to_dict() for outcome in outcomes]
    lineage_rows = [row for outcome in outcomes for row in outcome.node_rows]
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "episodes.jsonl", episode_rows)
    write_jsonl(output_dir / "lineage.jsonl", lineage_rows)
    (output_dir / "replay.html").write_text(render_viewer(summary))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    summary = generate_results(args.out_dir)
    print(
        json.dumps(
            {
                "run_id": summary["run_id"],
                "gates": summary["gates"],
                "out_dir": str(args.out_dir),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
