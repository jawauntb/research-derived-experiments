# Bio Claim Firewall: pilot-readiness evaluation

Decision: **READY_FOR_BOUNDED_PILOT**

This is a deterministic offline run over committed compact fixtures. PASS means bounded adapter/source consistency only; it does not establish authenticity, causality, efficacy, or universal truth.

| World | Status | Fatal gates | Controls |
| --- | --- | ---: | ---: |
| `clinical-trials-sec` `2025-09-01_2026-09-01` | **PASS** | 6/6 | 5/5 |
| `open-targets` `26.06` | **PASS** | 6/6 | 5/5 |
| `arc-vcc` `2025-h1-measurements` | **PASS** | 6/6 | 5/5 |

## Deferred worlds

- `flywire-codex` — Deferred: no committed licensed evidence fixture or adapter.
- `neurovault` — Deferred: no committed licensed evidence fixture or adapter.

## Gate evidence

### clinical-trials-sec

- `official_source_identity`: **PASS** — Manifest world/version and source IDs match the loaded fixture.
- `license_and_custody`: **PASS** — Manifest source licenses are verified and raw custody is outside the public fixture.
- `timestamp_cutoff_no_time_travel`: **PASS** — The world-specific adapter validated its frozen scope and integrity constraints.
- `complete_hashes_and_schema`: **PASS** — Adapter loaded the schema; source hashes and derived-artifact hash match the manifest.
- `organic_positive_negative_null_controls`: **PASS** — All preregistered organic and adversarial controls matched their expected fail-closed outcomes.
- `world_isolation_and_fail_closed`: **PASS** — Foreign-world and corrupted-fixture controls fail closed.
### open-targets

- `official_release_identity`: **PASS** — Manifest world/version and source IDs match the loaded fixture.
- `license_and_redistribution`: **PASS** — Manifest source licenses are verified and raw custody is outside the public fixture.
- `complete_hashes_and_schema`: **PASS** — Adapter loaded the schema; source hashes and derived-artifact hash match the manifest.
- `release_and_score_semantics`: **PASS** — The world-specific adapter validated its frozen scope and integrity constraints.
- `organic_positive_negative_null_controls`: **PASS** — All preregistered organic and adversarial controls matched their expected fail-closed outcomes.
- `world_isolation_and_fail_closed`: **PASS** — Foreign-world and corrupted-fixture controls fail closed.
### arc-vcc

- `dataset_license_scope`: **PASS** — Manifest source licenses are verified and raw custody is outside the public fixture.
- `official_release_identity`: **PASS** — Manifest world/version and source IDs match the loaded fixture.
- `split_integrity_no_leakage`: **PASS** — The world-specific adapter validated its frozen scope and integrity constraints.
- `complete_hashes_and_schema`: **PASS** — Adapter loaded the schema; source hashes and derived-artifact hash match the manifest.
- `organic_positive_negative_null_controls`: **PASS** — All preregistered organic and adversarial controls matched their expected fail-closed outcomes.
- `world_isolation_and_fail_closed`: **PASS** — Foreign-world and corrupted-fixture controls fail closed.
