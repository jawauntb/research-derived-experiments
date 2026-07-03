# Text Argument-Surface Transition Record

## Regime Transition

### Old Regime

- Artifact types: stochastic moved-bottleneck rows with compact slot arguments
  and alias-token slot arguments.
- Operations: the agent emits opcode, slot-argument, and value fields; the
  first tool call succeeds or fails stochastically; failures require a repair
  call, successes require a no-op.
- Verifiers/gates: closed-loop final accuracy, first-call field/schema
  validity, failed-repair parsed slot/value accuracy, success no-op accuracy,
  moved-slot memory specificity, tool-value specificity, rank above chance, and
  visible-control null.
- Claim level: synthetic neural-agent diagnostic.

### New Regime

- Added artifact type/operation/verifier/gate: the slot argument is rendered as
  a parser-facing text phrase before being mapped back to a canonical slot.
  Registered phrase variants per slot are `clue_i`, ordinal phrases such as
  `second clue`, and descriptive phrases such as `memory slot i`.
- Preserved artifacts: the stochastic tool-failure task, moved critical slot,
  visible-control null, Modal L4 cost guard, and bootstrap gate summary.
- Preserved gates rerun: all stochastic alias-surface gates are reused for
  `text_stochastic_bottleneck` and `text_visible_control`.

### Rejected Alternatives

- Alternative: jump directly to free-form language-model generation.
- Why rejected: it would change model class, tokenizer, prompting, decoding,
  and parser robustness at once. The text argument surface isolates the parser
  namespace change before moving to natural-language agents.

### Residual Finding

- What appeared beyond the old regime: the gate can now distinguish a moved
  bottleneck that survives text-labeled JSON arguments from one that only
  survives compact categorical aliases.
- What bottleneck remains: the emitted argument is still a classifier token
  rendered as text, not open-ended generation from a language model.

### Readiness

| Gate | Status | Evidence |
| --- | --- | --- |
| Parser round trip | Pass | `tests/test_long_horizon_bottleneck.py::test_text_argument_surface_renders_and_parses_phrase_variants` |
| Stochastic summary support | Pass | `tests/test_long_horizon_bottleneck.py::test_summarize_stochastic_rows_supports_text_argument_conditions` |
| Modal dry-run budget | Pass | Dry run `ap-EfkXRQLTBairmkcgYZURH0`; 32 L4 cells, conservative timeout cost `$8.63` under `$25.00` |
| Modal L4 text pass | Pass | Modal run `ap-IzaMxGOJyYo0Y3uNaJlcMI`; `text_stochastic_bottleneck` and `text_visible_control` gates pass |

### Allowed Claim

If the text pass clears the inherited stochastic gates, the allowed claim is:
the moved bottleneck survives a parser-facing text argument namespace in this
synthetic long-horizon neural-agent diagnostic. It is not yet a natural-language
agent, production API, or free-form generation result.

### Next Operation

If the text pass succeeds, run a prompt-level LLM or small language-model
transfer where the model emits JSON text directly and the parser sees generated
strings rather than classifier-rendered phrases.
