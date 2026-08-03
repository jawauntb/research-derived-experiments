# Representation Search (Fiber Finder)

Instrument 1 of the Structural Observatory (see
[`notes/structural_intelligence_conjecture.md`](../../notes/structural_intelligence_conjecture.md)).

Hypothesis: intelligence's central move is not to predict the answer but to
discover the quotient `q : X → Z` in which a hidden invariant becomes manifest.
The right representation is the one that (1) loses no task-relevant information —
`H(Y | q(X)) = 0`, the target descends to the quotient — while (2) confining all
irrelevant variation to the fibers `q⁻¹(z)` — maximal compression. This is the
counit-fidelity-then-compress rule of the meta-framework.

Method: over a tiny Boolean world (all `2ⁿ` worlds, uniform) with a known
ground-truth invariant, enumerate a lattice of candidate quotients (constant,
every-subset parity, identity) and three selectors — `minimal_sufficient`
(sufficient then min description length), `mdl_only` (min description length),
`accuracy_only` (max mutual information, finest). Everything is exact and
deterministic; no sampling, no seed.

Pre-registered gates:

- `minimal_sufficient_recovers_ground_truth`: the sufficient-then-compress
  selector recovers the exact ground-truth invariant in every task.
- `mdl_only_collapses_obstruction`: pure description-length minimization always
  picks an insufficient quotient (it destroys the obstruction).
- `accuracy_only_never_compresses`: pure mutual-information maximization always
  picks the identity (no compression).
- `sufficiency_beats_accuracy_on_compression`: the minimal-sufficient quotient is
  strictly more compressed than the accuracy-only choice.

This is a toy, not a proof: it establishes the *dissociation* between sufficiency,
description length, and accuracy on an exactly solvable case. It is the discrete,
non-interventional core of the **fiber audit** program (extension 4 in the note),
whose interventional version varies degrees of freedom inside a fiber.

Run:

```bash
python3 experiments/representation_search/experiment.py --output experiments/representation_search/results/representation_search_summary.json
```
