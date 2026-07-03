#!/usr/bin/env python3
"""Selectors that pick a single hypothesis from the train-consistent candidate
pool. Each selector implements a different inductive bias.

We compare:

- `train_loss`        : best training accuracy, tied by simplicity.
- `validation`        : holds out one train example and scores on it.
- `simplicity`        : shortest hypothesis form length.
- `compression`       : form_length + 20 * train errors (MDL-style proxy).
- `mdl_program`       : weight by 2^-form_length (Solomonoff-style proxy).
- `flatness_proxy`    : largest free-domain count. This is a symbolic
                        completion-volume proxy, not Hessian/weight-space
                        flatness.
- `weakness_oracle`   : largest equivariance count under the trial's true group.
- `weakness_wrong_group`: weakness scored under a wrong group (control).
- `weakness_noisy`    : weakness with a noisy subset of the true group.
- `weakness_data_inferred`: weakness under a group inferred from the data.
- `random`            : random train-consistent.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable

from experiments.symbolic_weakness.families import (
    Candidate,
    GroupAction,
    Trial,
    cyclic_group,
    dihedral_group,
    equivariance_count_with_action,
    ground_truth_from_invariant,
    ood_accuracy,
    parity_group,
    train_accuracy,
)


@dataclass(frozen=True)
class CandidateMetrics:
    name: str
    family: str
    train_accuracy: float
    ood_accuracy: float
    form_length: int
    compression_length: int
    flatness_proxy: int
    weakness_oracle: int
    weakness_wrong_group: int
    weakness_noisy_group: int
    weakness_data_inferred: int
    leave_one_out_validation: float
    mdl_program_weight: float


def _wrong_group_for_trial(trial: Trial, rng: random.Random) -> GroupAction:
    """Pick a clearly wrong group for the trial: random permutations that
    do not correspond to the trial's true symmetry. Identity is always
    included so the action remains well-defined.
    """
    n = trial.domain_size
    perms: list[tuple[int, ...]] = []
    identity = tuple(range(n))
    perms.append(identity)
    # Generate random non-identity permutations until we have a comparable
    # number to the true group's size, capped at n + 4 to avoid exhaustion
    # for small domains.
    target = min(max(len(trial.group), 4), n * 2)
    attempts = 0
    while len(perms) < target and attempts < 200:
        p = list(range(n))
        rng.shuffle(p)
        candidate = tuple(p)
        if candidate not in perms and candidate not in trial.group.elements:
            perms.append(candidate)
        attempts += 1
    return GroupAction(
        name="wrong_random_permutations",
        domain_size=n,
        elements=tuple(perms),
        identity_index=0,
    )


def _noisy_group_for_trial(trial: Trial, rng: random.Random) -> GroupAction:
    """Return a subset of the true group: keep identity, drop a random subset
    of the rest, and add one wrong element."""
    n = trial.domain_size
    true_group = trial.group
    elements = list(true_group.elements)
    identity = elements[true_group.identity_index]
    rest = [g for g in elements if g != identity]
    rng.shuffle(rest)
    keep = max(1, len(rest) // 2)
    kept = rest[:keep]
    # Add one wrong permutation
    wrong = list(range(n))
    rng.shuffle(wrong)
    wrong_t = tuple(wrong)
    if wrong_t in kept or wrong_t == identity:
        wrong_t = tuple(((x + 1) ^ 1) % n for x in range(n))
    new_elements = [identity] + kept + [wrong_t]
    return GroupAction(
        name=f"noisy_{true_group.name}",
        domain_size=n,
        elements=tuple(new_elements),
        identity_index=0,
    )


def _data_inferred_group(trial: Trial) -> GroupAction:
    """Infer a candidate transformation group from training data alone.

    Heuristic: enumerate a small transformation family implied by the domain
    type, then keep every input-side permutation g whose action on observed
    training pairs is consistent with at least one output-side permutation h
    from the same family. This is not unconstrained group discovery; it is an
    explicit, reproducible "no oracle offset" prior over rotations/reflections.
    """
    n = trial.domain_size
    train_pairs = list(trial.train_examples)
    if not train_pairs:
        return trial.group

    def _consistent_subset(
        base: GroupAction,
        *,
        name: str,
    ) -> GroupAction:
        seen = {ex.x: ex.y for ex in train_pairs}
        keep: list[tuple[int, ...]] = []
        for g in base.elements:
            valid_for_some_h = False
            for h in base.elements:
                valid = True
                for ex in train_pairs:
                    shifted_x = g[ex.x]
                    if shifted_x in seen and h[ex.y] != seen[shifted_x]:
                        valid = False
                        break
                if valid:
                    valid_for_some_h = True
                    break
            if valid_for_some_h:
                keep.append(g)
        identity = tuple(range(n))
        if identity not in keep:
            keep.insert(0, identity)
        return GroupAction(
            name=name.format(count=len(keep)),
            domain_size=n,
            elements=tuple(keep),
            identity_index=keep.index(identity),
        )

    if trial.family in {"cyclic_prefix_shift", "linear_mod", "compositional"}:
        # Circular-domain translation prior inferred by training-pair
        # consistency, without reading the trial's oracle group object.
        return _consistent_subset(
            cyclic_group(n),
            name="data_inferred_cyclic_subset_{count}",
        )

    if trial.family == "dihedral_reflection":
        # Signed circular-domain prior: rotations plus reflections. This fixes
        # the previous fallback that reused trial.group for dihedral tasks.
        return _consistent_subset(
            dihedral_group(n),
            name="data_inferred_dihedral_subset_{count}",
        )

    if trial.family == "parity_coset":
        # Infer identity/parity swap by checking the only nontrivial pairwise
        # involution available in the parity-domain prior.
        seen = {ex.x: ex.y for ex in train_pairs}
        keep: list[tuple[int, ...]] = []
        base = parity_group(n)
        for g in base.elements:
            for ex in train_pairs:
                shifted_x = g[ex.x]
                if shifted_x in seen and g[ex.y] != seen[shifted_x]:
                    break
            else:
                keep.append(g)
        return GroupAction(
            name=f"data_inferred_parity_subset_{len(keep)}",
            domain_size=n,
            elements=tuple(keep),
            identity_index=keep.index(tuple(range(n))),
        )

    if trial.family == "color_permutation":
        # In S_n the data-inferred group is small without more cues; we
        # keep the cyclic translation subgroup as a heuristic prior.
        return cyclic_group(n)

    return trial.group


def _mdl_weight(form_length: int) -> float:
    return math.pow(2.0, -float(form_length))


def _leave_one_out_validation(candidate: Candidate, trial: Trial) -> float:
    if len(trial.train_examples) <= 1:
        return train_accuracy(candidate, trial)
    correct = 0
    for held_out in trial.train_examples:
        # The candidate's predictions are fixed in the symbolic regime, so
        # leave-one-out simply scores how well the candidate predicts the
        # held-out training pair.
        if candidate.predict(held_out.x) == held_out.y:
            correct += 1
    return correct / len(trial.train_examples)


def candidate_metrics(
    candidate: Candidate,
    trial: Trial,
    *,
    rng: random.Random,
) -> CandidateMetrics:
    truth = ground_truth_from_invariant(trial)
    train_acc = train_accuracy(candidate, trial)
    ood_acc = ood_accuracy(candidate, trial, truth=truth)
    train_errors = round((1.0 - train_acc) * len(trial.train_examples))
    compression_length = candidate.form_length + 20 * train_errors

    # Symbolic completion-volume proxy: how many domain positions are
    # unconstrained by the training set. This is not Hessian flatness.
    flatness_proxy = trial.domain_size - len(trial.train_examples)

    # Definition: weakness = number of group elements g such that there
    # exists an output-group element h with f(g·x) = h·f(x) for all x.
    # This is the symmetry-compatibility count from Bennett-style weakness
    # generalized to non-abelian and non-input-output-identified actions.
    weakness_oracle = equivariance_count_with_action(
        candidate, trial.group, trial.group
    )
    wrong_group = _wrong_group_for_trial(trial, rng)
    noisy_group = _noisy_group_for_trial(trial, rng)
    data_group = _data_inferred_group(trial)

    def _safe_eq(group: GroupAction) -> int:
        return equivariance_count_with_action(candidate, group, group)

    weakness_wrong = _safe_eq(wrong_group)
    weakness_noisy = _safe_eq(noisy_group)
    weakness_inferred = _safe_eq(data_group)

    return CandidateMetrics(
        name=candidate.name,
        family=candidate.family,
        train_accuracy=train_acc,
        ood_accuracy=ood_acc,
        form_length=candidate.form_length,
        compression_length=compression_length,
        flatness_proxy=flatness_proxy,
        weakness_oracle=weakness_oracle,
        weakness_wrong_group=weakness_wrong,
        weakness_noisy_group=weakness_noisy,
        weakness_data_inferred=weakness_inferred,
        leave_one_out_validation=_leave_one_out_validation(candidate, trial),
        mdl_program_weight=_mdl_weight(candidate.form_length),
    )


def consistent_metrics(trial: Trial, rng: random.Random) -> list[CandidateMetrics]:
    """Return metrics for train-perfect candidates only.

    Includes a `min_form_length` tiebreaker stripped of randomness so that
    selectors that nominally tie reduce deterministically.
    """
    return [
        candidate_metrics(c, trial, rng=rng)
        for c in trial.candidates
        if train_accuracy(c, trial) == 1.0
    ]


def _argbest(
    items: Iterable[CandidateMetrics],
    key: Callable[[CandidateMetrics], float],
    *,
    maximize: bool,
    rng: random.Random,
    tiebreak: Callable[[list[CandidateMetrics], random.Random], CandidateMetrics],
) -> CandidateMetrics:
    items = list(items)
    if not items:
        raise ValueError("empty candidate list")
    target = max(key(x) for x in items) if maximize else min(key(x) for x in items)
    tied = [x for x in items if key(x) == target]
    if len(tied) == 1:
        return tied[0]
    return tiebreak(tied, rng)


def _tiebreak_simplicity(items: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    target = min(x.form_length for x in items)
    tied = [x for x in items if x.form_length == target]
    return rng.choice(tied)


def _tiebreak_compression(items: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    target = min(x.compression_length for x in items)
    tied = [x for x in items if x.compression_length == target]
    return rng.choice(tied)


def choose_train_loss(items: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    return _argbest(
        items, key=lambda x: x.train_accuracy, maximize=True, rng=rng,
        tiebreak=_tiebreak_simplicity,
    )


def choose_simplicity(items: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    return _argbest(
        items, key=lambda x: x.form_length, maximize=False, rng=rng,
        tiebreak=lambda xs, r: r.choice(xs),
    )


def choose_compression(items: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    return _argbest(
        items, key=lambda x: x.compression_length, maximize=False, rng=rng,
        tiebreak=lambda xs, r: r.choice(xs),
    )


def choose_flatness(items: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    return _argbest(
        items, key=lambda x: x.flatness_proxy, maximize=True, rng=rng,
        tiebreak=_tiebreak_simplicity,
    )


def choose_weakness_oracle(items: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    return _argbest(
        items, key=lambda x: x.weakness_oracle, maximize=True, rng=rng,
        tiebreak=_tiebreak_compression,
    )


def choose_weakness_wrong_group(items: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    return _argbest(
        items, key=lambda x: x.weakness_wrong_group, maximize=True, rng=rng,
        tiebreak=_tiebreak_compression,
    )


def choose_weakness_noisy_group(items: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    return _argbest(
        items, key=lambda x: x.weakness_noisy_group, maximize=True, rng=rng,
        tiebreak=_tiebreak_compression,
    )


def choose_weakness_data_inferred(items: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    return _argbest(
        items, key=lambda x: x.weakness_data_inferred, maximize=True, rng=rng,
        tiebreak=_tiebreak_compression,
    )


def choose_validation(items: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    return _argbest(
        items, key=lambda x: x.leave_one_out_validation, maximize=True, rng=rng,
        tiebreak=_tiebreak_simplicity,
    )


def choose_mdl_program(items: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    return _argbest(
        items, key=lambda x: x.mdl_program_weight, maximize=True, rng=rng,
        tiebreak=_tiebreak_simplicity,
    )


def choose_random(items: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    return rng.choice(items)


SELECTORS: dict[str, Callable[[list[CandidateMetrics], random.Random], CandidateMetrics]] = {
    "train_loss": choose_train_loss,
    "validation": choose_validation,
    "simplicity": choose_simplicity,
    "compression": choose_compression,
    "mdl_program": choose_mdl_program,
    "flatness_proxy": choose_flatness,
    "weakness_oracle": choose_weakness_oracle,
    "weakness_wrong_group": choose_weakness_wrong_group,
    "weakness_noisy_group": choose_weakness_noisy_group,
    "weakness_data_inferred": choose_weakness_data_inferred,
    "random": choose_random,
}


__all__ = [
    "CandidateMetrics",
    "SELECTORS",
    "candidate_metrics",
    "consistent_metrics",
]
