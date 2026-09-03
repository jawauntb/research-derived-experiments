# Bio Claim Firewall scope-binding confirmation — 2026-09-03

## Trigger and target decision

The final release review of the role-bound 36/36 checkpoint found two remaining
semantic substitutions that the deterministic boundary could accept: a parsed
positive direction from a negated, non-K562, non-knockdown, causal, or universal
sentence; and ambiguous role binding when the same gene appears more than once.
This card freezes the repair and an expanded confirmation before either the
boundary or live-case manifest changes. The decision is whether this stricter
boundary may replace the role-bound checkpoint in the public pilot receipt.

## Locked intervention

The K562 natural-language boundary will require an explicit K562 context and one
explicit knockdown, reject negation, unsupported perturbations, non-K562
contexts, and causal or universal qualifiers, and reject repeated known HGNC
symbols. After parsing, subject and object must be distinct, occur exactly once,
and appear in the supported subject -> knockdown -> predicate -> object order.
No prompt, evidence record, deterministic evidence rule, provider configuration,
or checker version may change.

## Representation, data clock, and controls

- Approved pre-intervention manifest SHA-256:
  `1d48433958df5685e41d408c6b0f25674df92f6379e509b3ade673bb14fa74c2`.
- Data clock: the same frozen six-source Replogle 2022 K562 evidence cache used
  by the prior 2026-09-02 runs.
- Matrix: the existing 12 cases plus one explicit negation case and one repeated
  entity/role-confusion case, each repeated three times (42 repetitions total).
- New unit controls must reject negated, wrong-context, wrong-perturbation,
  universal/causal, and repeated-entity inputs before the deterministic checker.
- Existing supported, reversed-sign, missing-pair, ambiguity, schema, bypass,
  and fake-citation controls must retain their expected outcomes.

## Fatal gates and provenance

All gates are noncompensatory: 42/42 safe repetitions; zero provider/runtime
errors; exact expected deterministic outcomes where required; fail-closed
refusal of all unsupported-scope cases; no attacker content in a canonical
receipt; per-result model-invocation accounting; and exact prompt-file,
boundary-source, model-config, manifest, case-manifest, and evidence-source
hashes in the ignored run summary. Any failure withholds the public replacement.

The run id is
`2026-09-03-openai-v2-boundary-scope-confirmation`. Results may be promoted only
through `bio-claim-firewall/eval/live_claims/RESULTS_2026-09-02.{json,md}` and
the allowlist exporter at `sites/bio_claim_firewall/export_live_model_receipt.py`.

## Promotion boundary

A pass supports only the pinned OpenAI/K562 boundary on this 14-case matrix and
the supported active-voice grammar. It does not support broad language
understanding, other models, other evidence worlds, biological truth, clinical
use, or demonstrated customer value. Rejected syntax remains rejected rather
than being silently reinterpreted.
