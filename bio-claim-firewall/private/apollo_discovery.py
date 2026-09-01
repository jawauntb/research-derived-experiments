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
from collections.abc import Iterable
from pathlib import Path
from typing import Any

APOLLO_BASE_URL = "https://api.apollo.io/api/v1"
ORGANIZATION_SEARCH_PATH = "/mixed_companies/search"
PEOPLE_SEARCH_PATH = "/mixed_people/api_search"
ALLOWED_POST_PATHS = frozenset({ORGANIZATION_SEARCH_PATH, PEOPLE_SEARCH_PATH})
PRIVATE_OUTPUT_ROOT = Path(__file__).resolve().parent / "artifacts" / "apollo_discovery"
ROLE_CATEGORIES = (
    "clinical intelligence",
    "computational biology",
    "scientific diligence",
    "scientific platform",
    "translational informatics",
)
ROLE_SEARCH_PAGE_SIZE = 25
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


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    """Never forward an authenticated Apollo request to another URL."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001, ARG002
        raise ApolloDiscoveryError(
            "Apollo redirect refused before forwarding credentials"
        )


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
        opener = urllib.request.build_opener(_RejectRedirects())
        with opener.open(request, timeout=timeout_seconds) as response:
            value = json.loads(response.read().decode("utf-8"))
    except ApolloDiscoveryError:
        raise
    except urllib.error.HTTPError as exc:
        raise ApolloDiscoveryError(
            f"Apollo request failed with HTTP {exc.code}"
        ) from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ApolloDiscoveryError(
            f"Apollo request failed: {type(exc).__name__}"
        ) from None

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
    if page < 1:
        raise ValueError("page must be positive")
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
    return (
        [item for item in value if isinstance(item, dict)]
        if isinstance(value, list)
        else []
    )


def _people(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Read Apollo's person candidates without projecting identity fields."""

    for key in ("people", "contacts"):
        value = response.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _people_count(response: dict[str, Any]) -> int:
    """Count candidates from the collection Apollo actually returned."""

    for key in ("people", "contacts"):
        value = response.get(key)
        if isinstance(value, list):
            return len([item for item in value if isinstance(item, dict)])
    pagination = response.get("pagination")
    if isinstance(pagination, dict) and isinstance(
        pagination.get("total_entries"), int
    ):
        return pagination["total_entries"]
    return 0


def private_account_rows(
    response: dict[str, Any], *, wedge: str
) -> list[dict[str, Any]]:
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
        "role_categories": list(ROLE_CATEGORIES),
        "outreach_performed": False,
        "person_level_data_included": False,
    }


def _deduplicate_account_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the first wedge assignment for each organization candidate."""

    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        organization_id = row.get("organization_id")
        if organization_id:
            key = f"id:{organization_id}"
        else:
            domain = row.get("domain")
            if not domain:
                # No stable identity means it cannot safely be deduplicated or
                # sent to a role query, so retain it as a private row only.
                result.append(row)
                continue
            key = f"domain:{str(domain).strip().casefold().rstrip('/')}"
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def _constrained_output_dir(output_dir: Path, *, private_root: Path) -> Path:
    root = private_root.resolve()
    candidate = output_dir.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise ApolloDiscoveryError(
            f"Apollo output must be under the private root {root}"
        ) from None
    return candidate


def _summary_with_role_counts(
    rows: Iterable[dict[str, Any]],
    *,
    role_response: dict[str, Any] | None,
    organization_ids: Iterable[str],
) -> dict[str, Any]:
    summary = aggregate_summary(rows)
    if role_response is not None:
        summary.update(
            {
                "organization_count_queried_for_roles": len(list(organization_ids)),
                "role_candidate_count": _people_count(role_response),
            }
        )
    return summary


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


def run_bounded_discovery(
    output_dir: Path | None = None,
    *,
    api_key: str,
    per_wedge: int,
    private_root: Path | None = None,
) -> dict[str, Any]:
    """Run bounded company and role searches, writing only private artifacts.

    ``private_root`` exists for isolated tests; production callers must use the
    module's explicit ``PRIVATE_OUTPUT_ROOT``.
    """

    if not 1 <= per_wedge <= 25:
        raise ValueError("per_wedge must be between 1 and 25")
    allowed_root = private_root or PRIVATE_OUTPUT_ROOT
    destination = _constrained_output_dir(
        output_dir or allowed_root, private_root=allowed_root
    )
    all_rows: list[dict[str, Any]] = []
    raw_dir = destination / "raw"
    for wedge, tags in DEFAULT_WEDGES.items():
        response = search_organizations(
            keyword_tags=tags, per_page=per_wedge, api_key=api_key
        )
        _secure_write_json(raw_dir / f"{wedge}.json", response)
        all_rows.extend(private_account_rows(response, wedge=wedge))

    all_rows = _deduplicate_account_rows(all_rows)
    organization_ids = list(
        dict.fromkeys(
            str(row["organization_id"])
            for row in all_rows
            if row.get("organization_id")
        )
    )
    role_response: dict[str, Any] | None = None
    if organization_ids:
        role_response = search_role_categories(
            organization_ids=organization_ids,
            titles=ROLE_CATEGORIES,
            per_page=ROLE_SEARCH_PAGE_SIZE,
            api_key=api_key,
        )
        _secure_write_json(raw_dir / "role_categories.json", role_response)

    _secure_write_json(destination / "private_accounts.json", all_rows)
    summary = _summary_with_role_counts(
        all_rows,
        role_response=role_response,
        organization_ids=organization_ids,
    )
    assert_public_safe(summary)
    _secure_write_json(destination / "aggregate_summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PRIVATE_OUTPUT_ROOT,
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
