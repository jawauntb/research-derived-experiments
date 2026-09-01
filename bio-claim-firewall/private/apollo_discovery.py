#!/usr/bin/env python3
"""Read-only Apollo discovery for private Bio Claim Firewall pilot research.

Raw responses and account candidates are local artifacts. This module never
enriches contact details, writes to Apollo, or sends outreach.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterable


APOLLO_BASE_URL = "https://api.apollo.io/api/v1"
ORGANIZATION_SEARCH_PATH = "/mixed_companies/search"
PEOPLE_SEARCH_PATH = "/mixed_people/api_search"
ALLOWED_POST_PATHS = frozenset({ORGANIZATION_SEARCH_PATH, PEOPLE_SEARCH_PATH})
PROHIBITED_PUBLIC_FIELDS = frozenset(
    {
        "apollo_id",
        "email",
        "first_name",
        "last_name",
        "linkedin_url",
        "name",
        "organization_id",
        "phone",
        "profile_url",
        "title",
    }
)


class ApolloDiscoveryError(RuntimeError):
    """Raised when a bounded read-only Apollo request cannot complete."""


def _secure_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def _post_json(
    path: str,
    payload: dict[str, Any],
    *,
    api_key: str,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    if path not in ALLOWED_POST_PATHS:
        raise ApolloDiscoveryError(f"Apollo path is not read-allowlisted: {path}")
    if not api_key:
        raise ApolloDiscoveryError("APOLLO_API_KEY is required")

    request = urllib.request.Request(
        f"{APOLLO_BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            value = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ApolloDiscoveryError(f"Apollo request failed with HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ApolloDiscoveryError(f"Apollo request failed: {type(exc).__name__}") from None

    if not isinstance(value, dict):
        raise ApolloDiscoveryError("Apollo response was not a JSON object")
    return value


def search_organizations(
    *,
    keyword_tags: Iterable[str],
    employee_ranges: Iterable[str] = ("51,200", "201,500", "501,1000", "1001,5000"),
    locations: Iterable[str] = ("United States",),
    page: int = 1,
    per_page: int = 10,
    api_key: str,
) -> dict[str, Any]:
    if not 1 <= per_page <= 100:
        raise ValueError("per_page must be between 1 and 100")
    if page < 1:
        raise ValueError("page must be positive")
    payload = {
        "q_organization_keyword_tags": list(keyword_tags),
        "organization_num_employees_ranges": list(employee_ranges),
        "organization_locations": list(locations),
        "page": page,
        "per_page": per_page,
    }
    return _post_json(ORGANIZATION_SEARCH_PATH, payload, api_key=api_key)


def search_role_categories(
    *,
    organization_ids: Iterable[str],
    titles: Iterable[str],
    page: int = 1,
    per_page: int = 10,
    api_key: str,
) -> dict[str, Any]:
    """Return masked role candidates; never request email/phone enrichment."""

    if not 1 <= per_page <= 100:
        raise ValueError("per_page must be between 1 and 100")
    payload = {
        "organization_ids": list(organization_ids),
        "person_titles": list(titles),
        "include_similar_titles": True,
        "page": page,
        "per_page": per_page,
    }
    return _post_json(PEOPLE_SEARCH_PATH, payload, api_key=api_key)


def _organizations(response: dict[str, Any]) -> list[dict[str, Any]]:
    value = response.get("organizations", [])
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def private_account_rows(response: dict[str, Any], *, wedge: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for organization in _organizations(response):
        domain = organization.get("primary_domain") or organization.get("website_url")
        rows.append(
            {
                "wedge": wedge,
                "organization_id": organization.get("id"),
                "name": organization.get("name"),
                "domain": domain,
                "industry": organization.get("industry"),
                "employee_count": organization.get("estimated_num_employees"),
                "city": organization.get("city"),
                "state": organization.get("state"),
                "country": organization.get("country"),
            }
        )
    return rows


def aggregate_summary(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    materialized = list(rows)
    wedges: dict[str, int] = {}
    with_domain = 0
    for row in materialized:
        wedge = str(row.get("wedge") or "unknown")
        wedges[wedge] = wedges.get(wedge, 0) + 1
        if row.get("domain"):
            with_domain += 1
    return {
        "account_count": len(materialized),
        "accounts_with_domain": with_domain,
        "counts_by_wedge": dict(sorted(wedges.items())),
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


def assert_public_safe(payload: Any, *, path: str = "$") -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            normalized = key.casefold()
            if normalized in PROHIBITED_PUBLIC_FIELDS:
                raise ApolloDiscoveryError(f"prohibited public field at {path}.{key}")
            if "api_key" in normalized or "token" in normalized:
                raise ApolloDiscoveryError(f"secret-like public field at {path}.{key}")
            assert_public_safe(value, path=f"{path}.{key}")
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            assert_public_safe(value, path=f"{path}[{index}]")


DEFAULT_WEDGES = {
    "clinical-trial-diligence": ["biotechnology", "clinical trials"],
    "target-validation": ["drug discovery", "computational biology"],
    "virtual-cell-platforms": ["single cell", "functional genomics"],
}


def run_bounded_discovery(output_dir: Path, *, api_key: str, per_wedge: int) -> dict[str, Any]:
    all_rows: list[dict[str, Any]] = []
    raw_dir = output_dir / "raw"
    for wedge, tags in DEFAULT_WEDGES.items():
        response = search_organizations(keyword_tags=tags, per_page=per_wedge, api_key=api_key)
        _secure_write_json(raw_dir / f"{wedge}.json", response)
        all_rows.extend(private_account_rows(response, wedge=wedge))

    _secure_write_json(output_dir / "private_accounts.json", all_rows)
    summary = aggregate_summary(all_rows)
    assert_public_safe(summary)
    _secure_write_json(output_dir / "aggregate_summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("deepline/data/bio-claim-firewall-buyers"),
    )
    parser.add_argument("--per-wedge", type=int, default=5)
    args = parser.parse_args()
    if not 1 <= args.per_wedge <= 25:
        parser.error("--per-wedge must be between 1 and 25")
    summary = run_bounded_discovery(
        args.output_dir,
        api_key=os.environ.get("APOLLO_API_KEY", ""),
        per_wedge=args.per_wedge,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
