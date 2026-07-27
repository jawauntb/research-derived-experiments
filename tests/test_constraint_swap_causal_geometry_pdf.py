from __future__ import annotations

import tempfile
import unittest
import subprocess
from pathlib import Path

from scripts.build_constraint_swap_causal_geometry_pdf import build_pdf
from scripts.make_constraint_swap_causal_geometry_figures import main as make_figures


class ConstraintSwapPaperPdfTests(unittest.TestCase):
    def test_builds_parseable_paper_with_equations_results_and_references(self) -> None:
        make_figures()
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
                next(line.split(":", 1)[1] for line in info.splitlines() if line.startswith("Pages:"))
            )

        self.assertGreaterEqual(pages, 8)
        self.assertGreater(size, 50_000)
        self.assertIn("Constraint Is Not Geometry", text)
        self.assertIn("reject", text.lower())
        self.assertIn("d_reach", text)
        self.assertIn("References", text)


if __name__ == "__main__":
    unittest.main()
