"""DR3 — cost moved off the extension, as DR2's theorem requires.

DR2 proved that cost attribution defined as a *minimum over the extension* can
never fire where weakness gain is silent::

    ext(R) ⊆ ext(R \\ D)  ⇒  a min over the extension improves only if it grew
                          ⇒  cost_attribution > 0  ⇒  weakness_gain > 0

The premise is the coupling. DR3 removes it: **cost attaches to the
propositions themselves**, as a resource commitment that is paid for holding
the constraint, independent of which hypotheses survive.

That is the real transformer case. "Computation proceeds sequentially" commits
you to ``O(n)`` depth whether or not it changes which functions are
expressible -- it forbids the parallel schedule rather than the parallel
function. A proposition can therefore be:

* **restrictive** -- filters the hypothesis space (weakness fires when deleted)
* **costly** -- carries a resource commitment (cost fires when deleted)
* both, or neither

The two axes are now independent by construction, which is the whole point:
DR2 showed the old formalisation made the interesting case *impossible*, so
DR3's first job is to exhibit a formalisation in which it is possible, and its
real job is to test whether the nominators and combiners actually work there.

``covers_omega`` accordingly has two conjuncts: some surviving hypothesis must
fit the parent task **semantically**, and the surviving representation's
resource commitment must meet the parent **budget**.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final, Mapping

from experiments.deletion_repair.toys import Proposition, ToySystem


__all__ = ["DR3Toy", "build_restrictive_toy", "build_costly_toy", "dr3_toys"]


@dataclass(frozen=True)
class DR3Toy:
    """A toy whose cost lives on the propositions, not on the hypotheses."""

    name: str
    system: ToySystem
    #: Resource commitment paid for *holding* each proposition.
    proposition_costs: Mapping[str, float]
    #: Parent-task budget on the representation's total commitment.
    representation_budget: float

    @property
    def deletable(self) -> tuple[Proposition, ...]:
        return self.system.deletable

    def extension(self, dropped: frozenset[str] = frozenset()):
        return self.system.extension(dropped)

    def representation_cost(self, dropped: frozenset[str] = frozenset()) -> float:
        """Total commitment of the propositions still held.

        Deliberately **not** a function of the extension. This is the line DR2's
        theorem turns on.
        """
        return sum(
            cost
            for name, cost in self.proposition_costs.items()
            if name not in dropped
        )

    def valid_on_alpha(self, dropped: frozenset[str] = frozenset()) -> bool:
        return any(self.system.fits_alpha(h) for h in self.extension(dropped))

    def covers_omega(self, dropped: frozenset[str] = frozenset()) -> bool:
        semantic = any(self.system.fits_omega(h) for h in self.extension(dropped))
        affordable = self.representation_cost(dropped) <= self.representation_budget
        return semantic and affordable


_N_NUISANCE: Final[int] = 16
_ALPHA_V: Final[tuple[float, ...]] = (0.01, 0.02, 0.05)
_OMEGA_V: Final[tuple[float, ...]] = (0.3, 0.6, 0.9)
_ALPHA_X: Final[float] = 0.01
_ALPHA_TOL: Final[float] = 1e-2
_OMEGA_TOL: Final[float] = 1e-9
_K_STEPS: Final[int] = 17


def _transform(h: Mapping[str, float], v: float):
    k = float(h["k"])
    gamma = (1.0 - v * v) ** (-k / 2.0) if v * v < 1.0 else math.inf
    return (gamma, -gamma * v, -k * gamma * v, gamma)


def _fits_alpha(h: Mapping[str, float]) -> bool:
    x = _ALPHA_X
    for v in _ALPHA_V:
        a, b, c, d = _transform(h, v)
        if not math.isfinite(a):
            return False
        if abs((a * x + b) - (x - v)) > _ALPHA_TOL:
            return False
        if abs((c * x + d) - 1.0) > _ALPHA_TOL:
            return False
    return True


def _fits_omega(h: Mapping[str, float]) -> bool:
    for v in _OMEGA_V:
        a, b, c, d = _transform(h, v)
        if not math.isfinite(a):
            return False
        if abs((a + b) - (c + d)) > _OMEGA_TOL:
            return False
    return True


def _nuisance(i: int) -> Proposition:
    bit = "n0" if i % 2 == 0 else "n1"
    return Proposition(
        f"nuisance_{i:02d}",
        (lambda b: (lambda h: h[b] == 1.0))(bit),
        True,
        "NEGATIVE",
    )


def build_restrictive_toy() -> DR3Toy:
    """RK — restrictive-only. Weakness must fire; cost must be silent.

    Every proposition carries zero resource commitment, so the representation
    cost is identically zero and cost attribution has nothing to say. The
    load-bearing deletion is the entangled facet triple, as in DR2.
    """
    hypotheses = [
        {"k": k_i / (_K_STEPS - 1), "n0": float(n & 1), "n1": float((n >> 1) & 1)}
        for k_i in range(_K_STEPS)
        for n in range(4)
    ]
    props: list[Proposition] = [
        Proposition("absolute_simultaneity", lambda h: h["k"] == 0.0, True, "facet 1/3"),
        Proposition("no_length_contraction", lambda h: h["k"] == 0.0, True, "facet 2/3"),
        Proposition("no_time_dilation", lambda h: h["k"] == 0.0, True, "facet 3/3"),
        Proposition("preferred_rest_frame", lambda h: h["n0"] == 1.0, True, "the trap"),
    ]
    props += [_nuisance(i) for i in range(_N_NUISANCE)]
    props.append(Proposition("linear_transform", lambda _h: True, False, "INVARIANT"))

    system = ToySystem(
        name="restrictive_kinematics",
        hypotheses=tuple(hypotheses),
        propositions=tuple(props),
        fits_alpha=_fits_alpha,
        fits_omega=_fits_omega,
        cost=lambda _h: 1.0,
        omega_cost_budget=math.inf,
    )
    return DR3Toy(
        name="restrictive_kinematics",
        system=system,
        proposition_costs={p.name: 0.0 for p in props},
        representation_budget=math.inf,
    )


_SEQ_DEPTH: Final[float] = 64.0
_OMEGA_BUDGET: Final[float] = 8.0


def build_costly_toy() -> DR3Toy:
    """CT — costly-only. Cost must fire where weakness is SILENT.

    ``sequential_schedule`` is **vacuous as a predicate**: every hypothesis
    satisfies it, because every scheme *can* be run sequentially. Deleting it
    therefore changes the extension not at all -- ``weakness_gain == 0`` exactly
    -- while removing a 64-unit depth commitment that the parent budget of 8
    cannot otherwise afford.

    This is the case DR2 proved impossible when cost was a minimum over the
    extension. Here it exists, which is what moving cost off the extension buys.
    """
    hypotheses = [
        {"expressive": 1.0, "n0": float(n & 1), "n1": float((n >> 1) & 1)}
        for n in range(4)
    ]
    props: list[Proposition] = [
        Proposition(
            "sequential_schedule",
            lambda _h: True,
            True,
            "VACUOUS predicate, COSTLY commitment -- the case DR2 ruled out",
        ),
        Proposition(
            "checkpoint_every_step",
            lambda _h: True,
            True,
            "also vacuous, also costly, but too cheap to reach the budget alone",
        ),
    ]
    props += [_nuisance(i) for i in range(_N_NUISANCE + 2)]
    props.append(Proposition("finite_sequence", lambda _h: True, False, "INVARIANT"))

    costs: dict[str, float] = {p.name: 0.0 for p in props}
    costs["sequential_schedule"] = _SEQ_DEPTH
    costs["checkpoint_every_step"] = 4.0

    system = ToySystem(
        name="costly_transduction",
        hypotheses=tuple(hypotheses),
        propositions=tuple(props),
        fits_alpha=lambda _h: True,
        fits_omega=lambda h: h["expressive"] == 1.0,
        cost=lambda _h: 1.0,
        omega_cost_budget=math.inf,
    )
    return DR3Toy(
        name="costly_transduction",
        system=system,
        proposition_costs=costs,
        representation_budget=_OMEGA_BUDGET,
    )


def dr3_toys() -> tuple[DR3Toy, ...]:
    return (build_restrictive_toy(), build_costly_toy())
