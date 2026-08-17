"""First variable-``x`` EML spectrum probe.

The constant grammar ``S → 1 | eml(S,S)`` has no free variable.  This
package labels every leaf with ``1`` or ``x``:

    S → 1 | x | eml(S, S)
    eml(a, b) = exp(a) - ln(b)    (real; undefined if b ≤ 0 or overflow)

There is still no 1-D integer invariant like polynomial degree, so the
fiber of a numerical function-tuple cannot be dynamic-programmed the
way ``x^(2^n)`` can.  This instrument enumerates the registered bound
and clusters trees by a quantized evaluation grid.

Banked
------
A. Leaf-labeled counts equal ``2^{k+1} C_k``.
B. Size is not a function invariant: ``eml(x,1)=exp(x)`` and
   ``eml(1,x)=e-ln(x)`` are both size 3 / 1-internal and disagree on
   the registered positive grid.
C. The all-ones fragment reproduces the constant size-2 split
   ``e-1`` vs ``exp(e)``.

Withheld
--------
US-4′.  Variable-leaf identity of functions.  Any 1-D complete
invariant.  The constant-grammar census on the companion
``eml_fiber_spectrum`` branch is a different package.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from itertools import product

EXPERIMENT_ID = "eml_variable_spectrum"
RUN_ID = "eml_variable_spectrum_2026_08_17"
PRODUCING_AGENT = "Cursor Grok 4.6 (cloud agent, under J. Brown direction)"
SESSION_REF = "bc-01a00d99-d2d8-7c5e-a8d0-d0090dfd7bdd"

MAX_INTERNAL = 5
ROUND_DIGITS = 10
LEAF_LABELS: tuple[str, ...] = ("1", "x")
# Positive so right-hand ``x`` stays in the real-log domain.
TEST_GRID: tuple[float, ...] = (0.25, 0.5, 1.0, 2.0, math.e, 4.0)
WITNESS_LEFT = "eml(x,1)"
WITNESS_RIGHT = "eml(1,x)"

GRID_DISCLOSURE = (
    "Agreement of two trees on a finite positive grid is not identity "
    "of functions.  Spectrum counts are computational.  The size-1 "
    "witness uses exact closed forms exp(x) vs e-ln(x), which already "
    "disagree at x=2."
)
US4_PRIME_WITHHELD = (
    "US-4′ (fiber free energy predicts gradient recovery on EML master "
    "formulas) is untested.  This package is a first variable-x census, "
    "not that claim."
)


def catalan(n: int) -> int:
    if n < 0:
        raise ValueError("catalan is defined for n >= 0")
    return math.comb(2 * n, n) // (n + 1)


def labeled_count(n_internal: int) -> int:
    """``2^{n_internal+1} C_{n_internal}`` full binary trees with binary leaves."""

    return catalan(n_internal) * (2 ** (n_internal + 1))


@dataclass(frozen=True)
class VarTree:
    """Full binary tree.  ``left is None`` iff this node is a labeled leaf."""

    left: VarTree | None = None
    right: VarTree | None = None
    leaf: str | None = "1"

    def __post_init__(self) -> None:
        if self.left is None:
            if self.right is not None:
                raise ValueError("leaf cannot have a right child")
            if self.leaf not in LEAF_LABELS:
                raise ValueError(f"leaf label must be 1 or x, got {self.leaf!r}")
        elif self.right is None or self.leaf is not None:
            raise ValueError("internal node must have two children and leaf=None")

    @property
    def is_leaf(self) -> bool:
        return self.left is None

    @property
    def n_internal(self) -> int:
        if self.is_leaf:
            return 0
        assert self.left is not None and self.right is not None
        return 1 + self.left.n_internal + self.right.n_internal

    @property
    def n_nodes(self) -> int:
        return 2 * self.n_internal + 1

    def pretty(self) -> str:
        if self.is_leaf:
            assert self.leaf is not None
            return self.leaf
        assert self.left is not None and self.right is not None
        return f"eml({self.left.pretty()},{self.right.pretty()})"

    def all_ones(self) -> bool:
        if self.is_leaf:
            return self.leaf == "1"
        assert self.left is not None and self.right is not None
        return self.left.all_ones() and self.right.all_ones()


def parse_var(text: str) -> VarTree:
    raw = text.strip()
    if raw in LEAF_LABELS:
        return VarTree(leaf=raw)
    if not (raw.startswith("eml(") and raw.endswith(")")):
        raise ValueError(f"not a variable-EML term: {text!r}")
    inner = raw[4:-1]
    depth = 0
    split_at = -1
    for index, char in enumerate(inner):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            split_at = index
            break
    if split_at < 0:
        raise ValueError(f"eml term is missing a top-level comma: {text!r}")
    return VarTree(
        left=parse_var(inner[:split_at]),
        right=parse_var(inner[split_at + 1 :]),
        leaf=None,
    )


def _combine(left_val: float | None, right_val: float | None) -> float | None:
    if left_val is None or right_val is None:
        return None
    if not math.isfinite(left_val) or not math.isfinite(right_val) or right_val <= 0.0:
        return None
    try:
        value = math.exp(left_val) - math.log(right_val)
    except OverflowError:
        return None
    if not math.isfinite(value):
        return None
    return value


def eval_at(tree: VarTree, x: float) -> float | None:
    if tree.is_leaf:
        if tree.leaf == "1":
            return 1.0
        return x
    assert tree.left is not None and tree.right is not None
    return _combine(eval_at(tree.left, x), eval_at(tree.right, x))


def eval_grid(tree: VarTree, grid: tuple[float, ...] = TEST_GRID) -> tuple[float | None, ...]:
    return tuple(eval_at(tree, x) for x in grid)


def enumerate_trees(max_internal: int = MAX_INTERNAL) -> dict[int, tuple[VarTree, ...]]:
    if max_internal < 0:
        raise ValueError("max_internal must be >= 0")
    memo: dict[int, tuple[VarTree, ...]] = {
        0: tuple(VarTree(leaf=label) for label in LEAF_LABELS),
    }
    for n_internal in range(1, max_internal + 1):
        trees: list[VarTree] = []
        for left_internal in range(n_internal):
            right_internal = n_internal - 1 - left_internal
            for left, right in product(memo[left_internal], memo[right_internal]):
                trees.append(VarTree(left=left, right=right, leaf=None))
        memo[n_internal] = tuple(trees)
    return memo


def numerical_fiber_id(values: tuple[float | None, ...], ndigits: int = ROUND_DIGITS) -> str:
    parts: list[str] = []
    for value in values:
        if value is None or not math.isfinite(value):
            parts.append("undef")
        else:
            parts.append(f"{round(float(value), ndigits):.{ndigits}f}")
    return "F:" + ",".join(parts)


def _size_not_function_witness() -> dict[str, object]:
    left = parse_var(WITNESS_LEFT)
    right = parse_var(WITNESS_RIGHT)
    left_grid = eval_grid(left)
    right_grid = eval_grid(right)
    x2_left = eval_at(left, 2.0)
    x2_right = eval_at(right, 2.0)
    differs = (
        left.n_internal == right.n_internal == 1
        and x2_left is not None
        and x2_right is not None
        and not math.isclose(x2_left, x2_right, rel_tol=0.0, abs_tol=1e-12)
        and left_grid != right_grid
        and math.isclose(x2_left, math.exp(2.0), rel_tol=0.0, abs_tol=1e-12)
        and math.isclose(x2_right, math.e - math.log(2.0), rel_tol=0.0, abs_tol=1e-12)
    )
    return {
        "n_internal": 1,
        "n_nodes": 3,
        "left": {"pretty": WITNESS_LEFT, "closed_form": "exp(x)", "at_2": x2_left},
        "right": {"pretty": WITNESS_RIGHT, "closed_form": "e-ln(x)", "at_2": x2_right},
        "grid_disagrees": left_grid != right_grid,
        "exact_witness": differs,
    }


def _constant_embedding_witness() -> dict[str, object]:
    left = parse_var("eml(1,eml(1,1))")
    right = parse_var("eml(eml(1,1),1)")
    # All-ones trees are constant in x; evaluate at 1.
    left_val = eval_at(left, 1.0)
    right_val = eval_at(right, 1.0)
    constant = all(eval_at(left, x) == left_val for x in TEST_GRID) and all(
        eval_at(right, x) == right_val for x in TEST_GRID
    )
    ok = (
        left.all_ones()
        and right.all_ones()
        and left.n_internal == right.n_internal == 2
        and left_val is not None
        and right_val is not None
        and constant
        and math.isclose(left_val, math.e - 1.0, rel_tol=0.0, abs_tol=1e-12)
        and math.isclose(right_val, math.exp(math.e), rel_tol=1e-12, abs_tol=0.0)
    )
    return {
        "left": {"pretty": left.pretty(), "value": left_val},
        "right": {"pretty": right.pretty(), "value": right_val},
        "constant_in_x": constant,
        "exact_witness": ok,
    }


def evaluate_benchmark() -> dict[str, object]:
    by_size = enumerate_trees(MAX_INTERNAL)
    tree_counts = {n_internal: len(trees) for n_internal, trees in by_size.items()}
    n_trees = sum(tree_counts.values())
    expected = {n_internal: labeled_count(n_internal) for n_internal in range(MAX_INTERNAL + 1)}

    grouped: dict[str, list[tuple[int, str]]] = defaultdict(list)
    n_undefined_rows = 0
    n_partial = 0
    for n_internal, trees in by_size.items():
        for tree in trees:
            values = eval_grid(tree)
            if all(value is None for value in values):
                n_undefined_rows += 1
                continue
            if any(value is None for value in values):
                n_partial += 1
            grouped[numerical_fiber_id(values)].append((n_internal, tree.pretty()))

    n_fibers = len(grouped)
    max_fiber = max((len(members) for members in grouped.values()), default=0)
    cross_size = [
        fiber_id
        for fiber_id, members in grouped.items()
        if len({n_internal for n_internal, _pretty in members}) > 1
    ]
    distinct_by_size: dict[int, int] = {}
    for n_internal, trees in by_size.items():
        ids = {numerical_fiber_id(eval_grid(tree)) for tree in trees}
        distinct_by_size[n_internal] = len(ids)

    size_witness = _size_not_function_witness()
    constant_witness = _constant_embedding_witness()
    enumeration_complete = all(
        tree_counts[n_internal] == expected[n_internal] for n_internal in expected
    )
    required = {
        "EVS_ENUMERATION_COMPLETE": enumeration_complete,
        "EVS_SIZE_NOT_FUNCTION": bool(size_witness["exact_witness"]),
        "EVS_CONSTANT_EMBEDDING": bool(constant_witness["exact_witness"]),
        "EVS_GRID_DISCLOSED": True,
        "EVS_US4_PRIME_WITHHELD": True,
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
            "leaf_labels": list(LEAF_LABELS),
            "grid": list(TEST_GRID),
            "round_digits": ROUND_DIGITS,
            "count_formula": "2^{k+1} C_k",
        },
        "tree_counts_by_size": {str(n): tree_counts[n] for n in range(MAX_INTERNAL + 1)},
        "expected_counts_by_size": {str(n): expected[n] for n in range(MAX_INTERNAL + 1)},
        "n_trees": n_trees,
        "spectrum": {
            "n_numerical_fibers": n_fibers,
            "max_fiber_size": max_fiber,
            "n_all_undefined": n_undefined_rows,
            "n_partial_undefined": n_partial,
            "n_cross_size_fibers": len(cross_size),
            "distinct_fibers_by_size": {str(n): distinct_by_size[n] for n in range(MAX_INTERNAL + 1)},
            "size_is_function_invariant": all(count <= 1 for count in distinct_by_size.values()),
        },
        "size_not_function_witness": size_witness,
        "constant_embedding_witness": constant_witness,
        "gates": required,
        "grid_disclosure": GRID_DISCLOSURE,
        "untested": {"US-4_prime": US4_PRIME_WITHHELD},
        "withheld": [
            "US-4′",
            "Identity of functions from finite-grid agreement",
            "A 1-D complete invariant of EML denotations",
        ],
        "citations": [
            "Odrzywołek, A. (2026). All elementary functions from a single binary operator. arXiv:2603.21852.",
        ],
    }

