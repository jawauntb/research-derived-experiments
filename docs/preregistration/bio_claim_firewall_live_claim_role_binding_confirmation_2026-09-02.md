# Bio Claim Firewall role-binding confirmation — 2026-09-02

## Trigger and target decision

After the first reviewed 36/36 confirmation, a self-audit found one remaining
transport ambiguity: checking that both parsed gene symbols occur in the input
does not prove that the parser preserved their subject/object roles. This card
freezes a final conservative repair before execution. The decision is whether
the role-bound boundary may replace the prior reviewed checkpoint in the public
pilot receipt.

## Locked intervention

For the supported K562 natural-language grammar, at least one exact parsed
subject token must occur before the sole recognized directional predicate and
at least one exact parsed object token must occur after it. Inputs outside that
narrow active-voice order fail closed. No manifest, prompt, evidence record,
checker rule, expected answer, provider configuration, or checker version may
change for the confirmation.

## Representation, assumptions, and controls

- Approved manifest SHA-256:
  `1d48433958df5685e41d408c6b0f25674df92f6379e509b3ade673bb14fa74c2`.
- Matrix: the same 12 cases × three repetitions and frozen six-source K562
  evidence cache used by all 2026-09-02 live-claim runs.
- The public pilot deliberately prefers refusal over guessing on passive voice
  or other unsupported syntax.
- New unit controls must reject a parser response that swaps `MED19` and `GYPB`
  even though both tokens are present.
- Existing supported, reversed-sign, missing-pair, ambiguity, scope, schema,
  bypass, and fake-citation controls must retain their expected outcomes.

## Fatal gates and provenance

All gates are noncompensatory: 36/36 safe repetitions; zero provider/runtime
errors; exact expected interpretations and deterministic outcomes where
required; allowed fail-closed hostile-input refusals; no attacker content in a
canonical receipt; 30 recorded model invocations and six pre-model refusals;
and exact prompt-file, boundary-source, model-config, manifest, and evidence
source hashes in the ignored run summary.

The run id is
`2026-09-02-openai-v2-boundary-role-confirmation`. Results are promoted only
through `bio-claim-firewall/eval/live_claims/RESULTS_2026-09-02.{json,md}` and
the allowlist exporter at `sites/bio_claim_firewall/export_live_model_receipt.py`.

## Promotion boundary

A pass supports only the role-bound, pinned OpenAI/K562 boundary on this fixed
matrix. It does not support passive-voice coverage, broad language
understanding, other models, other evidence worlds, biological truth, clinical
use, or demonstrated customer value.
