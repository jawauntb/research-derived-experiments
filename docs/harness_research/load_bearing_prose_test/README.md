# Load-Bearing Prose Test

Status: **scaffolding only** — plan and preregistration frozen 2026-07-21;
no live spend, no confirmatory result yet.

## What this is

A bounded empirical test of the concern-transport bridge theorem applied
to prose produced by LLM agents. Reuses the Constraint Transport (CT)
harness's κ substrate and commitment-surface oracle
(`experiments/grounded_statecharts/condition_policy.py`) to classify
extracted plan claims as **load-bearing** (deleting them changes the
executor's commitment surface) or **available but not load-bearing**
(the framing from `papers/commitment_surface/paper.md`).

## Why it exists

Field default: prose is only verifiable by LLM-as-judge (a
same-faculty judge with correlated errors). This experiment is the
shortest reachable move to test whether the bridge theorem's four
gates — positive concern mass, transport survival, gauge separation,
commitment-surface effect — identify a non-trivial load-bearing subset
of real agent-produced prose against a code-side oracle. A positive
result gives the field a first real prose oracle on a declared
substrate. A negative result publishes as a bounded null.

## Contracts

- **Plan:** [`../../plans/2026-07-21-001-feat-load-bearing-prose-test-plan.md`](../../plans/2026-07-21-001-feat-load-bearing-prose-test-plan.md)
- **Preregistration:** [`../../../experiments/load_bearing_prose_test/PREREGISTRATION.md`](../../../experiments/load_bearing_prose_test/PREREGISTRATION.md) (moved into the package alongside the manifest for provenance tooling)
- **Thesis:** [`../load_bearing_prose_test.md`](../load_bearing_prose_test.md)

## Layout (planned)

Planning documents live under `docs/harness_research/load_bearing_prose_test/`
until the package has a runnable manifest. Week 1 creates the runtime
package under `experiments/load_bearing_prose_test/` together with its
root `experiment_manifest.json` and structured-manifest entry in
`docs/experiment_contract_registry.json` in the same commit:

```
docs/harness_research/load_bearing_prose_test/
    PREREGISTRATION.md
    README.md
docs/plans/2026-07-21-001-feat-load-bearing-prose-test-plan.md
docs/harness_research/load_bearing_prose_test.md

# Created by Week 1 (Step 1) in a follow-on PR
experiments/load_bearing_prose_test/
    __init__.py
    experiment_manifest.json  # root manifest with initial planning run
    claims.py                 # Claim / Ablation / Verdict dataclasses
    extraction.py             # Deterministic + live-model claim extractors
    ablation.py               # delete / negate / paraphrase transforms
    fixtures/                 # Seed plans + expected extractions
    run_lbpt_smoke.py         # Deterministic CI smoke

# Week 2
    executor.py               # CT executor adapter
    scoring.py                # Δ(commitment surface) + verdict rules
    run_lbpt_pilot.py         # Pilot slice runner

# Week 4
    results/lbpt_public/      # Sanitized public dataset
```

## Non-claims

- Not sound in the ATP sense.
- Not a claim about arbitrary domains, models, or task families.
- Not a claim that inert claims are semantically empty.
- Not an extension to long-horizon plan coherence (deferred).
- Not κ inference from arbitrary NL contracts (deferred).
