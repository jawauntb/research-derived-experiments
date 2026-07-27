"""DR6h snippets: exclusive-file-access commitment.

Target D_h: 'This code assumes exclusive access to files it reads or
writes — no other process, thread, or async task will read, write,
truncate, or delete those files concurrently.'

D_h has no clean implicit-vs-explicit correlate. Both correctly-locked
and dangerously-unlocked file access can look 'implicit' (no explicit
mention of concurrency) or 'explicit' (comments about locking, use of
lock managers). DR5* predicts the wall bites even for LLM verifiers
because no domain-general proxy discriminates realisations from placebos.
"""

from __future__ import annotations

from typing import Final

from experiments.dr6_code_correctness_corollary.snippets import Snippet


__all__ = ["SNIPPETS_H"]


SNIPPETS_H: Final[tuple[Snippet, ...]] = (
    # ------------------------------------------------------------------
    # Realisations of D_h — assumes exclusive access
    # ------------------------------------------------------------------
    Snippet(
        snippet_id="RH1_readmodifywrite",
        kind="realisation",
        surface_form="read-modify-write with no locking",
        code="""\
from pathlib import Path


def increment_counter(path: Path) -> int:
    current = int(path.read_text().strip() or '0')
    new = current + 1
    path.write_text(f'{new}\\n')
    return new
""",
    ),
    Snippet(
        snippet_id="RH2_seek_write",
        kind="realisation",
        surface_form="seek+write pattern, single handle",
        code="""\
def patch_offset(fd, offset: int, replacement: bytes) -> None:
    fd.seek(offset)
    old = fd.read(len(replacement))
    fd.seek(offset)
    fd.write(replacement)
    return old
""",
    ),
    Snippet(
        snippet_id="RH3_append_log",
        kind="realisation",
        surface_form="append to log without lock",
        code="""\
def audit_event(path, event: str) -> None:
    with open(path, 'a') as fd:
        fd.write(event + '\\n')
""",
    ),
    Snippet(
        snippet_id="RH4_rename_after_write",
        kind="realisation",
        surface_form="write-then-rename, no coordination",
        code="""\
import os
from pathlib import Path


def atomic_replace(final: Path, contents: str) -> None:
    tmp = final.with_suffix(final.suffix + '.tmp')
    tmp.write_text(contents)
    os.rename(tmp, final)
""",
    ),
    Snippet(
        snippet_id="RH5_json_load_modify_dump",
        kind="realisation",
        surface_form="load-modify-dump JSON file",
        code="""\
import json
from pathlib import Path


def add_entry(path: Path, key: str, value: object) -> None:
    data = json.loads(path.read_text())
    data[key] = value
    path.write_text(json.dumps(data, indent=2))
""",
    ),
    # ------------------------------------------------------------------
    # Placebos — do NOT assume exclusive access
    # ------------------------------------------------------------------
    Snippet(
        snippet_id="PH1_fcntl_lock",
        kind="placebo",
        surface_form="fcntl exclusive lock",
        code="""\
import fcntl


def increment_counter_locked(path: str) -> int:
    with open(path, 'r+') as fd:
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX)
        try:
            current = int(fd.read().strip() or '0')
            fd.seek(0)
            fd.truncate()
            fd.write(f'{current + 1}\\n')
            return current + 1
        finally:
            fcntl.flock(fd.fileno(), fcntl.LOCK_UN)
""",
    ),
    Snippet(
        snippet_id="PH2_filelock_library",
        kind="placebo",
        surface_form="filelock library, explicit",
        code="""\
from filelock import FileLock
from pathlib import Path


def append_line_safely(path: Path, line: str) -> None:
    lock = FileLock(str(path) + '.lock')
    with lock:
        with open(path, 'a') as fd:
            fd.write(line + '\\n')
""",
    ),
    Snippet(
        snippet_id="PH3_no_file_access",
        kind="placebo",
        surface_form="in-memory only, no file access",
        code="""\
def rolling_average(values: list[float], window: int) -> list[float]:
    output = []
    for i in range(len(values)):
        window_slice = values[max(0, i - window + 1):i + 1]
        output.append(sum(window_slice) / len(window_slice))
    return output
""",
    ),
    Snippet(
        snippet_id="PH4_read_only_open",
        kind="placebo",
        surface_form="read-only open, side-effect free",
        code="""\
from pathlib import Path


def word_count(path: Path) -> int:
    total = 0
    with open(path) as fd:
        for line in fd:
            total += len(line.split())
    return total
""",
    ),
    Snippet(
        snippet_id="PH5_lockfile_context",
        kind="placebo",
        surface_form="hand-rolled lockfile w/ retry",
        code="""\
import time
from pathlib import Path


def with_pidlock(pidlock: Path, timeout: float = 10.0):
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = open(pidlock, 'x')
            fd.write(str(9999))
            fd.close()
            return True
        except FileExistsError:
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.05)
""",
    ),
)
