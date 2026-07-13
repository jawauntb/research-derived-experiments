# E6 — Commitment-Surface Reward vs Self-Consistency Reward in a Self-Training Loop

**Frozen: 2026-07-13 (UTC).** Frozen before any E6 candidate pool, reward, or
round metric is produced or inspected. This preregistration authorizes **no GPU
run**: only a smoke/dev calibration may precede any confirmatory Modal spend,
mirroring E5's `confirmatory_ready` discipline. No gate threshold below may be
retuned from observed cells.

## Question

Recent self-training work (SRT, arXiv:2505.21444) shows a self-consistency
reward improves then **collapses** every base model — the temporal signature of
optimizing an *available* proxy that has no commitment surface. E6 asks: if the
self-reward is replaced by a **commitment-surface-survival reward** (patch-CE at
the `(a+b) mod n` commitment surface that survives a change-of-commitment
transport `T`), does the collapse disappear? This converts the commitment-surface
*criterion* into a training *objective* — the first test of whether the framework
governs learning **dynamics**, not just static verification.

## Competing explanations

- **H_intrinsic (collapse is intrinsic to self-training):** the collapse is a
  property of bootstrapping on self-generated labels; any label-free reward on
  the same candidate pools collapses. CS and SC both fail G1.
- **H_surface (a commitment surface prevents collapse):** collapse is the
  signature of a reward with no load-bearing surface. A reward gated on
  transport-surviving patch-CE stays load-bearing across rounds; CS passes G1
  while SC fails it on the *identical* candidate pools.

These are mutually exclusive at G1.

## Frozen design

Base model and task reuse the E4/E5 Pythia-LoRA modular-addition setup exactly.

- **Task:** `(a + b) mod n`, `n ∈ {13, 17, 23}`, strict-subset split
  `train_frac = 0.5`. Per cell freeze `S_train`, `S_ood`, `K_train`, `K_novel`
  (disjoint) via `e5_core.make_split` before any training.
- **Base model:** Pythia `{70m, 160m, 410m}`, LoRA rank 8, alpha 16, dropout
  0.05, lr 5e-4, weight_decay 0, grad_clip 1.0 (frozen E5 values).
- **Rounds:** `R = 6` self-training rounds. Each round: (1) sample a candidate
  pool, (2) score it under the arm's reward, (3) fine-tune `E_round = 40` epochs
  on reward-selected candidates, (4) measure.
- **Candidate pool (shared):** per round, for each `x ∈ S_ood ∪ (S_train+K_novel
  images)` sample `G = 8` generations at temperature 0.8 from the *current*
  adapter. The resulting `(input, generation)` pool `P_r` is frozen per round and
  handed **identically** to SC and CS, so any SC/CS difference cannot be
  attributed to data volume.

Reward arms (leakage-separated, exposure-matched like E5):

- **SC (self-consistency, baseline):** reward = agreement of a candidate with the
  self-majority vote over its `G` generations. Expected to collapse.
- **CS (commitment-surface survival):** reward = per-candidate normalized
  compatibility-subspace patch-CE at the `(a+b) mod n` surface (reuse #344
  spectral-mass-normalized subspace, `spectral_mass_fraction = 0.5`), **masked to
  zero unless it also survives the change-of-commitment transport `T`**
  (paraphrase prompt + a novel additive relabel `k ∈ K_novel`): a candidate is
  eligible only if patch-CE `≥ ε` at both the canonical and transported
  commitment. No `S_ood` truth label enters the CS reward.
- **GT (ground-truth ceiling):** reward = correctness against true `(a+b) mod n`.
- **A-ref (frozen control):** no self-training; adapter frozen at round 0.

CS and SC select the same **number** of candidates each round (top-fraction
`ρ = 0.5` of `P_r` by reward, ties broken by frozen candidate order) so
supervised exposure counts match. `ε = 0.05` (frozen E5 patch-CE threshold).

- **Seeds:** base seed **`20260713`**. Every RNG key is derived collision-free as
  `int.from_bytes(sha256(f"e6|{base_seed}|{namespace}|{size}|{n}|{arm}|{round}|{seed_slot}".encode()).digest()[:8], "big")`,
  namespaces `{"split","candidate","generation","subspace","transport"}`.
  Confirmatory `seed_slot ∈ {0,1,2}` (≥3 seeds per `(size,n)` cell).

### Post-smoke record of pre-run implementation resolution

This explanatory addendum was written after the readiness smoke. The following
underspecified runner details were nevertheless resolved in code and bound into
the implementation fingerprint before the first E6 candidate pool was
generated. Recording them here does not retroactively change any reward,
threshold, gate, or claim boundary above.

- All arms begin from one E5-matched supervised bootstrap on `S_train` for 160
  epochs. The resulting LoRA adapter is copied byte-for-byte to SC, CS, and GT;
  A-ref is that same adapter frozen at round 0.
- The shared current-adapter proposer is a symmetric `paired_half_mix`. For each
  input and round, frozen candidate order alternates four draws from the current
  SC adapter with four draws from the current CS adapter. The combined eight-draw
  pool is hashed once and handed unchanged to both arms. This avoids privileging
  either diverged adapter while retaining the preregistered `G=8` pool size.
- One L4 worker owns a complete `(size,n,seed_slot)` stratum so paired adapter
  state and candidate pools cannot cross process boundaries. It emits separate
  analytical cells for the requested arms; the confirmatory grid therefore has
  108 analytical cells but 27 coupled GPU strata.

## Frozen analysis

Per round `r` and arm, record: canonical `S_ood` accuracy, paraphrase `S_ood`
accuracy, normalized compatibility-subspace patch-CE (canonical and transported),
novel-`k` equivariance accuracy, an E5-style generator-vs-coverage separation
(reuse `e5_core` logic: generator gain = novel-`k` equivariance gain; coverage
gain = correct-label share among selected candidates), the selected candidate
count, and a **collapse indicator** `collapse_r = 1[ acc_r < peak_{≤r} − τ ]`
with frozen `τ = 0.05`. Report full per-round trajectories; **aggregate-only
reporting is prohibited** — the collapse claim is about the trajectory shape.

All numerical gates are macro means over matched valid confirmatory cells
(exact E5 Cartesian-grid completeness + integrity audit required first).

## Gates & kill criteria

Integrity gates (all mandatory, per E5 `integrity_pass`):
- **I1** `S_train ∩ S_ood = ∅`, `K_train ∩ K_novel = ∅`; no `K_novel` shift used
  in any CS reward's canonical (non-transport) term.
- **I2** CS receives zero `S_ood` truth labels; the CS reward key contains no
  candidate correctness.
- **I3** SC and CS consume the *same* frozen pool `P_r` and select the same
  candidate count every round (per-round assertion).
- **I4** Normalized patches remove the configured spectral-mass fraction within
  `±0.02` in every patched matrix with nonzero LoRA mass.

Science gates (each a strict pass/fail; any failure reported as a failure):
- **G1 (no-collapse):** CS final-round canonical OOD `≥ peak_CS − τ` (`τ=0.05`).
  SC is expected to *fail* this. If CS also fails, H_surface is killed and
  H_intrinsic is supported.
- **G2 (load-bearing gain):** CS normalized canonical patch-CE is
  non-decreasing across rounds (allowing `≤0.01` dips) and final `≥ ε`.
- **G3 (transport survival):** CS's round-`R` patch-CE gain survives `T` —
  transported patch-CE `≥ ε` and paraphrase OOD lift over A-ref retains `≥75%`
  of the canonical lift (E5 transport-gate form).
- **G4 (not-mere-coverage):** CS's round-over-round generator gain exceeds its
  coverage gain by `≥0.10` (E5 separator). Failure blocks a generator
  interpretation even if G1–G3 pass.
- **G5 (exposure integrity):** I3 holds every round for every valid cell.

**Kill criteria.** H_surface is killed if CS fails G1, or if CS fails G2/G3
(reward not load-bearing / not transport-surviving), or if G4 fails (gain is
coverage, not generator learning). H_intrinsic is killed if CS passes G1–G4
while SC fails G1 on the identical pools. Any integrity failure kills the
affected cell and triggers a rerun; it is never repaired by relabeling.

The one-seed 70m/`n=13` smoke is harness validation only: it passes when SC/CS/
A-ref complete with finite per-round metrics and I1–I4 hold. It cannot support a
scientific claim, and it does not authorize the confirmatory grid.

## Claim boundary

A pass establishes that, **within Pythia-LoRA modular addition**, a
commitment-surface-survival reward prevents the self-consistency collapse and
that the framework's static criterion also governs self-training dynamics. It
does **not** establish: (i) collapse-prevention for general reasoning tasks or
non-group generators; (ii) that CS matches the GT ceiling (GT is a ceiling
reference, not a gate target); (iii) any claim in language or beyond modular
arithmetic; (iv) that a single successful transport `T` implies survival under
arbitrary commitments. E6 is a dynamics test on one aligned-generator regime.

## Rejected alternatives

- **Tuning reward weights / `ε` / `τ` post-hoc** to make CS pass — forbidden;
  all thresholds are frozen above.
- **Unpaired candidate pools** for SC vs CS — rejected; a difference would then
  confound reward with data volume (hence I3).
- **Single-round comparison** — rejected; collapse is a *temporal* signature and
  requires the full `R`-round trajectory.
- **Aggregate-only reporting** — rejected; peak-then-collapse is invisible in a
  final-round mean, so per-round trajectories are mandatory.
- **Full-adapter disable as the CS reward** — rejected in favor of the
  spectral-mass-normalized subspace patch (#344), so the reward compares equal
  fractions of adapter mass rather than conflating mechanism with magnitude.
