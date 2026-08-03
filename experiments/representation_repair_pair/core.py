"""Exact witness of Theorems RR-1 (lift table is well-defined) and RR-2
(lifts compose) from the companion paper *Representation-Repair Calculus*
(``papers/representation_repair_calculus/paper.md``).

Setup
-----

For each of the eight canonical ``(failure_signature, minimal_lift)`` pairs
listed in Extended-Program section 5.8 of *The Structural Intelligence
Conjecture*, we exhibit an exact witness on a tiny hand-designed world:

- a finite state space ``S``;
- a target invariant ``I : S -> value`` (the coarse fact one wants to
  compute from the representation);
- a *broken* representation ``R : S -> tuple`` that misses ``I``
  (there exist two states ``s != s'`` with ``R(s) = R(s')`` but
  ``I(s) != I(s')``);
- a *lifted* representation ``R' : S -> tuple`` that adds finitely many
  new components to ``R`` and captures ``I``
  (for every ``s, s'``, ``R'(s) = R'(s')`` implies ``I(s) = I(s')``);
- a *minimality* check: for every strictly smaller enlargement of ``R``
  (drop any non-empty subset of added components from ``R'``), the
  resulting representation misses ``I`` again.

The eight pairs are:

1. ``scalar_to_operator``          -- Pauli Z-only scalar vs full Bloch operator
2. ``global_norm_to_localized_measure`` -- support-size scalar vs per-cell measure
3. ``quotient_to_restored_fiber``  -- coarse label vs (label, fiber index)
4. ``static_to_path_space``        -- current state vs full trajectory
5. ``affine_to_projective``        -- affine chart vs homogeneous coordinate
6. ``point_to_ensemble``           -- point mean vs full moment vector
7. ``non_composing_to_interface``  -- module identity vs (identity, protocol)
8. ``symmetry_to_gauge_fix``       -- gauge-dependent scalar vs gauge-invariant offsets

We also compose two independent lifts (scalar->operator and static->path)
on a product world and verify that the composed lift captures the joint
invariant, per Theorem RR-2.

All arithmetic is on finite worlds with exact hashable representations;
gate outcomes are exact.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from itertools import combinations, product
from typing import Any, TypeVar

State = Any
Feature = Any
FeatureTuple = tuple[Feature, ...]

T = TypeVar("T")


# ---------- Core primitives ----------


@dataclass(frozen=True)
class Representation:
    """A representation is an ordered list of named features on ``S``.

    Each feature is a pure Python callable ``state -> value``. We use a
    *tuple of names* to preserve deterministic ordering, and evaluate
    every feature to build the state's feature-tuple.
    """

    names: tuple[str, ...]
    feature_fns: tuple[Callable[[State], Feature], ...] = field(compare=False)

    def evaluate(self, state: State) -> FeatureTuple:
        return tuple(fn(state) for fn in self.feature_fns)

    def subset(self, keep: Iterable[str]) -> "Representation":
        keep_set = tuple(name for name in self.names if name in set(keep))
        keep_index = [self.names.index(name) for name in keep_set]
        return Representation(
            names=keep_set,
            feature_fns=tuple(self.feature_fns[i] for i in keep_index),
        )


def invariant_captured(
    states: Sequence[State],
    rep: Representation,
    invariant: Callable[[State], Any],
) -> bool:
    """True iff ``I`` factors through ``rep``:

    for every ``s, s'``, ``rep(s) = rep(s')`` implies ``I(s) = I(s')``.
    """

    seen: dict[FeatureTuple, Any] = {}
    for state in states:
        rep_value = rep.evaluate(state)
        target_value = invariant(state)
        if rep_value in seen:
            if seen[rep_value] != target_value:
                return False
        else:
            seen[rep_value] = target_value
    return True


def invariant_missed(
    states: Sequence[State],
    rep: Representation,
    invariant: Callable[[State], Any],
) -> bool:
    """True iff ``I`` does NOT factor through ``rep`` -- equivalently,
    at least one collision on ``rep`` maps to distinct invariant values."""

    return not invariant_captured(states, rep, invariant)


def lift_is_minimal(
    states: Sequence[State],
    broken: Representation,
    lifted: Representation,
    invariant: Callable[[State], Any],
) -> tuple[bool, list[dict[str, Any]]]:
    """Test minimality: every strictly smaller enlargement of ``broken``
    below ``lifted`` fails to capture ``I``.

    Concretely: the added components ``A = lifted.names \\ broken.names``
    are all necessary. Dropping any non-empty subset ``D`` of ``A`` from
    ``lifted`` should yield a representation ``broken + (A \\ D)`` that
    misses ``I``.

    Returns (minimality_ok, per-drop-records). ``minimality_ok`` is True
    iff every non-empty subset of ``A`` dropped from ``lifted`` breaks
    capture.
    """

    broken_names = set(broken.names)
    lifted_names = set(lifted.names)
    if not broken_names.issubset(lifted_names):
        raise ValueError("broken must be a subset of lifted (by name)")

    added = tuple(name for name in lifted.names if name not in broken_names)
    records: list[dict[str, Any]] = []
    minimality_ok = True

    # Exhaustive check over every non-empty subset of added components.
    for k in range(1, len(added) + 1):
        for drop in combinations(added, k):
            kept = tuple(name for name in lifted.names if name not in set(drop))
            reduced = lifted.subset(kept)
            captured = invariant_captured(states, reduced, invariant)
            if captured:
                minimality_ok = False
            records.append(
                {
                    "dropped": list(drop),
                    "kept_names": list(kept),
                    "captures_invariant": captured,
                }
            )

    return minimality_ok, records


@dataclass(frozen=True)
class LiftPair:
    """One row of the calculus table: ``(broken, lifted)`` on a world
    ``S`` with target invariant ``I``.
    """

    key: str
    description: str
    states: tuple[State, ...] = field(compare=False)
    invariant: Callable[[State], Any] = field(compare=False)
    broken: Representation = field(compare=False)
    lifted: Representation = field(compare=False)

    def evaluate(self) -> dict[str, Any]:
        broken_misses = invariant_missed(self.states, self.broken, self.invariant)
        lifted_captures = invariant_captured(self.states, self.lifted, self.invariant)
        minimality_ok, minimality_records = lift_is_minimal(
            self.states, self.broken, self.lifted, self.invariant
        )
        return {
            "key": self.key,
            "description": self.description,
            "num_states": len(self.states),
            "broken_features": list(self.broken.names),
            "lifted_features": list(self.lifted.names),
            "added_features": [
                name for name in self.lifted.names if name not in set(self.broken.names)
            ],
            "broken_misses_invariant": broken_misses,
            "lifted_captures_invariant": lifted_captures,
            "lift_is_minimal": minimality_ok,
            "minimality_drop_records": minimality_records,
        }


# ---------- Pair 1: scalar -> operator ----------
#
# The Bloch sphere for one qubit. Every pure state has real invariants
# (<X>, <Y>, <Z>) with X^2 + Y^2 + Z^2 = 1 (Bloch unit sphere). A
# scalar Z-projection observable misses the states that differ only on
# other axes; the operator-valued lift (full Bloch vector) captures the
# full physical invariant tuple.

PAULI_STATES: tuple[str, ...] = ("|0>", "|1>", "|+>", "|->", "|i>", "|-i>")

_BLOCH_VECTOR: dict[str, tuple[int, int, int]] = {
    # (<X>, <Y>, <Z>)
    "|0>": (0, 0, 1),
    "|1>": (0, 0, -1),
    "|+>": (1, 0, 0),
    "|->": (-1, 0, 0),
    "|i>": (0, 1, 0),
    "|-i>": (0, -1, 0),
}


def _pauli_invariant(state: str) -> tuple[int, int, int]:
    return _BLOCH_VECTOR[state]


def _pauli_z(state: str) -> int:
    return _BLOCH_VECTOR[state][2]


def _pauli_x(state: str) -> int:
    return _BLOCH_VECTOR[state][0]


def _pauli_y(state: str) -> int:
    return _BLOCH_VECTOR[state][1]


PAIR_SCALAR_TO_OPERATOR = LiftPair(
    key="scalar_to_operator",
    description=(
        "Broken: Pauli-Z expectation alone (a scalar observable). Lifted:"
        " full Bloch vector (an operator-valued representation)."
    ),
    states=PAULI_STATES,
    invariant=_pauli_invariant,
    broken=Representation(names=("z",), feature_fns=(_pauli_z,)),
    lifted=Representation(
        names=("z", "x", "y"),
        feature_fns=(_pauli_z, _pauli_x, _pauli_y),
    ),
)


# ---------- Pair 2: global norm -> localized measure ----------
#
# States are 6 mass profiles on 3 spatial cells, hand-designed so every
# cell has at least one collision pair when its coordinate is dropped.
# The invariant is the full per-cell profile. The global scalar is
# ``support_size`` (number of nonzero cells), a genuinely lossy summary:
# knowing ``support_size`` and any 2 of the 3 cells' masses does NOT
# recover the third cell's mass. The lifted representation
# ``(support_size, m_0, m_1, m_2)`` restores the localized measure and is
# minimal: dropping any single cell mass creates a state pair that
# merges on the reduced representation while the invariant still
# separates them.

_GRID_STATES: tuple[str, ...] = ("s1", "s2", "s3", "s4", "s5", "s6")
_GRID_PROFILE: dict[str, tuple[int, int, int]] = {
    "s1": (1, 5, 7),
    "s2": (2, 5, 7),
    "s3": (3, 1, 7),
    "s4": (3, 2, 7),
    "s5": (5, 5, 1),
    "s6": (5, 5, 2),
}


def _grid_invariant(state: str) -> tuple[int, int, int]:
    return _GRID_PROFILE[state]


def _grid_support_size(state: str) -> int:
    return sum(1 for v in _GRID_PROFILE[state] if v != 0)


def _grid_m0(state: str) -> int:
    return _GRID_PROFILE[state][0]


def _grid_m1(state: str) -> int:
    return _GRID_PROFILE[state][1]


def _grid_m2(state: str) -> int:
    return _GRID_PROFILE[state][2]


PAIR_GLOBAL_NORM_TO_LOCALIZED_MEASURE = LiftPair(
    key="global_norm_to_localized_measure",
    description=(
        "Broken: a single global scalar summary (support size, the number"
        " of nonzero cells). Lifted: the per-cell mass profile"
        " ``(m_0, m_1, m_2)`` -- a localized measure."
    ),
    states=_GRID_STATES,
    invariant=_grid_invariant,
    broken=Representation(
        names=("support_size",), feature_fns=(_grid_support_size,)
    ),
    lifted=Representation(
        names=("support_size", "m0", "m1", "m2"),
        feature_fns=(_grid_support_size, _grid_m0, _grid_m1, _grid_m2),
    ),
)


# ---------- Pair 3: quotient -> restored fiber ----------
#
# Instrument-4-style world with a coarse quotient ``z`` and two extra
# in-fiber bits ``x, y``. Broken: only the quotient ``z``. Lifted: the
# whole tuple ``(z, x, y)`` -- the fiber is *restored*.

_FIBER_STATES: tuple[tuple[int, int, int], ...] = tuple(
    (z, x, y) for z, x, y in product((0, 1), (0, 1), (0, 1))
)


def _fiber_invariant(state: tuple[int, int, int]) -> tuple[int, int, int]:
    return state


def _fiber_z(state: tuple[int, int, int]) -> int:
    return state[0]


def _fiber_x(state: tuple[int, int, int]) -> int:
    return state[1]


def _fiber_y(state: tuple[int, int, int]) -> int:
    return state[2]


PAIR_QUOTIENT_TO_RESTORED_FIBER = LiftPair(
    key="quotient_to_restored_fiber",
    description=(
        "Broken: coarse quotient label ``z`` only (fibers collapsed)."
        " Lifted: ``(z, x, y)`` restoring the in-fiber coordinates."
    ),
    states=_FIBER_STATES,
    invariant=_fiber_invariant,
    broken=Representation(names=("z",), feature_fns=(_fiber_z,)),
    lifted=Representation(
        names=("z", "x", "y"),
        feature_fns=(_fiber_z, _fiber_x, _fiber_y),
    ),
)


# ---------- Pair 4: static -> path space ----------
#
# 8 length-3 binary trajectories. Invariant: the full trajectory. Broken:
# the current (last) coordinate only. Lifted: current + past coordinates.

_PATH_STATES: tuple[tuple[int, int, int], ...] = tuple(
    (a, b, c) for a, b, c in product((0, 1), (0, 1), (0, 1))
)


def _path_invariant(state: tuple[int, int, int]) -> tuple[int, int, int]:
    return state


def _path_current(state: tuple[int, int, int]) -> int:
    return state[2]


def _path_t0(state: tuple[int, int, int]) -> int:
    return state[0]


def _path_t1(state: tuple[int, int, int]) -> int:
    return state[1]


PAIR_STATIC_TO_PATH_SPACE = LiftPair(
    key="static_to_path_space",
    description=(
        "Broken: current-step scalar (a static observable). Lifted:"
        " the full trajectory (path-space representation)."
    ),
    states=_PATH_STATES,
    invariant=_path_invariant,
    broken=Representation(names=("current",), feature_fns=(_path_current,)),
    lifted=Representation(
        names=("current", "t0", "t1"),
        feature_fns=(_path_current, _path_t0, _path_t1),
    ),
)


# ---------- Pair 5: affine -> projective ----------
#
# States are 6 projective points (a : b : c). Two of them are affinely
# indistinguishable but projectively distinct because their ``c`` values
# differ (a finite point vs a point at infinity). The affine chart drops
# the ``c`` component and merges them; the projective (homogeneous)
# representation keeps ``c`` and separates them.

_PROJ_STATES: tuple[tuple[int, int, int], ...] = (
    (1, 0, 1),
    (0, 1, 1),
    (2, 3, 1),
    (2, 3, 0),
    (5, 0, 1),
    (2, 5, 1),
)


def _proj_invariant(state: tuple[int, int, int]) -> tuple[int, int, int]:
    return state


def _proj_a(state: tuple[int, int, int]) -> int:
    return state[0]


def _proj_b(state: tuple[int, int, int]) -> int:
    return state[1]


def _proj_c(state: tuple[int, int, int]) -> int:
    return state[2]


PAIR_AFFINE_TO_PROJECTIVE = LiftPair(
    key="affine_to_projective",
    description=(
        "Broken: affine chart ``(a, b)`` (the ``c = 1`` slice). Lifted:"
        " homogeneous coordinates ``(a, b, c)`` restoring points at"
        " infinity."
    ),
    states=_PROJ_STATES,
    invariant=_proj_invariant,
    broken=Representation(names=("a", "b"), feature_fns=(_proj_a, _proj_b)),
    lifted=Representation(
        names=("a", "b", "c"),
        feature_fns=(_proj_a, _proj_b, _proj_c),
    ),
)


# ---------- Pair 6: point -> ensemble ----------
#
# Eight (mean, variance, skew) triples for distinct distributions.
# The invariant is the full moment vector. Point estimates (mean only)
# merge distributions with the same mean; the ensemble (mean, var, skew)
# separates them.

_ENSEMBLE_STATES: tuple[tuple[int, int, int], ...] = tuple(
    (m, v, s) for m, v, s in product((0, 1), (1, 2), (0, 1))
)


def _ensemble_invariant(state: tuple[int, int, int]) -> tuple[int, int, int]:
    return state


def _ensemble_mean(state: tuple[int, int, int]) -> int:
    return state[0]


def _ensemble_var(state: tuple[int, int, int]) -> int:
    return state[1]


def _ensemble_skew(state: tuple[int, int, int]) -> int:
    return state[2]


PAIR_POINT_TO_ENSEMBLE = LiftPair(
    key="point_to_ensemble",
    description=(
        "Broken: point estimate (mean alone). Lifted: ensemble moment"
        " vector ``(mean, variance, skew)``."
    ),
    states=_ENSEMBLE_STATES,
    invariant=_ensemble_invariant,
    broken=Representation(names=("mean",), feature_fns=(_ensemble_mean,)),
    lifted=Representation(
        names=("mean", "var", "skew"),
        feature_fns=(_ensemble_mean, _ensemble_var, _ensemble_skew),
    ),
)


# ---------- Pair 7: non-composing -> interface ----------
#
# States are all 16 module-pair configurations ``(m1, m2, protocol_family,
# protocol_version)``. The invariant is the full tuple (whether the
# modules actually communicate). The non-composing broken rep is
# ``(m1, m2)`` alone -- it cannot distinguish handshake protocols. The
# interface lift adds the protocol tag so the composition is well-defined.
# Using the full 2 x 2 x 2 x 2 product ensures every added component has
# a collision pair that forces the drop test to break.

_INTERFACE_STATES: tuple[tuple[str, str, str, int], ...] = tuple(
    (m1, m2, family, version)
    for m1, m2, family, version in product(
        ("P", "Q"), ("P", "Q"), ("json", "grpc"), (1, 2)
    )
)


def _interface_invariant(
    state: tuple[str, str, str, int],
) -> tuple[str, str, str, int]:
    return state


def _interface_m1(state: tuple[str, str, str, int]) -> str:
    return state[0]


def _interface_m2(state: tuple[str, str, str, int]) -> str:
    return state[1]


def _interface_family(state: tuple[str, str, str, int]) -> str:
    return state[2]


def _interface_version(state: tuple[str, str, str, int]) -> int:
    return state[3]


PAIR_NON_COMPOSING_TO_INTERFACE = LiftPair(
    key="non_composing_to_interface",
    description=(
        "Broken: raw module identity pair ``(m1, m2)`` with no protocol"
        " tag (composition is ill-defined). Lifted: ``(m1, m2, family,"
        " version)`` where the protocol tag is the explicit interface."
    ),
    states=_INTERFACE_STATES,
    invariant=_interface_invariant,
    broken=Representation(
        names=("m1", "m2"),
        feature_fns=(_interface_m1, _interface_m2),
    ),
    lifted=Representation(
        names=("m1", "m2", "family", "version"),
        feature_fns=(
            _interface_m1,
            _interface_m2,
            _interface_family,
            _interface_version,
        ),
    ),
)


# ---------- Pair 8: symmetry -> gauge-fix ----------
#
# States are 6 configurations parameterised by ``(a, b, c)`` with a
# translation symmetry ``(a, b, c) ~ (a+t, b+t, c+t)``. The physical
# invariant is the orbit label ``(a-b, a-c)`` (translation-invariant).
# The gauge-dependent scalar ``a`` alone can neither identify a physical
# state (many raw ``(a, b, c)`` share the same ``a``) nor is it
# translation-invariant. The gauge-fixed lift adds the two invariant
# offsets ``(a-b, a-c)``, which are gauge-invariant scalars.

_GAUGE_STATES: tuple[tuple[int, int, int], ...] = (
    (0, 1, 2),
    (1, 2, 3),
    (0, 2, 1),
    (5, 7, 6),
    (0, 0, 0),
    (0, 1, 1),
)


def _gauge_invariant(state: tuple[int, int, int]) -> tuple[int, int]:
    return (state[0] - state[1], state[0] - state[2])


def _gauge_a(state: tuple[int, int, int]) -> int:
    return state[0]


def _gauge_ab(state: tuple[int, int, int]) -> int:
    return state[0] - state[1]


def _gauge_ac(state: tuple[int, int, int]) -> int:
    return state[0] - state[2]


PAIR_SYMMETRY_TO_GAUGE_FIX = LiftPair(
    key="symmetry_to_gauge_fix",
    description=(
        "Broken: gauge-dependent scalar ``a`` under translation"
        " symmetry ``(a, b, c) ~ (a+t, b+t, c+t)``. Lifted:"
        " gauge-invariant offsets ``(a, a-b, a-c)`` making the orbit"
        " label recoverable."
    ),
    states=_GAUGE_STATES,
    invariant=_gauge_invariant,
    broken=Representation(names=("a",), feature_fns=(_gauge_a,)),
    lifted=Representation(
        names=("a", "a_minus_b", "a_minus_c"),
        feature_fns=(_gauge_a, _gauge_ab, _gauge_ac),
    ),
)


# ---------- Canonical eight-pair table ----------


PAIRS: tuple[LiftPair, ...] = (
    PAIR_SCALAR_TO_OPERATOR,
    PAIR_GLOBAL_NORM_TO_LOCALIZED_MEASURE,
    PAIR_QUOTIENT_TO_RESTORED_FIBER,
    PAIR_STATIC_TO_PATH_SPACE,
    PAIR_AFFINE_TO_PROJECTIVE,
    PAIR_POINT_TO_ENSEMBLE,
    PAIR_NON_COMPOSING_TO_INTERFACE,
    PAIR_SYMMETRY_TO_GAUGE_FIX,
)


# ---------- Composition (Theorem RR-2) ----------
#
# Compose the ``scalar -> operator`` lift with the ``static -> path
# space`` lift on the product world ``PauliStates x PathStates``.
# Independence of the two failure modes is guaranteed by the product
# structure: each lift acts on a disjoint slot.
#
# Composite invariant: ``(I_pauli(a), I_path(b))``.
# Composite broken:    ``(z_a, current_b)``.
# Composite lifted:    ``(z_a, x_a, y_a, current_b, t0_b, t1_b)``.
#
# We check that the composed lifted representation captures the
# composite invariant, that removing any added component breaks capture,
# and that the composite lift is exactly the pointwise pairing of the
# two individual lifts (they commute).


ProductState = tuple[str, tuple[int, int, int]]


def _product_states() -> tuple[ProductState, ...]:
    return tuple(
        (pauli, path)
        for pauli in PAULI_STATES
        for path in _PATH_STATES
    )


def _product_invariant(
    state: ProductState,
) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    pauli, path = state
    return (_pauli_invariant(pauli), _path_invariant(path))


def _pair_feature(
    first_fn: Callable[[str], Any] | None,
    second_fn: Callable[[tuple[int, int, int]], Any] | None,
) -> Callable[[ProductState], Any]:
    def wrapped(state: ProductState) -> Any:
        pauli, path = state
        left = first_fn(pauli) if first_fn is not None else None
        right = second_fn(path) if second_fn is not None else None
        if first_fn is None:
            return right
        if second_fn is None:
            return left
        return (left, right)

    return wrapped


def build_composite_broken() -> Representation:
    return Representation(
        names=("z_a", "current_b"),
        feature_fns=(
            _pair_feature(_pauli_z, None),
            _pair_feature(None, _path_current),
        ),
    )


def build_composite_lifted() -> Representation:
    return Representation(
        names=("z_a", "x_a", "y_a", "current_b", "t0_b", "t1_b"),
        feature_fns=(
            _pair_feature(_pauli_z, None),
            _pair_feature(_pauli_x, None),
            _pair_feature(_pauli_y, None),
            _pair_feature(None, _path_current),
            _pair_feature(None, _path_t0),
            _pair_feature(None, _path_t1),
        ),
    )


def evaluate_composition() -> dict[str, Any]:
    states = _product_states()
    broken = build_composite_broken()
    lifted = build_composite_lifted()

    broken_misses_left = invariant_missed(
        states, broken, lambda s: _pauli_invariant(s[0])
    )
    broken_misses_right = invariant_missed(
        states, broken, lambda s: _path_invariant(s[1])
    )
    broken_misses_composite = invariant_missed(states, broken, _product_invariant)

    lifted_captures_left = invariant_captured(
        states, lifted, lambda s: _pauli_invariant(s[0])
    )
    lifted_captures_right = invariant_captured(
        states, lifted, lambda s: _path_invariant(s[1])
    )
    lifted_captures_composite = invariant_captured(
        states, lifted, _product_invariant
    )

    minimality_ok, minimality_records = lift_is_minimal(
        states, broken, lifted, _product_invariant
    )

    # Commutativity check: composing the two independent lifts on their
    # respective slots yields the same feature-tuple regardless of order.
    left_first = tuple(_pair_feature(fn, None) for fn in (_pauli_x, _pauli_y))
    right_first = tuple(_pair_feature(None, fn) for fn in (_path_t0, _path_t1))
    ordering_1 = Representation(
        names=("z_a", "current_b", "x_a", "y_a", "t0_b", "t1_b"),
        feature_fns=(
            _pair_feature(_pauli_z, None),
            _pair_feature(None, _path_current),
            *left_first,
            *right_first,
        ),
    )
    ordering_2 = Representation(
        names=("z_a", "current_b", "t0_b", "t1_b", "x_a", "y_a"),
        feature_fns=(
            _pair_feature(_pauli_z, None),
            _pair_feature(None, _path_current),
            *right_first,
            *left_first,
        ),
    )
    lifts_commute_capture_agrees = invariant_captured(
        states, ordering_1, _product_invariant
    ) and invariant_captured(states, ordering_2, _product_invariant)

    # The composed lifted rep captures BOTH sub-invariants simultaneously.
    return {
        "product_world_size": len(states),
        "broken_features": list(broken.names),
        "lifted_features": list(lifted.names),
        "broken_misses_scalar_operator_invariant": broken_misses_left,
        "broken_misses_static_path_invariant": broken_misses_right,
        "broken_misses_composite_invariant": broken_misses_composite,
        "lifted_captures_scalar_operator_invariant": lifted_captures_left,
        "lifted_captures_static_path_invariant": lifted_captures_right,
        "lifted_captures_composite_invariant": lifted_captures_composite,
        "composite_lift_is_minimal": minimality_ok,
        "composite_minimality_drop_records": minimality_records,
        "lifts_commute_capture_agrees_across_orderings": (
            lifts_commute_capture_agrees
        ),
    }


# ---------- Benchmark harness ----------


def evaluate_benchmark() -> dict[str, Any]:
    pair_records = [pair.evaluate() for pair in PAIRS]

    all_broken_miss = all(record["broken_misses_invariant"] for record in pair_records)
    all_lifted_capture = all(
        record["lifted_captures_invariant"] for record in pair_records
    )
    all_minimal = all(record["lift_is_minimal"] for record in pair_records)

    composition = evaluate_composition()

    two_independent_lifts_compose = (
        composition["lifted_captures_composite_invariant"]
        and composition["lifted_captures_scalar_operator_invariant"]
        and composition["lifted_captures_static_path_invariant"]
        and composition["composite_lift_is_minimal"]
        and composition["lifts_commute_capture_agrees_across_orderings"]
    )

    gates = {
        "rr1_every_canonical_pair_broken_representation_misses_invariant": (
            all_broken_miss
        ),
        "rr1_every_lifted_representation_captures_invariant": all_lifted_capture,
        "rr1_every_lift_is_minimal": all_minimal,
        "rr2_two_independent_lifts_compose": two_independent_lifts_compose,
    }
    status = "pass" if all(gates.values()) else "fail"
    return {
        "status": status,
        "gates": gates,
        "num_pairs": len(pair_records),
        "pair_records": pair_records,
        "composition": composition,
    }
