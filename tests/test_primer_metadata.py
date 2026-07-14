from __future__ import annotations

import unittest

from scripts.check_primer_metadata import PRIMERS, check


class PrimerMetadataTests(unittest.TestCase):
    def test_all_primers_have_matching_html_and_pdf_titles(self) -> None:
        errors = check()
        self.assertEqual(errors, [], "\n".join(errors))

    def test_expected_title_inventory_is_complete(self) -> None:
        self.assertEqual(len(PRIMERS), 6)
        self.assertIn("mathematics_of_constraint_primer", PRIMERS)
        self.assertIn("science_of_the_program_primer", PRIMERS)


if __name__ == "__main__":
    unittest.main()
