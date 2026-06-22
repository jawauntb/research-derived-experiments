# Discovery EWS (reflexive)

A retrospective early-warning proxy applied to **the program itself**, motivated by
the insight literature (Tabatabaeian et al., PNAS 2025) and the realization that the
surprisal early-warning signal is *structurally non-specific*: a breakthrough, a
stable delusion, and losing the plot all look identical on the surprisal curve. The
only discriminator — does the new regime survive transfer and bear external load —
is extrinsic and lagging.

So this tool does **not** score "are we about to break through." It scores the
program's *past* destabilizations: of the times the program jumped to a new/dormant
experiment family (a surprisal spike), what fraction **resolved into a load-bearing
regime** (held-out transfer survival + external anchoring or downstream reuse,
without being failure-dominated) versus merely **self-sealed** (passed its own gates,
no transfer/external) or **dissipated**.

```bash
python3 -m experiments.discovery_ews.discovery_ews --out artifacts/discovery_ews/scan.json
```

Headline (2026-06-18): **spike → load-bearing conversion ≈ 0.12**, dominated by
self-sealing episodes, generativity ratio ~1:1 — a quantitative version of the
"rigorous play in a self-built world" critique. See
`results/scan_2026_06_18.md`, including the **apophenia incident** (v1 mislabeled the
known graveyard "load_bearing" and required extrinsic correction — the detector
modeling the problem it measures) and the documented misclassifications.

This is a lagging mirror, not a warmth meter. The principled next version replaces
regex-over-markdown with the structured gate verdicts experiments already emit.
