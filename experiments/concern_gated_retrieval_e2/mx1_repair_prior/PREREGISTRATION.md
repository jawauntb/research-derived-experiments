# MX1 — Minimal De-Risk Experiment (frozen preregistration)

**Package:** `experiments/concern_gated_retrieval_e2/mx1_repair_prior/`
**Status:** frozen 2026-07-24, BEFORE any evaluation row was generated
**Predecessors (imported, never edited):** `wave0/`, `wave1b/`
**Human director:** Jawaun Brown
**Class:** single-shot GO/NO-GO de-risk probe. **Not a wave. Not a program.**

## 0. Why this exists

Wave 1b falsified L1: on honest learned geometry, rarity-corrected
multiplicative context×concern retrieval does not beat a degree-matched
random null. Per the noncompensatory rules, Waves 2–4 do not open.

The synthesis paper (§7) scopes exactly one successor question, drawn from
MIDAS (`github.com/ebarnes-ry/MIDAS`): can the **verify→repair loop** supply a
**care-independent** signal that the care model cannot launder? MX1 tests the
two transferable parts at the smallest scale that can answer GO/NO-GO. It
builds nothing beyond that.

## 1. Design correction recorded before freezing

Two facts about the substrate were established by a calibration probe on
CALIBRATION seeds before this document was frozen. Both changed the design,
and both are recorded here rather than silently absorbed:

1. **No persistent memory across episodes.** Candidate nodes are named
   `{family}_s{seed}_n{idx}`; candidate sets from different seeds are
   disjoint. A *cross-episode* repair-frequency prior has nothing to
   accumulate on. The original sketch assumed persistence; it was wrong.
2. **MIDAS's repair loop is within-problem, not cross-problem.** Its
   `difficulty_signal = (attempt_count - 1) / max_attempts` is computed
   per-trajectory, i.e. per problem. The faithful port is therefore a
   **within-episode** verify→repair loop, which requires no persistent
   memory and no generator change.

A third finding disqualified an alternative we considered and rejected:
keying the prior on **candidate position** would have been a fixture
artifact. The v2 paraphrase families genuinely invert — over 600 calibration
seeds, `friend_host_night` places the load-bearing memory in the most-recent
normalized bucket 81 times while `child_school_deadline`,
`partner_birthday`, and `wedding_anniversary` place it there **zero** times.
A position prior fits the majority rule and breaks on the minority family.
Rejected before freezing; recorded so it is not re-proposed.

## 2. Substrate (fixed)

- **One family:** `wave1b.families.delayed_commitments_v2` — recency-decoupled
  (`recency_load_bearing_corr = 0.150`) and bundle-planted, and it passed the
  Wave 1b G9 leakage audit (label-permutation p = `0.594`).
- **Bucket:** `TemplateBucket.CALIBRATION` only. Wave 1b's confirmatory pool
  (`200000..201999`) is **not touched** — MX1 is a probe, and must not
  consume confirmatory seeds.
- **Seeds:** `100000..100599` (600 episodes).
- **Per-episode retrieval budget:** the episode's own `budget` (= 2).
- **Attempt budget:** `MAX_ATTEMPTS = 3` for every policy, so all policies
  spend an identical total of `3 × 2 = 6` candidate-slots. Matched budget is
  enforced by construction, not by assertion after the fact.

## 3. Part A — within-episode repair-guided exploration

**Question.** Does a care-independent repair signal reach the load-bearing
memory in fewer attempts than the care model alone, and than random?

**Policies** (identical attempt budget; attempts never re-pick a
previously-tried candidate):

| id | attempt 1 | attempts 2–3 |
|---|---|---|
| `concern_sequential` | `multiplicative_ppr` top-2 | walk down the concern ranking |
| `repair_guided` | `multiplicative_ppr` top-2 | **repair-informed** (below) |
| `random_sequential` | random 2 | walk down a seeded random permutation |
| `oracle_set` | oracle top set | — (**ceiling; refused by promotion**) |

**Second substrate finding, recorded before freezing.** A graph-structural
repair rule was designed, probed, and **rejected as a no-op**. On this family
every candidate is structurally identical: the withheld geometry assigns
*every* candidate degree exactly `6`, and `wave0.baselines._local_graph` is a
uniform candidate clique (all pairs weight `0.1`). Down-weighting "the failed
picks and their graph neighbours" therefore down-weights everything equally.
There is **no** care-independent *structural* signal on this substrate.

What there *is* is genuine planted **interaction** structure, and that is what
Part A tests instead. Over the 600 seeds, 109 episodes carry a complementary
pair, and the super-additivity is large — a representative pair scores
`Δ({a}) = −0.011`, `Δ({b}) = −0.011`, `Δ({a,b}) = +0.378`.

**Repair-informed rule (the thing under test).** After each attempt the policy
receives only `AttemptFeedback(hit_count, fault_kind)` — how many of its `k`
picks were load-bearing, and the fault kind from §4. It never sees *which*
pick hit, and never sees roles, utilities, or the answer key.

On a REASONING_FAULT with `hit_count == 0`, `concern_sequential` abandons both
picks and moves to the next concern-ranked pair. `repair_guided` instead
**retains one member and re-pairs it** with the best untried candidate —
hypothesising that a pick scoring ≈ 0 alone may be one half of a
super-additive pair rather than worthless. On a VERIFIER_FAULT the attempt is
**not** counted as evidence about those candidates (§4).

This is care-independent: the retain-and-re-pair decision is driven purely by
observed task failure, never by the concern weights. It is also the direct
operational form of Spencer's bundle objection — a memory that looks useless
in isolation can be load-bearing in company.

**Primary metric.** `attempts_to_success` (MIDAS's difficulty signal),
`MAX_ATTEMPTS + 1` when never successful. Secondary: `simple_regret_set` of
the policy's best attempt, and `oracle_recall_at_k`.

**Part A GO** iff, over the 600 episodes, `repair_guided` has a strictly lower
mean `attempts_to_success` than **both** `concern_sequential` **and**
`random_sequential`, and each margin's bootstrap 95% CI excludes 0.
A tie with `random_sequential` means the repair signal adds nothing over naive
re-sampling ⇒ **NO-GO**.

## 4. Part B — verifier-fault split

**Question.** Does separating "the memory did not help" from "our checker
could not score this" prevent a genuinely useful memory from being mislabeled
useless?

**The verifier gap (realistic, not synthetic).** A **marginal** verifier scores
a set as `Σ Δ({c})` over its members. That is wrong exactly where the family
plants interaction structure: a *complementary pair* is super-additive (each
member alone scores ≈ 0, the pair is valuable), so a marginal verifier reports
≈ 0 and the pair is discarded as useless.

- `marginal_verifier(episode, S)` → additive sum of singleton deltas.
- `split_verifier(episode, S)` → `REASONING_FAULT` with the marginal value
  when the set carries no planted interaction; `VERIFIER_FAULT` (value
  withheld) when `S` contains members of a planted complementary pair or
  dangerous conjunction, i.e. when the marginal model is out of its
  competence. Ground truth for "was it genuinely useful" is
  `sealed_env_ext.compute_set_delta` (the SET-level oracle), which the
  verifiers themselves never call.

**Part B GO** iff both hold over the same 600 episodes:
1. `split_verifier` strictly reduces the count of
   **useful-bundle-mislabeled-useless** versus `marginal_verifier`; and
2. `split_verifier` has **precision 1.0** on cleanly-scorable singleton sets —
   zero false `VERIFIER_FAULT` where the marginal model is in fact correct.

## 5. Frozen knobs (no tuning to manufacture a GO)

```
FAMILY                  = delayed_commitments_v2
BUCKET                  = CALIBRATION
SEEDS                   = 100000..100599        (600 episodes)
MAX_ATTEMPTS            = 3
SUCCESS_DELTA_THRESHOLD = 0.0     (attempt succeeds iff Δ_task > 0)
BOOTSTRAP_RESAMPLES     = 2000
BOOTSTRAP_SEED          = 20260724
```

## 6. Promotion semantics

- **Both parts GO** → the two circularities are severable on this substrate;
  a successor arc may be preregistered. Still not L1, not a program.
- **Only A** → exploration-prior redesign only.
- **Only B** → verifier redesign only.
- **Neither** → the concern-gated retrieval mechanism programme is finished;
  the synthesis paper stands as its terminus.

Single-shot. No replay knobs. A NO-GO is a real NO-GO and gets written up as
one, per the honor-the-preregistration rule.

## 7. Scope limits stated in advance

MX1 runs on **one** synthetic family with authored bundle structure. It cannot
establish transfer, cannot establish L1, and cannot license any deployment or
cognitive claim. A GO licenses exactly one thing: preregistering a successor
experiment.
