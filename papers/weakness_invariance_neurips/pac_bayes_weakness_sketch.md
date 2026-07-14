# A Finite PAC-Bayes Bridge for Weakness

Status: analytic sketch, not an empirical PAC-Bayes result.

## Current frame

Weakness \(W_G(h)\) counts the transformations in a fixed candidate family \(G\)
with which a hypothesis \(h\) is compatible. The empirical program currently
treats this as a function-level selector for missing-orbit transport. The
PAC-Bayes bridge below gives a narrower complexity interpretation: if the
transformation family and its prior are fixed independently of the evaluation
sample, then compatibility can locate \(h\) inside a smaller, symmetry-indexed
hypothesis class. A prior that allocates mass to that class can therefore assign
\(h\) a smaller description/KL penalty.

This is not the claim that a large raw compatibility count automatically lowers
parameter-space KL, nor that it guarantees low OOD risk.

## Setup

Let:

- \(H\) be a finite hypothesis class;
- \(G\) be a finite transformation family fixed before observing the sample;
- \(W_G(h)\in\{1,\ldots,|G|\}\) be the repository's compatibility count;
- \(H_{\ge k}=\{h\in H:W_G(h)\ge k\}\);
- \(S\sim D^m\) be an IID sample;
- \(\ell(h,z)\in[0,1]\);
- \(\widehat L_S(Q)\) and \(L_D(Q)\) be posterior-averaged empirical and
  population risks.

Let \(K=\{k:H_{\ge k}\ne\varnothing\}\). Choose a data-independent mixture
prior

$$
P=\sum_{k\in K}\pi_k U_k,
$$

where \(\pi_k>0\), \(\sum_{k\in K}\pi_k=1\), and \(U_k\) is uniform on
\(H_{\ge k}\). Overlap between the nested classes is intentional.

The Langford-Seeger-Maurer PAC-Bayes-kl inequality states that, with probability
at least \(1-\delta\) over \(S\), for \(m\ge8\), \(\delta\in(0,1)\), and
simultaneously for all posteriors \(Q\),

$$
\operatorname{kl}\!\left(\widehat L_S(Q)\,\middle\|\,L_D(Q)\right)
\le
\frac{\operatorname{KL}(Q\|P)+\ln(2\sqrt m/\delta)}{m}.
$$

## Proposition: compatibility-indexed KL certificate

For a deterministic posterior \(Q=\delta_h\) and any
\(k\le W_G(h)\),

$$
\operatorname{KL}(\delta_h\|P)
=-\ln P(h)
\le \ln |H_{\ge k}|-\ln\pi_k.
$$

In particular, choosing \(k=W_G(h)\) yields

$$
\operatorname{KL}(\delta_h\|P)
\le
\ln |H_{\ge W_G(h)}|-\ln\pi_{W_G(h)}.
$$

Proof: because \(h\in H_{\ge k}\), the \(k\)-th mixture component contributes
\(\pi_k/|H_{\ge k}|\) to \(P(h)\). Thus
\(P(h)\ge\pi_k/|H_{\ge k}|\); applying \(-\ln\) gives the result.

For this particular overlapping mixture, the exact mass is

$$
P(h)=
\sum_{\substack{k\in K\\k\le W_G(h)}}
\frac{\pi_k}{|H_{\ge k}|}.
$$

It is therefore monotone in \(W_G(h)\): greater weakness adds positive prior
mass and lowers the exact deterministic KL. That monotonicity is designed into
this prior and is not independent evidence for weakness. The class
cardinalities determine the magnitude of the added mass, while the
\(\pi_k\) encode how much pre-sample belief is allocated to each compatibility
level. The single-component expression above is a convenient upper
certificate, not the exact mixture ranking; skewed weights can reverse those
single-component certificates without reversing the exact KL.

## Narrower fixed-action orbit-count special case

An exact count is available for a stricter notion than the repository's
weakness. Let a finite group \(G\) act on \(X\), fix one homomorphism
\(\rho:G\to\operatorname{Sym}(Y)\), and define

$$
H_{\mathrm{eq}}=
\{h:X\to Y:h(gx)=\rho(g)h(x)\ \forall g,x\}.
$$

Choose one representative \(x_j\) from each input orbit. An equivariant
hypothesis is determined by its value on the representatives, and the value at
\(x_j\) must be fixed by \(\rho(\operatorname{Stab}(x_j))\). Therefore

$$
|H_{\mathrm{eq}}|
=
\prod_j
\left|\operatorname{Fix}_Y\!\left(
\rho(\operatorname{Stab}(x_j))
\right)\right|
\le |Y|^r,
$$

where \(r\) is the number of input orbits. The unrestricted function class has
\(|Y|^{|X|}\) members. Suppose \(H_{\mathrm{eq}}\ne\varnothing\). Under a
hierarchical prior that assigns masses \(\pi_{\mathrm{eq}}\) and
\(\pi_{\mathrm{all}}\) to the equivariant and unrestricted components, the
available log-cardinality saving is at least

$$
(|X|-r)\ln |Y|
-\ln\frac{\pi_{\mathrm{all}}}{\pi_{\mathrm{eq}}},
$$

with a potentially larger saving when stabilizers restrict representative
labels. This is the precise sense in which orbit tying can reduce a
PAC-Bayes/description-length term.

This formula does **not** count \(H_{\ge |G|}\) for the repository definition.
Repository weakness existentially permits an output action separately for each
input transformation, whereas \(H_{\mathrm{eq}}\) fixes one coherent
homomorphism \(\rho\). Counting the repository level set requires the union over
all admissible output-action assignments and correction for overlaps. The
fixed-action result is therefore a limiting case and a diagnostic target, not a
proof that the observed weakness count already has the \(|Y|^r\) cardinality.

## Assumption ledger

1. **Prior independence.** \(G\), the thresholds, mixture weights, and class
   construction are fixed independently of \(S\). If \(G\) is inferred from the
   same data, use a held-out split, a hyperprior over candidate groups, or a
   valid data-dependent-prior theorem.
2. **IID and bounded loss.** The displayed PAC-Bayes-kl bound assumes IID draws
   and loss in \([0,1]\). Group-generated OOD deployment is not automatically
   the same distribution \(D\).
3. **Finite measurable classes.** The counting proof is finite. Neural
   parameter posteriors require a continuous prior/posterior and cannot inherit
   the count by analogy.
4. **Compatibility is class membership.** High \(W_G\) helps only when
   \(|H_{\ge k}|\) actually shrinks. A huge or uninformative \(G\) can leave many
   wrong hypotheses in every high-\(k\) class.
5. **Posterior choice.** The deterministic posterior gives a transparent Occam
   certificate. Practical neural PAC-Bayes bounds usually use stochastic
   posteriors and must also control empirical perturbation risk.
6. **Risk alignment.** A tighter complexity term does not compensate for worse
   empirical risk, and an IID bound does not prove transport to an arbitrary
   shifted distribution.

## Anomaly map and candidate reframes

- **Too-small \(G\):** weakness ties many hypotheses. Reframe: the relevant
  explanatory quantity is the prior mass and class-size profile, not \(k\)
  alone.
- **Too-large or misaligned \(G\):** wrong hypotheses can remain highly
  compatible. Reframe: symmetry must be synchronized with the deployment
  mechanism.
- **Data-inferred \(G\):** a posterior-looking group cannot be smuggled into the
  prior. Reframe: charge for group selection through a hyperprior or isolate it
  on a separate sample.
- **Neural flatness:** function-level orbit tying does not imply a broad basin
  in a chosen parameterization. Reframe: compare function-space symmetry priors
  with perturbation PAC-Bayes bounds rather than equating them.

## Discriminating predictions

The proposed explanation predicts more than the mixture's built-in monotonic
relation between \(W_G\) and deterministic KL:

1. Exact enumeration must recover
   \(P(h)=\sum_{k\le W_G(h)}\pi_k/|H_{\ge k}|\); failure kills the derivation's
   implementation.
2. Across predeclared groups with comparable raw weakness, smaller
   compatibility classes should yield larger prior mass contributions, while
   OOD ranking should agree only for deployment-aligned groups.
3. Charging a hyperprior for selecting among many candidate groups should erase
   gains that arise only from post-hoc group search.
4. Exact orbit tying should produce a complexity reduction proportional to the
   number of eliminated free orbit decisions, \(|X|-r\), after accounting for
   the class-prior penalty.

## Severe experiment and kill criteria

Pre-register a finite symbolic tournament before inspecting outcomes:

1. Before drawing any sample, freeze one reduced domain per family with
   \(|X|=|Y|\le7\), and fix the ambient class \(H=Y^X\). The largest full class
   is then \(7^7=823{,}543\), permitting exact CPU enumeration. Training
   consistency may select a posterior but may not redefine the prior support.
2. Freeze aligned, wrong-group, incomplete-group, and random-group candidates
   plus a uniform hyperprior over them.
3. Declare a separate IID lane with \(m\ge8\) draws from a fixed distribution
   \(D\). Compute exact mixture mass, deterministic PAC-Bayes-kl certificates,
   and population risk under that same \(D\).
4. Evaluate the existing biased prefix/coset split only as a separate
   group-generated OOD lane. Do not call that risk IID or use the displayed
   theorem to certify it.
5. Compare paired rankings among hypotheses with equal training error and use
   family/seed as the sampling unit.

Kill the proposed explanatory bridge if any of the following occurs:

- the exact class counts or fixed-action limiting count contradict the proposed
  compression mechanism;
- the IID certificate is vacuous on the preregistered finite lane;
- after paying the frozen group-selection penalty, certificate ranking adds no
  information beyond the prior's encoded weakness ordering;
- wrong/random groups receive equally tight certificates while failing OOD
  transport, killing the proposed OOD explanation (but not the IID theorem);
- conclusions about certificate magnitude depend primarily on arbitrary
  threshold-mixture weights;
- the finite result cannot be transported to a stochastic neural posterior
  without a vacuous bound or a new unregistered assumption.

## Claim boundary and next best test

Current claim strength: **analytic, conditional**. The derivation proves that
symmetry compatibility can lower a finite PAC-Bayes complexity certificate
through smaller prior-supported classes. It does not show that the repository's
existing weakness scores already produce tighter numerical bounds, that neural
weakness reduces parameter-space KL, or that PAC-Bayes explains the observed OOD
results.

The next best test is the fully enumerated symbolic tournament above. It is
CPU-only, exposes every class cardinality exactly, and can kill the bridge before
any neural perturbation study is attempted.

## References

- Langford, J. and Seeger, M. *Bounds for Averaging Classifiers.* CMU-CS-01-102
  (2001).
- Seeger, M. *PAC-Bayesian Generalisation Error Bounds for Gaussian Process
  Classification.* JMLR 3 (2002).
- Maurer, A. *A Note on the PAC Bayesian Theorem.* arXiv:cs/0411099 (2004).
- Dziugaite, G. K. and Roy, D. M. *Computing Nonvacuous Generalization Bounds
  for Deep (Stochastic) Neural Networks with Many More Parameters than Training
  Data.* UAI (2017).
- Lyle, C., van der Wilk, M., Kwiatkowska, M., Gal, Y., and Bloem-Reddy, B.
  *On the Benefits of Invariance in Neural Networks.* arXiv:2005.00178 (2020).
- Beck, A. and Ochs, P. *Symmetries in PAC-Bayesian Learning.*
  arXiv:2510.17303 (2025).
