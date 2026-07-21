---
title: Envelope Guard Product + CT Stress + CHS1 Handoff
type: feat
date: 2026-07-21
artifact_contract: ce-handoff/v1
artifact_readiness: implementation-ready
execution: code-and-experiments
repository: jawauntb/research-derived-experiments
prior_handoff: docs/next_agent_grounded_harness_experiments_handoff_2026-07-20.md
resume_focus: product contract editor; powered CT OOD/multi-model; author-blind CHS1
---

# Envelope Guard Product + CT Stress + CHS1 Handoff

> Start from a fresh fetch of `origin/main` and an isolated worktree. Do not
> edit the primary checkout or work directly on `main`.
>
> Human director: Jawaun Brown. Agent-generated code, results, and papers remain
> under his direction and review.
>
> Prior CT packaging handoff is **complete** (see completion status in
> `docs/next_agent_grounded_harness_experiments_handoff_2026-07-20.md`). This
> document is the next tranche: three parallel programs that were explicitly
> left optional after CT ship.

## Mission

Implement, run, learn from, and report back on three tracks:

| Track | Name | Goal |
|---|---|---|
| **1** | Product — Envelope Guard | Turn the public demo into a usable child-contract tool people can paste into real orchestrators |
| **2** | Science — CT stress | Powered multi-model + harder OOD wording/depth under name-free harness-v2 |
| **3** | Science — CHS1 | Author-blind human-withheld six-surface sealed Counterfactual Harness Search |

Do **not** reopen the closed CT claim boundary. Do **not** claim model-side
constraint learning or Harness Unlearning. HU remains out of scope unless a
later handoff opens it.

## Audited baseline (as of 2026-07-21)

| Surface | State on `main` | Boundary |
|---|---|---|
| CT live-eval | Name-free harness-v2; D2 held-out + D3 confirmatory δ = +1.0, CI [1.0, 1.0]; OOD paraphrase smoke; Haiku smoke | Claim is **harness enforcement**, not model learning |
| Public datasets | `experiments/grounded_statecharts/results/d2_pilot_public/`, `d3_ct_confirmatory_public/` | Sanitized only |
| Preprint / brief | `docs/papers/grounded_harness_*` + PDFs `33_*.pdf`, `33b_*.pdf` | Claim-bounded |
| Envelope Guard site | `sites/envelope_guard/` live at https://envelope-guard-production.up.railway.app | Interactive bench only; no paste-your-contract editor yet |
| CHS bridges | Injected faults, equal-budget repair search, withheld-at-score-time | **Not** author-blind CHS1 |
| Railway Actions | Atlas redeploy works; Envelope Guard / Inquiry fail if `RAILWAY_TOKEN` lacks project access | CLI deploy already shipped the site |

Credentials for live science (Tracks 2–3): Doppler `cofounder` / `dev`
(`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, Modal as needed). Never commit secrets
or `artifacts/` dumps.

Default live env (name-free gates only):

```bash
export GROUNDED_HARNESS_LIVE=1
export GROUNDED_HARNESS_PROVIDER=openai
export GROUNDED_HARNESS_MODEL=gpt-4.1-mini
# optional weak-prompt ablation:
# export GROUNDED_HARNESS_WEAK_PROMPT=1
# NEVER for gate claims:
# export GROUNDED_HARNESS_LABELED_PROMPT=1
```

---

## Discovery frame (shared)

### Current frame

Reliability for recursive agents comes from **external, evidence-scored child
contracts** (capability envelopes + artifact grafts), not from asking the model
to name or remember constraint labels.

### Assumption ledger

1. Name-free prompts remove the labeled-scaffold artifact that killed early D2.
2. `condition_policy.py` / `sites/envelope_guard/policy.js` are the authoritative
   enforcement surfaces; scoring uses applied evidence, not condition strings.
3. CT δ ≈ +1.0 under current tasks may be **easy-regime**; OOD wording/depth and
   other models can shrink it.
4. CHS attribution requires **labels sealed before score-time search**, ideally
   author-blind across six harness surfaces.
5. Product value is the **receipt + contract editor**, not another research chart.

### Anomaly map

- Labeled D2 looked strong → weak-prompt ablation → both effects 0.0.
- GS stayed narrowed after harness-v2; do not escalate GS in this tranche.
- HU live smoke: kill clean but **null** unlearning signal — leave closed.
- Actions `RAILWAY_TOKEN` unauthorized for Envelope Guard project.

### Claim boundary (do not cross)

**Allowed:** External guards recover joint success after capability widenings
under name-free prompts via harness enforcement; product can emit audit
receipts for child contracts.

**Forbidden without new severe evidence:** “Model learned constraints,”
“unlearning works,” “CHS finds the true fault in the wild” (needs Track 3),
“product replaces production security review.”

---

# Track 1 — Product: Envelope Guard contract editor

## Intent

Make https://envelope-guard-production.up.railway.app a tool people can use:

1. Declare a child contract (required / forbidden capabilities, optional
   required artifact).
2. Simulate a child action (obey / widen / claim-without-artifact / refuse).
3. Compare soft-prompt vs external guards.
4. Export a **receipt JSON** suitable for orchestrator logs / CI.

## Implement

### 1.1 Contract editor UI (`sites/envelope_guard/`)

Add to the existing whitelist static site (no build step, keep Node
`server.js` whitelist):

- Form fields: `required_capabilities` (comma/chip list),
  `forbidden_capabilities`, optional `required_artifact`, task blurb (free text,
  not used for scoring — display only).
- Preset buttons that load current `scenarios.json` cases.
- “Export receipt” downloads / copies JSON:

```json
{
  "product": "envelope_guard",
  "schema_version": "eg-receipt/v1",
  "contract": {
    "required_capabilities": ["delegate", "read_notes"],
    "forbidden_capabilities": ["shell_exec", "network_fetch"],
    "required_artifact": null
  },
  "provider_action": "delegate_with_widened_capability",
  "mode_comparison": {
    "soft_prompt": { "evidence": {}, "scores": {} },
    "external_guards": { "evidence": {}, "scores": {} }
  },
  "policy_digest": "...",
  "claim_boundary": "Harness enforcement of child envelope; not model learning."
}
```

Keep `policy.js` as the single browser policy implementation; stay aligned with
`experiments/grounded_statecharts/condition_policy.py`. If Python policy
changes, update `policy.js` + `tests/policy.test.js` in the same PR.

### 1.2 Optional “orchestrator stub” (same PR or follow-up)

Small documented example under `sites/envelope_guard/examples/receipt_consumer.md`
showing how to reject a child run when `joint_success` is false or when
`enforcement_applied` is true but operator policy forbids silent strip. Do **not**
add a live LLM backend to the public site in this tranche (keeps deploy simple
and secret-free).

### 1.3 Deploy

```bash
cd sites/envelope_guard
railway up --project 31f7bc34-f4f0-4782-8a95-7ca3f4d8b5cb \
  --environment 94ccae54-a7b2-4436-9093-17f82d3b605a \
  --service 7f247461-7ddc-4cb6-8d85-6966b1dce6d0 --ci
```

Domain: `https://envelope-guard-production.up.railway.app`

If GitHub Actions deploy is desired: replace repository secret `RAILWAY_TOKEN`
with a **workspace/account** token that can access projects
`envelope-guard`, `inquiry-black-box-site`, and `reafference-attribution-field`.
Project-scoped atlas tokens will keep failing Envelope Guard / Inquiry.

### 1.4 Tests / docs

- Extend `sites/envelope_guard/tests/policy.test.js` for custom contracts.
- Update `docs/system_design.md` + `docs/module_explainer.md` (AGENTS.md).
- Smoke: curl site 200; manual export receipt once.

## Run

1. Local: `cd sites/envelope_guard && npm start` (port 3020).
2. Exercise presets + a custom forbidden list including `shell_exec`.
3. Widen under soft vs guards; confirm soft `joint_success=false`, guards true +
   `enforcement_applied=true`.
4. Deploy via Railway CLI; verify production export.

## Learn

Record in the report-back (template below):

- Did users (or the director) understand the claim boundary from the UI alone?
- Was the receipt schema missing fields an orchestrator would need
  (`org_id`, run id, timestamps)?
- Any mismatch between `policy.js` and `condition_policy.py`?

Kill / pivot Track 1 if the editor stays a chart and nobody can export a usable
contract without reading the research paper.

## Report back (Track 1)

Open a short PR comment or `docs/` note `docs/envelope_guard_product_report_YYYY-MM-DD.md` with:

1. Demo URL + screenshot or pasted sample receipt.
2. Schema version and field list.
3. One “would use in orchestrator” checklist result (pass/fail per item).
4. Open issues / next product cut.

---

# Track 2 — Science: CT stress (multi-model + harder OOD)

## Intent

Ask whether the CT joint-success effect **survives** harder wording/depth and
at least one additional model family under name-free harness-v2 — or whether
δ ≈ +1.0 was an easy-regime artifact.

## Preregister before live spend

Create (commit before any scored live run):

`experiments/grounded_statecharts/LIVE_CT_STRESS_PREREGISTRATION.md`

Must freeze:

- Models: at least `gpt-4.1-mini` and one Anthropic model already smoked
  (`claude-haiku-4-5-20251001` or newer declared equivalent).
- Families: `recursive_constrained_tool_use` (CT primary). GS stays diagnostic-only.
- Conditions: soft/self-report vs `envelope_external_guards` (name-free prompts).
- OOD axes (minimum two):
  1. **Wording paraphrase** harder than the existing live smoke (new templates;
     no condition names).
  2. **Depth** escalation (deeper delegation than D3 cells, within budget).
- Sample size: powered estimate from D3 variance; if CI half-width target is
  unknown, start with a **predeclared** pilot N and a confirmatory N, never
  peek-then-resize.
- Primary endpoint: CT `joint_success` δ (guards − soft) with cluster bootstrap.
- Kill criteria (predeclared):
  - δ < 0.15 on either model under name-free prompts → **do not escalate** CT
    product claims for that model;
  - any labeled-prompt or condition-name leakage in prompts → run invalid;
  - integrity / budget / sanitization failure → discard rows.

## Implement

1. Extend OOD task generators / manifests under
   `experiments/grounded_statecharts/` (follow existing
   `run_constraint_ood_smoke` and D3 confirmatory patterns).
2. Multi-model adapter path already exists (`GROUNDED_HARNESS_PROVIDER` /
   `MODEL`); add a thin runner that loops the frozen matrix and writes
   gitignored `artifacts/grounded_statecharts/ct_stress_*/`.
3. Public-safe publish path: sanitize → `results/ct_stress_public/` (or dated
   sibling) with summary, rows, allowed claim, non-claims.
4. Tests for manifest validation + sanitization; no live calls in CI.

## Run

```bash
# after preregistration committed
doppler run -p cofounder -c dev -- \
  env GROUNDED_HARNESS_LIVE=1 \
      GROUNDED_HARNESS_PROVIDER=openai \
      GROUNDED_HARNESS_MODEL=gpt-4.1-mini \
  python3 -m experiments.grounded_statecharts.<ct_stress_runner>
# then Anthropic matrix cell with provider/model swapped
```

Never set `GROUNDED_HARNESS_LABELED_PROMPT=1` for gate rows. Optional weak-prompt
ablation may be run as a **secondary** check only.

## Learn

Compare observed vs preregistered predictions:

| Prediction | If true | If false |
|---|---|---|
| Guards still beat soft on hard paraphrase | CT claim transports across wording | Narrow claim to “easy paraphrase only” |
| Guards still beat soft at deeper depth | Depth is not the failure mode | Cap supported depth in product docs |
| Effect replicates on Haiku-class model | Cross-provider operational claim | Model-scope the claim |

Update claim strength in preprint/brief **only** with an explicit amendment PR
that cites the preregistration and public rows.

## Report back (Track 2)

File: `docs/ct_stress_report_YYYY-MM-DD.md` (or PR body) containing:

1. Link to preregistration + manifest hash.
2. N episodes per cell; integrity pass rate.
3. Primary δ + CI per model × OOD axis.
4. Kill criteria triggered? yes/no + which.
5. Revised allowed claim (one paragraph) and non-claims.
6. Whether Envelope Guard product copy needs a depth/model caveat.

---

# Track 3 — Science: CHS1 author-blind six-surface seals

## Intent

Move from synthetic/bridge CHS to **author-blind** Counterfactual Harness
Search: sealed fault labels across six harness surfaces, score-time search that
does not see labels, attribution vs placebo/non-interventional baseline.

Existing bridges (do not confuse with CHS1):

- `results/chs_injected_faults/`
- `results/chs_repair_search/`
- `results/chs_withheld_seals/`
- `results/chs_withheld_seal_search/`

## Preregister before sealing

Create:

`experiments/grounded_statecharts/CHS1_PREREGISTRATION.md`

Freeze:

- Six surfaces (align with existing injected-fault taxonomy in the package).
- Label protocol: human or independent agent seals labels **before** search;
  labels live in a sealed artifact not readable by the search runner.
- Equal evaluation budget for repair vs placebo vs passive baseline.
- Primary endpoint: exact or ranked attribution accuracy / causal credit vs
  chance and vs non-interventional baseline.
- Kill criteria:
  - attribution ≤ chance or ≤ strong passive baseline → **no causal CHS claim**;
  - any leakage of sealed labels into prompts, filenames visible to search, or
    score-time features → run invalid;
  - budget mismatch across arms → run invalid.

## Implement

1. Harvest or synthesize **live-mediated** failure candidates from CT/GS rows
   (prefer real failures; synthetic only if labeled as such and not mixed into
   the CHS1 confirmatory claim).
2. Sealing tool: write sealed labels + hash; search runner receives only
   unlabeled traces + intervention API.
3. Equal-budget repair search loop (extend
   `chs_withheld_seal_search` / repair-search code paths rather than forking a
   third stack).
4. Public bundle: `results/chs1_public/` with aggregation that cannot unseal
   individual human-identifying content.
5. Fixture tests for seal integrity (search process cannot read label file).

## Run

1. Commit preregistration + sealing schema.
2. Seal set A (held-out). Record seal hash.
3. Run search arm + placebo + passive baseline at matched budget.
4. Unseal only after scores frozen; compute attribution metrics.
5. Publish sanitized summary; keep raw seals out of git if sensitive.

## Learn

| Outcome | Interpretation |
|---|---|
| Attribution ≫ chance and ≫ passive | Escalate CHS claim carefully; still not “production root-cause AI” |
| Attribution ≈ chance | CHS remains a synthetic/bridge result; product should not advertise fault finding |
| Works only on injected faults, fails on live-mediated | Narrow claim to synthetic identifiability |

## Report back (Track 3)

File: `docs/chs1_report_YYYY-MM-DD.md` containing:

1. Seal hash + N cases per surface.
2. Attribution vs chance vs passive (+ CIs if stochastic).
3. Kill criteria triggered?
4. Allowed claim / non-claims for CHS.
5. Whether Track 1 product should mention CHS at all (default: **no** until kill
   criteria clear).

---

## Parallelism and ordering

Recommended cadence (can parallelize agents):

```text
Week slice A (parallel):
  Track 1 UI/receipt  |  Track 2 preregistration + generators  |  Track 3 preregistration + seal schema

Week slice B (parallel after A):
  Track 1 Railway deploy + report  |  Track 2 live matrix  |  Track 3 seal + search (no unseal yet)

Week slice C:
  Track 2 report + claim amendment if warranted
  Track 3 unseal + report
  Cross-track: update Envelope Guard copy from science caveats
```

Hard rules:

- Tracks 2 and 3: **preregister before peeking**.
- Track 1 must not wait on Track 3.
- Do not block Track 2 on Railway Actions token; use CLI deploy for the site.
- Prefer small atomic PRs: product site; CT stress prereg; CT stress results;
  CHS1 prereg; CHS1 results.

## Verification before every merge

```bash
python3 scripts/run_quality_checks.py   # substantive Python
# site-only:
cd sites/envelope_guard && /usr/local/bin/node --test tests/policy.test.js
python scripts/gen_provenance.py        # when experiment results/commands change
```

Update `docs/system_design.md` and `docs/module_explainer.md` for any meaningful
surface change. Refresh provenance when run commands or public results change.

## Report-back template (all tracks)

Each track’s report must include:

1. **What was implemented** (paths, PR links).
2. **What was run** (commands, N, models, dates).
3. **What was learned** (vs preregistered predictions; anomalies).
4. **Claim update** (allowed / narrowed / killed).
5. **Where human input is needed** (token, label sealing, spend approval, copy).
6. **Next best test** (one sentence).

Ping the director when a track’s report lands and when a kill criterion fires.

## Completion definition for this handoff

This handoff is complete when:

1. Track 1: production site exports `eg-receipt/v1` from a custom contract; short
   product report filed.
2. Track 2: preregistration + executed matrix + public-safe summary + stress
   report with kill verdict.
3. Track 3: preregistration + sealed run + unblinded metrics + CHS1 report with
   kill verdict.

Partial completion is fine if reports explicitly mark which tracks finished and
which are blocked (and on what).

## Start-here commands

```bash
git fetch origin main --prune
# worktree / branch off origin/main

# Track 1 local
cd sites/envelope_guard && npm start

# Track 2 / 3 live (after prereg)
doppler run -p cofounder -c dev -- printenv OPENAI_API_KEY >/dev/null
```

Primary code anchors:

- Product: `sites/envelope_guard/`
- Policy (Python): `experiments/grounded_statecharts/condition_policy.py`
- Live adapters: `experiments/grounded_statecharts/adapters/`
- Prior CT handoff: `docs/next_agent_grounded_harness_experiments_handoff_2026-07-20.md`
- Brief: `docs/papers/grounded_harness_brief_2026-07-20.md`

Make Tracks 1–3 goals. Work until each has a report-back. Parallelize where
safe. Prefer killing weak claims over stretching them.
