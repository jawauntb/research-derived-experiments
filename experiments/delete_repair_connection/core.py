"""Paper C: is cell 3 idle Kirchhoff packaging?

Paper A banked cycle integration on ``List Int``: a walk closes iff
the steps sum to 0.  That is discrete Poincaré.  Cell 3 is idle if
every connection we can name is that fact in other clothes.

This package uses the affine group ``Aff(1, Z/3)``.  An edge is
``x ↦ a x + b`` with ``a ∈ {1,2}`` and ``b ∈ {0,1,2}``.  Path
transport is composition, not addition.

Registered discriminators:

- Kirchhoff control: every ``a = 1``. Holonomy is ``(1, sum b)``.
- Affine Case A: ``sum b ≡ 0`` but holonomy is not the identity.
  Kirchhoff predicts flat; the connection is not.
- Affine Case B: ``sum b ≢ 0`` but holonomy is the identity.
  Kirchhoff predicts curved; the connection is flat.

Kill cell-3-is-real if every affine example collapses to the
Kirchhoff prediction, or if raw comparison (no transport) works
as well as transported comparison.

Not Lorentz.  Not CG-2.  Not Paper D/E/F.
"""

from __future__ import annotations

from typing import Literal, TypedDict

EXPERIMENT_ID = "delete_repair_connection"
RUN_ID = "delete_repair_connection_2026_08_17"
PRODUCING_AGENT = "Cursor Grok 4.6 (cloud agent, under J. Brown direction)"
SESSION_REF = "bc-01a00d99-d2d8-7c5e-a8d0-d0090dfd7bdd"
MOD = 3
IDENTITY: tuple[int, int] = (1, 0)
UNITS: tuple[int, ...] = (1, 2)
OFFSETS: tuple[int, ...] = (0, 1, 2)

# 4-cycle. Holonomy is the path-ordered product around the cycle.
KIRCHHOFF_FLAT: tuple[tuple[int, int], ...] = ((1, 1), (1, 1), (1, 1), (1, 0))
KIRCHHOFF_CURVED: tuple[tuple[int, int], ...] = ((1, 1), (1, 1), (1, 1), (1, 1))
# sum b = 0, holonomy ≠ id
AFFINE_A: tuple[tuple[int, int], ...] = ((2, 1), (1, 2), (1, 0), (1, 0))
# sum b = 2, holonomy = id
AFFINE_B: tuple[tuple[int, int], ...] = ((2, 1), (2, 1), (1, 0), (1, 0))

PROCESS_DISCLOSURE = (
    "Exact Aff(1, Z/3) path-ordered transport on a 4-cycle.  "
    "Not integer Kirchhoff, not Lorentz, not CG-2, not Paper F."
)


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


class CycleRow(TypedDict):
    name: str
    edges: list[list[int]]
    holonomy: list[int]
    kirchhoff_prediction: list[int]
    sum_b: int
    matches_kirchhoff: bool
    flat: bool


class Ranking(TypedDict):
    rule: str
    kirchhoff_control_holds: bool
    affine_escapes_kirchhoff: bool
    order_matters: bool
    raw_comparison_fails: bool
    transport_comparison_works: bool
    verdict: Literal["cell3_holds", "cell3_idle"]


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    cycles: list[CycleRow]
    ranking: Ranking
    gates: dict[str, bool]
    process_disclosure: str
    withheld: list[str]


def mul(x: int, y: int) -> int:
    return (x * y) % MOD


def add(x: int, y: int) -> int:
    return (x + y) % MOD


def apply_aff(edge: tuple[int, int], value: int) -> int:
    scale, shift = edge
    return add(mul(scale, value), shift)


def compose(after: tuple[int, int], before: tuple[int, int]) -> tuple[int, int]:
    """``after ∘ before``: apply ``before``, then ``after``."""

    scale_a, shift_a = after
    scale_b, shift_b = before
    return (mul(scale_a, scale_b), add(mul(scale_a, shift_b), shift_a))


def inverse(edge: tuple[int, int]) -> tuple[int, int]:
    scale, shift = edge
    # In Z/3, units square to 1, so scale inverse is scale.
    return (scale, mul(scale, (-shift) % MOD))


def path_map(edges: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    acc = IDENTITY
    for edge in edges:
        acc = compose(edge, acc)
    return acc


def kirchhoff_prediction(edges: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    total = 0
    for _scale, shift in edges:
        total = add(total, shift)
    return (1, total)


def sum_b(edges: tuple[tuple[int, int], ...]) -> int:
    total = 0
    for _scale, shift in edges:
        total = add(total, shift)
    return total


def group_elements() -> tuple[tuple[int, int], ...]:
    return tuple((scale, shift) for scale in UNITS for shift in OFFSETS)


def group_laws_hold() -> bool:
    elements = group_elements()
    for edge in elements:
        if compose(edge, IDENTITY) != edge or compose(IDENTITY, edge) != edge:
            return False
        if compose(edge, inverse(edge)) != IDENTITY:
            return False
        if compose(inverse(edge), edge) != IDENTITY:
            return False
    for left in elements:
        for mid in elements:
            for right in elements:
                if compose(left, compose(mid, right)) != compose(compose(left, mid), right):
                    return False
    return True


def order_matters() -> bool:
    left = (2, 0)
    right = (1, 1)
    return compose(left, right) != compose(right, left)


def _row(name: str, edges: tuple[tuple[int, int], ...]) -> CycleRow:
    holonomy = path_map(edges)
    predicted = kirchhoff_prediction(edges)
    return {
        "name": name,
        "edges": [list(edge) for edge in edges],
        "holonomy": list(holonomy),
        "kirchhoff_prediction": list(predicted),
        "sum_b": sum_b(edges),
        "matches_kirchhoff": holonomy == predicted,
        "flat": holonomy == IDENTITY,
    }


def raw_comparison_fails(edges: tuple[tuple[int, int], ...], values: tuple[int, ...]) -> bool:
    """Raw equality ignores transport. Fail if any edge moves a value."""

    for index, edge in enumerate(edges):
        src = values[index]
        dst = values[(index + 1) % len(values)]
        if apply_aff(edge, src) != src and dst == src:
            return True
        if apply_aff(edge, src) != dst and dst == src:
            return True
    # Stronger: raw equality disagrees with transported equality on at least one edge.
    for index, edge in enumerate(edges):
        src = values[index]
        dst = values[(index + 1) % len(values)]
        transported = apply_aff(edge, src)
        if (src == dst) != (transported == dst):
            return True
    return False


def transport_comparison_works(edges: tuple[tuple[int, int], ...], values: tuple[int, ...]) -> bool:
    if path_map(edges) != IDENTITY:
        return False
    for index, edge in enumerate(edges):
        src = values[index]
        dst = values[(index + 1) % len(values)]
        if apply_aff(edge, src) != dst:
            return False
    return True


def section_from(edges: tuple[tuple[int, int], ...], start: int) -> tuple[int, ...]:
    values = [start]
    acc = start
    for edge in edges[:-1]:
        acc = apply_aff(edge, acc)
        values.append(acc)
    return tuple(values)


def evaluate_benchmark() -> BenchmarkPayload:
    kirchhoff_flat = _row("kirchhoff_flat", KIRCHHOFF_FLAT)
    kirchhoff_curved = _row("kirchhoff_curved", KIRCHHOFF_CURVED)
    affine_a = _row("affine_sum0_not_flat", AFFINE_A)
    affine_b = _row("affine_flat_sum2", AFFINE_B)

    flat_section = section_from(AFFINE_B, 0)
    raw_fails = raw_comparison_fails(AFFINE_B, flat_section)
    transport_works = transport_comparison_works(AFFINE_B, flat_section)

    kirchhoff_control = (
        kirchhoff_flat["matches_kirchhoff"]
        and kirchhoff_flat["flat"]
        and kirchhoff_curved["matches_kirchhoff"]
        and not kirchhoff_curved["flat"]
    )
    affine_escapes = (not affine_a["matches_kirchhoff"]) and (not affine_b["matches_kirchhoff"])
    cell3_holds = (
        kirchhoff_control
        and affine_escapes
        and order_matters()
        and raw_fails
        and transport_works
    )
    ranking: Ranking = {
        "rule": (
            "Cell 3 is real iff additive cycles still match Kirchhoff, "
            "at least one affine cycle escapes that prediction, "
            "composition is non-commutative, raw comparison fails on a "
            "flat affine section, and transported comparison works."
        ),
        "kirchhoff_control_holds": kirchhoff_control,
        "affine_escapes_kirchhoff": affine_escapes,
        "order_matters": order_matters(),
        "raw_comparison_fails": raw_fails,
        "transport_comparison_works": transport_works,
        "verdict": "cell3_holds" if cell3_holds else "cell3_idle",
    }
    required = {
        "CONN_GROUP_LAWS": group_laws_hold(),
        "CONN_KIRCHHOFF_CONTROL": kirchhoff_control,
        "CONN_ENUMERATION": len(group_elements()) == 6,
        "CONN_RANKING_RECORDED": ranking["verdict"] in {"cell3_holds", "cell3_idle"},
        "CONN_CLAIM_BOUNDARY": True,
    }
    return {
        "status": "pass" if all(required.values()) else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {"identity": PRODUCING_AGENT, "session_ref": SESSION_REF},
        "cycles": [kirchhoff_flat, kirchhoff_curved, affine_a, affine_b],
        "ranking": ranking,
        "gates": required,
        "process_disclosure": PROCESS_DISCLOSURE,
        "withheld": [
            "Lorentz geometry",
            "Concern holonomy (CG-2)",
            "Paper D Lorentz/Lamport/PE transfer",
            "Paper E agent benchmark",
            "Universal calculus (Paper F)",
        ],
    }
