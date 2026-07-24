# DR2 — Does Cheap Nomination Beat Exhaustive Search When Exhaustive Search Hurts?

**Package:** `experiments/deletion_repair/` (DR2 modules)
**Status:** frozen 2026-07-24, BEFORE any scoring row was generated
**Predecessor:** DR1 (NO_GO on both hypotheses; see `papers/deletion_repair_dr1/`)
**Human director:** Jawaun Brown

## 0. Why DR2 exists

DR1's decisive limitation was not a result but a **regime**: 21 candidates,
each cheap to verify. Exhaustive search *is* the answer there, so a nominator
could not earn its keep no matter how well it ranked. DR1 validated the
harness, not the nominator, and could not have done otherwise.

DR2 scales until the nominator is necessary, and applies the two defects DR1
named in its own §5. These are continuation of a NO_GO, not rescue of one: the
changes were specified by the failed experiment before DR2 was designed, and
the hypotheses below are **freshly stated in graded form**, not DR1's binary
criteria relaxed until they pass.

## 1. What changed from DR1, and why

| DR1 defect (named in DR1 §5) | DR2 change |
|---|---|
| 21 candidates -- nominator unnecessary | `|R_deletable| = 20`, `|D| ≤ 3` ⇒ **1350** candidates |
| `max` disjunction worse than its best component | add **sum-of-normalised** and **min-of-ranks** combiners, scored head to head against `max` |
| `TT` base rate 40% -- `random` scored 0.67 by luck | base rates driven to **0.07%** and **1.4%** (measured, §3) |
| `recall@k` insensitive to search cost | primary metric is now **verifications-to-first-hit** |

## 2. The two scaled toys

**SK — Scaled Kinematics** (weakness-shaped). Three *entangled facets* of one
commitment — absolute simultaneity, no length contraction, no time dilation —
each pinning the same dial. **No subset frees anything; only the full triple
does.** A nominator scoring singletons or pairs cannot see it at all.
`preferred_rest_frame` is the Lorentz-without-Einstein trap: droppable,
enlarges the extension, reaches nothing. Cost is flat, so cost must stay
silent.

**ST — Scaled Transduction** (cost-shaped). Dropping sequential update
collapses parallel depth but leaves a **dangling obligation**: without
recurrence there is no order signal, so the deletion covers the parent task
only when `no_positional_input` is dropped alongside it. This mirrors the real
case, where removing recurrence forced positional encodings.

Sixteen inert nuisance propositions pad each toy. They are the negatives, and
there are deliberately many.

## 3. Calibration (measured before freezing, as Wave 0 discipline requires)

| toy | candidates | load-bearing | base rate | expected verifications under random order |
|---|---:|---:|---:|---:|
| SK | 1350 | 1 | 0.07% | **675.5** |
| ST | 1350 | 19 | 1.41% | **67.5** |

Exhaustive search is now genuinely painful, which is the precondition DR1
lacked.

## 4. Nominators

All execution-free; none may call `fits_omega`.

| id | definition |
|---|---|
| `weakness` | extension growth when `D` is dropped |
| `cost` | improvement in best achievable cost |
| `max_disjunction` | DR1's combiner, carried forward **as the thing under test** |
| `sum_disjunction` | **fix A** — sum of per-toy max-normalised scores |
| `minrank_disjunction` | **fix B** — `min` of the two nominators' ranks (either signal ranking you highly suffices) |
| `random`, `size_only` | controls |

Ties are broken by a seeded shuffle, never by name — the erratum-E1 defect DR1
caught during its own construction.

## 5. Metrics

- **`verifications_to_first_hit`** — 1-indexed position of the first
  load-bearing deletion in the nominator's ranking. This is the number of
  expensive parent-task verifications a cost-ordered pipeline would run before
  succeeding. **Primary.**
- **`speedup_vs_random`** — `expected_random_verifications /
  verifications_to_first_hit`.
- `recall@10`, reported for continuity with DR1.

## 6. Frozen gates

- **H1′ (dominance).** No single nominator attains the best
  `verifications_to_first_hit` on **both** toys. GO iff the argmin nominator
  differs between SK and ST. This is DR1's H1 restated in the graded form the
  DR1 evidence supported, and it is now a dominance test rather than a silence
  test.
- **H2′ (combiner fix).** At least one of `sum_disjunction` or
  `minrank_disjunction` attains `verifications_to_first_hit` no worse than the
  better of `weakness` and `cost` on **both** toys — the property `max` failed
  in DR1.
- **H3′ (the nominator earns its keep).** The best nominator achieves
  `speedup_vs_random ≥ 10` on **both** toys. Concretely: `≤ 67` verifications
  on SK and `≤ 6` on ST.

**Overall GO** requires all three. H3′ is the load-bearing one — it is the
question DR1 could not reach.

## 7. Anti-leakage, run before freezing

The inverted-signal audit is run over **every** nominator, in **both**
orderings, against the load-bearing set, and the tie-fraction is reported for
each. Any nominator that is entirely tied is reported as **silent**, and a
silent nominator scoring well is treated as a leak, not a result. This gate has
now caught a real defect in two consecutive programmes and is assumed to apply
here until measured.

## 8. Scope limits

Two authored toy systems, authored propositions, fixed vocabulary `𝔳`,
exhaustive oracle over `|D| ≤ 3`. DR2 says nothing about real corpora and
nothing about vocabulary extension — the known ceiling. A GO licenses exactly
one thing: preregistering a date-cut retrodiction. Single-shot; no replay
knobs; a NO_GO is a real NO_GO.
