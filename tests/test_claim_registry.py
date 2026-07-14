from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.validate_claim_registry import validate


class ClaimRegistryTests(unittest.TestCase):
    def test_committed_claims_reference_known_evidence(self) -> None:
        payload = validate()
        self.assertEqual(len(payload["claims"]), 6)

    def test_unknown_evidence_fails_closed(self) -> None:
        claims = json.loads(Path("docs/claim_registry.json").read_text())
        claims["claims"][0]["evidence_ids"] = ["EVID-DOES-NOT-EXIST"]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "claims.json"
            path.write_text(json.dumps(claims))
            with self.assertRaisesRegex(ValueError, "unknown evidence"):
                validate(path)


if __name__ == "__main__":
    unittest.main()
