# Output Templates

Use these templates as defaults. Adapt headings when the user asks for a different format.

## Discovery memo

```markdown
# Discovery Memo: [question or domain]

## 1. Current Frame
[Accepted explanation, ontology, and measurement regime.]

## 2. The Protected Assumption
[The field's possible "absolute time" equivalent.]

## 3. Assumption Ledger
| Assumption | Type | Load-bearing? | Why believed | Break test |
|---|---|---:|---|---|

## 4. Anomaly / Contradiction Map
| Anomaly | Why it strains the frame | Assumption implicated | Artifact risk | Cluster |
|---|---|---|---|---|

## 5. Candidate Einstein Moves
| Move | Assumption killed | Replacement concept | What becomes simpler | What must still be recovered | Falsifier |
|---|---|---|---|---|---|

## 6. Best Reframe
[Choose one, or explain why multiple remain live.]

## 7. Discriminating Predictions
| Test condition | Old frame predicts | New frame predicts | Diagnostic result |
|---|---|---|---|

## 8. Severe Experiment
[Protocol, controls, measurement, confounds, kill criterion.]

## 9. Claim Boundary
[Claim level, uncertainty, what is not established.]

## 10. Next Best Test
[One concrete high-information next action.]
```

## Experiment plan

```markdown
# Severe Experiment Plan: [title]

## Research Question
[Question precise enough to test.]

## Competing Frames
- Old frame: [claim]
- New frame: [claim]

## Hypothesis
[What should happen if the new frame is right.]

## Experimental Design
- Intervention/comparison:
- Units/samples/tasks:
- Measurement:
- Controls:
- Randomization/blinding:
- Replication plan:

## Predictions
| Outcome | Old frame interpretation | New frame interpretation | Decision rule |
|---|---|---|---|

## Artifact and Confound Checks
[Leakage, shortcuts, batch effects, evaluator artifacts, measurement artifacts, etc.]

## Kill Criterion
[Result that would force abandoning or materially weakening the hypothesis.]

## Analysis Plan
[Primary metric, secondary metrics, exclusion rules, uncertainty estimates.]

## Interpretation Boundaries
[What this experiment can and cannot prove.]
```

## Result-analysis report

```markdown
# Result Analysis: [experiment]

## 1. Pre-Result Predictions
| Theory/frame | Predicted result | Kill criterion |
|---|---|---|

## 2. Observed Results
[Concise summary of data/results.]

## 3. Measurement Validity Check
[Whether the measurement actually tracks the construct.]

## 4. Artifact / Confound Audit
[Most likely non-theory explanations.]

## 5. Theory Update
| Frame | Supported? | Weakened? | Needs patch? | New prediction required? |
|---|---:|---:|---:|---|

## 6. Claim Level
[level 0-4 with rationale.]

## 7. What Would Change My Mind
[Specific future evidence.]

## 8. Next Discriminating Test
[Highest-information follow-up.]
```

## Research-agent loop

```markdown
while research_question_not_resolved:
    gather_evidence_and_anomalies()
    update_assumption_ledger()
    identify_symmetry_or_invariance_failures()
    generate_candidate_reframes()
    score_reframes_for_anomaly_compression_and_risk()
    derive_discriminating_predictions()
    design_severe_experiment()
    run_or_simulate_or_request_experiment()
    analyze_results_against_predeclared_kill_criteria()
    update_claim_level_and_next_test()
```

Agent memory should preserve:

- Assumption ledger.
- Anomaly queue.
- Candidate reframes and scores.
- Experiment backlog.
- Prediction history.
- Result interpretations and claim levels.
- Abandoned theories and why they died.
