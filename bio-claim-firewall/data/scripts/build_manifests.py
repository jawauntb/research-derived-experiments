#!/usr/bin/env python3
"""Recompute every manifest's sha256 + row_count from the files actually on disk.

Run this any time a file under data/ontology_snapshots/ or
data/evidence_records/ changes without going through one of the
download_*.py / sample_*.py scripts, or just to double-check integrity
before committing manifests. It is a pure integrity pass: every other
manifest field (source_url, retrieved_at, license, preprocessing_cmd) is
read from the existing manifest and carried forward unchanged.

Uses the SAME hashing functions `evidence/loader.py` verifies against
(`evidence.hashing.sha256_dir` for a directory-backed ontology source,
`sha256_file` for a `records.jsonl`-backed evidence source), imported, never
reimplemented -- so this script can never drift from what the loader
actually checks. Mirrors `tests/fixtures/synthetic_world/recompute_hashes.py`.

Idempotent: running it twice with no source-file changes produces
byte-identical manifests the second time.
"""

from __future__ import annotations

import json
import re
import sys

from _common import (
    EVIDENCE_DIR,
    MANIFESTS_DIR,
    ONTOLOGY_DIR,
    log,
    ontology_row_count,
    sha256_dir,
    sha256_file,
    write_manifest_pair,
)

_MANIFEST_LINE_RE = re.compile(r"^([a-zA-Z0-9_]+):\s*(.*)$")


def _parse_existing_manifest(source: str) -> dict[str, object]:
    """Prefer the .json sibling (unambiguous types); fall back to the flat .yaml."""
    json_path = MANIFESTS_DIR / f"{source}.json"
    if json_path.is_file():
        return json.loads(json_path.read_text(encoding="utf-8"))

    yaml_path = MANIFESTS_DIR / f"{source}.yaml"
    out: dict[str, object] = {}
    for line in yaml_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _MANIFEST_LINE_RE.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif key == "row_count":
            value = int(value)
        out[key] = value
    return out


def _discover_sources() -> list[str]:
    sources: set[str] = set()
    for path in sorted(MANIFESTS_DIR.glob("*.json")):
        sources.add(path.stem)
    for path in sorted(MANIFESTS_DIR.glob("*.yaml")):
        sources.add(path.stem)
    return sorted(sources)


def main() -> int:
    sources = _discover_sources()
    if not sources:
        log(
            f"no manifests found under {MANIFESTS_DIR} -- run a download_*.py script first"
        )
        return 0

    updated = 0
    for source in sources:
        onto_dir = ONTOLOGY_DIR / source
        evidence_file = EVIDENCE_DIR / source / "records.jsonl"
        is_ontology = onto_dir.is_dir()
        is_evidence = evidence_file.is_file()

        if is_ontology and is_evidence:
            log(
                f"SKIP {source}: ambiguous -- both ontology dir and evidence file present"
            )
            continue
        if not is_ontology and not is_evidence:
            log(f"SKIP {source}: no data on disk yet (run its download script first)")
            continue

        fields = _parse_existing_manifest(source)
        if is_ontology:
            digest = sha256_dir(onto_dir)
            row_count = ontology_row_count(source)
        else:
            digest = sha256_file(evidence_file)
            row_count = len(
                [
                    ln
                    for ln in evidence_file.read_text(encoding="utf-8").splitlines()
                    if ln.strip()
                ]
            )

        changed = fields.get("sha256") != digest or fields.get("row_count") != row_count
        fields["sha256"] = digest
        fields["row_count"] = row_count
        write_manifest_pair(source, fields)
        updated += 1
        status = "CHANGED" if changed else "unchanged"
        log(f"{source}: sha256={digest} row_count={row_count} [{status}]")

    log(f"recomputed {updated}/{len(sources)} manifest(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
