"""US-4′ lowest bound: does truncated fiber mass, not shortest depth,
govern Gibbs access on the variable-``x`` EML language?

The monomial toy had extra shells that moved mass by many bits.  EML
has no degree key, so the spectrum is the enumerated census from
``experiments/eml_variable_spectrum`` (``k ≤ 5``, 3238 trees).

Two competing predictors, computed exactly on that truncated language
under ``π(t) ∝ 4^{-|t|}``:

- Shortest-only ``Q(z)``: one unit of mass at ``min_nodes(z)``.
  Every fiber with the same shortest depth is equally accessible.
- Fiber mass ``P(z) = Φ_z / Z``: every enumerated inhabitant counts.

Banked if they disagree at fixed min-size.  The registered witness is
the identically-zero function
``eml(a, eml(eml(a,1),1)) = 0`` for ``a ∈ {1,x}`` (two size-3 formulas)
versus a size-3 singleton constant.

Withheld
--------
Master-formula gradient recovery (Odrzywołek Outcome A).  Extra-shell
transfer from the Sq toy — at this bound extra shells add < 1% mass.
Identity of functions from the 6-point grid, except the exact zero
identity used as a control.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Literal, TypedDict

from experiments.eml_variable_spectrum.core import (
    MAX_INTERNAL,
    TEST_GRID,
    VarTree,
    enumerate_trees,
    eval_at,
    eval_grid,
    labeled_count,
    numerical_fiber_id,
    parse_var,
    require_finite,
)

EXPERIMENT_ID = "eml_us4_prime"
RUN_ID = "eml_us4_prime_2026_08_17"
PRODUCING_AGENT = "Cursor Grok 4.6 (cloud agent, under J. Brown direction)"
SESSION_REF = "bc-01a00d99-d2d8-7c5e-a8d0-d0090dfd7bdd"

GIBBS_BASE = 4
HEADLINE_MIN_INTERNAL = 3
MIN_SPLIT_RATIO = 2.0
MAX_EXTRA_SHELL_FACTOR = 1.05
ZERO_LEFT = "eml(1,eml(eml(1,1),1))"
ZERO_RIGHT = "eml(x,eml(eml(x,1),1))"
SINGLETON_CONSTANT = "eml(1,eml(1,eml(1,1)))"

GRID_DISCLOSURE = (
    "Rounded 6-point tuples are a clustering, not identity of functions. "
    "The zero fiber is an exact algebraic identity, not a grid collision: "
    "eml(a, eml(eml(a,1),1)) = 0 for a in {1,x}."
)
GRADIENT_WITHHELD = (
    "Master-formula gradient recovery (Odrzywołek Outcome A) is untested. "
    "This package asks whether truncated Gibbs mass, not shortest depth, "
    "governs sampler access on the enumerated language."
)
EXTRA_SHELL_NOTE = (
    "At k≤5, extra shells add less than 1% mass to the fattest finite "
    "fiber. The Sq-toy extra-shell mechanism does not transfer at this "
    "bound. The mass split is min-shell multiplicity."
)


def tree_mass(n_internal: int) -> float:
    return float(GIBBS_BASE ** (-(2 * n_internal + 1)))


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


class FiberRow(TypedDict):
    fiber_id: str
    n_trees: int
    min_internal: int
    n_min_shell: int
    n_sizes: int
    phi: float
    shortest_only: float
    extra_shell_factor: float
    example: str


class SplitRow(TypedDict):
    min_internal: int
    fat_example: str
    thin_example: str
    fat_phi: float
    thin_phi: float
    ratio: float
    fat_n_min_shell: int
    thin_n_min_shell: int


class ZeroWitness(TypedDict):
    left: str
    right: str
    exact_zero: bool
    n_internal: int


class RegisteredConfig(TypedDict):
    max_internal: int
    gibbs_base: int
    headline_min_internal: int
    min_split_ratio: float
    max_extra_shell_factor: float
    grid: list[float]
    count_formula: str


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    registered: RegisteredConfig
    n_trees: int
    n_finite_fibers: int
    language_z: float
    headline_split: SplitRow
    zero_witness: ZeroWitness
    n_same_minsize_splits: int
    n_size_class_inversions: int
    max_extra_shell_factor: float
    extra_shell_note: str
    gates: dict[str, bool]
    grid_disclosure: str
    untested: dict[str, str]
    withheld: list[str]
    citations: list[str]


def _is_finite_id(fiber_id: str) -> bool:
    return "undef" not in fiber_id


def _zero_witness() -> ZeroWitness:
    left = parse_var(ZERO_LEFT)
    right = parse_var(ZERO_RIGHT)
    exact = True
    for x_val in TEST_GRID:
        left_val = require_finite(eval_at(left, x_val), f"{ZERO_LEFT}@{x_val}")
        right_val = require_finite(eval_at(right, x_val), f"{ZERO_RIGHT}@{x_val}")
        if not math.isclose(left_val, 0.0, rel_tol=0.0, abs_tol=1e-12):
            exact = False
        if not math.isclose(right_val, 0.0, rel_tol=0.0, abs_tol=1e-12):
            exact = False
    return {
        "left": ZERO_LEFT,
        "right": ZERO_RIGHT,
        "exact_zero": exact and left.n_internal == right.n_internal == 3,
        "n_internal": 3,
    }


def _collect_fibers(
    by_size: dict[int, tuple[VarTree, ...]],
) -> list[FiberRow]:
    grouped: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for n_internal, trees in by_size.items():
        for tree in trees:
            grouped[numerical_fiber_id(eval_grid(tree))].append((n_internal, tree.pretty()))
    rows: list[FiberRow] = []
    for fiber_id, members in grouped.items():
        sizes = [n_internal for n_internal, _pretty in members]
        min_internal = min(sizes)
        n_min = sum(1 for n_internal in sizes if n_internal == min_internal)
        phi = sum(tree_mass(n_internal) for n_internal in sizes)
        shortest = n_min * tree_mass(min_internal)
        extra = phi / shortest if shortest > 0.0 else 1.0
        rows.append(
            {
                "fiber_id": fiber_id,
                "n_trees": len(members),
                "min_internal": min_internal,
                "n_min_shell": n_min,
                "n_sizes": len(set(sizes)),
                "phi": phi,
                "shortest_only": shortest,
                "extra_shell_factor": extra,
                "example": members[0][1],
            }
        )
    rows.sort(key=lambda row: (row["min_internal"], -row["phi"], row["fiber_id"]))
    return rows


def _headline_split(finite: list[FiberRow]) -> SplitRow:
    cohort = [row for row in finite if row["min_internal"] == HEADLINE_MIN_INTERNAL]
    if len(cohort) < 2:
        raise ValueError("headline min-size class has fewer than two finite fibers")
    fat = max(cohort, key=lambda row: row["phi"])
    thin = min(cohort, key=lambda row: row["phi"])
    return {
        "min_internal": HEADLINE_MIN_INTERNAL,
        "fat_example": fat["example"],
        "thin_example": thin["example"],
        "fat_phi": fat["phi"],
        "thin_phi": thin["phi"],
        "ratio": fat["phi"] / thin["phi"] if thin["phi"] > 0.0 else 0.0,
        "fat_n_min_shell": fat["n_min_shell"],
        "thin_n_min_shell": thin["n_min_shell"],
    }


def _same_minsize_splits(finite: list[FiberRow]) -> list[SplitRow]:
    by_min: dict[int, list[FiberRow]] = defaultdict(list)
    for row in finite:
        by_min[row["min_internal"]].append(row)
    splits: list[SplitRow] = []
    for min_internal, cohort in sorted(by_min.items()):
        if len(cohort) < 2:
            continue
        fat = max(cohort, key=lambda row: row["phi"])
        thin = min(cohort, key=lambda row: row["phi"])
        if thin["phi"] <= 0.0:
            continue
        ratio = fat["phi"] / thin["phi"]
        if ratio >= MIN_SPLIT_RATIO:
            splits.append(
                {
                    "min_internal": min_internal,
                    "fat_example": fat["example"],
                    "thin_example": thin["example"],
                    "fat_phi": fat["phi"],
                    "thin_phi": thin["phi"],
                    "ratio": ratio,
                    "fat_n_min_shell": fat["n_min_shell"],
                    "thin_n_min_shell": thin["n_min_shell"],
                }
            )
    return splits


def _size_class_inversions(finite: list[FiberRow]) -> int:
    count = 0
    for left in finite:
        for right in finite:
            if left["min_internal"] < right["min_internal"] and left["phi"] < right["phi"]:
                count += 1
    return count


def evaluate_benchmark() -> BenchmarkPayload:
    by_size = enumerate_trees(MAX_INTERNAL)
    tree_counts = {n_internal: len(trees) for n_internal, trees in by_size.items()}
    n_trees = sum(tree_counts.values())
    enumeration_complete = all(
        tree_counts[n_internal] == labeled_count(n_internal)
        for n_internal in range(MAX_INTERNAL + 1)
    )
    language_z = sum(
        labeled_count(n_internal) * tree_mass(n_internal)
        for n_internal in range(MAX_INTERNAL + 1)
    )
    rows = _collect_fibers(by_size)
    finite = [row for row in rows if _is_finite_id(row["fiber_id"])]
    splits = _same_minsize_splits(finite)
    headline = _headline_split(finite)
    zero = _zero_witness()
    inversions = _size_class_inversions(finite)
    extra_factors = [row["extra_shell_factor"] for row in finite]
    max_extra = max(extra_factors) if extra_factors else 1.0
    singleton = parse_var(SINGLETON_CONSTANT)
    singleton_ok = singleton.n_internal == 3 and all(
        eval_at(singleton, x_val) is not None for x_val in TEST_GRID
    )
    shortest_flat_fails = (
        headline["ratio"] >= MIN_SPLIT_RATIO
        and headline["fat_n_min_shell"] > headline["thin_n_min_shell"]
    )
    required = {
        "US4P_ENUMERATION_INHERITED": enumeration_complete and n_trees == 3238,
        "US4P_ZERO_IDENTITY": zero["exact_zero"],
        "US4P_SAME_MINSIZE_SPLIT": headline["ratio"] >= MIN_SPLIT_RATIO and singleton_ok,
        "US4P_SHORTEST_DOES_NOT_DETERMINE_P": shortest_flat_fails,
        "US4P_GRID_DISCLOSED": True,
        "US4P_GRADIENT_WITHHELD": True,
    }
    return {
        "status": "pass" if all(required.values()) else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {
            "identity": PRODUCING_AGENT,
            "session_ref": SESSION_REF,
        },
        "registered": {
            "max_internal": MAX_INTERNAL,
            "gibbs_base": GIBBS_BASE,
            "headline_min_internal": HEADLINE_MIN_INTERNAL,
            "min_split_ratio": MIN_SPLIT_RATIO,
            "max_extra_shell_factor": MAX_EXTRA_SHELL_FACTOR,
            "grid": list(TEST_GRID),
            "count_formula": "2^{k+1} C_k",
        },
        "n_trees": n_trees,
        "n_finite_fibers": len(finite),
        "language_z": language_z,
        "headline_split": headline,
        "zero_witness": zero,
        "n_same_minsize_splits": len(splits),
        "n_size_class_inversions": inversions,
        "max_extra_shell_factor": max_extra,
        "extra_shell_note": EXTRA_SHELL_NOTE,
        "gates": required,
        "grid_disclosure": GRID_DISCLOSURE,
        "untested": {"gradient_recovery": GRADIENT_WITHHELD},
        "withheld": [
            "Master-formula gradient recovery",
            "Sq-toy extra-shell transfer at k≤5",
            "Identity of functions from the grid except the exact zero identity",
        ],
        "citations": [
            "Odrzywołek, A. (2026). All elementary functions from a single binary operator. arXiv:2603.21852.",
        ],
    }
