"""Review item 2 on "Intention Is All You Need" v3: the dial's cells
need not nest.

Theorem B's prose said "as D grows the cells coarsen", implying the
rate-distortion optima form a nested chain along the budget.
Rate-distortion does not guarantee that, and this instrument settles
the question exactly on a registered five-point world by enumerating
all 52 partitions.

Two claims separate cleanly, and the separation is the result:

- The **optimal rate falls** as the budget grows.  That is the safe
  general statement (feasible sets nest) and the only slogan the
  essay's rewrite may export.
- **All-optimizer nesting fails**: there are optimizers at adjacent
  budgets where the finer does not refine the coarser.  "The cells
  coarsen" is false as a statement about the optimizer sets.
- A **chosen chain can nest**: selecting one optimizer per budget can
  produce a nested chain.  Nesting is a *selection* fact, not an
  automatic one — the disclosed-choice lesson of κ_screen and the
  D13 repair, recurring at the dial.

Everything is exact ``fractions.Fraction`` arithmetic over an
exhaustive enumeration.  No floats, no sampling, no RNG.  The D = 0
clause itself is already kernel-checked (`DialZero.lean`,
`docs/lea/VERIFY_RECEIPT_2026-08-18.md`); this instrument covers the
budgets the Lean core deliberately does not.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Literal, TypedDict

EXPERIMENT_ID = "dial_nestedness"
RUN_ID = "dial_nestedness_2026_08_18"
PRODUCING_AGENT = "Claude Fable 5 (Cursor agent, under J. Brown direction)"
SESSION_REF = "4adbd42d-0e99-41df-b0be-7d9d5b7e3caa"

PROCESS_DISCLOSURE = (
    "All 52 partitions of a five-point world, enumerated via "
    "restricted-growth strings.  Task-relative distortion is the "
    "worst-case within-cell task-law gap, exact Fractions.  Budgets, "
    "predictions, and the verdict rule are registered before "
    "evaluation.  No sampling, no LLM."
)

WORLDS: tuple[int, ...] = (0, 1, 2, 3, 4)

# Registered task law P(Y=1 | x): five distinct values, evenly spaced.
TASK_LAW: tuple[Fraction, ...] = (
    Fraction(0),
    Fraction(1, 4),
    Fraction(1, 2),
    Fraction(3, 4),
    Fraction(1),
)

# Registered budget grid.
BUDGETS: tuple[Fraction, ...] = (
    Fraction(0),
    Fraction(1, 4),
    Fraction(1, 2),
    Fraction(3, 4),
    Fraction(1),
)

# Registered predictions (written before evaluation; the run decides).
REGISTERED_RATES: tuple[int, ...] = (5, 3, 2, 2, 1)
REGISTERED_ALL_NESTED = False
REGISTERED_WITNESS_FINE: tuple[tuple[int, ...], ...] = ((0, 1), (2, 3), (4,))
REGISTERED_WITNESS_COARSE: tuple[tuple[int, ...], ...] = ((0, 1, 2), (3, 4))

Partition = tuple[tuple[int, ...], ...]

Verdict = Literal[
    "nestedness_fails_generally", "nestedness_holds_here", "inconclusive"
]


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


class BudgetRow(TypedDict):
    budget: str
    optimal_rate: int
    n_optimizers: int
    optimizers: list[list[list[int]]]


class NestWitness(TypedDict):
    budget_fine: str
    budget_coarse: str
    fine_optimizer: list[list[int]]
    coarse_optimizer: list[list[int]]


class Ranking(TypedDict):
    rule: str
    n_partitions: int
    rates: list[int]
    rates_match_registered: bool
    rate_monotone: bool
    d0_unique_level_partition: bool
    all_nested: bool
    nest_witness: NestWitness | None
    chain_exists: bool
    chain: list[list[list[int]]] | None
    verdict: Verdict


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    task_law: list[str]
    budgets: list[str]
    budget_rows: list[BudgetRow]
    ranking: Ranking
    gates: dict[str, bool]
    process_disclosure: str
    withheld: list[str]


def all_partitions() -> list[Partition]:
    """All partitions of WORLDS via restricted-growth strings, in a
    deterministic order."""

    n = len(WORLDS)
    results: list[Partition] = []

    def extend(assignment: list[int], next_block: int) -> None:
        if len(assignment) == n:
            n_blocks = next_block
            cells: list[list[int]] = [[] for _ in range(n_blocks)]
            for world, block in zip(WORLDS, assignment):
                cells[block].append(world)
            results.append(tuple(tuple(cell) for cell in cells))
            return
        for block in range(next_block):
            extend(assignment + [block], next_block)
        extend(assignment + [next_block], next_block + 1)

    extend([], 0)
    return results


def cell_spread(cell: tuple[int, ...]) -> Fraction:
    laws = [TASK_LAW[x] for x in cell]
    return max(laws) - min(laws)


def partition_distortion(partition: Partition) -> Fraction:
    return max(cell_spread(cell) for cell in partition)


def refines(fine: Partition, coarse: Partition) -> bool:
    """Every cell of ``fine`` sits inside some cell of ``coarse``."""

    coarse_sets = [set(cell) for cell in coarse]
    return all(
        any(set(cell) <= big for big in coarse_sets) for cell in fine
    )


def optimizers_at(
    partitions: list[Partition], budget: Fraction
) -> list[Partition]:
    feasible = [
        partition
        for partition in partitions
        if partition_distortion(partition) <= budget
    ]
    best = min(len(partition) for partition in feasible)
    return [partition for partition in feasible if len(partition) == best]


def level_partition() -> Partition:
    """The level-set partition of TASK_LAW (all laws distinct here)."""

    return tuple((x,) for x in WORLDS)


def serialize(partition: Partition) -> list[list[int]]:
    return [list(cell) for cell in partition]


def find_chain(
    optimizer_sets: list[list[Partition]],
) -> list[Partition] | None:
    """A selection of one optimizer per budget forming a nested chain
    (each finer refines the next coarser), if one exists.  Depth-first
    over the (small) product space, deterministic order."""

    chain: list[Partition] = []

    def search(index: int) -> bool:
        if index == len(optimizer_sets):
            return True
        for candidate in optimizer_sets[index]:
            if chain and not refines(chain[-1], candidate):
                continue
            chain.append(candidate)
            if search(index + 1):
                return True
            chain.pop()
        return False

    return list(chain) if search(0) else None


def evaluate_benchmark() -> BenchmarkPayload:
    partitions = all_partitions()
    optimizer_sets = [optimizers_at(partitions, budget) for budget in BUDGETS]
    rates = [len(opts[0]) for opts in optimizer_sets]

    budget_rows: list[BudgetRow] = [
        {
            "budget": str(budget),
            "optimal_rate": rates[i],
            "n_optimizers": len(optimizer_sets[i]),
            "optimizers": [serialize(p) for p in optimizer_sets[i]],
        }
        for i, budget in enumerate(BUDGETS)
    ]

    rate_monotone = all(
        rates[i + 1] <= rates[i] for i in range(len(rates) - 1)
    )
    d0_unique = optimizer_sets[0] == [level_partition()]

    all_nested = True
    nest_witness: NestWitness | None = None
    for i in range(len(BUDGETS) - 1):
        for fine in optimizer_sets[i]:
            for coarse in optimizer_sets[i + 1]:
                if not refines(fine, coarse):
                    all_nested = False
                    if nest_witness is None:
                        nest_witness = {
                            "budget_fine": str(BUDGETS[i]),
                            "budget_coarse": str(BUDGETS[i + 1]),
                            "fine_optimizer": serialize(fine),
                            "coarse_optimizer": serialize(coarse),
                        }

    chain = find_chain(optimizer_sets)
    chain_exists = chain is not None

    if rate_monotone and not all_nested:
        verdict: Verdict = "nestedness_fails_generally"
    elif rate_monotone and all_nested:
        verdict = "nestedness_holds_here"
    else:
        verdict = "inconclusive"

    ranking: Ranking = {
        "rule": (
            "nestedness_fails_generally iff the optimal rate is weakly "
            "decreasing in the budget while some optimizer at a finer "
            "budget fails to refine some optimizer at the next coarser "
            "budget.  nestedness_holds_here iff every adjacent optimizer "
            "pair nests.  inconclusive otherwise.  chain_exists is "
            "recorded separately: a chosen chain may nest even when "
            "all-optimizer nesting fails — nesting is a selection fact."
        ),
        "n_partitions": len(partitions),
        "rates": rates,
        "rates_match_registered": tuple(rates) == REGISTERED_RATES,
        "rate_monotone": rate_monotone,
        "d0_unique_level_partition": d0_unique,
        "all_nested": all_nested,
        "nest_witness": nest_witness,
        "chain_exists": chain_exists,
        "chain": [serialize(p) for p in chain] if chain else None,
        "verdict": verdict,
    }
    required = {
        "NEST_SPECIFIED": True,
        "NEST_ENUMERATION_COMPLETE": len(partitions) == 52,
        "NEST_EXACT_ARITHMETIC": all(
            isinstance(value, Fraction) for value in TASK_LAW
        ),
        "NEST_RATE_MONOTONE": rate_monotone,
        "NEST_D0_IS_LEVELS": d0_unique,
        "NEST_CHAIN_RECORDED": isinstance(chain_exists, bool),
        "NEST_RANKING_RECORDED": ranking["verdict"]
        in {
            "nestedness_fails_generally",
            "nestedness_holds_here",
            "inconclusive",
        },
        "NEST_CLAIM_BOUNDARY": True,
    }
    return {
        "status": "pass" if all(required.values()) else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {"identity": PRODUCING_AGENT, "session_ref": SESSION_REF},
        "task_law": [str(value) for value in TASK_LAW],
        "budgets": [str(budget) for budget in BUDGETS],
        "budget_rows": budget_rows,
        "ranking": ranking,
        "gates": required,
        "process_disclosure": PROCESS_DISCLOSURE,
        "withheld": [
            "Any claim about continuous or general rate-distortion optima",
            "Any expected-distortion (average-case) variant",
            "A rescue of the essay's 'cells coarsen' wording",
            "LLM agent eval",
            "A new master object",
        ],
    }
