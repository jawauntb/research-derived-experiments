---
title: U2 Unified Experiment Contract Registry - In-Progress Handoff
date: 2026-07-14
status: in_progress
branch: codex/implement-primer-residuals
base_sha: befa8beb10a8d02f1866eca0350ff76b62b864d1
---

# U2 Unified Experiment Contract Registry - In-Progress Handoff

This document is self-contained for an agent with no prior conversation context.
Continue the existing worktree and branch; do not restart from another branch or
discard the uncommitted changes.

Human research director: Jawaun Brown. Agent-generated code, results, and papers
remain under his direction and review.

## Mission

Finish and ship only U2 / PR 1 from
`docs/next_agent_evidence_infrastructure_handoff_2026-07-14.md`: one authoritative
experiment contract registry and a fail-closed package-coverage gate.

Do not attempt the six-PR program in one branch. U3 and later units require U2 to
merge first, followed by a fresh fetch of `main` and a new worktree/branch.

The governing acceptance scope is:

- Requirements R1-R5 and R16-R18.
- Acceptance examples AE1-AE2.
- Exact repository partition: 54 direct research packages = 5
  `structured_manifest` records + 49 `legacy_exception` records.
- `experiments/common` is support code and remains excluded.

## Non-negotiable user constraint

The user added this instruction after implementation began:

> don't use local cpu at all use modal

Interpret it as a compute constraint. Repository inspection and code editing may
remain local, but all tests, lint, type checks, and quality workloads from this
point forward must execute in Modal containers. Do not run local pytest, Ruff,
ty, experiment code, or the root quality command.

An ignored ephemeral runner already exists at `tmp/modal_u2_quality.py`. It mounts
the current checkout into a Modal CPU container and supports `targeted`, `type`,
and `full` modes. Keep it until verification is complete, then remove it; do not
commit it. Use the current Modal client (`--from modal`), not the earlier
`modal==1.2.6` pin: the old client exposes a runtime that cannot import existing
tracked modules using `single_use_containers=True`.

## Starting state and audit

- Worktree: `/Users/jawaun/.codex/worktrees/d3a3/Research Derived Experiments`
- Branch: `codex/implement-primer-residuals`
- Fresh base: `befa8beb10a8d02f1866eca0350ff76b62b864d1`
- At the start, `HEAD == origin/main`, GitHub had zero open PRs, and no active
  branch owned the registry/schema work.
- Audit count: 54 direct packages excluding `common`; 5 package-root manifests;
  no pre-existing contract registry.
- The source PDF is
  `/Users/jawaun/.codex/worktrees/9196/Research Derived Experiments/output/pdf/primer_derived_research_residuals_2026_07_14.pdf`.
- Its newer implementation-ready refinement is
  `docs/next_agent_evidence_infrastructure_handoff_2026-07-14.md` and is the
  controlling implementation plan.

U1 is complete. A disposable clean-tree `bayesian_voi` spike proved the proposed
run-record field names, SHA-256 sidecar binding, and delete-before-run byte
comparison. That spike ran before the user imposed the Modal-only constraint and
left no files behind.

## Work already implemented

### New files

- `docs/experiment_contract_registry.json`
- `schemas/experiment_contract_registry.schema.json`

### Modified files

- `scripts/validate_experiment_manifest.py`
- `tests/test_experiment_manifest.py`
- `tests/test_research_contract_schema_parity.py`

### Current git state

Nothing is staged or committed. The two new registry/schema files are untracked;
the three implementation/test files are modified. The handoff document itself is
also untracked.

### Immediate resume checkpoint (live Modal job)

The user asked to switch agent sessions while the final full remote gate was
running. Do not restart or discard this work. At handoff time:

- Live Modal app/run: `ap-4VlKWbZW4QphOtnLdJjpA0`
- Local Modal CLI process/session: unified-exec session `40799` (may disappear
  when the Codex session changes; the Modal run ID above is authoritative).
- Command that launched it:

  ```bash
  uvx --python 3.12 --from modal modal run \
    tmp/modal_u2_quality.py --mode full
  ```

- The mounted tree includes the final typing fix: the committed-registry test
  narrows `registry["packages"]` with `typing.cast`; no source behavior changed.
- A separate remote `ty` run is already green (details below), and the focused
  pytest batch was green immediately before this full run.
- Nothing is committed, pushed, or in a PR yet because the user required quality
  checks before publication. Once the live job is green, stage the six current
  U2 files plus this handoff, commit, push, and open a **draft** PR first. Then
  continue the architecture/TODO/adversarial-test updates on the same branch and
  push follow-up commits to that PR.

If the live run cannot be reattached to, inspect it in Modal by the app/run ID.
If it was preempted or cancelled, rerun the exact command above. Never substitute
a local quality workload.

### Implemented contract behavior

- The registry records all 54 packages in sorted order.
- Five existing root manifests are structured records:
  `bayesian_voi`, `commitment_surface`, `mathematical_claims`,
  `passive_active_phase_map`, and `seed_bootstrap_calibration`.
- Structured records already expose the U2-approved run shape: `run_id`,
  publication/runtime packages, provenance mode, integrity state, optional exact
  manifest path, report paths, claim IDs, evidence IDs, gate-verdict paths,
  package run coverage, and optional primary run.
- `commitment_surface` remains partial-history and names only the existing E5
  structured run. M5 is intentionally not canonically adjudicated in U2.
- The 49 legacy exceptions identify owner, bounded reason code, explanation,
  next action, review/expiry dates, frozen cutoff, and
  `adjudicates_claims: false`.
- Initial expiries are staggered:
  - `external_contact` and `phase5_external_validity`: 2026-09-15, scheduled
    safe migration.
  - Most legacy packages: 2026-12-01, missing root manifest.
  - `activation_geometry` and `rotation_weakness`: 2026-12-15, ambiguous run
    history.
  - `semantic_concern_geometry`: 2026-12-31, multi-execution contract needed.
- The sorted 49-package legacy set hashes to
  `86703ca46bc2a759a5f054247512c9c0df558404711db5c564ca58dfc76f2c77`.
  That digest is independently pinned in both validator code and the JSON Schema,
  so a new package cannot authorize itself by editing the list and adjacent
  digest together.
- Normal validation warns at 30 or fewer days before expiry, fails on the expiry
  date, and rejects horizons longer than 180 days.
- Date-sensitive validation accepts an injected `as_of` date. The CLI exposes
  this only through the visibly labeled `--historical-inspection --as-of
  YYYY-MM-DD` path; ordinary no-argument CI uses the current date.
- Explicit manifest-path validation remains registry-independent and backward
  compatible.
- No-argument manifest validation now validates the registry partition first,
  then validates every discovered manifest.
- The existing root quality wrapper already invokes the no-argument manifest
  validator, so `scripts/run_quality_checks.py` does not need a cosmetic change.

## Verification evidence so far

Proof-first tests were added before the registry reader. The initial pre-feature
run failed at import because the new registry functions/constants did not yet
exist, as expected.

After implementation, tests were dispatched to Modal. The first two runs used
the old pin:

```bash
uvx --python 3.12 --from modal==1.2.6 modal run \
  tmp/modal_u2_quality.py --mode targeted
```

First Modal run:

- Modal run: `ap-YuzJ2v7lz31moiBf1Ybrf2`
- Result: 29 passed, 12 subtests passed, 1 fixture failure.
- Failure: test-only `Path` construction used string division in the nested
  manifest fixture.
- The fixture was corrected; no production behavior changed for that fix.

Second Modal run:

- Modal run: `ap-q6k0ujl5nldLkZcfSH2EZ6`
- Result: **30 passed, 12 subtests passed**.
- Files tested: `tests/test_experiment_manifest.py`,
  `tests/test_research_contract_schema_parity.py`, and
  `tests/test_run_quality_checks.py`.

The old `modal==1.2.6` runtime then produced three unrelated import failures in
existing `world_responds` tests because it does not accept the tracked
`single_use_containers=True` argument. Switching only the ephemeral verifier to
the current Modal client resolved that infrastructure mismatch.

Current-client focused run:

- Modal run: `ap-OwjHsD0cGY3dBOXOlIK8A0`
- Result: **30 passed, 12 subtests passed**.

First current-client full run:

- Modal run: `ap-KNmo6DfokkpzHBWeLUdyQz`
- Pytest: **530 passed, 1 skipped, 54 subtests passed**.
- Publication guard, evidence/claim/manifest/gate validators, primer metadata,
  provenance freshness, compileall, and Ruff all passed.
- `ty` found two test-only container-shape annotations. After the first fix, a
  retry (`ap-ZNIvBF6B0xXQgiju1acW6s`) was worker-preempted and automatically
  restarted, then reduced the result to one remaining annotation diagnostic.

Dedicated current-client type run after the final cast:

- Modal run: `ap-OkwK7nTXhxGXNfowYf8omC`
- Result: **`ty check scripts experiments tests` passed**.

Final current-client full run:

- Modal run: `ap-4VlKWbZW4QphOtnLdJjpA0`
- Status at handoff: **running**. Monitor this run; it is the last pre-commit
  publication gate.

## Tests currently covered

The focused suite covers:

- Exact committed 54 = 5 + 49 partition.
- Missing package failure.
- New package exception outside the frozen set.
- Adjacent frozen-list plus recomputed-digest tampering against the independent
  anchor.
- Digest mismatch.
- Expiry inclusive failure and exactly-30-day warning.
- Exception horizon greater than 180 days.
- Duplicate and orphaned package records.
- Blank exception fields and forbidden scientific/status fields.
- Nested-only manifest not satisfying structured root coverage.
- Manifest-plus-exception overlap.
- `common` exclusion.
- Explicit manifest-path CLI backward compatibility.
- Schema/validator vocabulary and frozen digest parity.
- Required root-quality command still contains the no-argument manifest
  validator.

## Remaining implementation and review work

Continue in this order.

1. Inspect the current diff; preserve the implemented work.
2. Add or consciously disposition the remaining high-value adversarial cases:
   - Frozen list unsorted or duplicate.
   - Tampered `warning_days` or maximum horizon.
   - Invalid/future review date; expiry at/before review; 31-day no-warning
     boundary.
   - Absolute, traversal, cross-package, or symlink-escaping manifest/report
     paths.
   - Missing or malformed structured root manifest.
   - Duplicate/unknown `run_id` and unresolved `primary_run_id`.
   - Wrong publication package, nonexistent runtime package, and
     `provenance_mode`/manifest-path mismatch.
   - Duplicate or unsafe report/gate paths.
   - Historical CLI flag misuse and clearly labeled success output.
3. Review whether empty `gate_verdict_paths` alongside valid claim/evidence IDs is
   documented clearly enough. Ten evidence rows have gate IDs, but only E5 has a
   committed gate-verdict file. Do not fabricate verdict paths or equate manifest
   gate declarations with verdicts.
4. Update `docs/system_design.md` and `docs/module_explainer.md` as required by
   `AGENTS.md`. Describe the authoritative registry, 54 = 5 + 49 coverage, frozen
   set/digest, expiry semantics, run-shape readiness, and fail-closed quality-gate
   integration.
5. Update `TODO.md` without closing broad migration work. Recommended shape:

   ```markdown
   - [ ] Migrate experiment families to structured manifests and replace prose-only provenance extraction.
     - [x] Partition all 54 research packages in `docs/experiment_contract_registry.json`: 5 structured manifests and 49 time-bounded legacy exceptions.
     - [ ] Replace the 49 exceptions and partial run histories with exact structured run bindings.
   - [ ] Add CI lanes for manifest coverage, public-artifact envelopes, and clean-clone reproduction.
     - [x] Enforce manifest-or-active-exception package coverage in the required root quality gate.
     - [ ] Enforce public-artifact envelopes and clean-clone reproduction.
   ```

6. Update only the relevant implementation-log/detail rows in
   `docs/primers/backlogs/software_engineering_todo.md`:
   - Keep E-SE-023, E-SE-028, E-SE-029, E-SE-033, and E-SE-037 partial.
   - E-SE-029 should say the authoritative registry partitions 54 packages into
     5 structured manifests and 49 bounded exceptions; scaffolding and migration
     of legacy/partial histories remain.
   - E-SE-033 should say the registry supplies package/run fields but generated
     provenance does not consume them yet.
   - E-SE-037 should say the exact inventory/digest exists but generated doc
     fragments and stale-count injection checks remain.
   - Do not rewrite unrelated historical 50-package audit snapshots in this U2
     PR unless intentionally expanding to the broader Wave 0 truth-sync scope.
7. Rerun the targeted Modal batch after any test/code edits.
8. Run full verification on Modal:

   ```bash
   uvx --python 3.12 --from modal modal run \
     tmp/modal_u2_quality.py --mode full
   ```

   `full` calls `python scripts/run_quality_checks.py` inside the Modal container,
   which performs locked dependency sync, all tests, compileall, publication
   guard, all research-contract validators, primer metadata, provenance
   freshness, Ruff, and ty. Preserve the Modal run ID and result in the PR body.
9. Run a diff-scoped `ce-code-review` and apply every actionable finding. The
   registry is a trust boundary, so review path/date/digest bypasses carefully.
10. Remove `tmp/modal_u2_quality.py` after all remote verification is complete.
11. Confirm no generated provenance outputs changed. U2 does not yet make
    `gen_provenance.py` consume the registry, so do not regenerate unrelated
    cards merely to create noise.
12. Stage only U2 files, commit, push, and open a **draft** PR. Suggested title:
    `feat(contracts): enforce experiment package coverage`.
    The user's requested order is: publish the current verified diff to the
    draft PR first, then add the remaining updates as follow-up commits.
13. Do not begin U3 on this branch. U3 requires this PR to merge, then a fresh
    `origin/main` worktree/branch.

## Required final files for this PR

Expected tracked diff when finished:

- `docs/experiment_contract_registry.json`
- `schemas/experiment_contract_registry.schema.json`
- `scripts/validate_experiment_manifest.py`
- `tests/test_experiment_manifest.py`
- `tests/test_research_contract_schema_parity.py`
- `docs/system_design.md`
- `docs/module_explainer.md`
- `TODO.md`
- `docs/primers/backlogs/software_engineering_todo.md`
- This handoff may be included or omitted from the final PR depending on whether
  it remains useful after completion.

`scripts/run_quality_checks.py` and `tests/test_run_quality_checks.py` need no
behavioral edit unless integration changes: the existing required no-argument
manifest-validator step already becomes the coverage gate.

## Scientific and scope guardrails

- Do not add M5 claim/evidence/gate records in U2. The newer handoff reserves M5
  run semantics for U3 and requires it to remain valid, rejected at manifest
  surface, and canonically unadjudicated until explicitly bound.
- Do not launch E6, E5-L, E7, M5, or any GPU experiment.
- Do not change frozen gates or scientific outcomes.
- Do not infer claim status from manifest `accepted`/`rejected`, evidence
  `pass`/`fail`, or artifact maturity.
- Do not add a parallel registry or separate validator script; the authoritative
  registry is consumed by `validate_experiment_manifest.py`.
- Do not close the broad manifest/provenance/public-envelope/reproduction TODOs.
- Do not commit raw artifacts, secrets, `.env`, Modal tokens, or the ignored
  temporary Modal runner.

## Definition of done for this handoff

U2 is finished only when the exact 54-package partition and adversarial failure
cases pass on Modal, both required architecture docs and ledgers are accurate,
the full Modal-hosted root quality gate is green, diff-scoped review findings are
resolved, and the focused commit is pushed with a PR opened against `main`.

At the time this handoff was last updated, none of the work was staged,
committed, pushed, or placed in a PR; final full Modal run
`ap-4VlKWbZW4QphOtnLdJjpA0` was still running.
