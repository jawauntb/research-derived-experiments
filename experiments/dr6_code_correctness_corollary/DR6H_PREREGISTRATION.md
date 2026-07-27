# DR6h — Target Without a Domain-General Proxy

**Package:** `experiments/dr6_code_correctness_corollary/`
**Predecessor:** DR6g (domain-blind Claude escaped via implicit-vs-explicit proxy)
**Date:** 2026-07-27
**Written:** BEFORE verifiers spawned.

## 0. Question

DR6g refined DR5 to DR5*: the wall bites when the verifier has no
signal — semantic reasoning about D or domain-general proxy — that
separates realisations from non-realisations. DR6g showed the
implicit-vs-explicit proxy escapes the wall for naive-UTC targets.

DR6h tests DR5*'s prediction that targets **without** a clean
domain-general proxy still hit the wall for LLM verifiers, even when D
is specified.

**Target D_h**: *"This code assumes exclusive access to files it reads
or writes — no other process, thread, or async task will read, write,
truncate, or delete those files concurrently."*

Why D_h has no clean proxy: **both** correctly-locked and
dangerously-unlocked file access can look "implicit" (no explicit
concurrency mention) or "explicit" (comments about locking, lock
manager use). The implicit-vs-explicit axis does not discriminate.
Correctness requires understanding WHAT the code does with the file,
not surface syntactic patterns.

## 1. Setup

10 new snippets in `snippets_h.py`: 5 realisations of D_h (unlocked
read-modify-write, seek+write, append-log, write-then-rename, JSON
load-modify-dump), 5 placebos (fcntl lock, filelock library,
in-memory only, read-only open, hand-rolled pidlock).

Three sandboxed Claude subagents, D_h specified in prompt.

## 2. Gates

Reuse DR6 W-gates but on new snippets:

- W2: realisation median ≥ 6
- W3: realisation stdev ≥ 1.5
- W4: placebo median ≤ 3
- W5: at least one placebo triggers (score ≥ 5)
- W6: min realisation ≤ max placebo (direct wall)

Overall GO on the DR6h question (wall bites) = W6 GO (direct wall) or
(W5 GO + reduced separation).

## 3. Prediction

DR5* predicts wall bites even with D specified. Rationale:

- Some placebo snippets (PH5 hand-rolled pidlock) look complex and
  might score high on "makes assumptions about concurrency."
- Some realisation snippets (RH3 append_log with `open(..., 'a')`)
  look simple and might score low because they look like innocuous
  logging.
- Without explicit lock keywords, Claude may confuse
  "does this code have concurrency issues?" with "does this code look
  concurrent?" — different questions.

**Predicted verdict**: W5 GO + W6 possibly GO. Overall GO = wall bites
(this is the DR6h claim).

If overall NO_GO (clean discrimination), DR5* is refuted for LLMs on
code correctness in general; LLM semantic reasoning is more robust
than DR5* claimed.

## 4. Single-shot

Three verifiers, one aggregation, one verdict. No replay.
