# IDENT Definitions

Working objects for the one-shot identification benchmark.

## Hypothesis

A finite set \(H = \{h_1, \ldots, h_k\}\). Each \(h \in H\) is a complete hidden mechanism.

## Experiments and responses

- Observation / intervention set \(G\).
- Response function \(R(h, g)\) returning the observation produced by hypothesis \(h\) under experiment \(g\).
- Initial experiment set \(G_0\) (passive observation in v1).
- Cost \(c(g) \ge 0\).

## Experiment-relative equivalence

For any experiment family \(A \subseteq G\),

\[
h_i \sim_A h_j \iff R(h_i, g) = R(h_j, g)\ \text{for every}\ g \in A.
\]

The quotient \(H / {\sim_A}\) is the set of hypotheses still indistinguishable after experiments in \(A\).

## Separating interventions

\[
\mathrm{Sep}(h_i, h_j) = \{ g \in G : R(h_i, g) \ne R(h_j, g) \}.
\]

For a live class \(S \subseteq H\), intervention \(g\) **separates** \(S\) when
\(\lvert\{ R(h, g) : h \in S \}\rvert > 1\).

## Weakest separator

\[
g^\*(h_i, h_j) \in \arg\min_{g \in \mathrm{Sep}(h_i,h_j)} c(g).
\]

In the implemented benchmark, `minimum_separators` are the minimum-cost interventions that both separate the live class and uniquely identify the true hypothesis after one outcome (active sufficiency for one-shot v1).

## Passive chance bound

Under a uniform prior over a live equivalence class of size \(m\), no passive learner can exceed worst-case accuracy \(1/m\) at naming the true hypothesis.
