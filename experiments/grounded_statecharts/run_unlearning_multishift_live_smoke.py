"""Opt-in credentialed live smoke for Harness Unlearning memory sensitivity.

This is deliberately NOT a HU1-HU7 pilot. The deterministic multi-shift bank
in `unlearning_multishift.py` tests the memory ledger's own code path: a
Python object is suppressed and the harness recomputes deterministically.
This smoke instead asks a live model, in natural language, to choose a field
or action under a shifted regime with and without a textual memory reminder
present in the prompt (observed / target_suppressed / placebo_suppressed).
Prompts never name the condition, case id, or shift family; only the regime
id and the memory sentences vary, so the model cannot infer which arm it is
in from a label.

It checks that the live-adapter mechanics work end to end (prompt building,
provider dispatch, response parsing, budget accounting) for a
memory-sensitivity probe shape, AND it applies two explicit kill criteria to
a derived, prompt-level behavioral signal (`_live_quarantine_signal`) shaped
like `evaluate_causal_use` (target-specific effect, placebo unaffected):

1. Identical-semantics kill: a `model/version-identical-semantics` case
   (required action unchanged) must never show the quarantine-worthy
   pattern. If it does, this smoke records that as a false-forgetting risk
   signature rather than reinterpreting it as useful lifecycle behavior.
2. Specificity-before-quarantine kill: the signal is only ever raised when
   removing the target memory helps AND removing the unrelated placebo
   memory does not; a generic "less context helps" effect (placebo also
   helps) never counts as quarantine-worthy on its own.

This derived signal is still NOT the mechanistic `evaluate_causal_use`
intervention -- it is a natural-language behavioral probe, not a retrieval
suppression on an internal memory system, is not budget-matched against a
baseline, and authorizes no HU1-HU7 claim by itself.

Writes only under gitignored artifacts/. Smoke outcomes must not be reused as
evidence in a later pre-registered live Harness Unlearning pilot.

Example:

    GROUNDED_HARNESS_LIVE=1 \
    GROUNDED_HARNESS_PROVIDER=openai \
    GROUNDED_HARNESS_MODEL=gpt-4.1-mini \
    doppler run --config dev -- \
      python3 -m experiments.grounded_statecharts.run_unlearning_multishift_live_smoke
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from experiments.grounded_statecharts.adapters.live import (
    ACTION_SCHEMA,
    LIVE_OPT_IN_ENV,
    LiveExecutor,
)
from experiments.grounded_statecharts.budgets import BudgetSpec, BudgetUsage, settle_budget
from experiments.grounded_statecharts.runtime import canonical_json
from experiments.grounded_statecharts.unlearning_multishift import (
    ShiftCase,
    draft_shift_cases,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "grounded_statecharts" / "unlearning_multishift_live_smoke"

# Deliberately tiny: one changed-semantics case from each of the two shift
# families plus the identical-semantics negative control. This is a smoke of
# adapter mechanics, not a powered pilot.
SMOKE_CASE_IDS = (
    "tool_schema_v2_to_v3",
    "environment_policy_network_v1_to_v2",
    "model_version_identical_model_alias",
)
CONDITIONS = ("observed", "target_suppressed", "placebo_suppressed")
SMOKE_BUDGET_USD_PER_CALL = 0.02
SMOKE_MAX_OUTPUT_TOKENS = 200


def _selected_cases() -> tuple[ShiftCase, ...]:
    by_id = {case.case_id: case for case in draft_shift_cases()}
    return tuple(by_id[case_id] for case_id in SMOKE_CASE_IDS)


def _memory_sentence(case: ShiftCase, *, suppress_target: bool, suppress_placebo: bool) -> str:
    sentences = []
    if not suppress_target:
        sentences.append(
            f"Session memory records that under regime {case.prior_regime.regime_id}, "
            f"this call used the value `{case.fixture.target_action}`, and a derived "
            "summary of that session repeats the same value."
        )
    else:
        sentences.append("No prior tool-usage memory is available for this call.")
    if not suppress_placebo:
        sentences.append(
            "A separate, unrelated preference note (unrelated to this decision) is "
            "also present in memory."
        )
    return " ".join(sentences)


def build_memory_probe_messages(
    case: ShiftCase, *, condition: str
) -> list[dict[str, str]]:
    """Build a single-turn memory-sensitivity probe for one shift case."""

    if condition not in CONDITIONS:
        raise ValueError(f"unsupported condition: {condition}")
    memory_sentence = _memory_sentence(
        case,
        suppress_target=condition == "target_suppressed",
        suppress_placebo=condition == "placebo_suppressed",
    )
    system = (
        "You are an agent step deciding which value to use for one call. "
        "Return ONLY one JSON object matching this schema: "
        f"{ACTION_SCHEMA}. Put the exact value you will use in `action`. "
        "Do not wrap the JSON in markdown."
    )
    user = (
        f"Current regime: {case.shifted_regime.regime_id}. "
        f"Under this regime, the correct value for this call is "
        f"`{case.shifted_regime.required_action}`. {memory_sentence} "
        "Decide which single value you will use for this call and put it "
        "verbatim in the `action` field."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _matched_by_condition(
    rows: list[dict[str, Any]], case_id: str
) -> dict[str, bool] | None:
    """Return per-condition `matched_expected` for one case, or None if
    any of the three conditions is missing a publishable row (e.g. a
    provider failure)."""

    by_condition = {
        row["condition"]: bool(row["matched_expected"])
        for row in rows
        if row["case_id"] == case_id
    }
    if set(by_condition) != set(CONDITIONS):
        return None
    return by_condition


def _live_quarantine_signal(matched: dict[str, bool]) -> dict[str, Any]:
    """Derive a prompt-level, causal-use-shaped signal from one case's three
    conditions. This is NOT `evaluate_causal_use`: it never suppresses a
    memory retrieval mechanism, it only edits the prompt text handed to a
    live model. `target_effect` and `placebo_effect` are the change in
    matched-expected accuracy when the target or placebo memory sentence is
    removed from the prompt, relative to the observed (both-present)
    condition.
    """

    observed = int(matched["observed"])
    target_effect = int(matched["target_suppressed"]) - observed
    placebo_effect = int(matched["placebo_suppressed"]) - observed
    quarantine_signal = target_effect > 0 and placebo_effect <= 0
    return {
        "target_effect": target_effect,
        "placebo_effect": placebo_effect,
        "quarantine_signal": quarantine_signal,
    }


def evaluate_kill_criteria(
    rows: list[dict[str, Any]], cases: tuple[ShiftCase, ...]
) -> dict[str, Any]:
    """Apply the two live-smoke kill criteria to the derived quarantine signal.

    Kill criterion 1 (identical-semantics must not quarantine): an
    identical-semantics case must never show `quarantine_signal=True`.
    Kill criterion 2 (semantic shifts require the causal-use-shaped pattern
    before quarantine): `quarantine_signal` is only ever True when the
    placebo suppression did not also help (`placebo_effect <= 0`); this is
    enforced structurally by `_live_quarantine_signal` and re-checked here
    as a regression guard, not re-derived independently.
    """

    per_case: dict[str, Any] = {}
    insufficient_data_cases: list[str] = []
    for case in cases:
        matched = _matched_by_condition(rows, case.case_id)
        if matched is None:
            insufficient_data_cases.append(case.case_id)
            continue
        per_case[case.case_id] = {
            "semantics_changed": case.semantics_changed,
            **_live_quarantine_signal(matched),
        }

    identical_semantics_violations = [
        case_id
        for case_id, pattern in per_case.items()
        if not pattern["semantics_changed"] and pattern["quarantine_signal"]
    ]
    target_specificity_violations = [
        case_id
        for case_id, pattern in per_case.items()
        if pattern["quarantine_signal"] and pattern["placebo_effect"] > 0
    ]
    kill_triggered = bool(identical_semantics_violations) or bool(
        target_specificity_violations
    )
    return {
        "per_case": per_case,
        "insufficient_data_cases": insufficient_data_cases,
        "identical_semantics_violations": identical_semantics_violations,
        "target_specificity_violations": target_specificity_violations,
        "kill_triggered": kill_triggered,
        "description": (
            "Kill criterion 1: an identical-semantics case (required action "
            "unchanged under the shift) must never show a target-specific "
            "quarantine-worthy pattern; if one does, it is recorded here as "
            "a false-forgetting risk signature, not reinterpreted as useful "
            "lifecycle behavior. Kill criterion 2: a quarantine-worthy "
            "pattern must never be raised from a generic 'any suppression "
            "helps' effect (placebo_effect > 0); it requires the "
            "causal-use-shaped pattern (target-specific recovery, placebo "
            "unaffected) before it is raised at all. Both criteria evaluate "
            "a prompt-level behavioral signal, not the mechanistic "
            "`evaluate_causal_use` intervention."
        ),
    }


def generate_results(
    output_dir: Path, *, executor: LiveExecutor | None = None
) -> dict[str, Any]:
    if os.environ.get(LIVE_OPT_IN_ENV, "").strip() != "1":
        raise RuntimeError(f"set {LIVE_OPT_IN_ENV}=1 for credentialed smoke")
    if "results" in output_dir.parts:
        raise RuntimeError("refusing to write live smoke under results/")

    executor = executor or LiveExecutor.from_env()
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for case in _selected_cases():
        for condition in CONDITIONS:
            episode_id = f"hu-live-smoke:{case.case_id}:{condition}"
            messages = build_memory_probe_messages(case, condition=condition)
            try:
                response = executor.complete_messages(messages)
            except Exception as exc:  # noqa: BLE001 - smoke must finish the matrix
                failures.append(
                    {
                        "episode_id": episode_id,
                        "error_type": type(exc).__name__,
                        "error": str(exc)[:500],
                    }
                )
                continue
            usage = BudgetUsage().add(
                calls=response.usage.call_count,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                latency_ms=response.usage.latency_ms,
                estimated_cost_usd=response.usage.estimated_cost_usd,
            )
            budget_receipt = settle_budget(
                spec=_smoke_budget_spec(), usage=usage, planned_calls=1
            )
            matched_expected = response.action.strip() == case.shifted_regime.required_action
            rows.append(
                {
                    "episode_id": episode_id,
                    "run_id": "unlearning-multishift-live-smoke",
                    "case_id": case.case_id,
                    "shift_family": case.shift_family,
                    "semantics_changed": case.semantics_changed,
                    "condition": condition,
                    "expected_action": case.shifted_regime.required_action,
                    "observed_action": response.action.strip(),
                    "matched_expected": matched_expected,
                    "model_id": executor.model_id,
                    "provider_id": executor.provider_id,
                    "call_count": usage.call_count,
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "latency_ms": usage.latency_ms,
                    "estimated_cost_usd": usage.estimated_cost_usd,
                    "budget_ok": budget_receipt.ok,
                }
            )
    rows = sorted(rows, key=lambda row: canonical_json(row))
    kill_criteria = evaluate_kill_criteria(rows, _selected_cases())
    kill_triggered = kill_criteria["kill_triggered"]

    summary = {
        "adapter_id": "live",
        "provider_id": executor.provider_id,
        "model_id": executor.model_id,
        "case_count": len(SMOKE_CASE_IDS),
        "episode_count": len(SMOKE_CASE_IDS) * len(CONDITIONS),
        "publishable_rows": len(rows),
        "provider_failures": failures,
        "kill_criteria": kill_criteria,
        "allowed_claim": (
            (
                "Credentialed smoke validates live-adapter prompt/parse/budget "
                "mechanics for a memory-sensitivity probe shape. It reports "
                "whether the model's stated action matched the shifted regime's "
                "required action under observed/target-suppressed/placebo- "
                "suppressed prompt conditions, and neither live-smoke kill "
                "criterion fired: no identical-semantics case showed a "
                "target-specific quarantine-worthy pattern, and no "
                "quarantine-worthy pattern was raised without the "
                "causal-use-shaped placebo contrast. This does not authorize "
                "any scientific or commercial claim."
            )
            if not kill_triggered
            else (
                "KILL: at least one live-smoke kill criterion fired -- either "
                "an identical-semantics case showed a target-specific "
                "quarantine-worthy pattern (false-forgetting risk signature) "
                "or a quarantine-worthy pattern was raised without the "
                "required placebo contrast. This is recorded as evidence "
                "against this probe shape being ready to inform quarantine "
                "decisions for this model/run, not reinterpreted as a pass. "
                "See kill_criteria for the violating case ids."
            )
        ),
        "non_claims": [
            "Not a HU1-HU7 result.",
            "Not commitment-level causal use in the `evaluate_causal_use` "
            "sense; suppression here is a prompt edit, not an intervention "
            "on a retrieval mechanism.",
            "Not budget-matched against a no-memory or full-reset baseline.",
            "Not powered: 3 cases x 3 conditions x 1 repeat.",
            "Raw provider transcripts remain outside public results/ and "
            "outside this artifacts/ bundle's rows.",
            "A clean kill_criteria pass on 3 cases x 1 repeat does not "
            "authorize promoting this probe shape into a pre-registered "
            "pilot; it only means the mechanics and the derived signal did "
            "not misfire on this run.",
        ],
        "gates": {
            "opt_in": True,
            "writes_to_artifacts_only": True,
            "all_episodes_parsed": len(rows) == len(SMOKE_CASE_IDS) * len(CONDITIONS),
            "budget_ok": all(bool(row["budget_ok"]) for row in rows) if rows else False,
            "provider_failures": len(failures),
            "kill_triggered": kill_triggered,
        },
        "next_live_gate": (
            "Before any HU1-HU7 claim: pre-register a matched live pilot "
            "over the full 9-case bank with a no-memory and full-reset "
            "baseline, budget-matched calls, task-clustered bootstrap CIs, "
            "and frozen false-forgetting/recovery thresholds, following the "
            "shared evaluation standard in "
            "docs/harness_research/harness_unlearning.md."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    (output_dir / "rows.jsonl").write_text(
        "\n".join(canonical_json(row) for row in rows) + ("\n" if rows else "")
    )
    return summary


def _smoke_budget_spec() -> BudgetSpec:
    return BudgetSpec(
        max_calls=1,
        max_input_tokens=2_000,
        max_output_tokens=SMOKE_MAX_OUTPUT_TOKENS,
        max_tool_calls=0,
        max_latency_ms=60_000,
        max_cost_usd=SMOKE_BUDGET_USD_PER_CALL,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if "results" in args.output_dir.parts:
        raise SystemExit("refusing to write live smoke under results/")
    summary = generate_results(args.output_dir)
    print(
        json.dumps(
            {
                "output_dir": str(args.output_dir),
                **{
                    k: summary[k]
                    for k in (
                        "episode_count",
                        "publishable_rows",
                        "provider_id",
                        "model_id",
                        "gates",
                        "kill_criteria",
                    )
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
