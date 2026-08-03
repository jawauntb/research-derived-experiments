# Structure Compiler (one invariant, many verified embodiments)

Instrument 2 of the Structural Observatory (see
[`notes/structural_intelligence_conjecture.md`](../../notes/structural_intelligence_conjecture.md)).

Hypothesis: a structure can recur across substrates but becomes causally
effective only through embodiment, and a compact specification generally selects
an *ensemble* of realizations rather than one. So a single substrate-independent
dynamical structure should compile into several media that are provably "the same
work" — connected by explicit maps whose readback recovers the same abstract
trajectory.

The abstract structure exhibits three motifs: **accumulation** (a level
integrates an input), **phase transition** (a regime flips at an up-threshold),
and **memory as hysteresis** (the down-threshold is lower, so the regime
remembers). Compilers map its trajectory into music (pitch/octave), a visual bar
field (height/hue), text (regime-keyed lexicon, line length ~ level), and spatial
navigation (a corridor with regime-gated edges). Each medium has a readback
`q_i : R_i → S`.

Pre-registered gates:

- `all_media_commute`: for every medium `q_i ∘ F_i = id` on the trajectory
  (fidelity 1.0) — verified structural identity, not mood matching.
- `cross_medium_structural_identity`: all media read back to the *same* abstract
  trajectory.
- `structure_exhibits_phase_transition` and `structure_exhibits_hysteresis`: the
  structure genuinely contains the motifs (a mid-level appears in both regimes).

Honesty note: readback is lossless by construction for these structured encoders,
so fidelity 1.0 tests that the compilers *are* faithful functors, not that
faithful compilation is hard. The interesting open extension is the
**autocatalytic** version (extension 10 in the note): a compiler `Kₜ` that the
experience of `Eₜ` updates, so early movements teach the grammar by which later
movements become legible.

Run (writes SVG/poem/CSV/DOT embodiments to `results/`; `--wav` renders audio to
gitignored `artifacts/`):

```bash
python3 experiments/structure_compiler/experiment.py --output experiments/structure_compiler/results/structure_compiler_summary.json
```
