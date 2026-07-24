"""DR1 — the two toy systems.

Both expose the same five-slot interface so one harness scores both:

* ``hypotheses``   -- finite hypothesis space ``H``
* ``propositions`` -- each a predicate filtering ``H``; ``deletable`` flags
                      which may enter a candidate deletion ``D``
* ``fits_alpha``   -- does a hypothesis solve the child task?
* ``fits_omega``   -- does a hypothesis solve the parent task?
* ``cost``         -- resource measure, and ``omega_cost_budget``

TK is relativity-shaped: the load-bearing deletion enlarges the extension, so
**weakness** should fire and cost should be silent.

TT is attention-shaped: the load-bearing deletion leaves the expressible
function set unchanged but collapses parallel depth, so **cost** should fire
and weakness should be silent.

Neither toy contains relativity or attention. They are miniatures of the
*shape* of those moves -- an over-specification fitted to a child task that
excludes what the parent task needs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Final, Mapping, Sequence


__all__ = ["Proposition", "ToySystem", "build_toy_kinematics", "build_toy_transduction"]


@dataclass(frozen=True)
class Proposition:
    """One commitment in ``R``, acting as a predicate over the hypothesis space."""

    name: str
    predicate: Callable[[Mapping[str, float]], bool]
    deletable: bool
    note: str = ""


@dataclass(frozen=True)
class ToySystem:
    """A five-slot discovery-shaped problem over a finite hypothesis space."""

    name: str
    hypotheses: tuple[Mapping[str, float], ...]
    propositions: tuple[Proposition, ...]
    fits_alpha: Callable[[Mapping[str, float]], bool]
    fits_omega: Callable[[Mapping[str, float]], bool]
    cost: Callable[[Mapping[str, float]], float]
    omega_cost_budget: float

    @property
    def deletable(self) -> tuple[Proposition, ...]:
        return tuple(p for p in self.propositions if p.deletable)

    def extension(self, dropped: frozenset[str] = frozenset()) -> tuple[Mapping[str, float], ...]:
        """Hypotheses satisfying every proposition except those in ``dropped``."""
        active = [p for p in self.propositions if p.name not in dropped]
        return tuple(h for h in self.hypotheses if all(p.predicate(h) for p in active))


# --------------------------------------------------------------------------- #
# TK -- Toy Kinematics (relativity-shaped)
# --------------------------------------------------------------------------- #

#: Velocities used by the child task. Galilean and Lorentz agree to tolerance
#: here, so alpha genuinely fails to discriminate.
_ALPHA_V: Final[tuple[float, ...]] = (0.01, 0.02, 0.05)
#: The parent task probes a regime where the two diverge.
_OMEGA_V: Final[tuple[float, ...]] = (0.3, 0.6, 0.9)
_ALPHA_TOL: Final[float] = 1e-2
#: Child-task probe event. Small ``x`` keeps the ``v*x`` term negligible, which
#: is exactly the regime in which the low-velocity limit is a good description.
_ALPHA_X: Final[float] = 0.01
_OMEGA_TOL: Final[float] = 1e-9


def _transform(h: Mapping[str, float], v: float) -> tuple[float, float, float, float]:
    """Return ``(A, B, C, D)`` for the transform ``h`` at relative velocity ``v``.

    ``k`` mixes position into the time coordinate; ``p`` sets the dilation
    exponent. ``k = p = 0`` is the Galilean member, ``k = p = 1`` the Lorentz
    member. The two are entangled by construction in the same way length
    contraction and relativity of simultaneity are entangled in the real case.
    """
    k = float(h["k"])
    # ``p`` is not an independent dial: dilation is a facet of time mixing, in
    # the same way length contraction follows from relativity of simultaneity.
    p = k
    gamma = (1.0 - v * v) ** (-p / 2.0) if v * v < 1.0 else math.inf
    return (gamma, -gamma * v, -k * gamma * v, gamma)


def _tk_light_invariant(h: Mapping[str, float]) -> bool:
    """A light ray ``x = t`` must map to ``x' = t'`` at every parent velocity."""
    for v in _OMEGA_V:
        a, b, c, d = _transform(h, v)
        if not math.isfinite(a):
            return False
        x_out = a * 1.0 + b * 1.0
        t_out = c * 1.0 + d * 1.0
        if abs(x_out - t_out) > _OMEGA_TOL:
            return False
    return True


def _tk_matches_galilean_at_low_v(h: Mapping[str, float]) -> bool:
    """The child task: agree with the low-velocity limit to tolerance."""
    x = _ALPHA_X
    for v in _ALPHA_V:
        a, b, c, d = _transform(h, v)
        if not math.isfinite(a):
            return False
        # Reference is the low-velocity limit: x' = x - v t, t' = t.
        if abs((a * x + b * 1.0) - (x - v)) > _ALPHA_TOL:
            return False
        if abs((c * x + d * 1.0) - 1.0) > _ALPHA_TOL:
            return False
    return True


def build_toy_kinematics() -> ToySystem:
    """Relativity-shaped toy: the load-bearing deletion enlarges the extension."""
    hypotheses: list[Mapping[str, float]] = []
    for k_i in range(0, 9):
        for ether in (0.0, 1.0):
            hypotheses.append(
                {
                    "k": k_i / 8.0,
                    # Carried but inert for TK: cost is flat, so cost must stay
                    # silent on this toy. That silence is part of the finding.
                    "cost": 1.0,
                    "ether": ether,
                    "mass_invariant": 1.0,
                    "orientation": 1.0,
                }
            )

    props = (
        Proposition(
            "absolute_simultaneity",
            lambda h: h["k"] == 0.0,
            True,
            "time mixing is forbidden -- the load-bearing over-specification",
        ),
        Proposition(
            "no_length_contraction",
            lambda h: h["k"] == 0.0,
            True,
            "an entangled FACET of the same commitment -- also load-bearing",
        ),
        Proposition(
            "preferred_rest_frame",
            lambda h: h["ether"] == 1.0,
            True,
            "ether-shaped: droppable, enlarges the extension, but does NOT "
            "reach omega on its own -- the Lorentz-without-Einstein trap",
        ),
        Proposition(
            "invariant_mass",
            lambda h: h["mass_invariant"] == 1.0,
            True,
            "NEGATIVE: deleting it frees nothing",
        ),
        Proposition(
            "orientation_preserving",
            lambda h: h["orientation"] == 1.0,
            True,
            "NEGATIVE: deleting it frees nothing",
        ),
        Proposition(
            "velocity_in_range",
            lambda h: 0.0 <= h["k"] <= 1.0,
            True,
            "NEGATIVE: already implied by the grid",
        ),
        Proposition(
            "linear_transform",
            lambda _h: True,
            False,
            "INVARIANT: definitional",
        ),
    )

    return ToySystem(
        name="toy_kinematics",
        hypotheses=tuple(hypotheses),
        propositions=props,
        fits_alpha=_tk_matches_galilean_at_low_v,
        fits_omega=_tk_light_invariant,
        cost=lambda h: float(h["cost"]),
        omega_cost_budget=math.inf,
    )


# --------------------------------------------------------------------------- #
# TT -- Toy Transduction (attention-shaped)
# --------------------------------------------------------------------------- #

_TT_SEQUENCE_LENGTH: Final[int] = 64
#: Parent task depth budget. Sequential schemes cost O(n) and cannot meet it.
_TT_OMEGA_DEPTH_BUDGET: Final[float] = 8.0
#: Child task budget, loose enough that both schemes pass.
_TT_ALPHA_DEPTH_BUDGET: Final[float] = 1024.0


def _tt_expresses_task(h: Mapping[str, float]) -> bool:
    """Both access patterns express the task class; only global access sees all positions.

    This is the crux of TT: expressivity does **not** separate sequential from
    parallel here, so weakness has nothing to grab. What separates them is
    depth, which is a cost.
    """
    return h["global_access"] == 1.0 or h["causal"] == 1.0


def _tt_depth(h: Mapping[str, float]) -> float:
    """Parallel depth: sequential chaining costs O(n); parallel costs O(1)."""
    return float(_TT_SEQUENCE_LENGTH) if h["sequential"] == 1.0 else 1.0


def build_toy_transduction() -> ToySystem:
    """Attention-shaped toy: the load-bearing deletion collapses cost, not extension."""
    hypotheses: list[Mapping[str, float]] = []
    for sequential in (0.0, 1.0):
        for causal in (0.0, 1.0):
            for bounded_state in (0.0, 1.0):
                for positional in (0.0, 1.0):
                    hypotheses.append(
                        {
                            "sequential": sequential,
                            "causal": causal,
                            "bounded_state": bounded_state,
                            "positional": positional,
                            # Global access is available exactly when the
                            # scheme is not forced through a sequential chain.
                            "global_access": 0.0 if sequential == 1.0 else 1.0,
                        }
                    )

    props = (
        Proposition(
            "sequential_state_update",
            lambda h: h["sequential"] == 1.0,
            True,
            "the load-bearing over-specification -- costs depth, not expressivity",
        ),
        Proposition(
            "causal_masking",
            lambda h: h["causal"] == 1.0,
            True,
            "droppable but does not relieve the depth budget",
        ),
        Proposition(
            "bounded_state",
            lambda h: h["bounded_state"] == 1.0,
            True,
            "NEGATIVE: frees nothing under the parent budget",
        ),
        Proposition(
            "no_positional_input",
            lambda h: h["positional"] == 0.0,
            True,
            "the dangling obligation a repair must discharge",
        ),
        Proposition(
            "finite_sequence",
            lambda _h: True,
            False,
            "INVARIANT: definitional",
        ),
    )

    return ToySystem(
        name="toy_transduction",
        hypotheses=tuple(hypotheses),
        propositions=props,
        fits_alpha=lambda h: _tt_expresses_task(h)
        and _tt_depth(h) <= _TT_ALPHA_DEPTH_BUDGET,
        fits_omega=_tt_expresses_task,
        cost=_tt_depth,
        omega_cost_budget=_TT_OMEGA_DEPTH_BUDGET,
    )


def all_toys() -> tuple[ToySystem, ...]:
    return (build_toy_kinematics(), build_toy_transduction())


def describe(toy: ToySystem) -> Sequence[str]:
    """Human-readable summary used in receipts."""
    return [
        f"{toy.name}: |H|={len(toy.hypotheses)} "
        f"|R|={len(toy.propositions)} deletable={len(toy.deletable)}",
        f"  extension(R) = {len(toy.extension())}",
    ]
