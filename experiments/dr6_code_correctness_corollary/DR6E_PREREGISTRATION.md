# DR6e — Claude on DR6d's 11 Snippets (No Wall Predicted)

**Package:** `experiments/dr6_code_correctness_corollary/`
**Predecessor:** DR6d (regex missed R6, wall bit)
**Date:** 2026-07-27
**Written:** BEFORE new verifiers spawned.

## 0. Question

DR6d showed the wall bites for the regex verifier on the extended
11-snippet set (5 original realisations + 5 placebos + R6 novel).
Sharpened DR5 predicts a Claude verifier on the same 11 snippets should
NOT hit the wall, because condition (b) (semantic reasoning) is
available. DR6e tests this.

**If Claude misses R6**, sharpened DR5 is falsified. If Claude catches
R6 like the other realisations, the sharpened claim holds on both sides.

## 1. Setup

Same 11 snippets as DR6d. Three sandboxed Claude subagents. Prompt
IDENTICAL to DR6 (same $D$, same instructions, same scoring rule),
except pointing to `snippets_for_verifier_ext.json` (11 snippets
instead of 10). Consensus median across 3 verifiers.

## 2. Gates

Same six W-gates as DR6, plus one preregistered signal:

- **U6e**: consensus score on R6 ≥ 6. If R6 scores low, Claude also
  missed the novel realisation — refuting DR5's semantic-reasoning
  escape.

Overall GO = U6e GO + W2 GO + W3 NO_GO (uniform-good is fine) + W4 GO +
W5 NO_GO + W6 NO_GO (no overlap because R6 scores high).

## 3. Prediction

Claude catches R6 semantically. R6 scores 8+ (naive `datetime(year, ...)`
construction with UTC convention is clearly the target commitment).
Realisation distribution stays 8–10 with R6 fitting in. Placebos stay
0–1. Overlap gap remains positive. **Wall stays absent under open
enumeration when semantic reasoning is available.**

## 4. Single-shot

One extended snippet set (committed to `snippets_for_verifier_ext.json`),
three verifiers, one aggregation, one verdict.
