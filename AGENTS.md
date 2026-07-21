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

## Start-here pointers

- System design: `docs/system_design.md`
- Module catalog: `docs/module_explainer.md`
- Human README: `README.md`
- Verification index: `docs/verification.md`
- Modal handoff: `docs/next_agent_modal_handoff.md`
- Active ledger: `TODO.md`
