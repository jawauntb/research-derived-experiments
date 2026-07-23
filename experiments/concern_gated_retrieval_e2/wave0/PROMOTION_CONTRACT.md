# Wave 0 Promotion Contract

Frozen, non-compensatory promotion contract for the Wave 0 deliverable of the
Concern-Gated Retrieval E2 program. This file is authoritative. Where it
disagrees with anything else in this subtree, this file wins.

```yaml
claim_id: COGR-E2-WAVE0-CALIBRATION-FREEZE
target: >-
  Freeze the calibration variance estimate, non-ceiling headroom check,
  wrong-prior initialization, and three-family scaffolding that Wave 1
  (COGR-E2a then COGR-E2b) confirmatory rows will be scored against.
wave: 0
non_compensatory: true
scope:
  positive:
    - "Wave 0 is calibration-only."
    - "Wave 0 registers a wrong prior, three procedural families, sealed env, anti-leakage guard, baseline slate, and effect-threshold shape."
    - "Wave 0 produces variance estimates that turn TBD threshold rows into numeric rows."
  negative:
    - "Wave 0 does NOT claim learned memory geometry."
    - "Wave 0 does NOT claim concern recovery from experience."
    - "Wave 0 does NOT claim semantic meaning or selfhood."
    - "Wave 0 does NOT touch confirmatory templates or the confirmatory seed range."
    - "Wave 0 does NOT use non-synthetic history; the premise audit is future work with a stub receipt."
gates:
  - id: G0_ANTI_LEAKAGE
    kind: integrity
    description: >-
      Every evaluator-only field enumerated in PREREGISTRATION.md §4.1 is
      unreachable from calibration policy code. The runtime guard raises on
      each violation class and its regression tests pass. Confirmatory
      templates are inaccessible during calibration.
  - id: G1_WRONG_PRIOR
    kind: adversarial
    description: >-
      Every calibration row uses the wrong-prior specification in
      PREREGISTRATION.md §5: alarm region inflated to w_alarm_init=1.0,
      designated commitment region suppressed to w_commit_init=0.05, at
      least one true commitment left at uniform.
  - id: G2_NON_CEILING
    kind: non_ceiling
    description: >-
      headroom_to_ceiling is strictly positive on every family and no
      baseline saturates within 0.05 * bounded_reward_range of the oracle
      ceiling on any family.
  - id: G3_FAMILY_ROBUSTNESS
    kind: robustness
    description: >-
      Each family in {delayed_commitments, maintenance_fault,
      resource_constrained} produces an independent variance estimate; the
      calibration receipt records per-family, not only aggregate,
      statistics so a Wave 1 family-level reversal cannot be hidden by
      the aggregate.
  - id: G4_SEED_INDEPENDENCE
    kind: integrity
    description: >-
      Calibration seed range 100000-100999 is disjoint from the reserved
      confirmatory range 200000-201999, verified by the generator's
      seed-range guard.
  - id: G5_CODE_FREEZE
    kind: reproducibility
    description: >-
      WAVE0_ANALYSIS_HASH is a SHA-256 of every tracked file under
      experiments/concern_gated_retrieval_e2/wave0/** in sorted path
      order, matches the value mirrored into PROVENANCE.md, and is
      written only after the calibration Modal run completes.
  - id: G6_MODAL_BUDGET
    kind: operational
    description: >-
      Modal execution used L4 GPUs only. The realized effective GPU-hour
      cost is at or below 35% of the equivalent H100 rate for the same
      run. Deploy occurred before spawn and the deployed image hash is
      recorded in PROVENANCE.md.
promotion_rule: >-
  Wave 0 is promoted to "frozen" and Wave 1 may open iff every gate above
  (G0-G6) reports PASS in the calibration receipt, every TBD row in
  PREREGISTRATION.md §8 is populated with a finite numeric value, and the
  WAVE0_ANALYSIS_HASH is written into PREREGISTRATION.md §11 and mirrored
  into PROVENANCE.md. Non-compensatory: a single gate FAIL blocks
  promotion regardless of every other gate's status.
demotion_rule: >-
  If Wave 1 discovers, during confirmatory execution, that a Wave 0
  threshold was populated from a calibration row that violated any G0-G6
  gate, the Wave 0 freeze is retroactively demoted to REDESIGN. All
  Wave 1 rows scored against the invalidated threshold row are marked
  non-evidence. A new Wave 0 hash must be produced before Wave 1 can
  reopen. No post-hoc threshold swap is permitted.
artifacts_required:
  - path: experiments/concern_gated_retrieval_e2/wave0/PREREGISTRATION.md
    contains:
      - signed calibration manifest hash in §11
      - populated variance rows in §8
  - path: experiments/concern_gated_retrieval_e2/wave0/PROVENANCE.md
    contains:
      - calibration Modal deploy hash
      - calibration seed-range receipt (100000-100999)
      - per-family variance receipt (mirror of §8)
      - anti-leakage regression-test receipt (G0)
      - wrong-prior verification receipt (G1)
      - non-ceiling headroom receipt (G2)
      - premise-audit stub receipt (future work; explicitly non-evidential)
      - L4-only Modal cost receipt (G6)
  - path: experiments/concern_gated_retrieval_e2/wave0/PROMOTION_CONTRACT.md
    contains:
      - this file, unchanged after freeze
```
