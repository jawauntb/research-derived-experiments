# Concerned Ontology Haskell Gate

This prototype is the typed formal-methods side of Phase / Arc 2B. Python keeps
owning experiments, learners, Modal orchestration, and report generation. The
Haskell package owns a small typed ontology for computational body motifs and
emits machine-readable verdicts.

Run:

```bash
cabal test all
cabal run ontology-check
```

The current checker is intentionally small: it validates dependency, resource,
input-body, shortcut, and restless-probing rules for the body motifs used in
the Arc 2A/2B vector experiments. The next step is to make Python consume the
JSON verdicts directly, then move more ontology constraints from Python into
this typed layer.
