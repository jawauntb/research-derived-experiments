# From Controlled Concern Geometry to Foundation Models

Jawaun Brown

Research-Derived Experiments - Phase 5 external-validity transport suite

## Abstract

Phase 4 showed that several missing conditions in the Metric Stack of Concern
can be learned inside controlled diagnostic harnesses. Phase 5 asks which of
those mechanisms transport when the setup becomes more model-like, semantic,
and counterfactual. The suite runs four cheap L4-parallel transport gates:
language action coupling, foundation-style semantic metric deformation,
role-routed world modeling, and topology/seam causal disentanglement. The
allowed claim remains bounded: this is an external-validity proxy result that
decides where expensive real-model validation should go next.

## 1. Claim Boundary

This paper does not claim biological validity or foundation-model generality.
It tests whether the Phase 4 mechanisms survive harder proxies that more
closely resemble the next empirical tier. A mechanism is promoted only when it
clears a transport gate and its matched controls fail.

## 2. Transport Tracks

| Track | Transport question | Primary controls |
| --- | --- | --- |
| `language_action_transport` | Does hidden paraphrase geometry become an action-like controller under stronger open-model proxy conditions? | tiny LM, shuffled axis, matched prompt intervention |
| `foundation_semantic_metric` | Does value-weighted metric deformation survive frozen foundation-style semantic encoders? | frozen encoder, random value adapter, collapse index |
| `role_routed_world_model` | Do role-routed heads break the mediated-identifiability ceiling in a richer counterfactual world? | shared head, swapped-role counterfactual, shortcut head |
| `topology_seam_causality` | Is seam consistency, topology, or their interaction the causal carrier of OOD generalization? | both-broken, topology-only, seam-only, randomized phase |

## 3. Gate Results

The full L4 run used 256 L4 cells and produced 1216 rows. The conservative
timeout-bound cost estimate was $51.15 against the $1000 cap.

| Track | Status | Primary result | Interpretation |
| --- | --- | --- | --- |
| `language_action_transport` | PASS | geometry-action r = 0.858, heldout r = 0.837, intervention ratio = 4.472 | The Phase 4 language failure is rescued in the stronger open-model proxy while tiny/shuffled controls stay weak. |
| `foundation_semantic_metric` | PASS | moved lift = 0.228, specificity = 0.166, cross-encoder transfer = 1.425 | Value-weighted semantic metric deformation survives a frozen foundation-style encoder proxy. |
| `role_routed_world_model` | PASS | role MAE = 0.036, MoE MAE = 0.040, shared MAE = 0.316 | Role-routed and mixture heads break the mediated-identifiability ceiling in a richer world model. |
| `topology_seam_causality` | PASS | seam-only lift = 0.400, topology-only lift = 0.118, joint interaction = 0.089 | Seam consistency is the causal carrier; topology alone remains insufficient but participates in the joint condition. |

Overall suite status: PASS.

## 4. Main Findings

First, language action coupling becomes live again. Phase 4 found predictive
paraphrase geometry without enough causal-action strength. Phase 5 preserves the
failure as a tiny/shuffled control and shows that a stronger open-model proxy
clears both the held-out geometry and intervention gates.

Second, semantic metric deformation survives the first foundation-style boundary
check. The value-weighted adapter moves density around high-value semantic
neighborhoods, transfers across an image/text-style proxy field, and does not
collapse the embedding space.

Third, architecture remains a real ceiling-breaker. Shared and shortcut heads
underfit the richer role/world/counterfactual environment, while role-routed and
mixture-of-experts heads preserve counterfactual consistency.

Fourth, topology remains conditional on seam consistency. The factorial design
separates topology-only, seam-only, both-fixed, and both-broken conditions:
seam-only gives most of the OOD lift, topology alone is weak, and the both-fixed
condition adds a smaller joint interaction.

## 5. Discovery-Regime Audit

Old regime: Phase 4 learned missing conditions inside controlled harnesses.

Transition: Phase 5 preserves those gates but makes the environment more
external: language behavior gets held-out paraphrase and intervention controls;
semantic deformation is tested against a frozen encoder proxy; architecture is
tested in a richer role/world/counterfactual environment; topology is separated
from seam consistency through a factorial causal graph.

Transported evidence: the Phase 4 bounded negative on language scale remains
the baseline; semantic deformation, role routing, and seam mediation are carried
forward as live hypotheses.

Rejected alternatives remain visible: tiny language-model coupling, shuffled
axis steering, random value adapters, shared mediated heads, swapped-role
counterfactuals, and topology without seam consistency.

## 6. Next Operations

If these transport gates pass, the next expensive tier should run real open LMs
and frozen encoders: Qwen/Gemma/Pythia-style language action coupling, real
sentence/image embedding metric deformation, richer self/world role-routing
agents, and topology/seam interventions in a learned path-integration system.

If any transport gate fails, that failure should become the control for the
next version rather than being tuned away.
