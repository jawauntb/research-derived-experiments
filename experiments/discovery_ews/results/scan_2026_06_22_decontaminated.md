# Discovery-EWS — self-reference fix (de-contaminated rescan)

Date: 2026-06-22
Code: `experiments/discovery_ews/discovery_ews.py`

## What was wrong

The scanner globs `experiments/*/results/*.md`, which had begun to include the
discovery-EWS's own scan reports (`experiments/discovery_ews/results/scan_*.md`).
Those reports name every experiment family (inflating each family's `reuse` count,
which feeds the load-bearing `has_anchor` test) and are saturated with
"load_bearing / transfer / external" tokens (tripping the rubric). The result was a
**Goodhart feedback loop**: every time a scan was recorded, the next scan's
conversion rate drifted upward purely from self-reference. The post-P3 scan reported
conversion 0.167 (9/54); some of that rise was real (P3 is genuine external contact)
and some was the loop.

## The fix

Added `META_FAMILIES = {"discovery_ews"}` and excluded it from `collect_artifacts()`.
The detector no longer ingests artifacts that are *about* the program rather than
*part of* it. (This is the same lesson the v1 apophenia incident taught, applied to
the tool's own output: a detector that feeds on its own verdicts cannot stay honest.)

## De-contaminated numbers

| | Pre-fix (self-referential) | Post-fix |
|---|---|---|
| spike → load-bearing conversion | 0.167 (9 / 54) | **0.135 (7 / 52)** |
| episode verdicts | 37 self_sealing / 8 dissipated / 9 load_bearing | 37 self_sealing / 8 dissipated / 7 load_bearing |

`external_contact` remains `load_bearing` — P3 is real external contact and should
count. The two spurious load-bearing episodes removed were the self-reference
artifacts, not P3.

## Standing interpretation

P3 GloVe is the program's **first genuine external load-bearing episode** (allowed
claim: mechanism → regime transition, NOT a field claim). One pillar
(concept-geometry) survived first outside contact; the program has not yet escaped
the self-built-world problem — that needs P2 and P1 to land too. The honest
conversion rate is ~0.135 and should only move when a *past* destabilization is
shown to survive transfer + external load, never from recording scans.
