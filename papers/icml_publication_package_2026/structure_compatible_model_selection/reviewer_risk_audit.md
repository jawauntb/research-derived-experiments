# Reviewer Risk Audit

This is the adversarial review pass for the ICML-style package. The purpose is
to prevent the paper from sounding stronger than the evidence.

## Likely Rejection Reasons

1. **Bundle risk:** reviewers may see six phase notes plus a benchmark appendix
   rather than one paper. Mitigation: keep the main paper centered on Phase 6
   semantic model selection and use earlier phases as the evidence ladder.

2. **Oracle-structure risk:** several positive results use true or
   experimenter-chosen transformation families. Mitigation: label true
   compatibility as an upper bound, make discovered compatibility the deployable
   claim, and move oracle-only results into background.

3. **Thin uncertainty:** current tracked artifacts expose point estimates but
   not row-level bootstrap intervals. Mitigation: include the statistical plan,
   restore/generate row artifacts before submission, and do not claim
   significance until the intervals exist.

4. **Controls that weaken claims:** Phase 3 random vision augmentation is close
   to learned augmentation. Mitigation: present this as a boundary; do not make
   learned vision augmentation a headline.

5. **Semantic overclaim:** the semantic retrieval corpus is finite and
   constructed. Mitigation: say "finite semantic retrieval" and "frozen-encoder
   model selection," not broad paraphrase or language understanding.

6. **Benchmark appendix sprawl:** causally grounded agent suites could distract
   from the model-selection paper. Mitigation: keep the benchmark material in a
   short appendix and create a separate benchmark package.

7. **Reproducibility gap:** summary reports are tracked, raw SCG JSONL artifacts
   are absent. Mitigation: add row schema and artifact checklist now; restore or
   regenerate artifacts before submission.

## Strongest Safe Claim

In finite transformation-generated shifts, discovered structure-compatible
scores can improve OOD-free model selection among high train/ID candidates, and
wrong transformation controls can detect when the selected structure is not the
deployment-relevant one.

## Claims To Avoid

- "OOD certification" without the qualifier "finite structured setting."
- "Semantic robustness" without "finite retrieval" and "frozen encoder."
- "Causally grounded agents" as the main SCG result.
- "Learned transformation discovery" without noting experimenter-chosen
  candidate generator families.
- "ICML-ready" until CIs, row artifacts, and template conversion are complete.

## Concrete Fixes Already Reflected In This Package

- Main paper uses Phase 6 as the headline.
- Oracle compatibility is described as an upper bound.
- Vision/random-augmentation caveat appears in the appendix.
- Benchmark material is a companion appendix, not the main paper.
- Separate statistical plan names missing raw artifacts and required intervals.
- Separate benchmark package will carry the broader finite-agent claim.

