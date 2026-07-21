"""Opt-in credentialed live smoke for Harness Unlearning memory sensitivity.

This is deliberately NOT a HU1-HU7 pilot. The deterministic multi-shift bank
in `unlearning_multishift.py` tests the memory ledger's own code path: a
Python object is suppressed and the harness recomputes deterministically.
This smoke instead asks a live model, in natural language, to choose a field
or action under a shifted regime with and without a textual memory reminder
present in the prompt. It checks only that the live-adapter mechanics work
end to end (prompt building, provider dispatch, response parsing, budget
accounting) for a memory-sensitivity probe shape. It is not a causal-use
test in the mechanistic sense `evaluate_causal_use` performs, is not
budget-matched against a baseline, and authorizes no HU1-HU7 claim.

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

    summary = {
        "adapter_id": "live",
        "provider_id": executor.provider_id,
        "model_id": executor.model_id,
        "case_count": len(SMOKE_CASE_IDS),
        "episode_count": len(SMOKE_CASE_IDS) * len(CONDITIONS),
        "publishable_rows": len(rows),
        "provider_failures": failures,
        "allowed_claim": (
            "Credentialed smoke validates live-adapter prompt/parse/budget "
            "mechanics for a memory-sensitivity probe shape only. It reports "
            "whether the model's stated action matched the shifted regime's "
            "required action under observed/target-suppressed/placebo- "
            "suppressed prompt conditions, but does not authorize any "
            "scientific or commercial claim."
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
        ],
        "gates": {
            "opt_in": True,
            "writes_to_artifacts_only": True,
            "all_episodes_parsed": len(rows) == len(SMOKE_CASE_IDS) * len(CONDITIONS),
            "budget_ok": all(bool(row["budget_ok"]) for row in rows) if rows else False,
            "provider_failures": len(failures),
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
                **{k: summary[k] for k in ("episode_count", "publishable_rows", "provider_id", "model_id", "gates")},
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
