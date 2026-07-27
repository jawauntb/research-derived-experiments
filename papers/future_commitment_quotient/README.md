# The Coordinates Are Not the Causal Object

This bundle contains the manuscript, generated figures, and deterministic PDF
for the preregistered Future-Commitment Quotient study.

The scoped result is exact: in three deterministic finite-agent families,
coordinate-destroyed conjugacies preserve every registered future commitment,
while coordinate-preserved delayed transition mutants change the exact
commitment-bisimulation quotient. The formal core is classical automata and
bisimulation mathematics, not a novel quotient theorem.

Rebuild from committed public results:

```bash
uv run --no-sync python scripts/make_future_commitment_quotient_figures.py
uv run --no-sync python scripts/build_future_commitment_quotient_pdf.py
```
