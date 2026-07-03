# Generated JSON Surface Transition Record

## Regime Transition

### Old Regime

- Artifact types: stochastic moved-bottleneck rows with compact slot fields,
  alias-token fields, and parser-facing text argument fields.
- Operations: the agent emits opcode, slot/text-argument, and value fields; the
  first tool call succeeds or fails stochastically; failures require a repair
  call, successes require a no-op.
- Verifiers/gates: closed-loop final accuracy, first-call field/schema
  validity, failed-repair parsed slot/value accuracy, success no-op accuracy,
  moved-slot memory specificity, tool-value specificity, rank above chance, and
  visible-control null.
- Claim level: synthetic neural-agent diagnostic.

### New Regime

- Added artifact type/operation/verifier/gate: the agent now emits a
  fixed-length token sequence that renders to a JSON-like action string, such as
  `{ tool : read_slot , slot : second clue , value : 0 }` or `{ tool : noop }`.
  The evaluator parses the emitted token sequence back into opcode, slot, and
  value before granting external state.
- Preserved artifacts: the stochastic tool-failure task, moved critical slot,
  parser-facing text argument phrases, visible-control null, Modal L4 cost
  guard, and bootstrap gate summary.
- Preserved gates rerun: all stochastic text-surface gates are reused for
  `generated_json_bottleneck` and `generated_json_visible_control`, with field
  accuracy reinterpreted as exact emitted token-sequence accuracy.

### Rejected Alternatives

- Alternative: jump directly to a prompted production LLM with open-ended JSON
  tool calls.
- Why rejected: it would change model class, tokenizer, decoding, prompting,
  parser robustness, and tool-use prior at once. The generated token-sequence
  surface isolates the change from classifier-rendered fields to emitted
  parser strings while preserving the controlled synthetic neural-agent setup.

### Residual Finding

- What appeared beyond the old regime: the gate can now distinguish a moved
  bottleneck that survives emitted parser strings from one that only survives
  classifier-rendered text labels.
- What bottleneck remains: the emitted JSON is fixed-length and
  vocabulary-constrained, not natural-language autoregressive generation from a
  pretrained LLM.

### Readiness

| Gate | Status | Evidence |
| --- | --- | --- |
| Parser round trip | Pass | `tests/test_long_horizon_bottleneck.py::test_generated_json_surface_renders_and_parses_token_sequences` |
| Stochastic summary support | Pass | `tests/test_long_horizon_bottleneck.py::test_summarize_stochastic_rows_supports_generated_json_conditions` |
| Modal dry-run budget | Pass | Dry run `ap-F1mPrlinCEfkHbdW4gWUwy`; 32 L4 cells, conservative timeout cost `$8.63` under `$25.00` |
| Modal L4 generated JSON pass | Pass | Modal run `ap-Rl3RRB7Z1vDa9mGZdilrsg`; `generated_json_bottleneck` and `generated_json_visible_control` gates pass |

### Allowed Claim

If the generated JSON pass clears the inherited stochastic gates, the allowed
claim is: the moved bottleneck survives a parsed, emitted token-sequence JSON
tool-call surface in this synthetic long-horizon neural-agent diagnostic. It is
not yet a production API, pretrained LLM, or unconstrained natural-language
tool-use result.

### Next Operation

Run an autoregressive or prompt-level transfer where the model emits JSON text
under decoding rather than a fixed-length supervised token sequence, while
preserving closed-loop parser scoring, stochastic failures, and the
visible-control null.
