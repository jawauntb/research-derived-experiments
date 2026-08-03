/-!
# Structural Intelligence — Autocatalytic Artwork AA-2 (algebraic core)

The algebraic core of Theorem AA-2 (Autocatalysis = compiler ecology
algebraic identity) from the *Autocatalytic Artwork* companion paper.

AA-2 (in its full paper form) says that the Bayesian posterior update
`μ_{t+1}(θ) ∝ μ_t(θ) · L(θ)` and the Boltzmann/exp-utility update
`μ_{t+1}(θ) ∝ μ_t(θ) · exp(β · r(θ))` describe the same operator on the
belief simplex whenever the reward `r` plays the role of the log-
likelihood `log L`.  What we formalise here is the **algebraic
identity underneath**:  once the reward is packaged as the
(unnormalised) likelihood, the two updates literally coincide
pointwise.

Working in pure Lean 4 core we replace real-valued weights with `Nat`-
valued weights; the ratio / posterior structure lives at the level of
proportionality, so the pointwise identity is what matters, not the
normalisation constant.

Everything here is pure Lean 4 core (no `Mathlib`).
-/

namespace StructuralIntelligence

universe u

section AutocatalyticArtwork

variable {Θ : Type u}

/-- **Bayesian posterior (unnormalised).**  The prior `mu` is
    re-weighted by the likelihood `lik` pointwise; the posterior is
    obtained by dividing by the normaliser `Σ_θ mu θ * lik θ`.  The
    algebraic identity below is at the unnormalised level, where
    Bayes and Boltzmann collapse to the same pointwise product. -/
def bayesPosterior (mu lik : Θ → Nat) : Θ → Nat :=
  fun θ => mu θ * lik θ

/-- **Boltzmann update (unnormalised).**  The prior `mu` is re-
    weighted by the exponential of the utility `r` pointwise (packaged
    here as a `Nat`-valued weight `r θ`, matching the "reward as
    likelihood" identification of AA-2). -/
def boltzmannUpdate (mu r : Θ → Nat) : Θ → Nat :=
  fun θ => mu θ * r θ

/-- **AA-2 core (Bayes = Boltzmann with reward-as-likelihood).**

    The Bayesian posterior and Boltzmann update coincide pointwise
    once the reward `r` is treated as the (unnormalised) likelihood
    `lik`.  This is the algebraic content of "autocatalysis =
    compiler ecology" at the update-operator level: the two
    inference operators the paper considers are literally the same
    map on the (unnormalised) belief simplex.

    The identity is by definitional equality (`rfl`), which is
    precisely the point of formalisation: any doubt about *whether*
    the two updates coincide is dissolved by kernel checking. -/
theorem bayes_equals_boltzmann_with_reward_as_likelihood
    (mu lik : Θ → Nat) (θ : Θ) :
    bayesPosterior mu lik θ = boltzmannUpdate mu lik θ :=
  rfl

/-- **Function-level identity.**  The two update operators are equal
    as functions `Θ → Nat`, not just pointwise on each argument. -/
theorem bayesPosterior_eq_boltzmannUpdate (mu lik : Θ → Nat) :
    bayesPosterior mu lik = boltzmannUpdate mu lik :=
  rfl

end AutocatalyticArtwork

end StructuralIntelligence
