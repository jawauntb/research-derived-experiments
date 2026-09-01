#!/usr/bin/env python3
"""Build a compact ClinicalTrials.gov/SEC identity-consistency fixture.

The bounded pilot uses TransCode Therapeutics' June 3, 2026 8-K exhibit and
NCT06260774. Raw registry JSON and filing HTML remain outside git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from worlds.clinical_trials.adapter import load_fixture

WORLD_VERSION = "2025-09-01_2026-09-01"
NCT_ID = "NCT06260774"
SPONSOR = "TransCode Therapeutics"
INTERVENTION = "TTX-MC138"
CIK = "0001829635"
ACCESSION = "0001104659-26-069810"
SEC_ACCEPTED_AT = "2026-06-03T08:08:44Z"
CT_ACCEPTED_AT = "2025-10-02T00:00:00Z"
EXHIBIT_LOCATOR = "EX-99.1#NCT06260774"
SPAN_LOCATOR = "EX-99.1:sentence[NCT06260774]"
ASSERTED_SPAN = (
    "Further information about the trial is available at www.clinicaltrials.gov , "
    "(NCT Identifier: NCT06260774)."
)


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _html_text(path: Path) -> str:
    parser = _Text()
    parser.feed(path.read_text(encoding="utf-8", errors="strict"))
    return " ".join(" ".join(parser.parts).split())


def build(ct_source: Path, sec_source: Path, destination: Path) -> dict[str, object]:
    ct_raw = ct_source.read_bytes()
    sec_raw = sec_source.read_bytes()
    study = json.loads(ct_raw).get("protocolSection", {})
    identity = study.get("identificationModule", {})
    status = study.get("statusModule", {})
    sponsor = study.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {})
    interventions = study.get("armsInterventionsModule", {}).get("interventions", [])
    names = {row.get("name") for row in interventions if isinstance(row, dict)}
    if identity.get("nctId") != NCT_ID or sponsor.get("name") != SPONSOR or INTERVENTION not in names:
        raise ValueError("ClinicalTrials.gov identity does not match the preregistered trial")
    if status.get("lastUpdatePostDateStruct", {}).get("date") != "2025-10-02":
        raise ValueError("ClinicalTrials.gov data clock changed")
    filing_text = _html_text(sec_source)
    if ASSERTED_SPAN not in filing_text or INTERVENTION not in filing_text or SPONSOR not in filing_text:
        raise ValueError("human-confirmed SEC identity span or context disappeared")
    span_hash = hashlib.sha256(ASSERTED_SPAN.encode()).hexdigest()
    records = [
        {
            "record_id": f"ctgov:{NCT_ID}:2025-10-02",
            "source": "clinicaltrials-gov-api-v2",
            "nct_id": NCT_ID,
            "sponsor": SPONSOR,
            "intervention": INTERVENTION,
            "accepted_at": CT_ACCEPTED_AT,
            "status": status.get("overallStatus"),
        },
        {
            "record_id": f"sec:{ACCESSION}:EX-99.1:NCT06260774",
            "source": "sec-edgar-submissions-and-archives",
            "nct_id": NCT_ID,
            "cik": CIK,
            "sponsor": SPONSOR,
            "intervention": INTERVENTION,
            "sec_accession": ACCESSION,
            "exhibit_locator": EXHIBIT_LOCATOR,
            "span_locator": SPAN_LOCATOR,
            "asserted_span_sha256": span_hash,
            "human_confirmed": True,
            "accepted_at": SEC_ACCEPTED_AT,
        },
    ]
    fixture: dict[str, object] = {
        "schema_version": "clinical-trials-sec-ledger-0.1",
        "world_id": "clinical-trials-sec",
        "version": WORLD_VERSION,
        "source_hashes": {
            "clinicaltrials-gov-api-v2": hashlib.sha256(ct_raw).hexdigest(),
            "sec-edgar-submissions-and-archives": hashlib.sha256(sec_raw).hexdigest(),
        },
        "records": records,
        "provenance": {
            "clinicaltrials_url": f"https://clinicaltrials.gov/api/v2/studies/{NCT_ID}",
            "sec_url": "https://www.sec.gov/Archives/edgar/data/1829635/000110465926069810/tm2616719d1_ex99-1.htm",
            "sec_filing_accepted_at": SEC_ACCEPTED_AT,
            "window_start": "2025-09-01T00:00:00Z",
            "window_end": "2026-09-01T23:59:59Z",
            "raw_sources_committed": False,
        },
    }
    integrity_payload = {key: fixture[key] for key in ("schema_version", "world_id", "version", "source_hashes", "records")}
    fixture["integrity_sha256"] = _digest(integrity_payload)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    load_fixture(destination)
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--clinicaltrials-source", required=True, type=Path)
    parser.add_argument("--sec-source", required=True, type=Path)
    args = parser.parse_args()
    fixture = build(args.clinicaltrials_source, args.sec_source, args.destination)
    print(json.dumps({"record_count": len(fixture["records"]), "source_hashes": fixture["source_hashes"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
