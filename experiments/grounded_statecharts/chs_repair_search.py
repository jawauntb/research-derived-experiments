"""Equal-budget counterfactual repair/placebo search scored against sealed labels.

This module reuses `CounterfactualHarnessPilot` (`counterfactual_search.py`)
unmodified: every repair candidate and the placebo control cost exactly one
evaluation, so no arm gets a budget advantage over any other. What is new here
is the *scoring* path -- it re-runs that equal-budget search fresh (it never
trusts the `evidence` dict already embedded in a sealed label row) and checks
the result against two independently produced label sources for the same six
committed single-fault fixtures:

1. The adjudicated injected-fault seal tier
   (`results/chs_injected_faults/labels.jsonl`, sealed by
   `chs_adjudication.seal_from_injected_faults`, which itself required the
   search to recover exactly one credited repair matching the fixture's
   declared component).
2. The hand-authored synthetic sealed-label fixture
   (`fixtures/chs_sealed_labels.json`, the separate label artifact
   `chs_sealed.py` already scores against).

Agreement between (1) and (2) plus a fresh independent search re-run is a
stronger plumbing check than either alone, and it makes the equal-budget
property (identical per-arm cost, no placebo credit) an explicit, gated
metric rather than an implicit property of the pilot.

Claim boundary: this is still a constructed, repository-visible fixture
bridge over the same six deterministic single-fault cases used throughout
`counterfactual_search.py` / `chs_sealed.py` / `chs_adjudication.py`. It is
**not** CHS1 on naturalistic live failures. CHS1 requires labels withheld
from the diagnosis author across all six surfaces on real failure episodes,
scored by this same equal-budget repair/placebo search, which this module
does not provide.

This module also adds a stronger *withheld-at-score-time* tier
(`seal_withheld_labels` / `generate_withheld_seals` /
`score_withheld_repair_search` / `generate_withheld_results`): the equal-
budget search runs over `BlindFaultCase` / `BlindCounterfactualHarnessPilot`
(`counterfactual_search.py`), a case/result representation with no
`responsible_component` attribute at all, so the search procedure itself
cannot read the label even in principle. The label is written to a separate
file (`results/chs_withheld_seals/labels.jsonl`) that the search never
opens, and is joined back in by `fault_id` only, after the blind search has
already returned. This closes the gap the tier above leaves open: there,
`CounterfactualHarnessPilot.run` is handed the full `FaultCase` (including
`responsible_component`), so even though the *decision* logic never branches
on that field, the deterministic evaluator inside the search still reads it.
The withheld tier's claim boundary is the same as above: still synthetic,
repository-visible fixtures, still not CHS1 on naturalistic live failures --
what is new is that "withheld from the search" is now a structural property
of the types involved, not just a claim about how the scoring code happens
to be written.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

from experiments.grounded_statecharts.chs_adjudication import (
    INJECTED_SEAL_PROTOCOL_VERSION,
)
from experiments.grounded_statecharts.chs_sealed import SealedLabel
from experiments.grounded_statecharts.counterfactual_search import (
    COMPONENTS,
    BlindCounterfactualHarnessPilot,
    BlindFaultCase,
    BlindSearchResult,
    CounterfactualHarnessPilot,
    FaultCase,
    SearchResult,
)

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_SEALED_LABELS = PACKAGE_ROOT / "results" / "chs_injected_faults" / "labels.jsonl"
DEFAULT_FIXTURE_LABELS = PACKAGE_ROOT / "fixtures" / "chs_sealed_labels.json"
DEFAULT_CASES = PACKAGE_ROOT / "fixtures" / "counterfactual_faults.json"
DEFAULT_OUTPUT = PACKAGE_ROOT / "results" / "chs_repair_search"
DEFAULT_WITHHELD_SEAL_OUTPUT = PACKAGE_ROOT / "results" / "chs_withheld_seals"
DEFAULT_WITHHELD_SEALED_LABELS = DEFAULT_WITHHELD_SEAL_OUTPUT / "labels.jsonl"
DEFAULT_WITHHELD_SEARCH_OUTPUT = PACKAGE_ROOT / "results" / "chs_withheld_seal_search"

_REQUIRED_SEALED_LABEL_KEYS = {
    "case_id",
    "fault_id",
    "responsible_component",
    "protocol_version",
    "label_status",
}
_SEALED_LABEL_STATUS = "sealed_by_injected_fault_construction"
WITHHELD_SEAL_PROTOCOL_VERSION = "withheld-at-score-time-seal-1"
_WITHHELD_LABEL_STATUS = "sealed_withheld_at_score_time"


@dataclass(frozen=True)
class SealedInjectedLabel:
    """One row from the independently adjudicated injected-fault seal tier."""

    fault_id: str
    responsible_component: str

    @classmethod
    def load_many(cls, path: Path) -> tuple[Self, ...]:
        loaded: list[Self] = []
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or not _REQUIRED_SEALED_LABEL_KEYS <= set(row):
                raise ValueError("sealed injected label row is missing required fields")
            if row["protocol_version"] != INJECTED_SEAL_PROTOCOL_VERSION:
                raise ValueError("sealed injected label has an unexpected protocol version")
            if row["label_status"] != _SEALED_LABEL_STATUS:
                raise ValueError("sealed injected label has an unexpected label status")
            fault_id = row["fault_id"]
            component = row["responsible_component"]
            if not isinstance(fault_id, str) or not fault_id:
                raise ValueError("sealed injected label fault_id must be a non-empty string")
            if component not in COMPONENTS:
                raise ValueError("sealed injected label names an unknown harness surface")
            loaded.append(cls(fault_id=fault_id, responsible_component=component))
        if len({label.fault_id for label in loaded}) != len(loaded):
            raise ValueError("sealed injected labels must name each fault at most once")
        if {label.responsible_component for label in loaded} != set(COMPONENTS):
            raise ValueError("sealed injected labels do not cover every harness surface")
        return tuple(loaded)


@dataclass(frozen=True)
class WithheldSealedLabel:
    """One row from the withheld-at-score-time sealed label store.

    Loaded from a file `BlindCounterfactualHarnessPilot` never opens; the
    join with `predicted_component` happens only in `score_withheld_repair_search`,
    after the blind search has already returned.
    """

    fault_id: str
    responsible_component: str

    @classmethod
    def load_many(cls, path: Path) -> tuple[Self, ...]:
        loaded: list[Self] = []
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or not _REQUIRED_SEALED_LABEL_KEYS <= set(row):
                raise ValueError("withheld sealed label row is missing required fields")
            if row["protocol_version"] != WITHHELD_SEAL_PROTOCOL_VERSION:
                raise ValueError("withheld sealed label has an unexpected protocol version")
            if row["label_status"] != _WITHHELD_LABEL_STATUS:
                raise ValueError("withheld sealed label has an unexpected label status")
            fault_id = row["fault_id"]
            component = row["responsible_component"]
            if not isinstance(fault_id, str) or not fault_id:
                raise ValueError("withheld sealed label fault_id must be a non-empty string")
            if component not in COMPONENTS:
                raise ValueError("withheld sealed label names an unknown harness surface")
            loaded.append(cls(fault_id=fault_id, responsible_component=component))
        if len({label.fault_id for label in loaded}) != len(loaded):
            raise ValueError("withheld sealed labels must name each fault at most once")
        if {label.responsible_component for label in loaded} != set(COMPONENTS):
            raise ValueError("withheld sealed labels do not cover every harness surface")
        return tuple(loaded)


def _equal_budget_ledger(result: SearchResult | BlindSearchResult) -> dict[str, Any]:
    """Report per-arm cost so budget symmetry is an explicit, checkable fact.

    Works for both `SearchResult` and `BlindSearchResult`: both expose the
    same `interventions` tuple of `InterventionResult`.
    """

    repair_costs = {
        intervention.target_component: intervention.cost
        for intervention in result.interventions
        if intervention.kind == "repair"
    }
    placebo_costs = [
        intervention.cost
        for intervention in result.interventions
        if intervention.kind == "placebo"
    ]
    all_costs = set(repair_costs.values()) | set(placebo_costs)
    return {
        "repair_arm_costs": dict(sorted(repair_costs.items())),
        "placebo_arm_cost": placebo_costs[0] if placebo_costs else None,
        "total_arms": len(repair_costs) + len(placebo_costs),
        "equal_budget_repair_vs_placebo": len(all_costs) <= 1,
    }


def score_equal_budget_repair_search(
    sealed_labels: tuple[SealedInjectedLabel, ...],
    fixture_labels: tuple[SealedLabel, ...],
    cases: tuple[FaultCase, ...],
    *,
    pilot: CounterfactualHarnessPilot | None = None,
) -> list[dict[str, Any]]:
    """Re-run the equal-budget search fresh and score it against both label sources.

    Every case must appear in both label sources and in the fixture bank;
    missing coverage raises rather than silently skipping a surface.
    """

    active_pilot = pilot or CounterfactualHarnessPilot()
    cases_by_fault = {case.fault_id: case for case in cases}
    sealed_by_fault = {label.fault_id: label for label in sealed_labels}
    fixture_by_fault = {
        label.fault_id: label for label in fixture_labels if label.fault_id is not None
    }
    missing_sealed = set(cases_by_fault) - set(sealed_by_fault)
    missing_fixture = set(cases_by_fault) - set(fixture_by_fault)
    if missing_sealed:
        raise ValueError(f"fixture cases missing a sealed injected label: {sorted(missing_sealed)}")
    if missing_fixture:
        raise ValueError(f"fixture cases missing a fixture label: {sorted(missing_fixture)}")

    rows: list[dict[str, Any]] = []
    for fault_id in sorted(cases_by_fault):
        case = cases_by_fault[fault_id]
        sealed_label = sealed_by_fault[fault_id]
        fixture_label = fixture_by_fault[fault_id]
        result = active_pilot.run(case)
        ledger = _equal_budget_ledger(result)
        rows.append(
            {
                "fault_id": fault_id,
                "sealed_component": sealed_label.responsible_component,
                "fixture_component": fixture_label.responsible_component,
                "predicted_component": result.recovered_component,
                "sealed_top1_correct": result.recovered_component
                == sealed_label.responsible_component,
                "fixture_top1_correct": result.recovered_component
                == fixture_label.responsible_component,
                "label_sources_agree": sealed_label.responsible_component
                == fixture_label.responsible_component,
                "counterfactual_repair_success": result.counterfactual_repair_success,
                "placebo_credit": result.placebo_credit,
                "evaluation_budget": result.evaluation_budget,
                **ledger,
            }
        )
    return rows


def seal_withheld_labels(cases: tuple[FaultCase, ...]) -> list[dict[str, object]]:
    """Seal one label per fixture from its construction-time ground truth.

    This is the only function in the withheld tier that reads
    `case.responsible_component`. It writes the label to a store the search
    step never opens; the search step itself is only ever handed a
    `BlindFaultCase` (via `BlindFaultCase.from_fault_case`), which has no
    such attribute, so the label cannot leak from here into the search.
    """

    return [
        {
            "case_id": f"withheld-seal:{case.fault_id}",
            "fault_id": case.fault_id,
            "responsible_component": case.responsible_component,
            "protocol_version": WITHHELD_SEAL_PROTOCOL_VERSION,
            "label_status": _WITHHELD_LABEL_STATUS,
        }
        for case in cases
    ]


def generate_withheld_seals(
    *,
    cases_path: Path = DEFAULT_CASES,
    output_dir: Path = DEFAULT_WITHHELD_SEAL_OUTPUT,
) -> dict[str, Any]:
    """Write the withheld-seal label store (public-safe: purely synthetic fixtures).

    Kept under results/ deliberately: every label here traces back to the
    committed `fixtures/counterfactual_faults.json` construction, the same
    fixture bank `chs_sealed.py` / `chs_adjudication.py` already use, so
    sealing never touches a live episode or a provider call.
    """

    if "artifacts" in output_dir.parts:
        raise RuntimeError(
            "withheld-seal labels here are public-safe synthetic fixture "
            "constructions; write under results/, never under artifacts/"
        )
    cases = FaultCase.load_many(cases_path)
    sealed = seal_withheld_labels(cases)
    components_covered = {str(item["responsible_component"]) for item in sealed}
    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "tier": "withheld-at-score-time-seal",
        "protocol_version": WITHHELD_SEAL_PROTOCOL_VERSION,
        "source_cases": _repo_relative(cases_path),
        "sealed_count": len(sealed),
        "components_covered": sorted(components_covered),
        "gates": {
            "public_safe_synthetic_output": "artifacts" not in output_dir.parts,
            "six_surface_coverage": components_covered == set(COMPONENTS),
        },
        "claim_boundary": (
            "Labels here remain repository-visible synthetic fixture "
            "constructions, authored alongside the code that scores them -- "
            "not labels withheld from a diagnosis author on real failures. "
            "The 'withheld' property this tier demonstrates is structural: "
            "the label store is a separate file the search procedure never "
            "opens, and the search's own case/result types "
            "(BlindFaultCase / BlindSearchResult) have no "
            "responsible_component attribute to leak."
        ),
        "no_provider_calls": True,
    }
    if not all(summary["gates"].values()):
        raise RuntimeError("withheld seal generation must cover every harness surface")
    _write_json(output_dir / "summary.json", summary)
    _write_jsonl(output_dir / "labels.jsonl", sealed)
    return summary


def score_withheld_repair_search(
    sealed_labels: tuple[WithheldSealedLabel, ...],
    cases: tuple[FaultCase, ...],
    *,
    pilot: BlindCounterfactualHarnessPilot | None = None,
) -> list[dict[str, Any]]:
    """Run the equal-budget search blind to responsible_component, then score.

    `cases` are used only to build a `BlindFaultCase` (which strips the label
    before the search ever runs -- see `BlindFaultCase.from_fault_case`);
    `sealed_labels` are loaded from a completely separate file and joined by
    `fault_id` only, after the search has already returned its
    `BlindSearchResult`. Both `BlindFaultCase` and `BlindSearchResult` are
    asserted to have no `responsible_component` attribute, so a future edit
    that reintroduces one on either type fails loudly here rather than
    silently weakening the claim.
    """

    active_pilot = pilot or BlindCounterfactualHarnessPilot()
    cases_by_fault = {case.fault_id: case for case in cases}
    sealed_by_fault = {label.fault_id: label for label in sealed_labels}
    missing_sealed = set(cases_by_fault) - set(sealed_by_fault)
    if missing_sealed:
        raise ValueError(
            f"fixture cases missing a withheld sealed label: {sorted(missing_sealed)}"
        )

    rows: list[dict[str, Any]] = []
    for fault_id in sorted(cases_by_fault):
        case = cases_by_fault[fault_id]
        blind_case = BlindFaultCase.from_fault_case(case)
        if hasattr(blind_case, "responsible_component"):
            raise RuntimeError("BlindFaultCase must not carry responsible_component")
        sealed_label = sealed_by_fault[fault_id]
        result = active_pilot.run(blind_case)
        if hasattr(result, "responsible_component"):
            raise RuntimeError("BlindSearchResult must not carry responsible_component")
        ledger = _equal_budget_ledger(result)
        rows.append(
            {
                "fault_id": fault_id,
                "withheld_component": sealed_label.responsible_component,
                "predicted_component": result.recovered_component,
                "withheld_top1_correct": result.recovered_component
                == sealed_label.responsible_component,
                "counterfactual_repair_success": result.counterfactual_repair_success,
                "placebo_credit": result.placebo_credit,
                "evaluation_budget": result.evaluation_budget,
                **ledger,
            }
        )
    return rows


def generate_withheld_results(
    *,
    sealed_labels_path: Path = DEFAULT_WITHHELD_SEALED_LABELS,
    cases_path: Path = DEFAULT_CASES,
    output_dir: Path = DEFAULT_WITHHELD_SEARCH_OUTPUT,
) -> dict[str, Any]:
    """Write the public-safe withheld equal-budget repair-search bundle.

    Reuses this module's ledger/IO helpers (`_equal_budget_ledger`,
    `_write_json`, `_write_jsonl`, `_repo_relative`) and the same
    `--sealed-labels` CLI convention as `run_chs_repair_search.py`
    (`run_chs_withheld_seal_search.py`), pointed at the separate withheld-seal
    store instead of the injected-fault seal tier.
    """

    if "artifacts" in output_dir.parts:
        raise RuntimeError(
            "withheld equal-budget repair-search scoring is public-safe and "
            "synthetic; write under results/, never under artifacts/"
        )
    sealed_labels = WithheldSealedLabel.load_many(sealed_labels_path)
    cases = FaultCase.load_many(cases_path)
    rows = score_withheld_repair_search(sealed_labels, cases)

    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "tier": "withheld-at-score-time-equal-budget-repair-search",
        "source_sealed_labels": _repo_relative(sealed_labels_path),
        "source_cases": _repo_relative(cases_path),
        "cases": len(rows),
        "fault_surfaces": list(COMPONENTS),
        "metrics": {
            "withheld_top1_attribution": statistics.fmean(
                bool(row["withheld_top1_correct"]) for row in rows
            ),
            "placebo_false_credit_rate": statistics.fmean(
                bool(row["placebo_credit"]) for row in rows
            ),
            "mean_evaluation_budget": statistics.fmean(
                int(row["evaluation_budget"]) for row in rows
            ),
        },
        "gates": {
            "six_single_fault_cases_scored": len(rows) == len(COMPONENTS),
            "every_surface_covered": {row["fault_id"] for row in rows}
            == {case.fault_id for case in cases},
            "all_cases_repaired": all(row["counterfactual_repair_success"] for row in rows),
            "no_placebo_credit": not any(row["placebo_credit"] for row in rows),
            "equal_budget_every_case": all(
                row["equal_budget_repair_vs_placebo"] for row in rows
            ),
            "withheld_matches_search": all(row["withheld_top1_correct"] for row in rows),
            "search_case_type_has_no_label_attribute": "responsible_component"
            not in BlindFaultCase.__dataclass_fields__,
            "search_result_type_has_no_label_attribute": "responsible_component"
            not in BlindSearchResult.__dataclass_fields__,
            "no_provider_calls": True,
        },
        "allowed_claim": (
            "On the six committed synthetic single-fault fixtures, an "
            "equal-budget search -- run over a case/result representation "
            "(BlindFaultCase / BlindSearchResult) that has no "
            "responsible_component attribute at all, so the search "
            "procedure itself cannot read one -- freshly recovers a label "
            "loaded only from a separate sealed-label store at score time, "
            "for every surface, with zero placebo credit and exact per-arm "
            "budget parity."
        ),
        "non_claims": [
            "Labels remain synthetic, repository-visible fixture constructions "
            "authored alongside the code that scores them, not labels withheld "
            "from a diagnosis author on real failures.",
            "This is a CHS1-bridge demonstrating the withheld-at-score-time "
            "plumbing property, not author-blind human adjudication CHS1.",
            "No live D2/D3 episode, stochastic replay, multi-fault interaction, "
            "or OOD case was scored by this runner.",
            "This is not CHS1 on naturalistic live failures.",
        ],
        "next_best_test": (
            "Apply this same structurally-blind equal-budget repair/placebo "
            "search to a case representation built from live D2/D3 failure "
            "episodes, scored against labels withheld from the diagnosis "
            "author and stored separately, before making any CHS1 claim."
        ),
        "no_provider_calls": True,
    }
    if not all(summary["gates"].values()):
        raise RuntimeError("withheld equal-budget repair-search gates failed")
    _write_json(output_dir / "summary.json", summary)
    _write_jsonl(output_dir / "rows.jsonl", rows)
    return summary


def _repo_relative(path: Path) -> str:
    repo_root = PACKAGE_ROOT.parents[1]
    try:
        return str(path.resolve().relative_to(repo_root))
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def generate_results(
    *,
    sealed_labels_path: Path = DEFAULT_SEALED_LABELS,
    fixture_labels_path: Path = DEFAULT_FIXTURE_LABELS,
    cases_path: Path = DEFAULT_CASES,
    output_dir: Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    """Write the public-safe equal-budget repair-search bundle under results/."""

    if "artifacts" in output_dir.parts:
        raise RuntimeError(
            "equal-budget repair-search scoring is public-safe and synthetic; "
            "write under results/, never under artifacts/"
        )
    sealed_labels = SealedInjectedLabel.load_many(sealed_labels_path)
    fixture_labels = SealedLabel.load_many(fixture_labels_path)
    cases = FaultCase.load_many(cases_path)
    rows = score_equal_budget_repair_search(sealed_labels, fixture_labels, cases)

    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "tier": "equal-budget-repair-search-on-sealed-labels",
        "source_sealed_labels": _repo_relative(sealed_labels_path),
        "source_fixture_labels": _repo_relative(fixture_labels_path),
        "source_cases": _repo_relative(cases_path),
        "cases": len(rows),
        "fault_surfaces": list(COMPONENTS),
        "metrics": {
            "sealed_top1_attribution": statistics.fmean(
                bool(row["sealed_top1_correct"]) for row in rows
            ),
            "fixture_top1_attribution": statistics.fmean(
                bool(row["fixture_top1_correct"]) for row in rows
            ),
            "label_source_agreement_rate": statistics.fmean(
                bool(row["label_sources_agree"]) for row in rows
            ),
            "placebo_false_credit_rate": statistics.fmean(
                bool(row["placebo_credit"]) for row in rows
            ),
            "mean_evaluation_budget": statistics.fmean(
                int(row["evaluation_budget"]) for row in rows
            ),
        },
        "gates": {
            "six_single_fault_cases_scored": len(rows) == len(COMPONENTS),
            "every_surface_covered": {row["fault_id"] for row in rows}
            == {case.fault_id for case in cases},
            "all_cases_repaired": all(row["counterfactual_repair_success"] for row in rows),
            "no_placebo_credit": not any(row["placebo_credit"] for row in rows),
            "equal_budget_every_case": all(
                row["equal_budget_repair_vs_placebo"] for row in rows
            ),
            "sealed_matches_search": all(row["sealed_top1_correct"] for row in rows),
            "fixture_matches_search": all(row["fixture_top1_correct"] for row in rows),
            "sealed_and_fixture_labels_agree": all(
                row["label_sources_agree"] for row in rows
            ),
            "no_provider_calls": True,
        },
        "allowed_claim": (
            "On the six committed synthetic single-fault fixtures, an "
            "equal-budget search -- identical per-arm cost across every repair "
            "candidate and the placebo control -- freshly recovers the "
            "adjudicated injected-fault sealed label and the independently "
            "authored fixture label for every surface, with zero placebo "
            "credit and exact per-arm budget parity."
        ),
        "non_claims": [
            "Labels remain synthetic, repository-visible fixture constructions "
            "authored alongside the code that scores them, not labels withheld "
            "from the diagnosis author on real failures.",
            "No live D2/D3 episode, stochastic replay, multi-fault interaction, "
            "or OOD case was scored by this runner.",
            "Agreement between the injected-fault seal tier and the fixture "
            "label file is not independent triangulation across data sources: "
            "both trace back to the same committed fixture bank.",
            "This is not CHS1 on naturalistic live failures.",
        ],
        "next_best_test": (
            "Apply this same equal-budget repair/placebo scorer to labels "
            "withheld from the diagnosis author on live D2/D3 failure episodes "
            "across all six surfaces before making any CHS1 claim."
        ),
        "no_provider_calls": True,
    }
    if not all(summary["gates"].values()):
        raise RuntimeError("equal-budget repair-search gates failed")
    _write_json(output_dir / "summary.json", summary)
    _write_jsonl(output_dir / "rows.jsonl", rows)
    return summary
