# IDENT

One-shot benchmark for the smallest experiment that separates **prediction** from **mechanism identification**.

Observationally indistinguishable hidden mechanisms produce identical passive data. A successful agent must notice the underdetermination and request the weakest intervention that splits the live equivalence class.

Suggested paper title: *Prediction Is Not Identification: A Minimal Benchmark for Choosing the Experiment That Matters*.

## Package layout

```text
experiments/ident/
├── theory/                 # definitions + impossibility note
├── domains/                # boolean_causal, finite_state, small_programs
├── eval/                   # baselines, model protocol, runner, reports
├── splits/                 # fixed train/dev/test jsonl
├── results/                # public-safe baseline summary
├── schemas.py, actions.py, equivalence.py, separators.py, …
├── generation.py / validation.py / scoring.py
└── experiment.py           # regenerate + run baselines
```

## Reproduce

From the repository root:

```bash
# Generate 1000 items (700/150/150) and evaluate trivial baselines + oracle
python3 -m experiments.ident.experiment

# Or step-wise:
python3 -m experiments.ident.generation
python3 -m experiments.ident.eval.runner --split test
```

Tests:

```bash
python3 -m pytest tests/test_ident.py -q
```

## Model protocol

Strict one-tool JSON protocol (see `eval/model_adapters.py`). The model may answer immediately or spend exactly one menu intervention, then answer. Score structured fields only.

### OpenRouter eval

```bash
doppler run --project cofounder --config dev -- \
  python3 -m experiments.ident.eval.run_models \
  --models openai/gpt-4o-mini anthropic/claude-sonnet-4 google/gemini-2.5-flash \
  --limit 40 --no-robustness
```

Public summary: `results/model_summary.json`. Raw transcripts: `artifacts/ident/` (gitignored).

## Pre-registered gates

| Gate | Pass condition |
|---|---|
| G1 Formal ambiguity | Every item has live class size ≥ 2 |
| G2 Separability | Every item has ≥ 1 one-step separator |
| G3 Passive bound | Answer-now accuracy ≤ chance + slack |
| G4 Oracle solvability | Weakest identifying oracle ≥ 99% final ID |
| G5 Capability gap | (model eval) ≥1 strong model materially below oracle |
| G6 Nontriviality | EIG does not fully saturate every variant |
| G7 Robustness | (model eval) survives name/order/template randomization |

G1–G4 and G6 are checked by the local baseline suite. G5/G7 require frontier model transcripts.

## What this is not

Not a general theory of intelligence, not MIDAS integration, not a transformer training run, and not a natural-language science wrapper until the symbolic leak tests pass.
