import threading
from pathlib import Path

from audit import AuditLedger

N_THREADS = 4
APPENDS_PER_THREAD = 25


def _claim(claim_id):
    return {"claim_id": claim_id, "subject": {"id": "HGNC:1097", "label": "BRCA1"}}


def _verdict(thread_idx, i):
    return {
        "verdict": "ACCEPTED_CONDITIONALLY",
        "snapshot_hashes": {"ontology": "a" * 64},
        "checker_version": "0.1.0",
        "derivation": {"thread": thread_idx, "i": i},
    }


def test_concurrent_appends_all_land_and_ledger_stays_intact(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = AuditLedger(path)

    errors: list[BaseException] = []

    def worker(thread_idx: int) -> None:
        try:
            for i in range(APPENDS_PER_THREAD):
                claim_id = f"thread-{thread_idx}-claim-{i}"
                ledger.append(_claim(claim_id), _verdict(thread_idx, i))
        except BaseException as exc:  # noqa: BLE001 - capture for the main thread to re-raise
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(N_THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"worker thread(s) raised: {errors}"

    raw = path.read_bytes()
    lines = raw.splitlines()
    assert len(lines) == N_THREADS * APPENDS_PER_THREAD
    assert raw.count(b"\n") == N_THREADS * APPENDS_PER_THREAD

    entries = list(ledger.iter_entries())
    assert len(entries) == N_THREADS * APPENDS_PER_THREAD

    # No two entries collapsed onto the same verdict_id (every claim_id was
    # distinct, so every verdict_id should be too), and every claim_id from
    # every thread made it in exactly once.
    verdict_ids = {e.verdict_id for e in entries}
    assert len(verdict_ids) == N_THREADS * APPENDS_PER_THREAD

    claim_ids = {e.claim_id for e in entries}
    expected_claim_ids = {
        f"thread-{t}-claim-{i}" for t in range(N_THREADS) for i in range(APPENDS_PER_THREAD)
    }
    assert claim_ids == expected_claim_ids

    ledger.verify_integrity()  # must not raise
