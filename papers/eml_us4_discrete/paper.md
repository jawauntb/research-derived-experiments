# US-4′ frozen-leaf half

**Jawaun Brown** (human director) and **Cursor Grok 4.6** (agent, under review)
**Date:** August 17, 2026
**Status:** Φ-predicts-frozen-leaf-rewrite is **supported** at this
bound. Unknown-skeleton GD stays rejected. Neural bootstrap withheld.

## Current frame

Unknown-skeleton GD recovered both registered size-3 targets from 7
trees. The tempting reading is that min-size governs once the tree is
unknown. The protected assumption is that "the process could retune
every `1`-leaf" was an implementation detail.

## Assumption ledger

| Assumption | Type | Load-bearing? | Break test |
|---|---|---:|---|
| Frozen-leaf rewrite still tracks `Φ` | Mechanism | high | Equal extra basins |
| Exact 2-vs-1 is the same claim | Ontology | high | Rank extras, not totals |
| Unknown-skeleton GD already settled this | Ontology | high | Different process |
| A Gibbs draw would be a fair test | Ontology | high | Forbid it |
| Grid agreement is identity | Measurement | high | Require terminals in the exact set |

## Anomaly map

Exact unweighted hits stay **2 vs 1**. Unknown-skeleton GD stayed
**7 vs 7**. Matching-skeleton GD stayed `8/8` vs `6/8`. Those do not
decide this paper. Ranking on total basins would have faked a win
from the exact control alone.

## Candidate reframe

`Φ` is a fact about inhabitants *and about search that cannot retarget
a tree by moving constants*. Unknown-skeleton GD could weight-fit
either target. Frozen-leaf rewrite cannot. At `k=3` that restores a
basin gap.

## Discriminating predictions

| Predictor | `n_extra_basins` |
|---|---|
| `Φ` transfers to this process | zero > thin |
| Min-size / no extra access | equal, including 0 vs 0 |
| `Φ` is the wrong key | thin > zero |

## Severe experiment

Package: `experiments/eml_us4_discrete/`.
Language: all 80 size-3 variable-`x` trees.
Process: greedy descent. Moves: flip one leaf in `{1,x}`, or swap the
two children of one internal node. Leaves never become free weights.

Fatal gates (all passed):

| Gate | Fact |
|---|---|
| `US4D_ENUMERATION` | 80 trees |
| `US4D_EXACT_CONTROL` | unweighted 2 vs 1 |
| `US4D_FROZEN_LEAVES` | leaves stay `{1,x}` |
| `US4D_NOT_GD` | rewrite disclosure |
| `US4D_RANKING_RECORDED` | extras, not totals |
| `US4D_CLAIM_BOUNDARY` | neural bootstrap not claimed |

Observed: zero extras **43**, thin extras **28**. Total basins 45 vs
29. Every extra terminates on an exact registered formula: 26 to
`eml(1,eml(eml(1,1),1))`, 17 to `eml(x,eml(eml(x,1),1))`, 28 to
`eml(1,eml(1,eml(1,1)))`. Zero grid-only hits. Walks are short
(1–5 steps).

The extra ratio is `43/28 ≈ 1.54`, not the Gibbs `Φ` ratio `2.016`.
Do not identify the two numbers. The shared mechanism is min-shell
multiplicity: two exact zero attractors versus one singleton
attractor. The basins overlap (26+17=43, not 56), so this is not
"two sinks, double the count."

Kill was thin extras > zero extras. Equal extras would have rejected.

## Claim boundary

**Supported.** On this bound, frozen-leaf greedy rewrite ranks the
targets with `Φ` on extra basins.

**Still supported, different processes.** Gibbs 2-vs-1.
Matching-skeleton GD `8/8` vs `6/8`. Lean zero rewrite.

**Still rejected, different process.** Unknown-skeleton GD 7 vs 7.

**Withheld.** Neural bootstrap. Any claim that architecture search
"just follows `Φ`." Function identity from the grid except the exact
zero identity. A trained superior LLM.

**What would change the conclusion.** Equal extra basins on a later
bound; extras that hit only by grid collision; a rewrite system whose
moves are not flip/swap.

## Next best test

Do not train a net to "confirm" this. The live split is already
process-relative. Paper B is the owed taxonomy discriminator, not
another EML census. A later bound may ask whether BFS connectivity,
not greedy descent, changes the extra-basin gap. That is a different
process and is not this claim.
