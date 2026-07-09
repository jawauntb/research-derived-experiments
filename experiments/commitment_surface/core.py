"""Shared analysis utilities for the commitment-surface experiments.

The commitment-surface reframe treats compatibility / weakness as a
*diagnostic* rather than a cause. Load-bearing structure is what survives
transport to the deployment commitment surface, verified by a causal patch.
This module holds the stdlib pieces: extension arithmetic, weighted weakness,
concern generators, and the patch-CE calculator abstraction (the torch
patch-CE lives in ``e2_e3_neural_sweep`` because it needs the trained model).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
from statistics import mean, pstdev
from typing import Callable, Sequence


Pair = tuple[int, int]
Table = tuple[int, ...]


def _pair_index(a: int, b: int, modulus: int) -> int:
    return a * modulus + b


def all_pairs(modulus: int) -> list[Pair]:
    return [(a, b) for a in range(modulus) for b in range(modulus)]


def true_addition_table(modulus: int) -> Table:
    return tuple((a + b) % modulus for a, b in all_pairs(modulus))


# ---------------------------------------------------------------------------
# E1 -- concern-weighted extension arithmetic
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Deployment:
    """A concern-weighted deployment slice.

    ``pairs`` are the deployment futures; ``kappa`` is the concern weight
    per future (nonnegative, unnormalized).
    """

    pairs: tuple[Pair, ...]
    kappa: tuple[float, ...]

    def __post_init__(self) -> None:  # noqa: D401 -- dataclass hook
        if len(self.pairs) != len(self.kappa):
            raise ValueError("pairs and kappa must have equal length")
        if any(k < 0 for k in self.kappa):
            raise ValueError("kappa must be nonnegative")


def uniform_deployment(pairs: Sequence[Pair]) -> Deployment:
    return Deployment(pairs=tuple(pairs), kappa=tuple(1.0 for _ in pairs))


def unequal_deployment(
    pairs: Sequence[Pair],
    *,
    rng: random.Random,
    focus_fraction: float = 0.25,
    focus_weight: float = 10.0,
) -> Deployment:
    """A well-specified unequal-consequence deployment.

    A ``focus_fraction`` slice gets ``focus_weight``; the rest gets 1.0.
    This is the "true" concern signal a well-calibrated selector would use.
    """
    pool = list(pairs)
    rng.shuffle(pool)
    n_focus = max(1, int(round(len(pool) * focus_fraction)))
    focus = set(pool[:n_focus])
    kappa = tuple(focus_weight if p in focus else 1.0 for p in pairs)
    return Deployment(pairs=tuple(pairs), kappa=kappa)


def misspecified_deployment(
    pairs: Sequence[Pair],
    *,
    rng: random.Random,
    focus_fraction: float = 0.25,
    focus_weight: float = 10.0,
) -> Deployment:
    """A random misspecified concern weighting with the same distribution.

    Uses the same focus_weight and fraction so the marginal weight
    distribution matches the well-specified case -- only the *assignment*
    to pairs is randomized. This is the control that isolates the value
    of aligning kappa with the deployment generator.
    """
    n = len(pairs)
    n_focus = max(1, int(round(n * focus_fraction)))
    kappa = [focus_weight] * n_focus + [1.0] * (n - n_focus)
    rng.shuffle(kappa)
    return Deployment(pairs=tuple(pairs), kappa=tuple(kappa))


def weighted_extension_mass(
    table: Table,
    modulus: int,
    deployment: Deployment,
) -> float:
    """Sum of concern weights on deployment futures where ``table`` agrees
    with the true addition rule.

    This is the concern-weighted analogue of ``|Z_h cap U|`` -- restricted
    Bennett weakness under the deployment concern measure.
    """
    total = 0.0
    for pair, k in zip(deployment.pairs, deployment.kappa):
        a, b = pair
        if table[_pair_index(a, b, modulus)] == (a + b) % modulus:
            total += k
    return total


def unweighted_extension_mass(
    table: Table,
    modulus: int,
    deployment: Deployment,
) -> float:
    """Uniform Bennett weakness restricted to the deployment slice."""
    total = 0.0
    for pair in deployment.pairs:
        a, b = pair
        if table[_pair_index(a, b, modulus)] == (a + b) % modulus:
            total += 1.0
    return total


# ---------------------------------------------------------------------------
# Candidate hypothesis families
# ---------------------------------------------------------------------------


def candidate_shift_tables(modulus: int) -> list[Table]:
    """The cyclic-shift hypothesis family: ``(a + b + s) mod n`` for s in [0, n)."""
    tables: list[Table] = []
    for shift in range(modulus):
        tables.append(
            tuple((a + b + shift) % modulus for a, b in all_pairs(modulus))
        )
    return tables


def random_train_perfect_completion(
    modulus: int,
    train_pairs: Sequence[Pair],
    *,
    rng: random.Random,
    ood_correct_prob: float = 0.35,
) -> Table:
    """Sample a candidate that agrees with the truth on ``train_pairs`` and
    partially agrees on OOD pairs (each with probability ``ood_correct_prob``).

    This gives the E1 selectors a diverse pool of train-perfect hypotheses
    with heterogeneous OOD coverage -- exactly the regime where a
    concern-weighted selector *could* beat unweighted (or fail to).
    """
    train_set = set(train_pairs)
    values: list[int] = []
    for a, b in all_pairs(modulus):
        truth = (a + b) % modulus
        if (a, b) in train_set:
            values.append(truth)
        elif rng.random() < ood_correct_prob:
            values.append(truth)
        else:
            # sample a wrong label
            wrong = rng.randrange(modulus)
            if wrong == truth:
                wrong = (wrong + 1) % modulus
            values.append(wrong)
    return tuple(values)


def biased_train_perfect_completion(
    modulus: int,
    train_pairs: Sequence[Pair],
    high_focus: set[Pair],
    *,
    rng: random.Random,
    high_correct_prob: float,
    low_correct_prob: float,
) -> Table:
    """Candidate that is biased to cover the high-focus OOD block more
    reliably than the low-focus one (or vice versa if the probs are
    swapped).

    Used to seed the E1 pool with hypotheses that concern-weighted
    selection *would* find valuable IF the kappa weights point to the
    high-focus block.
    """
    train_set = set(train_pairs)
    values: list[int] = []
    for a, b in all_pairs(modulus):
        truth = (a + b) % modulus
        if (a, b) in train_set:
            values.append(truth)
            continue
        p = high_correct_prob if (a, b) in high_focus else low_correct_prob
        if rng.random() < p:
            values.append(truth)
        else:
            wrong = rng.randrange(modulus)
            if wrong == truth:
                wrong = (wrong + 1) % modulus
            values.append(wrong)
    return tuple(values)


def random_candidate_tables(
    modulus: int,
    n: int,
    *,
    rng: random.Random,
) -> list[Table]:
    """Fully random distractors (rare to be train-perfect at large n)."""
    tables: list[Table] = []
    for _ in range(n):
        tables.append(tuple(rng.randrange(modulus) for _ in range(modulus * modulus)))
    return tables


def local_shortcut_table(modulus: int, train_window: int) -> Table:
    """A train-perfect memorizer that defaults to ``a`` outside the window."""
    values: list[int] = []
    for a, b in all_pairs(modulus):
        if a < train_window:
            values.append((a + b) % modulus)
        else:
            values.append(a)
    return tuple(values)


def train_perfect(
    table: Table,
    modulus: int,
    train_pairs: Sequence[Pair],
) -> bool:
    return all(
        table[_pair_index(a, b, modulus)] == (a + b) % modulus for a, b in train_pairs
    )


# ---------------------------------------------------------------------------
# Selectors
# ---------------------------------------------------------------------------


Selector = Callable[[list[Table]], Table]


def unweighted_weakness_selector(
    deployment: Deployment,
    modulus: int,
) -> Selector:
    def _select(candidates: list[Table]) -> Table:
        scores = [
            unweighted_extension_mass(table, modulus, deployment)
            for table in candidates
        ]
        best = max(range(len(candidates)), key=lambda i: scores[i])
        return candidates[best]

    return _select


def concern_weighted_selector(
    deployment: Deployment,
    modulus: int,
) -> Selector:
    def _select(candidates: list[Table]) -> Table:
        scores = [
            weighted_extension_mass(table, modulus, deployment)
            for table in candidates
        ]
        best = max(range(len(candidates)), key=lambda i: scores[i])
        return candidates[best]

    return _select


def loss_selector(modulus: int, train_pairs: Sequence[Pair]) -> Selector:
    def _select(candidates: list[Table]) -> Table:
        # tie on train-perfect: prefer smaller lexicographic table
        for table in candidates:
            if train_perfect(table, modulus, train_pairs):
                return table
        return candidates[0]

    return _select


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------


def deployment_accuracy(
    table: Table,
    modulus: int,
    deployment: Deployment,
) -> float:
    """Concern-weighted accuracy on the deployment slice.

    Fraction of concern mass on which ``table`` matches the truth.
    """
    total = sum(deployment.kappa) or 1.0
    correct = weighted_extension_mass(table, modulus, deployment)
    return correct / total


def plain_accuracy(table: Table, modulus: int, pairs: Sequence[Pair]) -> float:
    if not pairs:
        return 0.0
    correct = sum(
        int(table[_pair_index(a, b, modulus)] == (a + b) % modulus)
        for a, b in pairs
    )
    return correct / len(pairs)


# ---------------------------------------------------------------------------
# Simple stats
# ---------------------------------------------------------------------------


def mean_ci95(values: Sequence[float]) -> tuple[float, float, float]:
    if not values:
        return (0.0, 0.0, 0.0)
    m = mean(values)
    if len(values) < 2:
        return (m, m, m)
    sd = pstdev(values)
    half = 1.96 * sd / math.sqrt(len(values))
    return (m, m - half, m + half)


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    def rank(vs: Sequence[float]) -> list[float]:
        order = sorted(range(len(vs)), key=lambda i: vs[i])
        r = [0.0] * len(vs)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vs[order[j + 1]] == vs[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = rank(xs), rank(ys)
    mx, my = mean(rx), mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0.0


@dataclass
class E1CellResult:
    modulus: int
    seed: int
    focus_fraction: float
    focus_weight: float
    unweighted_selector_acc: float
    concern_wellspec_selector_acc: float
    concern_misspec_selector_acc: float
    loss_selector_acc: float
    truth_selector_acc: float
    n_candidates: int
    metadata: dict[str, object] = field(default_factory=dict)


def run_e1_cell(
    *,
    modulus: int,
    seed: int,
    focus_fraction: float = 0.25,
    focus_weight: float = 10.0,
    n_candidates: int = 400,
    train_window_frac: float = 0.5,
    exclude_truth: bool = True,
) -> E1CellResult:
    """One E1 cell: build a diverse pool of train-perfect *partial-agreement*
    hypotheses and compare selectors under different concern weightings.

    The candidate pool contains random train-perfect completions plus a
    subset that is *deliberately biased* toward covering the wellspec
    high-focus block. This means:

    - if the selector correctly uses the wellspec kappa, it can pick a
      biased-toward-high-focus candidate that scores well on concern-
      weighted OOD accuracy;
    - if the selector uses uniform mass, it prefers whichever candidate
      has the largest overall OOD coverage, missing the concern signal;
    - if the selector uses a misspecified kappa, it should perform no
      better than the uniform one, because the misspec focus is disjoint
      (in expectation) from the true focus.

    The truth is *excluded* by default so no candidate trivially wins.
    """
    rng = random.Random(seed)
    train_window = max(2, int(round(modulus * train_window_frac)))
    train_pairs = [(a, b) for a in range(train_window) for b in range(modulus)]
    ood_pairs = [(a, b) for a in range(train_window, modulus) for b in range(modulus)]

    # Deployments.
    wellspec = unequal_deployment(
        ood_pairs, rng=random.Random(seed + 7), focus_fraction=focus_fraction,
        focus_weight=focus_weight,
    )
    misspec = misspecified_deployment(
        ood_pairs, rng=random.Random(seed + 11), focus_fraction=focus_fraction,
        focus_weight=focus_weight,
    )
    uniform = uniform_deployment(ood_pairs)
    high_focus = {p for p, k in zip(wellspec.pairs, wellspec.kappa) if k > 1.0}

    # Candidate pool: random completions + biased completions favouring
    # the wellspec high-focus block.
    candidates: list[Table] = []
    for _ in range(n_candidates):
        candidates.append(
            random_train_perfect_completion(
                modulus, train_pairs, rng=rng, ood_correct_prob=0.30
            )
        )
    for _ in range(n_candidates // 4):
        candidates.append(
            biased_train_perfect_completion(
                modulus,
                train_pairs,
                high_focus,
                rng=rng,
                high_correct_prob=0.75,
                low_correct_prob=0.20,
            )
        )
    if not exclude_truth:
        candidates.append(true_addition_table(modulus))

    unweighted_pick = unweighted_weakness_selector(uniform, modulus)(candidates)
    concern_wellspec_pick = concern_weighted_selector(wellspec, modulus)(candidates)
    concern_misspec_pick = concern_weighted_selector(misspec, modulus)(candidates)
    loss_pick = loss_selector(modulus, train_pairs)(candidates)
    truth_pick = true_addition_table(modulus)

    return E1CellResult(
        modulus=modulus,
        seed=seed,
        focus_fraction=focus_fraction,
        focus_weight=focus_weight,
        # Score every selector against the wellspec deployment: this is
        # the concern-weighted OOD accuracy the operator ultimately cares
        # about. Truth is the ceiling.
        unweighted_selector_acc=deployment_accuracy(unweighted_pick, modulus, wellspec),
        concern_wellspec_selector_acc=deployment_accuracy(
            concern_wellspec_pick, modulus, wellspec
        ),
        concern_misspec_selector_acc=deployment_accuracy(
            concern_misspec_pick, modulus, wellspec
        ),
        loss_selector_acc=deployment_accuracy(loss_pick, modulus, wellspec),
        truth_selector_acc=deployment_accuracy(truth_pick, modulus, wellspec),
        n_candidates=len(candidates),
        metadata={
            "train_window": train_window,
            "train_pairs": len(train_pairs),
            "ood_pairs": len(ood_pairs),
            "n_focus": sum(1 for k in wellspec.kappa if k > 1.0),
            "exclude_truth": exclude_truth,
        },
    )
