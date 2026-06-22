# Pre-Registration — External Contact Synthesis (papers/external_contact_synthesis)

This paper is a **synthesis** of four pre-registered external-contact tests, not a new pre-registration of a new claim. Its purpose is to organize the four frozen result reports into a single publishable narrative; the predictions and thresholds it reports were all pre-registered elsewhere, BEFORE the corresponding compute or transcription ran.

The primary pre-registration is `docs/external_contact_preregistration.md`, frozen 2026-06-18 before any external fetch, download, or sweep. It names three predictions:

- **P1** weakness → OOD on the Pythia model suite (ρ ≥ +0.5, beats classical predictors by ≥ 0.25 in |ρ|, wrong-group |ρ| ≤ 0.15; hard kill at ρ < 0.3 or any classical predictor within 0.10 of weakness).
- **P2** uncertainty ≠ error on Ovadia 2019 ensembles + Kirsch 2019 BALD (P2a per-sample |r| ≤ 0.2 on shifted slices, positive in-dist; P2b BatchBALD strictly beats naive BALD on label budget to target accuracy).
- **P3** concept-geometry convergence on GloVe (P3a margin ≥ 0.10 + NMI ≥ 0.25 after centering; P3b paraphrase gap ≥ 0.15; P3c cross-model RSA ≥ 0.60).

The cloud-agent handoff on 2026-06-22 added the **P3c-3way amendment**, pre-registered BEFORE fastText vectors were fetched: require the *minimum* pairwise RSA across all three external embedding families (GloVe-300d, GloVe-100d, fastText-300d) ≥ 0.60. This strictly tightens the original P3c.

## What is NOT pre-registered here

This synthesis does not pre-register any new claims of its own. It reports:

- P3 GloVe and P3c-3way results (against thresholds frozen in §3, §3c, and the 3-way amendment).
- P2 Tier A results (against P2a-aggregate and P2b thresholds, with explicit declaration that P2a literal is not checkable against published tables).
- P2 Tier B results (against the literal P2a per-sample |r| threshold; substrate-faithful, not substrate-equivalent, due to a declared methodology deviation for Modal egress).
- P1 Tier B linear-probe results (against the literal P1 thresholds; reported as degenerate / methodology degeneration, not falsification).

The synthesis's "sharpened claim" section (paper §4) re-states what the data actually support after honest interpretation; the synthesis's "falsified / narrowed" section (paper §5) lists what the data refute. **Neither set was pre-registered as the synthesis paper's claim** because the synthesis paper does not have its own pre-registered claim — it has only a pre-registered scope: "report honestly on what the four pre-registered Tier-A and Tier-B tests produced."

## What this synthesis paper IS pre-registered to do

Frozen scope, declared before writing:

1. Report each of the four frozen result reports' headline numbers as-recorded, without re-running any test, retroactively reframing any threshold, or omitting any pre-registered control.
2. Carry the methodology deviation for P2 Tier B (HF parquet + programmatic Hendrycks corruptions vs Zenodo .npy) declared up front in `modal_p2_ensembles_cifar10c.py` and `p2_tier_b_2026_06_22.md`.
3. Quote the discovery-EWS v1 instrument issue (positive-discipline tokens tripping the FAILURE regex) faithfully and resist tuning the v1 regex; recommend v2 structured-provenance as the fix.
4. Distinguish between (a) what the pre-reg ALLOWED a claim to be at each tier, (b) what the post-hoc data ACTUALLY supports, and (c) what the program can ship.

## Shared anti-cheat discipline (inherited from `docs/external_contact_preregistration.md`)

1. No-false-calm: every "pass" reports its kill-criterion control alongside.
2. Wrong-X controls mandatory: P1 wrong-group, P2 in-dist vs shift, P3 wrong-orbit + All-but-the-Top.
3. Frozen-now numbers: every Tier-A transcribed public number was committed before the comparison was computed (per-result-report citations + commit references).
4. Honest-negative is a result: P1 linear-probe degeneration recorded, not silently dropped; P3c-3way partial falsification recorded as a strict narrowing of the original P3 allowed claim.
