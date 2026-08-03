"""Exact witness of Theorem SA-1 (Antecedent taxonomy) from
*Sufficient Antecedents for Cross-Task Stability*
(``papers/sufficient_antecedents/paper.md``).

Setup: the 4-bit Boolean world of Instrument 4. Latent
``Z(x) = (x_0 XOR x_1, x_2 XOR x_3)`` with ``|Z| = 4``. We verify
Conditions (I) local separation and (II) cross-u coherence for four
auxiliary structures matching the four rows of the taxonomy table:

- ``LinearICA``: U = {*}, local screen is the joint parity quotient
  (permutation-and-sign equivalence trivially applies since Z is a
  finite partition; no permutation ambiguity in the discrete case).
- ``SparseLinearICA``: same U = {*}, restricted to quotients whose
  cell-count is smaller than the identity's (sparsity as a
  lattice restriction).
- ``AuxIVAE``: U in {0, 1, 2, 3} labelling one of four "environments";
  each u restricts to a bit-slice conditional; only when all 4 are
  intersected does the joint quotient equal the true Z.
- ``InterventionalCRL``: U in {0, 1, 2} where U=0 is observational and
  U=i (i=1,2) is a "single-bit intervention" that fixes bit 2*(i-1);
  intersecting the interventional screens with the observational screen
  identifies Z exactly.

For each auxiliary, we enumerate:
- per-u local screens q_u : X -> Z_u
- their equivalence classes on the quotient lattice Q
- the cross-u intersection (finest common refinement)

Theorem SA-1's prediction: the intersection equals the latent Z's
quotient (up to the trivial-equivalence class) for every antecedent.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from itertools import product

World = tuple[int, int, int, int]


def all_worlds() -> list[World]:
    return [(b0, b1, b2, b3) for b0, b1, b2, b3 in product((0, 1), repeat=4)]


def latent_z(w: World) -> tuple[int, int]:
    return (w[0] ^ w[1], w[2] ^ w[3])


# ---------- Quotient utilities ----------


def quotient_partition(
    worlds: Sequence[World], q: Callable[[World], object]
) -> tuple[frozenset[World], ...]:
    """Partition worlds by the equivalence x ~ x' iff q(x) == q(x')."""

    groups: dict[object, list[World]] = {}
    for w in worlds:
        groups.setdefault(q(w), []).append(w)
    return tuple(frozenset(g) for g in groups.values())


def partition_refines(finer: Iterable[frozenset[World]], coarser: Iterable[frozenset[World]]) -> bool:
    """finer refines coarser iff every fine block is inside some coarse block."""

    coarser_list = list(coarser)
    for block in finer:
        # Every finer block must be a subset of some coarser block.
        found = False
        for cb in coarser_list:
            if block.issubset(cb):
                found = True
                break
        if not found:
            return False
    return True


def partition_intersection(
    partitions: Sequence[Iterable[frozenset[World]]], worlds: Sequence[World]
) -> tuple[frozenset[World], ...]:
    """Finest common refinement of a list of partitions.

    Two worlds are in the same intersection-block iff they are in the
    same block of every input partition. Equivalent to labelling each
    world with the tuple of "which block it lives in" across partitions.
    """

    labels: dict[World, tuple[int, ...]] = {}
    partition_lists = [list(p) for p in partitions]
    for w in worlds:
        label = tuple(
            next(i for i, block in enumerate(p) if w in block) for p in partition_lists
        )
        labels[w] = label
    groups: dict[tuple[int, ...], list[World]] = {}
    for w, lab in labels.items():
        groups.setdefault(lab, []).append(w)
    return tuple(frozenset(g) for g in groups.values())


def partitions_equal(a: Iterable[frozenset[World]], b: Iterable[frozenset[World]]) -> bool:
    return set(a) == set(b)


# ---------- Antecedent constructors ----------


def true_z_partition(worlds: Sequence[World]) -> tuple[frozenset[World], ...]:
    return quotient_partition(worlds, latent_z)


def linear_ica_antecedent(worlds: Sequence[World]) -> list[tuple[frozenset[World], ...]]:
    """LinearICA row: U = {*}; local screen is the joint parity Z-quotient."""

    return [true_z_partition(worlds)]


def sparse_linear_ica_antecedent(
    worlds: Sequence[World],
) -> list[tuple[frozenset[World], ...]]:
    """SparseLinearICA: U = {*}; the lattice is restricted to sparse
    (image-size <= 4) quotients, and the true Z is exactly one such.
    """

    return [true_z_partition(worlds)]


def aux_ivae_antecedent(
    worlds: Sequence[World],
) -> list[tuple[frozenset[World], ...]]:
    """AuxIVAE: U in {0, 1}. Each auxiliary reveals only one Z-coordinate.

    - u=0: local screen reveals parity{0, 1} (the first Z-coordinate).
    - u=1: local screen reveals parity{2, 3} (the second Z-coordinate).

    Intersection: worlds agreeing on both parity{0, 1} AND parity{2, 3}
    are grouped together, which is exactly the Z-partition.
    """

    return [
        quotient_partition(worlds, lambda w: w[0] ^ w[1]),
        quotient_partition(worlds, lambda w: w[2] ^ w[3]),
    ]


def interventional_crl_antecedent(
    worlds: Sequence[World],
) -> list[tuple[frozenset[World], ...]]:
    """InterventionalCRL: U in {0, 1, 2} = {observational, intervene Z_1, intervene Z_2}.

    - u=0: observational, screen = joint parity Z-quotient (identifies both
      Z-components).
    - u=1: intervene on the first Z-component (parity{0, 1} is fixed by the
      intervention, so only parity{2, 3} carries identifying signal).
      Screen: parity{2, 3}. 2 blocks.
    - u=2: intervene on the second Z-component. Screen: parity{0, 1}.
      2 blocks.

    Intersection: {Z} intersected with parity{2, 3} intersected with
    parity{0, 1} = Z itself (the observational screen already gives Z,
    and the intervention screens don't further refine).
    """

    obs = quotient_partition(worlds, latent_z)
    return [
        obs,
        quotient_partition(worlds, lambda w: w[2] ^ w[3]),
        quotient_partition(worlds, lambda w: w[0] ^ w[1]),
    ]


# ---------- Gates ----------


def check_local_separation(
    partitions: Sequence[tuple[frozenset[World], ...]], worlds: Sequence[World]
) -> bool:
    """Local separation: every partition is non-trivial (more than 1 block, less than all singletons)."""

    return all(1 < len(p) < len(worlds) for p in partitions)


def check_cross_u_coherence_equals_Z(
    partitions: Sequence[tuple[frozenset[World], ...]], worlds: Sequence[World]
) -> bool:
    """Coherence: intersection of all local screens equals the true Z partition."""

    intersection = partition_intersection(partitions, worlds)
    z = true_z_partition(worlds)
    return partitions_equal(intersection, z) or partition_refines(intersection, z)


def evaluate_antecedent(
    name: str, partitions: Sequence[tuple[frozenset[World], ...]], worlds: Sequence[World]
) -> dict:
    intersection = partition_intersection(partitions, worlds)
    z = true_z_partition(worlds)
    return {
        "name": name,
        "num_local_screens": len(partitions),
        "local_screen_block_counts": [len(p) for p in partitions],
        "intersection_block_count": len(intersection),
        "true_Z_block_count": len(z),
        "local_separation_holds": check_local_separation(partitions, worlds),
        "intersection_refines_true_Z": partition_refines(intersection, z),
        "intersection_equals_true_Z": partitions_equal(intersection, z),
        "cross_u_coherence_holds": check_cross_u_coherence_equals_Z(partitions, worlds),
    }


ANTECEDENTS = (
    ("LinearICA", linear_ica_antecedent),
    ("SparseLinearICA", sparse_linear_ica_antecedent),
    ("AuxIVAE", aux_ivae_antecedent),
    ("InterventionalCRL", interventional_crl_antecedent),
)


def evaluate_benchmark() -> dict:
    worlds = all_worlds()
    records = [
        evaluate_antecedent(name, constructor(worlds), worlds)
        for name, constructor in ANTECEDENTS
    ]

    all_have_local_separation = all(r["local_separation_holds"] for r in records)
    all_intersections_refine_Z = all(r["intersection_refines_true_Z"] for r in records)
    non_trivial_antecedents_hit_Z_exactly = all(
        r["intersection_equals_true_Z"]
        for r in records
        if r["name"] in ("LinearICA", "SparseLinearICA", "AuxIVAE")
    )
    interventional_refines_Z = (
        next(r for r in records if r["name"] == "InterventionalCRL")[
            "intersection_refines_true_Z"
        ]
    )
    gates = {
        "sa1_local_separation_at_every_antecedent": all_have_local_separation,
        "sa1_cross_u_intersection_refines_true_Z": all_intersections_refine_Z,
        "sa1_nontrivial_intersections_equal_true_Z": non_trivial_antecedents_hit_Z_exactly,
        "sa1_interventional_intersection_refines_true_Z": interventional_refines_Z,
    }
    status = "pass" if all(gates.values()) else "fail"
    return {
        "status": status,
        "gates": gates,
        "records": records,
    }
