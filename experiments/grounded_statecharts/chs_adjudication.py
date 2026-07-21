"""Independent CHS sealing from pre-registered paired-condition contrasts.

Seals are derived from public-row matched interventions (same task + repeat,
different harness condition), not from the heuristic harvest map. Sealed labels
stay under artifacts/ until an explicit publish step; they never enter episode
rows.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

from experiments.grounded_statecharts.counterfactual_search import (
    COMPONENTS,
    CounterfactualHarnessPilot,
    FaultCase,
)
from experiments.grounded_statecharts.sanitization import sanitize_public_row

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "grounded_statecharts" / "chs_sealed_live"
DEFAULT_INJECTED_CASES = PACKAGE_ROOT / "fixtures" / "counterfactual_faults.json"
DEFAULT_INJECTED_OUTPUT = PACKAGE_ROOT / "results" / "chs_injected_faults"

PROTOCOL_VERSION = "paired-contrast-seal-1"
INJECTED_SEAL_PROTOCOL_VERSION = "injected-fault-seal-1"

SEAL_RULES: tuple[dict[str, Any], ...] = (
    {
        "rule_id": "ct_external_recovers_envelope_fail",
        "family": "recursive_constrained_tool_use",
        "fail_condition": "envelope_only",
        "recover_condition": "envelope_external_guards",
        "fail_requires": {"joint_success": False},
        "recover_requires": {"joint_success": True},
        "responsible_component": "orchestration",
        "rationale": (
            "Matched external-guard recovery after envelope-only joint failure "
            "attributes the failure to missing external orchestration guards."
        ),
    },
    {
        "rule_id": "gs_g3_repairs_g0_false_completion",
        "family": "artifact_completion",
        "fail_condition": "statechart_g0",
        "recover_condition": "statechart_g3",
        "fail_requires": {"false_completion": True},
        "recover_requires": {"false_completion": False, "joint_success": True},
        "responsible_component": "orchestration",
        "rationale": (
            "Matched G3 recovery after G0 false completion attributes the "
            "failure to self-report orchestration without artifact guards."
        ),
    },
    {
        "rule_id": "wrong_edge_output_surface",
        "family": None,
        "fail_condition": "wrong_edge_guard",
        "recover_condition": None,
        "fail_requires": {"invalid_transition": True, "joint_success": False},
        "recover_requires": None,
        "responsible_component": "output",
        "rationale": (
            "Wrong-edge invalid transitions are sealed to the output surface "
            "by construction of the wrong_edge_guard condition."
        ),
    },
)

PROTOCOL: dict[str, Any] = {
    "version": PROTOCOL_VERSION,
    "independence": (
        "Labels are produced from matched public-row condition contrasts only. "
        "The heuristic harvest predicted_component is never consulted."
    ),
    "rules": SEAL_RULES,
    "kill_criteria": (
        "Do not treat heuristic harvest agreement as CHS1.",
        "Do not write responsible_component into public episode rows.",
        "Abstain when a paired recover row is missing or contradicts the rule.",
        "Do not claim six-surface CHS1 from orchestration/output-only seals.",
    ),
}

INJECTED_FAULT_PROTOCOL: dict[str, Any] = {
    "version": INJECTED_SEAL_PROTOCOL_VERSION,
    "independence": (
        "Labels are the injected/deterministic fixture's declared "
        "responsible_component, sealed only when the isolated counterfactual "
        "search (counterfactual_search.py) recovers exactly one credited "
        "repair and it matches that declared component. The live heuristic "
        "harvest (chs_from_live.py) and its predicted_component are never "
        "consulted, and no live D2 row is read."
    ),
    "kill_criteria": (
        "Do not treat heuristic harvest agreement as CHS1.",
        "Do not seal a label when the search finds zero or more than one "
        "credited repair, or when placebo receives credit.",
        "Do not write responsible_component into live public episode rows.",
        "Do not claim six-surface CHS1 from injected/deterministic fixture "
        "seals alone: labels remain repository-visible constructions, not "
        "labels withheld from the diagnosis author on real failures.",
    ),
}


def _repo_relative(path: Path) -> str:
    """Render a repo-relative path string; never leak a local absolute path."""

    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _load_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        receipt = sanitize_public_row(row)
        if not receipt.ok:
            raise ValueError(f"row failed sanitization: {row.get('episode_id')}")
        rows.append(dict(receipt.public_row))
    return rows


def _matches(row: Mapping[str, Any], requires: Mapping[str, Any] | None) -> bool:
    if requires is None:
        return True
    return all(row.get(key) is value for key, value in requires.items())


def seal_from_paired_contrasts(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, object]]:
    """Seal labels using only pre-registered paired-condition contrasts."""

    by_key: dict[tuple[str, int], dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for row in rows:
        key = (str(row["task_id"]), int(row["repeat_index"]))
        by_key[key][str(row["condition"])] = row

    sealed: list[dict[str, object]] = []
    for (task_id, repeat_index), conditions in sorted(by_key.items()):
        for rule in SEAL_RULES:
            family = rule["family"]
            fail_condition = str(rule["fail_condition"])
            fail_row = conditions.get(fail_condition)
            if fail_row is None:
                continue
            if family is not None and fail_row.get("family") != family:
                continue
            fail_requires = rule["fail_requires"]
            if not isinstance(fail_requires, Mapping) or not _matches(fail_row, fail_requires):
                continue
            recover_condition = rule["recover_condition"]
            if recover_condition is not None:
                recover_row = conditions.get(str(recover_condition))
                recover_requires = rule["recover_requires"]
                if (
                    recover_row is None
                    or not isinstance(recover_requires, Mapping)
                    or not _matches(recover_row, recover_requires)
                ):
                    continue
                evidence = {
                    "fail_result_digest": fail_row["result_digest"],
                    "recover_result_digest": recover_row["result_digest"],
                    "recover_condition": recover_condition,
                }
            else:
                evidence = {
                    "fail_result_digest": fail_row["result_digest"],
                    "recover_result_digest": None,
                    "recover_condition": None,
                }
            sealed.append(
                {
                    "case_id": f"seal:{fail_row['result_digest']}",
                    "source_episode_id": fail_row["episode_id"],
                    "source_result_digest": fail_row["result_digest"],
                    "task_id": task_id,
                    "family": fail_row["family"],
                    "repeat_index": repeat_index,
                    "fail_condition": fail_condition,
                    "responsible_component": rule["responsible_component"],
                    "fault_id": rule["rule_id"],
                    "rule_id": rule["rule_id"],
                    "protocol_version": PROTOCOL_VERSION,
                    "label_status": "sealed_by_paired_contrast",
                    "evidence": evidence,
                }
            )
    return sealed


def generate_results(
    *,
    rows_path: Path,
    output_dir: Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    if "results" in output_dir.parts:
        raise RuntimeError("refusing to write sealed live labels under results/")
    rows = _load_rows(rows_path)
    sealed = seal_from_paired_contrasts(rows)
    components = sorted({str(item["responsible_component"]) for item in sealed})
    summary = {
        "schema_version": "1.0",
        "tier": "live-paired-contrast-seal",
        "protocol_version": PROTOCOL_VERSION,
        "protocol": PROTOCOL,
        "source_rows": _repo_relative(rows_path),
        "source_row_count": len(rows),
        "sealed_count": len(sealed),
        "components_covered": components,
        "gates": {
            "labels_under_artifacts_only": "results" not in output_dir.parts,
            "heuristic_harvest_not_used": True,
            "six_surface_chs1_claim": False,
            "claim_boundary": (
                "Paired-contrast seals support a narrow orchestration/output "
                "CHS bridge. Full CHS1 still needs withheld labels across all "
                "six surfaces plus matched repair/placebo search."
            ),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    (output_dir / "labels.jsonl").write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in sealed)
    )
    return summary


class _RepairSearchPilot(Protocol):
    """Structural contract for the search used to seal an injected-fault label.

    `CounterfactualHarnessPilot` satisfies this by construction; tests may
    substitute a stub pilot to exercise abstention without depending on the
    deterministic evaluator's internals.
    """

    def run(self, case: FaultCase) -> Any: ...


def seal_from_injected_faults(
    cases: Sequence[FaultCase],
    *,
    pilot: _RepairSearchPilot | None = None,
) -> list[dict[str, object]]:
    """Seal one label per injected/deterministic single-fault fixture.

    Ground truth is the fixture's declared ``responsible_component``, fixed
    at fixture-construction time -- independent of the live heuristic
    harvest (`chs_from_live.py`) and independent of any live D2 episode. A
    label seals only when the isolated counterfactual search
    (`counterfactual_search.py`) recovers exactly one credited repair, that
    repair restores joint success, and it matches the declared component.
    Ambiguous, unrepaired, or placebo-credited cases abstain rather than
    seal a guessed label.
    """

    active_pilot = pilot or CounterfactualHarnessPilot()
    sealed: list[dict[str, object]] = []
    for case in cases:
        result = active_pilot.run(case)
        if (
            not result.counterfactual_repair_success
            or result.placebo_credit
            or result.recovered_component != case.responsible_component
        ):
            continue
        sealed.append(
            {
                "case_id": f"seal:{case.fault_id}",
                "source_episode_id": case.source_episode_id,
                "fault_id": case.fault_id,
                "task_family": case.task_family,
                "responsible_component": case.responsible_component,
                "rule_id": "injected_single_component_search_repair",
                "protocol_version": INJECTED_SEAL_PROTOCOL_VERSION,
                "label_status": "sealed_by_injected_fault_construction",
                "evidence": {
                    "recovered_component": result.recovered_component,
                    "trace_suspect": result.trace_suspect,
                    "trace_repair_success": result.trace_repair_success,
                    "noop_identity": result.noop_identity,
                    "placebo_credit": result.placebo_credit,
                    "evaluation_budget": result.evaluation_budget,
                },
            }
        )
    return sealed


def generate_injected_results(
    *,
    cases_path: Path = DEFAULT_INJECTED_CASES,
    output_dir: Path = DEFAULT_INJECTED_OUTPUT,
) -> dict[str, Any]:
    """Write the injected-fault seal tier under results/ (public-safe, synthetic)."""

    if "artifacts" in output_dir.parts:
        raise RuntimeError(
            "injected-fault seals are public-safe synthetic fixture labels; "
            "write under results/, never under artifacts/"
        )
    cases = FaultCase.load_many(cases_path)
    sealed = seal_from_injected_faults(cases)
    components = sorted({str(item["responsible_component"]) for item in sealed})
    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "tier": "injected-fault-seal",
        "protocol_version": INJECTED_SEAL_PROTOCOL_VERSION,
        "protocol": INJECTED_FAULT_PROTOCOL,
        "source_cases": _repo_relative(cases_path),
        "source_case_count": len(cases),
        "sealed_count": len(sealed),
        "components_covered": components,
        "gates": {
            "public_safe_synthetic_output": "artifacts" not in output_dir.parts,
            "heuristic_harvest_not_used": True,
            "search_verified_unique_recovery_for_every_case": len(sealed) == len(cases),
            "six_surface_chs1_claim": False,
            "claim_boundary": (
                "Injected/deterministic single-fault fixtures with a "
                "search-verified unique repair seal one label per surface. "
                "Labels are constructed and repository-visible, not withheld "
                "real-failure labels, so this tier alone is not a "
                "publishable six-surface CHS1 result."
            ),
        },
        "no_provider_calls": True,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    (output_dir / "labels.jsonl").write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in sealed)
    )
    return summary


def summarize_combined_coverage(
    live_sealed: Sequence[Mapping[str, Any]],
    injected_sealed: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Report per-tier and combined surface coverage without conflating tiers.

    This never claims six-surface CHS1: CHS1 as pre-registered requires
    labels withheld from the diagnosis author across all six surfaces on
    real failures, plus matched repair/placebo search and pre-specified
    abstention handling. Combining a live-episode tier with a synthetic
    injected-fixture tier only shows that the *sealing protocol* now spans
    all six surfaces, not that a real-failure evaluation does.
    """

    live_components = sorted({str(item["responsible_component"]) for item in live_sealed})
    injected_components = sorted(
        {str(item["responsible_component"]) for item in injected_sealed}
    )
    any_tier_components = sorted(set(live_components) | set(injected_components))
    return {
        "live_paired_contrast_components": live_components,
        "injected_fault_seal_components": injected_components,
        "any_tier_sealed_components": any_tier_components,
        "six_surface_any_tier_protocol_coverage": set(any_tier_components) == set(COMPONENTS),
        "six_surface_live_withheld_chs1": False,
        "claim_boundary": (
            "Any-tier surface coverage combines live paired-contrast seals "
            "(real D2 episodes, orchestration/output only so far) with "
            "injected/deterministic fault-construction seals (synthetic, "
            "repository-visible fixtures, all six surfaces). It is not "
            "six-surface CHS1."
        ),
    }
