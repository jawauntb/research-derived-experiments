---
name: scientific-discovery-loop
description: general scientific discovery and experiment-design workflow for ai/ml, ai agents, neuroscience, physics, biology, and other research domains. use when asked to generate hypotheses, design or critique experiments, analyze experimental results, explain anomalies, plan research programs, improve research agents, compare theories, or search for einstein-style conceptual advances by exposing hidden assumptions, contradiction clusters, invariances, ontology failures, falsifiable predictions, and severe tests.
---

# Scientific Discovery Loop

## Purpose

Use this skill to turn research work into a disciplined discovery loop: evidence -> hidden assumptions -> contradiction clusters -> conceptual reframes -> risky predictions -> severe experiments -> bounded claims -> next tests.

The goal is not to produce impressive speculation. The goal is to identify the smallest assumption change that makes confusing evidence simpler and then design experiments that could kill that change.

## Load references only when needed

- For the complete step-by-step protocol, read `references/protocol.md`.
- For output structures for discovery memos, experiment plans, and result analyses, read `references/templates.md`.
- For ranking candidate theories, experiments, and anomalies, read `references/scoring-rubrics.md`.

## Operating rules

1. Treat discovery as frame diagnosis, not only hypothesis generation.
2. Separate observations, assumptions, interpretations, mechanisms, measurements, and claims.
3. Prefer invariants, symmetries, limiting cases, and causal interventions over surface correlations.
4. Identify the field's possible "absolute time" assumption: the concept everyone protects because it feels obvious.
5. Convert every conceptual reframe into at least one risky, discriminating prediction.
6. Design experiments that distinguish old frame vs new frame, not experiments that merely support the preferred idea.
7. State kill criteria before interpreting results.
8. Do not overclaim: label claim strength and specify what evidence would change the conclusion.
9. When current or niche literature is needed, gather and cite evidence from available sources before asserting domain facts.
10. For AI/ML and AI-agent research, always check for benchmark leakage, shortcut learning, prompt artifacts, evaluator artifacts, data contamination, distribution-shift fragility, and correlation-vs-causal-use confusion.

## Workflow decision tree

**If the user asks for a new discovery, theory, hypothesis, or research direction:** run the full discovery loop in `references/protocol.md`, then output a discovery memo.

**If the user asks for an experiment:** identify competing frames first, then design the smallest severe test that separates them.

**If the user provides results:** reconstruct what each theory predicted before seeing the results, compare observed vs predicted outcomes, identify artifacts/confounds, update claim strength, and propose the next discriminating test.

**If the user asks to improve a research agent:** convert the protocol into agent instructions, including assumption ledgers, anomaly queues, theory-score tables, experiment-score tables, and result-update loops.

## Minimum output requirements

Every substantive output should include:

- Current frame: the accepted explanation and its core ontology.
- Assumption ledger: load-bearing assumptions, measurement assumptions, and inherited assumptions.
- Anomaly map: observations, edge cases, or null results that strain the frame.
- Candidate reframes: which assumption is removed or replaced, and what becomes simpler.
- Discriminating predictions: what old and new frames predict differently.
- Severe experiment: protocol, controls, measurements, confounds, and kill criteria.
- Claim boundary: what can be concluded now, what remains unknown, and what would change the conclusion.
- Next best test: the highest-information next action.

## Discovery moves to actively search for

- **Magnet-and-conductor asymmetry:** the same observable gets different causal stories under arbitrary reframing.
- **Chasing-the-signal limit:** push a concept to an extreme case where the old ontology breaks.
- **Anomaly compression:** several unrelated-seeming exceptions become expected after changing one assumption.
- **Operationalization cut:** a vague concept becomes a measurement procedure, revealing hidden frame-dependence.
- **Gauge/artifact test:** an explanation depends on coordinates, labels, benchmark format, task wording, measurement device, or observer frame.
- **Causal-use test:** information is present or decodable but may not be used to control the outcome.
- **Transport test:** the claim survives relabeling, distribution shift, scale change, species/task change, or instrument change.
- **Limiting-case test:** the theory behaves correctly in known extremes and does not require special patches.

## AI/ML and agent-research defaults

When the domain is AI/ML or AI agents, include these checks unless clearly irrelevant:

- What is the claimed capability, and what transformations should preserve it?
- Could the result come from memorization, leakage, benchmark overfitting, prompt cues, evaluator bias, tool artifacts, or hidden scaffolding?
- Does the model merely verbalize the rule, or does behavior remain stable under causal and distributional interventions?
- Is the representation available, causally used, or only decodable after the fact?
- Are failures clustered by surface form, ontology mismatch, objective conflict, memory limits, tool-use errors, or evaluation design?
- What result would force abandoning the current interpretation rather than adding a patch?

## Quality bar

A strong output should feel like a research collaborator trying to break the frame productively. It should be concrete enough that an agent or lab could run the next test, and skeptical enough that the preferred theory can die.
