# US-4′ unknown-skeleton half

**Jawaun Brown** (human director) and **Cursor Grok 4.6** (agent, under review)
**Date:** August 17, 2026
**Status:** Φ-predicts-unknown-skeleton-GD is **rejected** at this
bound. Matching-skeleton GD stays banked. Neural bootstrap withheld.

## Current frame

After the Gibbs split and the matching-skeleton GD ranking, the
tempting transfer is: access *is* fiber mass, so any search process
should still prefer the fat zero target. The protected assumption is
that "the process was told the tree" was an implementation detail.

## Assumption ledger

| Assumption | Type | Load-bearing? | Break test |
|---|---|---:|---|
| Unknown-skeleton GD still tracks `Φ` | Mechanism | high | Equal skeleton counts |
| Exact 2-vs-1 is the same claim | Ontology | high | Separate it as the control |
| Matching-skeleton GD already settled this | Ontology | high | Different process |
| A Gibbs draw would be a fair test | Ontology | high | Forbid it |

## Anomaly map

Exact unweighted hits stay **2 vs 1**. Matching-skeleton GD stayed
`8/8` vs `6/8`. Those do not decide this paper.

## Candidate reframe

`Φ` is a fact about *inhabitants and known-tree basins*. It is not
automatically a fact about search that has to find the tree. At
`k=3`, enough size-3 skeletons can weight-fit *either* target, so
min-size governs once the skeleton is unknown.

## Discriminating predictions

| Predictor | `n_gd_skeletons` |
|---|---|
| `Φ` transfers | zero > thin |
| Min-size governs | equal |
| `Φ` is the wrong key | thin > zero |

## Severe experiment

Package: `experiments/eml_us4_search/`.
Language: all 80 size-3 variable-`x` trees.
Process: the same `descend()` as `eml_us4_gradient`, four blind seeds
per skeleton, both targets.

Fatal gates (all passed):

| Gate | Fact |
|---|---|
| `US4S_ENUMERATION` | 80 trees |
| `US4S_EXACT_CONTROL` | unweighted 2 vs 1 |
| `US4S_PROCESS_IS_NOT_GIBBS` | GD disclosure |
| `US4S_NOT_MATCHING_ONLY` | wrong trees included |
| `US4S_PERTURBED_CORRECT` | true zero skeleton still works |
| `US4S_RANKING_RECORDED` | `min_size_governs` |
| `US4S_CLAIM_BOUNDARY` | neural bootstrap not claimed |

Observed: zero **7** skeletons, thin **7** skeletons. Extra
skeletons **6 vs 6**. The two targets can even fit *each other's*
matching trees by moving weights.

Kill was thin > zero. Equal counts reject the transfer.

## Claim boundary

**Supported.** On this bound, unknown-skeleton GD does not rank the
targets by `Φ`. Min-size / shared size-3 flexibility governs.

**Still supported, different process.** Gibbs 2-vs-1. Matching-skeleton
GD `8/8` vs `6/8`. Lean zero rewrite.

**Withheld.** Neural bootstrap. Any claim that architecture search
"just follows `Φ`." Function identity from the grid except the exact
zero identity.

**What would change the conclusion.** A later bound where extra
unknown-skeleton basins reopen a `Φ` gap; a search process that
cannot retarget a tree by moving `1`-leaves.

## Next best test

A process that cannot freely retune every `1`-leaf — discrete formula
search with frozen leaves, or a neural bootstrap that proposes trees.
If that still ties, the access claim stays process-split. If it
reopens a `Φ` gap, unknown-skeleton GD was the wrong instrument.
