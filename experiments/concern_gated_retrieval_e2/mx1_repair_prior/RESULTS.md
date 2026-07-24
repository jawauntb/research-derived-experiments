# MX1 — results receipt

**Run date:** 2026-07-24
**Verdict artifact:** `results/mx1_verdict.json`
**Overall decision:** `PARTIAL_GO_B_ONLY`
**Compute:** local CPU, 600 episodes, no Modal, $0.

Frozen design: [`PREREGISTRATION.md`](PREREGISTRATION.md). Nothing below was
tuned after a result was seen; the two substrate findings that changed the
design were recorded in the preregistration *before* any evaluation row ran.

## Part A — within-episode repair-guided exploration: **NO_GO**

Mean `attempts_to_success` (lower is better; `4` = never succeeded within the
3-attempt budget) and success rate over 600 episodes:

| policy | mean attempts | success rate |
|---|---:|---:|
| `concern_sequential` | 2.933 | 0.545 |
| `random_sequential` | 2.975 | 0.510 |
| **`repair_guided`** | **3.218** | **0.350** |

Contrasts (negative = `repair_guided` better; GO required negative with the CI
excluding 0):

| contrast | mean diff | 95% CI |
|---|---:|---|
| vs `concern_sequential` | `+0.285` | `[+0.247, +0.323]` |
| vs `random_sequential` | `+0.243` | `[+0.112, +0.375]` |

`repair_guided` is **worse than both rivals**, decisively. Both CIs exclude 0
in the wrong direction.

**Diagnostic (reported, not used to move the verdict).** Split by whether the
episode actually plants a complementary pair:

| subset | n | `concern_sequential` | `random_sequential` | `repair_guided` |
|---|---:|---:|---:|---:|
| with complementary pair | 109 | 2.862 | 2.991 | **3.101** |
| without pair | 491 | 2.949 | 2.971 | **3.244** |

This is the informative part. `repair_guided` loses **even on the episodes that
contain a super-additive pair** — the case the strategy was designed for. So
the result is not "right idea, too expensive on average."

**Why it fails.** The rule retains `picks[0]`, the top *concern*-ranked pick.
Wave 1b already established that the concern ranking carries no representation
contribution, so the retained node is effectively arbitrary, and the chance it
is one half of the planted pair is low. The policy therefore pays a slot on a
known-failed arbitrary candidate almost every time, and buys the interaction
discovery almost never. Retain-and-re-pair needs a way to choose *which*
candidate to retain; on this substrate there is none, because every candidate
is structurally identical (uniform withheld-geometry degree `6`).

## Part B — verifier-fault split: **GO**

| quantity | marginal verifier | split verifier |
|---|---:|---:|
| genuinely useful pairs mislabeled useless | **109** | **0** |
| false `VERIFIER_FAULT` on singleton controls | n/a | **0 / 6920** |

The marginal verifier — the one that scores a set as the sum of its members —
mislabeled **every one** of the 109 genuinely useful complementary pairs as
useless, because each member scores ≈ 0 alone. The split verifier mislabeled
**none**, and never once declined on a set the marginal model could in fact
handle correctly (precision `1.0` across 6,920 singleton controls).

Both frozen GO conditions are met.

## What this licenses

Per [`PREREGISTRATION.md`](PREREGISTRATION.md) §6, `PARTIAL_GO_B_ONLY` licenses
**verifier redesign only** — and only the preregistration of a successor
experiment, not a program.

Concretely: separating "this memory did not help" from "our checker could not
score this" is worth carrying forward, and it is the operational answer to
Spencer's verifier-circularity objection. Deriving a care-independent
*exploration prior* from repair dynamics is **not** carried forward in this
form; MX1 falsified the only version of it this substrate can express.

## Honest scope limits

One synthetic family, authored bundle structure, calibration bucket only.
Part B's GO is a statement about a **marginal** verifier meeting **planted**
interactions; it shows the split is well-formed and safe, not that it helps on
natural data. Wave 1b's confirmatory pool was not touched.
