# IDENT OpenRouter model summary

- split: `test`
- n_items: 40 (primary); G7 reshuffle on n=15
- status: **pass**

## Gates

- PASS: `G5_capability_gap`
- PASS: `G7_robustness`

## Models (n=40)

- `oracle`: separator_acc=1.000, final_acc=1.000
- `anthropic/claude-sonnet-4`: separator_acc=1.000, false_certainty=0.050, post_id=0.5789473684210527, final_acc=0.550
- `google/gemini-2.5-flash`: separator_acc=0.800, false_certainty=0.000, post_id=0.25, final_acc=0.225
- `openai/gpt-4o-mini`: separator_acc=0.744, false_certainty=0.025, post_id=0.41379310344827586, final_acc=0.450

## G7 robustness (n=15 reshuffle)

- `anthropic/claude-sonnet-4`: sep=0.929, delta=0.0714285714285714, pass=True
- `openai/gpt-4o-mini`: sep=0.533, delta=0.06666666666666665, pass=True

## Failure shape

Models usually intervene (low false-certainty). Gap vs oracle is mainly post-intervention identification and, for weaker models, separator choice. Claude matches oracle separator accuracy on the n=40 slice but final ID remains ~0.55.

