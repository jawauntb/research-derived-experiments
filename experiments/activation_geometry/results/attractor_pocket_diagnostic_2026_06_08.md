# Attractor Pocket Diagnostic - 2026-06-08

## Question

Does the stable Pythia layer-5 `attractor` -> `attractor_network` matched-context pocket survive a focused distractor sweep, adversarial near-neighbor controls, and a second Pythia-family checkpoint?

The previous replication promoted only a narrow residual: layer-5 target patches from `attractor_network` reliably increased the `attractor network` answer margin when the source prompt was about `attractor`. This run asks whether that residual is a clean conceptual bridge or a broader answer-choice basin around nearby attractor-family terms.

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_deduped_attractor_pocket.json
artifacts/activation_geometry/modal_pythia_70m_attractor_pocket.json
```

Grid:

- Models: `EleutherAI/pythia-70m-deduped`, `EleutherAI/pythia-70m`
- Layers: primary `5`, backup `4`, control `6`
- Context variant: `0`
- Prompt frames: closest-related and stable-state-dynamics
- Positive distractors: `prototype`, `schema`, `conceptual_space`, `representation_manifold`
- Target near-controls: `attractor` -> `prototype`, `attractor` -> `schema`, with `attractor_network` as distractor
- Source near-controls: `prototype` -> `attractor_network`, `schema` -> `attractor_network`, with `attractor` as distractor
- Patch modes: `target`, `distractor`, `random`, `source_noop`
- Option orders: `std`, `tds`, `dst`
- Patch alpha: `1.0`
- Seed: `20260608`

Command template:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_attractor_pocket_diagnostic.py --model-id <MODEL> --primary-layer 5 --backup-layer 4 --control-layer 6 --max-length 128 --context-variant 0 --patch-alpha 1.0 --patch-modes target,distractor,random,source_noop --option-orders std,tds,dst --seed 20260608 --out <OUT>
```

Sanity gate:

- Max absolute `source_noop` aggregate delta: `0.0` for both models.
- This confirms that patching the source activation into its own prompt remains an exact hook-surface no-op.

Focused gate:

- All positive distractor/frame rows should pass target-over-best-control specificity at the primary layer.
- Near-neighbor controls should not pass the same target-specific gate.
- The same result should be visible on the second checkpoint before claiming checkpoint-stable bridge structure.

## Gate Summary

| Model | Role | Positive passes | Near-control passes | Mean positive delta | Mean positive advantage | Focused gate |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `EleutherAI/pythia-70m-deduped` | primary | 6/8 | 4/8 | 0.078 | 0.029 | fail |
| `EleutherAI/pythia-70m-deduped` | backup | 3/8 | 1/8 | 0.053 | 0.007 | fail |
| `EleutherAI/pythia-70m-deduped` | control | 2/8 | 4/8 | 0.042 | -0.029 | fail |
| `EleutherAI/pythia-70m` | primary | 4/8 | 1/8 | 0.002 | -0.006 | fail |
| `EleutherAI/pythia-70m` | backup | 2/8 | 1/8 | -0.004 | -0.024 | fail |
| `EleutherAI/pythia-70m` | control | 2/8 | 1/8 | 0.001 | -0.016 | fail |

## Primary Positive Rows

| Model | Frame / distractor | Target delta | Best control | Advantage | Pass |
| --- | --- | ---: | --- | ---: | --- |
| deduped | closest / conceptual_space | 0.138 | distractor | 0.009 | yes |
| deduped | closest / prototype | 0.205 | distractor | 0.161 | yes |
| deduped | closest / representation_manifold | 0.012 | source_noop | 0.012 | yes |
| deduped | closest / schema | 0.032 | random | 0.012 | yes |
| deduped | dynamics / conceptual_space | 0.129 | distractor | 0.024 | yes |
| deduped | dynamics / prototype | 0.158 | distractor | 0.090 | yes |
| deduped | dynamics / representation_manifold | -0.099 | source_noop | -0.099 | no |
| deduped | dynamics / schema | 0.044 | distractor | 0.018 | no |
| non-deduped | closest / conceptual_space | 0.064 | source_noop | 0.064 | yes |
| non-deduped | closest / prototype | -0.046 | source_noop | -0.046 | no |
| non-deduped | closest / representation_manifold | -0.039 | random | -0.062 | no |
| non-deduped | closest / schema | 0.018 | source_noop | 0.018 | yes |
| non-deduped | dynamics / conceptual_space | 0.052 | random | 0.036 | yes |
| non-deduped | dynamics / prototype | 0.001 | distractor | -0.013 | no |
| non-deduped | dynamics / representation_manifold | 0.019 | random | 0.011 | yes |
| non-deduped | dynamics / schema | -0.055 | source_noop | -0.055 | no |

## Leaky Near Controls

| Model | Kind | Pair | Target delta | Best control | Advantage |
| --- | --- | --- | ---: | --- | ---: |
| deduped | source near-control | `closest:prototype->attractor_network/d=attractor` | 0.141 | distractor | 0.095 |
| deduped | source near-control | `dynamics:prototype->attractor_network/d=attractor` | 0.181 | distractor | 0.119 |
| deduped | target near-control | `closest:attractor->schema/d=attractor_network` | 0.147 | random | 0.006 |
| deduped | target near-control | `dynamics:attractor->schema/d=attractor_network` | 0.253 | distractor | 0.035 |
| non-deduped | source near-control | `dynamics:prototype->attractor_network/d=attractor` | 0.143 | source_noop | 0.143 |

## Interpretation

The clean bridge claim fails the focused gate.

The deduped checkpoint still shows a real residual: six of eight positive rows pass in the primary layer, the mean target-margin delta is `0.078`, and the mean target-over-best-control advantage is `0.029`. But the same layer also has four of eight near-neighbor control passes. That leakage is too large to claim a selective `attractor` -> `attractor_network` conceptual bridge.

The non-deduped checkpoint weakens the residual further. Its primary positives pass only `4/8`, the mean positive target delta is approximately zero, and the mean target-over-best-control advantage is negative. This rejects checkpoint-stable bridge structure.

The most informative leakage is not random. In the deduped model, `prototype` -> `attractor_network` passes in both prompt frames when `attractor` is the distractor. That suggests the target activation can bias the answer surface toward `attractor network` even when the source concept is a different nearby cognitive term. The `attractor` -> `schema` target controls also leak in both prompt frames when `attractor_network` is the distractor, suggesting that the source prompt can support nearby cognitive targets too.

So the residual should be renamed:

```text
Pythia-70M-deduped layer 5 has an attractor-family answer-choice basin,
not a clean attractor-to-attractor-network bridge.
```

This is still useful. It says our intervention surface can reveal local answer-choice basins induced by matched-context final-token states, but the verifier currently cannot separate a narrow semantic bridge from a broader local target-label basin.

## Next Move

Run an answer-surface basin diagnostic before any free-form generation or steering demo:

- Add neutral-carrier patch prompts where the concept text is replaced by a minimal label-bearing sentence.
- Add relabel controls where answer labels are swapped for aliases or neutral symbols while source definitions remain intact.
- Add source-family sweeps around `attractor`, `prototype`, `schema`, `category` or the closest available substitute, and `conceptual_space`.
- Gate on whether the effect follows the semantic source/target relation, the answer label, or the option surface.

If the effect follows labels or option surface, treat this as an interface artifact and pivot to learned readout-conditioned probes. If it follows semantic source/target relation under relabeling, then return to bridge-patching with a stronger verifier.

## Discovery-Regime Audit

Question: does the focused attractor-network pocket survive distractor sweeps, adversarial near-neighbor controls, and second-checkpoint replication?

Current regime:

- Artifact types: matched-context patch payloads, specificity rows, focused gate summaries, near-neighbor leakage rows.
- Operations: distractor/frame sweep, target near-control, source near-control, second-checkpoint replication.
- Gates/verifiers: exact `source_noop` gate, positive distractor-sweep gate, near-control leakage gate, checkpoint-stability gate.
- Known limitations: only two Pythia-70M checkpoints, one context variant, answer-choice prompt surface only.

Action class:

- Retrieval/search/discovery: search inside the matched-context patching regime.
- Why: this run changes prompts, distractors, controls, and checkpoint while preserving the same causal-patching artifact type and verifier family.

Experiment:

- Manifest/report paths: this report; local ignored payloads listed above.
- Positive targets: `attractor` -> `attractor_network` across two prompt frames and four distractors.
- Negative controls: `attractor` -> `prototype`, `attractor` -> `schema`, `prototype` -> `attractor_network`, `schema` -> `attractor_network`, plus distractor/random/source patch modes.
- Stress tests: prompt-frame sweep, distractor sweep, near-neighbor source/target swaps, second Pythia-family checkpoint.

Gate:

- Acceptance rule: promote the pocket only if all positive primary rows pass, near-neighbor controls clear, source no-op is exact, and the second checkpoint supports the effect.
- Withheld/rejected rule: reject a clean bridge claim if near-neighbor controls mimic the same target-specific pattern or if the effect weakens on the second checkpoint.

Results:

- Accepted artifacts: this report; `experiments/activation_geometry/attractor_pocket_diagnostic.py`; `experiments/activation_geometry/modal_attractor_pocket_diagnostic.py`.
- Rejected or withheld artifacts: clean `attractor` -> `attractor_network` bridge claim is rejected.
- Key metrics: deduped primary positives `6/8`; deduped primary near-controls `4/8`; non-deduped primary positives `4/8`; non-deduped primary near-controls `1/8`; max source-noop delta `0.0`.
- Variance or ablation: deduped has a stronger but leakier basin; non-deduped has a weaker basin and no positive mean advantage.

Residual content:

- Explained by old regime: matched-context final-token patching can bias answer-choice margins.
- New content outside old claim: the surviving pattern is broader than one semantic bridge and looks like an attractor-family answer-choice basin.
- Retractions or supersessions: supersede "Pythia layer-5 attractor-network pocket" with "Pythia-70M-deduped layer-5 attractor-family answer-choice basin."

Next move: implement the answer-surface basin diagnostic to distinguish semantic source/target effects from label/option-surface effects.
