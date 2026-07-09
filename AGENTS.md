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

## Start-here pointers

- System design: `docs/system_design.md`
- Module catalog: `docs/module_explainer.md`
- Human README: `README.md`
- Verification index: `docs/verification.md`
- Modal handoff: `docs/next_agent_modal_handoff.md`
- Active ledger: `TODO.md`
