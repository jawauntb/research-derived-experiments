# Concern-Gated Retrieval Wave 1a (COGR-E2a) — Paper Directory

**Program:** Concern-Gated Retrieval (COGR) — Wave 1a (COGR-E2a)
**Deliverable:** technical report (`paper.md`) accompanying the Wave 1a
preregistration, promotion contract, and screen decision receipt at
`experiments/concern_gated_retrieval_e2/wave1a/`.
**Wave-boundary reminder:** Wave 1a is a **screen** for the concern-update
rule on fixed withheld geometry. Wave 1a **can KILL** the update rule as
written. Wave 1a **cannot** establish learned memory geometry, the L1
dual-source-retrieval mechanism claim, the L2 history-derived
concern-recovery claim, semantic meaning, or selfhood. Any restatement of
this paper as an L2 claim is inconsistent with the promotion contract at
[`../../experiments/concern_gated_retrieval_e2/wave1a/PROMOTION_CONTRACT.md`](../../experiments/concern_gated_retrieval_e2/wave1a/PROMOTION_CONTRACT.md).

## Summary

This directory contains the Wave 1a (COGR-E2a) technical report for the
Concern-Gated Retrieval E2 program. The paper (`paper.md`) motivates and
documents a **concern-recovery screen only** whose purpose is to expose
the frozen Wave 0 concern-update rule to falsification under an
adversarially misspecified prior on fixed withheld geometry, before Wave 1b
attempts the crossed learned-geometry × concern design that adjudicates
L1 and L2.

The screen crosses five conditions — frozen-wrong baseline, online-learned
IPS, online-learned DR, oracle ceiling, shuffled control, wrong-agent
control — with the three procedural families (`delayed_commitments`,
`maintenance_fault`, `resource_constrained`) and 300 paired seeds per
cell, over the confirmatory seed range `200000..201999`. Every
receipt-producing condition wraps its nomination policy in the frozen
Wave 0 `LoggedProbePolicy(epsilon=0.05)` so that selection propensities
are logged and are the sole quantity the IPS and doubly-robust estimators
divide by. A pre-analysis coverage audit rejects any confirmatory row
whose propensity-weighted coverage of the true commitment region falls
below the preregistered floor of `0.01`. Per-family effect thresholds are
frozen at `0.04845` (delayed commitments), `0.05340` (maintenance fault),
and `0.05000` (resource-constrained planning); the screen uses paired-seed
lower confidence bounds `delta_hat_{f,v} − 2·sigma_delta_{f,v}`, not
point estimates.

The paper explicitly documents Wave 1a's honest limitations — fixed
withheld geometry (not learned), no L1 adjudication, no L2 promotion on
this evidence alone, synthetic-only evaluation, no premise audit, no
poisoning stress — and points forward to COGR-E2b as the crossed design
that adjudicates L1 and L2.

## Result posture

At the time of this report, the confirmatory Modal run has not yet
executed; the screen decision receipt at
`experiments/concern_gated_retrieval_e2/wave1a/results/verdict.json` is
still a placeholder. Every numerical row in §3 of the paper is marked
**PLACEHOLDER**. The paper is intentionally built so that the writing of
the receipt — not the writing of the report — becomes the load-bearing
step. Once the receipt lands, the placeholder rows in §3 are populated
directly from `verdict.json` and the aggregate `PASS`/`KILL` propagates
into §4 verbatim.

Per the honor-the-preregistration rule
(`feedback-honor-pre-registration` in the human director's memory), only
the two knobs the preregistration §7 explicitly names as replayable —
`LoggedProbePolicy.epsilon` within `[0.05, 0.10]`, `update_concern.eta`
within `[0.05, 0.20]` — may be rerun after a fatal gate rejection, and
only on the reserved replay range `200900..201999` capped at 30% of an
affected cell. Every other knob (family definitions, condition
definitions, Wave 0 prior weights, poisoning-guard bounds, template
split, seed range, per-family thresholds in §6.2 of the preregistration,
the `IntegrityAudit` guard list) is frozen; any change is a redesign
requiring a new preregistration hash.

## Files

- `paper.md` — the Wave 1a (COGR-E2a) technical report (~4200 words,
  plain Markdown).
- `README.md` — this file.

Figures are not required by this build; the paper is intentionally
text-and-table only so that the placeholder verdict rows are
unambiguous. If figures are added by a follow-up build task, they should
mirror the Wave 0 figure conventions (`figures/fig1.png` two-flashlight
intuition, `figures/fig2.png` three-family scaffolding, and so on) and
should never be substituted for the tables in §3.

## Reproduction

Wave 1a is reproduced end-to-end by the confirmatory Modal run driven
from `experiments/concern_gated_retrieval_e2/wave1a/run_confirmatory.py`
or `experiments/concern_gated_retrieval_e2/wave1a/modal_l4_sweep.py`.
Operational requirements (see `AGENTS.md` and the roadmap [1]):

- **L4 only.** Modal H100 is explicitly forbidden by the wave-wide
  operating rule. The Wave 1a Modal function is pinned to `gpu="L4"` and
  the local entrypoint refuses to fan out if the conservative cost
  estimate exceeds the wave-wide $10.00 hard cap.
- **Modal app:** `research-derived-cogr-wave1a-e2a`.
- **`max_containers`:** up to 32 (explicitly authorized by the human
  director for Wave 1a above the wave-wide default of 10; every other
  constraint from Wave 0 still holds).
- **Deploy before spawn.** `modal deploy` runs *before* the fan-out
  step so `Function.from_name/spawn` uses the deployed image and not a
  stale one.
- **Doppler scope.** `/Users/jawaun/superoptimizers`. The token is
  injected per-invocation; no `.env` file is committed anywhere in this
  subtree.
- **Deterministic seeds.** Confirmatory seed range `200000..201999`
  (verified disjoint from calibration range `100000..100999`). The
  template-split guard raises `LeakageError` on any calibration seed
  touched by a confirmatory code path. Wave 1a runs with
  `COGR_WAVE0_CONFIRMATORY_RUN=1` set at Modal spawn time.
- **No calibration templates.** Wave 1a code never touches templates in
  the `CALIBRATION` bucket. The template-split runtime tripwire raises
  `LeakageError` on any attempted crossing.

After the Modal run completes,
`experiments/concern_gated_retrieval_e2/wave1a/PROVENANCE.md` §3-§7 is
populated from the Modal receipt (Modal deploy hash, seed-range receipt,
per-family delta receipt mirroring `PREREGISTRATION.md` §6.2, gate
receipts G0-G7, screen decision, and `WAVE1A_ANALYSIS_HASH`). The
signed preregistration is the sole channel that turns the `TBD`
numeric rows in `PREREGISTRATION.md` §6.2 (for `delta_hat` /
`sigma_delta`, not the frozen thresholds) and the `TBD` code freeze
hash in `PREREGISTRATION.md` §8 into numeric or hash values. No manual
edit is permitted. When every G0-G7 gate reports `PASS` and every
`TBD` is populated, Wave 1a promotes to `screen PASS` and Wave 1b
(COGR-E2b) may open against the frozen Wave 1a receipt for its
concern-update slot only.

## Wave-boundary claim

Wave 1a is a **screen**, not an L1 or L2 claim. Even a full screen
PASS is only permission to open Wave 1b. Every downstream claim ladder
step is gated on Wave 1b's rows against Wave 1b's own preregistration.
Wave 1a's receipt is inherited by Wave 1b for the concern-update slot
in the crossed matrix and for nothing else. See the promotion contract
at [`../../experiments/concern_gated_retrieval_e2/wave1a/PROMOTION_CONTRACT.md`](../../experiments/concern_gated_retrieval_e2/wave1a/PROMOTION_CONTRACT.md).

## References

[1] Jawaun Brown. *Concern-Gated Retrieval: Theory, Evidence, and
Research Program.* `../../docs/concern_gated_retrieval_research_program.md`
in this repository (2026-07-23).

[2] Jawaun Brown. *Concern-Gated Retrieval Wave 0: Preregistered
Calibration and Wrong-Prior Scaffolding for Learned-Geometry
Confirmation.* Wave 0 technical report.
[`../concern_gated_retrieval_wave0/paper.md`](../concern_gated_retrieval_wave0/paper.md)
in this repository (2026-07-23).

[3] Zhang, S. and Levin, M. *Intelligence from Learnable Novelty.*
arXiv preprint arXiv:2607.18433v1, 2026.
