# Concerned Ontology Haskell Gate

This prototype is the typed formal-methods side of Phase / Arc 2B. Python keeps
owning experiments, learners, Modal orchestration, and report generation. The
Haskell package owns a small typed ontology for computational body motifs and
emits machine-readable verdicts.

Run:

```bash
cabal test all
cabal run ontology-check
cabal run ontology-check -- modular_concerned_body restless_vector_body
cabal run ontology-check -- --motifs vector_surface_encoder,reward_head,causal_binding_head
```

The current checker is intentionally small: it validates dependency, resource,
input-body, shortcut, and restless-probing rules for the body motifs used in
the Arc 2A/2B vector experiments. Named body and motif invocations emit
line-delimited JSON verdicts for Python consumption. Python falls back to its
static verdicts when the local Haskell toolchain is unavailable, but records
`formal_source = "haskell"` whenever the external checker supplies the gate.
