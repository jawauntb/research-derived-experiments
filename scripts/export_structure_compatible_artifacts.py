#!/usr/bin/env python3
"""Export structure-compatible generalization artifacts to the local archive."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


DEFAULT_DEST = Path(
    "/Users/jawaun/Metaphysics of Intelligence/"
    "Structure_Compatible_Generalization_2026_07_06"
)


def source_files() -> list[Path]:
    files = [
        Path("papers/structure_compatible_generalization/paper.md"),
        Path("papers/structure_compatible_generalization/paper.pdf"),
        Path(
            "experiments/structure_compatible_generalization/results/"
            "structure_compatible_l4_2026_07_06.md"
        ),
    ]
    figure_dir = Path("papers/structure_compatible_generalization/figures")
    if figure_dir.exists():
        files.extend(sorted(figure_dir.glob("*.png")))
    return files


def export(dest: Path, *, dry_run: bool) -> list[Path]:
    files = source_files()
    missing = [path for path in files[:3] if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required artifacts: " + ", ".join(str(path) for path in missing)
        )
    copied: list[Path] = []
    for src in files:
        if not src.exists():
            continue
        target = dest / src.name
        copied.append(target)
        if dry_run:
            continue
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    return copied


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    copied = export(args.dest, dry_run=args.dry_run)
    verb = "Would copy" if args.dry_run else "Copied"
    print(f"{verb} {len(copied)} artifacts to {args.dest}")
    for path in copied:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

