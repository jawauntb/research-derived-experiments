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

None yet. Phase 2 will populate:

- Perturbation dataset (TBD; see `spec/non_goals.md` for selection criteria).
- HGNC / Ensembl gene identifier snapshot.
- Gene Ontology snapshot.
- Pathway source snapshot (Reactome or equivalent, license permitting).

Each snapshot will get a manifest entry with source URL, retrieval date, license text, SHA-256 of the raw file, preprocessing command, schema version, and row count.
