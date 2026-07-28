from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.build_obstruction_aware_admission_pdf import build_pdf


class ObstructionAwareAdmissionPdfTests(unittest.TestCase):
    def test_builds_parseable_scoped_paper_with_exact_results(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "paper.pdf"
            text_path = Path(directory) / "paper.txt"
            build_pdf(output_pdf=output, copy_pdf=None)
            info = subprocess.run(
                ["pdfinfo", str(output)],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            subprocess.run(
                ["pdftotext", str(output), str(text_path)],
                check=True,
            )
            text = text_path.read_text(encoding="utf-8")
            size = output.stat().st_size
            pages = int(
                next(
                    line.split(":", 1)[1]
                    for line in info.splitlines()
                    if line.startswith("Pages:")
                )
            )

        self.assertGreaterEqual(pages, 14)
        self.assertGreater(size, 150_000)
        self.assertIn("Obstruction-Aware Admission", text)
        self.assertIn("500,912", text)
        self.assertIn("26,304", text)
        self.assertIn("terminal obstruction", text.lower())
        self.assertIn("optimal decision-tree mathematics is not", text)
        self.assertIn("References", text)


if __name__ == "__main__":
    unittest.main()
