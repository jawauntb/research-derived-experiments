"""Publish curated row-level artifacts for Phase 6 semantic selection."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROWS_JSONL = Path(
    "experiments/structure_compatible_generalization/results/"
    "semantic_selection_rows_2026_07_06.jsonl"
)
SELECTION_RECORDS_JSONL = Path(
    "experiments/structure_compatible_generalization/results/"
    "semantic_selection_records_2026_07_06.jsonl"
)
MANIFEST_JSON = Path(
    "experiments/structure_compatible_generalization/results/"
    "semantic_selection_row_release_manifest_2026_07_06.json"
)
REPORT_MD = Path(
    "experiments/structure_compatible_generalization/results/"
    "semantic_selection_row_release_2026_07_06.md"
)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with path.open("w") as f:
        for row in rows:
            line = json.dumps(row, sort_keys=True)
            h.update(line.encode("utf-8"))
            h.update(b"\n")
            f.write(line + "\n")
    return h.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path.write_text(text)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_release(payload: dict[str, Any]) -> dict[str, Any]:
    rows = list(payload["rows"])
    records = list(payload["selection_records"])
    manifest = dict(payload.get("manifest", {}))
    return {
        "run_id": "semantic_selection_row_release_2026_07_06",
        "kind": "curated_phase6_semantic_selection_row_release",
        "source_payload_kind": payload.get("kind"),
        "source_manifest": manifest,
        "n_rows": len(rows),
        "n_selection_records": len(records),
        "row_schema": {
            "rows": "DiagnosticRow records: model/config metrics, compatibility scores, and selection metadata.",
            "selection_records": "Per-zoo selector outcomes over ID-equivalent candidate sets.",
            "privacy_curation": "No embeddings, model weights, credentials, or provider paths are included.",
        },
        "claim_boundary": [
            "This is a finite regenerated row release for Phase 6 semantic selection.",
            "It is not universal OOD certification or open-world semantic robustness.",
        ],
        "rows": rows,
        "selection_records": records,
    }


def write_release(release: dict[str, Any], out_root: Path = Path(".")) -> list[Path]:
    rows_path = out_root / ROWS_JSONL
    records_path = out_root / SELECTION_RECORDS_JSONL
    manifest_path = out_root / MANIFEST_JSON
    report_path = out_root / REPORT_MD
    rows_hash = _write_jsonl(rows_path, release["rows"])
    records_hash = _write_jsonl(records_path, release["selection_records"])
    manifest = {
        key: value
        for key, value in release.items()
        if key not in {"rows", "selection_records"}
    }
    manifest["artifacts"] = {
        ROWS_JSONL.as_posix(): {
            "rows": release["n_rows"],
            "sha256": rows_hash,
        },
        SELECTION_RECORDS_JSONL.as_posix(): {
            "rows": release["n_selection_records"],
            "sha256": records_hash,
        },
    }
    manifest_hash = _write_json(manifest_path, manifest)
    lines = [
        "# Phase 6 Semantic Selection Row Release",
        "",
        "Date: 2026-07-06",
        "",
        "## Contents",
        "",
        f"- Diagnostic rows: {release['n_rows']}",
        f"- Selection records: {release['n_selection_records']}",
        f"- Rows JSONL: `{ROWS_JSONL.as_posix()}`",
        f"- Selection JSONL: `{SELECTION_RECORDS_JSONL.as_posix()}`",
        f"- Manifest JSON: `{MANIFEST_JSON.as_posix()}`",
        "",
        "## Hashes",
        "",
        f"- Rows SHA-256: `{rows_hash}`",
        f"- Selection-record SHA-256: `{records_hash}`",
        f"- Manifest SHA-256: `{manifest_hash}`",
        "",
        "## Claim Boundary",
        "",
        "- Finite regenerated Phase 6 row-level evidence.",
        "- No embeddings, model weights, credentials, or provider paths are included.",
        "- Not universal OOD certification or open-world semantic robustness.",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n")
    return [rows_path, records_path, manifest_path, report_path]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", type=Path)
    parser.add_argument("--out-root", type=Path, default=Path("."))
    args = parser.parse_args()
    payload = json.loads(args.payload.read_text())
    release = build_release(payload)
    for path in write_release(release, args.out_root):
        print(path)


if __name__ == "__main__":
    main()
