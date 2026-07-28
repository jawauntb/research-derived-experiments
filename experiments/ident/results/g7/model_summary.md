# IDENT OpenRouter model summary

- split: `test`
- n_items: 15
- status: **pass**

## Gates

- PASS: `G5_capability_gap`
- PASS: `G7_robustness`

## Models

- `oracle`: separator_acc=1.000, final_acc=1.000
- `anthropic/claude-sonnet-4`: separator_acc=0.929, false_certainty=0.067, weakness_regret=0.017857142857142856, final_acc=0.667, robust_delta=0.0714285714285714
- `openai/gpt-4o-mini`: separator_acc=0.533, false_certainty=0.000, weakness_regret=0.13333333333333333, final_acc=0.600, robust_delta=0.06666666666666665
