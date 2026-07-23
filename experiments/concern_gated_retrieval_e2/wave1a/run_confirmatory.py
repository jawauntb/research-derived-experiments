#!/usr/bin/env python3
"""Wave 1a confirmatory aggregator.

Consumes the raw Modal receipt at ``artifacts/cogr_wave1a/e2a_rows.json``
produced by :mod:`.modal_l4_sweep` and produces the Wave 1a screen
verdict at
``experiments/concern_gated_retrieval_e2/wave1a/results/verdict.json``.

Pipeline
--------

1. Load the raw JSON payload.
2. Bucket rows by ``(family, seed)`` and per-arm ``arm`` slot.
3. Build :class:`SpecificityRow` objects, one per ``(family, seed)``,
   filling the seven canonical arm slots
   (``frozen_wrong``, ``online_learned_ips``, ``online_learned_dr``,
   ``info_matched_value``, ``info_matched_priority``,
   ``info_matched_recency``, ``wrong_agent``).
4. Compose the rows for each family into a :class:`SpecificityReport`
   and score it through :func:`score_e2a_all` against
   :data:`WAVE1A_PREREGISTERED_THRESHOLDS`.
5. For every ``(family, arm)`` cell whose receipts feed the coverage
   audit (``online_learned_ips``, ``online_learned_dr``,
   ``condition::shuffled``, ``condition::wrong_agent`` — the four
   receipt-producing conditions in ``PREREGISTRATION.md`` §5.1),
   reconstruct a :class:`ProbeReceipt`, resolve the per-family
   ``TCR(f)`` by unioning ``episode._answer_key`` values across the
   family's episodes, and call :func:`audit_coverage` with
   :data:`DEFAULT_COVERAGE_FLOOR`.
6. Write the screen verdict JSON.

Wave 1a decision rule (``PROMOTION_CONTRACT.md``): non-compensatory —
any single-gate FAIL kills the wave. This module reports the union of
per-family FAILs, the coverage audit results, and the aggregate
screen decision (``PASS`` iff every family PASSes and every coverage
audit passes; ``KILL`` otherwise). Per the honor-the-preregistration
rule, no post-hoc threshold swap is permitted.

Wave 1a scope
-------------

Aggregation only. This module CANNOT establish learned memory
geometry, an L1 dual-source-retrieval mechanism claim, or an L2
concern-recovery claim; those are Wave 1b objects.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal, Mapping, cast

# Path shim so ``python experiments/.../run_confirmatory.py`` works
# whether the caller is running from the repo root or from inside the
# subpackage.
for _parent in Path(__file__).resolve().parents:
    if (_parent / "experiments").exists():
        sys.path.insert(0, str(_parent))
        break

from experiments.concern_gated_retrieval_e2.wave0.concern_update import (  # noqa: E402
    ProbeReceipt,
)
from experiments.concern_gated_retrieval_e2.wave1a.coverage_audit import (  # noqa: E402
    DEFAULT_COVERAGE_FLOOR,
    CoverageAuditFailure,
    CoverageVerdict,
    audit_coverage,
)
from experiments.concern_gated_retrieval_e2.wave1a.arms import (  # noqa: E402
    ARM_FROZEN_WRONG,
    CONDITION_ARM_ORACLE,
    CONDITION_ARM_SHUFFLED,
    CONDITION_ARM_WRONG_AGENT,
    COVERAGE_AUDIT_ARMS,
    DEFAULT_ARTIFACT_PATH,
    FAMILY_SEED_RANGES,
    SPECIFICITY_ARMS,
)
from experiments.concern_gated_retrieval_e2.wave1a.promotion_harness import (  # noqa: E402
    WAVE1A_PREREGISTERED_THRESHOLDS,
    score_e2a_all,
)
from experiments.concern_gated_retrieval_e2.wave1a.specificity import (  # noqa: E402
    COMPARATORS,
    ContrastAggregate,
    SpecificityReport,
    SpecificityRow,
    VARIANTS,
    compute_contrast_aggregate,
)


__all__ = [
    "DEFAULT_VERDICT_PATH",
    "aggregate",
    "main",
    "read_rows",
    "write_verdict",
]


#: Committed public verdict path.
DEFAULT_VERDICT_PATH: Final[Path] = (
    Path(__file__).resolve().parent / "results" / "verdict.json"
)


# --------------------------------------------------------------------------- #
# Row-shape helpers
# --------------------------------------------------------------------------- #


def _row_key(row: Mapping[str, Any]) -> tuple[str, int]:
    return str(row["family"]), int(row["seed"])


def _receipt_from_row(row: Mapping[str, Any]) -> ProbeReceipt:
    """Reconstruct a :class:`ProbeReceipt` from a raw sweep row.

    Wave 0's :class:`ProbeReceipt` ``__post_init__`` enforces the
    ``selection_propensity ∈ (0, 1]`` and ``template_family_split ∈
    {"calibration", "confirmatory"}`` invariants, so a corrupted row
    fails here rather than silently entering the audit.
    """
    return ProbeReceipt(
        episode_id=str(row["episode_id"]),
        candidate=str(row["candidate"]),
        selection_propensity=float(row["selection_propensity"]),
        source_id=str(row["source_id"]),
        template_family_split=cast(
            Literal["calibration", "confirmatory"],
            str(row["template_family_split"]),
        ),
        exploratory=bool(row["exploratory"]),
    )


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class FamilyAggregate:
    """One family's aggregation output.

    Attributes
    ----------
    report:
        The :class:`SpecificityReport` scored by
        :func:`score_e2a_all`.
    coverage:
        Per-arm coverage verdicts for
        :data:`COVERAGE_AUDIT_ARMS`. Missing arms indicate an empty
        cell (automatic failure); the ``passed`` field is ``False`` on
        those.
    """

    report: SpecificityReport
    coverage: Mapping[str, CoverageVerdict]


def _family_tcr(rows_for_family: list[Mapping[str, Any]]) -> frozenset[str]:
    """Return the union of ``episode._answer_key`` node ids for one family.

    The sweep row shape carries the sealed answer-key nodes only on the
    first arm per ``(family, seed)`` — see
    :func:`experiments.concern_gated_retrieval_e2.wave1a.modal_l4_sweep._row_from_result`.
    Unioning across every row is safe because the empty lists on the
    subsequent arms contribute no elements.
    """
    tcr: set[str] = set()
    for row in rows_for_family:
        nodes = row.get("answer_key_nodes") or ()
        for node in nodes:
            if not isinstance(node, str) or not node:
                continue
            tcr.add(node)
    return frozenset(tcr)


def aggregate(
    payload: Mapping[str, Any],
    *,
    coverage_floor: float = DEFAULT_COVERAGE_FLOOR,
) -> dict[str, Any]:
    """Aggregate a raw sweep payload into the Wave 1a screen verdict.

    Parameters
    ----------
    payload:
        The raw Modal receipt loaded from
        ``artifacts/cogr_wave1a/e2a_rows.json``. Expected keys: ``rows``
        (list of per-arm dicts) and, optionally, ``manifest`` /
        ``cell_receipts`` for the operational receipt echo.
    coverage_floor:
        Wave 1a §5.1 propensity-weighted coverage floor (default
        :data:`DEFAULT_COVERAGE_FLOOR`, ``0.01``).

    Returns
    -------
    dict
        The screen verdict JSON. Includes per-family
        :class:`PromotionVerdict` data, coverage receipts, aggregate
        decision (``PASS`` iff every family PASSes and every coverage
        audit passes), and echoes the Modal manifest.
    """
    rows = list(payload.get("rows", []))
    # Bucket rows by (family, seed) and by arm.
    grouped: dict[tuple[str, int], dict[str, Mapping[str, Any]]] = defaultdict(dict)
    per_family_rows: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    per_family_arm_receipts: dict[str, dict[str, list[ProbeReceipt]]] = defaultdict(
        lambda: defaultdict(list)
    )
    per_family_arm_rewards: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    per_arm_totals: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )

    for row in rows:
        key = _row_key(row)
        family, _seed = key
        arm = str(row["arm"])
        grouped[key][arm] = row
        per_family_rows[family].append(row)
        per_arm_totals[family][arm] += 1
        # Coverage audit consumes receipts from the four
        # receipt-producing conditions in PREREGISTRATION.md §5.1.
        if arm in COVERAGE_AUDIT_ARMS:
            per_family_arm_receipts[family][arm].append(_receipt_from_row(row))
        # Diagnostic rewards per arm (for the oracle ceiling column,
        # which is not part of SpecificityReport but is echoed in the
        # verdict).
        per_family_arm_rewards[family][arm].append(float(row["realized_reward"]))

    reports: dict[str, SpecificityReport] = {}
    coverage_verdicts_per_family: dict[str, dict[str, dict[str, Any]]] = {}

    for family in sorted(FAMILY_SEED_RANGES):
        family_rows = per_family_rows.get(family, [])
        if not family_rows:
            # No rows for this family — treat as a KILL by emitting an
            # empty verdict.
            continue

        # Build SpecificityRows in seed order.
        seeds_seen: list[int] = []
        specificity_rows: list[SpecificityRow] = []
        for key in sorted(
            grouped, key=lambda k: (k[0], k[1])
        ):
            if key[0] != family:
                continue
            arm_map = grouped[key]
            # Every canonical specificity arm must be present.
            missing = tuple(a for a in SPECIFICITY_ARMS if a not in arm_map)
            if missing:
                raise ValueError(
                    f"family {family!r} seed {key[1]!r} missing arms "
                    f"{missing}; rows dropped or the sweep did not run "
                    "the full canonical slate"
                )
            rewards: dict[str, float] = {}
            for arm in SPECIFICITY_ARMS:
                rewards[arm] = float(arm_map[arm]["realized_reward"])
            episode_id = str(arm_map[ARM_FROZEN_WRONG]["episode_id"])
            specificity_rows.append(
                SpecificityRow(
                    family=family,
                    seed=int(key[1]),
                    episode_id=episode_id,
                    rewards=rewards,
                )
            )
            seeds_seen.append(int(key[1]))

        # Aggregate arm means.
        arm_means: dict[str, float] = {}
        n = len(specificity_rows)
        for arm in SPECIFICITY_ARMS:
            arm_means[arm] = (
                sum(float(r.rewards[arm]) for r in specificity_rows) / n
                if n > 0
                else 0.0
            )
        contrasts: list[ContrastAggregate] = []
        for variant in VARIANTS:
            for comparator in COMPARATORS:
                contrasts.append(
                    compute_contrast_aggregate(
                        specificity_rows,
                        variant=variant,
                        comparator=comparator,
                    )
                )
        report = SpecificityReport(
            family=family,
            seeds=tuple(seeds_seen),
            rows=tuple(specificity_rows),
            variants=VARIANTS,
            comparators=COMPARATORS,
            contrasts=tuple(contrasts),
            arm_means=arm_means,
            frozen_wrong_mean=float(arm_means[ARM_FROZEN_WRONG]),
        )
        reports[family] = report

        # Coverage audit.
        tcr = _family_tcr(family_rows)
        coverage_family: dict[str, dict[str, Any]] = {}
        for arm in COVERAGE_AUDIT_ARMS:
            receipts = per_family_arm_receipts.get(family, {}).get(arm, [])
            try:
                verdict = audit_coverage(
                    receipts, tcr, floor=coverage_floor
                )
                coverage_family[arm] = _coverage_dict(verdict, passed=True)
            except CoverageAuditFailure as exc:
                coverage_family[arm] = _coverage_dict(exc.verdict, passed=False)
        coverage_verdicts_per_family[family] = coverage_family

    # Promotion verdicts from the harness.
    per_family_verdicts = score_e2a_all(reports, WAVE1A_PREREGISTERED_THRESHOLDS)

    # Non-compensatory aggregate.
    aggregate_kill_reasons: list[str] = []
    for family, verdict in per_family_verdicts.items():
        if not verdict.promoted:
            for reason in verdict.kill_reasons:
                aggregate_kill_reasons.append(f"{family}::{reason}")
    for family, coverage in coverage_verdicts_per_family.items():
        for arm, entry in coverage.items():
            if not entry["passed"]:
                aggregate_kill_reasons.append(f"{family}::G1_COVERAGE::{arm}")

    aggregate_decision = (
        "PASS" if not aggregate_kill_reasons else "KILL"
    )

    verdict_json: dict[str, Any] = {
        "kind": "cogr_wave1a_e2a_screen_verdict",
        "wave": "1a",
        "target": "COGR-E2a concern-update rule screen",
        "confirmatory_seed_range": [200_000, 201_999],
        "coverage_floor": float(coverage_floor),
        "aggregate_screen_decision": aggregate_decision,
        "aggregate_kill_reasons": tuple(aggregate_kill_reasons),
        "families": {},
        "n_rows_total": len(rows),
        "manifest": payload.get("manifest"),
        "cell_receipts": payload.get("cell_receipts"),
    }
    for family in sorted(reports):
        report = reports[family]
        verdict = per_family_verdicts[family]
        verdict_json["families"][family] = {
            "specificity": _specificity_dict(report),
            "coverage": coverage_verdicts_per_family.get(family, {}),
            "promotion_verdict": _verdict_dict(verdict),
            "diagnostic_oracle_ceiling_mean": (
                sum(per_family_arm_rewards[family].get(CONDITION_ARM_ORACLE, []))
                / max(len(per_family_arm_rewards[family].get(CONDITION_ARM_ORACLE, [])), 1)
                if per_family_arm_rewards[family].get(CONDITION_ARM_ORACLE)
                else None
            ),
            "condition_arm_means": {
                arm: (
                    sum(per_family_arm_rewards[family].get(arm, [])) /
                    max(len(per_family_arm_rewards[family].get(arm, [])), 1)
                    if per_family_arm_rewards[family].get(arm) else None
                )
                for arm in (
                    CONDITION_ARM_ORACLE,
                    CONDITION_ARM_SHUFFLED,
                    CONDITION_ARM_WRONG_AGENT,
                )
            },
            "n_seeds": len(report.seeds),
        }
    return verdict_json


def _specificity_dict(report: SpecificityReport) -> dict[str, Any]:
    return {
        "family": report.family,
        "n_seeds": len(report.seeds),
        "arm_means": {
            arm: float(mean) for arm, mean in report.arm_means.items()
        },
        "frozen_wrong_mean": float(report.frozen_wrong_mean),
        "contrasts": [
            {
                "variant": c.variant,
                "comparator": c.comparator,
                "n_clusters": int(c.n_clusters),
                "mean_delta": float(c.mean_delta),
                "cluster_robust_se": float(c.cluster_robust_se),
                "lower_bound_2se": float(c.lower_bound_2se),
            }
            for c in report.contrasts
        ],
    }


def _coverage_dict(verdict: CoverageVerdict, *, passed: bool) -> dict[str, Any]:
    return {
        "passed": bool(passed and verdict.passed),
        "coverage": float(verdict.coverage),
        "floor": float(verdict.floor),
        "n_receipts": int(verdict.n_receipts),
        "n_hits": int(verdict.n_hits),
    }


def _verdict_dict(verdict: Any) -> dict[str, Any]:
    return {
        "promoted": bool(verdict.promoted),
        "kill_reasons": list(verdict.kill_reasons),
        "passing_variants": list(verdict.passing_variants),
        "family": verdict.family,
        "per_gate": {
            key: {
                "gate_id": g.gate_id,
                "passed": bool(g.passed),
                "detail": str(g.detail),
                "variant": g.variant,
                "metrics": {k: float(v) for k, v in g.metrics.items()},
            }
            for key, g in verdict.per_gate.items()
        },
    }


# --------------------------------------------------------------------------- #
# I/O
# --------------------------------------------------------------------------- #


def read_rows(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"raw sweep receipt not found at {path}; run the Modal sweep "
            "first (scripts/deploy_and_run_cogr_wave1a.sh)"
        )
    return json.loads(path.read_text())


def write_verdict(verdict: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m experiments.concern_gated_retrieval_e2.wave1a.run_confirmatory",
        description=(
            "Aggregate the Wave 1a Modal raw receipt into the screen "
            "verdict JSON. Non-compensatory: any per-family FAIL or "
            "coverage FAIL kills the wave."
        ),
    )
    parser.add_argument(
        "--in",
        dest="in_path",
        type=Path,
        default=DEFAULT_ARTIFACT_PATH,
        help=(
            "Path to the raw Modal receipt "
            f"(default: {DEFAULT_ARTIFACT_PATH})."
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_VERDICT_PATH,
        help=(
            "Path for the aggregated verdict JSON "
            f"(default: {DEFAULT_VERDICT_PATH})."
        ),
    )
    parser.add_argument(
        "--coverage-floor",
        type=float,
        default=DEFAULT_COVERAGE_FLOOR,
        help=(
            "PREREGISTRATION.md §5.1 propensity-weighted coverage floor "
            f"(default: {DEFAULT_COVERAGE_FLOOR})."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _cli_parser()
    args = parser.parse_args(argv)
    payload = read_rows(args.in_path)
    verdict = aggregate(payload, coverage_floor=float(args.coverage_floor))
    write_verdict(verdict, args.out)
    print(json.dumps(
        {
            "kind": "cogr_wave1a_verdict_summary",
            "aggregate_screen_decision": verdict["aggregate_screen_decision"],
            "aggregate_kill_reasons": list(verdict["aggregate_kill_reasons"]),
            "n_rows_total": verdict["n_rows_total"],
            "verdict_path": str(args.out),
        },
        indent=2,
        sort_keys=True,
    ))
    return 0 if verdict["aggregate_screen_decision"] == "PASS" else 2


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
