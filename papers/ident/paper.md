# Prediction Is Not Identification

A minimal benchmark for choosing the experiment that matters

**Jawaun Brown**  
Human director; experiment code and drafts generated under review  
2026-07-27 · IDENT v1

---

## Abstract

Observational prediction can be perfect while mechanism identification remains impossible. We introduce **IDENT**, a one-shot benchmark where two or more hidden mechanisms are indistinguishable under a supplied observation set, yet at least one permitted intervention separates them. We prove a finite passive-identification impossibility bound, ship a deterministic generator with exact separator annotations across three symbolic domains, and evaluate trivial baselines plus frontier models under a frozen one-intervention protocol. Construction gates pass. An oracle weakest identifying separator reaches 100% final identification. Strong models usually intervene rather than bluff, but final identification remains far below oracle—even when separator choice is perfect—revealing a residual failure in update-after-evidence.

## 1. Claim and scope

**Operational claim.** There exist tasks on which a passive learner cannot exceed chance at naming the true mechanism, while a single cheap intervention identifies it exactly.

IDENT is intentionally narrow. It is not a general theory of intelligence, a transformer training run, or a natural-language science suite. The contribution succeeds only if three pieces land together:

1. a formal impossibility result for passive learners on the benchmark family;
2. a compact generator with known latent mechanisms and exact separators;
3. an evaluation showing whether models recognize underdetermination and choose (then use) the right experiment.

## 2. Minimal theory

### 2.1 Objects

- Finite hypothesis set \(H=\{h_1,\ldots,h_k\}\).
- Experiment set \(G\) with costs \(c(g)\ge 0\).
- Response function \(R(h,g)\).
- Initial passive family \(G_0\subset G\).

### 2.2 Experiment-relative equivalence

For \(A\subseteq G\),

\[
h_i\sim_A h_j \iff R(h_i,g)=R(h_j,g)\ \text{for all }g\in A.
\]

The live class \(S=[h^\star]_{\sim_{G_0}}\) is the set of mechanisms still compatible with all passive observations.

### 2.3 Weakest identifying separator

Intervention \(g\) **separates** \(S\) when outcomes \(\{R(h,g):h\in S\}\) are not unique. It **identifies** \(h^\star\) when observing \(R(h^\star,g)\) leaves a singleton live class. IDENT annotates minimum-cost identifying separators.

### 2.4 Passive identification impossibility

**Theorem (benchmark form).** If \(|S|=m\ge 2\) and the held-out label is non-constant on \(S\), then no learner receiving only the passive transcript can exceed worst-case accuracy \(1/m\) at recovering the true hypothesis.

**Proof sketch.** Any two members of \(S\) induce identical passive transcripts. A deterministic map returns one answer on that transcript and is therefore wrong on at least one world. A randomized map has minimax accuracy at most \(1/m\) against an adversary choosing the true member of \(S\). □

The combinatorial core is Lean (`formal/structural-intelligence/StructuralIntelligence/IdentImpossibility.lean`, SafeVerify 2026-08-18): a transcript map cannot hit two distinct hypotheses that share a record, and on a duplicate-free constant-record list the hit count is at most one. Model scores stay Python.

**Active sufficiency.** IDENT v1 generates only items with at least one one-step identifying separator, so failure is not caused by an impossible task.

## 3. Benchmark

### 3.1 Task interface

Each item supplies prior observations, a hypothesis menu, and candidate interventions with costs. The model may answer immediately or spend exactly one intervention, receive the outcome, then answer.

### 3.2 Domains

| Domain | Latent object | Passive masking |
|---|---|---|
| `boolean_causal` | two-input Boolean mechanisms | agree on an observed input support |
| `finite_state` | tiny acceptors over \(\{0,1\}^{\le 3}\) | agree on observed traces |
| `small_programs` | integer functions | agree on supplied test inputs |

Every item includes a wasteful “more of the same” distractor that cannot separate the live class.

### 3.3 Dataset

Deterministic seed `20260727` yields 1000 items: train 700 / dev 150 / test 150. Validators enforce live-class size \(\ge 2\), existence of an identifying separator, exact minimum-separator annotations, passive chance bounds, and basic leak checks.

### 3.4 Metrics

Separator accuracy, weakness regret, false-certainty rate, post-intervention identification, final accuracy, and efficiency (identification gain / cost).

## 4. Pre-registered gates

| Gate | Result |
|---|---|
| G1 Formal ambiguity | PASS |
| G2 Separability / active sufficiency | PASS |
| G3 Passive bound (answer-now ≤ chance + Hoeffding slack) | PASS |
| G4 Oracle solvability (≥99% final ID) | PASS (100%) |
| G5 Capability gap vs oracle | PASS |
| G6 EIG nontriviality | PASS |
| G7 Label/order robustness | PASS |

## 5. Results

### 5.1 Baselines (full test, n=150)

| Baseline | Separator | False certainty | Final acc |
|---|---:|---:|---:|
| answer_now | 0.00 | 1.00 | 0.50 |
| random_intervention | 0.55 | 0.00 | 0.69 |
| max_output_variance | 1.00 | 0.00 | 0.92 |
| expected_information_gain | 1.00 | 0.00 | 0.93 |
| oracle_weakest_separator | 1.00 | 0.00 | 1.00 |

Answer-now is maximally falsely certain and remains near chance. Exact information gain already selects separators on this symbolic menu; IDENT is therefore a measurement instrument, not a claim of a new IG principle.

### 5.2 Frontier models via OpenRouter (test slice, n=40)

Frozen protocol; temperature 0; one permitted intervention.

| System | Separator | False certainty | Post-intervention ID | Final acc |
|---|---:|---:|---:|---:|
| oracle | 1.00 | 0.00 | 1.00 | 1.00 |
| anthropic/claude-sonnet-4 | 1.00 | 0.05 | 0.58 | 0.55 |
| openai/gpt-4o-mini | 0.74 | 0.03 | 0.41 | 0.45 |
| google/gemini-2.5-flash | 0.80 | 0.00 | 0.25 | 0.23 |

G7 reshuffle (n=15) leaves separator accuracy within 0.07 for Claude and GPT-4o-mini.

### 5.3 Frontier scale-up (direct APIs, n=40)

Same frozen protocol via Doppler `cofounder/stg_superoptimizers` (`openai:gpt-5.6-sol`, `anthropic:claude-opus-5`).

| System | Separator | False certainty | Post-intervention ID | Final acc |
|---|---:|---:|---:|---:|
| oracle | 1.00 | 0.00 | 1.00 | 1.00 |
| openai/gpt-5.6-sol | 1.00 | 0.00 | 0.55 | 0.55 |
| anthropic/claude-opus-5 | 1.00 | 0.00 | 0.58 | 0.58 |

Frontier models close the separator-choice gap (both 1.00, near-zero weakness regret) but **do not** close final identification. Result is essentially unchanged from Claude Sonnet 4 on final ID. G5 still passes once final/post-intervention accuracy is treated as a first-class gap (not only separator accuracy).

### 5.4 Failure shape

Models usually intervene. At mid-tier strength the gap mixes separator errors and update failures; at frontier strength the residual collapses to **update-after-evidence**: perfect or near-perfect separator choice with final identification stuck near 0.55–0.58. Expanding surface complexity is not required to preserve a publishable gap.

## 6. What this does not show

- That experiment-relative equivalence is a new concept.
- That information gain is a new learning principle.
- That model failure proves absence of “understanding.”
- That the result transports to natural-language science wrappers without further leak tests.

## 7. Reproduce

```bash
python3 -m experiments.ident.experiment
python3 -m pytest tests/test_ident.py -q
doppler run --project cofounder --config dev -- \
  python3 -m experiments.ident.eval.run_models --limit 40 --no-robustness
```

Package: `experiments/ident/`. Paper source: `papers/ident/paper.md`.

## 8. Conclusion

IDENT makes one missing capability hard to ignore: sounding certain—or even requesting an experiment—is not the same as identifying a mechanism. Passive prediction is provably bounded on the live equivalence class; the correct one-step separator is exactly known; and current strong models leave a reproducible gap between intervention and identification.
