# Bio Claim Firewall live OpenAI replay preregistration — 2026-09-02

## Discovery-Regime Audit

Question: Can the Bio Claim Firewall currently on `main` execute its configured
OpenAI proposer through `ModelManagerAdapter`, pass the model's output through
the deterministic verifier, and emit a public, sanitized, tamper-evident
receipt without exposing credentials or raw provider responses?

Current regime:

- Artifact types: fixed question manifests, model-produced claim JSON,
  hash-verified evidence records, deterministic verdicts, local JSONL
  trajectories, local summaries, and static public receipts.
- Operations: Doppler runtime injection, `ModelManagerAdapter`, `Proposer`,
  `verify()`, the Phase 5 smoke runner, and an allowlist-only receipt exporter.
- Gates/verifiers: immutable question digest, exact source hashes, proposer
  schema validation, the closed verdict enum, derivation resolution, public
  receipt schema, recursive secret/path exclusion, and site tests.
- Known limitations: this is one OpenAI configuration over five fixed K562
  cases. It is not an independent replication, a biology benchmark, a safety
  evaluation, or evidence of cross-model generalization.

Action class: **search** within the existing model-adapter and verifier regime.
The run adds current operational evidence and a new public receipt type; it
does not introduce or promote a scientific discovery claim.

## Experiment

- Runtime: `doppler run --project shared --config dev -- ...`; only the child
  process receives `OPENAI_API_KEY`, and neither its value nor the environment
  is written to a tracked artifact.
- Model/prompt: use the repository-pinned proposer provider and prompt from
  `bio-claim-firewall/src/model_manager/config.yaml` without post-run edits.
- Data clock: load the ignored, hash-verified six-source K562 pilot cache from
  the primary checkout and record every source digest in the local summary.
- Manifest: execute the already frozen `bio-claim-firewall/eval/smoke/questions.json`
  once under a new run id. This is an operational replay, not a second sample.
- Raw store: keep the trajectory and summary under the gitignored
  `bio-claim-firewall/eval/smoke_trajectories/` directory.
- Public store: generate one static receipt containing only allowlisted model,
  prompt, checker, manifest, hash, aggregate-usage, and per-case verdict fields.

## Fatal gate

Accept only if all five cases complete; every proposed claim is schema-valid;
the verifier emits no `CHECKER_ERROR`; each accepted derivation resolves to the
frozen ledger; the public receipt binds both raw files by SHA-256; and recursive
tests find no credential, environment dump, absolute local path, raw response,
or error payload. Any failure preserves the local run but withholds the public
receipt and all claims of a successful replay.

The sanitizer must also reject altered manifests, failed summaries,
case/trajectory mismatches, mixed provider/model/prompt provenance, invalid
claims, unresolved evidence ids, and unknown fields. Railway remains a static
GET/HEAD service and must not receive `OPENAI_API_KEY`.

## Promotion boundary

A pass supports only this statement: one recorded OpenAI run traversed the
configured proposer-to-verifier path on 2026-09-02, and its sanitized receipt
is internally bound to retained local artifacts. It does not authenticate the
provider cryptographically, prove the biological claims, establish robustness,
or show that customers receive value.
