"""Publish a claim-safe public dataset from already-sanitized live rows.

Copies only public-schema fields into results/, writes checksums, and refuses
raw/provider material, heuristic candidates, and sealed CHS labels.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from experiments.grounded_statecharts.evaluation import bootstrap_paired_effect
from experiments.grounded_statecharts.runtime import canonical_json
from experiments.grounded_statecharts.sanitization import (
    REQUIRED_PUBLIC_FIELDS,
    sanitize_public_row,
)

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "results" / "d2_pilot_public"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_sanitized_rows(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        receipt = sanitize_public_row(raw)
        if not receipt.ok:
            raise ValueError(
                f"refusing unsanitized row {raw.get('episode_id')}: "
                f"blocked={receipt.blocked_fields} missing={receipt.missing_fields}"
            )
        if set(receipt.public_row) - REQUIRED_PUBLIC_FIELDS:
            # allow only required public fields in the published dataset
            row = {key: receipt.public_row[key] for key in sorted(REQUIRED_PUBLIC_FIELDS)}
        else:
            row = dict(receipt.public_row)
        if any(key in row for key in ("predicted_component", "responsible_component", "raw")):
            raise ValueError("refusing row with label or raw fields")
        rows.append(row)
    return sorted(
        rows,
        key=lambda row: (
            str(row["family"]),
            str(row["task_id"]),
            str(row["condition"]),
            int(row["repeat_index"]),
            str(row["episode_id"]),
        ),
    )


def build_summary(rows: list[dict[str, object]], *, source_path: Path) -> dict[str, Any]:
    constraint_rows = [row for row in rows if row["family"] == "recursive_constrained_tool_use"]
    artifact_rows = [row for row in rows if row["family"] == "artifact_completion"]
    bootstrap: dict[str, object] = {}
    if len({str(row["task_id"]) for row in constraint_rows}) >= 2:
        bootstrap["joint_success_external_minus_envelope"] = bootstrap_paired_effect(
            constraint_rows,
            treatment="envelope_external_guards",
            control="envelope_only",
            metric="joint_success",
            bootstrap_samples=500,
            seed=20260720,
        ).to_dict()
    if len({str(row["task_id"]) for row in artifact_rows}) >= 2:
        bootstrap["false_completion_g3_minus_g0"] = bootstrap_paired_effect(
            artifact_rows,
            treatment="statechart_g3",
            control="statechart_g0",
            metric="false_completion",
            bootstrap_samples=500,
            seed=20260720,
        ).to_dict()
    confirmatory = any(row.get("condition") for row in rows) and not artifact_rows
    return {
        "schema_version": "1.0",
        "tier": "public-live-ct-confirmatory" if confirmatory else "public-live-d2-dataset",
        "source_path": str(source_path),
        "row_count": len(rows),
        "publishable_rows": sum(
            1 for row in rows if (row.get("integrity") or {}).get("publishable") is True
        ),
        "contract": {
            "name_free_prompts_default": True,
            "harness_enforced_conditions": True,
            "labeled_prompts_diagnostic_only": True,
            "excludes_raw_provider_material": True,
            "excludes_chs_sealed_labels": True,
        },
        "bootstrap": bootstrap,
        "allowed_claim": (
            "Public sanitized CT confirmatory rows under the harness-enforced "
            "name-free contract, with task-clustered uncertainty. External-guard "
            "joint-success recovery only — not model-side constraint learning."
            if confirmatory
            else (
                "Public sanitized held-out D2 rows under the harness-enforced "
                "name-free contract, with task-clustered uncertainty. Not a D3 "
                "confirmatory result and not a CHS1 sealed-label benchmark."
            )
        ),
        "non_claims": [
            "model-side constraint learning",
            "Grounded Statecharts product readiness",
            "CHS1 attribution on sealed real failures",
            "HU1–HU7 unlearning",
        ],
    }


def generate_results(*, source_rows: Path, output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    rows = load_sanitized_rows(source_rows)
    if not rows:
        raise ValueError("no rows to publish")
    if not all((row.get("integrity") or {}).get("publishable") is True for row in rows):
        raise ValueError("refusing to publish integrity-invalid rows")
    summary = build_summary(rows, source_path=source_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows_text = "".join(canonical_json(row) + "\n" for row in rows)
    summary_text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    (output_dir / "rows.jsonl").write_text(rows_text)
    (output_dir / "summary.json").write_text(summary_text)
    card = (
        "# Grounded Harness Public D2 Dataset\n\n"
        "Sanitized held-out live evaluation rows under the harness-enforced, "
        "name-free prompt contract.\n\n"
        "## Contents\n\n"
        "- `rows.jsonl`: public-schema episode rows only\n"
        "- `summary.json`: bootstrap contrasts and claim boundary\n"
        "- `checksums.json`: SHA-256 digests of the published files\n\n"
        "## Exclusions\n\n"
        "No prompts, transcripts, provider payloads, heuristic CHS candidates, "
        "or sealed labels.\n"
    )
    (output_dir / "DATASET.md").write_text(card)
    checksums = {
        "rows.jsonl": _sha256_bytes(rows_text.encode()),
        "summary.json": _sha256_bytes(summary_text.encode()),
        "DATASET.md": _sha256_bytes(card.encode()),
    }
    (output_dir / "checksums.json").write_text(
        json.dumps(checksums, indent=2, sort_keys=True) + "\n"
    )
    summary["checksums"] = checksums
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-rows", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = generate_results(source_rows=args.source_rows, output_dir=args.output_dir)
    print(json.dumps({"row_count": summary["row_count"], "output_dir": str(args.output_dir)}))


if __name__ == "__main__":
    main()
