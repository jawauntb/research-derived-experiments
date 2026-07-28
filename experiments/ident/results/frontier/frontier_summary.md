# IDENT frontier model summary (direct OpenAI / Anthropic)

- split: `test`
- n_items: 40
- status: **pass**
- config: Doppler `cofounder/stg_superoptimizers`

## Gates

- PASS: `G5_capability_gap`

## Models

- `oracle`: separator_acc=1.000, final_acc=1.000
- `anthropic:claude-opus-5`: separator_acc=1.000, false_certainty=0.000, post_id=0.575, final_acc=0.575, weakness_regret=0.025
- `openai:gpt-5.6-sol`: separator_acc=1.000, false_certainty=0.000, post_id=0.55, final_acc=0.550, weakness_regret=0.0

## Failure shape

Frontier models (gpt-5.6-sol, claude-opus-5) match oracle separator accuracy with near-zero false certainty, but final identification remains ~0.55–0.58. Stronger models did not close the update-after-evidence gap vs claude-sonnet-4.

