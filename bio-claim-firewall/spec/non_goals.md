# Non-goals

What this project is not, and what it will not become without an explicit re-authorization from the human director. Guarded as a hard list because the failure mode of AI-adjacent biology projects is scope inflation into things that cannot be verified.

## Not this project

- **A general-purpose biology chatbot.** Answering arbitrary biology questions is not the product. The product is the firewall around a narrow, declared claim grammar.
- **A universal knowledge graph.** We do not merge sources into a single "truth graph". Every evidence record stays attributed to a frozen source with a snapshot hash. Cross-source inferences are made by rules at verification time, not by pre-merge.
- **A new foundation model.** No training runs. No fine-tunes. Models are third-party black boxes we call as untrusted proposers.
- **A virtual cell.** No cell simulation, no expression prediction, no perturbation forecasting. The verifier only checks *claims* against *frozen recorded observations*; it does not simulate the underlying biology.
- **A multi-agent research system.** One proposer, one verifier, one repairer. No agent swarms, no self-play, no recursive delegation.
- **A wet-lab controller.** No experiment execution, no ordering primers, no LIMS integration, no protocol generation intended for physical use.
- **A drug-discovery / clinical decision tool.** Any claim rendered by this system carries scope conditions and evidence pointers, not treatment recommendations. Downstream consumers that want to use accepted claims for clinical decisions need their own verification layer.
- **A citation manager.** We check that citations resolve and are consistent with claims; we do not curate a bibliography.

## Not this phase

Deferred until the deterministic checker has earned empirical value (Phase 5 release gates passed on the pilot world):

- **Direct MIDAS source reuse in published commits.** Verbal permission is enough to unblock scaffolding and private branches. Before any MIDAS-derived code lands in a commit intended to be published, the paper trail in `PROVENANCE.md` must include a LICENSE on upstream or an archived written permission.
- **Full Lean / Coq formalization of the rule engine.** Deferred until (a) the rule set has stabilized under adversarial testing and (b) the rule engine's TCB is small enough that formalization is a bounded job. Formalizing a moving target is anti-productive.
- **Cross-species claims.** The pilot world is human. Adding mouse or another species requires its own ontology snapshots, its own alias tables, and its own adversarial suite; deferred.
- **Non-perturbation evidence types beyond the initial four `record_type`s.** No functional-genomics screen aggregators, no clinical trial results, no imaging assays until the pilot's core loop is validated.
- **Uncertainty quantification beyond the confidence ladder.** No Bayesian posteriors, no calibrated probabilities in the verdict. `ACCEPTED_CONDITIONALLY` carries scope conditions, not probabilities. Calibration is measured at eval time (Phase 5), not asserted in the verdict.
- **Public API.** No hosted service. No inbound webhooks. Local CLI only until Phase 5 gates pass.

## Prohibited moves

Things that would break the guarantee and must never be done inside this project without explicit re-scoping:

- **Silently converting `CHECKER_ERROR` into a `REJECTED_*` code.** Fail-closed means the verdict surfaces as `CHECKER_ERROR`; the downstream consumer decides.
- **Silently converting `INCONCLUSIVE` into `REJECTED_*` or `ACCEPTED_CONDITIONALLY`.** Either the rule cascade accepted the claim under a matched positive record or it didn't.
- **Executing LLM output.** LLM produces a `Claim` (data). No generated Python, no generated SQL, no generated rule code enters the verifier's runtime.
- **Widening the CURIE prefix set at proposal time.** Adding a prefix is a spec change (bumped `claim.schema.json` + rule id + snapshot manifest), not a runtime knob.
- **Merging evidence records across sources into a single row.** Records are per-source. Any cross-source alignment happens at rule-cascade time and is logged in the derivation.
- **Post-hoc rewriting of a verdict.** The audit ledger is append-only. A superseded verdict gets a new `verdict_id`; the old one stays visible.
- **Auto-repair loops with no cap.** The `repair_claim` interface (Phase 4) runs at most `max_repair_attempts` times and every attempt is logged with prior verdicts intact.
