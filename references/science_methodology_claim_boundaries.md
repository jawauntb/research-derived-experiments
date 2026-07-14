# Science-methodology claim-boundary dossier

Purpose: advance the first reading tranche of S-031, S-032, S-033, and S-034
as a decision memo tied to the science primer and the seed/bootstrap calibration
experiment. The full source packets and downstream protocols remain open.

## Primary-source reading map

| Source | Reliable takeaway | Misuse to avoid | Repo decision / experiment gate |
| --- | --- | --- | --- |
| Nosek, Ebersole, DeHaven & Mellor, “The Preregistration Revolution” (2018), [PNAS DOI 10.1073/pnas.1708274114](https://psychologicalsciences.unimelb.edu.au/__data/assets/pdf_file/0007/2888098/The-preregistration-revolution.pdf) | Prediction and postdiction are both useful but provide different evidence; preregistration makes the distinction visible. | Treating preregistration as proof of a good design, or rewriting a failed prediction as a discovered success. | Preserve original gate status immutably. Amendments and post-hoc explanations receive distinct IDs and cannot overwrite the registered verdict. |
| Bradley Efron, “Bootstrap Methods: Another Look at the Jackknife” (1979), [Annals of Statistics DOI 10.1214/aos/1176344552](https://projecteuclid.org/journals/annals-of-statistics/volume-7/issue-1/Bootstrap-Methods-Another-Look-at-the-Jackknife/10.1214/aos/1176344552.full) | Bootstrap resampling estimates a sampling distribution from an observed sample under a specified sampling model. | Calling resamples “reruns,” resampling episodes when seeds/models are the independent unit, or assuming many resamples compensate for three independent seeds. | Every interval declares its independent unit and resampling scheme. Three-seed percentile intervals remain descriptive until simulation shows adequate coverage for the declared regime. |
| Gelman & Carlin, “Beyond Power Calculations: Assessing Type S and Type M Errors” (2014), [DOI 10.1177/1745691614551642](https://pubmed.ncbi.nlm.nih.gov/26186114/) | Noisy small-sample studies risk wrong-sign estimates and exaggerated magnitudes even when a result is significant. | Choosing a universal seed floor without effect/noise/hierarchy assumptions. | S-022 currently measures coverage, width, power, false-positive rate, and raw sign stability. A preregistered conditional Type-M exaggeration metric remains required before the result can justify a general promotion policy. |
| Silberzahn et al., “Many Analysts, One Data Set” (2018), [DOI 10.1177/2515245917747646](https://www.econweb.umd.edu/~pope/crowdsourcing_paper.pdf) | Defensible analytic choices can materially change conclusions; analytic heterogeneity is itself evidence about robustness. | Calling a second implementation independent when it reuses the same transformation, metric code, or judgment calls. | Theory-changing positives and negatives need a blinded second analysis path plus a specification curve or explicit estimator-dependence report. |
| Belinda Mo, “The Age of AI Agents Demands a New Scientific Paradigm to Sustain Trustworthy Science” (ICML 2026 position paper), [OpenReview manuscript](https://openreview.net/attachment?id=Pwt0TeGUE6&name=pdf) | Agentic research raises a verification gap; observability, traceable attribution, and reproducibility infrastructure are proposed responses. | Treating a position paper under review as empirical proof that a particular provenance system is sufficient. | Require run/evidence manifests and honest attribution, then test their completeness and reproducibility rather than inferring trust from their presence. |
| Bai et al., “The Story is Not the Science” (2026), [OpenReview](https://openreview.net/forum?id=cmXVfGR44k) | Execution-grounded evaluation checks code/data/process beyond narrative review; the reported framework finds issues missed by narrative-only review. | Generalizing one workshop evaluation system or agreement number to all scientific domains. | A promoted claim needs an executable public bundle or an explicit access block. Reviewers compare generated outputs to registered claims, not prose alone. |

## Perspective scan

- **Practitioner:** Keep one promotion table keyed by independent units,
  interval width, sign risk, artifact reproducibility, and external analysis.
- **Academic:** Preregistration, bootstrap, power, and replication solve different
  problems. No one mechanism licenses “trustworthy” by itself.
- **Skeptic:** A registry can faithfully preserve a bad design; a thousand
  bootstrap resamples can faithfully quantify the wrong unit; an AI evaluator
  can share the original agent’s blind spots.
- **Incentives:** Positive, fast, narratively coherent outputs receive attention.
  Immutable failed gates, outside analysts, and execution bundles counter those
  pressures by making revision costs visible.
- **Historian:** The tools extend older responses to selective reporting and
  analytic flexibility. Agentic scale changes throughput, not the logic of
  independent evidence.

## Contradictions and synthesis

- Preregistration limits undisclosed flexibility but can fossilize a weak gate;
  severe controls and amendments remain necessary.
- Resampling is valuable when its hierarchy matches data generation, but it
  cannot create independent seeds/models/tasks that were never observed.
- Agent-generated verification scales review, but genuine independence depends
  on different data, code paths, models, institutions, or humans—not a new role
  prompt alone.

Claim boundary: the repository can say it records and checks declared evidence
more reliably; it cannot say that provenance proves correctness or that every
experiment is reproducible until the commands and comparators execute from a
clean environment.

## Next gates

1. Seed/bootstrap simulation: retain the completed coverage, width, power,
   false-positive, and raw sign-stability grid, then preregister and add
   conditional Type-M exaggeration by independent-seed count and hierarchy.
   Publish failure regimes and derive a decision table rather than a universal
   floor.
2. Independent-analysis pilot: blind a second implementation to the original
   reward-deformation and topology summarizers; compare verdicts before
   reconciliation.
3. Execution-grounded capsule: one flagship positive and one theory-changing
   negative must rebuild their tables from public-safe rows in a clean clone.

Peer-review confidence: 9/10 for the methodological boundaries, 7/10 that the
proposed gates are sufficient. The missing sixth perspective is a security and
privacy reviewer: public execution bundles can improve verification while
increasing leakage, licensing, and reconstruction risk.
