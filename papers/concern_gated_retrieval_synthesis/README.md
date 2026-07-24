# Concern-Gated Retrieval — Synthesis Paper

**Paper:** [`paper.md`](paper.md) — *The Concern-Gated Retrieval Program: A
Falsification Arc from Authored Diagnostic to Honest Null*

**Status:** synthesis / terminus of Wave 1. This paper closes the first COGR
arc. Under the program's noncompensatory rules, Waves 2–4 (live beachhead,
substrate transfer, safety) do **not** open on this foundation.

## What this is

A cumulative, paper-by-paper corrective map of the concern-gated retrieval
program. It is not a highlight reel — it is the honest arc showing what each
step established, what it corrected in the prior step, and what killed it or
what it froze. The terminus is a clean L1 falsification with the leakage audits
passing.

## The arc in one line

L0 authored diagnostic (hit@1 `1.000` vs `0.0052`, but the graph encodes the
answer) → Wave 0 wrong-prior calibration + freeze (mechanism collapses ~10×
below baseline under an adversarial prior) → Wave 1a KILL (recency was a covert
oracle: `recency = oracle` byte-for-byte — candidate-selection circularity) →
Wave 1b honest L1 KILL (leakage audits pass p=`0.594/0.366/0.515`;
learned−random mean_delta `≈ 0`; learned edges non-causal).

## Honest terminus

The two-flashlight intuition is not refuted in general, but its
operationalization as rarity-corrected multiplicative PPR over a learned graph
does **not** beat a degree-matched random null at matched budget on these three
families once the fixture stops leaking the answer.

## Source receipts (authoritative)

| Step | PR | Provenance | Analysis hash (prefix) |
|---|---|---|---|
| L0 pilot | #409/#410 | `experiments/concern_gated_retrieval/PROVENANCE.md` | — |
| Wave 0 | #411 | `experiments/concern_gated_retrieval_e2/wave0/PROVENANCE.md` | `9683c5a1…` |
| Wave 1a | #412 | `experiments/concern_gated_retrieval_e2/wave1a/PROVENANCE.md` | `c23b31d9…` |
| Wave 1b | #413 | `experiments/concern_gated_retrieval_e2/wave1b/PROVENANCE.md` | `51ca0219…` |

All numbers in `paper.md` are transcribed verbatim from these receipts. The
provenance skeletons are machine-populated only; manual edits to numeric or hash
fields are forbidden.

## Roadmap / theory

`docs/concern_gated_retrieval_research_program.md` — canonical two-flashlight
theory, the confound ledger (both Spencer circularities), and the gate contract.

## Figures

Built by the figures agent into `figures/`:

- `fig1_arc_ladder` — four-step falsification ladder with verdicts.
- `fig2_advantage_collapse` — L0 advantage vs Wave 1b learned−random delta.
- `fig3_recency_oracle` — Wave 1a recency=oracle byte-for-byte identity.
- `fig4_leakage_audits` — Wave 1b label-permutation p-values vs 0.01 tolerance.
- `fig5_next_arc` — MIDAS-style verifier + failure-frequency exploration prior.

## Next arc (future work)

A single de-risking minimal experiment, not a program: a MIDAS-style symbolic
verifier with a reasoning-fault vs verifier-fault split, plus a care-independent
exploration prior derived from verify-repair failure frequency — aimed directly
at the two circularities (candidate-selection and verifier) that made the easy
version of this claim impossible to trust.
