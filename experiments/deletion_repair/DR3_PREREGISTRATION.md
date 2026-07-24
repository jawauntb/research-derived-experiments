# DR3 — Cost Moved Off the Extension

**Package:** `experiments/deletion_repair/` (DR3 modules)
**Predecessor:** DR2 (H3′ GO, H2′ GO, H1′ NO_GO by theorem)
**Human director:** Jawaun Brown
**Date:** 2026-07-24

## 0. Freeze status — recorded honestly

The four gates below were fixed **in code** (`run_dr3.py`) before the
experiment was executed, and the code was not edited afterwards to change them.
This document, however, was written **after** the run, transcribing those gates
rather than preceding them.

That is a process slip against the discipline the rest of this repository
follows, and it had a concrete consequence, recorded in §5: **H4's threshold
was set without calibrating the costly toy's base rate, and turned out to be
unachievable by construction.** DR2's base rates were measured before its gates
were frozen; DR3's were not. The failure is a methodology error, not a finding
about the nominators, and it is reported as such.

## 1. Why DR3 exists

DR2 proved that cost attribution defined as a minimum over the extension can
never fire where weakness gain is silent:

```
ext(R) ⊆ ext(R \ D)   ⇒   a min over the extension improves only if it grew
                      ⇒   cost_attribution > 0  ⇒  weakness_gain > 0
```

The premise is the coupling. DR2's named fix was to move cost off the
extension — onto the search procedure or the representation's own description
length — rather than to build a better cost signal within it.

DR3 implements exactly that fix and asks whether it works.

## 2. The change

Cost attaches to **propositions**, as a resource commitment paid for *holding*
the constraint, independent of which hypotheses survive:

```
representation_cost(R \ D) = Σ  proposition_cost(p)   for p ∈ R \ D
cost_relief(D)             = representation_cost(R) − representation_cost(R \ D)
```

`covers_omega` gains a second conjunct: some surviving hypothesis must fit the
parent task **semantically**, *and* the surviving representation's commitment
must meet the parent **budget**.

A proposition can now be restrictive (filters hypotheses), costly (carries a
commitment), both, or neither. This is the real transformer case: "computation
proceeds sequentially" commits you to `O(n)` depth whether or not it changes
which functions are expressible — it forbids the parallel *schedule*, not the
parallel *function*.

## 3. The two toys

**RK — Restrictive Kinematics.** Every proposition costs zero, so
representation cost is identically zero and cost attribution has nothing to
say. The load-bearing deletion is DR2's entangled facet triple. Weakness must
fire; cost must be silent.

**CT — Costly Transduction.** `sequential_schedule` is **vacuous as a
predicate** — every hypothesis satisfies it, because every scheme *can* be run
sequentially — but carries a 64-unit depth commitment against a parent budget
of 8. Deleting it changes the extension not at all (`weakness_gain == 0`
exactly) while releasing the commitment. This is the case DR2 ruled out.
Cost must fire; weakness must be silent.

CT's construction deliberately exhibits the phenomenon. That is not the
experiment — it is the precondition for one. The experiment is whether the
nominators and combiners behave correctly once it exists.

## 4. Gates (frozen in `run_dr3.py` before execution)

- **H1″ — independence restored.** At least one candidate on CT has
  `cost_relief > 0` and `weakness_gain == 0`.
- **H2″ — complementarity.** The best single nominator differs between RK and
  CT. This is DR2's H1′, now testable because the theorem's premise is gone.
- **H3″ — combiner.** At least one combiner attains
  `verifications_to_first_hit` no worse than the better single nominator on
  **both** toys.
- **H4″ — speedup retained.** The best nominator achieves
  `speedup_vs_random ≥ 10` on both toys.

## 5. The defect in H4″, stated plainly

`speedup_vs_random = expected_random / verifications_to_first_hit`, and
`verifications_to_first_hit ≥ 1`. So **speedup is bounded above by
`expected_random`**, which is fixed by the toy's base rate alone.

CT has 191 load-bearing candidates out of 1350 — a 14% base rate — giving
`expected_random = 7.0`. **No nominator, however good, can exceed 7× on CT.**
The 10× threshold was therefore unachievable the moment the toy was written,
and H4″ measures my calibration rather than the nominator's quality.

The nominators in fact reached `verifications_to_first_hit = 1` on **both**
toys — the theoretical optimum. H4″'s NO_GO is a mis-specified gate, and the
correct repair for a successor is to lower CT's base rate (as DR2 did for its
toys, by padding the negative set) rather than to lower the threshold.

Recording this rather than quietly re-running is the point.

## 6. Scope

Two authored toys, authored propositions and costs, fixed vocabulary `𝔳`,
exhaustive oracle over `|D| ≤ 3`. DR3 shows the *formalisation* admits
independent cost and weakness signals and that the nominators exploit them. It
says nothing about real corpora, and nothing about vocabulary extension.
