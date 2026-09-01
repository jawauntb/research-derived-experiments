# Bio Claim Firewall Phase 5 live-model smoke preregistration

## Discovery-Regime Audit

Question: Can the configured untrusted proposer produce contract-valid claim
data that the deterministic verifier can process against the frozen Replogle
2022 K562 pilot world, without a checker failure?

Current regime:

- Artifact types: versioned prompts, claim JSON, evidence records, verifier
  verdicts, append-only trajectory JSONL, and run summaries.
- Operations: `ModelManagerAdapter` renders a configured prompt; `Proposer`
  parses model JSON; `verify()` evaluates the frozen snapshot; the
  `TrajectoryLogger` preserves each case.
- Gates/verifiers: snapshot hashes, proposer contract, closed verdict enum,
  accepted-claim derivation, and no `CHECKER_ERROR`.
- Known limitations: five cases and one provider configuration test only the
  operational path. They do not establish biological truth, robustness,
  adversarial resistance, or model-family generalization.

Action class:

- Search inside the existing schema and verifier regime.
- It changes neither an accepted artifact type nor the verifier; it tests one
  configured provider and prompt against five fixed evidence selectors.

Experiment:

- Manifest: `bio-claim-firewall/eval/smoke/questions.json`.
- Positive targets: five distinct K562 CRISPRi perturbation-effect pairs from
  `perturbseq.replogle_2022`, resolved by subject CURIE, object CURIE, and sign.
- Decisive controls: SHA-256-locked question manifest; exactly the six
  preregistered source manifests with hash-verified data loading; exact-one
  evidence selection; repair disabled (`max_repair_attempts=0`); every durable
  proposer claim must satisfy the full claim schema; accepted derivations must
  resolve only to the frozen ledger.
- Stress boundary: prompt injection and unsupported-claim attacks are withheld
  for the separately preregistered adversarial suite. This smoke result must
  not be reported as evidence that the firewall eliminates unsupported claims.

Gate:

- Acceptance rule: all five cases dispatch through the configured proposer,
  yield one or more schema-valid claims, produce only the closed verdict types,
  yield no `CHECKER_ERROR`, and ensure every accepted derivation cites a real
  frozen evidence id.
- Withheld/rejected rule: absent credentials, optional dependencies, or a
  non-hash-valid frozen snapshot block the run. A proposer contract failure,
  schema failure, or checker error writes a failed summary and withholds every
  smoke claim.

Evidence and provenance:

- Representation/data clock: the immutable five-question manifest digest and
  all six pilot-world manifest hashes are copied into each local summary at run
  time. The question selectors avoid literal evidence ids because re-downloading
  a source changes the provenance-bound id.
- Outputs: raw trajectories and summaries stay in
  `eval/smoke_trajectories/` and are Git-ignored. A future reviewed result
  document may summarize outcomes but must retain the local receipt paths and
  state the provider, model, prompt version, checker version, and snapshot hashes.

Results:

- Status at preregistration: not run. The current environment has no configured
  provider credential or model SDK; no model output has been generated.

Residual content:

- The old regime already establishes fake-provider adapter behavior and
  deterministic verifier behavior independently.
- A successful run would add narrow operational evidence only: one real
  provider can traverse this fixed path. It would not promote any biology or
  safety claim beyond that scope.

Next move: from `bio-claim-firewall/`, run `python -m eval.smoke --preflight`
with the chosen provider dependencies and credential, then execute the fixed
five-case manifest once.
