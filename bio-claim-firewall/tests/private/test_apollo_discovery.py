from __future__ import annotations

import importlib.util
import json
import stat
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).parents[2] / "private" / "apollo_discovery.py"
SPEC = importlib.util.spec_from_file_location("apollo_discovery", MODULE_PATH)
assert SPEC and SPEC.loader
apollo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(apollo)


def test_post_rejects_non_search_endpoint() -> None:
    with pytest.raises(apollo.ApolloDiscoveryError, match="not read-allowlisted"):
        apollo._post_json("/contacts", {}, api_key="test")


def test_private_rows_are_aggregated_without_identity_fields() -> None:
    response = {
        "organizations": [
            {
                "id": "org-1",
                "name": "Example Bio",
                "primary_domain": "example.bio",
                "industry": "biotechnology",
                "estimated_num_employees": 100,
            }
        ]
    }
    rows = apollo.private_account_rows(response, wedge="clinical-trial-diligence")
    summary = apollo.aggregate_summary(rows)

    assert rows[0]["organization_id"] == "org-1"
    assert summary == {
        "account_count": 1,
        "accounts_with_domain": 1,
        "counts_by_wedge": {"clinical-trial-diligence": 1},
        "role_categories": [
            "clinical intelligence",
            "computational biology",
            "scientific diligence",
            "scientific platform",
            "translational informatics",
        ],
        "outreach_performed": False,
        "person_level_data_included": False,
    }
    apollo.assert_public_safe(summary)


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "person@example.com"},
        {"nested": {"linkedin_url": "https://linkedin.com/in/person"}},
        {"rows": [{"first_name": "A"}]},
        {"api_key": "secret"},
    ],
)
def test_public_safe_rejects_person_and_secret_fields(payload: object) -> None:
    with pytest.raises(apollo.ApolloDiscoveryError):
        apollo.assert_public_safe(payload)


def test_secure_write_uses_owner_only_permissions(tmp_path: Path) -> None:
    target = tmp_path / "private" / "result.json"
    apollo._secure_write_json(target, {"ok": True})

    assert json.loads(target.read_text()) == {"ok": True}
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
