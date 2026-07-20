"""Regenerate the deterministic functional Harness Unlearning bundle."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from experiments.grounded_statecharts.harness_unlearning import (
    CommitmentOutcome,
    MemoryCommitHarness,
    MemoryLedger,
    MemoryStatus,
    evaluate_causal_use,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "results" / "harness_unlearning"
TARGET_MEMORY_ID = "mem-tool-v2"
PLACEBO_MEMORY_ID = "mem-color-placebo"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{json.dumps(row, sort_keys=True)}\n" for row in rows))


def phase_row(
    phase: str,
    ledger: MemoryLedger,
    outcome: CommitmentOutcome,
) -> dict[str, object]:
    return {
        "phase": phase,
        "target_status": ledger.item(TARGET_MEMORY_ID).status.value,
        "descendant_status": ledger.item("mem-tool-v2-summary").status.value,
        **outcome.to_dict(),
    }


def render_viewer(summary: dict[str, Any]) -> str:
    rows = []
    for phase in summary["phase_results"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(phase['phase'])}</td>"
            f"<td>{html.escape(phase['regime_id'])}</td>"
            f"<td>{html.escape(phase['target_status'])}</td>"
            f"<td>{html.escape(phase['action'])}</td>"
            f"<td>{'pass' if phase['joint_success'] else 'fail'}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Functional Harness Unlearning Replay</title>
<style>
:root {{ color-scheme: dark; font-family: ui-sans-serif, system-ui, sans-serif; }}
body {{ margin: 0; background: #111713; color: #f0fdf4; }}
main {{ max-width: 980px; margin: auto; padding: 44px 22px; }}
.eyebrow {{ color: #86efac; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
h1 {{ font-size: clamp(2rem, 6vw, 4.2rem); line-height: 1; margin: 12px 0 18px; }}
p {{ color: #d1d5db; max-width: 780px; line-height: 1.6; }}
.card {{ background: #17251c; border: 1px solid #3f6149; border-radius: 16px; padding: 20px; overflow: auto; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ border-bottom: 1px solid #3f6149; padding: 11px; text-align: left; }}
th {{ color: #bbf7d0; }} .claim {{ border-left: 3px solid #facc15; padding-left: 14px; margin-top: 24px; color: #fef08a; }}
</style></head><body><main>
<div class="eyebrow">Deterministic shift and recurrence fixture</div>
<h1>Stop stale use. Keep the receipt.</h1>
<p>Paired replay first proves that the v2 memory family controls the wrong v3 commitment. The ledger then quarantines, probes, retires, and restores the preserved memory when v2 recurs.</p>
<section class="card"><table><thead><tr><th>Phase</th><th>World</th><th>Memory state</th><th>Committed action</th><th>Outcome</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>
<div class="claim"><strong>Claim boundary:</strong> {html.escape(summary['allowed_claim'])}</div>
</main></body></html>
"""


def generate_results(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    ledger, regimes = MemoryLedger.load(
        PACKAGE_ROOT / "fixtures" / "harness_unlearning.json"
    )
    harness = MemoryCommitHarness()
    phases: list[dict[str, object]] = []

    acquisition = harness.commit(ledger, regimes["v2"])
    stable = harness.commit(ledger, regimes["v2"])
    phases.append(phase_row("acquisition", ledger, acquisition))
    phases.append(phase_row("stable_use", ledger, stable))

    nonshift_suppressed = harness.commit(
        ledger,
        regimes["v2"],
        suppressed_ids=ledger.family_ids(TARGET_MEMORY_ID),
    )
    matched_nonshift_kept = acquisition.joint_success and not nonshift_suppressed.joint_success

    append_only_shift = harness.commit(ledger, regimes["v3"])
    phases.append(phase_row("world_shift_append_only", ledger, append_only_shift))
    causal_use = evaluate_causal_use(
        ledger,
        regimes["v3"],
        target_memory_id=TARGET_MEMORY_ID,
        placebo_memory_id=PLACEBO_MEMORY_ID,
    )
    if not causal_use.passed:
        raise RuntimeError("causal-use prerequisite failed; refusing lifecycle execution")

    ledger = ledger.transition_family(
        TARGET_MEMORY_ID,
        MemoryStatus.QUARANTINED,
        reason="target-family suppression repaired shifted commitment",
        evidence_ref="causal-use://v3-target-vs-placebo",
    )
    quarantined_shift = harness.commit(ledger, regimes["v3"])
    phases.append(phase_row("quarantined_shift_recovery", ledger, quarantined_shift))

    ledger = ledger.transition_family(
        TARGET_MEMORY_ID,
        MemoryStatus.REVALIDATING,
        reason="bounded probe under current shifted regime",
        evidence_ref="probe://v3",
    )
    failed_v3_probe = harness.commit(ledger, regimes["v3"], probe=True)
    phases.append(phase_row("v3_revalidation_probe", ledger, failed_v3_probe))
    if failed_v3_probe.joint_success:
        raise RuntimeError("fixture v3 probe unexpectedly passed")
    ledger = ledger.transition_family(
        TARGET_MEMORY_ID,
        MemoryStatus.RETIRED,
        reason="controlled v3 probe confirmed stale causal effect",
        evidence_ref="probe://v3#failed",
    )
    retired_shift = harness.commit(ledger, regimes["v3"])
    phases.append(phase_row("retired_shift", ledger, retired_shift))

    full_reset_recurrence = harness.commit(ledger, regimes["v2"])
    phases.append(phase_row("v2_recurrence_full_reset", ledger, full_reset_recurrence))
    ledger = ledger.transition_family(
        TARGET_MEMORY_ID,
        MemoryStatus.REVALIDATING,
        reason="declared v2 recurrence opened bounded probe",
        evidence_ref="probe://v2",
    )
    recurrence_probe = harness.commit(ledger, regimes["v2"], probe=True)
    phases.append(phase_row("v2_recurrence_probe", ledger, recurrence_probe))
    if not recurrence_probe.joint_success:
        raise RuntimeError("fixture recurrence probe unexpectedly failed")
    ledger = ledger.transition_family(
        TARGET_MEMORY_ID,
        MemoryStatus.ACTIVE,
        reason="controlled v2 probe restored useful effect",
        evidence_ref="probe://v2#passed",
    )
    restored = harness.commit(ledger, regimes["v2"])
    phases.append(phase_row("v2_restored", ledger, restored))

    target_events = [
        event for event in ledger.events if event.memory_id == TARGET_MEMORY_ID
    ]
    observed_statuses = {MemoryStatus.ACTIVE.value}
    observed_statuses.update(event.status_after.value for event in target_events)
    audit_complete = all(event.reason and event.evidence_ref for event in ledger.events)
    gates = {
        "causal_use_prerequisite": causal_use.passed,
        "descendant_suppression_required": not causal_use.target_only_suppressed.joint_success
        and causal_use.target_family_suppressed.joint_success,
        "matched_nonshift_not_forgotten": matched_nonshift_kept,
        "all_memory_states_observed": observed_statuses
        == {status.value for status in MemoryStatus},
        "shift_recovery_after_quarantine": not append_only_shift.joint_success
        and quarantined_shift.joint_success
        and retired_shift.joint_success,
        "retired_memory_excluded_from_commitment": not full_reset_recurrence.joint_success
        and not full_reset_recurrence.retrieved_memory_ids,
        "recurrence_revalidation_restores_utility": recurrence_probe.joint_success
        and restored.joint_success,
        "descendant_transitions_match_parent": all(
            ledger.item(memory_id).status is MemoryStatus.ACTIVE
            for memory_id in ledger.family_ids(TARGET_MEMORY_ID)
        ),
        "audit_receipts_complete": audit_complete and len(ledger.events) == 10,
    }
    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": "harness_unlearning_fixture_2026_07_20",
        "shift": "tool regime v2 -> v3 -> v2 recurrence",
        "target_memory_id": TARGET_MEMORY_ID,
        "states": [status.value for status in MemoryStatus],
        "gates": gates,
        "metrics": {
            "time_to_stop_causal_use": 1,
            "post_shift_joint_success": int(quarantined_shift.joint_success),
            "append_only_post_shift_joint_success": int(append_only_shift.joint_success),
            "false_forgetting_rate": 0.0 if matched_nonshift_kept else 1.0,
            "recurrence_recovery": int(restored.joint_success),
            "full_reset_recurrence_success": int(full_reset_recurrence.joint_success),
            "ledger_events": len(ledger.events),
        },
        "causal_use": causal_use.to_dict(),
        "phase_results": phases,
        "regime_transition": {
            "old_regime": "retrieval status and task score without commitment influence proof",
            "new_artifacts": [
                "paired target-family/placebo suppression receipt",
                "scoped reversible memory-state ledger",
                "shift and recurrence commitment outcomes",
            ],
            "preserved_gates": [
                "exact deterministic replay",
                "single-component memory intervention",
                "separate task and critical-violation outcomes",
            ],
            "rejected_alternatives": [
                "lower retrieval as proof of unlearning",
                "deletion after one bad outcome",
                "permanent full reset without recurrence",
            ],
            "residual_finding": (
                "suppressing only the parent memory leaves a causally active derived summary, "
                "so lifecycle changes must cover declared descendants"
            ),
        },
        "allowed_claim": (
            "On one committed deterministic v2-to-v3-to-v2 fixture, paired replay "
            "showed that the stale memory family changed commitment; quarantine and "
            "retirement stopped that influence, and bounded recurrence revalidation "
            "restored the preserved memory and task success."
        ),
        "non_claims": [
            "This is functional harness memory control, not neural unlearning or legal erasure.",
            "One deterministic fixture does not estimate false-forgetting or recovery rates.",
            "No live model, stochastic replay, sealed shift, or OOD regime was evaluated.",
            "The result does not satisfy HU1-HU7.",
        ],
    }
    if not all(gates.values()):
        raise RuntimeError("Harness Unlearning exit gate failed; refusing publication")
    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "causal_use.json", causal_use.to_dict())
    write_json(output_dir / "ledger.json", ledger.to_dict())
    write_jsonl(output_dir / "events.jsonl", [event.to_dict() for event in ledger.events])
    write_jsonl(output_dir / "phases.jsonl", phases)
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
