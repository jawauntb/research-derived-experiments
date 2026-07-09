# Scoring Rubrics

Use these rubrics to rank candidate reframes, hypotheses, experiments, and results. Scores are decision aids, not proof.

## Candidate reframe score

Score each dimension 0-3.

| Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| anomaly compression | explains none | explains one | explains a cluster | makes several anomalies expected |
| assumption economy | adds patches | adds complexity | removes one assumption | replaces a protected assumption with a simpler principle |
| prediction risk | vague | weakly testable | clear prediction | clear prediction that could kill the theory |
| old-success recovery | ignores old successes | handwaves them | recovers most | recovers them as limiting cases |
| invariance/symmetry | no gain | minor gain | removes asymmetry | reveals a deeper invariant |
| operational clarity | vague terms | partially measurable | measurable | new clean measurement regime |
| artifact resistance | likely artifact | possible artifact | has checks | survives obvious artifact alternatives |

Suggested interpretation:

- **0-7:** speculative; do not prioritize unless cheap.
- **8-13:** plausible; needs sharper predictions.
- **14-18:** promising; design a severe test.
- **19-21:** high-leverage candidate; prioritize if feasible.

## Experiment severity score

Score each dimension 0-3.

| Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| discriminates theories | no | weakly | clearly | old and new frames predict opposite/quantitatively different outcomes |
| kill criterion | none | vague | specific | predeclared and hard to evade |
| artifact control | none | basic | strong | multiple independent artifact checks |
| measurement validity | poor | indirect | adequate | direct or independently triangulated |
| feasibility | infeasible | costly/slow | feasible | cheap, fast, and repeatable |
| information gain | low | moderate | high | resolves a central uncertainty |
| generalization | none | one context | multiple contexts | transports across relevant contexts/tasks/instruments |

Prioritize high-severity experiments over supportive demonstrations.

## Anomaly priority score

Score 0-3 each:

- Reproducible.
- Strains a load-bearing assumption.
- Appears across methods or contexts.
- Not easily dismissed as artifact.
- Connects to other anomalies.
- Points to a discriminating experiment.

High-priority anomalies are not necessarily large effects. Small, reliable asymmetries can be more important than dramatic but unstable effects.

## Claim-strength update rules

Upgrade claim strength only when evidence is severe:

- Survived a predeclared kill test.
- Replicated under independent measurement or data generation.
- Ruled out the leading artifact explanation.
- Distinguished the new frame from a strong old-frame alternative.
- Recovered old successes while predicting new results.

Downgrade when:

- A key prediction fails.
- A simpler artifact explains the result.
- The theory needs ad hoc patches without new predictions.
- The result only supports a weaker claim than originally stated.
- The effect does not transport across minimal reasonable variants.

## Red flags

Treat these as warnings:

- The theory explains every possible result.
- The proposed experiment can only confirm, not disconfirm.
- The key construct has no operational definition.
- The explanation changes when labels or frames change, but observables do not.
- The model adds hidden variables solely to save the frame.
- Evidence is correlation-only but the claim is causal.
- Evidence is benchmark-only but the claim is capability-general.
- Failure cases are described as noise without an artifact audit.
