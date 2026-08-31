# Fault taxonomy

The verifier assigns exactly one `fault_code` on `REJECTED`. Codes are a **closed** enum — any new code requires a schema-version bump, a new rule id, and a mutation test (Phase 5, §A). No code may be added because "the model kept doing something weird"; that is a proposer problem, not a checker gap.

Verdicts are separated on two axes:

|                                 | Contract violated by the **claim**                        | Verifier itself broke                |
|---------------------------------|-----------------------------------------------------------|--------------------------------------|
| Deterministic under snapshot    | `REJECTED_<FAULT_CODE>`                                   | `CHECKER_ERROR` (**fail closed**)    |
| No rule applies but no violation| `INCONCLUSIVE`                                            | —                                    |

`CHECKER_ERROR` is never silently converted into `REJECTED_*`. The distinction is inherited from MIDAS's split between a *reasoning fault* (math actually wrong) and a *codegen fault* (verifier broke), and is the load-bearing invariant of this system.

## Codes

### `UNKNOWN_ENTITY` — R-ENT-*

**Trigger.** Any `subject.id` / `object.id` in the claim, or the `species` CURIE, or the `cell_context.cell_type` CURIE does not resolve in the frozen ontology snapshot (or in the identifier-alias records for known deprecations).

**Not-triggers.** Label / id mismatch alone is a soft warning, not this fault. A valid CURIE in a *disabled* prefix (see `inference_rules.md §Allowed prefixes`) triggers this, not `INVALID_RELATION`.

**Adversarial example.** `{"id": "HGNC:9999999", "label": "MADEUPKINASE"}`.

**Mutation test (Phase 5).** Delete the resolver's snapshot-membership check → suite must fail.

---

### `INVALID_RELATION` — R-REL-*

**Trigger.** `relation` is not in the permitted grammar for the given `record_type` pairing, or the `polarity` is inconsistent with the relation (e.g. `polarity=positive` for `binds`).

**Adversarial example.** `{"relation": "regulates_epigenetically", ...}` (not in the enum), or `{"relation": "binds", "polarity": "negative"}`.

**Mutation test.** Widen the relation enum by one → the schema round-trip test must fail.

---

### `UNSUPPORTED_EDGE` — R-EDGE-*

**Trigger.** No record in `evidence_ids` licenses the (subject, relation, object) triple under any interpretation permitted by `inference_rules.md`.

**Distinct from `BAD_CITATION`.** The evidence ids resolve; they just don't support this edge.

**Adversarial example.** Cite a pathway-membership record to justify a direct `binds` claim between two genes in that pathway.

**Mutation test.** Drop the record-type / relation compatibility table → suite must fail on the smallest positive example.

---

### `SIGN_MISMATCH` — R-SIGN-*

**Trigger.** The evidence record's `effect.sign` disagrees with the claim's `polarity` (positive vs negative), under the same context and after applying the relation's sign convention (`increases` = positive effect, `decreases` = negative effect).

**Adversarial example.** Claim `A increases B` while the cited evidence records `effect.sign=negative` for the perturbation of A on B.

**Mutation test.** Invert the sign-comparison in the rule engine → any positive example flips to accepting the wrong sign.

---

### `CONTEXT_MISMATCH` — R-CTX-*

**Trigger.** The claim's `species`, `cell_context.cell_type`, `cell_context.cell_line`, `cell_context.state`, `assay_context.assay`, or `assay_context.perturbation` differs from the evidence record's corresponding field, and no rule waives the difference.

**Waivers (see `inference_rules.md`).** `cell_line=null` accepts any line under the same cell_type at status ≤ `hypothesis`. `state=null` accepts any state at status ≤ `hypothesis`.

**Adversarial example.** Cite a K562 perturbation record for a claim tagged with `cell_line=CLO:...RPE1...`.

**Mutation test.** Force the context comparator to always return equal → any context-swapped test must be caught by the suite.

---

### `CAUSALITY_OVERCLAIM` — R-CAUS-*

**Trigger.** `relation=causes`, or `confidence_language=causal`, with any cited record having `observation_type=observational`. Also: `relation=causes` without an interventional perturbation in `assay_context.perturbation`.

**Adversarial example.** Claim `A causes B` citing a co-expression correlation from bulk RNA-seq.

**Mutation test.** Allow `observational` to license `causes` → smallest correlational example accepts wrongly.

---

### `SCOPE_OVERCLAIM` — R-SCOPE-*

**Trigger.** `requested_status=established` while the evidence is single-study, single-context, or single-perturbation and the inference rule for that relation requires multi-context replication for the `established` tier.

**Adversarial example.** One K562 perturbation record → `requested_status=established`, universal wording.

**Mutation test.** Remove the replication-count check → single-study claim promotes to established.

---

### `CONTRADICTED` — R-CONTRA-*

**Trigger.** Some evidence record in the same source, same context, has `contradicts` linking to a record the claim depends on, or a directly-conflicting record exists under the same (subject, relation, object, context) with higher-priority observation_type (`interventional` > `observational`).

**Adversarial example.** Claim cites an observational co-expression while an interventional record with `sign` opposite exists in the same cell type.

**Mutation test.** Disable the contradiction lookup → the paired positive test must fail.

---

### `BAD_CITATION` — R-CITE-*

**Trigger.** Any `evidence_ids[i]` does not resolve in the frozen evidence ledger, or its `snapshot_hash` does not match its manifest's sha256.

**Distinct from `UNSUPPORTED_EDGE`.** Here the id itself is bogus (or tampered with).

**Adversarial example.** `evidence_ids: ["pubmed:99999999"]` (nonexistent), or `["perturbseq.replogle_2022:0000000000000000"]` (well-formed but no such record).

**Mutation test.** Bypass the ledger lookup → fabricated citations accept.

---

### `UNSUPPORTED_CERTAINTY` — R-CERT-*

**Trigger.** `confidence_language` exceeds the maximum tier the evidence rule permits for the relation + observation_type + replication combination (see `inference_rules.md §Certainty ladder`).

**Adversarial example.** Single observational record → `confidence_language=causal`.

**Mutation test.** Skip the certainty-ladder check → language freely inflates.

---

### `OUT_OF_SCOPE` — R-SCOPE-90

**Trigger.** The claim is well-formed and its entities resolve, but the relation, tissue, or assay is outside this pilot verifier's declared coverage (see `inference_rules.md §Coverage envelope`).

**Distinct from `INCONCLUSIVE`.** `OUT_OF_SCOPE` says "this verifier is not the right authority for this claim." `INCONCLUSIVE` says "this verifier is the right authority, but under the current snapshot no rule fires either way."

**Adversarial example.** A claim about a plant gene at Phase 2 (human-only pilot world).

**Mutation test.** Remove the coverage-envelope check → plant-species claim gets fully evaluated.

---

## `INCONCLUSIVE` (not a `REJECTED_*` code)

The verifier reaches the end of its rule cascade without any rule accepting or rejecting. This is a distinct terminal state, not a rejection, and never renders as verified.

Common causes: relation is in-scope but no matching evidence record exists in the frozen ledger for that specific (subject, object, context) tuple; the evidence exists but is `observation_type=observational` for a relation whose rule requires `interventional` and no interventional record was found either way (so we can't confirm *or* reject — just refuse to render).

## `CHECKER_ERROR` (not a `REJECTED_*` code)

Something inside the verifier broke: snapshot loader failed, hash mismatch on a manifest, rule-engine raised, verdict formatter refused. Verdict carries `checker_error.stage` and `.message`. Downstream consumers **must** treat this identically to "not verified" and MUST NOT retry silently against a different snapshot.

## Adding a code

To add a new fault code:

1. Bump `verdict.schema.json` and `claim.schema.json` minor version.
2. Add a rule id in `inference_rules.md` in the corresponding section.
3. Add a positive adversarial example and a mutation test to the Phase 5 mechanical suite.
4. Update this file with the new section.
5. All existing accepted claims stay valid; the new code only affects future verdicts.
