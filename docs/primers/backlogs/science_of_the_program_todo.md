# Science primer: comprehensive criticism-to-TODO analysis

Source: `science_of_the_program_primer.pdf`, *How This Knowledge Is Made: A Primer on the Scientific Method, Epistemology, and Trust Behind an AI-Generated Research Program* (30 PDF pages).

The Downloads copy and `docs/primers/science_of_the_program_primer.pdf` are byte-identical (SHA-256 `1796ebf7c30ff2d3e853310522557589b467a1ebe6ba7b0b25d73260c6bb71d0`). I read the full extracted text, checked the source HTML and README, and visually inspected PDF pages 1, 10, 12, 15, 21, 28, and 30. Page references below are PDF page numbers, not printed folios.

## Thesis

The primer's thesis is that AI-generated science cannot inherit credibility from reputation, labor cost, or assumed human oversight. It must earn calibrated trust through precommitted claims, negative controls, oracle ceilings, multi-seed uncertainty, conservative claim tiers, inspectable provenance, reproducibility, honest negative results, and empirical tests that distinguish retrieval/search from discovery. The program has built unusually strong experiment-level versions of these practices. Its unresolved scientific bottleneck is independence: the same research system still designs most worlds, gates, controls, summaries, tier assignments, and audits. Its unresolved statistical bottleneck is program-level error control: individually preregistered experiments do not control multiplicity across a long, adaptive research trajectory.

The executable implication is not “add more self-critique.” It is to build a program-wide evidence registry, promote structured raw evidence over prose extraction, calibrate uncertainty to actual seed counts, lock away audit gates and implementations, and arrange independent adversarial replication of both positive and negative flagship findings.

## Implementation log (2026-07-14)

| TODO | State | Implemented evidence |
| --- | --- | --- |
| S-001 | complete | HTML/PDF title metadata corrected and verified. |
| S-003 | partial | Reproduction language separates dispatch from verified reproduction; provenance has a non-mutating staleness check, while clean-clone equivalence remains. |
| S-022 | complete (synthetic calibration) | `experiments/seed_bootstrap_calibration/` evaluates 60 cells: three seeds fail every regime, hierarchy-aware promotion requires up to 64 seeds, and the weak/high-noise regime remains non-promotable. |
| S-031-S-034 | partial (first reading tranche) | `references/science_methodology_claim_boundaries.md` ties Nosek, Efron, Gelman/Carlin, Many Analysts, Mo, and Bai et al. to repo gates. Kerr, Gelman/Loken, selective inference/FDR, Tibshirani, Lakens, adversarial-collaboration protocols, Lu et al., the named replication study, and benchmark/reproduction evidence remain open. |
| S-036/S-038 | partial | Structured evidence, claim, manifest, and gate-verdict contracts validate in the root quality gate; full experiment migration remains. |

## Repo cross-check snapshot (2026-07-14)

- `docs/verification.json` enumerates 54 experiments, but only 20 have a linked preregistration, 24 have an auto-detected run command, and 13 have an auto-detected seed. Therefore the primer's “every serious experiment” and “exact command/seed” language is not presently machine-verifiable at repository scale.
- `scripts/gen_provenance.py` extracts up to four “gate-like” lines from the lexicographically latest Markdown result using a permissive regex. This is the exact prose-scraping failure mode the primer criticizes.
- `scripts/regen.py` has full local recipes for three experiment families and PDF builders for two families. Other entries print a detected command (which is absent for many); the script does not compare regenerated outputs against committed hashes. “One-command reproduce” exists as a dispatcher but not yet as a repository-wide reproduction guarantee.
- There are 195 Markdown result reports across 23 experiment directories, but only 24 committed result JSON files across five experiment directories. Structured/raw public evidence is therefore real but sparse and uneven.
- `docs/discovery_regime_audit.md` has 95 audit entries and repeatedly records action class, residual content, accepted/rejected artifacts, and next moves. This is valuable existing practice, but it is prose, not a normalized machine record linked one-to-one to all 54 experiment cards and all result versions.
- Existing strong foundations include `scripts/publication_guard.py`, `tests/test_publication_guard.py`, 54 generated `PROVENANCE.md` cards, `docs/external_contact_preregistration.md`, structured gate examples in `docs/causally_grounded_agents_release_schema.*`, many held-out/control experiments, and explicit negative/retraction records. The backlog below extends rather than discards these assets.
- `TODO.md` contains many experiment-specific replications but no program-level gate registry, multiplicity plan, independent replication program, locked audit-gate policy, or raw-row release policy for flagship claims.

## Exhaustive signal ledger

This ledger includes every distinct methodological idea, criticism, pitfall, or prescribed fix in the primer. Repeated statements are deduplicated into the S-prefixed TODOs below.

| PDF source | Signal | Kind | Repo cross-check | TODO mapping |
| --- | --- | --- | --- | --- |
| p.2, “Why a Book About Method” | Trust should rest on falsifiability and artifacts, not fluent prose or authority. | thesis | Strong norm, incompletely machine-enforced. | S-002, S-038, S-040, S-049 |
| pp.4-6, §§1.1-1.4 | Science is organized distrust; predictions should precede data; AI volume outruns human review; similar AI experimenters/reviewers share blind spots; observability/attribution/reproducibility are the response. | idea + criticism | Attribution and provenance exist; review independence does not. | S-002-S-004, S-019, S-028, S-040, S-048 |
| pp.8-10, §§2.1-2.2 | Prevent forking paths and HARKing with timestamped preregistrations containing setup, run count, thresholds, and a complete interpretation matrix. | idea | Preregistration links are detected for 20/54 cards and timestamp integrity is not automatically verified. | S-002, S-031, S-044 |
| pp.9-10, §2.3 | Gates should be named, numeric, precommitted, machine-readable booleans tied to claims. | idea | Structured examples exist, but the central provenance generator still scrapes prose. | S-036-S-038 |
| p.9, §2.4 | Behavior alone must never license a mechanism claim; structure-specific and anti-cheat gates must also pass. | idea | Strong recurring local practice, not a global schema invariant. | S-038, S-042, S-051 |
| pp.9-10, §2.5 | Interpretation matrices prevent spin, but “every outcome is publishable” can become unfalsifiable explanation. | tension | Common in preregistrations; no program-level audit of post-hoc cell use. | S-002, S-027, S-036, S-044 |
| pp.9-10, criticism after §2.5 | Single-study preregistration does not control between-study forking or family-wide false discoveries. Build a registry, multiplicity correction, and stopping rules. | central criticism | Missing. | S-030, S-031, S-036, S-037, S-044, S-052 |
| pp.11-13, §§3.1-3.3 | Use matched-random, wrong-signal, stale-signal, shuffled, suppression, and visible-answer controls; require distinct, mechanism-specific failures. | idea | Many examples exist, but no required cross-repo control taxonomy. | S-019, S-038 |
| p.12, §3.4 criticism | Anti-cheat controls cover only imagined shortcuts; similar systems share blind spots. Use independent adversaries to design shortcuts and verifiers. | central criticism | No independent-adversary program found. | S-019, S-028, S-033, S-046, S-048 |
| pp.14-16, §§4.1-4.2 | Report oracle ceilings; firewall oracle labels; use independent seeds to separate signal from luck. Three seeds are pilots, not promotion-grade evidence. | idea + criticism | Oracle and seed practices vary widely; seed metadata is sparse. | S-009, S-022, S-023, S-047 |
| p.15, §4.3 criticism | Bootstrap CIs over three seeds can project false precision; a CI cannot create information absent from the resampling units. | central criticism | Many three-/four-seed result families remain. | S-009, S-016, S-022, S-032, S-047 |
| pp.15-16, §4.4 | Lead with effect size and oracle gap, not significance alone. | idea | Common but not schema-enforced. | S-038, S-042 |
| pp.15-16, AUC pitfall | “AUC” denotes ROC AUC, error-time integral, and rank AUC with opposite directions. | concrete pitfall | No central metric namespace/type. | S-005, S-041 |
| pp.17-18, §§5.1-5.4 | Distinguish diagnostic, mechanism, regime-transition, and field claims; separately record evidence substrate; include claim boundaries and “do not claim” lists. | idea | Present in some papers and external-contact preregistration, not normalized across results. | S-027, S-042, S-050, S-051 |
| p.18, §5.4 criticism | Self-assigned prose tiers can drift upward; use an independent tier auditor. | criticism | No blind regrading workflow found. | S-027, S-028, S-042, S-046 |
| pp.20-21, §§6.1-6.2 | Provenance cards should be regenerated receipts containing command, seed, preregistration, evidence, and reproducibility instructions. | idea | Cards exist but many fields are missing and gate evidence is regex-extracted. | S-002, S-003, S-036, S-038, S-040 |
| pp.20-21, §6.3 | Publication guard, gitignore, and field allowlists should make public artifacts safe by construction. | idea | Publication guard and tests exist; standardized safe row exporters do not. | S-039, S-048 |
| p.21, §6.4 | A one-command reproducer should rerun deterministic work and verify outputs or dispatch exact remote commands. | idea | Partial dispatcher; little output equivalence verification. | S-003, S-040, S-045 |
| p.21, §6.4 criticism | Provenance proves a recorded recipe, not unbiased execution; gitignored rows and AI summaries leave a trust gap; prose regex has misread hedging. | central criticism | Confirmed in `gen_provenance.py`; structured rows cover only five result-producing experiment directories. | S-003, S-029, S-038-S-040, S-045 |
| pp.22-24, §§7.1-7.4 | Publish negatives, retractions, and crashes-as-non-evidence; explain misses without retroactively passing gates. | idea | Strong local practice, but no normalized status ledger. | S-010-S-018, S-029, S-043 |
| p.23, §7.4 criticism | Honest negative prose does not prove correct computation; independently replicate flagship negatives. | central criticism | No external negative-replication program found. | S-010-S-018, S-029, S-046 |
| pp.25-26, §§8.1-8.2 | Record retrieval/search/discovery and quarantine residual content not explained by the old framework. | idea | 95 prose audit entries; no normalized linkage to every result. | S-035, S-047, S-052 |
| p.26, §8.3 | Test discovery through invention of the next experiment, truly held-out transfer, and evidence-sensitive mechanism traces. | idea | Intervention invention, held-out transfer, and traces exist in bounded synthetic forms. | S-024-S-026, S-053 |
| p.26, §8.3 criticism | Self-classifying discovery is introspective and weak; behavioral transfer and confound-killing tests deserve more weight. | central criticism | Audit classes are self-authored prose. | S-024-S-028, S-047, S-053 |
| pp.28-29, §9.2 | Six pressure points: power, external validity, incomplete proxy resistance, program-level forking, metric-stack overfitting, and trust in AI summaries. | synthesis | All are partially or wholly open. | S-009, S-019-S-023, S-030, S-036-S-047 |
| p.29, §9.3 | Independence is the highest-value investment: outside red-team, data, implementation, and replication. | priority | Missing as an operating layer. | S-017-S-021, S-027-S-029, S-033, S-046, S-048 |
| pp.29-30, §§9.4-9.6 | Calibrated trust: accept synthetic diagnostic/mechanism claims provisionally; hold field claims until external replication; apply the eight-question reader checklist to every result. | operating rule | Not encoded as a promotion check. | S-036, S-042, S-049-S-052 |
| PDF metadata and visual pp.28-30 | PDF `/Title` incorrectly names the mathematics primer; the pressure-point and reader-checklist tables split across pages without repeated headers and with a row divided at the page boundary. | article defect (observed/inferred from render) | HTML `<title>` is wrong; CSS does not prevent the split. | S-001, S-008 |

## Deduplicated executable backlog

Priority meaning: P0 blocks trustworthy promotion or corrects a factual defect; P1 is the next high-value hardening/experiment; P2 materially improves the program but can follow the trust core; P3 is exploratory. Status describes the repository today, not whether the TODO is optional.

### Article corrections and improvements

#### S-001 — Correct the PDF/HTML document metadata

- **Priority / status:** P0 / new.
- **Source / inference:** PDF p.1 title; PDF metadata from `pdfinfo`; HTML `<title>`; inference flag: **no**.
- **Action:** Change the HTML `<title>` from “The Mathematics of the Research Program — A Primer from First Principles” to the actual science-primer title, rebuild the PDF, and verify embedded metadata.
- **Affected paths:** `docs/primers/science_of_the_program_primer.html`, `docs/primers/science_of_the_program_primer.pdf`, `docs/primers/README.md` if rebuild notes change.
- **Deliverable:** Rebuilt PDF whose visible title and `/Title` agree.
- **Pass/fail gate:** `pdfinfo ... | rg '^Title:'` returns “How This Knowledge Is Made”; text/page count remain expected; visual title page has no regression.
- **Dependencies:** Chromium PDF build command from `docs/primers/README.md`.
- **Rationale:** Incorrect metadata breaks indexing, accessibility, citation managers, and provenance for the very document teaching provenance.

#### S-002 — Replace universal methodology claims with an audited coverage table

- **Priority / status:** P0 / partial.
- **Source / inference:** pp.8-10 §§2.2-2.5, pp.20-21 §§6.2-6.4, p.25 §8.1; inference flag: **no**.
- **Action:** Audit each “every,” “never,” and “always” claim and either prove it from a generated manifest or qualify it. Add a dated coverage box for preregistration, seed, command, structured-gate, audit-card, and reproducibility coverage.
- **Affected paths:** primer HTML/PDF, `scripts/gen_provenance.py`, `docs/verification.json`, `docs/verification.md`.
- **Deliverable:** Generated methodology-coverage table embedded in the primer or linked as a versioned appendix.
- **Pass/fail gate:** Every universal claim has a machine test or is rewritten as a scoped claim; current counts reconcile exactly with the manifest.
- **Dependencies:** S-036, S-038, S-047.
- **Rationale:** Current machine evidence (20/54 prereg links, 24/54 commands, 13/54 seeds) does not justify the article's repository-wide wording.

#### S-003 — Correct the “one-command reproduce” and provenance guarantees

- **Priority / status:** P0 / partial.
- **Source / inference:** pp.20-21 §§6.2 and 6.4; inference flag: **no**.
- **Action:** Rewrite the article to distinguish “dispatcher,” “paper rebuild,” “deterministic rerun,” and “verified bit/metric equivalence.” State that provenance extraction can drift until structured records and hash verification land.
- **Affected paths:** primer HTML/PDF, `scripts/regen.py`, `scripts/gen_provenance.py`, `docs/verification.*`.
- **Deliverable:** Capability matrix with honest levels for all experiments and corrected explanatory prose.
- **Pass/fail gate:** Article statements match executable behavior; CI checks that every manifest entry has a declared reproduction level; no claim says outputs are checked unless a comparator runs.
- **Dependencies:** S-040, S-045.
- **Rationale:** Printing a possibly missing command is valuable, but it is not reproduction or equivalence verification.

#### S-004 — Add a real bibliography and claim-level source notes

- **Priority / status:** P1 / new.
- **Source / inference:** pp.4-5 (Feynman and Mo), pp.8-10 (forking paths/HARKing), pp.14-16 (bootstrap), pp.22-24 (publication bias); inference flag: **no**.
- **Action:** Add a references section and inline endnote markers for quoted/paraphrased methodological claims, including the exact Mo ICML/OpenReview record and the source of the Feynman quotation.
- **Affected paths:** primer HTML/PDF, `references/SOURCES.md`, optionally `papers/external_citation_review/*`.
- **Deliverable:** Human-readable bibliography with stable DOI/OpenReview links and a source ledger entry per methodological cluster.
- **Pass/fail gate:** Every named author, quotation, statistical prescription, and historical term resolves to a bibliographic record; the PDF contains no orphan citation.
- **Dependencies:** S-031-S-035.
- **Rationale:** A methodology primer should demonstrate the source transparency it prescribes.

#### S-005 — Replace bare “AUC” with typed metric names everywhere

- **Priority / status:** P1 / partial.
- **Source / inference:** pp.15-16 §4.4 pitfall; inference flag: **no**.
- **Action:** Revise the primer examples and audit papers/results for bare `AUC`. Require `roc_auc`, `rank_auc_probability`, or `error_time_integral` plus direction (`higher_is_better`) and units.
- **Affected paths:** primer HTML/PDF, `papers/**/*.md`, `experiments/**/results/*`, metric schema from S-041.
- **Deliverable:** Migration report and glossary table linking legacy labels to canonical metric IDs.
- **Pass/fail gate:** Linter finds zero ambiguous bare-AUC fields/headings outside quoted legacy text; every AUC value declares semantic type and direction.
- **Dependencies:** S-041.
- **Rationale:** The current three meanings can invert conclusions.

#### S-006 — Tighten the bootstrap explanation and promotion rule

- **Priority / status:** P1 / new.
- **Source / inference:** pp.14-16 §§4.2-4.4; inference flag: **yes** (the corrective statistical wording follows from the primer's own caveat).
- **Action:** Explain that the bootstrap estimates uncertainty under a specified resampling scheme; it is not literally a rerun simulator, and resampling three seeds cannot support reliable tail quantiles. Replace a universal 5-10 seed rule with preregistered precision/power targets and a minimum promotion floor.
- **Affected paths:** primer HTML/PDF, `docs/system_design.md`, preregistration template to be added under S-047.
- **Deliverable:** Corrected section with seed/episode/task hierarchy examples and a promotion decision table.
- **Pass/fail gate:** Examples identify the independent resampling unit; no promoted claim relies on a three-seed percentile interval; rule is backed by simulation S-022.
- **Dependencies:** S-022, S-032, S-047.
- **Rationale:** Seed count and bootstrap validity depend on hierarchy and target precision, not a decorative number of resamples.

#### S-007 — Add a live “what remains unverified” panel

- **Priority / status:** P1 / partial.
- **Source / inference:** pp.28-30 §§9.1-9.6; inference flag: **yes**.
- **Action:** Convert the six pressure points into a generated status panel with owner, evidence link, last audit date, and closure criterion.
- **Affected paths:** primer HTML/PDF, `TODO.md`, `docs/verification.*`, proposed `docs/program_evidence_registry.json`.
- **Deliverable:** Versioned panel showing open/partial/closed status without hand-edited drift.
- **Pass/fail gate:** Each pressure point maps to at least one registry record and gate; rebuilding the primer fails on a stale/missing mapping.
- **Dependencies:** S-036, S-052.
- **Rationale:** The criticism chapter should remain operational rather than freezing a 2026 snapshot into prose.

#### S-008 — Repair the two tables that split across pp.28-30

- **Priority / status:** P2 / new.
- **Source / inference:** visual inspection of PDF pp.28-30, §9.2 and §9.5; inference flag: **no**.
- **Action:** Prevent individual pressure-point rows from splitting, repeat table headers on continuation pages, and keep the reader-checklist header with its first rows.
- **Affected paths:** primer HTML/PDF CSS and table markup.
- **Deliverable:** Reflowed PDF with readable continued tables.
- **Pass/fail gate:** Rendered pages show no row divided mid-sentence, every continuation has column headers, and no clipping/overlap occurs.
- **Dependencies:** S-001 rebuild pass.
- **Rationale:** The current page boundary makes the central six-point critique harder to audit.

### Old experiments to correct or replicate

#### S-009 — Audit every three-seed claim and rerun promotion candidates

- **Priority / status:** P0 / partial.
- **Source / inference:** pp.14-16 §§4.2-4.3 and p.28 statistical-power pressure point; inference flag: **no**.
- **Action:** Inventory all result families with <=3 independent seeds; mark them pilot-only unless a preregistered precision analysis justifies otherwise; rerun only claims proposed for promotion using the seed count selected by S-022/S-047.
- **Affected paths:** `experiments/**/results/*`, `papers/**/*.md`, `docs/verification.json`, `TODO.md`.
- **Deliverable:** Machine-readable seed audit plus prioritized rerun queue and updated claim tiers.
- **Pass/fail gate:** No field/mechanism promotion cites an unqualified three-seed CI; reruns meet their preregistered interval-width/power target and publish per-seed rows.
- **Dependencies:** S-022, S-036, S-039, S-047.
- **Rationale:** This is the primer's most pervasive statistical weakness and affects multiple existing papers.

#### S-010 — Independently reproduce the 0.30-not-0.50 reward-deformation exponent

- **Priority / status:** P0 / partial.
- **Source / inference:** pp.22-24 §7.2; inference flag: **no**.
- **Action:** Reimplement the slope/effective-dimension estimator without reusing the original summarizer; rerun or rescore the capacity/reward-deformation rows; test whether anisotropic, stripe, and point geometries remain near effective dimension one.
- **Affected paths:** `experiments/grid_cell_weakness/*`, its result reports, `papers/grid_cell_weakness/preregistration.md`, rebuilt effective-dimension paper.
- **Deliverable:** Independent code path, public-safe row bundle, estimator comparison, and signed replication verdict.
- **Pass/fail gate:** Blinded implementation reproduces the preregistered rejection of 0.5 and estimates alpha within a preregistered tolerance; discrepancies trigger a correction, not averaging.
- **Dependencies:** S-039, S-046; external auditor preferred.
- **Rationale:** The negative is theory-changing and therefore deserves at least as much replication as a positive.

#### S-011 — Independently reproduce the failed weakness-to-topology mediation

- **Priority / status:** P0 / partial.
- **Source / inference:** pp.22-24 §7.2; inference flag: **no**.
- **Action:** Recompute topology, weakness, OOD, and mediation with a second implementation and preregistered causal estimand; verify that weakness and topology predict independently rather than through a single mediator.
- **Affected paths:** `experiments/grid_cell_weakness/*`, `papers/grid_cell_weakness/*`, relevant figure builders.
- **Deliverable:** Replication report with raw/aggregate rows, DAG/estimand, sensitivity analysis, and retraction status.
- **Pass/fail gate:** G2-G4 verdicts and mediation conclusion match under independent code and reasonable specification curve; otherwise downgrade the negative to method-dependent.
- **Dependencies:** S-031, S-039, S-046.
- **Rationale:** A failed mediation reorganized the theory; estimator dependence must be ruled out.

#### S-012 — Replicate the semantic concern-geometry wrong-sign result

- **Priority / status:** P1 / partial.
- **Source / inference:** pp.22-24 §7.2; inference flag: **no**.
- **Action:** Rerun the semantic concern deformation with a non-OpenAI encoder, external semantic negative controls, multiple prompt authors, and a blinded scorer; test whether the negative lift (-0.44 in the primer) is stable or model/prompt-specific.
- **Affected paths:** `experiments/semantic_concern_geometry/*`, `experiments/concept_geometry/*`, `TODO.md` open external controls.
- **Deliverable:** Cross-model sign-replication matrix and corrected claim boundary.
- **Pass/fail gate:** Direction and interval are preregistered; at least two independent model families and a prompt-author holdout agree before treating “does not transfer to language” as robust.
- **Dependencies:** S-021, S-039, S-046.
- **Rationale:** A wrong-sign result is especially sensitive to metric orientation, prompt construction, and substrate choice.

#### S-013 — Stress-test the external weakness hard kill on materially different external setups

- **Priority / status:** P0 / partial.
- **Source / inference:** pp.22-24 §7.2 and p.28 external-validity pressure point; inference flag: **no**.
- **Action:** Preserve the Pythia-LoRA P1 hard kill (`rho=-0.0817`) and test only materially different preregistered setups: public grokking checkpoints, full fine-tuning, two-input modular addition, or an outsider benchmark. Do not rerun the same operationalization until it passes.
- **Affected paths:** `experiments/external_contact/*`, `docs/external_contact_preregistration.md`, `papers/weakness_invariance_neurips/*`.
- **Deliverable:** One external replication tranche with immutable hard-kill interpretation.
- **Pass/fail gate:** Old negative remains recorded; each new setup has a frozen gate, wrong-group control, and no post-hoc redefinition; promotion requires independent external data/model authorship.
- **Dependencies:** S-021, S-036, S-044.
- **Rationale:** This is both a negative replication and the program's cleanest test of synthetic-to-real transfer.

#### S-014 — Reproduce the uncertainty-aware planner losing to greedy

- **Priority / status:** P1 / partial.
- **Source / inference:** pp.22-24 §7.2; inference flag: **no**.
- **Action:** Rerun the planner comparison at the decision boundary with calibrated and deliberately miscalibrated world models, more seeds, and an oracle-uncertainty arm; separate “uncertainty methods fail” from “confidence estimates are wrong.”
- **Affected paths:** `experiments/ensemble_uncertainty/modal_ensemble_uncertainty_sweep.py`, `papers/ensemble_uncertainty/paper.md`, its figures/provenance, and the program registry.
- **Deliverable:** Factorial replication isolating planner sophistication, calibration, and model misspecification.
- **Pass/fail gate:** Greedy-vs-aware contrast and all four original gate verdicts are reproduced or explicitly corrected; oracle uncertainty must rescue the planner if calibration is the mechanism.
- **Dependencies:** S-036 exact lineage mapping, S-039, S-047.
- **Rationale:** The result supports a broad “sophistication can hurt” lesson but may actually diagnose bad uncertainty.

#### S-015 — Reproduce the factorial that retracted the strong subset claim

- **Priority / status:** P0 / partial.
- **Source / inference:** pp.22-24 §7.2; inference flag: **no**.
- **Action:** Independently rescore `m4_suite_c_factorial_ablation` and rerun the load-bearing mechanism factorial with a held-out implementation; preserve the retraction unless the preregistered replication reverses it.
- **Affected paths:** `experiments/commitment_surface/results/m4_suite_c_factorial_ablation_2026_07_09.*`, `papers/commitment_surface/*`, Suite C runners.
- **Deliverable:** Independent factorial table, interaction estimates, and explicit retraction confirmation/correction.
- **Pass/fail gate:** Necessary/sufficient mechanism verdicts match the original across independent implementation and adequate seeds; no strong subset language survives without the same factorial gate.
- **Dependencies:** S-020, S-039, S-046.
- **Rationale:** This is a program-level self-correction and should become a flagship negative verification target.

#### S-016 — Re-evaluate the positive mean rejected by a wide CI

- **Priority / status:** P1 / partial.
- **Source / inference:** p.15 §4.3 (+0.695 with CI crossing zero); inference flag: **no**.
- **Action:** Identify the exact long-horizon specificity result in the registry, freeze a seed-expansion plan, and estimate the effect with hierarchical resampling at the correct unit.
- **Affected paths:** `experiments/long_horizon_bottleneck/results/zzzzzzzzzzz_prompt_json_transfer_l4_4seed_2026_07_03.md`, `experiments/long_horizon_bottleneck/BENCHMARK_CARD.md`, `papers/long_horizon_bottleneck/paper.md`, the corresponding runner, and program registry.
- **Deliverable:** Link from the primer example to exact rows, expanded result, and preserved original gate verdict.
- **Pass/fail gate:** Original failure is never retroactively passed; the follow-up is a separately registered study whose interval/power target is met and whose artifact ID is distinct.
- **Dependencies:** S-022, S-036, S-039, S-047.
- **Rationale:** This is the ideal worked example for distinguishing a failed preregistered gate from later evidence.

#### S-017 — Verify the near-miss calibration without converting it to a pass

- **Priority / status:** P1 / partial.
- **Source / inference:** p.23 §7.3 (-0.054 against a +/-0.05 band); inference flag: **no**.
- **Action:** Link the primer anecdote to its exact gate record, independently recompute the calibration distribution, and ensure all papers/provenance retain `failed_original_gate=true` plus a distinct post-hoc explanation.
- **Affected paths:** `experiments/commitment_surface/results/e1_concern_weighted.*`, `experiments/commitment_surface/results/e1_misspecification_variance.*`, `experiments/commitment_surface/README.md`, `papers/commitment_surface/*`, and the structured gate schema.
- **Deliverable:** Immutable two-record history: original failure and post-hoc calibration analysis.
- **Pass/fail gate:** No generated summary or provenance card reports the gate as passed; the explanation is labeled post-hoc and separately hashed.
- **Dependencies:** S-036, S-038, S-043.
- **Rationale:** The program's epistemic integrity depends on being able to represent explanation without verdict mutation.

#### S-018 — Independently replicate a balanced set of flagship positive claims

- **Priority / status:** P0 / new.
- **Source / inference:** pp.4-6 AI trust problem; p.29 §9.3; inference flag: **no**.
- **Action:** Select 3-5 promoted positives spanning synthetic, real-model, and causal-steering substrates; hand only preregistration, public bundle, and commands to an outside human/different-system replication team.
- **Affected paths:** new `replications/` package, selected experiments/papers, registry.
- **Deliverable:** Signed replication reports, environment manifests, independent code diffs, and resolution records.
- **Pass/fail gate:** Selection is frozen before replication; every selected result receives a verdict; failures downgrade claim tiers automatically.
- **Dependencies:** S-039, S-040, S-046, external collaborator.
- **Rationale:** Replicating only negatives or only successes would create a new selection bias.

### New experiments

#### S-019 — Run an independent adversarial-control challenge

- **Priority / status:** P0 / new.
- **Source / inference:** p.12 §3.4 criticism, pp.28-29 proxy-resistance/independence; inference flag: **no**.
- **Action:** Freeze a flagship task and its public behavior gate; ask an independent adversary, blind to the intended mechanism code, to build the strongest shortcut that passes. Experimenters may not add controls after seeing submissions for the primary round.
- **Affected paths:** new `experiments/adversarial_audit_challenge/`, selected benchmark card, preregistration, registry.
- **Deliverable:** Submitted cheats, exploit taxonomy, locked verifier results, and next-round corrections.
- **Pass/fail gate:** At least two independently authored shortcuts are evaluated; any shortcut pass invalidates the mechanism claim under the frozen verifier; zero passes supports only bounded proxy resistance.
- **Dependencies:** S-020, S-046, external adversary.
- **Rationale:** Controls designed by the original system cannot cover blind spots it cannot represent.

#### S-020 — Test a locked audit gate and unseen implementation

- **Priority / status:** P0 / new.
- **Source / inference:** pp.28-29 metric-stack overfitting; inference flag: **no**.
- **Action:** Develop against visible gates, then evaluate once on a cryptographically committed audit gate and independently written task implementation. Prohibit using audit outcomes to tune the primary claim.
- **Affected paths:** new audit harness, selected flagship experiment, registry, CI policy.
- **Deliverable:** Commitments, reveal log, unseen implementation, and one-shot verdict.
- **Pass/fail gate:** Hashes predate development completion; no audit data appear in training/dev artifacts; result passes both visible and locked gates.
- **Dependencies:** S-040, S-044, S-046.
- **Rationale:** This directly tests whether the program has overfit its own metric stack.

#### S-021 — Make outsider-authored environments the external-validity benchmark

- **Priority / status:** P0 / partial.
- **Source / inference:** pp.28-29 external-validity pressure point; inference flag: **no**.
- **Action:** Choose at least two third-party datasets/environments whose generators and metrics predate this program; preregister directional predictions and strongest shortcuts before access to held-out evaluation.
- **Affected paths:** extend `experiments/external_contact/`, `docs/external_contact_preregistration.md`, new data cards.
- **Deliverable:** External-contact suite with licenses, immutable versions, held-out access protocol, and result table.
- **Pass/fail gate:** No program-authored generator defines the headline task; results are scored by third-party or locked official evaluation; failures remain primary outcomes.
- **Dependencies:** data access/licensing, S-036, S-044.
- **Rationale:** Self-built worlds may encode the intended answer into both task and gate.

#### S-022 — Calibrate seed floors and bootstrap coverage by simulation

- **Priority / status:** P0 / new.
- **Source / inference:** pp.14-16 §§4.2-4.3 and p.28 power pressure point; inference flag: **yes**.
- **Action:** Use empirical variance structures from representative experiments to simulate true coverage, false-positive rate, interval width, and sign stability for n=3, 5, 8, 10, 16, and 64 under percentile, BCa, t, hierarchical, and randomization intervals.
- **Affected paths:** new `experiments/statistical_calibration/`, preregistration, results, test fixtures.
- **Deliverable:** Decision table mapping claim type/variance to required seeds and estimator.
- **Pass/fail gate:** Recommended policies achieve preregistered >=90/95% coverage as appropriate and target precision; methods failing coverage are barred from promotion.
- **Dependencies:** Representative public-safe rows from S-039; S-032.
- **Rationale:** The primer's 5-10 floor is directionally useful but should be empirically calibrated to this program.

#### S-023 — Deliberately inject oracle leakage and verify detectors

- **Priority / status:** P1 / new.
- **Source / inference:** p.14 §4.1 oracle firewall; inference flag: **yes**.
- **Action:** Create seeded leak variants (direct label, index correlation, preprocessing cache, split contamination, filename/order side channel) and measure whether existing grep/tests and behavioral controls detect them.
- **Affected paths:** new `experiments/oracle_leak_audit/`, reusable test utilities, quality checks.
- **Deliverable:** Leak corpus, detector matrix, and hardening patches.
- **Pass/fail gate:** Every preregistered leak class is caught before scoring; clean variants retain nominal performance; undetected leaks become blocking P0 issues.
- **Dependencies:** S-038, S-040.
- **Rationale:** A firewall should be tested with adversarial faults, not only inspected for known strings.

#### S-024 — Benchmark invention of the next experiment versus use of a supplied probe

- **Priority / status:** P0 / partial.
- **Source / inference:** p.26 §8.3; inference flag: **no**.
- **Action:** Build paired tasks where one agent chooses among supplied probes and another must invent a new intervention/apparatus under the same budget. Include latent mechanisms for which all supplied probes are insufficient but one compositional invention is diagnostic.
- **Affected paths:** extend `experiments/concerned_syntax/intervention_invention.py` or new discovery benchmark, preregistration, mechanism traces.
- **Deliverable:** Benchmark with ground-truth information gain, novelty constraints, and accepted/rejected inventions.
- **Pass/fail gate:** Discovery credit requires a new executable artifact, improved posterior identification on held-out mechanisms, and superiority to retrieval/search baselines; fluent novelty descriptions do not count.
- **Dependencies:** S-025, S-026, S-035.
- **Rationale:** This is the primer's most concrete behavioral alternative to self-declared discovery.

#### S-025 — Build a genuinely unseen transfer ladder

- **Priority / status:** P0 / partial.
- **Source / inference:** p.26 §8.3 and p.28 external validity; inference flag: **no**.
- **Action:** Standardize transfer from held-out seeds to roles, parse families, surfaces, generators, model families, and outsider datasets; prevent any training-time generated examples from covering the deployment region.
- **Affected paths:** relevant concerned-syntax, commitment-surface E5, structure-compatible, activation, and external-contact suites.
- **Deliverable:** Cross-experiment transfer matrix and contamination audit.
- **Pass/fail gate:** Every “discovery” or field promotion passes at least one generator/model/dataset level never used during design; transformed-label coverage is explicitly measured and absent.
- **Dependencies:** S-036, S-039, S-044.
- **Rationale:** The existing E5 confound shows that nominal holdout can still be retrieval through labeled coverage.

#### S-026 — Validate mechanism traces by evidence dependence, not narrative quality

- **Priority / status:** P1 / partial.
- **Source / inference:** p.26 §8.3; inference flag: **yes**.
- **Action:** Perturb observations, swap evidence order, insert contradictory evidence, and hide the final answer; score whether hypothesis/belief updates change correctly. Compare blind human/different-model judges against automated trace labels.
- **Affected paths:** `experiments/concerned_syntax/mechanism_trace.py`, results, trace schema.
- **Deliverable:** Causal trace-validity benchmark and counterfactual trace dataset.
- **Pass/fail gate:** Trace score predicts correct belief revision under held-out perturbations and rejects polished but evidence-insensitive rationalizations.
- **Dependencies:** S-028, S-038.
- **Rationale:** A narrated “hypothesis -> observation -> update” can itself be post-hoc pattern completion.

#### S-027 — Run blind claim-tier regrading

- **Priority / status:** P0 / new.
- **Source / inference:** p.18 §5.4 criticism; inference flag: **no**.
- **Action:** Strip paper titles/authors/conclusions, give structured evidence cards to independent graders, and ask them to assign diagnostic/mechanism/regime/field tiers plus evidence substrate. Compare with author-assigned tiers.
- **Affected paths:** new `audits/claim_tiers/`, paper/result metadata, registry.
- **Deliverable:** Inter-rater agreement, upgrade/downgrade matrix, adjudication record.
- **Pass/fail gate:** Promoted claims require no unresolved independent downgrade and a preregistered agreement threshold; systematic upward bias triggers tier-policy revision.
- **Dependencies:** S-042, S-046, independent graders.
- **Rationale:** Tier prose is not self-certifying.

#### S-028 — Measure shared-blind-spot risk across auditor types

- **Priority / status:** P1 / new.
- **Source / inference:** pp.4-5 §1.2, p.12 §3.4, p.29 §9.3; inference flag: **yes**.
- **Action:** Seed known statistical, leakage, claim-tier, and provenance faults into blinded bundles; compare same-model self-review, different-model review, human review, and hybrid review on detection, false alarms, and time/cost.
- **Affected paths:** new `experiments/auditor_diversity/`, audit fixtures, governance docs.
- **Deliverable:** Auditor-composition evidence and routing policy.
- **Pass/fail gate:** Independence claims require demonstrated incremental fault detection beyond repeated same-system review; chosen policy meets preregistered recall/false-positive gates.
- **Dependencies:** External reviewers, S-033, S-046.
- **Rationale:** “Different system” is only useful if its error correlation is actually lower.

#### S-029 — Verify that flagship negative numbers are correctly computed

- **Priority / status:** P0 / new.
- **Source / inference:** p.23 §7.4 criticism; inference flag: **no**.
- **Action:** Sample negatives stratified by theory impact and computation complexity; independently recompute from public-safe rows, trace raw-to-summary transformations, and audit metric direction/denominator/missing-cell handling.
- **Affected paths:** selected result families, new `replications/negative_verification/`, registry.
- **Deliverable:** Negative-result verification cards with computational and interpretive verdicts.
- **Pass/fail gate:** 100% of sampled high-impact negatives have reproducible row-level derivations; any mismatch issues a correction and expands the audit sample.
- **Dependencies:** S-039, S-040, S-046.
- **Rationale:** Publishing a negative demonstrates selection honesty, not arithmetic correctness.

#### S-030 — Run one prospective claim family under program-level error control

- **Priority / status:** P0 / new.
- **Source / inference:** pp.9-10 §2.5 criticism and p.28 program-level forking; inference flag: **no**.
- **Action:** Choose a new research family, preregister the complete hypothesis/gate family, alpha/FDR allocation or hierarchical decision rule, spending/stopping rule, and allowed redirects; register every attempted study including crashes/non-evidence.
- **Affected paths:** new experiment family plus `docs/program_evidence_registry.json`, statistical tooling.
- **Deliverable:** End-to-end demonstration of family-level inference across an adaptive research sequence.
- **Pass/fail gate:** All branches and gates are registered before outcomes; multiplicity-adjusted and raw results are both published; stopping occurs exactly at the frozen rule.
- **Dependencies:** S-031, S-036, S-037, S-044.
- **Rationale:** The sharpest critique should be resolved with a real prospective trial, not only infrastructure.

### Research to read, internalize, and cite

#### S-031 — Build the preregistration, selective-inference, and multiplicity reading packet

- **Priority / status:** P0 / partial.
- **Source / inference:** pp.8-10 Chapter 2 and p.28 program-level forking; inference flag: **yes**.
- **Action:** Read and synthesize Kerr on HARKing; Nosek et al., *The Preregistration Revolution*; Gelman/Loken on garden-of-forking-paths; Benjamini-Hochberg FDR; hierarchical/selective inference; and Registered Reports. Translate each into a concrete program policy.
- **Affected paths:** `references/SOURCES.md`, new `notes/program_level_inference.md`, primer bibliography, registry design.
- **Deliverable:** Source matrix: threat -> estimand -> control procedure -> repo implementation.
- **Pass/fail gate:** At least one primary source supports each registry/multiplicity choice; synthesis distinguishes confirmatory families from exploratory search and preserves raw p/effect estimates.
- **Dependencies:** None.
- **Rationale:** “Multiplicity correction” is not one universal operation; the unit/family and adaptive rule must be justified.

#### S-032 — Build the small-sample uncertainty and power reading packet

- **Priority / status:** P0 / partial (Efron and Gelman/Carlin tranche complete).
- **Source / inference:** pp.14-16 Chapter 4; inference flag: **yes**.
- **Action:** Read Efron/Tibshirani and modern bootstrap coverage guidance, Lakens on sample-size justification, hierarchical/mixed-effects resampling, randomization tests, and sequential/precision-based design. Explicitly study failure at n=3 independent units.
- **Affected paths:** `references/SOURCES.md`, new `notes/seed_and_bootstrap_policy.md`, primer bibliography.
- **Deliverable:** Statistical design memo with estimator selection flowchart and simulation hypotheses for S-022.
- **Pass/fail gate:** Memo identifies independent unit, dependence structure, effect/precision target, and stopping rule for each flagship design family.
- **Dependencies:** Access to representative schemas.
- **Rationale:** A seed floor without a statistical model is a heuristic, not a defensible design.

#### S-033 — Read adversarial collaboration, many-analyst, and replication-design literature

- **Priority / status:** P0 / partial (Many Analysts foundation complete).
- **Source / inference:** p.12 §3.4 and p.29 §9.3; inference flag: **yes**.
- **Action:** Internalize Kahneman's adversarial collaboration, Many Analysts/Many Labs, replicability-across-studies procedures, and independent reanalysis models. Extract contracts for blindness, frozen disagreements, authorship, and conflict resolution.
- **Affected paths:** `references/SOURCES.md`, new `docs/independent_audit_protocol.md`, primer bibliography.
- **Deliverable:** Operational protocol used by S-018-S-020 and S-027-S-029.
- **Pass/fail gate:** Protocol specifies independence criteria, what each party sees, immutable precommitments, payment/credit, and how contradictory outcomes update claims.
- **Dependencies:** Potential collaborator input.
- **Rationale:** “Ask an outsider” is underspecified until information flow and adjudication are designed.

#### S-034 — Update the AI-generated science trust evidence base

- **Priority / status:** P1 / partial.
- **Source / inference:** pp.4-6 §§1.2-1.3; inference flag: **yes**.
- **Action:** Read/cite Mo, *The Age of AI Agents Demands a New Scientific Paradigm to Sustain Trustworthy Science* (ICML 2026/OpenReview); Lu et al., *Towards end-to-end automation of AI research* (Nature 2026, DOI `10.1038/s41586-026-10265-5`); the 2026 PNAS AI replication-games study (DOI `10.1073/pnas.2524747123`); AI-Researcher/Scientist-Bench; and critical real-world reproduction studies of AI scientist systems.
- **Affected paths:** `references/SOURCES.md`, primer bibliography, new trust-method note.
- **Deliverable:** Evidence table comparing self-review, AI-led, AI-assisted, and independent-human replication.
- **Pass/fail gate:** Primer claims about AI volume, review, and trust are tied to current primary evidence and distinguish observed results from extrapolation.
- **Dependencies:** Literature access.
- **Rationale:** This emerging field changed rapidly after the program's initial methodological anchor.

#### S-035 — Ground “retrieval/search/discovery” in novelty and mechanism-validation research

- **Priority / status:** P1 / partial.
- **Source / inference:** pp.25-26 Chapter 8; inference flag: **yes**.
- **Action:** Review work on computational scientific discovery, underspecification, causal mechanism recovery, novelty/rediscovery benchmarks, and tool/invention evaluation. Include third-party AI-science benchmarks that separate guided reconstruction from open-ended discovery.
- **Affected paths:** `references/SOURCES.md`, `docs/discovery_regime_audit.md`, new `notes/discovery_validation.md`.
- **Deliverable:** Operational definitions with observable criteria and counterexamples.
- **Pass/fail gate:** “Discovery” cannot be assigned solely from prose; it requires a new artifact/verifier plus held-out empirical gain and survives contamination/rediscovery controls.
- **Dependencies:** S-024-S-026 design feedback.
- **Rationale:** The current three classes are useful vocabulary but not yet validated measurement.

### Software, framework, and skill work

#### S-036 — Implement the program-level evidence and gate registry

- **Priority / status:** P0 / new.
- **Source / inference:** pp.9-10 §2.5 and pp.28-29 §9.2; inference flag: **no**.
- **Action:** Create one append-only registry entry for every frozen gate, result version, status, claim family, prereg commit, outcome, correction, and supersession. Link experiments, papers, audits, and raw bundles by stable IDs.
- **Affected paths:** new `docs/program_evidence_registry.json` plus schema, generator, tests, human view; `docs/verification.*`; `TODO.md`.
- **Deliverable:** Complete searchable registry and migration of current flagship families.
- **Pass/fail gate:** No promoted claim lacks a closed set of contributing gates; dropped/failed/crashed gates remain visible; schema and referential-integrity tests pass.
- **Dependencies:** S-038, S-043, S-044.
- **Rationale:** This is the missing substrate for multiplicity, lineage, and independent auditing.

#### S-037 — Add claim-family multiplicity and sequential-stopping evaluation

- **Priority / status:** P0 / new.
- **Source / inference:** pp.9-10 §2.5 criticism and p.28 pressure point; inference flag: **no**.
- **Action:** Let each field/mechanism claim declare its hypothesis family and correction policy (e.g., Holm/FDR/hierarchical/e-values as justified), compute raw and adjusted decisions, and enforce preregistered alpha/effort spending and stop rules.
- **Affected paths:** registry tooling, statistical module, prereg template, CI tests.
- **Deliverable:** Deterministic family-level decision report.
- **Pass/fail gate:** Synthetic fixtures recover known family-wise/FDR behavior; every promoted family has an explicit denominator and policy; unregistered additions fail promotion.
- **Dependencies:** S-031, S-036, S-044.
- **Rationale:** Individual boolean gates do not control error across an adaptive program.

#### S-038 — Replace prose regex with structured gate records and a single scorer

- **Priority / status:** P0 / partial.
- **Source / inference:** pp.9-10 §2.3, p.21 §6.4 criticism, p.29 trust pressure point; inference flag: **no**.
- **Action:** Standardize records with gate ID, prereg threshold AST/expression, metric ID, resampling unit, achieved value/interval, pass/fail/non-evidence, claim axis, controls, oracle, and provenance hash. Generate Markdown from records, never records from Markdown.
- **Affected paths:** `docs/causally_grounded_agents_release_schema.*`, new schema/library, `scripts/gen_provenance.py`, summarizers, tests.
- **Deliverable:** Versioned gate schema, evaluator, migration adapters, and generated reports.
- **Pass/fail gate:** Structured fixtures reproduce existing gates; hedged prose cannot alter verdict; provenance contains record IDs/hashes rather than regex lines.
- **Dependencies:** S-036, S-041, S-043.
- **Rationale:** This closes the documented audit-layer misread and makes claim tests genuinely machine-checkable.

#### S-039 — Publish public-safe row evidence for flagship suites

- **Priority / status:** P0 / partial.
- **Source / inference:** p.21 §6.4 criticism and pp.28-29 trust pressure point; inference flag: **no**.
- **Action:** Define allowlisted row schemas that exclude secrets/raw copyrighted corpora while retaining seed, condition, metrics, exclusions, and lineage. Export signed compressed CSV/JSONL or Parquet for flagship positives and negatives.
- **Affected paths:** new `experiments/<name>/results/rows_*`, exporter library, `scripts/publication_guard.py`, schema/tests; extend precedent in `data/paper_b/`.
- **Deliverable:** Recomputable row bundles with data cards and hashes.
- **Pass/fail gate:** An independent script recomputes every headline gate from the public bundle; publication guard passes; forbidden fields are rejected by tests.
- **Dependencies:** S-038, S-040.
- **Rationale:** Summaries alone cannot establish that reported numbers faithfully reflect executions.

#### S-040 — Add immutable execution manifests, artifact hashes, and lineage

- **Priority / status:** P0 / new.
- **Source / inference:** pp.20-21 Chapter 6; inference flag: **yes**.
- **Action:** Record git SHA, dirty state, command argv, environment/container digest, dependencies, code/input/output hashes, seed list, timestamps, executor identity/type, and parent run IDs. Sign or at least content-address manifests.
- **Affected paths:** run wrapper, artifact-manifest schema, `scripts/gen_provenance.py`, `scripts/regen.py`.
- **Deliverable:** One manifest per run and an integrity verifier.
- **Pass/fail gate:** Tampered input/output/command is detected; a provenance card can be regenerated solely from manifests; dirty/unversioned runs cannot be promoted.
- **Dependencies:** S-038, storage policy.
- **Rationale:** A recorded command is a claim; content-addressed lineage is stronger evidence of what produced what.

#### S-041 — Create a typed metric registry (including AUC)

- **Priority / status:** P1 / new.
- **Source / inference:** pp.15-16 §4.4 pitfall; inference flag: **no**.
- **Action:** Give every metric a stable ID, mathematical definition, units, valid range, aggregation/resampling rules, direction, oracle/chance reference, and display label.
- **Affected paths:** new metric schema/library, experiment summarizers, papers/results lint, primer glossary.
- **Deliverable:** Metric registry plus adapters for legacy fields.
- **Pass/fail gate:** Schema rejects ambiguous `auc`; gate scorer cannot compare values with incompatible metric IDs or reversed direction.
- **Dependencies:** S-038.
- **Rationale:** Typed metrics turn a prose warning into compile/test-time prevention.

#### S-042 — Encode claim tier and evidence substrate as checked fields

- **Priority / status:** P0 / partial.
- **Source / inference:** pp.17-18 Chapter 5; inference flag: **no**.
- **Action:** Add separate enums for claim strength and substrate, required “does/does not claim” text, evidence prerequisites, external-replication status, and automatic maximum tier from passed gates.
- **Affected paths:** registry/gate schema, paper templates, `docs/external_contact_preregistration.md`, result generators, linter.
- **Deliverable:** Tier policy and generated claim-boundary blocks.
- **Pass/fail gate:** A synthetic diagnostic cannot be labeled field claim; mechanism requires behavior plus structure/causal gate; field requires transfer/adversarial/external criteria and independent audit.
- **Dependencies:** S-027, S-036, S-038.
- **Rationale:** Self-assigned free prose permits systematic half-rung inflation.

#### S-043 — Normalize positive, negative, failed-gate, crash, retraction, and supersession states

- **Priority / status:** P0 / partial.
- **Source / inference:** pp.22-24 Chapter 7; inference flag: **no**.
- **Action:** Implement immutable status transitions where crash/no-artifact is `non_evidence`, failed gates cannot become passed, post-hoc analyses are children, and retractions/supersessions retain the old record.
- **Affected paths:** gate/registry schema, result templates, provenance cards, tests.
- **Deliverable:** Status state machine and migrated flagship negative histories.
- **Pass/fail gate:** Invalid transitions fail tests/CI; generated views always show original and current verdict; crash rows never enter effect estimates.
- **Dependencies:** S-036, S-038.
- **Rationale:** The program already follows this norm in prose; encoding it prevents silent history rewriting.

#### S-044 — Verify preregistration integrity, amendments, and stopping rules

- **Priority / status:** P0 / partial.
- **Source / inference:** pp.8-10 Chapter 2 and p.28 program-level pressure point; inference flag: **no**.
- **Action:** Record prereg commit SHA/time, first-result commit/time, immutable gate hash, amendment parent, post-hoc flag, planned seeds/runs, and stopping rule; fail if chronology or mutation constraints are violated.
- **Affected paths:** prereg templates, registry, git audit script, quality checks.
- **Deliverable:** `prereg_audit` command and report for all promoted claims.
- **Pass/fail gate:** Every confirmatory result proves prereg hash predates data inspection; amendments cannot alter parent gates; planned vs observed sample counts reconcile.
- **Dependencies:** S-036, S-040.
- **Rationale:** A filename called `preregistration.md` does not by itself prove preregistration.

#### S-045 — Upgrade `regen.py` from dispatcher to verifier

- **Priority / status:** P0 / partial.
- **Source / inference:** p.21 §6.4; inference flag: **no**.
- **Action:** Declare reproduction level per experiment; execute hermetic/local recipes when possible; for remote runs emit exact pinned manifest; compare regenerated structured rows/gates/PDFs with committed hashes or tolerance contracts.
- **Affected paths:** `scripts/regen.py`, `docs/verification.json`, run manifests, tests, docs.
- **Deliverable:** `regen verify <name>` and repository coverage report.
- **Pass/fail gate:** Every experiment has a nonempty actionable recipe and declared limitation; verifier detects intentional output drift; promoted flagship suites reach row/gate equivalence.
- **Dependencies:** S-038-S-040.
- **Rationale:** Reproduction means verifying regenerated evidence, not merely printing an old command.

#### S-046 — Generate independent replication/audit bundles

- **Priority / status:** P0 / new.
- **Source / inference:** p.12 §3.4, p.18 §5.4, p.29 §9.3; inference flag: **yes**.
- **Action:** Package preregistration, environment, public rows, expected schema (not hidden outcomes), commands, known limitations, and a signed verdict template; support blinded bundles that omit author conclusions and audit-gate internals.
- **Affected paths:** new `scripts/build_replication_bundle.py`, `replications/README.md`, registry integration, publication guard tests.
- **Deliverable:** Reusable bundle for S-018-S-020 and S-027-S-029.
- **Pass/fail gate:** Clean-room machine can validate bundle and run smoke/recompute without private paths/secrets; bundle hash is registered before auditor access.
- **Dependencies:** S-039, S-040, S-045.
- **Rationale:** The observability apparatus should make outside checking cheap and well-scoped.

#### S-047 — Make discovery audits and seed/precision requirements first-class records

- **Priority / status:** P1 / partial.
- **Source / inference:** pp.14-16 Chapter 4 and pp.25-26 Chapter 8; inference flag: **no**.
- **Action:** Move action class, residual content, old-regime explanation, retractions, next verifier, seed hierarchy, target precision/power, and transfer level into structured records linked to gates/results. Generate `docs/discovery_regime_audit.md` from them.
- **Affected paths:** discovery ledger, registry schema, prereg/result templates, provenance generator.
- **Deliverable:** Normalized audit records covering every promoted result and every new experiment.
- **Pass/fail gate:** No discovery label lacks empirical verifier/transfer level; no promoted CI lacks independent-unit and precision fields; prose view round-trips from records.
- **Dependencies:** S-022, S-035-S-038.
- **Rationale:** Existing audit prose is rich but cannot be reliably queried or enforced.

#### S-048 — Preserve and extend public-safe-by-construction checks

- **Priority / status:** P1 / existing.
- **Source / inference:** pp.20-21 §6.3; inference flag: **no**.
- **Action:** Keep `publication_guard.py` and its tests mandatory; extend them with field-allowlist schema validation, archive/hash checks, and regression fixtures for new row/replication bundles.
- **Affected paths:** `scripts/publication_guard.py`, `tests/test_publication_guard.py`, exporter/bundle tests.
- **Deliverable:** Expanded safety test suite integrated into quality checks.
- **Pass/fail gate:** Secrets, forbidden archives, oversized files, and nonallowlisted row fields are blocked; safe fixtures pass; false-positive cases remain tested.
- **Dependencies:** S-039, S-046.
- **Rationale:** This is one of the article's strongest verified engineering ideas and should scale with new evidence releases.

### New directions to consider

#### S-049 — Adopt independence-first research governance

- **Priority / status:** P0 / new.
- **Source / inference:** p.29 §9.3; inference flag: **no**.
- **Action:** Separate roles for hypothesis author, implementer, adversary, gate custodian, scorer, tier grader, and replication lead; require at least one genuinely independent role for field-claim promotion.
- **Affected paths:** `AGENTS.md`, new `docs/research_governance.md`, registry roles, PR templates.
- **Deliverable:** RACI-style governance plus independence declaration per promoted claim.
- **Pass/fail gate:** Registry rejects field promotion when all roles share the same system/person/model lineage; exceptions are explicit and downgrade the tier.
- **Dependencies:** S-028, S-033, S-036.
- **Rationale:** Independence is a system architecture property, not a final review checkbox.

#### S-050 — Make external contact the primary promotion currency

- **Priority / status:** P0 / partial.
- **Source / inference:** pp.28-30 §§9.1-9.6; inference flag: **no**.
- **Action:** Prioritize outsider datasets/models/environments and independent replication over additional internally authored synthetic wins; keep synthetic studies for diagnosis and mechanism isolation.
- **Affected paths:** `TODO.md`, roadmap/strategy docs, claim-tier policy, external-contact suite.
- **Deliverable:** Promotion rubric and budget allocation for external validation.
- **Pass/fail gate:** No field claim is based solely on self-built worlds; roadmap reports share of compute/review spent on external contact and replication.
- **Dependencies:** S-021, S-042, S-049.
- **Rationale:** More internal rigor cannot substitute for contact with systems the program did not design.

#### S-051 — Treat synthetic worlds as a claim ceiling, not a defect

- **Priority / status:** P1 / partial.
- **Source / inference:** pp.17-18 claim tiers and pp.28-30 calibrated trust; inference flag: **yes**.
- **Action:** Formalize which conclusions synthetic worlds can support (instrument validation, diagnostic separation, bounded mechanism under explicit assumptions) and which they cannot (general field or human/neural claims).
- **Affected paths:** claim-tier policy, paper templates, benchmark cards, primer.
- **Deliverable:** Synthetic-evidence claim ceiling with examples from this repository.
- **Pass/fail gate:** Linter flags abstracts/conclusions that exceed the substrate ceiling; exceptions cite external/causal transfer evidence.
- **Dependencies:** S-042.
- **Rationale:** The right response is calibrated use, not abandoning controlled worlds or overgeneralizing from them.

#### S-052 — Build an evidence graph for cumulative program updates

- **Priority / status:** P1 / new.
- **Source / inference:** pp.9-10 program-level forking, pp.22-24 negative results, pp.25-26 residual content; inference flag: **yes**.
- **Action:** Represent claims, gates, experiments, dependencies, contradictions, retractions, and residual content as a DAG. Compute which high-level claims depend on failed or unreplicated nodes and show before/after program updates.
- **Affected paths:** registry, generated visualization/report, `docs/system_design.md`, paper lineage notes.
- **Deliverable:** Queryable evidence graph and claim-impact report.
- **Pass/fail gate:** Every promoted claim traces to evidence nodes; retracting a node deterministically identifies all affected claims; no circular support.
- **Dependencies:** S-036-S-038, S-043, S-047.
- **Rationale:** This makes “every result narrows the program” explicit and reveals hidden reuse/multiplicity across papers.

#### S-053 — Define discovery as new executable capability plus external verification

- **Priority / status:** P1 / partial.
- **Source / inference:** pp.25-26 Chapter 8; inference flag: **yes**.
- **Action:** Reserve “discovery” for results that introduce a new executable artifact/verifier, change feasible intervention space, outperform retrieval/search on held-out mechanisms, and survive independent or external validation. Keep “discovery-leaning” as exploratory only.
- **Affected paths:** discovery audit policy, claim-tier schema, experiment/paper language.
- **Deliverable:** Promotion rule with positive and rejected examples.
- **Pass/fail gate:** Self-authored novelty rationale alone cannot pass; S-024/S-025 behavioral gates and independent audit are required for promoted discovery.
- **Dependencies:** S-024-S-028, S-035, S-042, S-047.
- **Rationale:** The same pattern-completing system should not certify that it transcended pattern completion through introspection.

## Recommended execution order

1. **Correct the public account:** S-001-S-006 and S-008. The primer should not overstate current guarantees while infrastructure is being built.
2. **Create the trust substrate:** S-036-S-045 and S-047-S-048, beginning with structured gates, the evidence registry, immutable statuses, and public-safe rows.
3. **Resolve statistics prospectively:** S-022, S-031-S-032, S-037, S-044, S-047, then run S-030 and the targeted reruns S-009/S-016.
4. **Buy independence:** S-033, S-046, S-049, then S-018-S-021 and S-027-S-029. This is the highest-value scientific investment.
5. **Validate discovery rather than label it:** S-024-S-026, S-028, S-035, S-053.
6. **Replicate theory-changing negatives:** S-010-S-017 in parallel only after their public rows, exact lineages, and independent bundles exist.

## Coverage summary

- Article corrections/improvements: **8** TODOs (S-001-S-008).
- Old experiments to correct/replicate: **10** TODOs (S-009-S-018).
- New experiments: **12** TODOs (S-019-S-030).
- Research to read/internalize/cite: **5** TODOs (S-031-S-035).
- Software/framework/skill work: **13** TODOs (S-036-S-048).
- New directions: **5** TODOs (S-049-S-053).
- Total: **53** executable TODOs.

This backlog intentionally counts an idea once even when the primer repeats it. The signal ledger provides the full source-to-TODO mapping so no criticism disappears during deduplication.
