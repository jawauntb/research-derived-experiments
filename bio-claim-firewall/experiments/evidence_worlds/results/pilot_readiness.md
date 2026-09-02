# Bio Claim Firewall: pilot-readiness evaluation

Decision: **READY_FOR_BOUNDED_PILOT**

This deterministic offline run uses independently locked claims and immutable registry source contracts. PASS means bounded adapter/source consistency only; it does not establish authenticity, causality, efficacy, or universal truth.

| World | Status | Fatal gates | Controls |
| --- | --- | ---: | ---: |
| `clinical-trials-sec` `2025-09-01_2026-09-01` | **PASS** | 6/6 | 5/5 |
| `open-targets` `26.06` | **PASS** | 6/6 | 5/5 |
| `arc-vcc` `2025-h1-measurements` | **PASS** | 6/6 | 5/5 |

## Readiness requirements

- `three_distinct_preregistered_worlds`: **PASS**
- `all_manifests_admitted`: **PASS**
- `declared_perturbational_translational_pilot_roles_present`: **PASS**
- `declared_clinical_and_open_targets_registered_locators_exact`: **PASS**
- `preregistered_operator_reviews_current`: **PASS**
- `all_fatal_gates_and_controls_pass`: **PASS**

## Deferred worlds

- `flywire-codex` — Deferred: no committed licensed evidence fixture or adapter.
- `neurovault` — Deferred: no committed licensed evidence fixture or adapter.

## Gate evidence

### clinical-trials-sec

- `official_source_identity`: **PASS** — Manifest identity is ADMITTED and adapter hashes equal the immutable registry and preregistration contracts.
- `license_and_custody`: **PASS** — The manifest license ID, official source URL, and terms URL exactly match the immutable registry and a scope-limited operator review that is current for the manifest data clock.
- `timestamp_cutoff_no_time_travel`: **PASS** — The hash-bound fixture satisfies the preregistered world-specific semantic constraint.
- `complete_hashes_and_schema`: **PASS** — The derived fixture hash matches the manifest and adapter hashes exactly match the registered source contract; required review artifacts are present, hash-bound, and current for the locked evaluation date.
- `organic_positive_negative_null_controls`: **PASS** — Exactly one locked positive, negative, and null control ran and matched its preregistered outcome.
- `world_isolation_and_fail_closed`: **PASS** — Exactly one locked corruption and cross-world control ran and failed closed.
### open-targets

- `official_release_identity`: **PASS** — Manifest identity is ADMITTED and adapter hashes equal the immutable registry and preregistration contracts.
- `license_and_redistribution`: **PASS** — The manifest license ID, official source URL, and terms URL exactly match the immutable registry and a scope-limited operator review that is current for the manifest data clock.
- `complete_hashes_and_schema`: **PASS** — The derived fixture hash matches the manifest and adapter hashes exactly match the registered source contract; required review artifacts are present, hash-bound, and current for the locked evaluation date.
- `release_and_score_semantics`: **PASS** — The hash-bound fixture satisfies the preregistered world-specific semantic constraint.
- `organic_positive_negative_null_controls`: **PASS** — Exactly one locked positive, negative, and null control ran and matched its preregistered outcome.
- `world_isolation_and_fail_closed`: **PASS** — Exactly one locked corruption and cross-world control ran and failed closed.
### arc-vcc

- `dataset_license_scope`: **PASS** — The manifest license ID, official source URL, and terms URL exactly match the immutable registry and a scope-limited operator review that is current for the manifest data clock.
- `official_release_identity`: **PASS** — Manifest identity is ADMITTED and adapter hashes equal the immutable registry and preregistration contracts.
- `split_integrity_no_leakage`: **PASS** — The hash-bound fixture satisfies the preregistered world-specific semantic constraint.
- `complete_hashes_and_schema`: **PASS** — The derived fixture hash matches the manifest and adapter hashes exactly match the registered source contract; required review artifacts are present, hash-bound, and current for the locked evaluation date.
- `organic_positive_negative_null_controls`: **PASS** — Exactly one locked positive, negative, and null control ran and matched its preregistered outcome.
- `world_isolation_and_fail_closed`: **PASS** — Exactly one locked corruption and cross-world control ran and failed closed.
