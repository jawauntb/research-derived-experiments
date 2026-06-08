# Discovery-Regime Audit Ledger

## Project Regime: Initial Publication

Question: how do we turn the paper synthesis into a public, reproducible research workspace without publishing local-only source archives or secrets?

Current regime:

- Artifact types: synthesis notes, source manifest, TODO ledger, experiment scripts, result JSON, audit cards, rejected alternatives.
- Operations: source archiving, text extraction, synthesis, synthetic simulation, env probing, publication guard, GitHub PR workflow.
- Gates/verifiers: no tracked files over 10 MB, no tracked local source archives, no obvious secret values, Python unit tests, syntax checks, publication guard, human review.
- Known limitations: paper PDFs and full extracted text are local-only; Authorea blocked direct download, but a local PDF with the same DOI is archived.

Action class:

- Retrieval/search/discovery: retrieval plus initial search.
- Why: publication adds already representable artifacts; the first synthetic experiment searches inside the weakness-vs-simplicity schema.

Gate:

- Acceptance rule: public repo can be pushed without large files, full extracted corpora, or secrets; first experiment produces deterministic output and unit tests pass.
- Withheld/rejected rule: full PDFs, extracted text, raw API outputs, and any secret-bearing artifacts stay untracked.

Results:

- Accepted artifacts: `experiments/weakness_vs_simplicity/results/pilot_2026_06_08.md`.
- Rejected or withheld artifacts: `references/papers/`, `references/text/`, `references/html/`.
- Key metrics: trap condition weakness mean Jaccard 0.9533; simplicity mean Jaccard 0.0938; random mean Jaccard 0.5061. No-memorizer control weakness mean Jaccard 0.9587; simplicity mean Jaccard 0.9493.
- Variance or ablation: no-memorizer control added; unsafe broad-hypothesis stress test pending.

Residual content:

- Explained by old regime: source collection and synthesis.
- New content outside old regime: none yet.
- Retractions or supersessions: none.

Environment note: `superoptimizers` has Doppler project `cofounder` / config `dev` configured. Presence-only probe found OpenAI, Anthropic, Gemini, Hugging Face, and Modal token variables available. No secret values are recorded here.

Next move: publish via feature branch and PR, then add negative controls for the first benchmark.
