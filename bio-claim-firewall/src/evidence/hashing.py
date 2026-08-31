"""SHA-256 helpers used to verify frozen snapshots have not been tampered with."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    """Hex-encoded SHA-256 digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """Hex-encoded SHA-256 digest of a file's contents, streamed in chunks."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_dir(dir_path: Path) -> str:
    """Hex-encoded SHA-256 over every regular file directly inside ``dir_path``.

    # EVIDENCE-DECISION: an ontology source can span several sibling files
    # (aliases.jsonl, cell_ontology.jsonl, curies.txt) but
    # ``Manifest.sha256`` (spec: evidence.schema.json-adjacent, this
    # module's own Manifest dataclass) is a single field. We define the
    # manifest hash for a directory-backed (ontology) source as SHA-256 over
    # the sorted ``(filename, contents)`` pairs of every regular file
    # directly inside ``dir_path``, each framed as
    # ``b"<name>\\n<len(bytes)>\\n<bytes>"`` and concatenated in filename
    # order. This is deterministic regardless of filesystem iteration order,
    # and it changes if any file is added, removed, renamed, or edited.
    # Evidence sources (a single ``records.jsonl``) use plain
    # ``sha256_file`` instead -- see loader.py.
    """
    digest = hashlib.sha256()
    for file_path in sorted(p for p in Path(dir_path).iterdir() if p.is_file()):
        data = file_path.read_bytes()
        digest.update(file_path.name.encode("utf-8"))
        digest.update(b"\n")
        digest.update(str(len(data)).encode("utf-8"))
        digest.update(b"\n")
        digest.update(data)
    return digest.hexdigest()
