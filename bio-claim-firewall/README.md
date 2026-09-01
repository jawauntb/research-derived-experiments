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

## Use it now: local K562 claim checker

The current useful surface is deliberately narrow: check whether one claimed
direction for a perturbed gene and measured gene is supported by **one exact,
frozen Replogle 2022 K562 CRISPRi record**. It is not a general biology
chatbot, prediction system, or clinical tool. It gives a citation, the
decisive verifier rule, and scope conditions when it can answer; it rejects a
sign reversal and returns `INCONCLUSIVE` when no unique frozen record exists.

First reproduce the gitignored pilot snapshot using
[`data/README.md`](data/README.md). Then run the deterministic path (no model
or network access after the local snapshot is present):

```bash
PYTHONPATH=bio-claim-firewall/src uv run --with pyyaml --with pydantic \
  python -m claim_checker MED19 GYPB increases \
  --data-root bio-claim-firewall/data
```

For a one-sentence input, add the optional untrusted OpenAI parser. It needs
`OPENAI_API_KEY` in the environment and its optional runtime dependencies;
the parser may only extract `subject`, `object`, and `direction`. The frozen
ledger and deterministic verifier still decide the result.
It refuses input longer than 2,000 characters before any provider call.

```bash
PYTHONPATH=bio-claim-firewall/src uv run \
  --with openai --with httpx --with tenacity --with truststore \
  --with pyyaml --with jinja2 --with pydantic \
  python -m claim_checker \
  --claim "Does MED19 knockdown increase GYPB expression in K562?" \
  --data-root bio-claim-firewall/data
```

`--json` emits the original question and parsed fields (marked `untrusted_llm`),
provenance for the versioned parser prompt, the constructed claim, exact
evidence (including effect magnitude and whether significance was recorded),
and verifier verdict (including its frozen snapshot hashes). No claim is
accepted merely because a model parsed it. It uses exit `0` for a completed
verdict (including `REJECTED` or `INCONCLUSIVE`), `2` for invalid input, `3`
when the checker is unavailable, and `4` for fail-closed `CHECKER_ERROR`.
`--json` is machine-readable for each of those outcomes, including argument,
input, and availability errors. No-claim `INCONCLUSIVE` outcomes retain the
checker version and the hashes of the frozen snapshots inspected.

## Phase status

- [x] **Phase 1 — Spec.** Claim / evidence / verdict schemas, fault taxonomy, inference rules, non-goals. (#538)
- [x] **Phase 2 — Frozen pilot world.** HGNC (45,045 genes), Cell Ontology, Cell Line Ontology, NCBI Taxonomy, Reactome, Replogle 2022 Perturb-seq (9,400 records). All hash-verified. (#543)
- [x] **Phase 3 — Deterministic verifier.** Audit ledger, normalize, evidence loader, 30-rule cascade, top-level `verify()` composer. Fail-closed. (#539, #540, #541)
- [x] **Phase 4 preview — Untrusted model interfaces.** `Proposer` + `Repairer` + `Orchestrator` + `TrajectoryLogger`; MIDAS-derived `ModelManager` now connects through its prompt-rendering compatibility adapter. One configured OpenAI model has traversed the fixed five-case smoke path. (#542, #548)
- [x] **Phase 5a — Mutation-test framework.** 31 mutation sites discovered; direct R-CTX-02 and R-CTX-05 regressions close the two first-run coverage gaps, with all 18 `_shared.py` context mutants killed. (#542)
- [ ] **Phase 5b — Live-LLM end-to-end + adversarial + empirical suites + independent blinded audit.** The five-case live smoke passed as a narrow operational result; adversarial, multi-model, empirical, and blinded-review gates remain. See [`eval/smoke/RESULTS_2026-09-01.md`](eval/smoke/RESULTS_2026-09-01.md) and [`HANDOFF.md`](HANDOFF.md) §5.

**New agent picking this up: read [`HANDOFF.md`](HANDOFF.md) first.**

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
