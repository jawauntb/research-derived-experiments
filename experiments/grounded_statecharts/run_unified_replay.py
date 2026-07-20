"""Render the fixture-only public failure replay from committed result rows."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from experiments.grounded_statecharts.replay_viewer import (
    REQUIRED_SECTION_LABELS,
    render_unified_replay,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
SOURCE_DIR = PACKAGE_ROOT / "results"
DEFAULT_OUTPUT = SOURCE_DIR / "unified_replay"
SOURCE_FILES = ("summary.json", "original.jsonl", "guarded_replay.jsonl")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate_results(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    """Write a static replay using only existing public deterministic artifacts."""
    source_paths = {name: SOURCE_DIR / name for name in SOURCE_FILES}
    summary = _read_json(source_paths["summary.json"])
    original_events = _read_jsonl(source_paths["original.jsonl"])
    guarded_events = _read_jsonl(source_paths["guarded_replay.jsonl"])

    if not original_events or not guarded_events:
        raise RuntimeError("paired replay rows must not be empty")
    if not all(summary["gates"].values()):
        raise RuntimeError("source fixture gates failed; refusing to render replay")

    output_dir.mkdir(parents=True, exist_ok=True)
    replay_summary: dict[str, Any] = {
        "fixture": summary["fixture"],
        "primary_run_id": summary["run_id"],
        "required_sections": list(REQUIRED_SECTION_LABELS),
        "source_digests": {name: _digest(path) for name, path in source_paths.items()},
    }
    (output_dir / "summary.json").write_text(
        json.dumps(replay_summary, indent=2, sort_keys=True) + "\n"
    )
    (output_dir / "replay.html").write_text(
        render_unified_replay(
            summary=summary,
            original_events=original_events,
            guarded_events=guarded_events,
        )
    )
    return replay_summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    summary = generate_results(args.out_dir)
    print(json.dumps({"out_dir": str(args.out_dir), **summary}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
