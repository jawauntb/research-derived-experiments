# Metaphysics of Intelligence Reading Log

Generated: 2026-07-06

Source folder: `/Users/jawaun/Metaphysics of Intelligence`

Scope: top-level PDF files whose names begin with a number, read in numeric/version order from `0_geometric_meaning_and_agency.pdf` through `31_Future_Control_Moves_Memory_2026_07_06.pdf`. This pass includes lettered and versioned variants because the request was to read every paper starting at `0_` and move upward.

Extraction method: PDF text was extracted with `pypdf` into `/tmp/metaphysics_paper_extracts`, then checked through abstracts, result claims, conclusion/tail sections, and targeted finding sentences. The notes below are a running synthesis, not a verbatim extraction dump.

## Running Synthesis

The sequence starts from a philosophical spine: geometry is structured difference, meaning is geometry under concern, intelligence navigates that geometry, and agency is geometry coupled to action, self-maintenance, repair, boundary preservation, and time.

The first empirical arc makes "weakness" the initial operational handle. When training data admits both shortcuts and symmetry-compatible rules, weakness predicts out-of-distribution generalization where loss, validation, compression, flatness, and simplicity-style proxies fail. The strongest version is not just oracle symmetry: finite groups can often be inferred from data, and learned-function weakness remains predictive.

The second arc turns passive geometry into active geometry. A latent structure is not enough just because it clusters. It becomes causally load-bearing only when coupled to action or viability. This is the transition from paraphrase clusters and group discovery into homeostatic agents whose representations organize around valence, delta_E prediction, planning, and survival.

The third arc repeatedly separates representation, competence, exploration, and calibration. Concern-shaped geometry can exist without an exploitable policy; a policy can succeed using a proxy representation; a model can be behaviorally correct while internally misattributing causes. The program's strength is that it keeps finding these separations instead of smoothing them away.

The fourth arc moves into self/world attribution. Architectural factorization alone is gauge-symmetric: the model can split "self" and "world" arbitrarily while preserving total prediction and action accuracy. Null actions become the key gauge-breaking intervention. Later papers turn this into autonomous probing, probe-value estimation, habituated re-engagement, learned probe abstractions, and finally an architectural ceiling.

The latest papers broaden the mechanism. Value-weighted training can move learned metric density across spatial models; the measured allocation exponent suggests an effective dimension near one rather than the physical 2-D arena; translation augmentation can produce toroidal codes and OOD generalization while failing the proposed weakness-topology mediation triangle; future-control demands can move memory geometry toward the delayed bottleneck variable.

The recurring lesson: "concern" is not a label on a representation. It is a stack of measurable constraints: invariant structure, causal load-bearing, viability prediction, action selection, coverage, calibration, interventional identifiability, saturation, re-engagement, and architecture-specific representational capacity.

## Paper-by-Paper Findings

### 01. `0_geometric_meaning_and_agency.pdf` - 28 pp

Finding: The conceptual base says geometry appears when differences are organized into relations such as nearness, direction, boundary, continuity, invariance, and possible movement. Meaning is geometry under concern; intelligence is navigation of that geometry; agency is geometry that acts to preserve and expand its own navigability.

Running note: This paper supplies the vocabulary for the whole folder. Later papers keep cashing out "concern" as valence, viability, self-maintenance, boundary preservation, and repair rather than as an introspective or merely semantic property.

### 02. `1_Weakness_Predicts_OOD_2026_06_09.pdf` - 12 pp

Finding: Weakness, defined as the size of the transformation set under which a hypothesis remains equivariant, predicts OOD generalization when local shortcuts and globally invariant rules both fit the training set. On cyclic and dihedral symbolic families, weakness selects the invariant rule with Wilson lower bound 0.992 while the tested classical baselines select the shortcut. In MLP sweeps, learned-function weakness is the strongest OOD correlate, around Pearson r = +0.82.

Running note: The paper also reports boundaries: parity and large symmetric-group cases are honest negative or degraded regimes. The language-model result is only partial: paraphrase geometry appears in hidden states, but next-token behavioral coupling is not yet demonstrated at the tested scale.

### 03. `2_Learning_the_Group_2026_06_09.pdf` - 10 pp

Finding: The symmetry group does not always need to be given by oracle. A data-inferred rotation-group procedure recovers the true Z_8 group from partial-orbit training data with mean recall 89.7% and precision 71.3%. Weakness scored against the inferred group retains about 90% of the oracle signal for OOD prediction, and learned augmentation recovers most of the oracle augmentation lift.

Running note: This makes weakness less brittle as a framework, but the language transfer is weak. The candidate similarity/calibration problem becomes an early version of a recurring theme: the right metric and selection rule matter as much as the formal idea.

### 04. `3_When_Pixels_Beat_Embeddings_2026_06_09.pdf` - 8 pp

Finding: Three neural approaches to transformation discovery underperform the simple pixel-cosine enumerative baseline on synthetic strokes under threshold-based selection. On rotated MNIST, top-K selection changes the story: encoder methods can outperform pixel cosine, while threshold selection makes methods look artificially tied.

Running note: This is a useful methodological warning. The result is not "neural methods fail" in general; it is that discovery quality depends heavily on operating regime, candidate density, and selection rule.

### 05. `4_From_Passive_to_Active_Geometry_v2_2026_06_10.pdf` - 9 pp

Finding: A paraphrase latent axis that is mostly passive before fine-tuning becomes causally load-bearing after action coupling through supervised fine-tuning. Ablating the paraphrase axis destroys active classifier accuracy much more than passive readout accuracy, and the paraphrase-specific intervention effect grows about 7x.

Running note: This is the first clean bridge from "geometry predicts" to "geometry does work." It answers the worry that hidden-state clusters may be epiphenomenal.

### 06. `5_From_Active_to_Autopoietic_Control_2026_06_10.pdf` - 9 pp

Finding: Active geometry is tested against autopoietic-style criteria: viability buffer, repair after perturbation, and the Law of the Stack. Fine-tuned systems recover from classifier-head noise through test-time updates, showing a small repair/ultrastability behavior. Lower-layer slack constrains upper-layer adaptive capacity.

Running note: This extends the action-coupling result beyond "the trained head uses the feature" toward self-maintaining capability. The important constraint is that representation quality sets a ceiling for later adaptation.

### 07. `6_Objects_Form_from_Concern_2026_06_10.pdf` - 8 pp

Finding: Valence-coupled encoders cluster objects by causal-valence role rather than sensory similarity. The sensory encoder clusters by color; the valence encoder clusters by reward/role while preserving high task performance.

Running note: This is the first concrete "objects from concern" result. It operationalizes the philosophical claim that what counts as an object depends on what matters for action and viability.

### 08. `7_When_Active_Geometry_Transfers_2026_06_10.pdf` - 9 pp

Finding: Valence-pretrained encoders transfer into episodic homeostatic RL where sparse-reward RL from non-valence starts fails on XOR. However, one additive reward condition shows survival can be achieved through a representation that does not itself encode reward structure.

Running note: The paper complicates the story in a good way: competence and representational organization can decouple. Survival is not always evidence that the intended internal geometry is present.

### 09. `8_Bootstrapping_Concern_2026_06_10.pdf` - 10 pp

Finding: An action-conditioned delta_E auxiliary loss can build valence geometry without supervised optimal-action labels in easier structures, but sparse-reward policy gradients still fail to exploit it in harder XOR-like regimes.

Running note: This identifies representation and competence as separate bottlenecks. A system can learn what matters without yet knowing how to use that knowledge for action.

### 10. `9_Two_Bottlenecks_2026_06_10.pdf` - 10 pp

Finding: Decoupling representation learning from policy learning confirms the two-bottleneck diagnosis. A delta_E auxiliary encoder can develop strong reward geometry; a supervised policy head can exploit it for near-perfect return, while REINFORCE remains much weaker.

Running note: Policy-gradient noise is not just inefficient. In this setup it can disrupt or fail to exploit the concern-shaped representation. This sets up model-based planning as the next move.

### 11. `10_Planning_from_Concern_2026_06_10.pdf` - 12 pp

Finding: Greedy model-based planning over the learned delta_E head solves the policy bottleneck. The model_plan_delta_E condition reaches 50/50 return and about 0.996 action accuracy on XOR without supervised optimal-action labels and without policy-gradient training.

Running note: This is a major positive result: once the model has learned "what action changes viability how," direct planning can convert concern-shaped representation into competence.

### 12. `10_Planning_from_Concern_v2_2026_07_06.pdf` - 11 pp

Finding: The July 6 version preserves the Paper 10 result: delta_E-organized encoders plus greedy delta_E planning produce self-organized homeostatic competence without optimal-action supervision.

Running note: Treat this as the updated presentation of the same core finding, useful for citations or a cleaned synthesis pass.

### 13. `10b_Distributed_Concern_2026_06_10.pdf` - 13 pp

Finding: The Paper 10 planning result is robust, but the simple "single reward axis drives action" interpretation fails. Ablating the reward axis and ablating a random direction cause similar action-accuracy drops, implying that competence depends on distributed geometry, calibration, action coverage, and readout/head capacity rather than one privileged latent axis.

Running note: This is one of the most important anti-overinterpretation papers. It keeps concern from becoming a single-vector story.

### 14. `11_Learning_to_Ask_What_Matters_2026_06_10.pdf` - 9 pp

Finding: A biased initial policy can collapse the Paper 10 pipeline despite strong reward geometry. Conservative exploration mechanisms, especially epsilon decay and margin-based epistemic sampling, can recover XOR competence; novelty-seeking/prediction-error curiosity and ensemble disagreement fail in this setup.

Running note: The third requirement after representation and readout is action coverage. The agent has to ask the right counterfactual questions often enough to learn.

### 15. `11b_Exploration_Diagnostics_2026_06_10.pdf` - 8 pp

Finding: Diagnostics show that working methods have near-perfect margin sign accuracy, while failing methods remain near chance. Margin-based epistemic sampling partly recovers from confidently wrong initialization, but all mechanisms fail under high noise.

Running note: The result narrows the exploration issue to calibrated branch/margin knowledge. Exploration is not magic novelty; it is targeted uncertainty about action consequences.

### 16. `12_State_Dependent_Concern_Fails_2026_06_10.pdf` - 8 pp

Finding: State-dependent concern fails under online homeostatic training. When the same item changes role depending on internal energy, all tested online conditions stay near chance even though the same architecture succeeds on static XOR.

Running note: This is a sharp negative result. "Meaning is geometry under concern" requires state-conditional concern, but online policy-induced data distributions can prevent the model from learning the regime split.

### 17. `13a_Off_Policy_State_Coverage_2026_06_11.pdf` - 9 pp

Finding: Off-policy state-aware delta_E training partially recovers state-dependent concern, reaching about 0.96 action accuracy away from the singular boundary. But it refutes the simple coverage diagnosis: the remaining failure is a boundary-smoothing problem around E = 0.5.

Running note: More data coverage helps, but the model class still smooths over a discontinuity. The bottleneck shifts from coverage to regime representation.

### 18. `13b_Regime_Sensitive_DE_Models_2026_06_11.pdf` - 8 pp

Finding: Adding an oracle boundary feature, 1[E < 0.5], solves the state-dependent concern task at the diagnostic limit: 50/50 return, state-conditional competence 1.00, and margin sign accuracy 1.00 across the energy grid. Learned alternatives help away from the singular point but do not fully close the boundary gap.

Running note: The system needs the right regime variable. Smooth approximators can look almost solved while failing exactly where the trajectory distribution concentrates.

### 19. `14_Allostatic_State_Control_2026_06_11.pdf` - 10 pp

Finding: Adding a regulate action improves boundary-condition return from the Paper 13b failure, but the hypothesized uncertainty-aware planners underperform. Greedy planning with a safe regulation fallback beats two-step and uncertainty-bonus variants.

Running note: This is an honest falsification of the prettier allostatic story. The useful mechanism is simpler: regulate away from the dangerous boundary, but do not trust the model's own confidence bonus when it is confidently wrong.

### 20. `14b_Ensemble_Uncertainty_2026_06_11.pdf` - 8 pp

Finding: Bootstrap ensembles fail to detect the regime-boundary failure. The models do not know what they do not know; they are wrong together. Risk-averse or optimistic ensemble planners therefore do not rescue allostatic control.

Running note: This generalizes the earlier warning about uncertainty. Variance is not error when the whole model family shares the blind spot.

### 21. `15_Tapestry_of_Valence_2026_06_11.pdf` - 10 pp

Finding: Vector delta_V heads support flexible multi-dimensional concern under shifted internal-priority weights. Scalar drive heads cannot correctly reweight medicine handling across hungry, injured, and balanced contexts, while vector heads track the oracle much more closely.

Running note: This is the move from scalar homeostasis to Bennett-style "tapestry of valence." Mattering is not one variable; it is a vector of internal consequences under changing priorities.

### 22. `16_First_Order_Self_2026_06_11.pdf` - 8 pp

Finding: Architectural self/world factorization alone does not recover the true self component. The self and world heads are gauge-symmetric: they can split total predicted delta_E arbitrarily while preserving action accuracy and return. Only oracle source labels recover the true decomposition.

Running note: This is a central warning for interpretability. Behavioral correctness can coexist with representational false credit.

### 23. `16_First_Order_Self_v2_2026_07_06.pdf` - 9 pp

Finding: The July 6 version restates the same gauge-symmetry result and makes the required next ingredient clearer: a reafferent self/world split needs a gauge-breaking signal such as source labels, active null intervention, temporal asymmetry, or another loss that pins the exogenous component.

Running note: Treat this as the updated framing of Paper 16. It points directly to Paper 16b.

### 24. `16b_Identifiability_Through_Intervention_2026_06_11.pdf` - 10 pp

Finding: Null actions break the self/world gauge symmetry when used as active world anchors. The null action is dynamically like skip but labeled as a direct measurement of world-caused change; supervised use of null observations reduces false credit dramatically. Passive null exposure without anchoring is not enough.

Running note: The agent learns the boundary by deliberately not acting. This is the first real self/world identifiability mechanism in the sequence.

### 25. `17A_Learning_When_Not_To_Act_2026_06_11.pdf` - 10 pp

Finding: Scheduled null anchors replicate strongly, reducing food self-overshoot by about 85%, but autonomous costly-null selection fails most pre-registered gates. The learned V_probe captures coarse scale but not fine rank within uncertainty clusters.

Running note: Intervention works; deciding when intervention is worth the cost is harder. This opens the probe-value arc.

### 26. `18_Online_Identifying_Interventions_2026_06_11.pdf` - 10 pp

Finding: The anchor mechanism replicates again, with a reported 159% reduction in food self overshoot versus no-null baseline. The factorial design shows that online data regime matters, but the new bottleneck is calibration between the learned probe target and current systematic attribution error.

Running note: The program starts separating three issues: intervention signal, data regime, and target calibration. That decomposition is more useful than a single "probe learning failed" label.

### 27. `19_Current_Error_Calibration_2026_06_12.pdf` - 9 pp

Finding: Current-replay calibration fixes the staleness problem by recomputing residuals against the present model. Food self MAE falls to about 0.017, close to oracle source, and learned probing finally beats matched-random by 61.5% MAE.

Running note: Historical residuals are not enough. Epistemic value must be computed against the model as it is now, not the model as it was when the data arrived.

### 28. `20B_Vector_First_Order_Self_2026_06_12.pdf` - 10 pp

Finding: Vector valence, null anchoring, and current-replay probing compose into a multi-valence first-order self. Per-dimension attribution can be near-oracle and medicine action accuracy stays close to oracle across priority contexts. However, learned probing is worse than matched-random at matched null count because smaller-magnitude dimensions are miscalibrated.

Running note: The mechanism composes, but scale asymmetry appears as the next bottleneck.

### 29. `21A_Scale_Normalized_VProbe_2026_06_12.pdf` - 10 pp

Finding: Scale-normalized V_probe targets and per-dimension thresholds fix the catastrophic scale asymmetry from Paper 20B, reducing total MAE by about 64% in the highlighted comparison. At near-oracle convergence the probe often stops firing, making some selection/calibration metrics vacuous.

Running note: This is a partial positive. The attribution mechanism is repaired, but the evaluation setup needs metrics that remain meaningful when a competent agent no longer probes.

### 30. `22_World_Responds_2026_06_12.pdf` - 10 pp

Finding: Action-correlated world shocks require a three-head decomposition: direct self, mediated world, and exogenous world. This improves final MAE relative to action-blind two-head models, but learned probing beats time-matched random by only 16%, below the 25% threshold. Current attribution error is not the same as marginal value of another probe.

Running note: The world can respond to the agent. Once it does, "world" is no longer just independent noise, and probe policy has to estimate value of information rather than raw error.

### 31. `22_World_Responds_Reengagement_Floor_2026_07_06.pdf` - 9 pp

Finding: The updated July 6 presentation preserves the Paper 22 findings and foregrounds the re-engagement problem: learned probing trends positive but remains below gate, and current-error oracles can misallocate probes catastrophically.

Running note: This version frames the next step clearly: the probe must know when to ask again after the world changes.

### 32. `23A_Probe_Value_Reengagement_2026_06_12.pdf` - 9 pp

Finding: A principled probe-value oracle improves over a current-error oracle, and a two-timescale prediction-error boost re-engages probes after a regime shift. The headline learned mechanism fires strongly after change, but it does not recover to MAE <= 0.10 and produces an "anxiety" failure mode: too much continued probing.

Running note: Re-engagement is solved before saturation is solved. The agent learns to ask again, but not when to calm down.

### 33. `23B_Habituated_Reengagement_2026_06_12.pdf` - 11 pp

Finding: Decision-layer cooling stabilizes autonomous probing after re-engagement. Leaky effort integration, decision refractory periods, and burst-then-refractory variants cut post-shift AUC roughly 45-50% versus the anxious Paper 23A baseline. Signal-layer cooling creates false calm by suppressing the surprise signal itself.

Running note: This is a very clean design distinction: reduce action tendency, not perception. Habituation should damp response while preserving detection.

### 34. `24_Interventional_Contrast_2026_06_12.pdf` - 10 pp

Finding: Interventional contrast supervision reduces the mediated/exogenous identifiability gap that remained after Paper 23B. Shuffled contrast pairs do not help, which supports the semantic specificity of the mechanism; wrong-history controls reveal remaining environmental underconstraint.

Running note: Pairwise interventional contrast is the next gauge-breaking tool after null anchoring. It helps, but it also exposes when the environment makes the intended split underdetermined.

### 35. `25_Role_Specific_Identifiability_2026_06_12.pdf` - 9 pp

Finding: Role-specific mediated effects, two-sided gauge anchoring, and learned buckets reveal an architectural ceiling. The shared mediated head cannot represent per-role mediated coefficients of different magnitudes within the tested setup, regardless of probe-policy improvements.

Running note: This is the natural endpoint of the autonomous-probing arc. Further progress requires a representational change, such as disjoint per-role heads or richer intervention types, not just better probe scheduling.

### 36. `26_Metric_Stack_of_Concern_2026_06_12.pdf` - 14 pp

Finding: The first Metric Stack synthesis reports a 25-paper arc in which a minimal homeostatic agent accumulates concern-like representation, vector valence, null-anchored intervention, calibrated probe selection, habituation, learned abstractions, and then hits the shared-head architectural ceiling.

Running note: This paper turns the sequence into a diagnostic stack. Its main value is vocabulary: geometry, causal load-bearing, repair, valence, competence, planning, coverage, calibration, identifiability, maintained boundary, learned abstraction, ceiling.

### 37. `26_Metric_Stack_of_Concern_v2_2026_06_12.pdf` - 26 pp

Finding: Version 2 expands the synthesis, clarifies that the work studies minimal computational precursors of concern-like agency rather than consciousness, and presents the positive mechanism as a detect-allocate-saturate-re-engage cycle with learned probe abstractions.

Running note: This version is the more complete methodological record and reproducibility-oriented synthesis.

### 38. `26_Metric_Stack_of_Concern_v3_2026_06_12.pdf` - 29 pp

Finding: Version 3 sharpens the measurement question: how can we tell whether behavior depends on the intended internal structure rather than a proxy? It frames the role-specific mediated-identifiability gap as an architectural limit of the shared-head/null-intervention setup.

Running note: This version is useful when arguing that the program is not only about agent behavior but about diagnosing internal causal structure.

### 39. `26_Metric_Stack_of_Concern_v4_2026_07_06.pdf` - 27 pp

Finding: Version 4 is the latest top-level synthesis in this folder. It preserves the positive mechanism and ceiling: a working detect-allocate-saturate-re-engage cycle, three-head world decomposition, learned probe abstractions, and a precise limit at role-specific mediated identifiability.

Running note: This is the likely canonical current Metric Stack paper for the July 6 folder state.

### 40. `27_Concern_Deforms_a_Learned_Metric_2026_07_02_draft.pdf` - 12 pp

Finding: Value-weighted training deforms learned representational metrics across RNN, Transformer, and JEPA-style spatial models. Moving the priority field moves local metric density with positive lift and specificity across all three architectures. A pretrained text-encoder boundary check fails, so the claim is bounded to controlled spatial models.

Running note: This is the spatial metric version of "valuable regions receive resolution." It extends concern from object/action attribution into geometry of representational capacity.

### 41. `28_Effective_Dimension_Law_2026_07_02_draft.pdf` - 6 pp

Finding: A preregistered rate-distortion test rejects the physical 2-D allocation prediction alpha = 1/2 for the path-integration RNN harness. Measured exponents are around alpha = 0.30 for anisotropic, stripe, and point value fields, implying an effective allocation dimension near one.

Running note: This is a productive negative: metric density moves with value, but the allocation law reveals the architecture's effective bottleneck rather than the arena's physical dimension.

### 42. `28_Effective_Dimension_Law_2026_07_02_neurips_arxiv_ready.pdf` - 6 pp

Finding: The arXiv-ready version preserves the same effective-dimension result: finite-capacity path-integration RNNs allocate value-weighted resolution with an exponent near 0.30, not the expected 0.50 for a genuinely 2-D code.

Running note: Treat this as the polished/citable version of Paper 28.

### 43. `29_Weakness_Predicts_Topology_2026_07_02_draft.pdf` - 7 pp

Finding: Translation augmentation reliably produces toroidal codes and improves larger-arena generalization, but the proposed weakness-topology-OOD mediation triangle fails. Weakness only weakly predicts toroidal score, does not beat final loss by the preregistered margin for OOD prediction, and topology does not mediate the weakness-OOD relation.

Running note: This is an important bounded negative. Structured training can causally produce toroidal, generalizing codes, but weakness is not the whole topology story in this harness.

### 44. `30_Weakness_Predicts_OOD_2026_07_02_draft.pdf` - 6 pp

Finding: This compact draft strengthens the weakness/OOD result with larger MLP sweeps. On cyclic and dihedral symbolic families, weakness recovers the invariant rule in 100% of trials while loss, validation, description length, MDL-style, compression, and flatness proxies recover it 0%. Across 256, 1024, and 4096 trained MLPs, weakness remains the strongest OOD correlate, with r about +0.81 and positive residual signal after augmentation fixed effects.

Running note: This is the tighter modern form of Paper 1. It also keeps the boundary cases: parity is cleanly negative and large symmetric groups degrade data-inferred discovery.

### 45. `31_Future_Control_Moves_Memory_2026_07_06.pdf` - 8 pp

Finding: The long-horizon moved-bottleneck diagnostic asks whether future-critical variables reshape memory geometry. The registered metric is final hidden-state sensitivity under single-slot bit flips, and the positive result is that the sensitivity peak follows the moved critical slot while remaining absent in a visible-control condition across an increasingly agent-like synthetic ladder.

Running note: This extends the program from concern-shaped representation and self/world boundary into temporally delayed control: memory geometry moves toward what later action will need.

## Cross-Paper Open Questions

1. Language/model scale: Hidden paraphrase geometry appears in small language models, but behavioral coupling remains weak. Larger models, sharper log-probability metrics, and broader paraphrase sets are still needed.

2. Non-enumerative symmetry discovery: Enumerative group discovery works in finite vision regimes, but neural transformation generators and threshold selection remain brittle.

3. Regime variables: State-dependent concern needs explicit or learned regime features. Smooth approximators can fail exactly at singular boundaries.

4. Uncertainty calibration: Ensembles and confidence proxies often miss systematic model-family errors. Probe value must estimate marginal information gain, not current error or variance alone.

5. Architecture beyond the ceiling: The role-specific mediated-identifiability ceiling likely requires disjoint per-role representations, mixture-of-experts routing, richer counterfactual interventions, or environments with stronger identifying variation.

6. Foundation-model generality: Spatial concern deformation is robust in controlled finite-capacity models, but the text-encoder boundary check fails. Extending the metric-deformation story to foundation models remains open.

7. Topology mediation: Translation augmentation can produce toroidal OOD-generalizing codes, but weakness does not mediate topology in the tested path-integration harness. A richer topology metric or different causal graph may be needed.

