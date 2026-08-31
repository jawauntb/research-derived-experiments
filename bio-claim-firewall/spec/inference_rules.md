# Inference rules

The complete rule table the deterministic verifier uses. Every rule has a stable id (`R-<AREA>-<NN>`) that appears in the verdict's `reasons[].rule_id` or `derivation.applied_rules`. The rule engine is a fixed cascade, not a search — if a rule fires, later rules in its group are not consulted for the same claim.

Any change to the rule text or the ordering below is a **checker_version** bump (`verdict.schema.json`).

## §0. Coverage envelope

The Phase 2 pilot world is **human**, **cell-line and primary-cell perturbation and expression data**, and **pathway / GO / HGNC identifier ontologies**. Claims outside this envelope get `OUT_OF_SCOPE` before any other rule runs.

- **R-SCOPE-90.** Reject with `OUT_OF_SCOPE` unless `species == NCBITaxon:9606` (human).
- **R-SCOPE-91.** Reject with `OUT_OF_SCOPE` if the relation requires an assay class not present in any frozen source (e.g. `binds` requires a physical-interaction source; if none is snapshotted, all `binds` claims are `OUT_OF_SCOPE`, not `INCONCLUSIVE`).

## §1. Allowed prefixes

Only these CURIE prefixes resolve. Anything else → `UNKNOWN_ENTITY`.

| Prefix | Class | Snapshot |
|--------|-------|----------|
| `HGNC` | Gene symbol | hgnc.<snapshot_tag> |
| `ENSEMBL` | Gene / transcript | ensembl.<snapshot_tag> |
| `UNIPROT` | Protein | uniprot.<snapshot_tag> |
| `MONDO` | Disease | mondo.<snapshot_tag> |
| `CL` | Cell type | cellontology.<snapshot_tag> |
| `GO` | Gene Ontology term | go.<snapshot_tag> |
| `CHEBI` | Small molecule | chebi.<snapshot_tag> |
| `REACT` | Reactome pathway | reactome.<snapshot_tag> |
| `NCBITaxon` | Species | ncbitaxon.<snapshot_tag> |
| `CLO` | Cell line | cellline.<snapshot_tag> |

- **R-ENT-01.** Reject with `UNKNOWN_ENTITY` if any CURIE's prefix is not in the table above.
- **R-ENT-02.** Reject with `UNKNOWN_ENTITY` if a CURIE's prefix is allowed but the id does not appear in that prefix's frozen snapshot and no identifier-alias record maps it forward.
- **R-ENT-03.** Reject with `UNKNOWN_ENTITY` if `cell_context.cell_type` is a CURIE (not the literal `unspecified`) but does not resolve in the Cell Ontology snapshot.

## §2. Relation grammar

Permitted `(relation, polarity)` pairs and which `record_type`s can license each.

| Relation | Polarity | Licensing record_type | Requires |
|----------|----------|------------------------|----------|
| `increases` | `positive` | `perturbation_effect`, `expression_observation` | evidence.effect.sign == positive |
| `decreases` | `negative` | `perturbation_effect`, `expression_observation` | evidence.effect.sign == negative |
| `binds` | `none` | `physical_interaction` | subject/object appear as a partner pair |
| `expressed_in` | `none` | `expression_observation`, `ontology_annotation` | evidence.subject == claim.subject; cell_type matches |
| `causes` | `positive` \| `negative` | `perturbation_effect` | evidence.observation_type == interventional (see §4) |
| `correlates_with` | `positive` \| `negative` | `expression_observation` | evidence.effect.magnitude_scale in {pearson_r, spearman_r} |

- **R-REL-01.** Reject with `INVALID_RELATION` if `(relation, polarity)` is not a row above.
- **R-REL-02.** Reject with `INVALID_RELATION` if `polarity != none` for `binds` or `expressed_in`.
- **R-EDGE-01.** Reject with `UNSUPPORTED_EDGE` if no cited evidence record has a `record_type` in the licensing set for the relation.
- **R-EDGE-02.** Reject with `UNSUPPORTED_EDGE` if the licensing record type is present but its (subject, object) pair does not match the claim's (subject, object) pair after alias normalization.

## §3. Sign matching

- **R-SIGN-01.** For `increases` / `decreases`: reject `SIGN_MISMATCH` if the cited evidence's `effect.sign` disagrees with the relation's canonical direction.
- **R-SIGN-02.** For `correlates_with` with `polarity=positive`: cited evidence's `effect.magnitude` must be > 0; for `negative`, < 0. Zero or null → `INCONCLUSIVE`, not sign mismatch.

## §4. Causality

The certainty ladder here is deliberately steep.

- **R-CAUS-01.** Reject `CAUSALITY_OVERCLAIM` if `relation == causes` and any cited evidence has `observation_type == observational`.
- **R-CAUS-02.** Reject `CAUSALITY_OVERCLAIM` if `relation == causes` and `assay_context.perturbation` is null.
- **R-CAUS-03.** Reject `CAUSALITY_OVERCLAIM` if `confidence_language == causal` and no cited evidence has `observation_type == interventional`.
- **R-CAUS-04.** For `established` status on a `causes` claim, at least **two** interventional records in different cell lines (or the same cell line across two perturbation modalities, e.g. CRISPRi + siRNA) are required. Single-record `causes` claims cap at `hypothesis` (also fires `SCOPE_OVERCLAIM` if requested_status was `established`).

## §5. Context matching

Fields compared: `species`, `cell_context.cell_type`, `cell_context.cell_line`, `cell_context.state`, `assay_context.assay`, `assay_context.perturbation`.

- **R-CTX-01.** Reject `CONTEXT_MISMATCH` if `species` differs from every cited record.
- **R-CTX-02.** Reject `CONTEXT_MISMATCH` if the claim's `cell_context.cell_type` (when not `unspecified`) is not equal to, or an ancestor of via the Cell Ontology's `is_a` closure of, the cited record's cell_type.
- **R-CTX-03.** Reject `CONTEXT_MISMATCH` if `cell_line` is specified in the claim and does not equal the cited record's `cell_line`. `cell_line=null` in the claim waives this rule but caps status at `hypothesis`.
- **R-CTX-04.** Reject `CONTEXT_MISMATCH` if `state` is specified in the claim and does not equal the cited record's `state` (exact string match). `state=null` waives this rule but caps status at `hypothesis`.
- **R-CTX-05.** Reject `CONTEXT_MISMATCH` if the claim's `assay_context.assay` differs from the cited record's `assay` AND the two assays are not in the same equivalence class in the assay-class table (below).
- **R-CTX-06.** Reject `CONTEXT_MISMATCH` if `assay_context.perturbation` is specified and does not match the cited record's `perturbation` string.

**Assay equivalence classes.**

- `{scRNA-seq, snRNA-seq, bulk-RNA-seq}` all license `expression_observation` and `perturbation_effect`.
- `{CRISPRi_screen, CRISPRa_screen, siRNA_knockdown, ORF_overexpression}` all license `perturbation_effect` at `observation_type=interventional`.
- `{ChIP-seq, CUT&RUN, ChIP-nexus}` license `binds` when subject is a TF and object is a genomic locus.
- `{co-IP, AP-MS, Y2H, BioID}` license `binds` for protein-protein pairs.

## §6. Scope

- **R-SCOPE-01.** Reject `SCOPE_OVERCLAIM` if `requested_status == established` and the accepted evidence set contains only one distinct study id.
- **R-SCOPE-02.** Reject `SCOPE_OVERCLAIM` if `requested_status == established` and the accepted evidence set spans only one `cell_line`. (Same as R-CAUS-04 for `causes`; here it applies to all relations.)
- **R-SCOPE-03.** Reject `SCOPE_OVERCLAIM` if the claim's `cell_context.cell_type` is generalized beyond the cited records' cell_types (e.g. records are all in `CL:0000988` (hematopoietic cell), claim asserts in the broader `CL:0000000` (cell)) without a rule-book entry authorizing that generalization.

## §7. Contradiction

- **R-CONTRA-01.** Reject `CONTRADICTED` if the frozen ledger contains a record with the same `(subject, object, cell_context, assay_context)` and opposite `effect.sign`, whose `observation_type` outranks the cited evidence's (`interventional` > `observational`).
- **R-CONTRA-02.** Reject `CONTRADICTED` if any record in the accepted evidence set carries the cited record's id in its `contradicts` array.

## §8. Certainty ladder

Mapping from evidence available to the maximum `confidence_language` permitted:

| Evidence set | Max confidence_language | Max requested_status |
|--------------|-------------------------|----------------------|
| ≥1 observational record only | `observed` | `hypothesis` |
| ≥1 interventional record, single study | `supported` | `hypothesis` |
| ≥2 interventional records, multiple studies OR multiple cell lines | `suggestive` for correlational relations, `causal` for `causes` | `established` |
| Contradicted by higher-priority record | rejected earlier by R-CONTRA-* | — |

- **R-CERT-01.** Reject `UNSUPPORTED_CERTAINTY` if the claim's `confidence_language` exceeds the row above.
- **R-CERT-02.** Reject `UNSUPPORTED_CERTAINTY` if `confidence_language == causal` and no interventional evidence is cited (subsumes R-CAUS-03; both fire, verdict picks R-CAUS-03 as more specific).

## §9. Citation resolution

Runs before every other §1–§8 rule.

- **R-CITE-01.** Reject `BAD_CITATION` if any `evidence_ids[i]` does not exist in the frozen ledger.
- **R-CITE-02.** Reject `BAD_CITATION` if any cited record's `snapshot_hash` does not equal the sha256 of the raw source file in `data/manifests/`.
- **R-CITE-03.** Reject `BAD_CITATION` if a record's cited `source_citation` is a PubMed / DOI id and that id does not resolve to the study named in the manifest. (Ledger builders enforce this offline; the verifier checks the flag `citation_verified` set by the loader.)

## Rule cascade order

For a given claim, the verifier runs rules in this order and stops at the first that fires:

1. `R-CITE-*` (bad citations poison everything downstream)
2. `R-ENT-*`
3. `R-SCOPE-90..91` (out-of-envelope)
4. `R-REL-*`
5. `R-EDGE-*`
6. `R-CTX-*`
7. `R-SIGN-*`
8. `R-CAUS-*`
9. `R-SCOPE-01..03`
10. `R-CONTRA-*`
11. `R-CERT-*`

If none fire and at least one evidence record positively licenses the edge under matched context: `ACCEPTED_CONDITIONALLY` with the license conditions rendered from the winning record's context fields.

If none fire and no rule positively licenses the edge: `INCONCLUSIVE`.
