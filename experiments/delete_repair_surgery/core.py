"""Paper E: name-blind one-shot assumption surgery.

Papers A–D banked a three-cell taxonomy, a swap cell, a connection
that is not integer Kirchhoff, and a failed Lorentz/Lamport/PE
transfer.  Paper E asks whether that taxonomy is an *agent rule*:
a cheap, name-blind signature that picks one repair without
trying the menu and without reading English.

It is not text nomination.  DR/DCR stay closed.  No LLM.  No
Paper F.

Input to the policy is only ``Signature``.  Gold is empirical:
which menu action actually repairs.  Construction rows are the
authoring toys (disclosed).  Held-out rows include unused
symmetry and preferred-index leftover privilege.

Kill the "taxonomy is a one-shot agent rule" claim if any
held-out gold disagrees with the pre-registered signature rule.
That verdict still passes CI.

Not a better LLM.  Not a universal calculus.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal, TypedDict

from experiments.delete_repair_connection.core import (
    AFFINE_A,
    KIRCHHOFF_FLAT,
    kirchhoff_prediction,
    path_map,
)
from experiments.delete_the_absolute.core import (
    Feature,
    World,
    all_perms,
    all_worlds,
    apply_perm,
    fiber_count,
    identity_perm,
    q_id,
    q_perm,
    q_rot,
    q_stab0,
    y_bag,
    y_constant_on_fibers,
    y_first_bit,
    y_identity,
)

EXPERIMENT_ID = "delete_repair_surgery"
RUN_ID = "delete_repair_surgery_2026_08_17"
PRODUCING_AGENT = "Cursor Grok 4.6 (cloud agent, under J. Brown direction)"
SESSION_REF = "bc-01a00d99-d2d8-7c5e-a8d0-d0090dfd7bdd"

# Held-out Aff(1, Z/3) 4-cycle: Kirchhoff predicts identity, holonomy is (1, 1).
# Distinct from Paper C's AFFINE_A / AFFINE_B.
AFFINE_C: tuple[tuple[int, int], ...] = ((1, 0), (1, 0), (2, 1), (2, 2))

PROCESS_DISCLOSURE = (
    "Name-blind one-shot signature rule on a finite menu.  "
    "Gold is empirical representability / Kirchhoff mismatch.  "
    "Not text nomination, not an LLM, not Paper F."
)

Action = Literal["restore", "quotient", "transport", "noop", "broken"]
Split = Literal["construction", "held_out"]


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


class Signature(TypedDict):
    mixes: bool
    n_fibres: int
    n_worlds: int
    y_has_nontrivial_symmetry: bool
    connection_mismatch: bool


class CaseRow(TypedDict):
    case_id: str
    split: Split
    task_id: str
    screen_id: str
    signature: Signature
    gold: Action
    policy: Action
    hit: bool


class Ranking(TypedDict):
    rule: str
    construction_hits: int
    construction_n: int
    held_out_hits: int
    held_out_n: int
    held_out_exact: bool
    best_constant_held_out: str
    best_constant_held_out_hits: int
    pair_eq_id_is_the_grain_miss: bool
    verdict: Literal["surgery_holds", "surgery_killed"]


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    menu: list[str]
    cases: list[CaseRow]
    ranking: Ranking
    gates: dict[str, bool]
    process_disclosure: str
    withheld: list[str]


def q_stab_last(x: World) -> World:
    """Keep the last bit; sort the prefix.  Dual of ``q_stab0``."""

    return tuple(sorted(x[:-1])) + (x[-1],)


def y_last_bit(x: World) -> int:
    return int(x[-1])


def y_parity(x: World) -> int:
    return int(sum(x) % 2)


def y_pair_eq(x: World) -> int:
    return int(x[0] == x[1])


SCREEN_FNS: dict[str, Callable[[World], Feature]] = {
    "q_id": q_id,
    "q_rot": q_rot,
    "q_perm": q_perm,
    "q_stab0": q_stab0,
    "q_stab_last": q_stab_last,
}

TASK_FNS: dict[str, Callable[[World], Feature]] = {
    "bag": y_bag,
    "first_bit": y_first_bit,
    "identity": y_identity,
    "last_bit": y_last_bit,
    "parity": y_parity,
    "pair_eq": y_pair_eq,
}

MENU: tuple[str, ...] = ("q_id", "q_rot", "q_perm", "q_stab0", "q_stab_last")


class CaseSpec(TypedDict):
    case_id: str
    split: Split
    task_id: str
    screen_id: str
    edges: tuple[tuple[int, int], ...]


# Construction = authoring toys the signature rule was written against.
# Held-out = new tasks / new cycle.  Policy never sees these labels.
CASES: tuple[CaseSpec, ...] = (
    {
        "case_id": "first_bit_q_perm",
        "split": "construction",
        "task_id": "first_bit",
        "screen_id": "q_perm",
        "edges": KIRCHHOFF_FLAT,
    },
    {
        "case_id": "bag_q_id",
        "split": "construction",
        "task_id": "bag",
        "screen_id": "q_id",
        "edges": KIRCHHOFF_FLAT,
    },
    {
        "case_id": "bag_q_perm",
        "split": "construction",
        "task_id": "bag",
        "screen_id": "q_perm",
        "edges": KIRCHHOFF_FLAT,
    },
    {
        "case_id": "bag_q_perm_affine_a",
        "split": "construction",
        "task_id": "bag",
        "screen_id": "q_perm",
        "edges": AFFINE_A,
    },
    {
        "case_id": "last_bit_q_perm",
        "split": "held_out",
        "task_id": "last_bit",
        "screen_id": "q_perm",
        "edges": KIRCHHOFF_FLAT,
    },
    {
        "case_id": "last_bit_q_id",
        "split": "held_out",
        "task_id": "last_bit",
        "screen_id": "q_id",
        "edges": KIRCHHOFF_FLAT,
    },
    {
        "case_id": "parity_q_id",
        "split": "held_out",
        "task_id": "parity",
        "screen_id": "q_id",
        "edges": KIRCHHOFF_FLAT,
    },
    {
        "case_id": "identity_q_id",
        "split": "held_out",
        "task_id": "identity",
        "screen_id": "q_id",
        "edges": KIRCHHOFF_FLAT,
    },
    {
        "case_id": "pair_eq_q_perm",
        "split": "held_out",
        "task_id": "pair_eq",
        "screen_id": "q_perm",
        "edges": KIRCHHOFF_FLAT,
    },
    {
        "case_id": "pair_eq_q_id",
        "split": "held_out",
        "task_id": "pair_eq",
        "screen_id": "q_id",
        "edges": KIRCHHOFF_FLAT,
    },
    {
        "case_id": "bag_q_perm_affine_c",
        "split": "held_out",
        "task_id": "bag",
        "screen_id": "q_perm",
        "edges": AFFINE_C,
    },
)


def connection_mismatch(edges: tuple[tuple[int, int], ...]) -> bool:
    return path_map(edges) != kirchhoff_prediction(edges)


def has_nontrivial_symmetry(
    y_fn: Callable[[World], Feature], worlds: tuple[World, ...]
) -> bool:
    identity = identity_perm()
    return any(
        perm != identity
        and all(y_fn(apply_perm(perm, world)) == y_fn(world) for world in worlds)
        for perm in all_perms()
    )


def signature_of(spec: CaseSpec, worlds: tuple[World, ...]) -> Signature:
    q_fn = SCREEN_FNS[spec["screen_id"]]
    y_fn = TASK_FNS[spec["task_id"]]
    return {
        "mixes": not y_constant_on_fibers(worlds, q_fn, y_fn),
        "n_fibres": fiber_count(worlds, q_fn),
        "n_worlds": len(worlds),
        "y_has_nontrivial_symmetry": has_nontrivial_symmetry(y_fn, worlds),
        "connection_mismatch": connection_mismatch(spec["edges"]),
    }


def decide(signature: Signature) -> Action:
    """Pre-registered one-shot rule.  No names.  No menu search."""

    if signature["connection_mismatch"]:
        return "transport"
    if signature["mixes"]:
        return "restore"
    if (
        signature["y_has_nontrivial_symmetry"]
        and signature["n_fibres"] == signature["n_worlds"]
    ):
        return "quotient"
    return "noop"


def gold_of(spec: CaseSpec, worlds: tuple[World, ...]) -> Action:
    """Empirical gold: which menu action repairs, not which cell we named."""

    if connection_mismatch(spec["edges"]):
        return "transport"
    q_fn = SCREEN_FNS[spec["screen_id"]]
    y_fn = TASK_FNS[spec["task_id"]]
    current = fiber_count(worlds, q_fn)
    represents = y_constant_on_fibers(worlds, q_fn, y_fn)
    if not represents:
        if any(
            fiber_count(worlds, SCREEN_FNS[name]) > current
            and y_constant_on_fibers(worlds, SCREEN_FNS[name], y_fn)
            for name in MENU
        ):
            return "restore"
        return "broken"
    if any(
        fiber_count(worlds, SCREEN_FNS[name]) < current
        and y_constant_on_fibers(worlds, SCREEN_FNS[name], y_fn)
        for name in MENU
    ):
        return "quotient"
    return "noop"


def _hits(rows: list[CaseRow], split: Split) -> tuple[int, int]:
    chosen = [row for row in rows if row["split"] == split]
    return sum(1 for row in chosen if row["hit"]), len(chosen)


def _constant_score(rows: list[CaseRow], action: Action) -> int:
    return sum(1 for row in rows if row["gold"] == action)


def evaluate_benchmark() -> BenchmarkPayload:
    worlds = all_worlds()
    rows: list[CaseRow] = []
    for spec in CASES:
        signature = signature_of(spec, worlds)
        gold = gold_of(spec, worlds)
        policy = decide(signature)
        rows.append(
            {
                "case_id": spec["case_id"],
                "split": spec["split"],
                "task_id": spec["task_id"],
                "screen_id": spec["screen_id"],
                "signature": signature,
                "gold": gold,
                "policy": policy,
                "hit": policy == gold and gold != "broken",
            }
        )

    construction_hits, construction_n = _hits(rows, "construction")
    held_out_hits, held_out_n = _hits(rows, "held_out")
    held_out = [row for row in rows if row["split"] == "held_out"]
    constant_actions: tuple[Action, ...] = ("restore", "quotient", "transport", "noop")
    constant_scores = {action: _constant_score(held_out, action) for action in constant_actions}
    best_constant = max(constant_actions, key=lambda action: constant_scores[action])
    pair_eq_id = next(row for row in rows if row["case_id"] == "pair_eq_q_id")
    held_out_exact = held_out_n > 0 and held_out_hits == held_out_n
    ranking: Ranking = {
        "rule": (
            "surgery_holds iff the name-blind signature rule matches "
            "empirical gold on every held-out row.  Construction rows "
            "are disclosed authoring toys and do not save a miss."
        ),
        "construction_hits": construction_hits,
        "construction_n": construction_n,
        "held_out_hits": held_out_hits,
        "held_out_n": held_out_n,
        "held_out_exact": held_out_exact,
        "best_constant_held_out": best_constant,
        "best_constant_held_out_hits": constant_scores[best_constant],
        "pair_eq_id_is_the_grain_miss": (not pair_eq_id["hit"])
        and pair_eq_id["gold"] == "noop"
        and pair_eq_id["policy"] == "quotient",
        "verdict": "surgery_holds" if held_out_exact else "surgery_killed",
    }
    gold_defined = all(row["gold"] != "broken" for row in rows)
    required = {
        "SUR_ENUMERATION": construction_n >= 4 and held_out_n >= 4,
        "SUR_MENU": len(MENU) >= 3,
        "SUR_GOLD_DEFINED": gold_defined,
        "SUR_NAME_BLIND": all(
            set(row["signature"])
            == {
                "mixes",
                "n_fibres",
                "n_worlds",
                "y_has_nontrivial_symmetry",
                "connection_mismatch",
            }
            for row in rows
        ),
        "SUR_HELD_OUT_CONNECTION": next(
            row["signature"]["connection_mismatch"]
            for row in rows
            if row["case_id"] == "bag_q_perm_affine_c"
        ),
        "SUR_RANKING_RECORDED": ranking["verdict"] in {"surgery_holds", "surgery_killed"},
        "SUR_CLAIM_BOUNDARY": True,
    }
    return {
        "status": "pass" if all(required.values()) else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {"identity": PRODUCING_AGENT, "session_ref": SESSION_REF},
        "menu": list(MENU),
        "cases": rows,
        "ranking": ranking,
        "gates": required,
        "process_disclosure": PROCESS_DISCLOSURE,
        "withheld": [
            "Text nomination / DR / DCR",
            "LLM agent eval",
            "Universal calculus (Paper F)",
            "A better language model",
        ],
    }
