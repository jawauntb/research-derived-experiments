# bio-claim-firewall

A proof-carrying biological claim system.

An untrusted model proposes a biological claim. A deterministic verifier accepts the claim only when, under a frozen and versioned knowledge snapshot, all of the following hold:

1. Every referenced entity resolves.
2. The claim's relation type is in the permitted grammar.
3. Direction, sign, species, cell context, and assay context match the cited evidence.
4. No higher-priority contradicting record exists under the same context.
5. The claim's confidence language does not exceed what its evidence rule allows.

The verifier returns exactly one of:

- `ACCEPTED_CONDITIONALLY`
- `REJECTED_<FAULT_CODE>`
- `INCONCLUSIVE`
- `CHECKER_ERROR`

`INCONCLUSIVE` and `CHECKER_ERROR` are never rendered as verified. `CHECKER_ERROR` fails closed.

## What this does not do

It does not prove biology. It proves that an accepted claim obeys a locked formal and evidence contract. See [`spec/non_goals.md`](spec/non_goals.md).

## Phase status

- [x] **Phase 1 — Spec.** Claim / evidence / verdict schemas, fault taxonomy, inference rules, non-goals. No biology data touched.
- [ ] **Phase 2 — Frozen pilot world.** One perturbation dataset + separated ontology snapshots. Pending dataset selection and download authorization.
- [ ] **Phase 3 — Deterministic verifier.** Tiny TCB: parser, snapshot loader, identifier resolver, rule engine, verdict formatter, hashing.
- [ ] **Phase 4 — Untrusted model interfaces.** `propose_claims` + `repair_claim`. Ablations.
- [ ] **Phase 5 — Pre-registered validation.** Mechanical + adversarial + empirical suites, mutation tests per fault code, independent blinded audit.

## Provenance

Architectural patterns (typed steps, Generate→Execute→Analyse verifier contract, reasoning/codegen fault separation, JSONL trajectory logger) are adapted from [MIDAS](https://github.com/ebarnes-ry/MIDAS) with reuse permission from its author. See [`PROVENANCE.md`](PROVENANCE.md). The biology domain contract (claim language, evidence records, inference rules, fault codes) is authored fresh here.

## Project layout

```
bio-claim-firewall/
  README.md
  PROVENANCE.md
  spec/                     # Phase 1 — locked before any biology code runs
    claim.schema.json
    evidence.schema.json
    verdict.schema.json
    fault_taxonomy.md
    inference_rules.md
    non_goals.md
  data/                     # Phase 2 — frozen manifests + evidence records
  src/                      # Phase 3 — deterministic verifier
  eval/                     # Phase 5 — pre-registered evaluation suites
```

## Non-goals (see spec/non_goals.md)

No general-purpose biology chatbot. No universal knowledge graph. No new foundation model. No wet-lab execution. No agent swarm. No Lean/Coq formalization before the small deterministic checker earns empirical value.
