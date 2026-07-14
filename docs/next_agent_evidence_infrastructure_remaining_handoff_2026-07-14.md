---
title: Evidence Infrastructure Remaining Work Handoff
type: feat
date: 2026-07-14
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready-with-one-explicit-stop
product_contract_source: ce-plan-bootstrap
execution: code
supersedes_execution_state: docs/next_agent_evidence_infrastructure_handoff_2026-07-14.md
---

# Evidence Infrastructure Remaining Work Handoff

> Start from a fresh fetch of `origin/main`.
>
> Audited baseline: `main` at
> `5bdf070623c668e6acf4ebd66172f965cbf2110f`, after PR #364 merged on
> 2026-07-14. There were no open pull requests at the audit.
>
> Human director: Jawaun Brown. Agent-generated code, results, and papers remain
> under his direction and review.

## Mission

Finish the evidence-infrastructure program defined in
`docs/next_agent_evidence_infrastructure_handoff_2026-07-14.md`. Preserve that
document's requirements R1-R18, acceptance examples AE1-AE10, scientific queue
boundary, and scope boundaries. This handoff replaces only its stale execution
state and landing instructions.

The original six implementation PRs are **not merged**. PR 1 has two reviewed
implementation commits on an unpublished remote branch; PRs 2-6 remain
unimplemented. Land all six dependency layers in order.

Do not launch Modal, GPU, E6, E7, M5, E5-L, or any new scientific sweep. This is
CPU-only repository infrastructure work.

## Audited State

| Surface | State on audited `main` |
|---|---|
| Open PRs | 0 |
| Direct research packages | 54, excluding `experiments/common` |
| Root experiment manifests | 5 |
| Structured contract registry | absent on `main` |
| Claims / evidence | 12 / 12 |
| Gate-verdict JSON | 1 |
| Generated cards / result reports | 54 / 229 |
| Public-artifact envelopes | absent |
| Clean-clone reproduction lane | absent |
| Latest unrelated merge | PR #364, conditional weakness/PAC-Bayes theory note |

### Unmerged PR-1 implementation

Remote branch:
`origin/claude/evidence-infrastructure-handoff-r7h0h3`

Commits:

1. `46e3208` — `feat: add fail-closed experiment contract registry and coverage gate`
2. `2fb5e5d` — `fix: harden contract-registry validator from diff-scoped review`

The branch adds the unified registry, schema, validator integration, tests, and
required documentation. Its diff is 11 files and roughly 2,100 added lines.
There is no PR for it.

Do not duplicate this implementation. Also do not merge it blindly: it is based
on pre-PR-364 `main` and touches `TODO.md`, `docs/system_design.md`, and
`docs/module_explainer.md`, which PR #364 also changed.

Recommended recovery:

```bash
git fetch --prune origin
git switch -c codex/evidence-contract-registry-final origin/main
git cherry-pick 46e3208 2fb5e5d
```

Resolve documentation conflicts by preserving **both** the registry additions
and PR #364's PAC-Bayes entries. Before doing this, confirm that no active agent
still owns the remote branch. If ownership is active, coordinate rather than
rewriting its work.

## Discovery-Regime Audit

### Current frame

The repository can represent individual manifests, claims, evidence, and one
gate verdict, but it cannot yet fail closed over package coverage, exact
multi-run provenance, public-artifact lineage, or clean-clone reproduction.
Artifact maturity, manifest status, execution integrity, and scientific
adjudication are still easy to conflate.

### Assumption ledger

1. Package coverage and historical run coverage are different facts.
2. A manifest's `status` is noncanonical `manifest_status`, not a claim verdict.
3. `integrity_state` describes execution validity; a failed scientific gate can
   still be integrity-valid.
4. Claim status comes only from `docs/claim_registry.json`.
5. Public safety is established from tracked repo-relative bytes and declared
   receipts, not workstation file existence.
6. Ignored raw artifacts are intentionally unavailable in a clean clone.
7. A reproduction recipe must create a fresh output; a pre-existing oracle
   cannot make a no-op command pass.
8. Frozen preregistrations and committed outcomes outrank migration convenience.

### Anomaly map

- `commitment_surface` has an E5 root manifest while generated provenance
  currently displays an M5 command found heuristically.
- M5 is a strict scientific FAIL but execution-valid; E7 is integrity-invalid;
  E6 was blocked before round 1.
- External Contact has two P1 reports with the same base seed; only the LoRA
  negative is authorized for structured migration.
- Phase 5 has one Modal producer command and a separate summarization command,
  while manifest schema v1 represents one runtime command.
- E4 and E5 public JSON are committed, but their raw sources are ignored and
  unavailable to clean clones.
- `scripts/regen.py` still uses `shell=True` and does not verify fresh creation.

### Candidate reframes

1. Replace “one package, one latest run” with explicit publication/runtime run
   records and a separate primary display choice.
2. Replace one overloaded status with artifact surface, `manifest_status`,
   `integrity_state`, and claim-level adjudications.
3. Replace “file exists locally” with tracked payload + digest envelope +
   receipt-only raw lineage.
4. Replace regeneration dispatch with delete-before-run creation verification
   in an isolated checkout.

### Discriminating predictions

- A malformed nested run manifest fails rather than falling back to prose.
- Selecting M5 as the card primary never substitutes the E5 root manifest.
- M5 renders `integrity_state: valid`; only E7 renders `invalid`.
- Phase 5 can render `manifest_status: accepted` and remain scientifically
  `unadjudicated`.
- E4 and E5 envelopes resolve their own producer manifests even when M5 is the
  package primary.
- A no-op recipe fails after the declared output is deleted.

### Severe infrastructure experiment

The final severe test is the clean-clone lane: in an isolated checkout, remove
the two allowlisted committed outputs, execute structured argv/cwd recipes
without a shell, require new files, and byte-compare them with saved oracles.

Kill the implementation if it inherits source-tree outputs, invokes Modal or
network/GPU work, accepts an untracked artifact, permits heuristic fallback for
a structured run, or maps evidence/gate PASS/FAIL directly to claim status.

### Claim boundary

This work improves evidence integrity and reproducibility. It does not change
any scientific verdict, validate an ignored raw artifact, make all historical
runs structured, or activate a new experiment.

### Next best test

Land the recovered PR-1 branch, then add the first PR-2 regression: a malformed
registry-bound nested M5 manifest must fail closed instead of using the E5 root
manifest or prose.

## Dependency-Ordered Landing Plan

For every PR: fetch `origin/main`, confirm no overlapping PR/branch ownership,
create a fresh branch, add failing tests first, implement only that layer, update
`docs/system_design.md` and `docs/module_explainer.md`, refresh provenance when
affected, run targeted tests and the full quality gate, perform a diff-scoped
review, then push, open, and merge before starting the next layer.

### Remaining PR 1 — Recover and land unified package coverage

Base: recovered commits `46e3208` and `2fb5e5d`.

Required outcome:

- `docs/experiment_contract_registry.json` is authoritative.
- Exact partition: 5 structured packages + 49 active legacy exceptions = 54.
- Frozen legacy SHA-256 remains
  `86703ca46bc2a759a5f054247512c9c0df558404711db5c564ca58dfc76f2c77`.
- Missing, duplicate, orphaned, nested-only, expired, manifest-plus-exception,
  and ungrounded-new-exception cases fail.
- Historical `--as-of` mode is visibly non-certifying.
- Safe nested run-manifest paths are representable for PR 2 without permitting
  traversal or arbitrary files.

Before merge, verify the recovered branch actually validates nested manifest
content rather than only `Path.is_file()`. Keep claim/evidence/gate
bidirectional joins in PR 2 if they are not already present; do not broaden PR 1
into provenance generation.

Verification:

```bash
uv run --no-sync python -m pytest -q \
  tests/test_experiment_contract_registry.py \
  tests/test_experiment_manifest.py \
  tests/test_research_contract_schema_parity.py \
  tests/test_run_quality_checks.py
uv run --no-sync python scripts/validate_experiment_manifest.py
QUALITY_PYTEST_WORKERS=auto python3 scripts/run_quality_checks.py
```

### Remaining PR 2 — Exact run provenance and adjudication

Add:

- `experiments/commitment_surface/manifests/m5/experiment_manifest.json`
- registry records for E5, M5, E6, and E7
- run-aware provenance and gate-verdict resolution
- explicit card fields: artifact `status`, `manifest_status`,
  `integrity_state`, `run_coverage`, and `scientific_adjudications[]`

Exact bindings:

- M5: runtime package `world_responds`, publication package
  `commitment_surface`, `manifest_status: rejected`,
  `integrity_state: valid`, canonically unadjudicated.
- E6: blocked 8/104 versus 52 required, `integrity_state: not_assessed`.
- E7: 6/32 timing groups exceed the frozen 2% gate,
  `integrity_state: invalid`; do not relabel as rejected.
- E5: preserve the existing root manifest and canonical
  `COMMITMENT_GENERATOR_GENERALIZATION` /
  `EVID-COMMITMENT-E5-COVERAGE` binding.
- Select M5 as package primary and keep `run_coverage: partial`.

M5 command:

```text
uvx --python 3.12 --with numpy python -m experiments.world_responds.suite_c_reopen_reset_trigger --seeds 20260709,20261712,20262715,20263718,20264721,20265724,20266727,20267730 --out artifacts/world_responds/m5_suite_c_reopen_reset_trigger_2026_07_14.json --summary-json experiments/commitment_surface/results/m5_suite_c_reopen_reset_trigger_2026_07_14.json --summary-md experiments/commitment_surface/results/m5_suite_c_reopen_reset_trigger_2026_07_14.md
```

Required regression tests:

- malformed bound manifest is fatal;
- M5 primary never reads E5 fields;
- accepted manifest with no claim is unadjudicated;
- mixed supported/rejected claims remain separate;
- evidence PASS can support a rejected claim without changing claim status;
- unregistered heuristic fallback is an error;
- gate verdict uses the registry-bound manifest.

Run `python scripts/gen_provenance.py` and `--check`.

### Remaining PR 3 — Migrate External Contact and decide Phase 5

External Contact is unambiguous:

- bind only `experiments/external_contact/results/p1_pythia_lora_2026_06_22.md`;
- base seed `20260618`;
- `manifest_status: rejected`, `integrity_state: valid`;
- claim `WEAKNESS_EXTERNAL_PORTABILITY`;
- evidence `EVID-EXTERNAL-WEAKNESS-P1`;
- preserve `p1_pythia_2026_06_22.md` as legacy history.

#### Explicit stop: Phase 5 runtime representation

Phase 5 has:

1. Modal producer:
   `experiments/phase5_external_validity/modal_l4_suite.py --preset full
   --seeds 64 --budget-usd 1000 --out
   artifacts/phase5_external_validity/l4_full_suite.json`
2. Summarizer:
   `python -m experiments.phase5_external_validity.summarize --in
   artifacts/phase5_external_validity/l4_full_suite.json --out
   experiments/phase5_external_validity/results/phase5_l4_suite_2026_07_06.md`

Do not silently collapse this into one command or bind the auto-detected
`experiments.phase5_external_validity.core` smoke command.

Before migrating Phase 5, obtain an explicit director decision:

- either treat the Modal producer as the canonical runtime and record the
  summarizer in a reviewed structured postprocess field, extending schema/tests;
- or defer Phase 5 and keep its legacy exception active.

If deferred, migrate External Contact alone and report a 6 structured + 48
legacy partition. Do not claim the original 7 + 47 target. If the structured
postprocess extension is authorized and validated, migrate both atomically to
7 + 47.

Phase 5 remains `manifest_status: accepted`, `integrity_state: valid`, and
canonically unadjudicated. Its report has 1,216 rows and 64 seeds (0-63).

Do not migrate `semantic_concern_geometry`.

### Remaining PR 4 — Public-artifact envelope framework and E5

Add:

- `schemas/public_artifact_envelope.schema.json`
- `scripts/validate_public_artifact_envelopes.py`
- manifest `envelope_path` support
- a template and focused validator/exporter tests
- quality-gate integration
- `e5_generator_vs_coverage.json.envelope.json`

Committed E5 facts:

- payload SHA-256:
  `27305249a991a224b417950af241939ed0c1a4aff5d135a1b105f78d5876f943`
- payload bytes: 109,516
- embedded raw receipt SHA-256:
  `402cb833fd0091e5143f745e1a980842567e814e45004fa5aa62204dc003613a`
- embedded raw bytes: 5,619,830
- cells: 135
- producer: `experiments/commitment_surface/experiment_manifest.json`

Use `source_verification: receipt_only`. Validate tracked repo-relative state,
digest consistency, receipt consistency, omission metadata, and exact producer
binding. Do not regenerate the committed E5 payload without its raw source.

### Remaining PR 5 — E4 producer manifest and envelope

Add:

- `experiments/commitment_surface/manifests/e4/experiment_manifest.json`
- E4 registry run record, preserving package `run_coverage: partial`
- exporter sidecar support and focused tests
- `e4_pythia_lora_v2_appendix.json.envelope.json`

Committed E4 facts:

- payload SHA-256:
  `58b98a379f84c4c0672ce07252aa44f9ffef6172a0844752b416d7cf0272539a`
- payload bytes: 77,480
- embedded raw receipt SHA-256:
  `67e86aef888540ba70d013de6a2be2def1871aa0970134bd3d115e2f2dbc5428`
- embedded raw bytes: 209,612
- cells: 108
- `manifest_status: rejected`
- `integrity_state: valid`
- empty canonical reference arrays plus explicit `unadjudicated`

The producer is the E4 nested manifest, never the E5 root or M5 primary.

### Remaining PR 6 — Structured reproduction and clean-clone CI

Allowlist only:

| Package | Oracle |
|---|---|
| `bayesian_voi` | `experiments/bayesian_voi/results/bayesian_voi_summary.json` |
| `mathematical_claims` | `experiments/mathematical_claims/results/mathematical_claims_summary.json` |

Rewrite `scripts/regen.py` so verifier mode:

- consumes registry/manifest structured argv and cwd;
- never uses `shell=True`;
- copies the oracle aside;
- deletes the declared output in an isolated checkout;
- requires a newly created file;
- byte-compares it with the oracle;
- rejects unknown/nonallowlisted packages;
- keeps Modal recipes inspectable but non-dispatching.

Add `tests/test_regen.py` and a Linux clean-clone workflow. Include no-op,
missing-output, byte-mismatch, cwd, nonallowlisted, dirty-output, and Modal
non-dispatch cases.

Current oracle SHA-256 values:

- Bayesian VOI:
  `c765291079ec365328412350fc2fedd16a5d43aa732afd33c7159a24e9ad105b`
- Mathematical claims:
  `e370b61fa5abe936aa7f81f53d3c1ecb780290e8900524d0d44f854991766b09`

Linux CI is canonical for byte stability.

## Cross-Cutting Verification

Every PR:

```bash
uv run --no-sync ruff check .
uv run --no-sync ty check scripts experiments tests
QUALITY_PYTEST_WORKERS=auto python3 scripts/run_quality_checks.py
```

When provenance changes:

```bash
python scripts/gen_provenance.py
uv run --no-sync python scripts/gen_provenance.py --check
```

Envelope PRs:

```bash
uv run --no-sync python scripts/publication_guard.py
uv run --no-sync python scripts/validate_public_artifact_envelopes.py
```

Before each merge, verify the real affected workflow, review the full diff, and
confirm that no scientific status was inferred from artifact maturity, manifest
status, evidence status, or gate status.

## Final Audit

After all landed work:

1. Fetch fresh `main`.
2. Recount structured packages and active exceptions.
3. Recount structured and explicit legacy run records.
4. Validate both envelope pairs from tracked bytes.
5. Run both clean-clone recipes.
6. Run the full quality gate.
7. Confirm no open PR remains.
8. Leave broad migration TODOs open while exceptions or partial histories
   remain.
9. Record `semantic_concern_geometry` as blocked on multi-execution semantics.
10. Report the Phase 5 decision honestly.

The next smallest structural migration after this tranche should be chosen by
expiry pressure and run-binding clarity, not by scientific desirability.
