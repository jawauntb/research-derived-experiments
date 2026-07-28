# Passive Identification Impossibility

**Target claim.** If two hypotheses are equivalent under every observation available to a passive learner, but require different answers on a held-out query, no learner receiving only those passive observations can identify the correct hypothesis with worst-case accuracy above chance over the indistinguishable class.

## Setup

Fix a finite hypothesis set \(H\) and an initial experiment family \(A = G_0\). Let

\[
S = [h]_{\sim_A} = \{ h' \in H : h' \sim_A h \}
\]

be the live equivalence class of the true hypothesis, with \(\lvert S \rvert = m \ge 2\).

Assume the held-out query / label \(Y\) is a function of the true hypothesis and is **not constant** on \(S\): there exist \(h_i, h_j \in S\) with \(Y(h_i) \ne Y(h_j)\). In IDENT v1, \(Y(h) = h\).

A passive learner is any (possibly randomized) map

\[
f : \mathrm{Obs}(A) \to \Delta(\mathcal{Y})
\]

that sees only the transcript of experiments in \(A\).

## Indistinguishability argument

Construct two worlds \(w_i, w_j\) with true hypotheses \(h_i, h_j \in S\).

1. By \(h_i \sim_A h_j\), the observation transcripts under \(A\) are identical: \(\mathrm{Obs}_{w_i}(A) = \mathrm{Obs}_{w_j}(A)\).
2. Therefore any deterministic \(f\) returns the same answer on both worlds.
3. Those worlds have different correct labels, so deterministic \(f\) is wrong on at least one of them.
4. For randomized \(f\), let \(p_y\) be the probability of answering \(y\) on the shared transcript. Worst-case accuracy over \(\{w_i, w_j\}\) is at most \(\max_y p_y \le 1\). Extending to the full class \(S\) with an adversary choosing the true member of \(S\), minimax accuracy is at most \(1/m\) under a uniform prior (or any prior supported on \(S\) after renormalization of the worst atom).

Hence no passive learner can exceed the chance bound \(1/m\) in the worst case over the live class.

## Active sufficiency (benchmark design)

If there exists \(g \in G\) such that observing \(R(h^\star, g)\) leaves a singleton live class, then one intervention identifies \(h^\star\). IDENT v1 generates only items with at least one such one-step identifying separator, so failures are attributable to underdetermination recognition or intervention choice—not to an impossible task.

## Scope

This is a finite, experiment-relative indistinguishability lemma for the benchmark family. It does not claim novelty for the general idea of observational equivalence; it pins the IDENT scoring contract.
