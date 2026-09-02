"""Pure loader: data_root -> hash-verified, in-memory SnapshotBundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Iterator

from .errors import EvidenceError
from .hashing import sha256_dir, sha256_file
from .ledger import EvidenceLedger
from .manifest import Manifest, load_manifest
from .snapshot import SnapshotBundle

_MANIFEST_SUFFIXES = (".yaml", ".yml", ".json")


def _iter_manifest_path_groups(manifests_dir: Path) -> Iterator[list[Path]]:
    """One group of same-stem candidate manifest paths per source.

    Grouped (not just individually yielded) so a source that ships more
    than one manifest format side by side under the same stem -- e.g.
    `cellline_v_test.yaml` + a `cellline_v_test.json` sibling, emitted so
    the loader can ingest a source even where `pyyaml` is not importable,
    see `evidence/manifest.py` -- is tried as ONE source by
    `_load_first_parseable_manifest`, not raised as a spurious
    `duplicate_manifest_source`. Groups are yielded in sorted-stem order
    for determinism: `load_bundle` must return the same `SnapshotBundle`
    for the same `data_root` regardless of filesystem iteration order.
    """
    by_stem: dict[str, list[Path]] = {}
    for path in sorted(manifests_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in _MANIFEST_SUFFIXES:
            by_stem.setdefault(path.stem, []).append(path)
    for stem in sorted(by_stem):
        yield by_stem[stem]


def _load_first_parseable_manifest(candidate_paths: list[Path]) -> Manifest:
    """Load the one manifest a same-stem group of candidates represents.

    A single candidate (the common case -- every pre-existing data root
    has exactly one manifest file per source) is loaded exactly as before,
    with no behavior change: any error propagates unmodified.

    Multiple same-stem candidates (a `.yaml`/`.yml` manifest plus a
    `.json` sibling for the same source) are tried in `_MANIFEST_SUFFIXES`
    order; the first one that parses without raising is used -- "the
    loader chooses whichever it can parse" -- so a `.yaml` manifest that
    fails only because `pyyaml` is not importable in this environment
    falls through to its `.json` sibling instead of failing the whole load.
    """
    if len(candidate_paths) == 1:
        return load_manifest(candidate_paths[0])

    by_suffix = {path.suffix.lower(): path for path in candidate_paths}
    last_error: ValueError | None = None
    for suffix in _MANIFEST_SUFFIXES:
        path = by_suffix.get(suffix)
        if path is None:
            continue
        try:
            return load_manifest(path)
        except ValueError as exc:
            last_error = exc
    assert last_error is not None  # candidate_paths is non-empty by construction
    raise last_error


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise EvidenceError(
            "HASH_MISMATCH", reason="unreadable_file", path=str(path), error=str(exc)
        ) from exc

    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvidenceError(
                "HASH_MISMATCH",
                reason="malformed_jsonl_line",
                path=str(path),
                lineno=lineno,
            ) from exc
        if not isinstance(row, dict):
            raise EvidenceError(
                "HASH_MISMATCH",
                reason="jsonl_line_not_object",
                path=str(path),
                lineno=lineno,
            )
        rows.append(row)
    return rows


def _load_ontology_source(
    onto_dir: Path, manifest: Manifest, source: str
) -> tuple[set[str], dict[str, str], dict[str, tuple[str, ...]], dict[str, str]]:
    actual_hash = sha256_dir(onto_dir)
    if actual_hash != manifest.sha256:
        raise EvidenceError(
            "HASH_MISMATCH",
            source=source,
            path=str(onto_dir),
            expected=manifest.sha256,
            actual=actual_hash,
        )

    curies: set[str] = set()
    curies_path = onto_dir / "curies.txt"
    if curies_path.is_file():
        for line in curies_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                curies.add(line)

    # EVIDENCE-DECISION: labels.jsonl is an OPTIONAL companion file (not
    # every ontology source needs human-readable labels), read the same way
    # aliases.jsonl / cell_ontology.jsonl are: absent -> empty map, present
    # -> parsed and folded into the merged SnapshotBundle.labels map. It
    # participates in sha256_dir(onto_dir) like every other file in the
    # directory, so it is part of the frozen, hash-verified snapshot with
    # no separate verification path needed.
    labels: dict[str, str] = {}
    labels_path = onto_dir / "labels.jsonl"
    if labels_path.is_file():
        for row in _read_jsonl(labels_path):
            try:
                labels[row["curie"]] = row["label"]
            except KeyError as exc:
                raise EvidenceError(
                    "HASH_MISMATCH",
                    reason="malformed_label_row",
                    source=source,
                    row=row,
                ) from exc

    aliases: dict[str, str] = {}
    aliases_path = onto_dir / "aliases.jsonl"
    if aliases_path.is_file():
        for row in _read_jsonl(aliases_path):
            try:
                aliases[row["deprecated"]] = row["canonical"]
            except KeyError as exc:
                raise EvidenceError(
                    "HASH_MISMATCH",
                    reason="malformed_alias_row",
                    source=source,
                    row=row,
                ) from exc

    ancestors: dict[str, tuple[str, ...]] = {}
    cell_ontology_path = onto_dir / "cell_ontology.jsonl"
    if cell_ontology_path.is_file():
        for row in _read_jsonl(cell_ontology_path):
            try:
                ancestors[row["curie"]] = tuple(row.get("ancestors", []))
            except KeyError as exc:
                raise EvidenceError(
                    "HASH_MISMATCH",
                    reason="malformed_cell_ontology_row",
                    source=source,
                    row=row,
                ) from exc

    return curies, aliases, ancestors, labels


def _load_evidence_source(
    evidence_file: Path,
    manifest: Manifest,
    source: str,
    all_records: dict[str, dict[str, Any]],
) -> str:
    actual_hash = sha256_file(evidence_file)
    if actual_hash != manifest.sha256:
        raise EvidenceError(
            "HASH_MISMATCH",
            source=source,
            path=str(evidence_file),
            expected=manifest.sha256,
            actual=actual_hash,
        )

    for row in _read_jsonl(evidence_file):
        evidence_id = row.get("evidence_id")
        if not evidence_id:
            raise EvidenceError(
                "HASH_MISMATCH",
                reason="record_missing_evidence_id",
                source=source,
                path=str(evidence_file),
            )
        if evidence_id in all_records:
            raise EvidenceError(
                "HASH_MISMATCH", reason="duplicate_evidence_id", evidence_id=evidence_id
            )
        all_records[evidence_id] = row

    return actual_hash


def load_bundle(
    data_root: Path, *, allowed_sources: Iterable[str] | None = None
) -> SnapshotBundle:
    """Load, hash-verify, and return a SnapshotBundle for ``data_root``.

    Pure: given the same ``data_root`` on disk, deterministically returns
    an equivalent ``SnapshotBundle`` every time. No caching to disk, no
    network calls, no mutation of ``data_root``.

    Expected layout::

        data_root/
          manifests/*.{yaml,json}
          ontology_snapshots/<source>/{aliases.jsonl, cell_ontology.jsonl, curies.txt, labels.jsonl}
          evidence_records/<source>/records.jsonl

    ``labels.jsonl`` (one ``{"curie": ..., "label": ...}`` object per line)
    is an optional companion file per ontology source. When present, it is
    merged across every loaded source into ``SnapshotBundle.labels`` for
    human-readable rendering (e.g. ``src/rules/licensing.py``'s accepted
    conditions) -- purely additive, never used for identity/matching.

    Fails closed (raises ``EvidenceError("HASH_MISMATCH", ...)``) on any
    manifest whose declared ``sha256`` disagrees with the hash actually
    computed from the files on disk, on a source with no matching data
    directory, on a source present in both locations, on a duplicate
    ``evidence_id`` across sources, or on any unreadable/malformed
    snapshot file. Never silently continues past a mismatch.

    # EVIDENCE-DECISION: row_count in the manifest is stored on Manifest
    # but not cross-checked against the actual number of rows loaded. The
    # brief only specifies a sha256 fail-closed check here; row_count is
    # documented as free-form provenance metadata in the schema and JSON
    # Schema validation of records is explicitly out of scope for this
    # module ("Do NOT do JSON Schema validation here"). Cross-checking it
    # would be a reasonable belt-and-suspenders addition but is left to a
    # higher layer (or a future revision) rather than invented here.
    """
    data_root = Path(data_root)
    # An allowlist is an explicit world boundary.  The historical no-argument
    # call retains ambient loading for existing verifier fixtures; world-bound
    # callers must pass the registered source set and get no source merging.
    allowed = None if allowed_sources is None else frozenset(allowed_sources)
    if allowed is not None and (
        not allowed
        or any(not isinstance(source, str) or not source for source in allowed)
    ):
        raise EvidenceError("HASH_MISMATCH", reason="invalid_source_allowlist")
    manifests_dir = data_root / "manifests"
    ontology_dir = data_root / "ontology_snapshots"
    evidence_dir = data_root / "evidence_records"

    if not manifests_dir.is_dir():
        raise EvidenceError(
            "HASH_MISMATCH", reason="missing_manifests_dir", path=str(manifests_dir)
        )

    manifests: dict[str, Manifest] = {}
    for candidate_paths in _iter_manifest_path_groups(manifests_dir):
        manifest = _load_first_parseable_manifest(candidate_paths)
        if manifest.source in manifests:
            raise EvidenceError(
                "HASH_MISMATCH",
                reason="duplicate_manifest_source",
                source=manifest.source,
                path=str(candidate_paths[0]),
            )
        manifests[manifest.source] = manifest

    if allowed is not None:
        loaded_sources = frozenset(manifests)
        extra = sorted(loaded_sources - allowed)
        missing = sorted(allowed - loaded_sources)
        if extra or missing:
            raise EvidenceError(
                "HASH_MISMATCH",
                reason="source_not_allowlisted",
                extra_sources=extra,
                missing_sources=missing,
            )

    all_curies: set[str] = set()
    all_aliases: dict[str, str] = {}
    all_ancestors: dict[str, tuple[str, ...]] = {}
    all_labels: dict[str, str] = {}
    all_records: dict[str, dict[str, Any]] = {}
    record_file_hashes: dict[str, str] = {}

    for source, manifest in manifests.items():
        onto_source_dir = ontology_dir / source
        evidence_file = evidence_dir / source / "records.jsonl"

        is_ontology = onto_source_dir.is_dir()
        is_evidence = evidence_file.is_file()

        if is_ontology and is_evidence:
            raise EvidenceError(
                "HASH_MISMATCH",
                reason="ambiguous_source_location",
                source=source,
                ontology_dir=str(onto_source_dir),
                evidence_file=str(evidence_file),
            )
        if not is_ontology and not is_evidence:
            raise EvidenceError(
                "HASH_MISMATCH",
                reason="source_data_missing",
                source=source,
                checked=[str(onto_source_dir), str(evidence_file)],
            )

        if is_ontology:
            curies, aliases, ancestors, labels = _load_ontology_source(
                onto_source_dir, manifest, source
            )
            all_curies.update(curies)
            all_aliases.update(aliases)
            all_ancestors.update(ancestors)
            all_labels.update(labels)
        else:
            record_file_hashes[source] = _load_evidence_source(
                evidence_file, manifest, source, all_records
            )

    ledger = EvidenceLedger(all_records, record_file_hashes)
    return SnapshotBundle(
        manifests=manifests,
        ledger=ledger,
        curies=frozenset(all_curies),
        alias_map=all_aliases,
        ancestor_map=all_ancestors,
        labels=all_labels,
    )
