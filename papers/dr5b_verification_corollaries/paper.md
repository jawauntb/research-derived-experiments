# DR5b: Where the Wall Shows Up — Verification Corollaries

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Deletion-Repair — DR5b (corollary paper)
**Date:** 2026-07-27

---

## Abstract

DR5 established a structural limit: a proposition-ranking nominator $N$
cannot distinguish a commitment $D$ from any specific realisation $r_i$
when $D$ admits more than one non-equivalent surface form; escape
requires importing an external grouping function $g$; and when $g$ is
inherited from a matcher, the projection-vs-genuine-signal ambiguity is
inherited too. The DCR arc supplied ground truth (Einstein's 1905
deletion) for exactly one such $D$ (absolute simultaneity) in exactly
one corpus (pre-1905 electrodynamics).

DR5b enumerates four concrete verification settings outside the DCR arc
where the theorem operates, with worked examples of the wall in each.
It also gives specific guidance for verifier designers who want to check
whether their protocol is above or below the DR5 wall for their specific
target.

The claim is not that verification is impossible for multi-realisation
targets. It is that the standard placebo-based test — *"our checker
fires on this positive case; it does not fire on this control; therefore
our checker works"* — is *insufficient* whenever the target admits
multiple non-equivalent surface forms. Something stronger is required,
and DR5 says exactly what.

---

## 1. Recap: what DR5 says, in one paragraph

Let $D$ be a target commitment with realisations $\{r_1, \dots, r_k\}
\subseteq C$ in a corpus $C$. Let $N: C \to \mathbb{R}$ be a
proposition-ranking scoring function: $N(p)$ depends only on $p$, not on
any subset structure over $C$. Then $N$ produces $k$ distinct scores
$\{N(r_i)\}$ that cannot be aggregated into a single "score for $D$"
without importing an external grouping function $g$ that identifies the
realisation set. Once $g$ is imported, the ranking is class-based, not
proposition-based, and the correctness of $g$ (soundness + completeness
for $D$) becomes the load-bearing question.

The wall shows up as follows: a matcher tuned to catch $r_i$ misses
$r_j$ ($j \neq i$); a matcher wide enough to catch all $r_j$ overfires
on the placebo; there is no calibration that resolves both without an
external $g$.

## 2. Corollary 1 — Code correctness

**Setting.** A verifier checks whether an implementation satisfies a
specification. The specification $D$ is what the code should do; the
implementation $p$ is a specific source-code artifact. A
proposition-ranking verifier scores $p$ against $D$ independently of
other implementations.

**Where $D$ becomes multi-realisation.**

Consider $D$ = *"the code assumes 0-based indexing throughout."* Surface
realisations of this commitment in Python include:

- `for i in range(len(xs)): ...`
- `for i, x in enumerate(xs): ... use i ...`
- `xs[0]` as the first element
- Slicing `xs[i:i+n]` with the convention `i` starts at 0
- Comments like `"# 0-indexed"`

An implementation might embody $D$ in one of these forms; a different
implementation of the same functional spec might embody it in another.
A verifier prompted with "*does this code assume 0-based indexing?*"
without an explicit grouping function will either:

- **Match only one surface form** — e.g., only firing on `xs[0]` — and
  miss the others; or
- **Match all forms** with a wider pattern that also fires on 1-based
  code that happens to have `xs[0]` in a different logical position.

**Where the placebo fails.** A placebo (1-based indexing) can look
identical at the surface level in short snippets. Verifiers that check
by lexical matching (`xs[0]` appears) will fire on placebos where `xs[0]`
is an aliased sentinel value rather than a first-element access. DR5 §5
says this is not a bug in the verifier — it is the wall.

**Practical guidance.** If the code-correctness target admits multiple
surface realisations, do not rely on placebo-based verification of a
proposition-independent scorer. Either supply an explicit $g$ (a
specification-derived AST rewrite that canonicalises all realisations to
one form before scoring), or accept that the verifier operates *above*
the DR5 wall only when the target has a canonical form.

## 3. Corollary 2 — LLM reasoning verification

**Setting.** An oracle checks whether a language model's reasoning trace
supports its conclusion. The oracle scores each step independently.
$D$ is *"the model's answer is derived from valid reasoning steps."*

**Where $D$ becomes multi-realisation.** Valid reasoning has many
surface forms. For a math problem, the model might:

- Derive the answer symbolically (substitutions, algebraic
  manipulations)
- Derive it numerically (guess-and-check, tabulation)
- Derive it geometrically (a diagram, an area argument)
- Derive it by analogy to a solved instance
- Derive it by verification (checking the answer's properties)

Each is a distinct realisation of the same commitment (*valid
derivation*). A verifier prompted with *"is this reasoning valid?"* will
be trained on some surface distribution and will overfire or underfire
on distributions it has not seen. Adversarial reasoning generation —
producing plausible-looking but invalid reasoning that matches the
verifier's surface distribution — is exactly what DR5 predicts is
possible when the verifier is proposition-independent.

**Where the placebo fails.** A placebo of "obviously wrong reasoning"
tests only the class of wrong-reasoning surface forms the placebo
designer imagined. Adversarial wrong-reasoning that mimics the surface
form of valid reasoning will pass the verifier. This is the same wall
as the DCR1f Maxwell hit: the "placebo was invalid" reading
(realisations of $D$ we did not anticipate at the placebo cut) is
formally indistinguishable from the "verifier is projecting" reading
without an external $g$ for "valid reasoning."

**Practical guidance.** If step-independence is a defining property of
the verifier (as it typically is for cheap LLM judges), do not use its
placebo-vs-positive delta as the correctness signal. Supply an
independent structural check ($g$) — a proof checker, a symbolic
executor, a constraint solver — and score the LLM against $g$'s
output rather than treating the LLM as $g$ itself.

## 4. Corollary 3 — Retrieval-augmented factual grounding

**Setting.** An LLM generates a claim; a citation is attached; a
verifier checks whether the citation supports the claim. $D$ is
*"the cited source establishes the claim."*

**Where $D$ becomes multi-realisation.** A citation "supports" a claim
in many surface forms:

- Direct assertion: *"X is true."*
- Definitional: the citation *defines* X such that the claim is trivial.
- Implicit: the citation asserts $Y$ where $Y$ presupposes $X$.
- Deductive: the citation asserts premises from which $X$ follows.
- Statistical: the citation reports data consistent with $X$.

A verifier prompted with *"does the citation support the claim?"* will
train on some subset of these surface forms and miss others. Both
false positives (citation surface-matches but does not actually support)
and false negatives (citation supports but not in a form the verifier
recognises) follow directly from DR5.

**Where the placebo fails.** A placebo of "citation clearly unrelated
to claim" tests only unrelated citations, not citations that
surface-match but do not actually support. The DR5 wall predicts that
adversarial retrieval — retrieving citations that surface-match the
claim's vocabulary without supporting it — will pass proposition-
independent verifiers.

**Practical guidance.** Do not treat citation quality as a
proposition-level scoring problem. Impose a structural check: does the
citation's content, under some canonical semantic form, entail the
claim? This is exactly the $g$ DR5 requires. Absent it, the verifier
is above the wall only for the surface forms it happens to have seen.

## 5. Corollary 4 — Latent goal identification

**Setting.** An observer watches an agent take actions and tries to
identify the agent's goal. $D$ is the goal; each action $a_i$ is a
proposition-analogue; a verifier scores each action against $D$
independently.

**Where $D$ becomes multi-realisation.** A goal admits multiple action
realisations trivially: any goal that can be achieved by more than one
sequence of actions has multiple realisations. In practice:

- Goal = *"navigate to the kitchen."*
- Realisation 1: walk directly.
- Realisation 2: walk to the living room first, then kitchen.
- Realisation 3: pretend not to be going to the kitchen, then arrive
  there.

Realisation 3 is adversarial. A verifier that checks per-action
plausibility against $D$ will judge each of Realisation 3's actions
individually plausible (or implausibly, depending on the surface form),
and will not aggregate them into the goal-recognition question.

**Where the placebo fails.** A placebo of "agent doing something else"
tests only obvious alternatives, not adversarial realisations of the
target goal. DR5 predicts that any agent whose action distribution
partially overlaps the goal's realisation set will fool a proposition-
independent verifier.

**Practical guidance.** Goal recognition is inherently a class-level
problem, not an action-level problem. Trying to build a per-action
goal-detector without an explicit goal-representation $g$ is above the
DR5 wall only for goals with canonical action forms.

## 6. What DR5b does not claim

- **It does not claim these corollaries are proved.** DR5 is a
  theorem; DR5b enumerates settings where the theorem operates. Each
  corollary is stated as an application, not as a separate theorem.
- **It does not claim verification is impossible for
  multi-realisation targets.** It claims that proposition-independent
  scoring is insufficient. Class-aware nomination (with a sound $g$) is
  the escape route DR5 identifies.
- **It does not identify the correct $g$ for any specific domain.**
  That is per-domain work. The best DR5 can offer is: know that you
  need $g$, and know what "sound and complete for $D$" means for your
  specific $D$.
- **It does not attempt empirical demonstration.** DR6 (planned but not
  attempted) would run a concrete controlled experiment in one of these
  domains and report where the wall appears.

## 7. Practical guidance for verifier designers

Six specific questions that determine whether your verification protocol
is above or below the DR5 wall for your specific target $D$:

1. **Does $D$ admit multiple non-equivalent surface forms in your
   corpus?** If yes, DR5 applies. If no, standard placebo-based
   verification is above the wall.
2. **Is your scoring function $N$ proposition-independent?** ($N(p)$
   depends only on $p$, not on other propositions or an external group
   structure.) If yes, DR5 applies to $N$.
3. **What is your grouping function $g$?** If you do not have an
   explicit $g$, then your protocol is doing implicit grouping —
   somewhere your pipeline is deciding *which* propositions belong to
   the target class before scoring. Find that step; treat it as $g$;
   audit it for soundness and completeness.
4. **Does your placebo distinguish "your verifier projects on the
   placebo" from "the placebo is not clean for $D$"?** If not, DR5 §5
   applies: the ambiguity is irreducible in your protocol.
5. **Is $g$ derived from the same signal as $N$?** If yes, you have
   Spencer's candidate-selection circularity at the class level; the
   wall re-appears one level up.
6. **Is the wall you are hitting a calibration problem or a
   structural problem?** A calibration problem is fixable by tuning
   $N$; a structural problem requires importing $g$ or restating the
   question. DCR1f showed how to distinguish: if narrowing $N$ to fix
   one problem worsens another (precision-recall tradeoff over the
   held-out register), the wall is structural, not calibratable.

## 8. Where the arc goes from here

DR5 established the theorem. DR5b lists corollaries. Two named
next-steps that would advance the framework meaningfully:

- **DR6 — empirical corollary.** Run a controlled experiment in one of
  the four domains above (code correctness is the tractable candidate)
  and report whether the wall appears as DR5 predicts. This would move
  DR5 from "theorem with one worked instance" to "theorem with
  independent empirical corroboration."
- **DR7 — grouping function correctness.** Study when $g$ can be
  constructed *soundly* for a specific $D$. What structural properties
  must the extractor have? Can $g$ be learned? Under what conditions
  does the DCR1e-style "presupposition-inferring extractor implicitly
  defines $g$" observation generalise?

Neither is trivial. Both are follow-ups DR5 opens rather than closes.

---

## Appendix: reproduction

DR5b is a paper-only artifact. It does not add code or run experiments.
The DCR arc's empirical corroboration reproduces via each paper's
`run_dcr1*.py` and `run_dcr2a.py`. All prior verdicts unchanged.
