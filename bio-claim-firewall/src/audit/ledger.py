"""The append-only, tamper-evident audit ledger.

Every (claim, verdict) pair the verifier issues lands here, and stays.
There is no delete, no truncate, no in-place edit -- see spec/non_goals.md
("Post-hoc rewriting of a verdict. The audit ledger is append-only. A
superseded verdict gets a new verdict_id; the old one stays visible.").

# AUDIT-DECISION: this module never opens the ledger file in a truncating
# mode. Every `os.open` call below passes `O_CREAT | O_APPEND` and never
# `O_TRUNC`; every stdlib `open()` call uses mode "r" (read) or is avoided
# in favor of `os.open`. There is intentionally no method on `AuditLedger`
# that can shrink or rewrite the file.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

from .entry import LedgerEntry
from .errors import AuditError
from .hashing import compute_verdict_id

try:
    import fcntl

    _HAS_FCNTL = True
except ImportError:  # pragma: no cover - exercised only on Windows
    fcntl = None  # type: ignore[assignment]
    _HAS_FCNTL = False


class _AppendLock:
    """Exclusive lock guarding the append critical section of one ledger file.

    # AUDIT-DECISION: on POSIX, use `fcntl.flock(fd, LOCK_EX)` on the
    # ledger's own file descriptor -- released in `finally` via
    # `LOCK_UN`, so a raised exception (including `AuditError` for a
    # duplicate id) never leaves the file locked.
    #
    # # AUDIT-DECISION: `fcntl` doesn't exist on Windows. There, fall back
    # to a sidecar lockfile (`<ledger>.jsonl.lock`) created with
    # `os.open(..., O_CREAT | O_EXCL)`: the first process to successfully
    # create that file holds the lock; it deletes the file to release.
    # This is advisory, like flock -- it only serializes cooperating
    # `AuditLedger` instances/processes, not arbitrary other writers to
    # the ledger path -- which matches flock's own semantics, so behavior
    # is consistent across platforms even though the mechanism differs.
    """

    _POLL_INTERVAL_S = 0.005

    def __init__(self, ledger_path: Path, fd: int) -> None:
        self._fd = fd
        self._lockfile_path = ledger_path.with_name(ledger_path.name + ".lock")
        self._holding_fallback = False

    def __enter__(self) -> "_AppendLock":
        if _HAS_FCNTL:
            fcntl.flock(self._fd, fcntl.LOCK_EX)
        else:
            self._acquire_fallback()
        return self

    def __exit__(self, *exc_info: object) -> None:
        if _HAS_FCNTL:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
        else:
            self._release_fallback()

    def _acquire_fallback(self) -> None:
        while True:
            try:
                lock_fd = os.open(str(self._lockfile_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(lock_fd)
                self._holding_fallback = True
                return
            except FileExistsError:
                time.sleep(self._POLL_INTERVAL_S)

    def _release_fallback(self) -> None:
        if not self._holding_fallback:
            return
        try:
            os.remove(str(self._lockfile_path))
        finally:
            self._holding_fallback = False


class AuditLedger:
    """Append-only, tamper-evident ledger of (claim, verdict) pairs.

    Backed by a `.jsonl` file: one `LedgerEntry` per line, in issue order.
    `append` is the only mutating operation this class exposes.
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        # Create the file if missing; never truncate an existing one.
        fd = os.open(str(self.path), os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o644)
        os.close(fd)

    def append(self, claim: dict, verdict: dict) -> LedgerEntry:
        """Append one (claim, verdict) pair as a new ledger entry.

        Computes `verdict_id` via `compute_verdict_id(claim, verdict,
        verdict["snapshot_hashes"], verdict["checker_version"])`. If a
        verdict with that exact `verdict_id` already appears in the
        ledger, raises `AuditError("DUPLICATE_VERDICT_ID", ...)` and
        writes nothing. A superseding verdict is a normal `append` call
        whose `verdict` dict carries a different `supersedes` field (or
        differs in any other way) -- since that changes the hashed tuple,
        it naturally gets a new `verdict_id` and is accepted; the prior
        entry is untouched and still returned by `find_by_claim_id`.

        Every successful write is followed by `flush`-equivalent
        (`os.write` on an unbuffered fd) + `os.fsync`, before the file
        descriptor is closed and the lock released, so a crash
        immediately after `append()` returns cannot silently lose the
        write.
        """
        snapshot_hashes = verdict.get("snapshot_hashes", {})
        checker_version = verdict.get("checker_version", "")
        verdict_id = compute_verdict_id(claim, verdict, snapshot_hashes, checker_version)
        claim_id = claim.get("claim_id", "")
        issued_at = _now_iso8601_utc()

        entry = LedgerEntry(
            verdict_id=verdict_id,
            claim_id=claim_id,
            issued_at=issued_at,
            claim=claim,
            verdict=verdict,
        )
        line = entry.write_line()

        fd = os.open(str(self.path), os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o644)
        try:
            with _AppendLock(self.path, fd):
                # Duplicate check happens *inside* the lock so two
                # concurrent writers can't both pass the check for the
                # same verdict_id and then both append it.
                if self._contains_verdict_id(verdict_id):
                    raise AuditError(
                        "DUPLICATE_VERDICT_ID",
                        "a verdict with this verdict_id is already in the ledger",
                        verdict_id=verdict_id,
                    )
                os.write(fd, (line + "\n").encode("utf-8"))
                os.fsync(fd)
        finally:
            os.close(fd)

        return entry

    def iter_entries(self) -> Iterator[LedgerEntry]:
        """Stream ledger entries in file (issue) order. Read-only."""
        if not self.path.exists():
            return
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                yield LedgerEntry.from_line(line)

    def find_by_claim_id(self, claim_id: str) -> list[LedgerEntry]:
        """Return every verdict ever issued for `claim_id`, in issue order.

        A claim may have more than one entry if a later verdict
        supersedes an earlier one (see spec/non_goals.md); both stay
        visible here, oldest first.
        """
        return [entry for entry in self.iter_entries() if entry.claim_id == claim_id]

    def verify_integrity(self) -> None:
        """Re-parse and re-hash every line; raise on any mismatch.

        For each line: re-parses it into a `LedgerEntry` (a JSON decode
        failure or missing/malformed field raises `AuditError`
        `"LEDGER_TAMPERED"` immediately), then recomputes `verdict_id`
        from the stored `claim`/`verdict` and compares it to the stored
        `verdict_id`. Any mismatch -- from hand-editing a single character
        of the line -- raises `AuditError("LEDGER_TAMPERED", line=n, ...)`
        with the 1-indexed line number.
        """
        if not self.path.exists():
            return
        with open(self.path, "r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, start=1):
                text = raw.rstrip("\n")
                if not text:
                    continue
                try:
                    entry = LedgerEntry.from_line(text)
                except (json.JSONDecodeError, KeyError, TypeError) as exc:
                    raise AuditError(
                        "LEDGER_TAMPERED",
                        f"line {lineno} could not be parsed as a ledger entry: {exc}",
                        line=lineno,
                    ) from exc

                snapshot_hashes = entry.verdict.get("snapshot_hashes", {})
                checker_version = entry.verdict.get("checker_version", "")
                recomputed = compute_verdict_id(
                    entry.claim, entry.verdict, snapshot_hashes, checker_version
                )
                if recomputed != entry.verdict_id:
                    raise AuditError(
                        "LEDGER_TAMPERED",
                        "recomputed verdict_id does not match the stored verdict_id",
                        line=lineno,
                        stored_verdict_id=entry.verdict_id,
                        recomputed_verdict_id=recomputed,
                    )

    def _contains_verdict_id(self, verdict_id: str) -> bool:
        # AUDIT-DECISION: O(n) scan over the whole ledger on every append.
        # Simple and correct, and this module has no external dependency
        # to build an index with; at the scale of a single verifier run's
        # ledger this is not a bottleneck. Revisit if the ledger grows
        # large enough for this to matter (e.g. maintain a sidecar index),
        # but that's a performance change, not a correctness one.
        for entry in self.iter_entries():
            if entry.verdict_id == verdict_id:
                return True
        return False


def _now_iso8601_utc() -> str:
    """Current time as ISO 8601 UTC with millisecond precision and a `Z` suffix."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
