"""Door 3 follow-up: a registered instrument for ESTIMATED concern.

Door 3 (`experiments/delete_repair_concern/`) opened the third job —
care which matter — with concern as a registered weight vector: given
the weights, κ_concern picks the screen worth holding, exactly.  Its
paper closed with the licensed next step: learned concern stays out
until a registered instrument exists for it.  This package is that
instrument, at the smallest honest size.

Concern here is ESTIMATED by registered frequency counting.  Given a
fixed literal sequence of task draws, the plug-in weights after n
draws are the empirical frequencies (exact Fractions), and the
plug-in choice at n is κ_concern of those weights on door 3's menu
and cost rule, unchanged.  Nothing is fit: the sequences, the
estimator, and the convergence steps were all registered before the
run, so the run can only confirm or refute them.

Registered sequences (24 draws each, literal task-id tuples):

``SEQ_BAG``   ("bag",) * 24 — oracle concern δ_bag, oracle choice
              q_perm, registered convergence step 1.
``SEQ_MIX``   ("bag", "first_bit") * 12 — oracle uniform{bag,
              first_bit}, oracle choice q_stab0, registered step 2.
``SEQ_PAIR``  ("bag", "pair_eq") * 12 — oracle uniform{bag, pair_eq},
              oracle choice q_id, registered step 6: the odd-prefix
              pair_eq frequency k/(2k+1) crosses door 3's exact
              11/27 boundary between n = 5 (2/5, still q_perm) and
              n = 7 (3/7, q_id); even prefixes sit at 1/2 from n = 2.

Misspecification control: on SEQ_PAIR's true concern the SEQ_MIX
oracle choice q_stab0 has expected cost 20 against q_id's 16 — an
exact Fraction gap of 4 for holding the wrong sequence's screen.

Registered outcomes (all pass CI):

``estimation_works``
    Every sequence's plug-in choice equals its oracle choice for all
    prefixes n >= the registered step, and each step is minimal.

``estimation_fails``
    Some final-prefix (n = 24) plug-in choice differs from oracle.

``inconclusive``
    Anything else (converges and stays, but not at the registered
    steps).

Not SGD.  Not valence.  Not learned representations.  Not an LLM.
Not a new master object.  Not Paper G.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Literal, TypedDict

from experiments.delete_repair_concern.core import (
    Concern,
    concern_of,
    kappa_concern,
    representing_set_for_bag,
    serving_cost,
)
from experiments.delete_the_absolute.core import World, all_worlds

EXPERIMENT_ID = "delete_repair_concern_estimation"
RUN_ID = "delete_repair_concern_estimation_2026_08_18"
PRODUCING_AGENT = "Claude Fable 5 (Cursor agent, under J. Brown direction)"
SESSION_REF = "4adbd42d-0e99-41df-b0be-7d9d5b7e3caa"

PROCESS_DISCLOSURE = (
    "Concern is estimated by registered frequency counting on three "
    "literal 24-draw task sequences.  Plug-in weights after n draws "
    "are exact empirical Fractions; the plug-in choice is door 3's "
    "kappa_concern on the unchanged menu and cost rule.  The "
    "convergence steps 1/2/6 and the misspecification gap 4 were "
    "registered before the run.  No SGD, no valence, no learned "
    "representations, no RNG."
)

N_DRAWS = 24

Verdict = Literal["estimation_works", "estimation_fails", "inconclusive"]

SEQ_BAG: tuple[str, ...] = ("bag",) * 24
SEQ_MIX: tuple[str, ...] = ("bag", "first_bit") * 12
SEQ_PAIR: tuple[str, ...] = ("bag", "pair_eq") * 12

MISSPEC_FOREIGN_CHOICE = "q_stab0"
MISSPEC_ORACLE_CHOICE = "q_id"


class SequenceSpec(TypedDict):
    sequence_id: str
    draws: tuple[str, ...]
    oracle_concern: Concern
    oracle_choice: str
    registered_step: int


REGISTERED_SEQUENCES: tuple[SequenceSpec, ...] = (
    {
        "sequence_id": "seq_bag",
        "draws": SEQ_BAG,
        "oracle_concern": concern_of({"bag": Fraction(1)}),
        "oracle_choice": "q_perm",
        "registered_step": 1,
    },
    {
        "sequence_id": "seq_mix",
        "draws": SEQ_MIX,
        "oracle_concern": concern_of(
            {"bag": Fraction(1, 2), "first_bit": Fraction(1, 2)}
        ),
        "oracle_choice": "q_stab0",
        "registered_step": 2,
    },
    {
        "sequence_id": "seq_pair",
        "draws": SEQ_PAIR,
        "oracle_concern": concern_of(
            {"bag": Fraction(1, 2), "pair_eq": Fraction(1, 2)}
        ),
        "oracle_choice": "q_id",
        "registered_step": 6,
    },
)


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


class TraceRow(TypedDict):
    sequence_id: str
    n: int
    weights: dict[str, str]
    plugin_choice: str
    oracle_choice: str
    matches_oracle: bool


class SequenceRow(TypedDict):
    sequence_id: str
    draws: list[str]
    n_draws: int
    oracle_weights: dict[str, str]
    oracle_choice: str
    banked_door3_choice: str
    oracle_anchor_ok: bool
    registered_step: int
    observed_step: int
    step_matches_registered: bool
    final_matches_oracle: bool


class MisspecRow(TypedDict):
    true_concern: dict[str, str]
    foreign_choice: str
    oracle_choice: str
    cost_foreign: str
    cost_oracle: str
    gap: str


class Ranking(TypedDict):
    rule: str
    n_sequences: int
    n_draws_each: int
    registered_steps: dict[str, int]
    observed_steps: dict[str, int]
    all_steps_match_registered: bool
    all_finals_match_oracle: bool
    misspec_gap: str
    verdict: Verdict


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    representing_set: list[str]
    sequences: list[SequenceRow]
    trace: list[TraceRow]
    misspec: MisspecRow
    ranking: Ranking
    gates: dict[str, bool]
    process_disclosure: str
    withheld: list[str]


def plugin_weights(draws: tuple[str, ...], n: int) -> Concern:
    """Empirical frequencies over the first ``n`` draws, as exact Fractions."""
    counts: dict[str, int] = {}
    for task_id in draws[:n]:
        counts[task_id] = counts.get(task_id, 0) + 1
    return concern_of(
        {task_id: Fraction(count, n) for task_id, count in counts.items()}
    )


def expected_cost_from_serving(
    screen_id: str, concern: Concern, worlds: tuple[World, ...]
) -> Fraction:
    total = Fraction(0)
    for task_id, weight in concern:
        _represents, cost = serving_cost(screen_id, task_id, worlds)
        total += weight * cost
    return total


def convergence_step(matches: list[bool]) -> int:
    """Minimal 1-based n such that every prefix from n on matches oracle.

    Returns ``len(matches) + 1`` when the final prefix mismatches, i.e.
    the sequence never converged within the registered horizon.
    """
    step = len(matches) + 1
    for index in range(len(matches) - 1, -1, -1):
        if not matches[index]:
            break
        step = index + 1
    return step


def is_exact_rational_string(value: str) -> bool:
    return "/" in value or value.lstrip("-").isdigit()


def evaluate_benchmark() -> BenchmarkPayload:
    worlds = all_worlds()
    candidates = representing_set_for_bag(worlds)

    sequence_rows: list[SequenceRow] = []
    trace: list[TraceRow] = []
    registered_steps: dict[str, int] = {}
    observed_steps: dict[str, int] = {}
    anchors_ok = True
    for spec in REGISTERED_SEQUENCES:
        oracle_choice, _oracle_costs = kappa_concern(
            spec["oracle_concern"], candidates, worlds
        )
        anchor_ok = oracle_choice == spec["oracle_choice"]
        anchors_ok = anchors_ok and anchor_ok

        matches: list[bool] = []
        for n in range(1, len(spec["draws"]) + 1):
            weights = plugin_weights(spec["draws"], n)
            plugin_choice, _costs = kappa_concern(weights, candidates, worlds)
            match = plugin_choice == spec["oracle_choice"]
            matches.append(match)
            trace.append(
                {
                    "sequence_id": spec["sequence_id"],
                    "n": n,
                    "weights": {task: str(weight) for task, weight in weights},
                    "plugin_choice": plugin_choice,
                    "oracle_choice": spec["oracle_choice"],
                    "matches_oracle": match,
                }
            )
        observed = convergence_step(matches)
        registered_steps[spec["sequence_id"]] = spec["registered_step"]
        observed_steps[spec["sequence_id"]] = observed
        sequence_rows.append(
            {
                "sequence_id": spec["sequence_id"],
                "draws": list(spec["draws"]),
                "n_draws": len(spec["draws"]),
                "oracle_weights": {
                    task: str(weight) for task, weight in spec["oracle_concern"]
                },
                "oracle_choice": oracle_choice,
                "banked_door3_choice": spec["oracle_choice"],
                "oracle_anchor_ok": anchor_ok,
                "registered_step": spec["registered_step"],
                "observed_step": observed,
                "step_matches_registered": observed == spec["registered_step"],
                "final_matches_oracle": matches[-1],
            }
        )

    # Misspecification control: hold SEQ_MIX's oracle screen while the
    # true concern is SEQ_PAIR's.  Registered exact gap: 20 - 16 = 4.
    pair_concern = REGISTERED_SEQUENCES[2]["oracle_concern"]
    cost_foreign = expected_cost_from_serving(
        MISSPEC_FOREIGN_CHOICE, pair_concern, worlds
    )
    cost_oracle = expected_cost_from_serving(
        MISSPEC_ORACLE_CHOICE, pair_concern, worlds
    )
    misspec: MisspecRow = {
        "true_concern": {task: str(weight) for task, weight in pair_concern},
        "foreign_choice": MISSPEC_FOREIGN_CHOICE,
        "oracle_choice": MISSPEC_ORACLE_CHOICE,
        "cost_foreign": str(cost_foreign),
        "cost_oracle": str(cost_oracle),
        "gap": str(cost_foreign - cost_oracle),
    }

    all_steps = all(row["step_matches_registered"] for row in sequence_rows)
    all_finals = all(row["final_matches_oracle"] for row in sequence_rows)
    if all_steps and all_finals:
        verdict: Verdict = "estimation_works"
    elif not all_finals:
        verdict = "estimation_fails"
    else:
        verdict = "inconclusive"

    ranking: Ranking = {
        "rule": (
            "estimation_works iff every sequence's plug-in choice equals "
            "its oracle choice for all prefixes n >= the registered step "
            "and each step is minimal (seq_bag 1, seq_mix 2, seq_pair 6).  "
            "estimation_fails iff any final-prefix choice differs from "
            "oracle.  inconclusive otherwise."
        ),
        "n_sequences": len(sequence_rows),
        "n_draws_each": N_DRAWS,
        "registered_steps": registered_steps,
        "observed_steps": observed_steps,
        "all_steps_match_registered": all_steps,
        "all_finals_match_oracle": all_finals,
        "misspec_gap": misspec["gap"],
        "verdict": verdict,
    }
    required = {
        "EST_SPECIFIED": True,
        "EST_SEQUENCES_REGISTERED": len(REGISTERED_SEQUENCES) == 3
        and all(len(spec["draws"]) == N_DRAWS for spec in REGISTERED_SEQUENCES),
        "EST_EXACT_ARITHMETIC": all(
            is_exact_rational_string(weight)
            for row in trace
            for weight in row["weights"].values()
        )
        and is_exact_rational_string(misspec["gap"]),
        "EST_ORACLE_ANCHORS": anchors_ok,
        "EST_CONVERGENCE_RECORDED": len(trace) == 3 * N_DRAWS
        and len(observed_steps) == 3,
        "EST_MISSPEC_RECORDED": is_exact_rational_string(misspec["cost_foreign"])
        and is_exact_rational_string(misspec["cost_oracle"]),
        "EST_RANKING_RECORDED": ranking["verdict"]
        in {"estimation_works", "estimation_fails", "inconclusive"},
        "EST_CLAIM_BOUNDARY": True,
    }
    return {
        "status": "pass" if all(required.values()) else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {"identity": PRODUCING_AGENT, "session_ref": SESSION_REF},
        "representing_set": candidates,
        "sequences": sequence_rows,
        "trace": trace,
        "misspec": misspec,
        "ranking": ranking,
        "gates": required,
        "process_disclosure": PROCESS_DISCLOSURE,
        "withheld": [
            "Valence, agency, consciousness, phenomenology",
            (
                "Learning beyond registered frequency counting "
                "(no SGD, no learned representations)"
            ),
            "Any menu or cost rule other than door 3's registered ones",
            "A new master object above SIC",
            "LLM agent eval",
            "A better language model",
        ],
    }
