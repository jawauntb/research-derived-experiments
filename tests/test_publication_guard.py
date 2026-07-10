from __future__ import annotations

import unittest

from scripts.publication_guard import contains_possible_secret


class PublicationGuardTests(unittest.TestCase):
    def test_detects_vendor_and_assignment_credentials(self) -> None:
        vendor_token = "sk-" + ("a" * 24)
        assignment = "api_" + "key = '" + ("b" * 16) + "'"

        self.assertTrue(contains_possible_secret(vendor_token))
        self.assertTrue(contains_possible_secret(assignment))

    def test_fixture_credential_names_do_not_trigger_assignment_pattern(self) -> None:
        fixture_source = (
            'const fixturePairingCredential = "fixture-pairing-secret";\n'
            'const fixtureTokenLabel = "paired-token";'
        )

        self.assertFalse(contains_possible_secret(fixture_source))


if __name__ == "__main__":
    unittest.main()
