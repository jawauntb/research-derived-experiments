"""Gate 1 of "Intention Is All You Need" at the kernel: the dividend gate.

The essay's Gate 1 prices what a compiler's choice is worth before
any capability claim is credited: intelligence pays only on slack.
This package is the essay's P11/D12 kernel arithmetic as an exact
instrument.  On the sixteen worlds {0,1}^4 (encoded 0..15) a task is
a compliant region plus a principal value function U mapping worlds
to Fractions.  The choice dividend of a task (D12) is the exact gap
between the best compliant value and the uniform compiler's expected
value over the region.  The P11 / Theorem-B framing: the dividend is
zero exactly when compliance leaves no slack for choice to exploit —
singleton regions, and wide regions on which the value is flat — and
positive exactly when the region is wide AND the value varies on it.

Registered task table (three families x specifics):

* SINGLETON — region {5} with U(x) = x; region {12} likewise.
  Dividend must be 0.
* WIDE-VARYING — region = all even worlds (8 worlds) with U(x) = x;
  region = worlds with popcount >= 2 (11 worlds) with
  U(x) = popcount(x) * 4 - (x % 3), a registered
  arbitrary-but-fixed variation.  Dividend positive, computed
  exactly: 7 and 73/11.
* WIDE-FLAT — region = all odd worlds with constant U(x) = 5, the
  essay's "everything compliant equally good" case.  Dividend must
  be 0.

Capability sweep: selector best-of-k for k = 1..|region|: scan the
region in registered ascending order and take the max U among the
first k elements; gain(k) = that max minus the uniform-compiler
expectation E_uniform[U].  k = 1 under this scan is deterministic
first-element, so gain(1) can be negative; it is recorded; the
registered claim is about the curve's endpoint and monotonicity, not
gain(1) >= 0.

Registered outcomes (all pass CI):

``dividend_confirmed``
    All three gate families hold: singleton dividends 0 with flat
    gain curves, flat-task dividend 0 with gains <= 0 closing at 0,
    and both wide-varying dividends positive with weakly increasing
    gain curves ending exactly at the dividend.

``dividend_refuted``
    Any zero-case shows a positive dividend, or a wide curve fails
    to reach its dividend.

``inconclusive``
    Anything else.

Kernel arithmetic of P11/D12 only.  The learner half of Gate 1 —
real capability sweeps on real models — is explicitly NOT run here
and stays open.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Literal, TypedDict

EXPERIMENT_ID = "choice_dividend"
RUN_ID = "choice_dividend_2026_08_18"
PRODUCING_AGENT = "Claude Fable 5 (Cursor agent, under J. Brown direction)"
SESSION_REF = "4adbd42d-0e99-41df-b0be-7d9d5b7e3caa"

PROCESS_DISCLOSURE = (
    "Five registered tasks on the sixteen worlds {0,1}^4: two "
    "singletons ({5} and {12}, U(x) = x), two wide-varying regions "
    "(the eight even worlds with U(x) = x; the eleven popcount >= 2 "
    "worlds with U(x) = popcount(x) * 4 - (x % 3)), and one "
    "wide-flat region (the eight odd worlds, U constant 5).  The "
    "choice dividend is max U over the region minus the uniform "
    "expectation, exact Fractions throughout.  The best-of-k sweep "
    "scans each region in registered ascending order.  The expected "
    "dividends (0, 0, 7, 73/11, 0) were registered before the run.  "
    "No RNG, no floats, no learner, no LLM."
)

WORLDS: tuple[int, ...] = tuple(range(16))

Verdict = Literal["dividend_confirmed", "dividend_refuted", "inconclusive"]

Family = Literal["singleton", "wide_varying", "wide_flat"]


def popcount(x: int) -> int:
    return x.bit_count()


class TaskSpec(TypedDict):
    task_id: str
    family: Family
    region: tuple[int, ...]
    values: tuple[Fraction, ...]
    value_rule: str
    expected_dividend: Fraction


def _identity_values(region: tuple[int, ...]) -> tuple[Fraction, ...]:
    return tuple(Fraction(x) for x in region)


EVEN_REGION: tuple[int, ...] = tuple(x for x in WORLDS if x % 2 == 0)
ODD_REGION: tuple[int, ...] = tuple(x for x in WORLDS if x % 2 == 1)
POPCOUNT_GE2_REGION: tuple[int, ...] = tuple(x for x in WORLDS if popcount(x) >= 2)

REGISTERED_TASKS: tuple[TaskSpec, ...] = (
    {
        "task_id": "singleton_5",
        "family": "singleton",
        "region": (5,),
        "values": _identity_values((5,)),
        "value_rule": "U(x) = x",
        "expected_dividend": Fraction(0),
    },
    {
        "task_id": "singleton_12",
        "family": "singleton",
        "region": (12,),
        "values": _identity_values((12,)),
        "value_rule": "U(x) = x",
        "expected_dividend": Fraction(0),
    },
    {
        "task_id": "even_worlds",
        "family": "wide_varying",
        "region": EVEN_REGION,
        "values": _identity_values(EVEN_REGION),
        "value_rule": "U(x) = x",
        "expected_dividend": Fraction(7),
    },
    {
        "task_id": "popcount_ge2",
        "family": "wide_varying",
        "region": POPCOUNT_GE2_REGION,
        "values": tuple(
            Fraction(popcount(x) * 4 - (x % 3)) for x in POPCOUNT_GE2_REGION
        ),
        "value_rule": "U(x) = popcount(x) * 4 - (x % 3)",
        "expected_dividend": Fraction(73, 11),
    },
    {
        "task_id": "odd_flat",
        "family": "wide_flat",
        "region": ODD_REGION,
        "values": tuple(Fraction(5) for _ in ODD_REGION),
        "value_rule": "U(x) = 5",
        "expected_dividend": Fraction(0),
    },
)


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


class TaskRow(TypedDict):
    task_id: str
    family: Family
    region: list[int]
    region_size: int
    values: list[str]
    value_rule: str
    uniform_expectation: str
    best_value: str
    dividend: str
    expected_dividend: str
    dividend_matches_registered: bool
    gains: list[str]
    gain_first: str
    gain_final: str
    gains_weakly_increasing: bool
    final_gain_equals_dividend: bool


class Ranking(TypedDict):
    rule: str
    n_tasks: int
    dividends: dict[str, str]
    singleton_zero: bool
    flat_zero: bool
    wide_positive: bool
    verdict: Verdict


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    worlds: list[int]
    tasks: list[TaskRow]
    ranking: Ranking
    gates: dict[str, bool]
    process_disclosure: str
    withheld: list[str]


def uniform_expectation(values: tuple[Fraction, ...]) -> Fraction:
    return sum(values, start=Fraction(0)) / len(values)


def choice_dividend(values: tuple[Fraction, ...]) -> Fraction:
    """D12: best compliant value minus the uniform-compiler expectation."""
    return max(values) - uniform_expectation(values)


def best_of_k_gains(values: tuple[Fraction, ...]) -> list[Fraction]:
    """Gain curve of the registered ascending-scan best-of-k selector."""
    expectation = uniform_expectation(values)
    gains: list[Fraction] = []
    best = values[0]
    for value in values:
        best = value if value > best else best
        gains.append(best - expectation)
    return gains


def weakly_increasing(series: list[Fraction]) -> bool:
    return all(later >= earlier for earlier, later in zip(series, series[1:]))


def is_exact_rational_string(value: str) -> bool:
    return "/" in value or value.lstrip("-").isdigit()


def evaluate_benchmark() -> BenchmarkPayload:
    task_rows: list[TaskRow] = []
    for spec in REGISTERED_TASKS:
        values = spec["values"]
        expectation = uniform_expectation(values)
        best = max(values)
        dividend = choice_dividend(values)
        gains = best_of_k_gains(values)
        task_rows.append(
            {
                "task_id": spec["task_id"],
                "family": spec["family"],
                "region": list(spec["region"]),
                "region_size": len(spec["region"]),
                "values": [str(value) for value in values],
                "value_rule": spec["value_rule"],
                "uniform_expectation": str(expectation),
                "best_value": str(best),
                "dividend": str(dividend),
                "expected_dividend": str(spec["expected_dividend"]),
                "dividend_matches_registered": dividend == spec["expected_dividend"],
                "gains": [str(gain) for gain in gains],
                "gain_first": str(gains[0]),
                "gain_final": str(gains[-1]),
                "gains_weakly_increasing": weakly_increasing(gains),
                "final_gain_equals_dividend": gains[-1] == dividend,
            }
        )

    by_family: dict[str, list[TaskRow]] = {}
    for row in task_rows:
        by_family.setdefault(row["family"], []).append(row)
    singletons = by_family["singleton"]
    wides = by_family["wide_varying"]
    flats = by_family["wide_flat"]

    singleton_zero = all(
        Fraction(row["dividend"]) == 0
        and row["dividend_matches_registered"]
        and all(Fraction(gain) == 0 for gain in row["gains"])
        for row in singletons
    )
    flat_zero = all(
        Fraction(row["dividend"]) == 0
        and row["dividend_matches_registered"]
        and all(Fraction(gain) <= 0 for gain in row["gains"])
        and Fraction(row["gain_final"]) == 0
        for row in flats
    )
    wide_positive = all(
        Fraction(row["dividend"]) > 0
        and row["dividend_matches_registered"]
        and row["gains_weakly_increasing"]
        and row["final_gain_equals_dividend"]
        for row in wides
    )

    zero_case_shows_positive = any(
        Fraction(row["dividend"]) > 0 for row in singletons + flats
    )
    wide_curve_misses_dividend = any(
        not row["final_gain_equals_dividend"] for row in wides
    )
    if singleton_zero and flat_zero and wide_positive:
        verdict: Verdict = "dividend_confirmed"
    elif zero_case_shows_positive or wide_curve_misses_dividend:
        verdict = "dividend_refuted"
    else:
        verdict = "inconclusive"

    ranking: Ranking = {
        "rule": (
            "dividend_confirmed iff all three gate families hold "
            "(singletons: dividend 0 and every gain 0; flat: dividend "
            "0, gains <= 0, final gain 0; wide-varying: dividend > 0 "
            "matching the registered value, gains weakly increasing, "
            "final gain exactly the dividend).  dividend_refuted iff "
            "any zero-case shows a positive dividend or a wide curve "
            "fails to reach its dividend.  inconclusive otherwise."
        ),
        "n_tasks": len(task_rows),
        "dividends": {row["task_id"]: row["dividend"] for row in task_rows},
        "singleton_zero": singleton_zero,
        "flat_zero": flat_zero,
        "wide_positive": wide_positive,
        "verdict": verdict,
    }
    required = {
        "DIV_SINGLETON_ZERO": singleton_zero and len(singletons) == 2,
        "DIV_FLAT_ZERO": flat_zero and len(flats) == 1,
        "DIV_WIDE_POSITIVE": wide_positive and len(wides) == 2,
        "DIV_EXACT_ARITHMETIC": all(
            is_exact_rational_string(value)
            for row in task_rows
            for value in (
                *row["values"],
                *row["gains"],
                row["uniform_expectation"],
                row["best_value"],
                row["dividend"],
            )
        ),
        "DIV_RANKING_RECORDED": ranking["verdict"]
        in {"dividend_confirmed", "dividend_refuted", "inconclusive"},
        "DIV_CLAIM_BOUNDARY": True,
    }
    return {
        "status": "pass" if all(required.values()) else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {"identity": PRODUCING_AGENT, "session_ref": SESSION_REF},
        "worlds": list(WORLDS),
        "tasks": task_rows,
        "ranking": ranking,
        "gates": required,
        "process_disclosure": PROCESS_DISCLOSURE,
        "withheld": [
            "Valence, agency, consciousness, phenomenology",
            (
                "The learner half of Gate 1 (real capability sweeps "
                "on real models) — explicitly not run here"
            ),
            "Any region or value rule other than the five registered tasks",
            "LLM agent eval",
            "A better language model",
        ],
    }
