"""Exact witness of Theorems TA-1 (cocycle iff gluing) and TA-2
(cocycle-failure classifies obstructions) from *The Theory Atlas*
(``papers/theory_atlas/paper.md``).

Setup
-----

The 4-bit Boolean world of Instrument 4.

- ``X = {0, 1}^4`` (16 worlds; uniform base distribution).
- Three context subsets:

  * ``U_1 = { x : x_0 = 0 }`` -- 8 worlds
  * ``U_2 = { x : x_1 = 0 }`` -- 8 worlds
  * ``U_3 = { x : x_2 = 0 }`` -- 8 worlds

- Pairwise overlaps (each 4 worlds):

  * ``U_12 = U_1 ∩ U_2 = { x_0 = x_1 = 0 }``
  * ``U_13 = U_1 ∩ U_3 = { x_0 = x_2 = 0 }``
  * ``U_23 = U_2 ∩ U_3 = { x_1 = x_2 = 0 }``

- Triple overlap ``U_123 = { x_0 = x_1 = x_2 = 0 }`` (2 worlds).

Target label space
------------------

``T = Z/4 = {0, 1, 2, 3}``. Transitions ``T_ij : T -> T`` are permutations
of ``T`` (bijections on the label alphabet).

Underlying observable ``g(x) = (2 * x[2] + x[3]) mod 4`` on ``X``,
valued in ``T``.

Chart maps ``M_i : U_i -> T`` (same in both families)
-----------------------------------------------------

- ``M_1(x) = g(x)`` on ``U_1`` (identity presentation on chart 1).
- ``M_2(x) = (g(x) + 1) mod 4`` on ``U_2`` (shift-by-1 presentation).
- ``M_3(x) = (g(x) + 2) mod 4`` on ``U_3`` (shift-by-2 presentation).

The chart maps are *identical* between the good and bad families. The two
families differ only in the transition tables ``T_ij``, which are the
part of the presheaf-of-theories that carries the gluing information.

Good charts (cocycle holds)
---------------------------

Transitions match the shifts implied by the chart presentations:

- ``T_12(a) = (a + 1) mod 4`` (chart-1 -> chart-2)
- ``T_23(a) = (a + 1) mod 4`` (chart-2 -> chart-3)
- ``T_13(a) = (a + 2) mod 4`` (chart-1 -> chart-3)

Cocycle: ``T_23(T_12(a)) = (a + 1) + 1 = a + 2 = T_13(a)`` for all
``a`` in ``T``. Holds exactly.

Bad charts (cocycle fails; missing-latent signature)
----------------------------------------------------

Same chart maps ``M_i``. Transitions altered so that the composition
around the loop drifts:

- ``T_12(a) = (a + 1) mod 4``
- ``T_23(a) = (a + 1) mod 4``
- ``T_13(a) = (a + 3) mod 4``  # "should" be (a + 2) for consistency

Cocycle discrepancy: ``D(a) = T_13^{-1}(T_23(T_12(a))) - a``, a
permutation of ``T``. Concretely ``D`` is the shift-by-``(2 - 3) mod 4
= 3``, which has no fixed points: ``rank(D) = 4``.

All three transitions are non-identity (each carries a non-zero shift),
so the discrepancy is *spread across all pairwise overlaps* -- the
missing-latent signature of Theorem TA-2. In contrast, a
phase/boundary transition would have exactly one non-identity ``T_ij``
with the other two trivial: the failure would be *localised to one
overlap*.

Predictions (pre-registered)
----------------------------

- ``ta1_good_charts_satisfy_cocycle``: for every triple ``(i, j, k)``,
  the composed transition equals the direct transition.
- ``ta1_bad_charts_violate_cocycle``: at least one triple has non-zero
  discrepancy.
- ``ta1_glue_iff_cocycle``: good charts admit a global theory (unique
  up to relabelling of ``T``); bad charts do not.
- ``ta2_bad_discrepancy_matches_missing_latent_signature``: bad-case
  discrepancy is spread across all three pairwise overlaps (all three
  ``T_ij`` non-identity) and non-trivial (``rank >= 1``), distinguishing
  it from a boundary/phase-transition signature (rank >= 1 on the loop
  but only one ``T_ij`` non-identity).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from itertools import combinations, product
from typing import cast

World = tuple[int, int, int, int]
Label = int

N_BITS: int = 4
TARGET_SIZE: int = 4
TARGET: tuple[int, ...] = tuple(range(TARGET_SIZE))


# ---------- World and contexts ----------


def all_worlds() -> list[World]:
    return [cast(World, tuple(bits)) for bits in product((0, 1), repeat=N_BITS)]


def context_U1(worlds: Iterable[World]) -> tuple[World, ...]:
    return tuple(w for w in worlds if w[0] == 0)


def context_U2(worlds: Iterable[World]) -> tuple[World, ...]:
    return tuple(w for w in worlds if w[1] == 0)


def context_U3(worlds: Iterable[World]) -> tuple[World, ...]:
    return tuple(w for w in worlds if w[2] == 0)


CONTEXT_INDICES: tuple[int, ...] = (1, 2, 3)


def contexts(worlds: Sequence[World]) -> dict[int, tuple[World, ...]]:
    return {
        1: context_U1(worlds),
        2: context_U2(worlds),
        3: context_U3(worlds),
    }


def pairwise_overlap(
    ctxs: Mapping[int, Sequence[World]], i: int, j: int
) -> tuple[World, ...]:
    left = set(ctxs[i])
    return tuple(w for w in ctxs[j] if w in left)


def triple_overlap(
    ctxs: Mapping[int, Sequence[World]], i: int, j: int, k: int
) -> tuple[World, ...]:
    left = set(ctxs[i])
    middle = set(ctxs[j])
    return tuple(w for w in ctxs[k] if w in left and w in middle)


def context_union(ctxs: Mapping[int, Sequence[World]]) -> tuple[World, ...]:
    seen: set[World] = set()
    out: list[World] = []
    for idx in sorted(ctxs):
        for w in ctxs[idx]:
            if w not in seen:
                seen.add(w)
                out.append(w)
    return tuple(out)


# ---------- Underlying observable and chart maps ----------


def observable_g(world: World) -> Label:
    return (2 * world[2] + world[3]) % TARGET_SIZE


def chart_M(chart_index: int, world: World) -> Label:
    """M_i : U_i -> T for the paper's fixed chart presentation.

    The chart maps are the same across the good and bad families; only the
    transitions differ."""
    if chart_index == 1:
        return observable_g(world)
    if chart_index == 2:
        return (observable_g(world) + 1) % TARGET_SIZE
    if chart_index == 3:
        return (observable_g(world) + 2) % TARGET_SIZE
    raise ValueError(f"unknown chart index: {chart_index}")


# ---------- Permutations on the target label space ----------


@dataclass(frozen=True)
class Permutation:
    """A permutation of ``T`` stored as a tuple ``sigma[a] = image``."""

    name: str
    table: tuple[int, ...] = field(compare=True)

    def __post_init__(self) -> None:  # pragma: no cover - construction guard
        assert sorted(self.table) == list(range(len(self.table))), (
            f"Permutation {self.name!r} is not a bijection on T: {self.table}"
        )

    def apply(self, a: int) -> int:
        return self.table[a]

    def inverse(self) -> "Permutation":
        n = len(self.table)
        inv: list[int] = [0] * n
        for src, dst in enumerate(self.table):
            inv[dst] = src
        return Permutation(name=f"{self.name}^-1", table=tuple(inv))

    def compose(self, other: "Permutation") -> "Permutation":
        """Return self ∘ other, i.e. ``a -> self(other(a))``."""
        return Permutation(
            name=f"{self.name}∘{other.name}",
            table=tuple(self.table[other.table[a]] for a in range(len(self.table))),
        )

    def rank(self) -> int:
        """Number of moved elements (`|{a : sigma(a) != a}|`)."""
        return sum(1 for a, sigma_a in enumerate(self.table) if sigma_a != a)

    def is_identity(self) -> bool:
        return self.rank() == 0


def identity_perm(n: int = TARGET_SIZE) -> Permutation:
    return Permutation(name="id", table=tuple(range(n)))


def shift_perm(k: int, n: int = TARGET_SIZE) -> Permutation:
    """Cyclic shift by ``k`` on Z/n."""
    normalised = k % n
    return Permutation(
        name=f"+{normalised}", table=tuple((a + normalised) % n for a in range(n))
    )


# ---------- Chart family (charts + transitions) ----------


TransitionKey = tuple[int, int]


@dataclass(frozen=True)
class ChartFamily:
    name: str
    chart_map: Callable[[int, World], Label]
    transitions: Mapping[TransitionKey, Permutation]

    def transition(self, i: int, j: int) -> Permutation:
        return self.transitions[(i, j)]


def good_family() -> ChartFamily:
    """Cocycle holds: shifts (+1, +1, +2) close consistently."""
    return ChartFamily(
        name="good",
        chart_map=chart_M,
        transitions={
            (1, 2): shift_perm(1),
            (2, 3): shift_perm(1),
            (1, 3): shift_perm(2),
        },
    )


def bad_family() -> ChartFamily:
    """Cocycle fails; all three T_ij are non-identity (spread signature)."""
    return ChartFamily(
        name="bad",
        chart_map=chart_M,
        transitions={
            (1, 2): shift_perm(1),
            (2, 3): shift_perm(1),
            (1, 3): shift_perm(3),
        },
    )


def phase_boundary_family() -> ChartFamily:
    """Reference family for taxonomy contrast: only one non-identity T_ij.

    Cocycle fails, but the failure is *localised* to T_12 alone (T_23 and
    T_13 are both the identity). Used to verify Theorem TA-2's rank/
    support classification distinguishes phase-boundary from missing-
    latent signatures. Not itself gated -- present so that the taxonomy
    check has both regimes to compare against.
    """
    return ChartFamily(
        name="phase_boundary",
        chart_map=chart_M,
        transitions={
            (1, 2): shift_perm(1),
            (2, 3): identity_perm(),
            (1, 3): identity_perm(),
        },
    )


# ---------- Cocycle discrepancy ----------


def cocycle_discrepancy(family: ChartFamily, i: int, j: int, k: int) -> Permutation:
    """T_ik^{-1} ∘ T_jk ∘ T_ij as a permutation on the target alphabet.

    Identity iff the cocycle ``T_jk ∘ T_ij = T_ik`` holds on the triple.
    Its rank / support carries the obstruction taxonomy of Theorem TA-2.
    """
    T_ij = family.transition(i, j)
    T_jk = family.transition(j, k)
    T_ik = family.transition(i, k)
    return T_ik.inverse().compose(T_jk.compose(T_ij))


def cocycle_holds_on_triple(
    family: ChartFamily, i: int, j: int, k: int
) -> bool:
    return cocycle_discrepancy(family, i, j, k).is_identity()


def all_triples(indices: Sequence[int] = CONTEXT_INDICES) -> list[tuple[int, int, int]]:
    out: list[tuple[int, int, int]] = []
    for combo in combinations(indices, 3):
        ordered = sorted(combo)
        out.append((ordered[0], ordered[1], ordered[2]))
    return out


def cocycle_holds_all_triples(family: ChartFamily) -> bool:
    return all(
        cocycle_holds_on_triple(family, i, j, k) for i, j, k in all_triples()
    )


# ---------- Gluing attempt ----------


def _target_iter() -> Sequence[int]:
    return TARGET


def glue_attempt(
    family: ChartFamily,
    worlds: Sequence[World],
) -> dict:
    """Try to construct a global theory ``M : union(U_i) -> T`` by pivoting
    through chart 1.

    Fix ``psi_1 = identity``; set ``psi_i := T_1i^{-1}`` for ``i > 1`` --
    the natural chart-1-pivot choice implied by the transitions
    (``M(x) = psi_i(M_i(x))`` and ``T_ij = psi_j^{-1} ∘ psi_i`` give
    ``psi_i = T_1i^{-1}``). Define ``M(x) := psi_i(M_i(x))`` for any
    ``i`` with ``x in U_i``. Consistency: on the pairwise overlap
    ``U_ij`` the two candidate values must agree.

    Returns a dict with the constructed ``M`` (if consistent) and the list
    of inconsistent worlds. ``consistent`` iff no inconsistencies were
    detected.
    """

    ctxs = contexts(worlds)
    psi: dict[int, Permutation] = {1: identity_perm()}
    for i in CONTEXT_INDICES:
        if i == 1:
            continue
        psi[i] = family.transition(1, i).inverse()

    candidates: dict[World, dict[int, int]] = {}
    for i in CONTEXT_INDICES:
        for w in ctxs[i]:
            value = psi[i].apply(family.chart_map(i, w))
            candidates.setdefault(w, {})[i] = value

    inconsistent: list[dict[str, object]] = []
    M: dict[World, int] = {}
    for w, per_chart in candidates.items():
        values = set(per_chart.values())
        if len(values) > 1:
            inconsistent.append(
                {
                    "world": list(w),
                    "per_chart": {str(i): v for i, v in per_chart.items()},
                }
            )
        M[w] = next(iter(values)) if len(values) == 1 else -1

    consistent = not inconsistent
    return {
        "consistent": consistent,
        "psi": {i: list(psi[i].table) for i in psi},
        "M": {"".join(str(b) for b in w): v for w, v in M.items()},
        "inconsistent_worlds": inconsistent,
    }


# ---------- Taxonomy of cocycle failure ----------


def transition_support_report(family: ChartFamily) -> dict[str, object]:
    """Which pairwise transitions are non-identity? Reports rank per edge."""

    report: dict[str, object] = {}
    per_edge: dict[str, int] = {}
    non_identity_edges: list[str] = []
    for (i, j), sigma in sorted(family.transitions.items()):
        edge = f"T_{i}{j}"
        per_edge[edge] = sigma.rank()
        if not sigma.is_identity():
            non_identity_edges.append(edge)
    report["per_edge_rank"] = per_edge
    report["non_identity_edges"] = non_identity_edges
    report["num_non_identity_edges"] = len(non_identity_edges)
    report["num_edges"] = len(family.transitions)
    return report


def taxonomy_verdict(family: ChartFamily) -> str:
    """Classify a family's obstruction by Theorem TA-2's rank / support rule.

    * ``glue``: cocycle holds on every triple (discrepancy rank 0 everywhere).
    * ``phase_transition``: at least one triple has rank >= 1 and the
      non-identity transitions are supported on a strict subset of the
      pairwise overlaps (the discrepancy is *localised*).
    * ``missing_latent``: at least one triple has rank >= 1 and every
      pairwise transition is non-identity (the discrepancy is *spread*
      across all overlaps).
    """
    if cocycle_holds_all_triples(family):
        return "glue"
    support = transition_support_report(family)
    n_non_id = cast(int, support["num_non_identity_edges"])
    n_edges = cast(int, support["num_edges"])
    if n_non_id < n_edges:
        return "phase_transition"
    return "missing_latent"


def triple_records(family: ChartFamily) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for i, j, k in all_triples():
        disc = cocycle_discrepancy(family, i, j, k)
        out.append(
            {
                "triple": [i, j, k],
                "discrepancy_table": list(disc.table),
                "discrepancy_rank": disc.rank(),
                "cocycle_holds": disc.is_identity(),
            }
        )
    return out


# ---------- Benchmark ----------


def evaluate_family(family: ChartFamily, worlds: Sequence[World]) -> dict[str, object]:
    triples = triple_records(family)
    support = transition_support_report(family)
    verdict = taxonomy_verdict(family)
    glue = glue_attempt(family, worlds)
    return {
        "family": family.name,
        "transitions": {
            f"T_{i}{j}": list(sigma.table)
            for (i, j), sigma in sorted(family.transitions.items())
        },
        "triples": triples,
        "transition_support": support,
        "taxonomy_verdict": verdict,
        "glue_attempt_consistent": glue["consistent"],
        "glue_attempt_num_inconsistent_worlds": len(glue["inconsistent_worlds"]),
        "glue_attempt": glue,
    }


def evaluate_benchmark() -> dict:
    worlds = all_worlds()
    ctxs = contexts(worlds)

    context_sizes = {i: len(ctxs[i]) for i in CONTEXT_INDICES}
    pair_sizes = {
        f"U_{i}{j}": len(pairwise_overlap(ctxs, i, j))
        for i, j in combinations(CONTEXT_INDICES, 2)
    }
    triple_size = len(triple_overlap(ctxs, *CONTEXT_INDICES))
    union_size = len(context_union(ctxs))

    good = good_family()
    bad = bad_family()
    phase = phase_boundary_family()

    good_record = evaluate_family(good, worlds)
    bad_record = evaluate_family(bad, worlds)
    phase_record = evaluate_family(phase, worlds)

    # --- Gates ---

    ta1_good_charts_satisfy_cocycle = cocycle_holds_all_triples(good)
    ta1_bad_charts_violate_cocycle = not cocycle_holds_all_triples(bad)
    ta1_glue_iff_cocycle = (
        cast(bool, good_record["glue_attempt_consistent"]) is True
        and cast(bool, bad_record["glue_attempt_consistent"]) is False
    )

    ta2_bad_discrepancy_matches_missing_latent_signature = (
        cast(str, bad_record["taxonomy_verdict"]) == "missing_latent"
        and cast(str, phase_record["taxonomy_verdict"]) == "phase_transition"
        and cast(str, good_record["taxonomy_verdict"]) == "glue"
    )

    gates = {
        "ta1_good_charts_satisfy_cocycle": ta1_good_charts_satisfy_cocycle,
        "ta1_bad_charts_violate_cocycle": ta1_bad_charts_violate_cocycle,
        "ta1_glue_iff_cocycle": ta1_glue_iff_cocycle,
        "ta2_bad_discrepancy_matches_missing_latent_signature": (
            ta2_bad_discrepancy_matches_missing_latent_signature
        ),
    }
    status = "pass" if all(gates.values()) else "fail"

    return {
        "status": status,
        "gates": gates,
        "world": {
            "n_bits": N_BITS,
            "target_size": TARGET_SIZE,
            "context_indices": list(CONTEXT_INDICES),
            "context_sizes": context_sizes,
            "pairwise_overlap_sizes": pair_sizes,
            "triple_overlap_size": triple_size,
            "context_union_size": union_size,
        },
        "families": {
            "good": good_record,
            "bad": bad_record,
            "phase_boundary_reference": phase_record,
        },
    }
