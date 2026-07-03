# Autoregressive JSON Surface Transition Record

## Regime Transition

### Old Regime

- Artifact types: stochastic moved-bottleneck rows with compact fields, alias
  fields, parser-facing text fields, and fixed-length generated JSON token
  sequences.
- Operations: the agent emits an action at the first commit position; the first
  tool call succeeds or fails stochastically; failures require a repair call,
  successes require a no-op.
- Verifiers/gates: closed-loop final accuracy, first-action sequence/schema
  validity, failed-repair parsed slot/value accuracy, success no-op accuracy,
  moved-slot memory specificity, action-channel specificity, rank above chance,
  and visible-control null.
- Claim level: synthetic neural-agent diagnostic.

### New Regime

- Added artifact type/operation/verifier/gate: the action sequence is decoded
  autoregressively from the commit state, using the previously emitted token as
  input to the next step. The parser and JSON-like vocabulary are preserved.
- Preserved artifacts: stochastic tool failures, moved critical slot,
  parser-facing text argument phrases, emitted JSON token strings,
  visible-control null, Modal L4 cost guard, and bootstrap gate summary.
- Preserved gates rerun: all generated JSON stochastic gates are reused for
  `autoregressive_json_bottleneck` and `autoregressive_json_visible_control`.

### Rejected Alternatives

- Alternative: jump directly to a pretrained prompt-level LLM tool-use
  benchmark.
- Why rejected: a pretrained model would introduce tokenizer, prompt, decoding,
  prior knowledge, and parser-recovery confounds. The autoregressive JSON pass
  isolates decoding dynamics while keeping the controlled neural-agent task.

### Residual Finding

- What appeared beyond the old regime: the moved bottleneck can now be tested
  under a decoded action channel rather than a parallel sequence classifier.
- What bottleneck remains: decoding is still fixed-vocabulary, fixed-length,
  supervised, and synthetic rather than open-ended natural-language generation.

### Readiness

| Gate | Status | Evidence |
| --- | --- | --- |
| Stochastic summary support | Pass | `tests/test_long_horizon_bottleneck.py::test_summarize_stochastic_rows_supports_autoregressive_json_conditions` |
| Modal dry-run budget | Pass | Dry run `ap-RXUon2Eyammm4zCZRKlsZp`; 32 L4 cells, conservative timeout cost `$8.63` under `$25.00` |
| Modal L4 autoregressive JSON pass | Pass | Modal run `ap-Euh8MDI0zcNHo5thWHWtX2`; `autoregressive_json_bottleneck` and `autoregressive_json_visible_control` gates pass |

### Allowed Claim

If the autoregressive JSON pass clears the inherited stochastic gates, the
allowed claim is: the moved bottleneck survives a parsed, autoregressively
decoded JSON-like tool-call surface in this synthetic long-horizon neural-agent
diagnostic. It is not yet a production API, pretrained LLM, or open-ended
language tool-use result.

### Next Operation

Run a small pretrained or prompt-level transfer where JSON action text is
produced by a tokenizer/decoder stack and scored by the same parser, while
preserving stochastic failures and the visible-control null.
