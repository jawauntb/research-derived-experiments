from __future__ import annotations

import importlib.util
import json
import stat
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[2] / "private" / "apollo_discovery.py"
TRACKED_SUMMARY_PATH = (
    Path(__file__).parents[2]
    / "experiments"
    / "evidence_worlds"
    / "results"
    / "buyer_discovery_summary.json"
)
SPEC = importlib.util.spec_from_file_location("apollo_discovery", MODULE_PATH)
assert SPEC and SPEC.loader
apollo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(apollo)


def test_post_rejects_non_search_endpoint() -> None:
    with pytest.raises(apollo.ApolloDiscoveryError, match="not read-allowlisted"):
        apollo._post_json("/contacts", {}, api_key="test")


def test_post_refuses_redirect_without_forwarding_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: list[str | None] = []

    class TargetHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            received.append(self.headers.get("x-api-key"))
            self.send_response(200)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return

    target = ThreadingHTTPServer(("127.0.0.1", 0), TargetHandler)

    class RedirectHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            self.send_response(302)
            self.send_header(
                "Location", f"http://127.0.0.1:{target.server_port}/stolen"
            )
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return

    redirect = ThreadingHTTPServer(("127.0.0.1", 0), RedirectHandler)
    threads = [
        threading.Thread(target=server.serve_forever, daemon=True)
        for server in (target, redirect)
    ]
    for thread in threads:
        thread.start()
    monkeypatch.setattr(
        apollo, "APOLLO_BASE_URL", f"http://127.0.0.1:{redirect.server_port}"
    )
    try:
        with pytest.raises(apollo.ApolloDiscoveryError, match="redirect refused"):
            apollo._post_json(apollo.ORGANIZATION_SEARCH_PATH, {}, api_key="test")
        assert received == []
    finally:
        redirect.shutdown()
        target.shutdown()
        redirect.server_close()
        target.server_close()


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


def test_bounded_run_rejects_output_outside_explicit_private_root(
    tmp_path: Path,
) -> None:
    with pytest.raises(apollo.ApolloDiscoveryError, match="private root"):
        apollo.run_bounded_discovery(
            tmp_path / "outside",
            api_key="test",
            per_wedge=1,
            private_root=tmp_path / "allowed",
        )


def test_bounded_run_intercepts_organizations_then_deduped_role_search(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_organizations(**kwargs: object) -> dict[str, object]:
        calls.append(("organizations", kwargs))
        tags = kwargs["keyword_tags"]
        if "clinical trials" in tags:
            organizations = [
                {"id": "org-1", "name": "One", "primary_domain": "one.example"},
                {"id": "org-2", "name": "Two", "primary_domain": "two.example"},
            ]
        else:
            organizations = [
                {
                    "id": "org-1",
                    "name": "One duplicate",
                    "primary_domain": "one.example",
                },
            ]
        return {"organizations": organizations}

    def fake_people(**kwargs: object) -> dict[str, object]:
        calls.append(("people", kwargs))
        return {
            "people": [{"id": "person-1"}, {"id": "person-2"}],
            "pagination": {"total_entries": 99},
        }

    monkeypatch.setattr(apollo, "search_organizations", fake_organizations)
    monkeypatch.setattr(apollo, "search_role_categories", fake_people)
    output_root = tmp_path / "private"
    summary = apollo.run_bounded_discovery(
        output_root / "run",
        api_key="test",
        per_wedge=2,
        private_root=output_root,
    )

    assert [kind for kind, _ in calls] == [
        "organizations",
        "organizations",
        "organizations",
        "people",
    ]
    people_call = calls[-1][1]
    assert people_call["organization_ids"] == ["org-1", "org-2"]
    assert people_call["titles"] == apollo.ROLE_CATEGORIES
    assert summary["account_count"] == 2
    assert summary["organization_count_queried_for_roles"] == 2
    assert summary["role_candidate_count"] == 2
    assert (output_root / "run" / "raw" / "role_categories.json").exists()
    assert (output_root / "run" / "private_accounts.json").exists()
    assert (output_root / "run" / "aggregate_summary.json").exists()


def test_tracked_summary_is_aggregate_and_public_safe() -> None:
    summary = json.loads(TRACKED_SUMMARY_PATH.read_text(encoding="utf-8"))

    apollo.assert_public_safe(summary)
    assert summary["account_count"] == 15
    assert summary["role_candidate_count"] == 25
    assert summary["outreach_performed"] is False
    assert summary["person_level_data_included"] is False
