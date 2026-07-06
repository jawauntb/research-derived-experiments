# Benchmarking Causally Grounded Finite Agents

**Condensed Design Note for a Proxy-Resistant Agent Benchmark**

**Jawaun Brown**
2026-07-06

## Source Note

This note is a benchmark-facing condensation of the research program in this
repository. It is not a replacement for the full empirical reports.

Portable source paths:

- umbrella benchmark: `docs/causally_grounded_agents_benchmark.md`
- release schema: `docs/causally_grounded_agents_release_schema.md`
- long-horizon benchmark card: `experiments/long_horizon_bottleneck/BENCHMARK_CARD.md`
- long-horizon paper: `papers/long_horizon_bottleneck/paper.pdf`
- structure-compatible generalization: `papers/structure_compatible_generalization/`
- Metaphysics archive name for this note:
  `32_Benchmarking_Causally_Grounded_Finite_Agents_2026_07_06.pdf`

## Benchmark North Star

A finite agent is not grounded because it succeeds. It is grounded when the
variables that matter for future control are represented, attributed, queried,
and committed at the causal surfaces where action is selected.

## 1. Purpose

This benchmark should test whether agents succeed for the right causal reasons.
Many current evaluations score final task success, but an agent can answer
correctly by shortcut, uniform storage, stale confidence, source confusion, or
local final-token cues. The benchmark should therefore evaluate whether
future-relevant variables are tracked at the places where they actually control
action: predictive models, self/world attribution, inquiry mechanisms, memory
states, tool calls, repairs, generated action strings, and OOD transformation
structure.

Allowed claim: the benchmark is not a consciousness test, not a production
reliability certificate, and not a general solution to OOD generalization. It
is a controlled diagnostic suite for finite agents whose behavior may be proxy
supported or causally grounded.

Design target: a good benchmark instance makes the shortcut behaviorally
tempting while making the causal structure measurable. Final accuracy should be
necessary but insufficient.

## 2. Failure Modes

| Failure mode | What it looks like | Benchmark countermeasure |
|---|---|---|
| Shortcut success | The agent gets the answer right through a local cue, artifact, or spurious invariant. | Structure-compatible OOD split, wrong-group control, matched distractors. |
| Ungrounded policy | A learned representation contains the relevant signal, but a separate policy learner fails to exploit it. | Planning from an action-conditioned consequence model; policy/distillation parity. |
| Gauge-symmetric attribution | The model predicts total outcomes correctly but assigns self-caused and world-caused components arbitrarily. | Source-attribution gates, null intervention, oracle/source-label upper bound. |
| Learned silence | The agent stops probing after convergence and fails to restart inquiry after the world changes. | Regime-shift re-engagement, no-false-calm gate. |
| Uniform memory | The agent stores every early variable equally or uses the final query cue rather than tracking the future-critical variable. | Moved-bottleneck specificity, visible-control null, causal patch. |
| Brittle commitment | The agent knows the value but fails when it must commit through a tool, schema, alias, repair, or generated action surface. | Tool-call, repair, schema, stochastic-failure, and generated-action suites. |

## 3. Four Benchmark Laws

### Law 1: Predictive Policy Closure

When an agent learns action-conditioned change in what it cares about, the
consequence model itself can become the policy by action argmax. In the
planning-from-concern result, an action-conditioned Delta-E model reaches full
return and near-perfect action accuracy on the XOR task without optimal-action
labels or policy-gradient training.

### Law 2: Reafferent Identifiability

Input factorization is not identification. A self head that sees action and a
world head that does not can still split the same total prediction arbitrarily.
Source attribution requires a gauge-breaking signal such as explicit labels,
active null intervention, temporal asymmetry, interventional contrast, or a
distinct source-pinning loss.

### Law 3: Re-Engagement Floor

Efficient inquiry is not adaptive inquiry. An agent can learn to probe
selectively, then stop probing after convergence and fail to restart after a
regime shift. In changing worlds, quiet is not evidence of stability.

### Law 4: Commitment-Surface Memory

Memory becomes agent-relevant where it is coupled to a future commitment
surface: a later action, tool call, repair, emitted JSON value, or causal
readout. The moved-bottleneck diagnostic tests whether hidden-state sensitivity
follows the moved future-critical slot rather than any matched distractor.

## 4. Recommended Benchmark Suites

| Suite | Core setup | Primary measurements | Current status |
|---|---|---|---|
| A. Consequence-to-action | Train on observation, action, observed Delta-E; evaluate action by model argmax. | Return, action accuracy, encoder necessity, planning/distillation parity. | Strong. |
| B. Reafferent source attribution | Observed outcome equals self-caused action effect plus exogenous or mediated world shock. | Self MAE, world MAE, action/attribution dissociation, gauge-breaker benefit. | Strong with architecture ceiling. |
| C. Re-engagement under world change | A hidden hazard or rule changes after convergence. The agent must reopen inquiry despite prior confidence. | Post-shift probe rate, no-false-calm, cost-adjusted return, value-of-information proxy. | Partial; active bottleneck. |
| D. Long-horizon moved bottleneck | Matched early clues; one becomes future-critical after a delay; critical slot moves across runs. | Final accuracy, memory specificity, rank, visible-control null, patch/readout effect. | Hardened. |
| E. Tool commitment and repair | The critical variable must be emitted through a tool call, schema, alias, JSON field, or repair after failure. | Schema validity, parsed slot/value, repair slot/value, no-op after success. | Hardened. |
| F. Structure-compatible OOD | Training admits shortcut and transformation-compatible rules; deployment is generated by known or inferred transformations. | Compatibility score, wrong-group null, OOD-free model selection, OOD accuracy after selection. | Strong, needs unified packaging. |

## 5. Scoring Model

Report a vector score rather than collapsing everything into one leaderboard
number. A single scalar invites proxy optimization; the benchmark should
preserve diagnostic separability.

| Score axis | Question | Example metrics |
|---|---|---|
| Behavior | Does the agent succeed at the task? | Final accuracy, return, tool success. |
| Causal representation | Is the internal structure specific to the future-relevant variable? | Moved-slot specificity, latent displacement, causal patch effect. |
| Attribution | Does the agent assign outcomes to self versus world correctly? | Source MAE, gauge-breaking improvement, oracle gap. |
| Inquiry | Does the agent probe when information is valuable and re-engage after change? | Probe efficiency, post-shift probe floor, no-false-calm. |
| Commitment | Does the tracked variable survive the action interface? | Parsed field correctness, repair correctness, schema validity. |
| Generalization | Does the learned function preserve deployment-generating structure? | Compatibility, wrong-group control, OOD-free selected OOD. |

Minimum pass rule: a model should not be called causally grounded unless it
passes behavior plus at least one structure-specific gate tied to the benchmark
condition.

## 6. Anti-Cheat Controls

- Matched distractors: early variables should match the critical variable in
  frequency and salience.
- Visible controls: when the answer is visible at query time, early-slot
  specificity should collapse.
- Wrong-group controls: compatibility with irrelevant transformations should be
  null or negative.
- Shuffled-source controls: shuffled self/world labels should lower attribution
  quality even if behavior remains partly competent.
- Fixed-action localization: hidden specificity should not merely reflect the
  model generating a different answer string.
- Cost-aware inquiry: probe rate, uncertainty signal, and outcome error should
  be checked together.
- Post-shift audits: agents should be tested after confidence has had time to
  become stale.

## 7. Latest Incorporated Result

The long-horizon moved-bottleneck work now includes a black-box API surface.
Gemini 3.1 Flash-Lite, Anthropic Haiku 4.5, and OpenAI GPT-4.1 Nano pass the
registered prompt-family behavior suite. The external-stress suite found an
OpenAI dispatch negative, but a 720-request Modal CPU follow-up narrowed that
negative sharply: across 16 `(stress, critical slot)` cells, only the 8-slot,
gap-16, critical-slot-0 cell reproduced as a failed-repair value miss. Controls
passed, and neutral wording, value-copy assistance, and repair hinting all
passed for the reproduced cell.

The allowed interpretation is narrow: the OpenAI result is a real but sparse
black-box repair-surface pressure point, not a broadly stable dispatch failure
and not hidden-state evidence.

## 8. Release Package

A serious benchmark release should make every gate auditable and every failure
interpretable. Suggested release artifacts:

- task generators with fixed seeds and declarative manifests;
- JSONL row schema for each episode, model, condition, seed, prompt family, and
  provider where applicable;
- behavior-only black-box evaluator plus optional hidden-state evaluator for
  open models;
- reference lower/upper baselines;
- benchmark card describing what each suite can and cannot certify;
- figure-regeneration scripts or committed result reports.

The shared schema is defined in
`docs/causally_grounded_agents_release_schema.md`.

## 9. Interpretation Boundaries

Do not claim that the benchmark certifies consciousness, full autonomy, general
intelligence, or production reliability. Do not claim that one pass proves
universal OOD robustness. The benchmark should instead claim controlled
evidence about whether success is tied to the variables and causal surfaces
that future action depends on.

Strong allowed claim: a model that passes the relevant gates has shown, in a
controlled finite setting, that its behavior is less likely to be a pure proxy
artifact because the task-relevant variable is tracked at the required
prediction, attribution, inquiry, memory, or commitment surface.

## 10. Primary Source Papers

Primary internal papers and benchmark sources are stored in this repository and
archived as PDFs in the Metaphysics of Intelligence folder.

- Brown, Jawaun. Planning from Concern. 2026. Repo:
  `papers/planning_from_concern/paper.pdf`. Archive:
  `10_Planning_from_Concern_v2_2026_07_06.pdf`.
- Brown, Jawaun. First-Order Self. 2026. Repo:
  `papers/first_order_self/paper.pdf`. Archive:
  `16_First_Order_Self_v2_2026_07_06.pdf`.
- Brown, Jawaun. When the World Responds. 2026. Repo:
  `papers/world_responds/paper.pdf`. Archive:
  `22_World_Responds_Reengagement_Floor_2026_07_06.pdf`.
- Brown, Jawaun. Future Control Moves Memory. 2026. Repo:
  `papers/long_horizon_bottleneck/paper.pdf`. Archive:
  `31_Future_Control_Moves_Memory_2026_07_06.pdf`.
- Brown, Jawaun. Structure-Compatible Generalization. 2026. Repo:
  `papers/structure_compatible_generalization/`.
- Brown, Jawaun. Finite Representations Allocate Resolution and Generalization
  Under Structure. 2026. Archive:
  `unified_metric_weakness_portfolio/finite_representations_portfolio.pdf`.

## 11. External Citations To Include

- Brehmer, J., De Haan, P., Lippe, P., and Cohen, T. (2022). Weakly supervised
  causal representation learning.
- D'Amour, A. et al. (2022). Underspecification presents challenges for
  credibility in modern machine learning. Journal of Machine Learning Research.
- Geirhos, R. et al. (2020). Shortcut learning in deep neural networks. Nature
  Machine Intelligence.
- Houlsby, N., Huszar, F., Ghahramani, Z., and Lengyel, M. (2011). Bayesian
  active learning for classification and preference learning.
- Locatello, F. et al. (2019). Challenging common assumptions in the
  unsupervised learning of disentangled representations. ICML.
- Scholkopf, B. et al. (2021). Toward causal representation learning.
  Proceedings of the IEEE.
- Settles, B. (2009). Active Learning Literature Survey.
- Sutton, R. S. (1990). Integrated architectures for learning, planning, and
  reacting based on approximating dynamic programming. ICML.
- Sutton, R. S. et al. (2011). Horde: a scalable real-time architecture for
  learning knowledge from unsupervised sensorimotor interaction. AAMAS.
- Hafner, D. et al. (2019). Learning latent dynamics for planning from pixels.
  ICML.

## One-Sentence Benchmark Charter

Evaluate not only whether an agent succeeds, but whether the
future-controlling variable is represented, attributed, queried, and committed
at the causal surface where the action is actually chosen.

