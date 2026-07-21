"""Draft multi-shift extension of the deterministic Harness Unlearning fixture.

Each shift instance below is an independently authored memory ledger and
regime pair: distinct memory ids, content actions, provenance tags, and
regime identifiers. Nothing here is the single `fixtures/harness_unlearning.json`
ledger replayed under a relabeled case id. Three shift families each carry
three independent variants, so the bank has nine non-duplicate instances
instead of one instance replayed three times.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from experiments.grounded_statecharts.harness_unlearning import (
    MemoryCommitHarness,
    MemoryItem,
    MemoryLedger,
    MemoryStatus,
    Regime,
    evaluate_causal_use,
)

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "results" / "unlearning_multishift"

VARIANTS_PER_FAMILY = 3


@dataclass(frozen=True)
class ShiftFixture:
    """An independently authored memory-ledger/regime pair for one shift instance.

    Every field below is chosen per instance (memory ids, content actions,
    provenance tags, and regime ids), so two instances never share a ledger
    even when they belong to the same shift family.
    """

    target_memory_id: str
    target_kind: str
    target_action: str
    descendant_memory_id: str
    placebo_memory_id: str
    prior_regime_id: str
    prior_default_action: str
    prior_required_action: str
    shifted_regime_id: str
    shifted_default_action: str
    shifted_required_action: str
    provenance_tag: str

    def __post_init__(self) -> None:
        ids = (
            self.target_memory_id,
            self.descendant_memory_id,
            self.placebo_memory_id,
        )
        if len(set(ids)) != len(ids):
            raise ValueError("shift fixture memory ids must be pairwise distinct")
        if self.prior_regime_id == self.shifted_regime_id:
            raise ValueError("shift fixture must declare two distinct regime ids")

    def build_ledger(self) -> MemoryLedger:
        target = MemoryItem(
            memory_id=self.target_memory_id,
            kind=self.target_kind,
            content_action=self.target_action,
            provenance=(
                f"run-{self.provenance_tag}-acquisition",
                f"intervention-{self.provenance_tag}",
            ),
            valid_regimes=(self.prior_regime_id,),
            descendant_ids=(self.descendant_memory_id,),
        )
        descendant = MemoryItem(
            memory_id=self.descendant_memory_id,
            kind=f"derived_{self.target_kind}",
            content_action=self.target_action,
            provenance=(self.target_memory_id,),
            valid_regimes=(self.prior_regime_id,),
            descendant_ids=(),
        )
        placebo = MemoryItem(
            memory_id=self.placebo_memory_id,
            kind="preference",
            content_action=None,
            provenance=(f"run-{self.provenance_tag}-unrelated",),
            valid_regimes=(self.prior_regime_id, self.shifted_regime_id),
            descendant_ids=(),
        )
        return MemoryLedger((target, descendant, placebo))

    def build_regimes(self) -> tuple[Regime, Regime]:
        prior = Regime(
            self.prior_regime_id, self.prior_default_action, self.prior_required_action
        )
        shifted = Regime(
            self.shifted_regime_id,
            self.shifted_default_action,
            self.shifted_required_action,
        )
        return prior, shifted


@dataclass(frozen=True)
class ShiftCase:
    """A named semantic-shift instance, deliberately not a live-model condition."""

    case_id: str
    shift_family: str
    fixture: ShiftFixture
    semantics_changed: bool
    mechanism: str

    def __post_init__(self) -> None:
        if not self.case_id or not self.shift_family or not self.mechanism:
            raise ValueError("shift case labels must be non-empty")
        prior, shifted = self.fixture.build_regimes()
        observed_change = prior.required_action != shifted.required_action
        if observed_change != self.semantics_changed:
            raise ValueError("semantics_changed must match the required-action shift")

    @property
    def prior_regime(self) -> Regime:
        return self.fixture.build_regimes()[0]

    @property
    def shifted_regime(self) -> Regime:
        return self.fixture.build_regimes()[1]

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "shift_family": self.shift_family,
            "prior_regime": self.prior_regime.regime_id,
            "shifted_regime": self.shifted_regime.regime_id,
            "target_memory_id": self.fixture.target_memory_id,
            "semantics_changed": self.semantics_changed,
            "mechanism": self.mechanism,
        }


def _tool_schema_fixtures() -> tuple[ShiftFixture, ...]:
    return (
        ShiftFixture(
            target_memory_id="mem-tool-v2",
            target_kind="tool_pattern",
            target_action="legacy_name",
            descendant_memory_id="mem-tool-v2-summary",
            placebo_memory_id="mem-color-placebo",
            prior_regime_id="v2",
            prior_default_action="current_name",
            prior_required_action="legacy_name",
            shifted_regime_id="v3",
            shifted_default_action="current_name",
            shifted_required_action="current_name",
            provenance_tag="toolschema-toolname",
        ),
        ShiftFixture(
            target_memory_id="mem-auth-header-v1",
            target_kind="tool_pattern",
            target_action="use_basic_auth",
            descendant_memory_id="mem-auth-header-v1-note",
            placebo_memory_id="mem-timezone-placebo",
            prior_regime_id="authpolicy-v1",
            prior_default_action="use_bearer_auth",
            prior_required_action="use_basic_auth",
            shifted_regime_id="authpolicy-v2",
            shifted_default_action="use_bearer_auth",
            shifted_required_action="use_bearer_auth",
            provenance_tag="toolschema-authheader",
        ),
        ShiftFixture(
            target_memory_id="mem-date-format-v1",
            target_kind="tool_pattern",
            target_action="format_mmddyyyy",
            descendant_memory_id="mem-date-format-v1-cache",
            placebo_memory_id="mem-font-placebo",
            prior_regime_id="datefmt-v1",
            prior_default_action="format_iso8601",
            prior_required_action="format_mmddyyyy",
            shifted_regime_id="datefmt-v2",
            shifted_default_action="format_iso8601",
            shifted_required_action="format_iso8601",
            provenance_tag="toolschema-dateformat",
        ),
    )


def _environment_policy_fixtures() -> tuple[ShiftFixture, ...]:
    return (
        ShiftFixture(
            target_memory_id="mem-egress-allowlist-v1",
            target_kind="environment_policy",
            target_action="allow_direct_egress",
            descendant_memory_id="mem-egress-allowlist-v1-cache",
            placebo_memory_id="mem-locale-placebo",
            prior_regime_id="netpolicy-v1",
            prior_default_action="route_via_proxy",
            prior_required_action="allow_direct_egress",
            shifted_regime_id="netpolicy-v2",
            shifted_default_action="route_via_proxy",
            shifted_required_action="route_via_proxy",
            provenance_tag="envpolicy-network",
        ),
        ShiftFixture(
            target_memory_id="mem-residency-us-v1",
            target_kind="environment_policy",
            target_action="store_us_only",
            descendant_memory_id="mem-residency-us-v1-note",
            placebo_memory_id="mem-theme-placebo",
            prior_regime_id="residency-v1",
            prior_default_action="store_eu_only",
            prior_required_action="store_us_only",
            shifted_regime_id="residency-v2",
            shifted_default_action="store_eu_only",
            shifted_required_action="store_eu_only",
            provenance_tag="envpolicy-residency",
        ),
        ShiftFixture(
            target_memory_id="mem-cred-rotation-30d",
            target_kind="environment_policy",
            target_action="rotate_every_30_days",
            descendant_memory_id="mem-cred-rotation-30d-cache",
            placebo_memory_id="mem-avatar-placebo",
            prior_regime_id="credpolicy-v1",
            prior_default_action="rotate_every_7_days",
            prior_required_action="rotate_every_30_days",
            shifted_regime_id="credpolicy-v2",
            shifted_default_action="rotate_every_7_days",
            shifted_required_action="rotate_every_7_days",
            provenance_tag="envpolicy-credrotation",
        ),
    )


def _model_version_identical_fixtures() -> tuple[ShiftFixture, ...]:
    return (
        ShiftFixture(
            target_memory_id="mem-model-alias-gpt",
            target_kind="model_reference",
            target_action="use_alias_gpt_x",
            descendant_memory_id="mem-model-alias-gpt-cache",
            placebo_memory_id="mem-wallpaper-placebo",
            prior_regime_id="modelid-preview",
            prior_default_action="use_alias_gpt_y",
            prior_required_action="use_alias_gpt_x",
            shifted_regime_id="modelid-ga",
            shifted_default_action="use_alias_gpt_y",
            shifted_required_action="use_alias_gpt_x",
            provenance_tag="modelversion-alias",
        ),
        ShiftFixture(
            target_memory_id="mem-embed-dim-1536",
            target_kind="model_reference",
            target_action="use_1536_dim",
            descendant_memory_id="mem-embed-dim-1536-cache",
            placebo_memory_id="mem-keyboard-placebo",
            prior_regime_id="embed-v1-fp32",
            prior_default_action="use_768_dim",
            prior_required_action="use_1536_dim",
            shifted_regime_id="embed-v1-fp16",
            shifted_default_action="use_768_dim",
            shifted_required_action="use_1536_dim",
            provenance_tag="modelversion-embeddim",
        ),
        ShiftFixture(
            target_memory_id="mem-endpoint-alias",
            target_kind="model_reference",
            target_action="use_regional_endpoint",
            descendant_memory_id="mem-endpoint-alias-cache",
            placebo_memory_id="mem-icon-placebo",
            prior_regime_id="endpoint-blue",
            prior_default_action="use_global_endpoint",
            prior_required_action="use_regional_endpoint",
            shifted_regime_id="endpoint-green",
            shifted_default_action="use_global_endpoint",
            shifted_required_action="use_regional_endpoint",
            provenance_tag="modelversion-endpointalias",
        ),
    )


_CASE_SPECS: tuple[tuple[str, str, bool, ShiftFixture, str], ...] = (
    (
        "tool_schema_v2_to_v3",
        "tool-schema",
        True,
        _tool_schema_fixtures()[0],
        "The accepted tool field changes from legacy_name to current_name.",
    ),
    (
        "tool_schema_auth_v1_to_v2",
        "tool-schema",
        True,
        _tool_schema_fixtures()[1],
        "The accepted authorization header convention changes from "
        "use_basic_auth to use_bearer_auth.",
    ),
    (
        "tool_schema_datefmt_v1_to_v2",
        "tool-schema",
        True,
        _tool_schema_fixtures()[2],
        "The accepted date-serialization format changes from format_mmddyyyy "
        "to format_iso8601.",
    ),
    (
        "environment_policy_network_v1_to_v2",
        "environment-policy",
        True,
        _environment_policy_fixtures()[0],
        "A policy-enforced environment now rejects direct egress and "
        "requires routing via proxy.",
    ),
    (
        "environment_policy_residency_v1_to_v2",
        "environment-policy",
        True,
        _environment_policy_fixtures()[1],
        "A policy-enforced environment now requires EU-only storage instead "
        "of US-only storage.",
    ),
    (
        "environment_policy_credential_rotation_v1_to_v2",
        "environment-policy",
        True,
        _environment_policy_fixtures()[2],
        "A policy-enforced environment now requires 7-day credential "
        "rotation instead of 30-day rotation.",
    ),
    (
        "model_version_identical_model_alias",
        "model/version-identical-semantics",
        False,
        _model_version_identical_fixtures()[0],
        "The model identifier changes from preview to GA labeling while the "
        "required alias commitment remains identical.",
    ),
    (
        "model_version_identical_embedding_dim",
        "model/version-identical-semantics",
        False,
        _model_version_identical_fixtures()[1],
        "The embedding backend precision label changes from fp32 to fp16 "
        "while the required dimensionality commitment remains identical.",
    ),
    (
        "model_version_identical_endpoint_alias",
        "model/version-identical-semantics",
        False,
        _model_version_identical_fixtures()[2],
        "The deployment slot alias changes from blue to green while the "
        "required regional-endpoint commitment remains identical.",
    ),
)


def draft_shift_cases() -> tuple[ShiftCase, ...]:
    """Return nine independently authored shift instances across three families.

    Each instance owns its own memory ids, content actions, and regime ids
    (see `ShiftFixture`), so the bank is not one ledger replayed under
    relabeled case ids. Regimes are still deterministic, hand-authored
    fixtures; this is not a live or neural-unlearning claim.
    """

    return tuple(
        ShiftCase(case_id, family, fixture, changed, mechanism)
        for case_id, family, changed, fixture, mechanism in _CASE_SPECS
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def _row(
    case: ShiftCase,
    phase: str,
    ledger: MemoryLedger,
    *,
    task_success: bool,
    retrieved_memory_ids: tuple[str, ...],
) -> dict[str, object]:
    return {
        **case.to_dict(),
        "phase": phase,
        "target_status": ledger.item(case.fixture.target_memory_id).status.value,
        "task_success": task_success,
        "joint_success": task_success,
        "retrieved_memory_ids": list(retrieved_memory_ids),
    }


def _run_case(case: ShiftCase) -> tuple[list[dict[str, object]], dict[str, object]]:
    ledger = case.fixture.build_ledger()
    harness = MemoryCommitHarness()
    rows: list[dict[str, object]] = []

    prior = harness.commit(ledger, case.prior_regime)
    shifted = harness.commit(ledger, case.shifted_regime)
    rows.extend(
        (
            _row(
                case,
                "prior_regime",
                ledger,
                task_success=prior.joint_success,
                retrieved_memory_ids=prior.retrieved_memory_ids,
            ),
            _row(
                case,
                "append_only_shift",
                ledger,
                task_success=shifted.joint_success,
                retrieved_memory_ids=shifted.retrieved_memory_ids,
            ),
        )
    )

    causal_use_passed = False
    lifecycle_applied = False
    if case.semantics_changed:
        causal_use = evaluate_causal_use(
            ledger,
            case.shifted_regime,
            target_memory_id=case.fixture.target_memory_id,
            placebo_memory_id=case.fixture.placebo_memory_id,
        )
        causal_use_passed = causal_use.passed
        if not causal_use_passed:
            raise RuntimeError(f"causal-use prerequisite failed for {case.case_id}")
        ledger = ledger.transition_family(
            case.fixture.target_memory_id,
            MemoryStatus.QUARANTINED,
            reason=f"{case.shift_family} target-family suppression repaired commitment",
            evidence_ref=f"causal-use://{case.case_id}",
        )
        repaired = harness.commit(ledger, case.shifted_regime)
        lifecycle_applied = True
        rows.append(
            _row(
                case,
                "quarantined_shift_recovery",
                ledger,
                task_success=repaired.joint_success,
                retrieved_memory_ids=repaired.retrieved_memory_ids,
            )
        )
        recovered = repaired.joint_success
    else:
        recovered = shifted.joint_success

    return rows, {
        **case.to_dict(),
        "prior_success": prior.joint_success,
        "append_only_shift_success": shifted.joint_success,
        "causal_use_prerequisite": causal_use_passed,
        "lifecycle_applied": lifecycle_applied,
        "post_lifecycle_success": recovered,
        "false_forgetting": case.semantics_changed is False and lifecycle_applied,
    }


def generate_results(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    """Generate public-safe draft rows without providers, credentials, or network."""

    cases = draft_shift_cases()
    case_rows: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    for case in cases:
        rows, result = _run_case(case)
        case_rows.extend(rows)
        summaries.append(result)
    changed = [result for result in summaries if bool(result["semantics_changed"])]
    unchanged = [result for result in summaries if not bool(result["semantics_changed"])]
    families = {str(result["shift_family"]) for result in summaries}
    target_memory_ids = [str(result["target_memory_id"]) for result in summaries]
    regime_ids = {
        (str(result["prior_regime"]), str(result["shifted_regime"])) for result in summaries
    }
    gates = {
        "three_shift_families_registered": families
        == {
            "tool-schema",
            "environment-policy",
            "model/version-identical-semantics",
        },
        "variants_per_family": all(
            sum(1 for result in summaries if result["shift_family"] == family)
            == VARIANTS_PER_FAMILY
            for family in families
        ),
        "independent_target_memory_ids": len(set(target_memory_ids)) == len(cases),
        "independent_regime_id_pairs": len(regime_ids) == len(cases),
        "changed_semantics_fail_append_only": all(
            not bool(result["append_only_shift_success"]) for result in changed
        ),
        "changed_semantics_pass_causal_use": all(
            bool(result["causal_use_prerequisite"]) for result in changed
        ),
        "changed_semantics_recover_after_quarantine": all(
            bool(result["post_lifecycle_success"]) for result in changed
        ),
        "identical_semantics_preserves_use": all(
            bool(result["append_only_shift_success"])
            and not bool(result["lifecycle_applied"])
            for result in unchanged
        ),
        "no_live_calls": True,
    }
    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": "unlearning_multishift_independent_bank_2026_07_20",
        "tier": "deterministic-draft-scaffold",
        "cases": summaries,
        "gates": gates,
        "allowed_claim": (
            "These deterministic draft cases exercise the existing memory "
            "ledger's causal-use and quarantine mechanics under nine "
            "independently authored shift instances (distinct memory ids, "
            "content actions, and regime ids): three tool-schema variants, "
            "three environment-policy variants, and three "
            "model/version-identical-semantics negative-control variants. "
            "They are not live, OOD, stochastic, or neural-unlearning evidence."
        ),
        "next_best_test": (
            "Run the opt-in credentialed live smoke "
            "(run_unlearning_multishift_live_smoke.py) against a subset of "
            "this bank, then pre-register a matched live pilot with "
            "false-forgetting and recovery gates before claiming HU1-HU7."
        ),
    }
    if not all(gates.values()):
        raise RuntimeError("multi-shift draft gates failed")
    _write_json(output_dir / "summary.json", summary)
    _write_jsonl(output_dir / "rows.jsonl", case_rows)
    return summary
