"""Regenerate the deterministic Counterfactual Harness Search pilot bundle."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from experiments.grounded_statecharts.counterfactual_search import (
    COMPONENTS,
    CounterfactualHarnessPilot,
    DeterministicHarnessEvaluator,
    FaultCase,
    HarnessConfig,
    SearchResult,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "results" / "counterfactual_search"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{json.dumps(row, sort_keys=True)}\n" for row in rows))


def _rate(results: tuple[SearchResult, ...], attribute: str) -> float:
    return sum(bool(getattr(result, attribute)) for result in results) / len(results)


def render_viewer(summary: dict[str, Any]) -> str:
    rows = []
    for case in summary["case_results"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(case['responsible_component'])}</td>"
            f"<td>{html.escape(case['trace_suspect'])}</td>"
            f"<td>{html.escape(case['recovered_component'])}</td>"
            f"<td>{'yes' if case['counterfactual_repair_success'] else 'no'}</td>"
            f"<td>{'yes' if case['trace_repair_success'] else 'no'}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Counterfactual Harness Search Pilot</title>
<style>
:root {{ color-scheme: dark; font-family: ui-sans-serif, system-ui, sans-serif; }}
body {{ margin: 0; background: #11101b; color: #f5f3ff; }}
main {{ max-width: 980px; margin: auto; padding: 44px 22px; }}
.eyebrow {{ color: #c4b5fd; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
h1 {{ font-size: clamp(2rem, 6vw, 4.2rem); line-height: 1; margin: 12px 0 18px; }}
p {{ color: #d6d3d1; max-width: 780px; line-height: 1.6; }}
.card {{ background: #1c1830; border: 1px solid #4c3f74; border-radius: 16px; padding: 20px; overflow: auto; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ border-bottom: 1px solid #4c3f74; padding: 11px; text-align: left; }}
th {{ color: #ddd6fe; }} .claim {{ border-left: 3px solid #fb7185; padding-left: 14px; margin-top: 24px; color: #fecdd3; }}
</style></head><body><main>
<div class="eyebrow">Synthetic-identifiable pilot · equal budget 7</div>
<h1>Intervene before assigning blame.</h1>
<p>Each row starts from one faulted harness surface. Six isolated repairs and one placebo are compared against six passive no-op replays plus one trace-selected repair.</p>
<section class="card"><table><thead><tr><th>Injected surface</th><th>Trace suspect</th><th>Recovered</th><th>Counterfactual repair</th><th>Trace repair</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>
<div class="claim"><strong>Claim boundary:</strong> {html.escape(summary['allowed_claim'])}</div>
</main></body></html>
"""


def generate_results(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    cases = FaultCase.load_many(PACKAGE_ROOT / "fixtures" / "counterfactual_faults.json")
    transport_summary = json.loads(
        (PACKAGE_ROOT / "results" / "constraint_transport" / "summary.json").read_text()
    )
    transport_sources = {
        item["episode_id"] for item in transport_summary["known_fault_cases"]
    }
    evaluator = DeterministicHarnessEvaluator()
    clean_reference_passes = all(
        evaluator.evaluate(case, HarnessConfig.clean()).joint_success for case in cases
    )
    faulted_reference_fails = all(
        not evaluator.evaluate(case, HarnessConfig.faulted(case)).joint_success
        for case in cases
    )
    results = CounterfactualHarnessPilot(evaluator).run_all(cases)
    context_case = next(case for case in cases if case.responsible_component == "context")
    context_source_reused = context_case.source_episode_id in transport_sources
    counterfactual_rate = _rate(results, "counterfactual_repair_success")
    trace_rate = _rate(results, "trace_repair_success")
    gates = {
        "six_surface_fault_coverage": {
            case.responsible_component for case in cases
        }
        == set(COMPONENTS),
        "clean_pass_faulted_fail": clean_reference_passes and faulted_reference_fails,
        "noop_replay_identity": all(result.noop_identity for result in results),
        "exact_top1_attribution": all(result.attribution_correct for result in results),
        "responsible_repairs_restore_joint_success": counterfactual_rate == 1.0,
        "placebo_false_credit_zero": not any(result.placebo_credit for result in results),
        "equal_evaluation_budget": all(result.evaluation_budget == 7 for result in results),
        "counterfactual_repairs_beat_trace_diagnosis": counterfactual_rate > trace_rate,
        "constraint_transport_fault_reused": context_source_reused,
    }
    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": "counterfactual_harness_pilot_2026_07_20",
        "tier": "synthetic-identifiable",
        "fault_surfaces": list(COMPONENTS),
        "cases": len(cases),
        "evaluation_budget_per_case": {
            "counterfactual_search": 7,
            "trace_diagnosis": 7,
        },
        "gates": gates,
        "metrics": {
            "counterfactual_top1_attribution": _rate(results, "attribution_correct"),
            "counterfactual_repair_success": counterfactual_rate,
            "trace_diagnosis_top1_attribution": sum(
                result.trace_suspect == result.responsible_component for result in results
            )
            / len(results),
            "trace_diagnosis_repair_success": trace_rate,
            "placebo_false_credit_rate": _rate(results, "placebo_credit"),
            "unidentified_rate": sum(
                result.recovered_component is None for result in results
            )
            / len(results),
        },
        "case_results": [
            {
                "fault_id": result.fault_id,
                "responsible_component": result.responsible_component,
                "trace_suspect": result.trace_suspect,
                "recovered_component": result.recovered_component,
                "attribution_correct": result.attribution_correct,
                "counterfactual_repair_success": result.counterfactual_repair_success,
                "trace_repair_success": result.trace_repair_success,
            }
            for result in results
        ],
        "regime_transition": {
            "old_regime": "passive deterministic traces plus a heuristic suspect",
            "new_operation": "paired single-component repair and matched-placebo replay",
            "preserved_gates": [
                "exact no-op replay",
                "separate task and violation outcomes",
                "registered Constraint Transport fault source",
            ],
            "rejected_alternatives": [
                "natural-language diagnosis as causal proof",
                "bundled multi-component repairs",
                "credit without a matched placebo",
            ],
            "residual_finding": (
                "isolated replay distinguishes the injected surface from a plausible "
                "non-causal trace suspect on every committed fixture"
            ),
        },
        "allowed_claim": (
            "On six committed deterministic single-fault fixtures, isolated component "
            "replay recovered every injected harness surface and selected six valid "
            "repairs versus zero for the narrow trace diagnosis baseline at equal budget."
        ),
        "non_claims": [
            "Fault labels are committed, not sealed from the repository author.",
            "The trace baseline is deterministic and is not a strong learned diagnostic model.",
            "No live model, stochastic replay, interaction fault, OOD case, or confidence interval was evaluated.",
            "The result does not satisfy CHS1-CHS6.",
        ],
    }
    if not all(gates.values()):
        raise RuntimeError("Counterfactual Harness Search gate failed; refusing publication")
    case_rows = [result.to_dict() for result in results]
    intervention_rows = [
        {
            "fault_id": result.fault_id,
            "responsible_component": result.responsible_component,
            **intervention.to_dict(),
        }
        for result in results
        for intervention in result.interventions
    ]
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "cases.jsonl", case_rows)
    write_jsonl(output_dir / "interventions.jsonl", intervention_rows)
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
