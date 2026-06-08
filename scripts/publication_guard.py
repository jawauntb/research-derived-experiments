#!/usr/bin/env python3
"""Fail if tracked files look unsafe for a public research repository."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


MAX_TRACKED_FILE_BYTES = 10 * 1024 * 1024
FORBIDDEN_TRACKED_PREFIXES = (
    "references/papers/",
    "references/text/",
    "references/html/",
    "data/",
    "artifacts/",
)
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    re.compile(r"gh[opsu]_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?i)(api_key|token|secret)\s*=\s*['\"][^'\"\n]{12,}['\"]"),
)


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return [Path(line) for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    failures: list[str] = []
    for path in tracked_files():
        normalized = path.as_posix()
        if normalized.startswith(FORBIDDEN_TRACKED_PREFIXES):
            failures.append(f"forbidden tracked path: {normalized}")
            continue
        if path.exists() and path.stat().st_size > MAX_TRACKED_FILE_BYTES:
            failures.append(f"tracked file over 10 MB: {normalized}")
            continue
        if path.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"possible secret pattern in: {normalized}")
                break

    if failures:
        print("Publication guard failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Publication guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

