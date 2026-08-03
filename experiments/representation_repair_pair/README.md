# Representation-Repair Pair (Theorems RR-1 and RR-2 witness)

Companion instrument for
[`papers/representation_repair_calculus/paper.md`](../../papers/representation_repair_calculus/paper.md).

Hypothesis: for each of the eight canonical `(failure_signature,
minimal_lift)` pairs listed in Extended-Program section 5.8 of
*The Structural Intelligence Conjecture*, there is a small hand-designed
world on which

- the broken representation `R` misses the target invariant `I`
  (there exist two states with the same `R`-value but different `I`-value);
- the lifted representation `R'` captures `I`
  (for every pair of states, `R'` agreeing forces `I` to agree);
- `R'` is a minimal enlargement of `R`: for every nonempty subset `S` of
  the added components, `R + (added \ S)` no longer captures `I`.

Additionally, the composition gate (Theorem RR-2) checks that two
lifts on independent slots of a product world commute and jointly
repair both invariants, and that the composed lift is minimal on the
product world.

Method: pure Python enumeration on finite worlds (6 to 16 states per
pair; 48 states in the composition world). Every check is exact and
deterministic; no randomness. Runs in well under a second.

Pre-registered gates:

- `rr1_every_canonical_pair_broken_representation_misses_invariant`:
  8/8 pairs -- for every pair, the broken rep misses the invariant.
- `rr1_every_lifted_representation_captures_invariant`:
  8/8 pairs -- for every pair, the lifted rep captures the invariant.
- `rr1_every_lift_is_minimal`:
  8/8 pairs -- for every pair, no strictly smaller enlargement of the
  broken rep also captures the invariant.
- `rr2_two_independent_lifts_compose`: on the product of the
  scalar->operator world and the static->path-space world, the composed
  lift captures both invariants, is minimal, and produces the same
  factorisation regardless of the lift-application order.

Result: all four gates pass exactly.

Run:

```bash
python3 experiments/representation_repair_pair/experiment.py
```
