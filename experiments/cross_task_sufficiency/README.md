# Cross-task Sufficiency (Theorem 4 witness)

Instrument 4 of the Structural Observatory (see
[`notes/structural_intelligence_conjecture.md`](../../notes/structural_intelligence_conjecture.md)
and [`papers/structural_intelligence/paper.md`](../../papers/structural_intelligence/paper.md)).

Hypothesis: cross-task stability — the fifth clause of the Structural
Intelligence Conjecture — is not a claim about intelligence but a claim about
the world. If the tasks a system faces all factor through a shared latent
`Z`, then `Z` itself is the coarsest common sufficient statistic (CSS) for
the whole family. If they do not, the coarsest CSS collapses to the identity
(no shared compression). Combining tasks strictly tightens the required
partition: the family CSS is finer than any single task's minimal sufficient
statistic.

Method: exact enumeration on a 4-bit Boolean world (all `2⁴ = 16` worlds,
uniform) with latent `Z(x) = (parity{0,1}(x), parity{2,3}(x))` (a 4-valued
generator). Two task families:

- **Shared through Z:** `parity{0,1}`, `parity{2,3}`, `parity{0,1,2,3}` —
  every task factors through Z.
- **Not shared beyond Z:** the four individual bit reads `bit_0`, `bit_1`,
  `bit_2`, `bit_3` — each task depends on X in a way Z does not resolve.

A rich quotient lattice is enumerated: constant, all subset parities, joint
pair-parities (including Z itself), joint bit reads, and the identity. For
each quotient and each family we compute per-task conditional entropies,
common-sufficiency status, and description length. The coarsest CSS (min
description length among common-sufficient quotients) is selected. Nothing is
sampled; every entropy is exact.

Pre-registered gates:

- `shared_css_equals_latent_Z`: the coarsest CSS for the shared family is
  exactly `joint(parity{0,1}, parity{2,3})` — the latent Z — with image size 4.
- `shared_css_strictly_coarser_than_identity`: the family compresses
  (`image_size < 2⁴`).
- `not_shared_css_equals_identity`: the coarsest CSS for the not-shared family
  is the identity, image size 16.
- `family_css_strictly_finer_than_some_single_task_mss`: the shared family's
  CSS has image size strictly greater than the largest per-task minimal
  sufficient statistic — combining tasks tightens the partition.

This is a toy, not a proof of the general SIC. It establishes the *conditional
theorem* underlying clause (5): cross-task stability holds iff the task family
admits a common Markov screen (a shared generative latent). The instrument
exhibits both the positive direction (shared → CSS is Z) and the collapse
(not shared → CSS is identity) on an exactly solvable case.

Run:

```bash
python3 experiments/cross_task_sufficiency/experiment.py
```
