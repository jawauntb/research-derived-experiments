#!/usr/bin/env python3
"""Task families for the symbolic weakness benchmark.

Each family produces a `Trial` with:

- a finite ground-truth function `ground_truth(x) -> y`;
- a training subset (biased: it does not cover the full domain or the full
  transformation orbit), so multiple hypotheses fit;
- a held-out OOD subset of inputs that the training set does not constrain;
- a list of candidate hypotheses (local shortcut, memorizer, true rule,
  near-miss rules);
- a transformation group acting on the domain, used to define equivariance
  weakness.

Families differ in their group structure (cyclic, dihedral, parity, S_n,
compositional) so we can show that weakness predicts OOD generalization
across diverse symmetry types, not just translations of Z_n.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass
from typing import Callable, Sequence


@dataclass(frozen=True)
class Example:
    x: int
    y: int


@dataclass(frozen=True)
class Candidate:
    name: str
    predictions: tuple[int, ...]
    form_length: int
    family: str

    def predict(self, x: int) -> int:
        return self.predictions[x]


@dataclass(frozen=True)
class GroupAction:
    """A finite group action on the domain {0, ..., domain_size - 1}.

    `elements` is a tuple of permutations of the domain, encoded as tuples of
    image indices. `identity_index` marks the identity element.
    """

    name: str
    domain_size: int
    elements: tuple[tuple[int, ...], ...]
    identity_index: int

    def __len__(self) -> int:
        return len(self.elements)

    def apply(self, element_index: int, x: int) -> int:
        return self.elements[element_index][x]


@dataclass(frozen=True)
class Trial:
    family: str
    domain_size: int
    train_examples: tuple[Example, ...]
    ood_inputs: tuple[int, ...]
    candidates: tuple[Candidate, ...]
    invariant_name: str
    group: GroupAction


def _identity_perm(n: int) -> tuple[int, ...]:
    return tuple(range(n))


def cyclic_group(modulus: int) -> GroupAction:
    elements = tuple(
        tuple((x + shift) % modulus for x in range(modulus))
        for shift in range(modulus)
    )
    return GroupAction(
        name=f"Z_{modulus}",
        domain_size=modulus,
        elements=elements,
        identity_index=0,
    )


def dihedral_group(n: int) -> GroupAction:
    rotations = tuple(
        tuple((x + shift) % n for x in range(n))
        for shift in range(n)
    )
    reflections = tuple(
        tuple(((-x - 1) + shift) % n for x in range(n))
        for shift in range(n)
    )
    elements = rotations + reflections
    return GroupAction(
        name=f"D_{n}",
        domain_size=n,
        elements=elements,
        identity_index=0,
    )


def symmetric_group(n: int) -> GroupAction:
    elements = tuple(tuple(p) for p in itertools.permutations(range(n)))
    identity = elements.index(_identity_perm(n))
    return GroupAction(
        name=f"S_{n}",
        domain_size=n,
        elements=elements,
        identity_index=identity,
    )


def parity_group(domain_size: int) -> GroupAction:
    identity = _identity_perm(domain_size)
    swap = tuple(x ^ 1 if x ^ 1 < domain_size else x for x in range(domain_size))
    return GroupAction(
        name=f"Parity_{domain_size}",
        domain_size=domain_size,
        elements=(identity, swap),
        identity_index=0,
    )


def equivariance_count(candidate: Candidate, group: GroupAction) -> int:
    # Count group elements g such that f(g·x) = g·f(x) for all x — i.e. g
    # commutes with the candidate function under the canonical action on
    # outputs (same group acts on inputs and outputs).
    n = group.domain_size
    count = 0
    for g in group.elements:
        is_equivariant = True
        for x in range(n):
            f_gx = candidate.predict(g[x])
            f_x = candidate.predict(x)
            if f_gx != g[f_x]:
                is_equivariant = False
                break
        if is_equivariant:
            count += 1
    return count


def equivariance_count_with_action(
    candidate: Candidate,
    input_group: GroupAction,
    output_group: GroupAction,
) -> int:
    """Count input-group elements whose action on outputs (induced by the
    candidate) coincides with a single output-group element.

    This is the symmetry-count generalization for when input and output
    sets are not naturally identified (e.g. permutation tasks).
    """
    n = input_group.domain_size
    count = 0
    for g in input_group.elements:
        induced = tuple(candidate.predict(g[x]) for x in range(n))
        # Need to find an output-group element h such that h(f(x)) == induced[x]
        # for all x. Equivalently, the mapping x -> induced[x] must equal
        # h composed with f.
        # We try every h and check.
        found = False
        for h in output_group.elements:
            if all(h[candidate.predict(x)] == induced[x] for x in range(n)):
                found = True
                break
        if found:
            count += 1
    return count


# ---------------------------------------------------------------------------
# Cyclic prefix-shift family (kept compatible with the original pilot).


def cyclic_prefix_trial(
    *, rng: random.Random, modulus: int, train_window: int
) -> Trial:
    if not 1 < train_window < modulus:
        raise ValueError("train_window must satisfy 2 <= train_window < modulus")
    offset = rng.randrange(1, modulus)
    group = cyclic_group(modulus)
    train_examples = tuple(
        Example(x=x, y=(x + offset) % modulus) for x in range(train_window)
    )
    ood_inputs = tuple(range(train_window, modulus))

    def shift_predictions(k: int) -> tuple[int, ...]:
        return tuple((x + k) % modulus for x in range(modulus))

    train_outputs = {ex.x: ex.y for ex in train_examples}
    local_patch = Candidate(
        name="local_prefix_patch",
        predictions=tuple(
            train_outputs[x] if x in train_outputs else x
            for x in range(modulus)
        ),
        form_length=3,
        family="local_patch",
    )
    memorizer = Candidate(
        name="memorize_train_examples",
        predictions=tuple(
            train_outputs[x] if x in train_outputs else 0
            for x in range(modulus)
        ),
        form_length=train_window + 2,
        family="memorizer",
    )
    invariant = Candidate(
        name=f"global_shift_{offset}",
        predictions=shift_predictions(offset),
        form_length=5,
        family="invariant",
    )
    wrong_shifts: list[Candidate] = [
        Candidate(
            name=f"global_shift_{k}",
            predictions=shift_predictions(k),
            form_length=5,
            family="wrong_invariant",
        )
        for k in range(1, modulus)
        if k != offset
    ]
    candidates_list: list[Candidate] = [local_patch, memorizer, invariant]
    candidates_list.extend(wrong_shifts)
    candidates = tuple(candidates_list)

    return Trial(
        family="cyclic_prefix_shift",
        domain_size=modulus,
        train_examples=train_examples,
        ood_inputs=ood_inputs,
        candidates=candidates,
        invariant_name=invariant.name,
        group=group,
    )


# ---------------------------------------------------------------------------
# Linear-mod family: y = (a * x + b) mod n, with a in (Z/nZ)* fixed by the
# global rule and an affine local shortcut available.


def linear_mod_trial(
    *, rng: random.Random, modulus: int, train_window: int
) -> Trial:
    if not 1 < train_window < modulus:
        raise ValueError("train_window must satisfy 2 <= train_window < modulus")
    coprime = [a for a in range(1, modulus) if _gcd(a, modulus) == 1]
    a = rng.choice([c for c in coprime if c != 1])
    b = rng.randrange(0, modulus)
    group = cyclic_group(modulus)

    def predictions(a_val: int, b_val: int) -> tuple[int, ...]:
        return tuple((a_val * x + b_val) % modulus for x in range(modulus))

    train_examples = tuple(
        Example(x=x, y=(a * x + b) % modulus) for x in range(train_window)
    )
    ood_inputs = tuple(range(train_window, modulus))
    train_outputs = {ex.x: ex.y for ex in train_examples}

    local_patch = Candidate(
        name="local_prefix_patch",
        predictions=tuple(
            train_outputs[x] if x in train_outputs else x
            for x in range(modulus)
        ),
        form_length=3,
        family="local_patch",
    )
    memorizer = Candidate(
        name="memorize_train_examples",
        predictions=tuple(
            train_outputs[x] if x in train_outputs else 0
            for x in range(modulus)
        ),
        form_length=train_window + 2,
        family="memorizer",
    )
    invariant = Candidate(
        name=f"affine_{a}_{b}",
        predictions=predictions(a, b),
        form_length=7,
        family="invariant",
    )
    wrong_affines = []
    for ap in coprime:
        for bp in range(modulus):
            if (ap, bp) == (a, b):
                continue
            preds = predictions(ap, bp)
            if all(preds[ex.x] == ex.y for ex in train_examples):
                wrong_affines.append(
                    Candidate(
                        name=f"affine_{ap}_{bp}",
                        predictions=preds,
                        form_length=7,
                        family="wrong_invariant",
                    )
                )
    candidates_list: list[Candidate] = [local_patch, memorizer, invariant]
    candidates_list.extend(wrong_affines)
    candidates = tuple(candidates_list)

    return Trial(
        family="linear_mod",
        domain_size=modulus,
        train_examples=train_examples,
        ood_inputs=ood_inputs,
        candidates=candidates,
        invariant_name=invariant.name,
        group=group,
    )


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


# ---------------------------------------------------------------------------
# Parity-coset family: domain is {0,1,...,2k-1}, x is paired with x^1, the
# rule sends each pair to its image under a hidden parity map. Training only
# sees one coset (only even or only odd indices), so the local rule "identity
# on the seen coset" fits the data but breaks parity equivariance.


def parity_coset_trial(*, rng: random.Random, domain_size: int) -> Trial:
    if domain_size < 4 or domain_size % 2:
        raise ValueError("domain_size must be an even integer >= 4")
    group = parity_group(domain_size)

    # Two cosets: evens vs odds. Pick a coset to expose during training.
    seen_even = rng.random() < 0.5
    seen_coset = [x for x in range(domain_size) if (x % 2 == 0) == seen_even]
    unseen_coset = [x for x in range(domain_size) if (x % 2 == 0) != seen_even]

    # Ground truth: swap each pair (x, x^1). I.e. for any input, output is the
    # parity-partner.
    truth = tuple(x ^ 1 if x ^ 1 < domain_size else x for x in range(domain_size))

    train_examples = tuple(Example(x=x, y=truth[x]) for x in seen_coset)
    ood_inputs = tuple(unseen_coset)
    train_outputs = {ex.x: ex.y for ex in train_examples}

    local_patch = Candidate(
        name="seen_coset_swap",
        predictions=tuple(
            train_outputs[x] if x in train_outputs else x
            for x in range(domain_size)
        ),
        form_length=3,
        family="local_patch",
    )
    memorizer = Candidate(
        name="memorize_seen_coset",
        predictions=tuple(
            train_outputs[x] if x in train_outputs else 0
            for x in range(domain_size)
        ),
        form_length=len(seen_coset) + 2,
        family="memorizer",
    )
    invariant = Candidate(
        name="parity_swap",
        predictions=truth,
        form_length=5,
        family="invariant",
    )
    wrong_invariant = Candidate(
        name="identity",
        predictions=tuple(range(domain_size)),
        form_length=2,
        family="wrong_invariant",
    )
    candidates = tuple(  # type: tuple[Candidate, ...]
        [local_patch, memorizer, invariant, wrong_invariant]
    )

    return Trial(
        family="parity_coset",
        domain_size=domain_size,
        train_examples=train_examples,
        ood_inputs=ood_inputs,
        candidates=candidates,
        invariant_name=invariant.name,
        group=group,
    )


# ---------------------------------------------------------------------------
# Color permutation family: domain is {0,..,n-1}, ground truth is a fixed
# permutation pi. Training only shows a subset of the support, so memorizers,
# identity-on-unseen, and the true permutation all fit. The transformation
# group is S_n acting on the codomain; equivariance under input-relabeling
# corresponds to "the rule must commute with input/output permutations".


def color_permutation_trial(
    *, rng: random.Random, domain_size: int, train_window: int
) -> Trial:
    if domain_size < 4:
        raise ValueError("domain_size must be >= 4")
    if not 1 < train_window < domain_size:
        raise ValueError("train_window must be in 2..domain_size-1")

    # Pi: a non-identity, fixed-point-free involution.
    perm = list(range(domain_size))
    rng.shuffle(perm)
    pi = tuple(perm)
    # Ensure non-identity
    if pi == tuple(range(domain_size)):
        pi = tuple([1, 0] + list(range(2, domain_size)))

    truth = pi
    train_inputs = sorted(rng.sample(range(domain_size), train_window))
    ood_inputs_sorted = [x for x in range(domain_size) if x not in train_inputs]
    train_examples = tuple(Example(x=x, y=truth[x]) for x in train_inputs)
    ood_inputs = tuple(ood_inputs_sorted)
    train_outputs = {ex.x: ex.y for ex in train_examples}

    local_patch = Candidate(
        name="local_train_patch",
        predictions=tuple(
            train_outputs[x] if x in train_outputs else x
            for x in range(domain_size)
        ),
        form_length=3,
        family="local_patch",
    )
    memorizer = Candidate(
        name="memorize_train",
        predictions=tuple(
            train_outputs[x] if x in train_outputs else 0
            for x in range(domain_size)
        ),
        form_length=train_window + 2,
        family="memorizer",
    )
    invariant = Candidate(
        name="permutation_truth",
        predictions=truth,
        form_length=4 + domain_size,
        family="invariant",
    )

    # Build a few wrong permutations that still fit train (rare but possible).
    wrong_perms: list[Candidate] = []
    for _ in range(min(8, domain_size)):
        cand = list(range(domain_size))
        rng.shuffle(cand)
        cand_t = tuple(cand)
        if cand_t == truth:
            continue
        if all(cand_t[ex.x] == ex.y for ex in train_examples):
            wrong_perms.append(
                Candidate(
                    name=f"wrong_perm_{len(wrong_perms)}",
                    predictions=cand_t,
                    form_length=4 + domain_size,
                    family="wrong_invariant",
                )
            )

    cp_list: list[Candidate] = [local_patch, memorizer, invariant]
    cp_list.extend(wrong_perms)
    candidates = tuple(cp_list)

    # For S_n equivariance scoring, we use the full symmetric group on the
    # domain. We use the "input-and-output share the same relabeling" version
    # of equivariance, so that a permutation candidate is equivariant under
    # exactly the conjugation orbit (typically |centralizer(pi)| elements).
    group = symmetric_group(domain_size)

    return Trial(
        family="color_permutation",
        domain_size=domain_size,
        train_examples=train_examples,
        ood_inputs=ood_inputs,
        candidates=candidates,
        invariant_name=invariant.name,
        group=group,
    )


# ---------------------------------------------------------------------------
# Compositional family: ground truth is f(x) = (a*x + b) mod n with both a
# multiplicative and additive structure. Training data is consistent with the
# additive sub-rule alone, the multiplicative sub-rule alone, and the combined
# rule. Only the combined rule survives in the held-out region under cyclic
# translations.


def compositional_trial(
    *, rng: random.Random, modulus: int, train_window: int
) -> Trial:
    return linear_mod_trial(rng=rng, modulus=modulus, train_window=train_window)


# ---------------------------------------------------------------------------
# Family registry


FAMILY_REGISTRY: dict[str, Callable[..., Trial]] = {
    "cyclic_prefix_shift": cyclic_prefix_trial,
    "parity_coset": parity_coset_trial,
    "color_permutation": color_permutation_trial,
    "dihedral_reflection": lambda **kw: dihedral_reflection_trial(**kw),  # type: ignore[arg-type]
}


def dihedral_reflection_trial(
    *, rng: random.Random, modulus: int, train_window: int
) -> Trial:
    """Dihedral family: the truth is reflection-with-shift on a discrete
    n-gon: f(x) = (b - x) mod n. The training prefix only contains forward
    rotations, so a local rotation patch fits the data but breaks reflection
    equivariance under the dihedral group D_n.
    """
    if modulus < 4:
        raise ValueError("modulus must be >= 4")
    if not 1 < train_window < modulus:
        raise ValueError("train_window must satisfy 2 <= train_window < modulus")

    b = rng.randrange(0, modulus)
    truth = tuple((b - x) % modulus for x in range(modulus))
    train_inputs = list(range(train_window))
    train_examples = tuple(Example(x=x, y=truth[x]) for x in train_inputs)
    ood_inputs = tuple(range(train_window, modulus))
    train_outputs = {ex.x: ex.y for ex in train_examples}

    # Local shortcut: a forward shift that fits the prefix (truth[0] - 0 = b,
    # so the shortcut "f(x) = (x + truth[0]) mod n" matches f(0) but breaks
    # everywhere else under reflection). For simplicity we just use the
    # exact training outputs and identity elsewhere.
    local_patch = Candidate(
        name="rotation_patch_then_identity",
        predictions=tuple(
            train_outputs[x] if x in train_outputs else x
            for x in range(modulus)
        ),
        form_length=3,
        family="local_patch",
    )
    memorizer = Candidate(
        name="memorize_train",
        predictions=tuple(
            train_outputs[x] if x in train_outputs else 0
            for x in range(modulus)
        ),
        form_length=train_window + 2,
        family="memorizer",
    )
    invariant = Candidate(
        name=f"reflection_b{b}",
        predictions=truth,
        form_length=6,
        family="invariant",
    )

    # Wrong dihedral elements: pure rotations (which match a "shift" rule).
    wrong: list[Candidate] = []
    for shift in range(modulus):
        preds = tuple((x + shift) % modulus for x in range(modulus))
        if all(preds[ex.x] == ex.y for ex in train_examples) and preds != truth:
            wrong.append(
                Candidate(
                    name=f"rotation_shift_{shift}",
                    predictions=preds,
                    form_length=5,
                    family="wrong_invariant",
                )
            )

    candidates_list: list[Candidate] = [local_patch, memorizer, invariant]
    candidates_list.extend(wrong)
    candidates = tuple(candidates_list)

    return Trial(
        family="dihedral_reflection",
        domain_size=modulus,
        train_examples=train_examples,
        ood_inputs=ood_inputs,
        candidates=candidates,
        invariant_name=invariant.name,
        group=dihedral_group(modulus),
    )


def make_trial(family: str, **kwargs: object) -> Trial:
    if family not in FAMILY_REGISTRY:
        raise KeyError(f"unknown family: {family}")
    return FAMILY_REGISTRY[family](**kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Accuracy helpers (shared with selectors.py).


def train_accuracy(candidate: Candidate, trial: Trial) -> float:
    if not trial.train_examples:
        return 1.0
    correct = sum(
        1
        for ex in trial.train_examples
        if candidate.predict(ex.x) == ex.y
    )
    return correct / len(trial.train_examples)


def ood_accuracy(candidate: Candidate, trial: Trial, *, truth: Sequence[int]) -> float:
    if not trial.ood_inputs:
        return 1.0
    correct = sum(
        1 for x in trial.ood_inputs if candidate.predict(x) == truth[x]
    )
    return correct / len(trial.ood_inputs)


def ground_truth_from_invariant(trial: Trial) -> tuple[int, ...]:
    for candidate in trial.candidates:
        if candidate.name == trial.invariant_name:
            return candidate.predictions
    raise KeyError(f"invariant candidate {trial.invariant_name!r} not found")
