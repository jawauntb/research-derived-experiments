"""First estimator of the EML-native numerical fiber spectrum.

Odrzywołek (arXiv:2603.21852) gives the binary operator
``eml(x, y) = exp(x) - ln(y)`` and the grammar ``S → 1 | eml(S, S)``.
Closed terms are full binary trees with every leaf equal to ``1``.

The monomial toy ``x^(2^n)`` has *degree* as a 1-D complete invariant of
denotation, so its fiber is dynamic-programmable (see
``experiments/squaring_separation`` on the companion branch).  EML
denotations have no such invariant.  This package does **not** invent
one.  It enumerates every tree with ``n_internal ≤ MAX_INTERNAL`` and
estimates the numerical spectrum.

What this instrument banks
--------------------------
A. Size is not a denotation invariant: two equal-size trees disagree at
   a registered evaluation (exact witness, not a collision).
B. Exhaustive Catalan-complete census at the registered bound, grouped
   by a rounded numerical fiber id.  Spectrum *counts* are
   ``claim_tier = computational``.
C. Closed-form sanity: ``eml(1, 1) = e`` and a few hand trees.

What it withholds
-----------------
US-4′ (fiber free energy predicts EML gradient recovery) is untested.
A truncated Gibbs mass at this depth is a census statistic, not that
claim.  Agreement of two trees on a finite probe grid is not identity
of functions.

Optional gate
-------------
Different sizes in the same *well-resolved* numerical fiber (size is
not a complete invariant of the numerical denotation).  Observed here
by exact algebraic identities such as ``e - ln(exp(e-1)) = 1``.  If
absent at a later bound the gate is withheld, not averaged away.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Sequence

EXPERIMENT_ID = "eml_fiber_spectrum"
RUN_ID = "eml_fiber_spectrum_2026_08_17"
PRODUCING_AGENT = "Cursor Grok 4.6 (cloud agent, under J. Brown direction)"
SESSION_REF = "bc-01a00d99-d2d8-7c5e-a8d0-d0090dfd7bdd"

# Registered exhaustive bound: all trees with n_internal ≤ 6.
# C_0..C_6 = 1+1+2+5+14+42+132 = 197.  C_7 = 429 is tractable but not
# the registered census.
MAX_INTERNAL = 6
ROUND_DIGITS = 10
GIBBS_BASE = 4

# Probe coincides with the closed denotation at (1, 1).
WITNESS_POINT: tuple[float, float] = (1.0, 1.0)
TEST_GRID: tuple[tuple[float, float], ...] = (
    (0.0, 1.0),
    (1.0, 1.0),
    (1.0, 2.0),
    (0.5, 0.5),
    (-1.0, 1.0),
    (2.0, math.e),
)

# Magnitudes outside this window are treated as resolution-suspect:
# float64 cannot separate X from X-1 near 1e114, and 1e-12 spreads at
# 1e-6 are rounding, not identities.
WELL_RESOLVED_ABS_MAX = 1.0e8
WELL_RESOLVED_ABS_MIN = 1.0e-8
WELL_RESOLVED_SPREAD = 1.0e-12

GRID_COLLISION_DISCLOSURE = (
    "Agreement on a finite probe grid is not identity of functions. "
    "Two different elementary functions can collide on the grid, and "
    "two different reals can collide after rounding or at extreme "
    "magnitude.  Spectrum counts are computational.  A same-size "
    "disagreement at a single registered point is a witness, not a "
    "collision."
)

US4_PRIME_WITHHELD = (
    "US-4′ (fiber free energy predicts gradient recovery on EML master "
    "formulas) is untested.  This package is a first numerical-spectrum "
    "instrument, not that claim."
)

REQUIRED_GATES: tuple[str, ...] = (
    "EFS_SIZE_NOT_DENOTATION",
    "EFS_ENUMERATION_COMPLETE",
    "EFS_GRID_COLLISION_DISCLOSED",
    "EFS_US4_PRIME_WITHHELD",
)
OPTIONAL_GATES: tuple[str, ...] = ("EFS_CROSS_SIZE_COLLISION",)


@dataclass(frozen=True)
class EmlTree:
    """Full binary tree.  ``left is None`` iff the node is a leaf ``1``."""

    left: EmlTree | None = None
    right: EmlTree | None = None

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
            return "1"
        assert self.left is not None and self.right is not None
        return f"eml({self.left.pretty()},{self.right.pretty()})"


LEAF = EmlTree()


def catalan(n: int) -> int:
    """``C_n = (1/(n+1)) * binom(2n, n)``; trees with ``n`` internal nodes."""

    if n < 0:
        raise ValueError("catalan is defined for n >= 0")
    return math.comb(2 * n, n) // (n + 1)


def eml(x: float, y: float) -> float:
    """``exp(x) - ln(y)``.  Requires ``y > 0`` over the reals."""

    if y <= 0.0 or not math.isfinite(y) or not math.isfinite(x):
        raise ValueError("eml domain requires finite x and y > 0")
    return math.exp(x) - math.log(y)


def parse_eml(text: str) -> EmlTree:
    """Parse ``1`` or ``eml(S,S)`` with no spaces."""

    raw = text.strip()
    if raw == "1":
        return LEAF
    if not (raw.startswith("eml(") and raw.endswith(")")):
        raise ValueError(f"not an EML term: {text!r}")
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
    return EmlTree(parse_eml(inner[:split_at]), parse_eml(inner[split_at + 1 :]))


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


def eval_closed(tree: EmlTree) -> float | None:
    """Closed denotation: every leaf is the constant ``1``."""

    if tree.is_leaf:
        return 1.0
    assert tree.left is not None and tree.right is not None
    return _combine(eval_closed(tree.left), eval_closed(tree.right))


def eval_probe(tree: EmlTree, x: float, y: float) -> float | None:
    """Leaf-chirality probe: left leaves := ``x``, right leaves := ``y``.

    The size-0 tree has no parent, so it stays ``1``.  At ``(x, y) = (1, 1)``
    the probe coincides with ``eval_closed``.  This is a registered
    *representation*, not Odrzywołek's variable-leaf grammar.
    """

    def go(node: EmlTree, side: str | None) -> float | None:
        if node.is_leaf:
            if side == "L":
                return x
            if side == "R":
                return y
            return 1.0
        assert node.left is not None and node.right is not None
        return _combine(go(node.left, "L"), go(node.right, "R"))

    return go(tree, None)


def enumerate_trees(max_internal: int = MAX_INTERNAL) -> dict[int, tuple[EmlTree, ...]]:
    """All full binary trees with ``n_internal ≤ max_internal``, by size."""

    if max_internal < 0:
        raise ValueError("max_internal must be >= 0")
    memo: dict[int, tuple[EmlTree, ...]] = {0: (LEAF,)}
    for n_internal in range(1, max_internal + 1):
        trees: list[EmlTree] = []
        for left_internal in range(n_internal):
            right_internal = n_internal - 1 - left_internal
            for left in memo[left_internal]:
                for right in memo[right_internal]:
                    trees.append(EmlTree(left, right))
        memo[n_internal] = tuple(trees)
    return memo


def numerical_fiber_id(values: Sequence[float], ndigits: int = ROUND_DIGITS) -> str:
    rounded = tuple(round(float(value), ndigits) for value in values)
    return "F:" + ",".join(f"{item:.{ndigits}f}" for item in rounded)


def is_well_resolved(values: Sequence[float]) -> bool:
    if not values:
        return False
    magnitude = max(abs(value) for value in values)
    if magnitude > WELL_RESOLVED_ABS_MAX:
        return False
    if any(0.0 < abs(value) < WELL_RESOLVED_ABS_MIN for value in values):
        return False
    spread = max(values) - min(values)
    return spread <= WELL_RESOLVED_SPREAD * max(1.0, magnitude)


def _fiber_id_or_none(value: float | None) -> str | None:
    if value is None:
        return None
    return numerical_fiber_id((value,))


def _probe_tuple(tree: EmlTree, grid: Sequence[tuple[float, float]] = TEST_GRID) -> tuple[float, ...] | None:
    values: list[float] = []
    for x_val, y_val in grid:
        probed = eval_probe(tree, x_val, y_val)
        if probed is None:
            return None
        values.append(probed)
    return tuple(values)


# Hand trees with known closed values (Odrzywołek identities + grammar).
SANITY_TREES: tuple[tuple[str, str, float], ...] = (
    ("leaf", "1", 1.0),
    ("eml_1_1_is_e", "eml(1,1)", math.e),
    ("eml_1_e_is_e_minus_1", "eml(1,eml(1,1))", math.e - 1.0),
    ("eml_e_1_is_exp_e", "eml(eml(1,1),1)", math.exp(math.e)),
    ("ln_1_is_zero", "eml(1,eml(eml(1,1),1))", 0.0),
    ("closed_identity_one", "eml(1,eml(eml(1,eml(1,1)),1))", 1.0),
)

# Exact same-size disagreement.  Size 2 is the first Catalan shell with
# two trees; they differ at the closed denotation / witness point (1, 1).
SIZE_NOT_DENOTATION_LEFT = "eml(1,eml(1,1))"
SIZE_NOT_DENOTATION_RIGHT = "eml(eml(1,1),1)"

# Exact cross-size identities at well-resolved magnitudes.
CROSS_SIZE_WITNESSES: tuple[tuple[str, str, float], ...] = (
    ("1", "eml(1,eml(eml(1,eml(1,1)),1))", 1.0),
    ("eml(1,1)", "eml(1,eml(1,eml(eml(1,eml(1,1)),1)))", math.e),
    ("eml(1,eml(eml(1,1),1))", "eml(eml(1,1),eml(eml(eml(1,1),1),1))", 0.0),
    ("eml(1,eml(1,1))", "eml(1,eml(1,eml(1,eml(eml(1,eml(1,1)),1))))", math.e - 1.0),
    ("eml(eml(1,1),1)", "eml(eml(1,1),eml(1,eml(eml(1,eml(1,1)),1)))", math.exp(math.e)),
)


def check_sanity_trees(rel_tol: float = 1e-12) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for name, pretty, expected in SANITY_TREES:
        tree = parse_eml(pretty)
        observed = eval_closed(tree)
        ok = observed is not None and math.isclose(observed, expected, rel_tol=rel_tol, abs_tol=1e-15)
        rows.append(
            {
                "name": name,
                "pretty": pretty,
                "n_internal": tree.n_internal,
                "expected": expected,
                "observed": observed,
                "ok": ok,
            }
        )
    return rows


def check_operator_grid() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for x_val, y_val in TEST_GRID:
        expected = math.exp(x_val) - math.log(y_val)
        observed = eml(x_val, y_val)
        rows.append(
            {
                "x": x_val,
                "y": y_val,
                "expected": expected,
                "observed": observed,
                "ok": math.isclose(observed, expected, rel_tol=0.0, abs_tol=0.0),
            }
        )
    return rows


def _size_not_denotation_witness() -> dict[str, object]:
    left = parse_eml(SIZE_NOT_DENOTATION_LEFT)
    right = parse_eml(SIZE_NOT_DENOTATION_RIGHT)
    left_val = eval_closed(left)
    right_val = eval_closed(right)
    point_left = eval_probe(left, *WITNESS_POINT)
    point_right = eval_probe(right, *WITNESS_POINT)
    differs = (
        left_val is not None
        and right_val is not None
        and left_val != right_val
        and point_left is not None
        and point_right is not None
        and point_left != point_right
        and left.n_internal == right.n_internal == 2
    )
    return {
        "n_internal": 2,
        "point": {"x": WITNESS_POINT[0], "y": WITNESS_POINT[1]},
        "left": {"pretty": SIZE_NOT_DENOTATION_LEFT, "closed": left_val, "at_point": point_left},
        "right": {"pretty": SIZE_NOT_DENOTATION_RIGHT, "closed": right_val, "at_point": point_right},
        "algebra": "eml(1,e)=e-1 versus eml(e,1)=exp(e)",
        "exact_witness": differs,
    }


def _cross_size_witnesses() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for left_pretty, right_pretty, expected in CROSS_SIZE_WITNESSES:
        left = parse_eml(left_pretty)
        right = parse_eml(right_pretty)
        left_val = eval_closed(left)
        right_val = eval_closed(right)
        ok = (
            left_val is not None
            and right_val is not None
            and left.n_internal != right.n_internal
            and math.isclose(left_val, expected, rel_tol=1e-12, abs_tol=1e-15)
            and math.isclose(right_val, expected, rel_tol=1e-12, abs_tol=1e-15)
            and is_well_resolved((left_val, right_val, expected))
        )
        rows.append(
            {
                "expected": expected,
                "left": {"pretty": left_pretty, "n_internal": left.n_internal, "closed": left_val},
                "right": {"pretty": right_pretty, "n_internal": right.n_internal, "closed": right_val},
                "ok": ok,
            }
        )
    return rows


def _group_closed(
    by_size: dict[int, tuple[EmlTree, ...]],
) -> tuple[dict[str, list[tuple[int, EmlTree, float]]], int]:
    grouped: dict[str, list[tuple[int, EmlTree, float]]] = defaultdict(list)
    n_undefined = 0
    for n_internal, trees in by_size.items():
        for tree in trees:
            value = eval_closed(tree)
            if value is None:
                n_undefined += 1
                continue
            grouped[numerical_fiber_id((value,))].append((n_internal, tree, value))
    return grouped, n_undefined


def _group_probe(
    by_size: dict[int, tuple[EmlTree, ...]],
) -> tuple[dict[str, list[tuple[int, EmlTree, tuple[float, ...]]]], int]:
    grouped: dict[str, list[tuple[int, EmlTree, tuple[float, ...]]]] = defaultdict(list)
    n_undefined = 0
    for n_internal, trees in by_size.items():
        for tree in trees:
            values = _probe_tuple(tree)
            if values is None:
                n_undefined += 1
                continue
            grouped[numerical_fiber_id(values)].append((n_internal, tree, values))
    return grouped, n_undefined


def _closed_fiber_rows(
    grouped: dict[str, list[tuple[int, EmlTree, float]]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for fiber_id, members in grouped.items():
        values = [value for _n, _tree, value in members]
        sizes = sorted({n_internal for n_internal, _tree, _value in members})
        n_nodes_list = [2 * n_internal + 1 for n_internal, _tree, _value in members]
        phi_hat = sum(GIBBS_BASE ** (-n_nodes) for n_nodes in n_nodes_list)
        rows.append(
            {
                "fiber_id": fiber_id,
                "n_trees": len(members),
                "sizes": sizes,
                "n_sizes": len(sizes),
                "mean_value": sum(values) / len(values),
                "spread": max(values) - min(values),
                "well_resolved": is_well_resolved(values),
                "truncated_phi": phi_hat,
                "example_trees": [tree.pretty() for _n, tree, _value in members[:3]],
            }
        )
    rows.sort(key=lambda row: (-int(row["n_trees"]), str(row["fiber_id"])))
    return rows


def evaluate_gates(
    *,
    tree_counts: dict[int, int],
    size_witness: dict[str, object],
    cross_witnesses: Sequence[dict[str, object]],
    closed_rows: Sequence[dict[str, object]],
    sanity_ok: bool,
    operator_ok: bool,
) -> tuple[dict[str, bool], dict[str, object]]:
    enumeration_complete = all(
        tree_counts[n_internal] == catalan(n_internal) for n_internal in range(MAX_INTERNAL + 1)
    ) and sum(tree_counts.values()) == sum(catalan(n) for n in range(MAX_INTERNAL + 1))
    same_size_split = any(
        n_internal >= 2
        and tree_counts[n_internal] >= 2
        for n_internal in tree_counts
    ) and bool(size_witness["exact_witness"])
    # Same-size trees in different fibers: the size-2 witness, plus any
    # size whose finite closed values are not a singleton.
    required = {
        "EFS_SIZE_NOT_DENOTATION": same_size_split and sanity_ok and operator_ok,
        "EFS_ENUMERATION_COMPLETE": enumeration_complete,
        "EFS_GRID_COLLISION_DISCLOSED": True,
        "EFS_US4_PRIME_WITHHELD": True,
    }
    well_resolved_cross = [
        row
        for row in closed_rows
        if bool(row["well_resolved"]) and int(row["n_sizes"]) > 1
    ]
    exact_cross = all(bool(row["ok"]) for row in cross_witnesses) and bool(cross_witnesses)
    if exact_cross and well_resolved_cross:
        optional = {
            "EFS_CROSS_SIZE_COLLISION": {
                "status": "pass",
                "observed": True,
                "n_well_resolved_cross_fibers": len(well_resolved_cross),
                "n_exact_witnesses": sum(1 for row in cross_witnesses if row["ok"]),
            }
        }
    else:
        optional = {
            "EFS_CROSS_SIZE_COLLISION": {
                "status": "withheld",
                "observed": False,
                "n_well_resolved_cross_fibers": len(well_resolved_cross),
                "n_exact_witnesses": sum(1 for row in cross_witnesses if row["ok"]),
            }
        }
    return required, optional


def evaluate_benchmark() -> dict[str, object]:
    by_size = enumerate_trees(MAX_INTERNAL)
    tree_counts = {n_internal: len(trees) for n_internal, trees in by_size.items()}
    n_trees = sum(tree_counts.values())

    closed_grouped, n_closed_undefined = _group_closed(by_size)
    probe_grouped, n_probe_undefined = _group_probe(by_size)
    closed_rows = _closed_fiber_rows(closed_grouped)

    finite_closed = n_trees - n_closed_undefined
    n_closed_fibers = len(closed_grouped)
    max_closed_fiber = max((len(members) for members in closed_grouped.values()), default=0)
    n_probe_fibers = len(probe_grouped)
    max_probe_fiber = max((len(members) for members in probe_grouped.values()), default=0)

    distinct_closed_by_size: dict[int, int] = {}
    for n_internal, trees in by_size.items():
        ids = {
            _fiber_id_or_none(eval_closed(tree))
            for tree in trees
            if eval_closed(tree) is not None
        }
        distinct_closed_by_size[n_internal] = len(ids)

    size_is_denotation_invariant = all(
        count <= 1 for count in distinct_closed_by_size.values()
    )
    well_resolved_cross = [
        row for row in closed_rows if row["well_resolved"] and int(row["n_sizes"]) > 1
    ]
    suspect_cross = [
        {
            "fiber_id": row["fiber_id"],
            "sizes": row["sizes"],
            "n_trees": row["n_trees"],
            "mean_value": row["mean_value"],
            "spread": row["spread"],
        }
        for row in closed_rows
        if (not row["well_resolved"]) and int(row["n_sizes"]) > 1
    ]
    probe_cross = [
        fiber_id
        for fiber_id, members in probe_grouped.items()
        if len({n_internal for n_internal, _tree, _values in members}) > 1
    ]

    sanity = check_sanity_trees()
    operator_grid = check_operator_grid()
    size_witness = _size_not_denotation_witness()
    cross_witnesses = _cross_size_witnesses()
    sanity_ok = all(bool(row["ok"]) for row in sanity)
    operator_ok = all(bool(row["ok"]) for row in operator_grid)

    required, optional = evaluate_gates(
        tree_counts=tree_counts,
        size_witness=size_witness,
        cross_witnesses=cross_witnesses,
        closed_rows=closed_rows,
        sanity_ok=sanity_ok,
        operator_ok=operator_ok,
    )

    z_hat = sum(
        GIBBS_BASE ** (-(2 * n_internal + 1)) * count
        for n_internal, count in tree_counts.items()
    )
    required_pass = all(required.values())
    return {
        "status": "pass" if required_pass else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {
            "identity": PRODUCING_AGENT,
            "session_ref": SESSION_REF,
        },
        "claim_tier_spectrum": "computational",
        "claim_tier_size_witness": "exact_witness",
        "registered": {
            "max_internal": MAX_INTERNAL,
            "round_digits": ROUND_DIGITS,
            "witness_point": {"x": WITNESS_POINT[0], "y": WITNESS_POINT[1]},
            "test_grid": [{"x": x_val, "y": y_val} for x_val, y_val in TEST_GRID],
            "gibbs_base": GIBBS_BASE,
            "size_convention": "n_internal = number of eml nodes; n_nodes = 2*n_internal+1",
        },
        "tree_counts_by_size": {str(n): tree_counts[n] for n in range(MAX_INTERNAL + 1)},
        "catalan_by_size": {str(n): catalan(n) for n in range(MAX_INTERNAL + 1)},
        "n_trees": n_trees,
        "closed_spectrum": {
            "n_finite": finite_closed,
            "n_undefined": n_closed_undefined,
            "n_numerical_fibers": n_closed_fibers,
            "max_fiber_size": max_closed_fiber,
            "distinct_fibers_by_size": {
                str(n): distinct_closed_by_size[n] for n in range(MAX_INTERNAL + 1)
            },
            "size_is_denotation_invariant": size_is_denotation_invariant,
            "n_well_resolved_cross_size_fibers": len(well_resolved_cross),
            "suspect_cross_size_fibers": suspect_cross,
            "largest_fibers": closed_rows[:8],
        },
        "probe_spectrum": {
            "representation": (
                "leaf_chirality_probe: left leaves := x, right leaves := y; "
                "size-0 tree stays 1.  Not the variable-leaf EML grammar."
            ),
            "n_finite_on_grid": n_trees - n_probe_undefined,
            "n_undefined_on_grid": n_probe_undefined,
            "n_numerical_fibers": n_probe_fibers,
            "max_fiber_size": max_probe_fiber,
            "n_cross_size_fibers": len(probe_cross),
            "cross_size_status": "withheld" if not probe_cross else "observed_computational",
        },
        "truncated_gibbs": {
            "base": GIBBS_BASE,
            "size_convention": "n_nodes = 2*n_internal+1",
            "Z_hat": z_hat,
            "note": (
                "Truncated language mass over the registered census. "
                "Not a fiber-free-energy claim. US-4' withheld."
            ),
        },
        "sanity": sanity,
        "operator_grid": operator_grid,
        "size_not_denotation_witness": size_witness,
        "cross_size_witnesses": cross_witnesses,
        "gates": required,
        "optional_gates": optional,
        "grid_collision_disclosed": True,
        "grid_collision_disclosure": GRID_COLLISION_DISCLOSURE,
        "untested": {
            "US-4_prime": US4_PRIME_WITHHELD,
        },
        "citations": [
            "Odrzywołek, A. (2026). All elementary functions from a single binary operator. arXiv:2603.21852.",
        ],
        "citations_pending_verification": [
            "Stachowiak 2026 arXiv:2604.23893 (algebraic structure of EML; primary text not checked here)",
        ],
    }
