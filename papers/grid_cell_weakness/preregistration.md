# Paper A Scale-Up Pre-Registration

**Title (working):** Weakness Predicts the Toroidal Topology and Generalization of Population Codes

**Frozen:** 2026-06-28, before any grid-cell-RNN sweep.

## Question

Does **weakness** — the symbolic flagship's reparameterization-invariant predictor of OOD
generalization — also predict the **topology** of a learned population code on a real spatial task,
and does that topology mediate generalization?

The flagship established, on small symbolic and 16×16 vision tasks, that weakness
`W_G(f) = |{g∈G : ∃h∈G, ∀x, f(g·x)=h·f(x)}|` predicts OOD where train loss, MDL, compression, and
flatness all fail (cyclic/dihedral 100% vs 0%; neural r≈+0.81 at 256 and 1024 models; causal
augmentation lift +51.5pp). This pre-registration scales weakness onto the path-integration task that
yields the **entorhinal torus** (Gardner et al. 2022; Sorscher–Ganguli grid-cell-from-RNN), where
three quantities should coincide if and only if the network has discovered the translation group:
weakness (a scalar), Fourier/irrep structure (a mechanism), and toroidal homology (an observable).

This is a confirmatory test of the **Fourier ↔ weakness ↔ torus** triangle from
[../../notes/weakness_topology_program_synthesis.md](../../notes/weakness_topology_program_synthesis.md).

## Environment

A recurrent network performs **2-D path integration**: given a sequence of velocity inputs it
predicts position via a place-cell-like readout over a square arena. Trained networks are known to
develop periodic ("grid") rate maps; a single grid module's population activity lies on a 2-torus.

- Self-contained reimplementation (~Sorscher–Ganguli recipe): velocity-driven RNN/GRU, place-cell
  target basis, L2 + nonnegativity-style regularization. **No external repository is required** —
  public grid-cell repos are unreachable from this environment (proxy is repo-scoped; `git ls-remote`
  to `ganguli-lab/grid-pattern-formation` returns 403). `torch`, `numpy`, and persistent-homology
  libraries (`ripser`/`persim`/`gudhi`) install via pip (`pypi` is on the egress allowlist).
- Group of interest: the **2-D translation group** of the arena (toroidalized for the periodic code),
  approximated on a finite grid Zₙ×Zₘ.

## Conditions (what varies across the network population)

Mirror the flagship's augmentation-gradient design so weakness varies by construction:

| Condition | Training augmentation / regime | Expected weakness |
|---|---|---|
| `full_translation` | translation-augmented trajectories (full group) | high |
| `partial_translation` | subset of translations only | mid |
| `none` | no augmentation | low–mid |
| `wrong_group` | pixel/state-permutation "augmentation" (matched count, wrong group) | null control |
| `random_shift` | random non-group jitter (soft null) | null control |

Sweep ≥ 64 networks per condition across random seeds and 2 architectures (vanilla RNN, GRU),
following the 256/1024-model precedent. All sweeps are seeded and logged.

## Measured quantities (per network)

| Quantity | Operationalization |
|---|---|
| `weakness_translation` | fraction of translations g for which the population code transforms consistently, `r(x+Δ) ≈ T_Δ r(x)` under a fit linear `T_Δ`; normalized to [0,1] |
| `toroidal_score` | persistence-weighted closeness of the population point cloud's Betti numbers to (b₀,b₁,b₂)=(1,2,1); continuous, from `ripser` H₀/H₁/H₂ persistence ratios |
| `ood_accuracy` | path-integration decoding accuracy on **held-out arena geometry** (larger arena / novel trajectory distribution) |
| `fourier_pr` | participation ratio of the spatial DFT of single-unit rate maps (low = spectrally concentrated / few aligned irreps) |
| classical baselines | train loss, val loss, parameter L2, Hutchinson sharpness, gridness score |

## Gates

The triangle claim passes only if all hold (population-level unless noted; bootstrap 95% CIs):

| Gate | Criterion |
|---|---|
| G1 manifold recovered | in `full_translation`, median (b₀,b₁,b₂)=(1,2,1) with significant H₁ persistence in ≥ 60% of nets |
| G2 weakness↔topology | Spearman ρ(`weakness_translation`, `toroidal_score`) ≥ 0.5, and ≥ 2× the best classical baseline |
| G3 weakness↔OOD | Spearman ρ(`weakness_translation`, `ood_accuracy`) ≥ 0.5, exceeding train loss / val / flatness / parameter L2 by ≥ 2× |
| G4 topology mediates | partial ρ(weakness, OOD `|` toroidal_score) drops by ≥ 50% vs the raw ρ (topology carries the weakness→OOD signal, not three independent correlations) |
| G5 spectral leg | high-weakness nets show low `fourier_pr` (spectral concentration); ρ(`weakness_translation`, −`fourier_pr`) ≥ 0.5 |
| G6 causal | `full_translation` raises both `toroidal_score` and `ood_accuracy` vs `none` by a pre-set margin, exceeding `random_shift`; paired by seed/architecture (mirrors the +51.5pp augmentation result) |

## Negative-control expectations

- `wrong_group` weakness must be **null or negatively** correlated with OOD and `toroidal_score`
  (mirrors the flagship's wrong-group control at r≈−0.12 to −0.34).
- `random_shift` is a **soft** null (a dense shift set passively overlaps the translation group); it
  may lift OOD modestly but must stay below `full_translation`.
- Classical baselines (loss, val, flatness, parameter L2) must **not** match weakness on G2/G3.
- `gridness` (a hand-designed grid metric) is allowed to correlate; the claim is that weakness is
  **substrate-general** (it is defined without grid-specific priors), not that it beats every
  bespoke spatial statistic.

## Interpretation Matrix

| Result | Interpretation |
|---|---|
| G1–G6 pass | weakness governs whether a population code carries the task's toroidal topology, and topology mediates generalization — the triangle holds on a real task |
| G2 passes, G3 fails | weakness tracks geometry but not generalization at this scale; topology is decorative, not load-bearing |
| G3 passes, G2 fails | weakness predicts OOD by a non-topological route; the torus is incidental |
| G4 fails (G2,G3 pass) | weakness and topology each predict OOD independently; no single mediating object |
| G6 fails (correlational gates pass) | relationship is correlational only; defer causal language |
| only `wrong_group`/baselines move | weakness signal is an artifact of the augmentation-count confound |

## Brain-data extension (deferred, high-variance)

The notoriety claim — that `weakness_translation` tracks toroidal integrity in **biological** grid
cells (Gardner et al. 2022) — is **not testable from this environment** (external data hosts are
proxy-blocked). It is registered here as a **prediction**: applied to the published recordings, weakness
should correlate with H₁-persistence of the population torus across modules/animals. Run only in an
environment with data access; report as a separate confirmatory study, not folded into the network claim.

## Reward-deformation follow-up (Paper B seed)

After G1–G6, introduce a reward location and test the Paper B claim: reward **deforms** the torus by
**locally lowering weakness** (breaking translation symmetry) to raise local decoding resolution.
Pre-registered separately once Paper A locks.

## What This Does Not Claim

This preregistration does not claim consciousness, biological realism of the RNN, or that the torus is
the only code for space. It does not claim weakness beats every bespoke spatial statistic. It tests one
falsifiable proposition: that a single substrate-general scalar (weakness) predicts the topology and
out-of-distribution generalization of a learned population code, and that the topology mediates the
generalization. Weakness is treated as a selection pressure measured *after* validity, consistent with
the flagship's broad-excluder caveat.

---

## Frozen Addendum: Reward-Deformation Exponent Gate

**Frozen:** 2026-07-02, before the large Modal reward-deformation sweep.

This addendum pre-registers the decision rule for the rate-distortion "Newton" test in
`experiments/grid_cell_weakness/modal_reward_deformation_sweep.py`. The prior CPU result showed that
adding a finite-capacity bottleneck causally moves the area-density exponent from approximately
`+0.07` to approximately `+0.30`, but it did **not** confirm the 2-D prediction `alpha = 1/2`.
The open question is whether the plateau near `1/3` is explained by an effectively 1-D
reallocation, or whether a genuinely 2-D reward geometry reaches the predicted exponent.

### Primary estimand

For each reward geometry and amplitude, regress `log sqrt(det g(x))` on `log w(x)` over spatial
bins with finite positive metric density. The slope is the area-density exponent `alpha`. The
derived effective dimension is reported as:

`d_eff = 2 alpha / (1 - alpha)`.

The primary comparison is at amplitude `A = 6`, with the full amplitude sweep (`A in {3,6,12}`)
used to check stability and peak-resolution scaling.

### Locked hypotheses

| Reward geometry | Interpretation | Pre-registered prediction |
| --- | --- | --- |
| `stripe` | one coordinate is value-weighted, so allocation is effectively 1-D | `alpha` near `1/3` |
| `aniso2d` | both coordinates are value-weighted, so allocation is genuinely 2-D | `alpha` near `1/2` |
| `point` | radially symmetric bump; diagnostic for the earlier plateau | resolves by measured `d_eff` |

### Decision gate

The 2-D rate-distortion law is counted as confirmed only if, at `A = 6`:

1. `aniso2d` has bootstrap standard error `<= 0.02` for `alpha`, its 95% CI excludes `1/3`, and its
   mean is closer to `1/2` than to `1/3`;
2. `stripe` has bootstrap standard error `<= 0.02`, its 95% CI includes or is closer to `1/3` than
   `1/2`, and the `stripe` vs `aniso2d` exponent gap has a bootstrap 95% CI excluding zero;
3. coverage and log-log fit diagnostics are reported for every cell; low-coverage or poor-fit cells
   may be flagged but not selectively removed unless a mechanical worker failure is documented.

If all geometries remain near `1/3`, or if `aniso2d` fails to separate from `stripe`, the 2-D law is
not confirmed as stated. The honest conclusion then becomes a measured effective-dimension law
(`d_eff` near 1 in this harness), not a Newton-style confirmation of `alpha = 1/2`.

### Precision and scaling rule

The sweep should be run on Modal with enough seeds to reach bootstrap standard error `<= 0.02` for
the primary exponents whenever the platform quota permits. If the first large sweep misses this
precision target, dispatch additional seeds with a non-overlapping `base_seed` and combine the JSONs
before writing the result report. If Modal quota, package failure, or wall-clock interruption prevents
the target, report the achieved uncertainty plainly and do not call the exponent gate decisive.

No tuning may use the exponent value itself. Harness tuning is allowed only for mechanical worker
success and for the Paper A emergence precondition (`betti_match_torus` in `full_translation`), never
to move `alpha` toward `1/2`.
