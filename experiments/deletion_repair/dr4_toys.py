"""DR4 — DR3's formalisation with the costly toy's base rate repaired.

DR3's H4'' failed on a gate that was unachievable by construction:
``speedup = expected_random / verifications`` with ``verifications >= 1``, so
speedup is bounded above by ``expected_random``, which depends only on the
toy's base rate. DR3's costly toy had 191 load-bearing candidates of 1350 --
14% -- capping speedup at 7x against a 10x gate.

DR3's paper named the repair: **lower the base rate by tightening the parent
budget**, not by lowering the threshold. DR4 does exactly that.

The mechanism is principled rather than cosmetic. In DR3 a single costly
commitment (64 units) exceeded the budget (8), so *any* deletion containing it
sufficed and 191 candidates qualified. In DR4 the budget is tight enough that
**all three** costly commitments must be released together. Only one deletion
does that, so the base rate falls to 1/1350 -- matching the restrictive toy,
and putting ``expected_random`` at 675.5 where a 10x gate is reachable.

This also sharpens the analogy. The real move is rarely "drop one thing": it is
drop the constraint *and* discharge what the constraint was silently
providing. DR4's costly toy requires releasing an entangled set, exactly as
DR3's restrictive toy requires the entangled facet triple.
"""

from __future__ import annotations

import math
from typing import Final

from experiments.deletion_repair.dr3_toys import (
    DR3Toy,
    _nuisance,
    build_restrictive_toy,
)
from experiments.deletion_repair.toys import Proposition, ToySystem


__all__ = ["build_calibrated_costly_toy", "dr4_toys"]

_N_NUISANCE: Final[int] = 17

#: Three commitments that must ALL be released to meet the parent budget.
_COSTLY: Final[dict[str, float]] = {
    "sequential_schedule": 64.0,
    "checkpoint_every_step": 4.0,
    "sync_barrier": 2.0,
}
#: Tight enough that no proper subset of the three suffices: dropping the two
#: largest still leaves 2 > 1.
_OMEGA_BUDGET: Final[float] = 1.0


def build_calibrated_costly_toy() -> DR3Toy:
    """CT4 — costly-only, with a base rate low enough for the speedup gate.

    Every costly proposition is **vacuous as a predicate**: each is satisfied by
    every hypothesis, so deleting any of them leaves the extension identical and
    ``weakness_gain == 0`` exactly. Only the resource commitment changes. This
    keeps DR3's independence property while fixing its base rate.
    """
    hypotheses = [
        {"expressive": 1.0, "n0": float(n & 1), "n1": float((n >> 1) & 1)}
        for n in range(4)
    ]

    props: list[Proposition] = [
        Proposition(
            name,
            lambda _h: True,
            True,
            f"VACUOUS predicate, COSTLY commitment ({cost} units)",
        )
        for name, cost in _COSTLY.items()
    ]
    props += [_nuisance(i) for i in range(_N_NUISANCE)]
    props.append(Proposition("finite_sequence", lambda _h: True, False, "INVARIANT"))

    costs: dict[str, float] = {p.name: 0.0 for p in props}
    costs.update(_COSTLY)

    system = ToySystem(
        name="calibrated_costly_transduction",
        hypotheses=tuple(hypotheses),
        propositions=tuple(props),
        fits_alpha=lambda _h: True,
        fits_omega=lambda h: h["expressive"] == 1.0,
        cost=lambda _h: 1.0,
        omega_cost_budget=math.inf,
    )
    return DR3Toy(
        name="calibrated_costly_transduction",
        system=system,
        proposition_costs=costs,
        representation_budget=_OMEGA_BUDGET,
    )


def dr4_toys() -> tuple[DR3Toy, ...]:
    """The restrictive toy unchanged from DR3, plus the recalibrated costly one."""
    return (build_restrictive_toy(), build_calibrated_costly_toy())
