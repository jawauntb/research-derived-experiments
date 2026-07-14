#!/usr/bin/env python3
"""Check that each primer identifies itself consistently in HTML and PDF metadata."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIMERS = {
    "history_lineage_and_trajectory_primer": "The Lineage and the Trajectory",
    "mathematics_of_constraint_primer": "The Mathematics of Constraint",
    "philosophy_what_it_means_primer": "What It All Means",
    "science_of_the_program_primer": "How This Knowledge Is Made",
    "software_engineering_primer": "The Instrument",
    "systems_theory_complexity_primer": "Systems That Hold Themselves Together",
}


def pdf_title(path: Path) -> str:
    try:
        completed = subprocess.run(
            ["pdfinfo", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"could not inspect PDF metadata for {path}: {exc}") from exc
    for line in completed.stdout.splitlines():
        if line.startswith("Title:"):
            return line.split(":", 1)[1].strip()
    return ""


def check(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for stem, expected in PRIMERS.items():
        html = root / "docs" / "primers" / f"{stem}.html"
        pdf = root / "docs" / "primers" / f"{stem}.pdf"
        text = html.read_text(errors="replace") if html.exists() else ""
        match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        actual_html = re.sub(r"\s+", " ", match.group(1)).strip() if match else ""
        if actual_html != expected and not actual_html.startswith(expected + " —"):
            errors.append(f"{html.relative_to(root)} title={actual_html!r}; expected {expected!r}")
        if not pdf.exists():
            errors.append(f"missing PDF: {pdf.relative_to(root)}")
        else:
            actual_pdf = pdf_title(pdf)
            if actual_pdf != expected:
                errors.append(f"{pdf.relative_to(root)} metadata={actual_pdf!r}; expected {expected!r}")
    return errors


def main() -> int:
    errors = check()
    if errors:
        print("[primer-metadata] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"[primer-metadata] PASS: {len(PRIMERS)} HTML/PDF pairs agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
