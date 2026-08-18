# Door 1: gold is menu-relative, so no menu-blind κ

**Jawaun Brown** (human director) and **Claude Fable 5** (agent, under review)
**Date:** August 18, 2026
**Status:** Door 1 of the close-out is **closed at this bound**, and
categorically: not "five fields are too few" but "no width works."
Verdict `menu_blind_dead`. Not Paper G. Possibility 1 stays dead.

## Current frame

The close-out licensed exactly one reopening of Possibility 1: a
specified κ that does *not* look at the menu and still hits a larger
held-out family. The close-out also predicted, as a confound note,
that enlarging the menu could make `pair_eq` quotientable and erase
the cheap collision. This instrument walks through the door and banks
both facts.

## Assumption ledger

| Assumption | Type | Load-bearing? | Break test |
|---|---|---:|---|
| Gold is a property of (Y, q) | Ontology | high | Same case, two menus, two golds |
| Five fields failed for lack of width | Mechanism | high | Any width fails if gold flips |
| The cheap collision is absolute | Measurement | high | Recompute collisions per menu |
| The Paper F tie-break is natural | Mechanism | medium | Relabel a tied pair |

## Severe experiment

Package: `experiments/delete_repair_menu_blind/`. The 11 Paper E
cases plus 6 new held-out rows (tasks `pair23`, `or`, `count_ge2`;
screens `q_pair01`, `q_pair23`, 12 fibres each). Two disclosed menus:
`MENU_BASE` (Paper E's five screens) and `MENU_EXT` (plus the two
pair screens). Gold is Paper E's empirical rule with the menu as an
explicit argument. κ_cheap is Paper E's `decide`, imported **frozen**
— the close-out forbade refitting it, and we did not.

Observed:

| Fact | Base menu | Extended menu |
|---|---|---|
| `pair_eq_q_id` gold | noop | **quotient** |
| `pair23_q_id` gold | noop | **quotient** |
| Cheap hits | 15/17 | **17/17** |
| Cheap mixed-gold buckets | 1 (7 cases) | **0** |
| κ_screen | 17/17 | 17/17 |

Two gold flips exist. A menu-blind κ — any function of `(Y, q, edges)`,
of any signature width — is constant across menus and therefore wrong
on at least one side of each flip. That is the categorical kill: the
five-field rule did not fail because it was cheap; it failed because
its *type* cannot express the answer. The same type limitation makes
its success under the extended menu (17/17, zero collisions) a fact
about the menu, not a rescue of the rule.

New finding: the Paper F total order (fewest fibres, then name) is
not relabel-natural on ties. Under reversal, `pair_eq` should choose
the dual of `pair23`'s screen; both choose `q_pair01` because the tie
is broken by name. Action-level naturality holds on every registered
pair. This is `bag_not_unique` casting a longer shadow: when the
representing set is not a singleton, any name-based tie-break is
coordinate-dependent.

## Claim boundary

**Supported.** Gold is menu-relative on this harness. No menu-blind κ
is correct across menus. The cheap collision and the cheap rule's
correctness are menu-relative. κ_screen, recomputed per menu, is
exact on all 34 rows. The name tie-break is not relabel-natural on
ties; actions are.

**Not supported.** A new master object. A rescue of κ_cheap. A claim
about menus beyond the two registered ones. An LLM. Paper G.

**What would change the conclusion.** A gold semantics that is
menu-independent and still matches Paper E's banked verdicts — none
is on the table. A relabel-natural total order — that would repair
the tie-break finding, not the flip.

## Next best test

Door 1 is closed at this bound. The remaining licensed doors are the
(q, K)-reduction audit (door 2) and concern (door 3), which are
separate instruments.

## Provenance

`python3 experiments/delete_repair_menu_blind/experiment.py`;
`python3 -m unittest tests.test_delete_repair_menu_blind`. Human
director: Jawaun Brown. Agent: Claude Fable 5, session
`4adbd42d-0e99-41df-b0be-7d9d5b7e3caa`, under review.
