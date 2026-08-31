"""Deterministic canonicalization and hashing for the audit ledger.

`compute_verdict_id` is the tamper-evidence primitive described in
spec/verdict.schema.json: "SHA-256, first 32 hex chars, of the
canonicalized (claim + verdict + derivation + snapshot_hashes +
checker_version) tuple." Here `verdict_body` is the full verdict dict
(it already contains `derivation` when present), so the hashed tuple is
`[claim, verdict_body, snapshot_hashes, checker_version]`.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any


def _normalize(obj: Any) -> Any:
    """Recursively walk `obj`, rejecting anything that isn't JSON-shaped.

    Dict keys are coerced to `str` (JSON object keys are always strings);
    tuples are treated as lists (JSON has no tuple type); floats are
    checked for NaN/Infinity, which are not valid JSON and must never
    silently enter a hash. Sorting of dict keys happens later, in
    `json.dumps(..., sort_keys=True)` -- doing it there instead of here
    keeps this pass a single, simple validation/normalization step.
    """
    if isinstance(obj, dict):
        return {str(k): _normalize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_normalize(v) for v in obj]
    if isinstance(obj, bool) or obj is None or isinstance(obj, str):
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            raise ValueError(
                f"canonicalize_for_hash: non-finite float is not JSON-representable: {obj!r}"
            )
        return obj
    raise TypeError(f"canonicalize_for_hash: unsupported type {type(obj).__name__!r}")


def canonicalize_for_hash(obj: Any) -> bytes:
    """Produce a stable byte representation of a JSON-shaped Python object.

    Guarantees, load-bearing for `compute_verdict_id`'s tamper-evidence
    property:

    - Object keys are sorted lexicographically at every nesting level
      (`sort_keys=True`), so dict insertion order never affects the result.
    - No incidental whitespace: `separators=(",", ":")`.
    - Floats are rendered via the same algorithm as `repr(float)`
      (`json.dumps` calls `float.__repr__` internally for finite floats),
      which is Python's shortest round-tripping representation -- e.g.
      `1.0`, `-0.0`, `1e-10` -- and is what a second clean-room caller of
      this same function will also produce, so two dicts that are equal
      after JSON round-tripping hash identically.
    - `None` / `True` / `False` render as JSON `null` / `true` / `false`.
    - Non-finite floats (`nan`, `inf`, `-inf`) are rejected rather than
      silently emitted as invalid JSON tokens.

    AUDIT-DECISION: `ensure_ascii=False` -- canonical bytes are UTF-8
    encoded unicode rather than `\\uXXXX`-escaped ASCII. Either choice is
    internally consistent (this function is the only place semantic
    content is turned into hash input), but real UTF-8 bytes make the
    canonical form directly inspectable/diffable.
    """
    normalized = _normalize(obj)
    text = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return text.encode("utf-8")


def compute_verdict_id(
    claim: dict,
    verdict_body: dict,
    snapshot_hashes: dict[str, str],
    checker_version: str,
) -> str:
    """Return the first 32 hex chars of sha256 over the canonicalized tuple
    `[claim, verdict_body, snapshot_hashes, checker_version]`.

    Two calls with semantically-equal arguments (regardless of key order,
    dict identity, or which process/invocation made the call) MUST produce
    the same id -- that's the whole tamper-evidence contract.
    """
    payload = [claim, verdict_body, snapshot_hashes, checker_version]
    canonical = canonicalize_for_hash(payload)
    digest = hashlib.sha256(canonical).hexdigest()
    return digest[:32]
