# Neurophenom Project Approach Menu
Created: 2026-07-07

## Source Scope

This scopes the project ideas from the pasted Neurophenom notes and the local
Neurophenom material in `coherence-testbench/`. I did not find a literal
`neurophenom/` directory in this checkout; the relevant repo-local trail is:

- `coherence-testbench/README.md`
- `coherence-testbench/NEXT_STEPS.md`
- `coherence-testbench/POST_MORTEM.md`
- `coherence-testbench/QUIZ_VERIFICATION.md`
- `coherence-testbench/MODALITY_COMPARISON.md`
- `coherence-testbench/docs/foundation_model_options.md`

Interpretation guardrail: generated idea lists are scaffolds. The strongest
local evidence is diagnostic: EEG phase-0 is a cross-subject KILL; eyetrack has
real but heterogeneous signal; the corrected quiz run is INCONCLUSIVE; the
confound-controlled residual eyetrack result peaks around Spearman rho +0.207
at n_train=24. Anything about consumer learning, human cognition, steering, or
neural validation needs its own gate.

## Strategic Spine

The best unifying frame is not "decode the brain." It is:

Exposure -> state estimate -> intervention -> verification.

Use BBBD and `coherence-testbench/` to validate which traces survive controls.
Use product prototypes to test whether weak state estimates still create value
when they choose useful repairs. Use interpretability and steering only where
they improve the intervention or verification loop.

## Research And Benchmark Projects

| Project | Approach 1 | Approach 2 | Approach 3 | First gate |
|---|---|---|---|---|
| EEG-over-gaze residual test | Run nested FWL: demographics/stimulus -> gaze -> EEG residual contribution. | Treat EEG as a complement only in event windows, not session aggregates. | Report null as a positive result: gaze carries the usable trace, EEG does not generalize. | Delta rho over gaze-only with train-only residualization. |
| Braindecode fleet benchmark | Fixed-split, fixed-label Modal fan-out over EEGNet, Deep4, ShallowFBCSP, ATCNet, EEGConformer, EEGITNet. | Add one "modern encoder" lane only if it runs without custom dependency work. | Publish as architecture-agnostic EEG KILL if all fail under same gates. | No heroic tuning; same residual gates and LSO splits. |
| VLM/stimulus-only baseline | Build dumb stimulus features: transcript length, speech rate, duration, topic, video ID. | Add VLM/LLM ratings for difficulty, novelty, clarity, affect, expected retention. | Use TRIBE-style stimulus modeling only as an offline research baseline, not product path. | Physiology must beat stimulus-only residuals. |
| Event-centered windows | Align around saccades, fixation onsets, blinks, pupil peaks, video cuts. | Align around semantic events: definition, example, transition, quiz-relevant segment. | Try sequence objectives inspired by Brain2Qwerty, but do not copy its typed-sentence framing. | Event windows beat session aggregates on held-out subjects. |
| Foundation-model EEG triage | Same-day ingestion test for LaBraM, EEGPT, CBraMod, BENDR-like encoders. | Use braindecode as the unified launcher where possible. | Stop immediately if license or tensor-shape friction exceeds the triage budget. | Encoder emits embeddings and clears one clean split. |
| Custom SSL EEG encoder | Pretrain a small masked-spectrogram model on `bbbd-cache`. | Compare frozen embeddings vs fine-tuned head. | Use as evidence that scale, not architecture, is the missing EEG ingredient if it fails. | Beats hand-crafted EEG baseline under same residual gate. |
| Cross-corpus eyetrack replication | Pick one external cognitive-outcome eyetrack corpus and run exact residual pipeline. | Start with OpenNeuro-style attention/arousal/N-back/SART datasets if license fits. | Make external replication a separate pre-reg, not a post-hoc BBBD rerun. | Oculomotor residual signal transfers outside BBBD. |
| Reliability ceiling and label-noise audit | Estimate quiz split-half and item consistency where available. | Model per-video/question difficulty before physiology. | Reframe rho +0.2 as strong or weak relative to achievable ceiling. | Ceiling estimate makes residual effect interpretable. |
| Negative-control labels | Permute quiz scores within video. | Shift eyetrack features across subjects or assign future participant scores. | Predict labels physiology should not predict, such as unrelated demographics. | Controls fail while true labels stay above null. |
| Temporal ablation | Compare first, middle, last, and question-relevant video windows. | Test high-pupil, post-cut, fixation-only, blink/saccade transition windows. | Convert temporal concentration into a mechanistic story about integration moments. | Signal localizes rather than spreading uniformly. |
| Cross-modal directionality | Test whether pupil shifts precede gaze instability. | Test whether EEG spectral shifts precede pupil/gaze changes. | Add respiration/ECG as slow-state drivers of attention loss. | Lagged modality predicts future modality changes out of sample. |
| Full multimodal benchmark | Combine demographics, stimulus, gaze, EEG, peripheral physiology, fusion, model zoo. | Add negative controls, reliability ceiling, and per-experiment reporting. | Release as a pre-registered benchmark package. | One table with honest GO/KILL/INCONCLUSIVE rows. |
| Closed-loop intervention recall study | Trigger recap/quiz/rewatch from predicted state and measure immediate recall. | Randomize intervention type to learn which repair works for which state. | Test delayed recall so the target is memory, not just quiz compliance. | Triggered repair beats random repair. |
| Minimum observable trace study | Compare stimulus-only, interaction-only, webcam/gaze, EEG, and fusion. | Quantify marginal utility per privacy/cost tier. | Use within-person personalization as a separate product gate from cross-subject science. | Smallest trace that improves repair selection wins. |
| Gaze-as-bridge modality study | Treat gaze/pupil as the practical bridge between stimulus and comprehension. | Compare gaze features against stimulus-only and demographics residuals. | External-replicate before making broad oculomotor claims. | Gaze residual survives stimulus and demographic controls. |

## Product And Tool Projects

| Project | Approach 1 | Approach 2 | Approach 3 | First gate |
|---|---|---|---|---|
| Comprehension GPS | Start stimulus + interaction traces -> confusion/load estimate -> targeted repair -> recall check. | Add optional webcam/gaze only after the no-sensor loop is useful. | Make it a general loop engine, not a one-off video assistant. | Users accept repairs and recall improves. |
| Attention Replay | Browser extension records scroll, pause, rewind, highlight, and tab-switch traces. | Add webcam gaze approximation and blink/head-pose as weak evidence. | Generate a session replay: where attention fragmented and what to revisit. | Replay points to segments users agree they missed. |
| Comprehension Heatmap | Stimulus-only timeline of likely hard/confusing segments. | Personalize with behavior: rewinds, pauses, notes, quiz failures. | Add cohort analytics for course teams. | Heatmap predicts actual rereads or missed questions. |
| Adaptive quiz scheduler | Insert retrieval checks when overload or integration risk is high. | Learn per-user timing: after definition, before transition, after example. | Use quiz outcomes as verifier for the state model. | State-triggered checks beat fixed-interval checks. |
| Confusion-to-quiz compiler | Generate checkpoint questions at conceptual transitions. | Tune question type to likely confusion: definition, mechanism, transfer, contrast. | Use wrong-answer patterns to select the next repair. | Generated checks expose real misunderstandings. |
| Creator cognitive-load editor | Upload video/docs and flag density, missing recaps, unclear transitions. | Suggest edits: example earlier, recap inserted, term count reduced. | Add optional audience-panel traces later. | Creators accept edits and comprehension metrics improve. |
| Meeting comprehension monitor | Aggregate-only meeting timeline: attention drop, confusion spike, clarify moment. | Make it post-hoc for recordings first to avoid surveillance dynamics. | Offer team-level coaching, never individual scoring by default. | Participants rate summaries as accurate and non-creepy. |
| Personal focus fingerprint | Learn personal modes: deep focus, overload, boredom, near-breakthrough. | Use app switching, typing cadence, scroll patterns, session labels. | Add environment adaptation: break, music, block apps, change reading mode. | State predictions help the user choose the next action. |
| Neurophenom journal | User labels subjective states: flow, confused-good, confused-bad, anxious, locked in. | Correlate labels with behavior traces and optional webcam/gaze. | Build a personal state map tied to inquiry and recall outcomes. | User recognizes signatures and uses them again. |
| Adaptive research reader | Track paper/video reading behavior and produce reread queues, concept gaps, questions. | Add concept-map dependency tracing across papers. | Add optional gaze/webcam only for personalization. | It saves time on the user's next dense paper. |
| Adaptive reading mode | Dynamically insert summaries, diagrams, definitions, checkpoint questions. | Switch explanation mode when user gets stuck: analogy, mechanism, example-first. | Use recall outcome to learn which mode worked. | Adaptive mode beats static reader on recall or completion. |
| Research Session Replay | Reconstruct inquiry trajectory after a session. | Identify abandoned branches, unresolved tensions, next experiment/paragraph. | Tie sessions to a long-term concern graph. | User can resume the next day faster. |
| Epistemic black box recorder | Capture browser trails, notes, prompts, copied snippets, pauses, rewrites. | Summarize what the user was trying to understand. | Distinguish productive stuckness from avoidant orbiting. | Recorder produces a useful next-action memo. |
| Paper triage with cognitive cost | Rank papers by relevance, difficulty, prerequisite burden, and likely payoff. | Add "skim/deep/read-later" recommendations. | Personalize using prior reading and forgotten concepts. | Rankings match what the user later found worth reading. |
| Explanation compiler | Rewrite content for target reader models: novice, expert, skeptical reviewer, tired reader. | Generate multiple intervention styles: analogy, diagram, Socratic, example-first. | Add verifier that predicts whether the target reader state improved. | Rewrites score better with target readers or reader models. |
| Memory-aware research notebook | Track concepts likely to be forgotten from reading and writing traces. | Schedule resurfacing tied to actual projects, not generic flashcards. | Link old concepts to new results and drafts. | Resurfaced concepts improve future synthesis or recall. |
| Misunderstanding detector for drafts | CLI/slash command annotates paragraphs where readers lose the thread. | Generate three rewrites by reader model: skeptic, skimmer, adjacent-field expert. | Add activation/persona-steered local model later for research novelty. | Day-1 dogfood finds real weak paragraphs. |
| Adaptive lecture player | Insert pauses, mini-recaps, diagrams, prerequisites, replay prompts. | Personalize using interaction traces and quiz outcomes. | Add live overlay only after post-hoc suggestions work. | Learners retain more than with static playback. |
| Inquiry health dashboard | Track whether a session is deepening a question or merely orbiting it. | Detect reading without integration and generation without testing. | Map "concern" as the organizing thread across sessions. | Dashboard changes what the user does next. |
| Cognitive Load CI | Run on docs/course PRs and fail when sections overload novices. | Provide repair suggestions: add example, recap, definition, quiz. | Integrate as CI for documentation and onboarding teams. | Human reviewers agree with flagged comprehension failures. |
| Cognitive-load A/B testing for ads | Predict clarity, overload, trust drop-off, memorability, action readiness. | Compare variants with VLM saliency and stimulus features. | Add small webcam/gaze panel only for validation. | Predictions correlate with intent lift or comprehension. |
| Flow editor for short-form video | Optimize for calm retention, educational clarity, memorability, or high energy. | Flag cuts that boost arousal but harm comprehension. | Add creator-facing edit suggestions and before/after metrics. | Edited version improves chosen retention/comprehension metric. |
| Stimulus-only cognitive-load reviewer | No sensors: analyze PDF/video/transcript for difficulty and recap points. | Use it as the first wedge for Comprehension GPS. | Add behavior traces only after the baseline has product value. | Users find predicted hard segments accurate. |
| Personal comprehension assistant | Use scroll, pause, rewind, highlight, notes, quiz, tab switching. | Personalize within-user before chasing universal models. | Treat webcam/gaze as optional evidence, not the core product. | Personal model beats population baseline. |
| Webcam-only learning-state stack | MacBook camera estimates rPPG, blink rate, gaze, head pose, micro-expression. | Combine with screen interaction to avoid overclaiming from video alone. | Validate against BBBD-style labels or self-report prompts. | Webcam features improve state prediction beyond interaction traces. |
| Keystroke-only working-memory meter | Track inter-keystroke timing, burstiness, deletion, hesitation, context switches. | Build a local coding/writing extension with private telemetry. | Pair with self-labels: overloaded, stuck, fake productive, near-breakthrough. | Meter predicts self-reported load or task failure. |
| Reading-vs-skimming extension | Classify skim vs read from scroll velocity, dwell, selection, gaze approximation. | Trigger targeted summaries only for skimmed sections. | Use quiz/recall checks to calibrate "missed" predictions. | It identifies sections users cannot later explain. |
| Consumer EEG decoder | Keep as lab/research mode, not product dependency. | Use cheap EEG only for within-person personalization experiments. | Treat failure as evidence that gaze/interaction is the product path. | Consumer EEG adds marginal utility over webcam/gaze. |
| TRIBE/VLM brain-response visualization | Use video/audio/text -> predicted response as science-art and stimulus baseline. | Do not put TRIBE v2 on the commercial path due non-commercial license. | Compare predicted stimulus demand against human comprehension failures. | Visualization predicts difficulty better than simple stimulus features. |

## LLM, Interpretability, And Steering Projects

| Project | Approach 1 | Approach 2 | Approach 3 | First gate |
|---|---|---|---|---|
| Persuasion delta bench | Pre/post Likert around arguments with controlled structure. | Add user traits, argument type, and resistance-state labels. | Add EEG/webcam only in lab mode after text-only benchmark works. | Argument structure predicts position delta out of sample. |
| LLM cognitive-state judge | Feed keystroke/interaction traces plus partial output to an LLM judge. | Validate against self-report and task outcomes. | Use it as a cheap baseline that neuro signals must beat. | LLM judge beats simple heuristics. |
| VLM-annotated stimulus features | Score each second for load, novelty, affect, semantic density, expected retention. | Residualize physiology against these features. | Reuse features across BBBD, videos, ads, lectures, and docs. | VLM features explain variance beyond dumb stimulus features. |
| Persona-variance confidence estimator | Run cautious, assertive, adversarial, naive personas and measure answer variance. | Compare against logprob and self-consistency baselines. | Use activation steering in open-weight models to make personas less prompt-fragile. | Variance predicts correctness on hard reasoning. |
| Refusal-circuit atlas | Use open-weight models and SAE/tooling to locate refusal-related features. | Compare benign refusal, policy refusal, and jailbreak variants. | Test whether interventions change output without damaging general capability. | Identified circuit predicts and controls refusal behavior. |
| Activation-signature calibration | Probe activations for confidently wrong vs correct answers. | Compare internal probes to external judge/confidence baselines. | Use as verifier for persona/steering interventions. | Activation signature predicts hallucination or error. |
| Pre-reg to verify harness | Generalize `coherence-testbench` discipline: YAML pre-reg -> run -> nulls -> verdict. | Package residualization, leakage checks, controls, and report generation. | Apply beyond neurophenom to small-lab ML science. | Harness catches a seeded bug and blocks a false GO. |
| Multi-persona empirical judge panel | Generate skeptic, methodologist, reviewer, and adversarial persona critiques. | Require claims to survive a structured refutation panel. | Tie panel to actual data checks where available. | Panel catches real weaknesses before human review. |
| Domain-agnostic closed-loop repair engine | Define common schema: exposure, state, intervention, verifier. | Configure for learning, persuasion, writing, coding, ads, therapy-style affect repair. | Build one intervention library with domain-specific verifiers. | Same engine supports two domains with minimal custom code. |
| Persona/steering intervention library | Define intervention personas: analogist, Socratic questioner, concrete-example generator. | Learn which persona repairs which user/concept state. | Use steering vectors in open-weight models for research version. | Persona choice changes verified repair success. |
| LLM coding stuckness repair | Detect engineer stuck state from code context, prompt history, typing, failed tests. | Choose repair: explanation, example, decomposition, debug hypothesis. | Verify by whether fix lands or tests pass. | Triggered repair reduces time-to-fix. |
| Interpretability closed-loop verifier | For model-facing loops, verify activation movement, not just output difference. | Pair steering with activation-signature calibration. | Use verifier as safety layer for persona interventions. | Internal state shifts toward intended profile and behavior improves. |
| Ads closed-loop repair | Exposure is creative; state is attention/affect/friction; intervention is variant/cut/pacing; verifier is intent lift. | Start with VLM/stimulus-only predictor. | Add behavioral panel validation later. | Predicted repair improves ad or landing-page outcome. |
| Therapy-style affect repair | Treat as experimental and safety-limited: state is affect trajectory, intervention is reframe, verifier is self-report. | Keep it self-help/non-clinical unless clinically supervised. | Use privacy-first local data and strong opt-in boundaries. | Users report short-term affect improvement without harm flags. |

## Paper And Publication Tracks

| Project | Approach 1 | Approach 2 | Approach 3 | First gate |
|---|---|---|---|---|
| Adversarial Residualization paper | Methods/results note from BBBD bug retraction, EEG KILL, eyetrack residual. | Emphasize protocol over huge performance claims. | Include negative controls and pre-reg transparency as the contribution. | Claims match corrected `QUIZ_VERIFICATION.md`. |
| From Brain Decoding to Learning-State Instrumentation | Conceptual paper arguing for loop instrumentation over mind-reading. | Tie product thesis to exposure/state/intervention/verification. | Use BBBD as cautionary case, not proof of consumer readiness. | Argument does not depend on unvalidated product claims. |
| Gaze Survives Where EEG Fails | Short empirical paper if gaze residual survives stimulus and demographics. | Include EEG KILL, gaze residual, and fusion test. | Keep title conditional until corrected and residual gates are clean. | Gaze beats EEG under matched LSO controls. |
| Gaze vs EEG vs Fusion in BBBD | One-week empirical table across demographics, stimulus, gaze, EEG, physiology, all modalities. | Report raw and residual targets separately. | Publish nulls and heterogeneity by experiment. | Incremental table is stable across seeds. |
| Stimulus-only baselines paper | Show video/content alone predicts learning outcomes. | Make stimulus difficulty a required baseline for neuro-learning claims. | Use VLM features as the modern "smart baseline." | Stimulus-only baseline is strong enough to change interpretation. |
| Braindecode model-zoo paper | Run broad supervised EEG model zoo under same residual gates. | If all fail, publish "No free lunch in educational EEG." | If one works, publish first robust supervised BBBD baseline. | Fleet result is reproducible and pre-registered. |
| Event-locked comprehension paper | Shift from final quiz score to event-centered prediction. | Use gaze and semantic transitions as anchors. | Connect to Brain2Qwerty only as a sequence-window inspiration. | Events outperform session aggregates. |
| Learning-State Instrumentation benchmark plus prototype | Combine benchmark and Comprehension GPS prototype. | Show stress-tested signal and the interface it enables. | Include intervention selector and recall verification. | Prototype demonstrates verified repair, not just state display. |
| Product/research bridge paper | HCI-style paper: benchmark -> adaptive reader/video assistant -> user study design. | Include privacy and sensor-minimization analysis. | Position EEG as lab instrument, not consumer dependency. | Product loop works with stimulus/interaction traces first. |

## Recommended Execution Order

1. Stabilize the evidence base: residual gaze vs stimulus/demographics, EEG-over-gaze, reliability ceiling, negative controls.
2. Produce one compact paper: adversarial residualization or gaze-vs-EEG-fusion, depending on the cleanest table.
3. Build the fastest loop prototype: Misunderstanding Detector for Drafts or Stimulus-only Comprehension Risk Detector.
4. Upgrade into Comprehension GPS: add interaction traces, repair selection, and recall verification.
5. Only then add webcam/gaze or interpretability/steering. They should improve verified repair, not decorate the demo.

## Kill Rules

- Do not headline raw quiz prediction when residual or corrected results disagree.
- Do not treat generated-text project ideas as human behavioral evidence.
- Do not put TRIBE v2 or Brain2Qwerty on a commercial product path without license resolution.
- Do not copy Brain2Qwerty framing for BBBD; use it as sequence-window inspiration only.
- Do not make EEG the consumer product dependency unless it beats cheaper traces.
- Do not ship individual-level meeting surveillance as the lead use case.
- Do not call a state estimate useful until it changes an intervention or verification outcome.
