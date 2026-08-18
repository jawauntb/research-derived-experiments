# dial_nestedness

Review item 2 on "Intention Is All You Need" v3
(`docs/intention_essay_v3_corrections.md`): Theorem B's "as D grows
the cells coarsen" implied nested rate-distortion optima. This
instrument enumerates all 52 partitions of a registered five-point
world under task-relative worst-case distortion and settles it:

- Optimal rates on the grid (0, ¼, ½, ¾, 1): **5, 3, 2, 2, 1** —
  the rate falls, which is the only wording the essay may export.
- The D = 0 optimum is uniquely the level-set partition (matching
  the kernel-checked `DialZero.lean`).
- **All-optimizer nesting fails**: a `{01}{23}{4}` optimizer at ¼
  does not refine a `{012}{34}` optimizer at ½ (witness recorded).
- **A chosen chain nests**: `singletons → {0}{12}{34} → {012}{34} →
  {012}{34} → {01234}`. Nesting is a *selection* fact — the
  disclosed-choice lesson of κ_screen and the D13 repair, recurring
  at the dial.

Verdict: `nestedness_fails_generally`.

Run:

```bash
python3 experiments/dial_nestedness/experiment.py
python3 -m unittest tests.test_dial_nestedness
```

Paper: `papers/dial_nestedness/paper.md`. Not Paper G.
