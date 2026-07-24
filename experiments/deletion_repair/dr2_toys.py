"""DR2 — scaled toy systems where a nominator is actually necessary.

DR1's setting did not need a nominator: 21 candidates, each cheap to verify, so
exhaustive search *is* the answer. A nominator only earns its keep when
enumeration is expensive. DR2 scales until that is true:

* ``|R_deletable| = 20`` and ``|D| <= 3`` gives **1350** candidates.
* The load-bearing base rate is driven far below DR1's, so a random ordering
  performs badly and ``verifications-to-first-hit`` becomes the honest metric.

Both toys keep DR1's shapes so the dominance question survives:

**SK -- Scaled Kinematics** (weakness-shaped). Three *entangled facets* of one
commitment -- absolute simultaneity, no length contraction, no time dilation --
each of which pins the same dial. No subset of them frees anything; only the
full triple does. A nominator scoring singletons or pairs cannot see it.

**ST -- Scaled Transduction** (cost-shaped). Dropping sequential update
collapses parallel depth, but leaves a **dangling obligation**: without
recurrence there is no order information, so the deletion only covers the
parent task when the no-positional-input commitment is dropped alongside it.
That mirrors the real case, where removing recurrence forced positional
encodings.
"""

from __future__ import annotations

import math
from typing import Final, Mapping

from experiments.deletion_repair.toys import Proposition, ToySystem


__all__ = ["build_scaled_kinematics", "build_scaled_transduction", "dr2_toys"]

#: Nuisance propositions padding ``R`` out to 20 deletable commitments. Each
#: pins one inert bit, so deleting it frees hypotheses without ever helping --
#: these are the negatives, and there are many of them on purpose.
_N_NUISANCE_KINEMATICS: Final[int] = 16
_N_NUISANCE_TRANSDUCTION: Final[int] = 16

_ALPHA_V: Final[tuple[float, ...]] = (0.01, 0.02, 0.05)
_OMEGA_V: Final[tuple[float, ...]] = (0.3, 0.6, 0.9)
_ALPHA_X: Final[float] = 0.01
_ALPHA_TOL: Final[float] = 1e-2
_OMEGA_TOL: Final[float] = 1e-9

_K_STEPS: Final[int] = 17


def _sk_transform(h: Mapping[str, float], v: float) -> tuple[float, float, float, float]:
    k = float(h["k"])
    gamma = (1.0 - v * v) ** (-k / 2.0) if v * v < 1.0 else math.inf
    return (gamma, -gamma * v, -k * gamma * v, gamma)


def _sk_fits_alpha(h: Mapping[str, float]) -> bool:
    x = _ALPHA_X
    for v in _ALPHA_V:
        a, b, c, d = _sk_transform(h, v)
        if not math.isfinite(a):
            return False
        if abs((a * x + b) - (x - v)) > _ALPHA_TOL:
            return False
        if abs((c * x + d) - 1.0) > _ALPHA_TOL:
            return False
    return True


def _sk_fits_omega(h: Mapping[str, float]) -> bool:
    """Light-ray invariance -- satisfied only by the fully mixed member."""
    for v in _OMEGA_V:
        a, b, c, d = _sk_transform(h, v)
        if not math.isfinite(a):
            return False
        if abs((a + b) - (c + d)) > _OMEGA_TOL:
            return False
    return True


def build_scaled_kinematics() -> ToySystem:
    """20 deletable propositions; the load-bearing deletion is a facet TRIPLE."""
    hypotheses: list[Mapping[str, float]] = []
    for k_i in range(_K_STEPS):
        for nuisance in range(4):
            hypotheses.append(
                {
                    "k": k_i / (_K_STEPS - 1),
                    "cost": 1.0,  # flat: cost must stay silent on this toy
                    "n0": float(nuisance & 1),
                    "n1": float((nuisance >> 1) & 1),
                }
            )

    props: list[Proposition] = [
        Proposition(
            "absolute_simultaneity", lambda h: h["k"] == 0.0, True,
            "facet 1 of 3 -- alone it frees nothing",
        ),
        Proposition(
            "no_length_contraction", lambda h: h["k"] == 0.0, True,
            "facet 2 of 3 -- alone it frees nothing",
        ),
        Proposition(
            "no_time_dilation", lambda h: h["k"] == 0.0, True,
            "facet 3 of 3 -- only the full triple frees the dial",
        ),
        Proposition(
            "preferred_rest_frame", lambda h: h["n0"] == 1.0, True,
            "the Lorentz-without-Einstein trap: enlarges the extension, reaches nothing",
        ),
    ]
    # Inert padding. Each pins a bit that no task depends on.
    for i in range(_N_NUISANCE_KINEMATICS):
        bit = "n0" if i % 2 == 0 else "n1"
        props.append(
            Proposition(
                f"nuisance_{i:02d}",
                (lambda b: (lambda h: h[b] == 1.0))(bit),
                True,
                "NEGATIVE",
            )
        )
    props.append(Proposition("linear_transform", lambda _h: True, False, "INVARIANT"))

    return ToySystem(
        name="scaled_kinematics",
        hypotheses=tuple(hypotheses),
        propositions=tuple(props),
        fits_alpha=_sk_fits_alpha,
        fits_omega=_sk_fits_omega,
        cost=lambda h: float(h["cost"]),
        omega_cost_budget=math.inf,
    )


_ST_LENGTH: Final[int] = 64
_ST_OMEGA_DEPTH: Final[float] = 8.0
_ST_ALPHA_DEPTH: Final[float] = 1024.0


def _st_depth(h: Mapping[str, float]) -> float:
    return float(_ST_LENGTH) if h["sequential"] == 1.0 else 1.0


def _st_fits_omega(h: Mapping[str, float]) -> bool:
    """The parent task needs order information AND global access.

    Recurrence supplies order implicitly. Delete it and the obligation dangles:
    only a scheme carrying an explicit positional signal can still solve the
    task. This is the dangling-obligation slot of the schema.
    """
    has_order = h["sequential"] == 1.0 or h["positional"] == 1.0
    return has_order and _st_depth(h) <= _ST_OMEGA_DEPTH


def build_scaled_transduction() -> ToySystem:
    """20 deletable propositions; the load-bearing deletion must discharge an obligation."""
    hypotheses: list[Mapping[str, float]] = []
    for sequential in (0.0, 1.0):
        for positional in (0.0, 1.0):
            for nuisance in range(4):
                hypotheses.append(
                    {
                        "sequential": sequential,
                        "positional": positional,
                        "n0": float(nuisance & 1),
                        "n1": float((nuisance >> 1) & 1),
                    }
                )

    props: list[Proposition] = [
        Proposition(
            "sequential_state_update", lambda h: h["sequential"] == 1.0, True,
            "the over-specification: costs depth, not expressivity",
        ),
        Proposition(
            "no_positional_input", lambda h: h["positional"] == 0.0, True,
            "the DANGLING OBLIGATION -- must be dropped alongside recurrence",
        ),
    ]
    for i in range(_N_NUISANCE_TRANSDUCTION + 2):
        bit = "n0" if i % 2 == 0 else "n1"
        props.append(
            Proposition(
                f"nuisance_{i:02d}",
                (lambda b: (lambda h: h[b] == 1.0))(bit),
                True,
                "NEGATIVE",
            )
        )
    props.append(Proposition("finite_sequence", lambda _h: True, False, "INVARIANT"))

    return ToySystem(
        name="scaled_transduction",
        hypotheses=tuple(hypotheses),
        propositions=tuple(props),
        fits_alpha=lambda h: _st_depth(h) <= _ST_ALPHA_DEPTH,
        fits_omega=_st_fits_omega,
        cost=_st_depth,
        omega_cost_budget=_ST_OMEGA_DEPTH,
    )


def dr2_toys() -> tuple[ToySystem, ...]:
    return (build_scaled_kinematics(), build_scaled_transduction())
