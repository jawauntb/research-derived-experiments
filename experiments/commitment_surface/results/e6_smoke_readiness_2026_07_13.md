# E6 L4 smoke readiness

Status: **BLOCKED at the frozen round-1 CS eligibility gate; development and
confirmatory execution withheld.**

This is a harness/readiness result, not evidence for either E6 collapse
hypothesis. The pinned Modal image and result Volume passed preflight, and the
single coupled L4 worker completed the shared bootstrap, candidate generation,
and CS reward scoring. It then stopped before any round-1 self-training because
only **8 of 104** candidates survived both frozen patch-CE thresholds, while
matched top-half exposure required **52** candidates.

## Exact run

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal==1.2.6 modal run \
  experiments/commitment_surface/modal_e6_commitment_reward.py \
  --sizes 70m --ns 13 --seed-slots 1 --arms SC,CS,GT,A-ref \
  --run-kind smoke --execute --max-gpu-cells 1 \
  --out artifacts/commitment_surface/e6_smoke_reviewed.json
```

- Final post-review L4 run: <https://modal.com/apps/generalintelligencecompany/main/ap-KB0bzzztV40VIfazjhpshv>
- Development-manifest dry-run: <https://modal.com/apps/generalintelligencecompany/main/ap-XO0wvPQzoJZsgY08IdMsnb>
- Manifest ID: `0498cd7e0440df3ffd507debad2842f5f9587cc883b5a7cbf18b4cdaee85b25c`
- Implementation fingerprint: `24afc68a904a6a7e6d79528bdf2fbe1353fd5ed5e447e017e4b5340e787e101b`
- Raw output: `artifacts/commitment_surface/e6_smoke_reviewed.json` (gitignored)
- Local exit: nonzero after the resumable failure artifact was written
- Remote cells/checkpoints: 0 complete, 4 analytical cells missing, 0 active
  E6 leases after exit

An earlier launch reached no training because the control container imported a
GPU-only module that was absent from its mount. That packaging fault was fixed.
The final post-review run above also includes fail-closed stale-lease handling
and exact returned-cell/checkpoint validation; it reached the scientific
eligibility check. The infrastructure failure and superseded smoke fingerprints
are not counted as E6 evidence.

## Frozen-gate outcome

| Check | Outcome |
|---|---:|
| Pinned dependency and Volume preflight | PASS |
| One symmetric SC/CS candidate pool built | PASS |
| Candidate pool size | 104 |
| Frozen top-half selection requirement | 52 |
| CS candidates with canonical and transported patch-CE ≥ 0.05 | 8 |
| Round-1 matched SC/CS training | NOT STARTED |
| Smoke integrity gate | FAIL / incomplete |
| Confirmatory readiness | FALSE |

The runner did not lower `ε=0.05`, reduce `ρ=0.5`, admit zero-masked
ineligible candidates, add bootstrap epochs, or relabel the failure. Any of
those would modify the objective after observing the calibration and requires a
new frozen design. Because no round trajectory exists, G1–G4 are untested; the
only valid E6 verdict remains `pending_confirmatory_grid`.

## Resource and launch decision

The failed stratum did not emit complete worker-duration telemetry, so a
defensible development or confirmatory cost estimate is unavailable. More
importantly, the one-stratum smoke failed before self-training. The planned
nine-stratum development calibration and 27-stratum confirmatory grid were
therefore **not launched**, independent of cost and while the separate E5 grid
continued under its own app, Volume, and leases.

## Discovery-regime audit

- **Current regime:** E6 can represent paired current-adapter pools, typed
  label-free CS rewards, strict transport eligibility, six-round trajectories,
  and exact manifest/integrity gates.
- **Action class:** a new training operation was exercised, but no discovery
  artifact was accepted because the operation could not produce the frozen
  round-1 exposure volume.
- **Accepted artifact:** the pinned L4 runner, deterministic manifest, and
  negative readiness record.
- **Rejected/withheld artifact:** all collapse, load-bearing, transport, and
  generator-learning claims; development and confirmatory spends.
- **Residual content:** under the frozen bootstrap and threshold, the CS reward
  is too sparse for exposure-matched top-half training in the smallest smoke.
- **Next move:** if E6 is redesigned, preregister a reward-density diagnostic or
  a different selection contract before another GPU run. Do not tune the
  existing E6 gates from this result.

## Claim boundary

Supported: the L4 harness enforces the symmetric-pool, label-separation,
transport-threshold, matched-volume, manifest, lease, exact-checkpoint, and
fail-closed launch contracts through real bootstrap and candidate scoring.
Stale lease records are never reclaimed automatically.

Not supported: whether CS or SC collapses, whether the commitment-surface reward
is load-bearing, whether it transports across rounds, or any E6 scientific
mechanism verdict.
