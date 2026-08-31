import copy

from audit import compute_verdict_id

CLAIM = {
    "claim_id": "11111111-1111-4111-8111-111111111111",
    "subject": {"id": "HGNC:1097", "label": "BRCA1"},
    "relation": "increases",
    "object": {"id": "HGNC:1100", "label": "BRCA2"},
    "polarity": "positive",
}
VERDICT_BODY = {
    "claim_id": "11111111-1111-4111-8111-111111111111",
    "verdict": "ACCEPTED_CONDITIONALLY",
    "derivation": {
        "evidence_ids": ["perturbseq.replogle_2022:000001"],
        "applied_rules": ["R-EDGE-01"],
        "conditions": ["only in K562, resting state"],
    },
}
SNAPSHOT_HASHES = {"ontology": "a" * 64, "evidence": "b" * 64}
CHECKER_VERSION = "0.1.0"


def _compute():
    return compute_verdict_id(CLAIM, VERDICT_BODY, SNAPSHOT_HASHES, CHECKER_VERSION)


def test_deterministic_across_calls():
    assert _compute() == _compute()


def test_deterministic_across_equal_but_distinct_objects():
    a = compute_verdict_id(copy.deepcopy(CLAIM), copy.deepcopy(VERDICT_BODY), dict(SNAPSHOT_HASHES), str(CHECKER_VERSION))
    b = compute_verdict_id(copy.deepcopy(CLAIM), copy.deepcopy(VERDICT_BODY), dict(SNAPSHOT_HASHES), str(CHECKER_VERSION))
    assert a == b


def test_is_32_lowercase_hex_chars():
    vid = _compute()
    assert len(vid) == 32
    assert all(c in "0123456789abcdef" for c in vid)


def test_changes_when_claim_changes():
    other_claim = copy.deepcopy(CLAIM)
    other_claim["polarity"] = "negative"
    assert compute_verdict_id(other_claim, VERDICT_BODY, SNAPSHOT_HASHES, CHECKER_VERSION) != _compute()


def test_changes_when_verdict_body_changes():
    other_verdict = copy.deepcopy(VERDICT_BODY)
    other_verdict["verdict"] = "REJECTED"
    assert compute_verdict_id(CLAIM, other_verdict, SNAPSHOT_HASHES, CHECKER_VERSION) != _compute()


def test_changes_when_snapshot_hashes_change():
    other_snapshots = dict(SNAPSHOT_HASHES, ontology="c" * 64)
    assert compute_verdict_id(CLAIM, VERDICT_BODY, other_snapshots, CHECKER_VERSION) != _compute()


def test_changes_when_checker_version_changes():
    assert compute_verdict_id(CLAIM, VERDICT_BODY, SNAPSHOT_HASHES, "0.2.0") != _compute()


def test_key_order_in_inputs_does_not_change_id():
    reordered_claim = {k: CLAIM[k] for k in reversed(list(CLAIM.keys()))}
    reordered_snapshots = {k: SNAPSHOT_HASHES[k] for k in reversed(list(SNAPSHOT_HASHES.keys()))}
    assert compute_verdict_id(reordered_claim, VERDICT_BODY, reordered_snapshots, CHECKER_VERSION) == _compute()


def test_supersedes_field_changes_id():
    superseding = copy.deepcopy(VERDICT_BODY)
    superseding["supersedes"] = "deadbeefdeadbeefdeadbeefdeadbeef"
    assert compute_verdict_id(CLAIM, superseding, SNAPSHOT_HASHES, CHECKER_VERSION) != _compute()
