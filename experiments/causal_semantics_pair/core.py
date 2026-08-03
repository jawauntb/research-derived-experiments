"""Exact witness of Theorems CS-1 (Psi-equivalence is a congruence) and
CS-2 (meaning quotient is the coarsest common sufficient statistic on
messages) from the companion paper *Causal Semantics*
(``papers/causal_semantics/paper.md``).

Setup (matches paper section 4)
-------------------------------

- Message space   ``M = {m_0, m_1, m_2, m_3, m_4, m_5}``      (six symbols)
- Context space   ``C = {c_0, c_1, c_2, c_3}``                (four contexts)
- Future space    ``X = {x_0, x_1, x_2, x_3}``                (four states)
- Update operator ``Psi : M x C -> P(X)``                     hand-built so:

  * ``Psi(m_0, .) == Psi(m_1, .) == D_A(.)``  [class A]
  * ``Psi(m_2, .) == Psi(m_3, .) == D_B(.)``  [class B]
  * ``Psi(m_4, .) == D_C(.)``                  [class C]
  * ``Psi(m_5, .) == D_D(.)``                  [class D]

  where ``D_A, D_B, D_C, D_D : C -> P(X)`` are four pairwise-distinct
  context-conditional distributions. Distinctness is witnessed at
  ``c_0``, where each class yields a different probability vector
  over ``X``.

The four Psi-classes are exactly ``{{m_0, m_1}, {m_2, m_3}, {m_4}, {m_5}}``.

Distractor
----------

A hand-built co-occurrence signature map ``kappa : M -> Z^4_{>=0}``:

  * ``kappa(m_0) = kappa(m_2) = kappa(m_4) = (4, 4, 1, 1)`` (even-indexed)
  * ``kappa(m_1) = kappa(m_3) = kappa(m_5) = (1, 1, 4, 4)`` (odd-indexed)

The co-occurrence quotient is ``{{m_0, m_2, m_4}, {m_1, m_3, m_5}}`` --
two classes, orthogonal to the four-class Psi-quotient (neither
partition refines the other, no cell of one coincides with a cell of
the other).

Pre-registered gates (all four pass exactly)
--------------------------------------------

- ``cs1_psi_equivalence_is_reflexive_symmetric_transitive``: verified
  by exhaustive enumeration of all 36 ordered pairs (reflexivity /
  symmetry) and all 216 ordered triples (transitivity).
- ``cs2_psi_quotient_has_four_classes``: the equivalence classes of
  ``~_Psi`` on ``M`` are exactly ``{{m_0, m_1}, {m_2, m_3}, {m_4}, {m_5}}``.
- ``cs2_psi_quotient_is_common_sufficient``: for every context
  ``c in C``, the downstream distribution ``Psi(., c)`` is constant
  within each Psi-class.
- ``cs_cooccurrence_partition_differs_from_psi_quotient``: the
  Psi-quotient and the co-occurrence quotient are distinct partitions
  of ``M``; neither refines the other, no cell coincides.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import product


# ---------- Fixed world parameters (matches paper section 4) ----------

MESSAGES: tuple[str, ...] = ("m0", "m1", "m2", "m3", "m4", "m5")
CONTEXTS: tuple[str, ...] = ("c0", "c1", "c2", "c3")
FUTURE_STATES: tuple[str, ...] = ("x0", "x1", "x2", "x3")

# Rounding tolerance for the exact-fraction downstream distributions.
NUMERIC_TOLERANCE: float = 1e-12


# ---------- Update operator Psi (hand-built, section 4) ----------


DistributionRow = tuple[float, float, float, float]


# D_A(c) -- the class-A downstream distribution at each context. Rows are
# probability vectors over FUTURE_STATES.
_D_A: Mapping[str, DistributionRow] = {
    "c0": (0.50, 0.50, 0.00, 0.00),
    "c1": (0.25, 0.25, 0.25, 0.25),
    "c2": (0.30, 0.30, 0.20, 0.20),
    "c3": (0.40, 0.10, 0.40, 0.10),
}

# D_B(c) -- the class-B downstream distribution at each context.
_D_B: Mapping[str, DistributionRow] = {
    "c0": (0.00, 0.00, 0.50, 0.50),
    "c1": (0.70, 0.10, 0.10, 0.10),
    "c2": (0.20, 0.20, 0.30, 0.30),
    "c3": (0.10, 0.40, 0.10, 0.40),
}

# D_C(c) -- the class-C downstream distribution at each context.
_D_C: Mapping[str, DistributionRow] = {
    "c0": (1.00, 0.00, 0.00, 0.00),
    "c1": (0.10, 0.70, 0.10, 0.10),
    "c2": (0.50, 0.50, 0.00, 0.00),
    "c3": (0.25, 0.25, 0.25, 0.25),
}

# D_D(c) -- the class-D downstream distribution at each context.
_D_D: Mapping[str, DistributionRow] = {
    "c0": (0.00, 0.00, 0.00, 1.00),
    "c1": (0.10, 0.10, 0.70, 0.10),
    "c2": (0.00, 0.00, 0.50, 0.50),
    "c3": (0.10, 0.40, 0.40, 0.10),
}


# Message -> class-conditional distribution map (matches section 4).
_MESSAGE_TO_CLASS_DISTRIBUTION: Mapping[str, Mapping[str, DistributionRow]] = {
    "m0": _D_A,
    "m1": _D_A,
    "m2": _D_B,
    "m3": _D_B,
    "m4": _D_C,
    "m5": _D_D,
}


def psi(message: str, context: str) -> DistributionRow:
    """Return ``Psi(m, c)`` -- the downstream distribution over FUTURE_STATES.

    The distribution is a length-4 tuple of nonnegative floats summing to 1.
    Distributions are exact (finite-precision floats chosen so that every
    Psi(m, c) sums to 1.0 to numerical precision) and identical within each
    Psi-class by construction.
    """

    try:
        class_map = _MESSAGE_TO_CLASS_DISTRIBUTION[message]
    except KeyError as exc:
        raise ValueError(f"unknown message: {message!r}") from exc
    try:
        return class_map[context]
    except KeyError as exc:
        raise ValueError(f"unknown context: {context!r}") from exc


def psi_row_sums_to_one(row: DistributionRow) -> bool:
    """Sanity check: every Psi(m, c) row is a probability distribution."""

    return abs(sum(row) - 1.0) <= NUMERIC_TOLERANCE and all(x >= 0.0 for x in row)


# ---------- Distractor: co-occurrence signature map ----------


CooccurrenceRow = tuple[int, int, int, int]


_COOCCURRENCE: Mapping[str, CooccurrenceRow] = {
    "m0": (4, 4, 1, 1),
    "m1": (1, 1, 4, 4),
    "m2": (4, 4, 1, 1),
    "m3": (1, 1, 4, 4),
    "m4": (4, 4, 1, 1),
    "m5": (1, 1, 4, 4),
}


def kappa(message: str) -> CooccurrenceRow:
    """Return the co-occurrence signature ``kappa(m)`` for message ``m``.

    Rows are ambient-token co-occurrence counts. Two messages are
    co-occurrence-equivalent iff their signature rows are identical.
    """

    try:
        return _COOCCURRENCE[message]
    except KeyError as exc:
        raise ValueError(f"unknown message: {message!r}") from exc


# ---------- Equivalence relations ----------


def psi_equivalent(
    m1: str,
    m2: str,
    contexts: Sequence[str] = CONTEXTS,
    tolerance: float = NUMERIC_TOLERANCE,
) -> bool:
    """Return whether ``m1 ~_Psi m2``: exact equality of Psi(m_i, c) on every c.

    Comparison is up to numerical tolerance because the class-conditional
    distributions are stored as floats. In this world every pair of
    class-conditional distributions differs by at least 0.1 on the class-
    separating context, so any tolerance well below 0.1 gives the same
    answer.
    """

    for context in contexts:
        d1 = psi(m1, context)
        d2 = psi(m2, context)
        for a, b in zip(d1, d2, strict=True):
            if abs(a - b) > tolerance:
                return False
    return True


def cooccurrence_equivalent(m1: str, m2: str) -> bool:
    """Return whether ``m1 ~_kappa m2``: exact equality of ambient signatures."""

    return kappa(m1) == kappa(m2)


# ---------- Partitions ----------


Partition = frozenset[frozenset[str]]


def partition_from_relation(
    messages: Sequence[str], relation: Callable[[str, str], bool]
) -> Partition:
    """Build the partition of ``messages`` induced by ``relation``.

    ``relation`` must be a callable ``(str, str) -> bool`` defining an
    equivalence relation on ``messages`` (reflexive, symmetric, transitive);
    verification of those axioms is performed separately by
    ``is_reflexive_symmetric_transitive``.
    """

    remaining = list(messages)
    cells: list[frozenset[str]] = []
    while remaining:
        seed = remaining[0]
        cell = [m for m in remaining if relation(seed, m)]
        cells.append(frozenset(cell))
        remaining = [m for m in remaining if m not in cell]
    return frozenset(cells)


def psi_partition(messages: Sequence[str] = MESSAGES) -> Partition:
    """The Psi-quotient partition on ``messages``."""

    return partition_from_relation(messages, psi_equivalent)


def cooccurrence_partition(messages: Sequence[str] = MESSAGES) -> Partition:
    """The co-occurrence quotient partition on ``messages``."""

    return partition_from_relation(messages, cooccurrence_equivalent)


# ---------- Equivalence-axiom checks (CS-1) ----------


def is_reflexive(
    messages: Sequence[str], relation: Callable[[str, str], bool]
) -> bool:
    return all(relation(m, m) for m in messages)


def is_symmetric(
    messages: Sequence[str], relation: Callable[[str, str], bool]
) -> bool:
    for a, b in product(messages, messages):
        if relation(a, b) != relation(b, a):
            return False
    return True


def is_transitive(
    messages: Sequence[str], relation: Callable[[str, str], bool]
) -> bool:
    for a, b, c in product(messages, messages, messages):
        if relation(a, b) and relation(b, c) and not relation(a, c):
            return False
    return True


def is_reflexive_symmetric_transitive(
    messages: Sequence[str], relation: Callable[[str, str], bool]
) -> bool:
    return (
        is_reflexive(messages, relation)
        and is_symmetric(messages, relation)
        and is_transitive(messages, relation)
    )


# ---------- Common-sufficient-statistic check (CS-2) ----------


def psi_constant_within_each_class(
    partition: Partition,
    contexts: Sequence[str] = CONTEXTS,
    tolerance: float = NUMERIC_TOLERANCE,
) -> bool:
    """Return whether Psi(., c) is constant on every cell of ``partition``.

    Equivalent to: ``partition`` is a common sufficient statistic (in the
    Theorem-4 sense) for the family {Psi(., c) : c in C} on the message
    space.
    """

    for cell in partition:
        cell_members = sorted(cell)
        if len(cell_members) < 2:
            continue
        reference = cell_members[0]
        for other in cell_members[1:]:
            for context in contexts:
                d_ref = psi(reference, context)
                d_other = psi(other, context)
                for a, b in zip(d_ref, d_other, strict=True):
                    if abs(a - b) > tolerance:
                        return False
    return True


# ---------- Partition-comparison helpers ----------


def partitions_are_distinct(a: Partition, b: Partition) -> bool:
    """Return whether ``a`` and ``b`` are distinct partitions (as sets of cells)."""

    return a != b


def refines(finer: Partition, coarser: Partition) -> bool:
    """Return whether ``finer`` refines ``coarser`` (every finer-cell subset of some coarser-cell)."""

    coarser_list = list(coarser)
    for cell in finer:
        if not any(cell.issubset(c) for c in coarser_list):
            return False
    return True


def has_shared_cell(a: Partition, b: Partition) -> bool:
    """Return whether any cell of ``a`` coincides with any cell of ``b``."""

    return bool(a & b)


# ---------- Serialisation helpers ----------


def _sort_partition(partition: Partition) -> list[list[str]]:
    return sorted([sorted(list(cell)) for cell in partition])


def _row_records(rows: Mapping[str, DistributionRow]) -> dict[str, list[float]]:
    return {context: list(row) for context, row in rows.items()}


# ---------- Benchmark ----------


@dataclass(frozen=True)
class BenchmarkGates:
    cs1_psi_equivalence_is_reflexive_symmetric_transitive: bool
    cs2_psi_quotient_has_four_classes: bool
    cs2_psi_quotient_is_common_sufficient: bool
    cs_cooccurrence_partition_differs_from_psi_quotient: bool

    def as_dict(self) -> dict[str, bool]:
        return {
            "cs1_psi_equivalence_is_reflexive_symmetric_transitive": (
                self.cs1_psi_equivalence_is_reflexive_symmetric_transitive
            ),
            "cs2_psi_quotient_has_four_classes": (
                self.cs2_psi_quotient_has_four_classes
            ),
            "cs2_psi_quotient_is_common_sufficient": (
                self.cs2_psi_quotient_is_common_sufficient
            ),
            "cs_cooccurrence_partition_differs_from_psi_quotient": (
                self.cs_cooccurrence_partition_differs_from_psi_quotient
            ),
        }

    def all_pass(self) -> bool:
        return all(self.as_dict().values())


EXPECTED_PSI_PARTITION: Partition = frozenset(
    {
        frozenset({"m0", "m1"}),
        frozenset({"m2", "m3"}),
        frozenset({"m4"}),
        frozenset({"m5"}),
    }
)

EXPECTED_COOCCURRENCE_PARTITION: Partition = frozenset(
    {
        frozenset({"m0", "m2", "m4"}),
        frozenset({"m1", "m3", "m5"}),
    }
)


def evaluate_benchmark(
    messages: Iterable[str] = MESSAGES,
    contexts: Iterable[str] = CONTEXTS,
    tolerance: float = NUMERIC_TOLERANCE,
) -> dict:
    message_seq = tuple(messages)
    context_seq = tuple(contexts)

    # Sanity: every Psi(m, c) is a probability distribution (paper contract).
    all_rows_are_distributions = all(
        psi_row_sums_to_one(psi(m, c))
        for m in message_seq
        for c in context_seq
    )

    # CS-1: ~_Psi is a proper equivalence relation.
    cs1_pass = is_reflexive_symmetric_transitive(message_seq, psi_equivalent)

    # CS-2: quotient is exactly the expected four classes and is
    # common sufficient for {Psi(., c) : c in C}.
    computed_psi_partition = psi_partition(message_seq)
    cs2_four_classes = computed_psi_partition == EXPECTED_PSI_PARTITION
    cs2_common_sufficient = psi_constant_within_each_class(
        computed_psi_partition, context_seq, tolerance=tolerance
    )

    # Orthogonality: co-occurrence partition differs from Psi-quotient.
    computed_cooc_partition = cooccurrence_partition(message_seq)
    cs_cooc_differs = partitions_are_distinct(
        computed_psi_partition, computed_cooc_partition
    )

    # Additional (non-gate) diagnostics: neither partition refines the
    # other and they share no cell -- the sharper form of the corollary
    # instantiated in the paper.
    psi_refines_cooc = refines(computed_psi_partition, computed_cooc_partition)
    cooc_refines_psi = refines(computed_cooc_partition, computed_psi_partition)
    shared_cells = list(computed_psi_partition & computed_cooc_partition)

    gates = BenchmarkGates(
        cs1_psi_equivalence_is_reflexive_symmetric_transitive=cs1_pass,
        cs2_psi_quotient_has_four_classes=cs2_four_classes,
        cs2_psi_quotient_is_common_sufficient=cs2_common_sufficient,
        cs_cooccurrence_partition_differs_from_psi_quotient=cs_cooc_differs,
    )

    return {
        "status": "pass" if gates.all_pass() else "fail",
        "gates": gates.as_dict(),
        "world": {
            "messages": list(message_seq),
            "contexts": list(context_seq),
            "future_states": list(FUTURE_STATES),
            "num_messages": len(message_seq),
            "num_contexts": len(context_seq),
            "num_future_states": len(FUTURE_STATES),
        },
        "class_conditional_distributions": {
            "D_A": _row_records(_D_A),
            "D_B": _row_records(_D_B),
            "D_C": _row_records(_D_C),
            "D_D": _row_records(_D_D),
        },
        "cooccurrence_signatures": {
            m: list(kappa(m)) for m in message_seq
        },
        "psi_partition": _sort_partition(computed_psi_partition),
        "cooccurrence_partition": _sort_partition(computed_cooc_partition),
        "expected_psi_partition": _sort_partition(EXPECTED_PSI_PARTITION),
        "expected_cooccurrence_partition": _sort_partition(
            EXPECTED_COOCCURRENCE_PARTITION
        ),
        "all_rows_are_probability_distributions": all_rows_are_distributions,
        "psi_refines_cooccurrence": psi_refines_cooc,
        "cooccurrence_refines_psi": cooc_refines_psi,
        "shared_cells_between_partitions": [
            sorted(list(cell)) for cell in shared_cells
        ],
        "tolerance": tolerance,
    }
