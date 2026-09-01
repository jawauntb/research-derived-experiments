# Provenance

## Upstream code reuse

### MIDAS

- **Upstream**: https://github.com/ebarnes-ry/MIDAS
- **Local checkout used as reference**: `~/MIDAS` (as of 2026-08-31)
- **Reuse permission**: Granted verbally by MIDAS's author to Jawaun Brown, relayed on 2026-08-31.
- **Scope of permission (as relayed)**: source reuse for this project (`bio-claim-firewall`).
- **What we intend to lift**:
  - Typed intermediate step dataclasses.
  - Generate → Execute → Analyse verifier contract.
  - Separation between a domain-fault (verifier disproved a step) and a checker-fault (contract violation, timeout, crash).
  - Versioned Jinja2 prompt system.
  - JSONL trajectory logger.
  - `ModelManager` abstraction over local (Ollama) and remote (OpenAI-compatible) providers.
- **What we will not reuse without further review**: Marker/VLM vision pipeline, SymPy execution sandbox (biology-inappropriate), student-feedback prompt (math-specific), FastAPI surface (out of scope until Phase 3+).
- **Attribution obligation**: Retain author credit in the README, mark MIDAS-derived files with a header comment linking upstream, and cite in any paper that describes the verifier architecture.

### Pending written trace

The verbal permission is enough to unblock scaffolding. Before any code that reuses MIDAS source lands in a commit intended to be published, at least one of the following must be attached to this file:

- A LICENSE file added to the MIDAS upstream repository.
- A dated email or written message from MIDAS's author granting the reuse, archived under `bio-claim-firewall/legal/`.

Until then, MIDAS-derived files stay in unpublished commits or private branches only.

## Data snapshots

Phase 2 froze six real, hash-verified pilot-world sources on 2026-08-31:

- `hgnc.2026_pilot`: 45,045 HGNC CURIEs plus 3,449 merge aliases (CC0-1.0).
- `ncbitaxon.2026_pilot`: seven NCBI Taxonomy terms (Public Domain).
- `cellontology.2026_pilot`: 3,335 Cell Ontology CURIEs with an `is_a` closure (CC-BY-4.0).
- `cellline.2026_pilot`: seven Cell Line Ontology terms (CC-BY-4.0).
- `reactome.2026_pilot`: 2,012 human Reactome pathway CURIEs and 20,000 memberships (CC0-1.0).
- `perturbseq.replogle_2022`: 9,400 K562 perturbation-effect records sampled from Replogle et al. 2022 (CC0-1.0).

Each JSON manifest in `data/manifests/` records its source URL, retrieval timestamp,
license, SHA-256, preprocessing command, schema version, and row count. The complete
sampling and substitution rationale is in `data/README.md`; the reproducible download
and manifest build commands are in `data/scripts/`.

## Evaluation receipts

### Context-rule mutation coverage — 2026-09-01

- **Target**: the six context guards in `src/rules/sections/_shared.py`, including the
  formerly surviving R-CTX-02 ancestor and R-CTX-05 assay-equivalence `delete_line`
  mutants.
- **Command**: `cd bio-claim-firewall && uv run --no-sync python -m eval.mutation --limit 6 --report /tmp/bcf-context-mutation-2026-09-01.md`.
- **Result**: 18/18 mutants killed; 0 survived; 0 skipped. The report is intentionally
  local scratch output; the reproducible test assertions are committed in
  `tests/rules/test_r_ctx.py`.
