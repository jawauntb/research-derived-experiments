"""A single-file advisory lock shared by the daemon and the nightly pass.

The nightly pass rewrites a day's file wholesale; the daemon appends to it.
Without a lock, a summary written at 23:30 can drop a note spoken at 23:30:00.5.
``flock`` is enough here: both writers are on the same machine, and the lock is
advisory between our own processes only.
"""

from __future__ import annotations

import contextlib
import logging
from collections.abc import Iterator
from pathlib import Path

log = logging.getLogger(__name__)

__all__ = ["notes_lock", "LOCK_NAME"]

LOCK_NAME = ".gazenotes.lock"


@contextlib.contextmanager
def notes_lock(notes_dir: Path | str, *, blocking: bool = True) -> Iterator[bool]:
    """Hold the notes-directory lock for the duration of the block.

    Yields ``True`` when the lock was taken. On a platform without ``fcntl``,
    or when the lock file cannot be created, it yields ``True`` and proceeds:
    an unavailable lock must not stop the user's note from being written.
    """
    try:
        import fcntl
    except ImportError:  # pragma: no cover - non-POSIX
        yield True
        return

    directory = Path(notes_dir).expanduser()
    try:
        directory.mkdir(parents=True, exist_ok=True)
        handle = open(directory / LOCK_NAME, "w")  # noqa: SIM115 - closed below
    except OSError as exc:
        log.debug("could not open lock file: %s", exc)
        yield True
        return

    acquired = False
    try:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except OSError:
            log.debug("notes lock is held by another process")
        yield acquired
    finally:
        if acquired:
            with contextlib.suppress(OSError):
                fcntl.flock(handle, fcntl.LOCK_UN)
        handle.close()


def lock_is_free(notes_dir: Path | str) -> bool:
    """Whether the lock could be taken right now (used by ``doctor``)."""
    with notes_lock(notes_dir, blocking=False) as acquired:
        return acquired
