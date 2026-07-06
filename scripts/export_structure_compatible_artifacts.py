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


def paper_pdfs() -> list[Path]:
    return [
        Path(
            "papers/structure_compatible_generalization/"
            "structure_compatible_generalization.pdf"
        ),
        Path(
            "papers/structure_compatible_generalization/"
            "inferred_transformations_intervention.pdf"
        ),
        Path(
            "papers/structure_compatible_generalization/"
            "learned_generators_transfer.pdf"
        ),
    ]


def source_files(*, include_supporting: bool) -> list[Path]:
    files = paper_pdfs()
    if not include_supporting:
        return files
    files.extend(
        [
            Path(
                "papers/structure_compatible_generalization/"
                "structure_compatible_generalization.md"
            ),
            Path(
                "experiments/structure_compatible_generalization/results/"
                "structure_compatible_l4_2026_07_06.md"
            ),
            Path(
                "papers/structure_compatible_generalization/"
                "inferred_transformations_intervention.md"
            ),
            Path(
                "experiments/structure_compatible_generalization/results/"
                "phase2_transformations_2026_07_06.md"
            ),
            Path(
                "papers/structure_compatible_generalization/"
                "learned_generators_transfer.md"
            ),
            Path(
                "experiments/structure_compatible_generalization/results/"
                "phase3_learned_generators_2026_07_06.md"
            ),
        ]
    )
    figure_dir = Path("papers/structure_compatible_generalization/figures")
    if figure_dir.exists():
        files.extend(sorted(figure_dir.glob("*.png")))
    return files


def export(
    dest: Path,
    *,
    dry_run: bool,
    include_supporting: bool,
    clean: bool,
) -> list[Path]:
    files = source_files(include_supporting=include_supporting)
    required = [path for path in files if path.suffix == ".pdf"]
    missing = [path for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required artifacts: " + ", ".join(str(path) for path in missing)
        )
    if clean and not dry_run and dest.exists():
        keep_names = {path.name for path in files}
        for child in dest.iterdir():
            if child.is_file() and child.name not in keep_names:
                child.unlink()
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
    parser.add_argument(
        "--include-supporting",
        action="store_true",
        help="Also copy markdown reports and figures. Default copies paper PDFs only.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove files in the destination that are not part of this export set.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    copied = export(
        args.dest,
        dry_run=args.dry_run,
        include_supporting=args.include_supporting,
        clean=args.clean,
    )
    verb = "Would copy" if args.dry_run else "Copied"
    print(f"{verb} {len(copied)} artifacts to {args.dest}")
    for path in copied:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
