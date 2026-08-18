# AGENTS.md

Guidance for AI coding agents and human contributors working in this repository.

## Documentation sync (required)

Whenever you make a **meaningful** addition or change to the codebase — new or
renamed experiments, scripts, tests, packages, runtime flows, dependencies,
environment requirements, deploy paths, or public surfaces — you **must** update:

1. [`docs/system_design.md`](docs/system_design.md) — end-to-end system design and operating model
2. [`docs/module_explainer.md`](docs/module_explainer.md) — package/module/script/test/doc catalog

Trivial edits (typos, comment-only tweaks, pure formatting) do not require a doc
pass. If the change would affect how someone understands, runs, maintains, or
extends the repo, update both docs in the same PR/commit series.

Also refresh provenance when experiment results or run commands change:

```bash
python scripts/gen_provenance.py
```

## Merge on complete (required)

You are **allowed and compelled** to squash-merge finished work to `main`
as soon as this task's check is green. Do not stockpile draft PRs, wait
for sibling lanes, or defer landing to a later integration agent.

1. One branch, one concern, one check.
2. Open a PR vs `main`. Draft only while the check is still running.
3. When the check passes: `gh pr ready N` then `gh pr merge N --squash`.
   This repo does not have GitHub auto-merge; squash immediately.
4. Use GitHub squash merge. Do not check out `main` in a second local
   worktree (`/tmp/us4-search` already holds it).

Do **not** merge PR **464**. Do not merge a failed check, secrets, or a
new scientific letter this tranche did not ask for. Do not force-push
`main`. Always-on Cursor rule: `.cursor/rules/merge-on-complete.mdc`.

## Research operating norms

- Prefer small, reviewable commits; do not break local quality checks.
- Keep the public surface safe: summarize into `experiments/*/results/`; leave raw dumps in gitignored `artifacts/`.
- Do not commit secrets, `.env`, Modal tokens, or full-text citation archives under `references/papers|text|html/`.
- Pre-register gates before large sweeps; preserve rejected alternatives.
- Run `python3 scripts/run_quality_checks.py` before merging substantive Python changes.
- Attribution: human director Jawaun Brown; agent-generated code/papers under review — keep provenance honest.

## Experiment review routing (required)

- Run the `scientific-discovery-regime-audit` skill when creating or preregistering an experiment, before a large sweep, and when interpreting results for promotion or a discovery claim. Do not run the full unified reviewer for routine code or documentation work.
- Before execution, record the target object and decision, representation and data clock, material assumptions, fatal gates, decisive controls, and evidence/provenance paths in the preregistration or audit card. Keep this compact and use only the relevant domain modules from `papers/unified_citation_grounded_review/paper.md`.
- Treat fatal gates as noncompensatory: a failed or unknown necessary gate cannot be averaged away by strong downstream scores. Withhold or reject the affected claim while preserving supported subclaims.
- When sources or results conflict, preserve both claims and resolve the tension by object, scope, conditions, representation, validity layer, and evidence. Never erase a conflicting or rejected artifact to simplify the narrative.

## Mathematical claim routing (required)

- Apply this gate when adding or materially changing a theorem, derivation, stochastic model, geometric construction, estimator, statistical test, or optimization objective. Do not run it for routine arithmetic or implementation-only changes.
- Before promotion, record the mathematical objects, types, domains/support and units; exact claim and quantifiers; assumptions and identification conditions; derivation/proof dependencies; coordinate or invariance choices; and edge, limiting, and null cases. Use only the relevant domain modules from `papers/unified_citation_grounded_review/paper.md`.
- Pair analytic review with proportionate executable checks such as symbolic identities, dimensional checks, limiting cases, toy counterexamples, or numerical agreement. Simulation and empirical fit are sanity checks, not substitutes for a proof when the claim is theorem-level.
- A failed or unknown mathematical prerequisite blocks the mathematical claim and every downstream claim that depends on it. Preserve valid subclaims and rejected derivations; do not waive or average away the failure.

## Theorem proving with Lea (required)

Every theorem-level claim — new, materially changed, or promoted from a
Python enumeration — **must** be proved in Lean 4 and kernel-audited
through the local Lea pipeline before any paper, doc, or summary labels
it stronger than "python-enumerated". Empirical process results (seed
counts, Φ ratios, GD tallies) are exempt and stay labeled Python.
Backlog and status live in `docs/lea/theorem_backlog.md`.

1. **Two states, never collapsed.** *Proved* = `lake build` green, zero
   `sorry`. *Verified* = SafeVerify kernel replay passed with axioms ⊆
   `{propext}`. A green build or UI badge is never "verified". Receipts
   go in `docs/lea/VERIFY_RECEIPT_<date>.md`; labels in papers/docs are
   derived from the latest receipt, never stored ahead of it.
2. **No `native_decide`, ever** — SafeVerify rejects it. The house move
   is kernel `decide` with raised `set_option maxRecDepth` /
   `maxHeartbeats`. No Mathlib in the mathlib-free cores under
   `formal/structural-intelligence/`.
3. **Statement hygiene.** No `{ field := … }` structure literals inside
   theorem *statements* (SafeVerify's sorry-target splitter breaks on
   the embedded `:=`); assert projections instead. Quantify over
   explicit lists (`∀ x ∈ [...]`) rather than bare inductives so kernel
   `decide` applies without Fintype instances.
4. **Runbook.** Lea lives at `~/.local/src/Lea`; the headless adapter is
   `apps/lea-standalone/adapter/.venv/bin/python run_api.py` (serves
   `http://127.0.0.1:8001`; source the root `.env` first). If startup
   fails: restore `apps/lea-standalone/config/lea.local.toml` from the
   example file. Model keys come from Doppler (`cofounder`/`dev`) into
   the gitignored `.env` — never commit keys, SQLite, or
   `apps/lea-standalone/data/`. SafeVerify binary:
   `prover/third_party/SafeVerify/.lake/build/bin/safe_verify` (Lean
   4.29 both sides; rebuild files in a 4.29 scratch when the repo pin
   differs). Full method: `.cursor/skills/lea/SKILL.md`.
5. **Waves.** One lemma file, one lane, one PR, squash on green build;
   the INT PR banks aggregator imports, labels, docs; the receipt PR
   banks SafeVerify verdicts. A lane may not relabel its own work
   verified.

## Start-here pointers

- System design: `docs/system_design.md`
- Module catalog: `docs/module_explainer.md`
- Human README: `README.md`
- Verification index: `docs/verification.md`
- Modal handoff: `docs/next_agent_modal_handoff.md`
- SIC / Lea continuation: `docs/next_agent_lea_handoff_2026-08-17.md`
- Lea skill: `.cursor/skills/lea/SKILL.md`
- Active ledger: `TODO.md`
