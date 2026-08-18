# PAC-Bayes weakness enumeration — 2026-08-18

Verdict: `finite_iid_holds_ood_or_weight_killed`.

The finite IID certificate holds. The uniform OOD-from-PAC-Bayes
reading is killed by the frozen **parity** family. Cyclic and
dihedral keep the aligned ranking. Neural PAC-Bayes stays withheld.

| Gate | Result |
|---|---|
| `|H|=n^n` | pass (823543, 823543, 46656, 46656) |
| mixture mass formula | pass |
| cyclic `|H_eq|=7` for `ρ=id` | pass (`H_{≥7}` is 49, not 7) |
| m=8 aligned-truth bound < 0.99 | pass (0.666 cyclic/dihedral; 0.762 parity; 0.760 color) |
| π sign stable | pass |
| hyperprior ≠ pure `W` monotone | pass |
| wrong/random not as tight as truth while shortcut fails OOD | **fail on parity** |
| neural withheld | withheld |

Parity is the paper's known too-small-group negative case: aligned
`W(truth)=W(shortcut)=2`, and `C_6` as a wrong group gives the
shortcut a tighter KL (6.28) than the aligned truth (6.75) while
OOD risk is 1 vs 0. That kills a uniform "the certificate explains
OOD" claim. It does not kill the mass formula or the IID plug-in.

Cyclic/dihedral: aligned KL(truth)≈4.05 vs KL(shortcut)≈15.6–16.3,
OOD risk 0 vs 1. Wrong/random groups do **not** match the truth
certificate.

`H_{≥7}=49` on `C_7` is the affine maps `x↦ax+b` over `𝔽_7`. The
fixed-action identity-`ρ` subclass is the 7 translations. Repository
weakness is strictly larger than the sketch's `|Y|^r` limit.

## Discovery-regime audit (post-run)

Question: does exact `H=Y^X` on the frozen `|X|≤7` domains recover
the mixture-mass certificate, a non-vacuous IID plug-in, and the
claimed OOD/group/weight distinctions?

Current regime: Wave 11 mixture mass (Lean-verified toy) + Wave 12
compatibility-class KL certificate (proved-not-verified). LSM remains
a citation. Action class: **search** inside that schema — a new
artifact type was not added; class cards are the same objects, now
enumerated.

Accepted: cardinality, mass formula, cyclic `|H_eq|=7`, non-vacuous
m=8 aligned-truth bounds, π-sign stability, hyperprior ≠ pure `W`.
Rejected as a uniform claim: OOD-from-certificate (parity).
Withheld: neural / stochastic PAC-Bayes; LSM as a theorem.

Residual: the finite IID certificate is real; a uniform OOD reading
is not. Cyclic/dihedral still rank aligned truth over the shortcut.
Next move on this sketch is not another Lean axiom and not LSM.
