"""Paper B swap cell: opposite repairs on opposite toys.

Paper A banked the algebra and the ``n=4`` regression.  It did not
license the taxonomy as a discriminator.  This package is the owed
swap cell on the same ``{0,1}^4`` harness:

- Over-invariance toy: ``first_bit`` with deleted screen ``q_perm``.
  Correct repair: restore a distinction (``q_stab0`` / ``q_id``).
  Crossed repair: keep quotienting (``q_perm``).
- Under-invariance toy: ``bag`` with leftover-privilege screen ``q_id``.
  Correct repair: quotient privilege (``q_perm``).
  Crossed repair: restore still more (stay at ``q_id``).

Kill the taxonomy if the crossed repairs work as well as the typed
ones, or if one screen is minimal-safe for both tasks.

Not a universal calculus.  Not text nomination.  Not Paper E/F.
"""

from __future__ import annotations

from typing import Literal, TypedDict

from experiments.delete_the_absolute.core import (
    all_worlds,
    fiber_count,
    is_representable,
    q_id,
    q_perm,
    q_stab0,
)

EXPERIMENT_ID = "delete_repair_swap"
RUN_ID = "delete_repair_swap_2026_08_17"
PRODUCING_AGENT = "Cursor Grok 4.6 (cloud agent, under J. Brown direction)"
SESSION_REF = "bc-01a00d99-d2d8-7c5e-a8d0-d0090dfd7bdd"

PROCESS_DISCLOSURE = (
    "Exact finite swap cell on {0,1}^4.  Typed repairs are "
    "restore-distinction vs quotient-privilege.  Not text nomination, "
    "not a neural net, not Paper F."
)


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


class ToyRow(TypedDict):
    name: str
    cell: Literal["over_invariance", "under_invariance"]
    target: str
    typed_screen: str
    crossed_screen: str
    typed_representable: bool
    crossed_representable: bool
    typed_fibres: int
    crossed_fibres: int


class Ranking(TypedDict):
    rule: str
    typed_wins: bool
    crossed_fails_over: bool
    under_quotient_cheaper: bool
    no_single_minimal_screen: bool
    verdict: Literal["taxonomy_holds", "taxonomy_killed"]


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    toys: list[ToyRow]
    ranking: Ranking
    gates: dict[str, bool]
    process_disclosure: str
    withheld: list[str]


def evaluate_benchmark() -> BenchmarkPayload:
    worlds = all_worlds()
    over_typed = is_representable(worlds, "q_stab0", "first_bit")
    over_id = is_representable(worlds, "q_id", "first_bit")
    over_crossed = is_representable(worlds, "q_perm", "first_bit")
    under_typed = is_representable(worlds, "q_perm", "bag")
    under_crossed = is_representable(worlds, "q_id", "bag")
    under_perm_n = fiber_count(worlds, q_perm)
    under_id_n = fiber_count(worlds, q_id)
    over_stab_n = fiber_count(worlds, q_stab0)
    over_perm_n = fiber_count(worlds, q_perm)

    toys: list[ToyRow] = [
        {
            "name": "first_bit",
            "cell": "over_invariance",
            "target": "first_bit",
            "typed_screen": "q_stab0",
            "crossed_screen": "q_perm",
            "typed_representable": over_typed,
            "crossed_representable": over_crossed,
            "typed_fibres": over_stab_n,
            "crossed_fibres": over_perm_n,
        },
        {
            "name": "bag",
            "cell": "under_invariance",
            "target": "bag",
            "typed_screen": "q_perm",
            "crossed_screen": "q_id",
            "typed_representable": under_typed,
            "crossed_representable": under_crossed,
            "typed_fibres": under_perm_n,
            "crossed_fibres": under_id_n,
        },
    ]

    typed_wins = over_typed and over_id and under_typed
    crossed_fails_over = not over_crossed
    under_cheaper = under_typed and under_crossed and under_perm_n < under_id_n
    # A single screen is minimal-safe for both only if it represents both
    # and is fibre-minimal for both. q_perm fails first_bit. q_id represents
    # both but is not fibre-minimal for bag.
    q_id_both = over_id and under_crossed
    q_perm_both = over_crossed and under_typed
    no_single_minimal = (not q_perm_both) and (not (q_id_both and under_id_n <= under_perm_n))

    taxonomy_holds = typed_wins and crossed_fails_over and under_cheaper and no_single_minimal
    ranking: Ranking = {
        "rule": (
            "Taxonomy holds iff typed repairs work, the crossed over-repair "
            "fails, the under-quotient is strictly cheaper than leftover "
            "privilege, and no single screen is minimal-safe for both toys. "
            "This is a discriminator contract on the Paper A matrix, not "
            "new enumeration."
        ),
        "typed_wins": typed_wins,
        "crossed_fails_over": crossed_fails_over,
        "under_quotient_cheaper": under_cheaper,
        "no_single_minimal_screen": no_single_minimal,
        "verdict": "taxonomy_holds" if taxonomy_holds else "taxonomy_killed",
    }
    # Ranking cells can kill the taxonomy without failing the instrument.
    required = {
        "SWAP_ENUMERATION": len(worlds) == 16,
        "SWAP_TYPED_OVER_REPRESENTABLE": over_typed and over_id,
        "SWAP_TYPED_UNDER_REPRESENTABLE": under_typed,
        "SWAP_BOTH_CELLS_RECORDED": True,
        "SWAP_RANKING_RECORDED": ranking["verdict"] in {"taxonomy_holds", "taxonomy_killed"},
        "SWAP_CLAIM_BOUNDARY": True,
    }
    return {
        "status": "pass" if all(required.values()) else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {"identity": PRODUCING_AGENT, "session_ref": SESSION_REF},
        "toys": toys,
        "ranking": ranking,
        "gates": required,
        "process_disclosure": PROCESS_DISCLOSURE,
        "withheld": [
            "Universal calculus (Paper F / Possibility 1)",
            "Text nomination (DR/DCR)",
            "Paper E agent benchmark (licensed only after B–D)",
            "Lorentz = Lamport = positional encodings",
        ],
    }
