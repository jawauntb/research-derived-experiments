# Wave 1a Promotion Contract (COGR-E2a)

Frozen, non-compensatory promotion contract for the Wave 1a deliverable of
the Concern-Gated Retrieval E2 program. This file is authoritative. Where
it disagrees with anything else in this subtree, this file wins.

```yaml
claim_id: COGR-E2-WAVE1A-CONCERN-UPDATE-RULE-SCREEN
target: >-
  Screen the frozen Wave 0 concern-update rule (LoggedProbePolicy
  + update_concern with IPS and DR variants + poisoning guard) on
  fixed withheld geometry from the Wave 0 build_withheld_graph, under
  the Wave 0 adversarially wrong prior, over the confirmatory seed
  range 200000-201999, on the three procedural families in
  ../wave0/PREREGISTRATION.md §6.
wave: 1a
non_compensatory: true
scope:
  positive:
    - "Wave 1a is a concern-recovery SCREEN for the concern-update rule."
    - "Wave 1a decides whether the rule survives every fatal gate in PREREGISTRATION.md §5 and every per-family threshold in §6."
    - "Wave 1a publishes IPS and DR off-policy estimates of the rule against the Wave 0 frozen-wrong baseline."
    - "Wave 1a records propensity-weighted coverage of the true commitment region and rejects rows below the preregistered floor."
  negative:
    - "Wave 1a does NOT claim learned memory geometry (Wave 1b / COGR-E2b object)."
    - "Wave 1a does NOT establish the L1 dual-source-retrieval mechanism claim."
    - "Wave 1a does NOT establish the L2 history-derived-concern-recovery claim."
    - "Wave 1a does NOT claim semantic meaning or selfhood."
    - "Wave 1a does NOT execute untrusted-source poisoning stress; the wave registers the poisoning-guard tolerance shape only."
    - "Wave 1a does NOT block Wave 1b's L1 rows on failure. A Wave 1a KILL kills the update rule as written but does not invalidate a separate L1 mechanism claim in Wave 1b."
    - "Wave 1a does NOT touch calibration seeds 100000-100999; the template-split guard raises LeakageError on misuse."
    - "Wave 1a does NOT use non-synthetic history; the premise audit remains future work."
gates:
  - id: G0_ANTI_LEAKAGE
    kind: integrity
    description: >-
      Every evaluator-only field enumerated in
      ../wave0/PREREGISTRATION.md §4.1 is unreachable from any Wave 1a
      policy code path. The IntegrityAudit AST walker gates every
      callable that enters the confirmatory sweep. A single audited
      violation is a fatal integrity failure that retroactively demotes
      any dependent statistic.
  - id: G1_COVERAGE
    kind: coverage
    description: >-
      For every (family, condition) cell that logs receipts,
      propensity-weighted coverage of the true commitment region under
      the logging policy meets the PREREGISTRATION.md §5.1 floor
      (coverage_{f,c} >= 0.01). Pre-analysis rejection rate on any
      (family, condition) cell must not exceed 5% of that cell's
      confirmatory rows.
  - id: G2_PROPENSITY_ACCOUNTING
    kind: propensity
    description: >-
      Every logged selection_propensity lies strictly in (0, 1]; every
      update_concern call uses a homogeneous template_family_split; every
      aggregated update carries the poisoning-guard receipt with
      max_source_influence = 1.0; the IPS ESS floor of 50 per
      (family, condition) cell is met.
  - id: G3_SPECIFICITY
    kind: specificity
    description: >-
      On every family the online-learned condition beats every
      info-matched generic value / priority / recency baseline in the
      Wave 0 slate by at least sigma_hat_best_matched_wave0, AND neither
      the shuffled (C4) nor wrong-agent (C5) condition mean is within
      sigma_hat_multiplicative_wave0 of the online-learned mean.
  - id: G4_PER_FAMILY_EFFECT
    kind: effect
    description: >-
      On every family f the paired-seed lower confidence bound
      delta_hat_{f,v} - 2 * sigma_delta_{f,v} meets or exceeds the
      per-family threshold delta_thresh_E2a_{f} in PREREGISTRATION.md
      §6.2 for at least one candidate variant v in {ips, dr}. Aggregate
      success cannot hide a per-family reversal.
  - id: G5_SEED_INDEPENDENCE
    kind: integrity
    description: >-
      Confirmatory seed range 200000-201999 is disjoint from calibration
      range 100000-100999, verified by the Wave 0 template-split guard
      raising LeakageError on any calibration seed touched by a
      confirmatory code path. Wave 1a runs with
      COGR_WAVE0_CONFIRMATORY_RUN=1 set at Modal spawn time.
  - id: G6_CODE_FREEZE
    kind: reproducibility
    description: >-
      WAVE1A_ANALYSIS_HASH is a SHA-256 of every tracked file under
      experiments/concern_gated_retrieval_e2/wave1a/** in sorted path
      order, matches the value mirrored into PROVENANCE.md, and is
      written only after the confirmatory Modal run completes and every
      per-family threshold in §6.2 has been tested. The referenced
      WAVE0_ANALYSIS_HASH matches ../wave0/PROVENANCE.md §6 byte-for-byte.
  - id: G7_MODAL_BUDGET
    kind: operational
    description: >-
      Modal execution used L4 GPUs only, app name
      research-derived-cogr-wave1a-e2a, max_containers <= 32, Doppler
      scope /Users/jawaun/superoptimizers. Deploy occurred before spawn
      and the deployed image hash is recorded in PROVENANCE.md.
promotion_rule: >-
  Wave 1a is promoted to "screen PASS" iff every gate G0-G7 reports
  PASS and G4 reports PASS for at least one candidate variant v in
  {ips, dr}. Non-compensatory: a single gate FAIL kills the wave
  regardless of every other gate's status. A screen PASS opens Wave 1b;
  it does NOT establish learned geometry, an L1 mechanism claim, or an
  L2 concern-recovery claim.
demotion_rule: >-
  If Wave 1b (or any downstream reviewer) discovers that a Wave 1a
  passing row violated any G0-G7 gate, the Wave 1a PASS is
  retroactively demoted to KILL. All Wave 1b rows that consumed the
  invalidated screen receipt are marked non-evidence. A new Wave 1a
  hash must be produced before Wave 1b can reopen. No post-hoc
  threshold swap or seed-range swap is permitted.
non_blocking_of_L1: >-
  A Wave 1a KILL does not block Wave 1b's L1 dual-source-retrieval
  rows. Wave 1a's target is the concern-update rule; Wave 1b's L1 gate
  is the frozen non-ceiling concern crossed with learned, frequency-
  matched, and oracle geometry. The two gates are separable by the
  roadmap's noncompensatory rule ("Failed E2a concern recovery
  withholds L2 but does not block E2b's L1 rows",
  docs/concern_gated_retrieval_research_program.md § "Wave 1 — staged
  mechanism identification").
non_blocking_of_L2: >-
  A Wave 1a PASS is a screen result, not an L2 claim. L2 promotion
  requires the Wave 1b crossed design (learned vs frequency-matched vs
  oracle geometry × frozen-wrong vs learned vs oracle concern) and the
  L2-specificity gates in Wave 1b's own preregistration.
replayable_knobs:
  - path: PREREGISTRATION.md §7
    description: >-
      Only LoggedProbePolicy.epsilon (up to 0.10), update_concern.eta
      (within [0.05, 0.20]), and cell-level rejection replay within the
      reserved seed range 200900-201999 (capped at 30% of that cell's
      receipts) may be rerun after a fatal gate rejection. Every other
      knob is frozen; a change is a redesign requiring a new
      preregistration hash. Honor-the-preregistration rule is
      authoritative.
artifacts_required:
  - path: experiments/concern_gated_retrieval_e2/wave1a/PREREGISTRATION.md
    contains:
      - signed WAVE1A_ANALYSIS_HASH in §8
      - byte-for-byte verified WAVE0_ANALYSIS_HASH reference in §6
      - populated per-family thresholds in §6.2
  - path: experiments/concern_gated_retrieval_e2/wave1a/PROVENANCE.md
    contains:
      - confirmatory Modal deploy hash
      - confirmatory seed-range receipt (200000-201999)
      - per-family delta_hat and sigma_delta receipt (mirror of §6)
      - coverage-audit receipt (G1)
      - propensity-accounting receipt (G2)
      - specificity receipt (G3)
      - anti-leakage regression-test receipt (G0)
      - L4-only Modal cost receipt (G7)
      - screen decision receipt (PASS / KILL, per candidate variant)
  - path: experiments/concern_gated_retrieval_e2/wave1a/PROMOTION_CONTRACT.md
    contains:
      - this file, unchanged after freeze
```
