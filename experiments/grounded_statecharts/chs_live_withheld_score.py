"""Score the live heuristic harvest against a withheld paired-contrast seal.

Both sides are already independently blind by construction:
`chs_from_live.harvest_candidates` reads only sanitized public rows, which
never carry a `responsible_component` field
(`test_public_rows_never_carry_sealed_labels`); `chs_adjudication.seal_from_paired_contrasts`
never reads `predicted_component`. What this module adds is the missing
third step: join the two, by `source_result_digest` only, after both have
already run, using a sealed-label file this module writes and then re-reads
from disk rather than trusting the in-memory value the sealer just produced.

Claim boundary: this is a live withheld-at-score-time CHS1-bridge, not
author-blind human adjudication CHS1. Paired-contrast seals cover only
orchestration/output on matched real D2 episodes, so joint coverage across
the harvest and the seal is typically a small subset of all rows, and the
heuristic harvest is a symptom-pattern classifier, not an equal-budget
repair/placebo search -- it has no placebo arm and no evaluation-budget
notion, so "agreement" here means predicted-component-matches-seal, not a
placebo arm receiving spurious joint_success credit.
"""

from __future__ import annotations

import json
import statistics
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from experiments.grounded_statecharts.chs_adjudication import (
    PROTOCOL_VERSION,
    seal_from_paired_contrasts,
)
from experiments.grounded_statecharts.chs_from_live import (
    HEURISTIC_VERSION,
    harvest_candidates,
)
from experiments.grounded_statecharts.sanitization import sanitize_public_row

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_ROWS = (
    REPO_ROOT / "artifacts" / "grounded_statecharts" / "d2_pilot_harness_v2" / "rows.jsonl"
)
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "grounded_statecharts" / "chs_live_withheld_score"


def _repo_relative(path: Path) -> str:
    """Render a repo-relative path string; never leak a local absolute path."""

    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _load_public_rows(path: Path) -> list[dict[str, Any]]:
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


def score_live_withheld_harvest(
    candidates: Sequence[Mapping[str, Any]],
    sealed_labels: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Join harvest candidates against sealed labels by result digest only.

    Iterates over the sealed labels (the withheld ground truth) rather than
    the harvest candidates, so an episode the harvest never harvested still
    appears in the join with `harvest_covered=False` instead of silently
    dropping out.
    """

    candidates_by_digest = {
        str(candidate["source_result_digest"]): candidate for candidate in candidates
    }
    rows: list[dict[str, Any]] = []
    for label in sealed_labels:
        digest = str(label["source_result_digest"])
        candidate = candidates_by_digest.get(digest)
        harvested_component = candidate["predicted_component"] if candidate else None
        sealed_component = str(label["responsible_component"])
        rows.append(
            {
                "source_result_digest": digest,
                "sealed_component": sealed_component,
                "harvested_component": harvested_component,
                "harvest_covered": candidate is not None,
                "top1_agrees": harvested_component == sealed_component,
            }
        )
    return rows


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def generate_results(
    *,
    rows_path: Path = DEFAULT_ROWS,
    output_dir: Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    """Seal, harvest, and join fresh from live rows; never trust a stale file.

    Refuses `results/` output: the join reports per-episode
    `source_result_digest` values and component labels derived from real D2
    episodes, so it stays private under `artifacts/`, like every other
    live-row-derived CHS artifact in this package.
    """

    if "results" in output_dir.parts:
        raise RuntimeError(
            "live withheld-seal scoring touches real episode rows; write "
            "under artifacts/, never under results/"
        )
    rows = _load_public_rows(rows_path)
    sealed = seal_from_paired_contrasts(rows)
    candidates = harvest_candidates(rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(output_dir / "sealed_labels.jsonl", sealed)
    _write_jsonl(output_dir / "harvest_candidates.jsonl", candidates)

    # Re-read both from disk: the join below runs against the sealed store
    # and the harvest ledger as written, never the in-memory objects the
    # sealer/harvester just produced.
    reloaded_sealed = [
        json.loads(line)
        for line in (output_dir / "sealed_labels.jsonl").read_text().splitlines()
        if line.strip()
    ]
    reloaded_candidates = [
        json.loads(line)
        for line in (output_dir / "harvest_candidates.jsonl").read_text().splitlines()
        if line.strip()
    ]
    join_rows = score_live_withheld_harvest(reloaded_candidates, reloaded_sealed)
    covered = [row for row in join_rows if row["harvest_covered"]]

    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "tier": "live-withheld-at-score-time-harvest-vs-paired-contrast-seal",
        "seal_protocol_version": PROTOCOL_VERSION,
        "harvest_heuristic_version": HEURISTIC_VERSION,
        "source_rows": _repo_relative(rows_path),
        "source_row_count": len(rows),
        "sealed_count": len(sealed),
        "harvest_candidate_count": len(candidates),
        "joint_coverage_count": len(covered),
        "metrics": {
            "seal_coverage_rate": (len(covered) / len(join_rows)) if join_rows else 0.0,
            "top1_agreement_rate_given_coverage": (
                statistics.fmean(bool(row["top1_agrees"]) for row in covered)
                if covered
                else None
            ),
        },
        "gates": {
            "labels_under_artifacts_only": "results" not in output_dir.parts,
            "harvest_never_reads_sealed_store": True,
            "seal_never_reads_harvest_predictions": True,
            "join_performed_after_both_independently_return": True,
            "six_surface_chs1_claim": False,
        },
        "allowed_claim": (
            "Among live D2 harness-v2 rows where the paired-contrast seal "
            "commits a label, the sanitized-row heuristic harvest -- which "
            "has no access to responsible_component because public rows "
            "never carry one -- is scored for top-1 agreement, joined by "
            "result digest only, after both procedures have already run "
            "independently."
        ),
        "non_claims": [
            "The heuristic harvest is a symptom-pattern classifier, not an "
            "equal-budget repair/placebo search: it has no placebo arm or "
            "evaluation-budget notion.",
            "Paired-contrast seals cover only orchestration/output on "
            "matched real episodes, so joint coverage is a narrow subset "
            "of all rows.",
            "This is a live withheld-at-score-time CHS1-bridge, not "
            "author-blind human adjudication CHS1.",
        ],
        "next_best_test": (
            "Extend live-episode surface coverage to context/tools/"
            "generation/memory, and replace the heuristic harvest with an "
            "equal-budget repair/placebo search over live episodes, before "
            "making any CHS1 claim."
        ),
    }
    _write_json(output_dir / "summary.json", summary)
    _write_jsonl(output_dir / "rows.jsonl", join_rows)
    return summary
