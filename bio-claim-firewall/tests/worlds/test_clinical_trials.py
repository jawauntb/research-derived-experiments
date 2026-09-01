from __future__ import annotations

import json
from pathlib import Path

from worlds.clinical_trials import (
    ClinicalTrialsAdapter,
    OutcomeKind,
    check_clinical_trials_claim,
)

FIXTURE = Path(__file__).parents[1] / "fixtures" / "worlds" / "clinical_trials" / "fixture.json"


def _claim(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "nct_id": "NCT06260774",
        "sponsor": "TransCode Therapeutics",
        "intervention": "TTX-MC138",
        "sec_accession": "0001104659-26-069810",
        "cik": "0001829635",
        "exhibit_locator": "EX-99.1#NCT06260774",
        "asserted_span_sha256": "1ec3a0b235e0653bbced4f641d97df751f475020f5e18f72a71b5d354b973f33",
        "as_of": "2026-06-03T08:09:00Z",
    }
    value.update(changes)
    return value


def test_exact_human_confirmed_timestamped_match_is_accepted_and_stable() -> None:
    adapter = ClinicalTrialsAdapter(FIXTURE)
    first = adapter.check(_claim())
    second = adapter.check(_claim())
    assert first.verdict is OutcomeKind.ACCEPTED_CONDITIONALLY
    assert first.outcome == "ACCEPTED"
    assert first.evidence is not None and first.evidence["human_confirmed"] is True
    assert first.receipt == second.receipt


def test_identity_and_span_mutations_are_rejected() -> None:
    adapter = ClinicalTrialsAdapter(FIXTURE)
    assert adapter.check(_claim(sponsor="Different Sponsor")).reason_code == "SPONSOR_MISMATCH"
    assert adapter.check(_claim(asserted_span_sha256="b" * 64)).reason_code == "ASSERTED_SPAN_MISMATCH"


def test_post_cutoff_and_missing_identity_are_inconclusive() -> None:
    adapter = ClinicalTrialsAdapter(FIXTURE)
    assert adapter.check(_claim(as_of="2026-06-03T08:08:00Z")).verdict is OutcomeKind.INCONCLUSIVE
    assert adapter.check(_claim(sec_accession="0001104659-26-069899")).reason_code == "IDENTITY_NOT_RESOLVED"


def test_foreign_world_and_corrupt_fixture_fail_closed(tmp_path: Path) -> None:
    adapter = ClinicalTrialsAdapter(FIXTURE)
    foreign = _claim(world_id="open-targets", world_version="26.06")
    assert adapter.check(foreign).verdict is OutcomeKind.CHECKER_ERROR
    corrupted = json.loads(FIXTURE.read_text(encoding="utf-8"))
    corrupted["records"][0]["sponsor"] = "tampered"
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(corrupted), encoding="utf-8")
    assert check_clinical_trials_claim(_claim(), path).verdict is OutcomeKind.CHECKER_ERROR
