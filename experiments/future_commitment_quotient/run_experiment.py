#!/usr/bin/env python3
"""Run the preregistered exact future-commitment quotient factorial."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict

from .analysis import summarize_rows
from .core import (
    CONDITIONS,
    FAMILIES,
    build_condition_pair,
    build_registered_family,
)


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent
DESIGN_PATH = PACKAGE / "registered_design.json"
PREREGISTRATION_PATH = PACKAGE / "PREREGISTRATION.md"
RAW_PATH = ROOT / "artifacts" / "future_commitment_quotient" / "registered_run.json"
ROWS_PATH = PACKAGE / "results" / "registered_rows.jsonl"
SUMMARY_PATH = PACKAGE / "results" / "summary.json"
SUMMARY_MARKDOWN_PATH = PACKAGE / "results" / "summary.md"
PAPER_PATH = ROOT / "papers" / "future_commitment_quotient" / "paper.md"
CLAIM_CALIBRATION_PATH = PACKAGE / "claim_calibration.json"
CLAIM_CALIBRATION_ARTIFACT_CONTRACT = "future-commitment-quotient-claim-calibration/v2"


class ClaimCalibrationRequirement(TypedDict):
    evidence_anchor: str
    required_content: list[str]


CLAIM_CALIBRATION_REQUIREMENTS: dict[str, ClaimCalibrationRequirement] = {
    "prior_art_citations": {
        "evidence_anchor": "## 9. Relation to prior work",
        "required_content": [
            "Model minimization and bisimulation already establish "
            "coordinate-free state equivalence for planning and transition systems",
            "Unsupervised disentanglement is not identifiable without inductive biases",
            "Causal abstraction and distributed alignment work use interventions "
            "to connect neural states to high-level causal models",
        ],
    },
    "bounded_interaction_prior_art": {
        "evidence_anchor": "## 9. Relation to prior work",
        "required_content": [
            "the 2026 bounded-interaction theorem extends that logic to "
            "agent-limited POMDP probes",
            "Our deterministic finite result is a simpler specialization",
        ],
    },
    "theorem_novelty_calibration": {
        "evidence_anchor": "## 3. Theorems",
        "required_content": [
            "Theorems 1--4 are proved finite specializations or corollaries of "
            "classical automata-minimization, bisimulation, and "
            "distinguishing-sequence results; they are not presented as novel "
            "theorems.",
        ],
    },
    "prior_constraint_swap_null_preserved": {
        "evidence_anchor": "## 8. Resolution of the earlier Constraint-Swap null",
        "required_content": [
            "This paper does not rescue that mechanism.",
            "The null remains evidence against the geometry-mediated mechanism.",
        ],
    },
    "unsupported_claims_withheld": {
        "evidence_anchor": "## 7. What has not been proved",
        "required_content": [
            "It withholds claims about learned constraint discovery, stochastic "
            "agents, real networks, natural tasks, and general intelligence.",
        ],
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def _claim_calibration_audit(
    *,
    calibration_path: Path = CLAIM_CALIBRATION_PATH,
    paper_path: Path = PAPER_PATH,
) -> dict[str, Any]:
    expected_check_ids = set(CLAIM_CALIBRATION_REQUIREMENTS)
    actual_paper_sha256 = _sha256(paper_path)
    paper = paper_path.read_text(encoding="utf-8")
    normalized_paper = _normalize_whitespace(paper)
    try:
        checklist = json.loads(calibration_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {
            "artifact_contract": None,
            "artifact_contract_matches": False,
            "paper_sha256": {
                "expected": None,
                "actual": actual_paper_sha256,
                "matches": False,
            },
            "independent_review": {
                "status": "unavailable",
                "approved": False,
            },
            "human_review": {
                "status": "unavailable",
                "approved": False,
            },
            "checks": {},
            "identifiers_match": False,
            "schema_valid": False,
            "machine_checks_pass": False,
            "error": f"{type(error).__name__}: {error}",
            "pass": False,
        }

    if not isinstance(checklist, dict):
        checklist = {}
    checks = checklist.get("checks")
    if not isinstance(checks, dict):
        checks = {}
    identifiers_match = set(checks) == expected_check_ids

    details: dict[str, dict[str, Any]] = {}
    for check_id, requirement in CLAIM_CALIBRATION_REQUIREMENTS.items():
        raw_check = checks.get(check_id)
        check = raw_check if isinstance(raw_check, dict) else {}
        evidence_anchor = requirement["evidence_anchor"]
        required_content = requirement["required_content"]
        required_content_present = {
            content: _normalize_whitespace(content) in normalized_paper
            for content in required_content
        }
        details[check_id] = {
            "adjudication": check.get("adjudication"),
            "adjudication_approved": check.get("adjudication") == "approved",
            "evidence_anchor": check.get("evidence_anchor"),
            "evidence_anchor_matches": (
                check.get("evidence_anchor") == evidence_anchor
            ),
            "evidence_anchor_present": evidence_anchor in paper,
            "required_content": check.get("required_content"),
            "required_content_matches": (
                check.get("required_content") == required_content
            ),
            "required_content_present": required_content_present,
            "schema_valid": (
                isinstance(raw_check, dict)
                and set(raw_check)
                == {"adjudication", "evidence_anchor", "required_content"}
            ),
        }

    independent_review = checklist.get("independent_review")
    if not isinstance(independent_review, dict):
        independent_review = {}
    independent_review_approved = (
        independent_review.get("status") == "approved"
        and isinstance(independent_review.get("reviewer"), str)
        and bool(independent_review["reviewer"].strip())
        and isinstance(independent_review.get("reviewed_at"), str)
        and bool(independent_review["reviewed_at"].strip())
    )
    human_review = checklist.get("human_review")
    if not isinstance(human_review, dict):
        human_review = {}
    human_review_status = human_review.get("status")
    human_review_approved = (
        human_review_status == "approved"
        and isinstance(human_review.get("reviewer"), str)
        and bool(human_review["reviewer"].strip())
        and isinstance(human_review.get("reviewed_at"), str)
        and bool(human_review["reviewed_at"].strip())
    )
    artifact_contract_matches = (
        checklist.get("artifact_contract") == CLAIM_CALIBRATION_ARTIFACT_CONTRACT
    )
    paper_sha256_matches = checklist.get("paper_sha256") == actual_paper_sha256
    schema_valid = (
        set(checklist)
        == {
            "artifact_contract",
            "paper_sha256",
            "independent_review",
            "human_review",
            "checks",
        }
        and set(independent_review) == {"status", "reviewer", "reviewed_at"}
        and set(human_review) == {"status", "reviewer", "reviewed_at"}
        and all(check["schema_valid"] for check in details.values())
    )
    machine_checks_pass = (
        artifact_contract_matches
        and paper_sha256_matches
        and identifiers_match
        and schema_valid
        and all(
            check["evidence_anchor_matches"]
            and check["evidence_anchor_present"]
            and check["required_content_matches"]
            and all(check["required_content_present"].values())
            for check in details.values()
        )
    )
    return {
        "artifact_contract": checklist.get("artifact_contract"),
        "artifact_contract_matches": artifact_contract_matches,
        "paper_sha256": {
            "expected": checklist.get("paper_sha256"),
            "actual": actual_paper_sha256,
            "matches": paper_sha256_matches,
        },
        "independent_review": {
            **independent_review,
            "approved": independent_review_approved,
        },
        "human_review": {
            **human_review,
            "approved": human_review_approved,
        },
        "checks": details,
        "identifiers_match": identifiers_match,
        "schema_valid": schema_valid,
        "machine_checks_pass": machine_checks_pass,
        "pass": (
            machine_checks_pass
            and independent_review_approved
            and all(check["adjudication_approved"] for check in details.values())
        ),
    }


def run_registered() -> dict[str, Any]:
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    start = int(design["confirmatory_seeds"]["start"])
    stop = int(design["confirmatory_seeds"]["stop_exclusive"])
    registered_families = {
        family: build_registered_family(family) for family in FAMILIES
    }
    rows = [
        build_condition_pair(
            family,
            seed=seed,
            condition=condition,
            registered_family=registered_families[family],
        ).to_row()
        for family in FAMILIES
        for seed in range(start, stop)
        for condition in CONDITIONS
    ]
    claim_calibration = _claim_calibration_audit()
    summary = summarize_rows(
        rows,
        expected_rows=int(design["expected_confirmatory_rows"]),
        expected_seeds=range(start, stop),
        claim_calibration_pass=bool(claim_calibration["pass"]),
    )
    payload = {
        "artifact_contract": "future-commitment-quotient-run/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "design_sha256": _sha256(DESIGN_PATH),
        "preregistration_sha256": _sha256(PREREGISTRATION_PATH),
        "design": design,
        "claim_calibration": claim_calibration,
        "rows": rows,
        "summary": summary,
    }
    return payload


def write_artifacts(payload: dict[str, Any]) -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    rows = payload["rows"]
    ROWS_PATH.write_text(
        "".join(
            json.dumps(row, sort_keys=True, allow_nan=False) + "\n" for row in rows
        ),
        encoding="utf-8",
    )
    SUMMARY_PATH.write_text(
        json.dumps(
            payload["summary"],
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    SUMMARY_MARKDOWN_PATH.write_text(
        render_summary_markdown(payload),
        encoding="utf-8",
    )


def render_summary_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Future-Commitment Quotient — Registered Result",
        "",
        f"- **Decision:** `{summary['verdict']['decision']}`",
        f"- **All gates pass:** `{summary['verdict']['all_gates_pass']}`",
        f"- **Exact confirmatory rows:** `{summary['n_rows']}`",
        f"- **Preregistration SHA-256:** `{payload['preregistration_sha256']}`",
        "",
        "## Predictor separation",
        "",
        "| Predictor | Leave-one-family-out balanced accuracy |",
        "| --- | ---: |",
    ]
    for name, result in summary["predictors"].items():
        lines.append(f"| `{name}` | {result['balanced_accuracy']:.3f} |")
    lines.extend(
        [
            "",
            "## Factorial cells",
            "",
            "| Cell | Coordinate equality | Geometry correlation | "
            "Depth-one agreement | Quotient agreement | Behavioral disagreement |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for condition, metrics in summary["condition_metrics"].items():
        lines.append(
            f"| `{condition}` "
            f"| {metrics['coordinate_equality_mean']:.3f} "
            f"| {metrics['coordinate_geometry_correlation_mean']:.3f} "
            f"| {metrics['depth_one_agreement_mean']:.3f} "
            f"| {metrics['quotient_agreement_mean']:.3f} "
            f"| {metrics['behavioral_disagreement_mean']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Noncompensatory gates",
            "",
            "| Gate | Status |",
            "| --- | --- |",
        ]
    )
    for gate, result in summary["gates"].items():
        lines.append(f"| `{gate}` | **{'PASS' if result['pass'] else 'FAIL'}** |")
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "This exact construction verifies a scoped deterministic finite-agent "
            "double dissociation. It does not establish learned constraint "
            "discovery, stochastic or natural-task generalization, a real-network "
            "mechanism, or a novel quotient theorem.",
            "",
            "## Discovery-Regime Audit",
            "",
            "- **Accepted if gated:** exact coordinate-destroyed conjugacies, "
            "coordinate-preserved delayed mutants, quotient partitions, and "
            "distinguishing witnesses.",
            "- **Rejected/withheld:** coordinate and depth-one baselines as complete "
            "future predictors; universal or novelty claims.",
            "- **Transported evidence:** automata/bisimulation theory explains the "
            "formal quotient; the earlier Constraint-Swap geometry null remains.",
            "- **Residual content:** learning the quotient, choosing interventions, "
            "discovering a load-bearing relaxation, and constructing minimal repair.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Compute and print the verdict without writing artifacts.",
    )
    args = parser.parse_args()
    payload = run_registered()
    if not args.check_only:
        write_artifacts(payload)
    print(
        json.dumps(
            payload["summary"]["verdict"],
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
