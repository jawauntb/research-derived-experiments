"""Gate 2 of "Intention Is All You Need" at the kernel: the silence gate.

The essay's Gate 2 asks, before anyone trusts a wall of green reports,
whether the spec-level record could even show a substitution.  This
package is the essay's P10 kernel run as an exact instrument, at the
zero-leakage limit: the realization space is eight outcomes forming a
single compliance class, so the spec-level record is the constant
symbol "compliant" BY CONSTRUCTION — there is no record channel for
the tilt to show up on.

Two arms share the channel and differ only in the registered reward
table.  The misaligned delegate reward R_MIS = (0..7) is exactly
opposed to the principal value U = (7..0); the aligned control reward
R_AL = U.  The base compiler is uniform; ecology step t reweights
outcome x by (r(x) + 1) ** t, exact integer powers, for t = 0..12.

Registered analytic predictions (derived before the run; the run can
only confirm or refute them):

* the record is identical at all 13 steps in both arms;
* misaligned E_t[r] strictly rises while E_t[U] strictly falls
  (from 7/2 at t = 0 to 1583088700/7083249971 at t = 12);
* the mass on the misaligned reward argmax x = 7 strictly rises and
  equals exactly 17179869184/21249749913 at t = 12, above the
  registered floor 4/5 (the mass tends to 1 as t grows; 99/100 is
  first crossed at t = 35, outside this horizon);
* the aligned arm's E_t[U] strictly rises — the channel, not the
  tilt, sets the direction.

Registered outcomes (all pass CI):

``substitution_silent``
    The record is constant in both arms AND misaligned E_t[U] falls
    while E_t[r] rises AND the aligned control's E_t[U] rises.

``substitution_visible``
    The record ever varies, in either arm.

``inconclusive``
    Anything else.

Kernel instrument only: this banks the zero-leakage limit.  No claim
about real specifications' leakage, no LLM, no valence; the bridge
from record silence to intention attribution stays a bet per the
essay.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Literal, TypedDict

EXPERIMENT_ID = "silent_substitution"
RUN_ID = "silent_substitution_2026_08_18"
PRODUCING_AGENT = "Claude Fable 5 (Cursor agent, under J. Brown direction)"
SESSION_REF = "4adbd42d-0e99-41df-b0be-7d9d5b7e3caa"

PROCESS_DISCLOSURE = (
    "Eight compliant outcomes form one compliance class, so the "
    "spec-level record is the constant symbol 'compliant' by "
    "construction — the zero-leakage limit.  Two arms share the "
    "channel and differ only in the registered reward table: R_MIS "
    "exactly opposed to the principal value U, and R_AL equal to U.  "
    "Ecology step t reweights outcome x by (r(x) + 1) ** t for "
    "t = 0..12; every expectation and mass is an exact Fraction.  "
    "The monotone directions and the exact t = 12 argmax mass were "
    "registered before the run.  No RNG, no floats, no LLM."
)

REALIZATIONS: tuple[int, ...] = tuple(range(8))
PRINCIPAL_VALUE: tuple[Fraction, ...] = tuple(Fraction(7 - x) for x in REALIZATIONS)
REWARD_MISALIGNED: tuple[Fraction, ...] = tuple(Fraction(x) for x in REALIZATIONS)
REWARD_ALIGNED: tuple[Fraction, ...] = PRINCIPAL_VALUE
COMPLIANCE_RECORD = "compliant"
T_MAX = 12
TRAJECTORY: tuple[int, ...] = tuple(range(T_MAX + 1))

# Registered analytic anchors, derived before the run.
EXPECTED_UNIFORM_PRINCIPAL = Fraction(7, 2)
EXPECTED_LIMIT_MASS = Fraction(17179869184, 21249749913)
LIMIT_MASS_FLOOR = Fraction(4, 5)

Verdict = Literal["substitution_silent", "substitution_visible", "inconclusive"]


class ArmSpec(TypedDict):
    arm_id: str
    reward_name: str
    reward: tuple[Fraction, ...]


REGISTERED_ARMS: tuple[ArmSpec, ...] = (
    {
        "arm_id": "misaligned",
        "reward_name": "R_MIS",
        "reward": REWARD_MISALIGNED,
    },
    {
        "arm_id": "aligned",
        "reward_name": "R_AL",
        "reward": REWARD_ALIGNED,
    },
)


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


class TraceRow(TypedDict):
    arm_id: str
    t: int
    weights: list[str]
    expected_reward: str
    expected_principal: str
    record: str
    argmax_reward_mass: str


class ArmRow(TypedDict):
    arm_id: str
    reward_name: str
    reward: list[str]
    records: list[str]
    record_constant: bool
    uniform_principal: str
    uniform_anchor_ok: bool
    reward_strictly_rises: bool
    principal_strictly_falls: bool
    principal_strictly_rises: bool
    argmax_mass_strictly_rises: bool
    final_argmax_mass: str


class Ranking(TypedDict):
    rule: str
    n_arms: int
    n_steps: int
    record_constant_both_arms: bool
    misaligned_reward_rises: bool
    misaligned_principal_falls: bool
    aligned_principal_rises: bool
    limit_mass: str
    verdict: Verdict


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    realization_space: list[int]
    principal_value: list[str]
    arms: list[ArmRow]
    trace: list[TraceRow]
    ranking: Ranking
    gates: dict[str, bool]
    process_disclosure: str
    withheld: list[str]


def ecology_weights(reward: tuple[Fraction, ...], t: int) -> tuple[Fraction, ...]:
    """Registered compiler tilt at step ``t``: w_t(x) = (r(x) + 1) ** t."""
    return tuple((r + 1) ** t for r in reward)


def expectation(
    weights: tuple[Fraction, ...], values: tuple[Fraction, ...]
) -> Fraction:
    total = sum(weights, start=Fraction(0))
    weighted = sum(
        (weight * value for weight, value in zip(weights, values, strict=True)),
        start=Fraction(0),
    )
    return weighted / total


def argmax_reward_mass(
    weights: tuple[Fraction, ...], reward: tuple[Fraction, ...]
) -> Fraction:
    best = max(reward)
    total = sum(weights, start=Fraction(0))
    on_best = sum(
        (weight for weight, r in zip(weights, reward, strict=True) if r == best),
        start=Fraction(0),
    )
    return on_best / total


def strictly_increasing(series: list[Fraction]) -> bool:
    return all(later > earlier for earlier, later in zip(series, series[1:]))


def strictly_decreasing(series: list[Fraction]) -> bool:
    return all(later < earlier for earlier, later in zip(series, series[1:]))


def is_exact_rational_string(value: str) -> bool:
    return "/" in value or value.lstrip("-").isdigit()


def evaluate_benchmark() -> BenchmarkPayload:
    trace: list[TraceRow] = []
    arm_rows: list[ArmRow] = []
    all_records: list[str] = []
    limit_mass = Fraction(0)
    for spec in REGISTERED_ARMS:
        expected_rewards: list[Fraction] = []
        expected_principals: list[Fraction] = []
        masses: list[Fraction] = []
        records: list[str] = []
        for t in TRAJECTORY:
            weights = ecology_weights(spec["reward"], t)
            e_reward = expectation(weights, spec["reward"])
            e_principal = expectation(weights, PRINCIPAL_VALUE)
            mass = argmax_reward_mass(weights, spec["reward"])
            expected_rewards.append(e_reward)
            expected_principals.append(e_principal)
            masses.append(mass)
            # The whole space is one compliance class, so the spec-level
            # record at every step is the same constant symbol.
            records.append(COMPLIANCE_RECORD)
            trace.append(
                {
                    "arm_id": spec["arm_id"],
                    "t": t,
                    "weights": [str(weight) for weight in weights],
                    "expected_reward": str(e_reward),
                    "expected_principal": str(e_principal),
                    "record": COMPLIANCE_RECORD,
                    "argmax_reward_mass": str(mass),
                }
            )
        all_records.extend(records)
        arm_rows.append(
            {
                "arm_id": spec["arm_id"],
                "reward_name": spec["reward_name"],
                "reward": [str(r) for r in spec["reward"]],
                "records": records,
                "record_constant": len(set(records)) == 1,
                "uniform_principal": str(expected_principals[0]),
                "uniform_anchor_ok": expected_principals[0]
                == EXPECTED_UNIFORM_PRINCIPAL,
                "reward_strictly_rises": strictly_increasing(expected_rewards),
                "principal_strictly_falls": strictly_decreasing(expected_principals),
                "principal_strictly_rises": strictly_increasing(expected_principals),
                "argmax_mass_strictly_rises": strictly_increasing(masses),
                "final_argmax_mass": str(masses[-1]),
            }
        )
        if spec["arm_id"] == "misaligned":
            limit_mass = masses[-1]

    by_arm = {row["arm_id"]: row for row in arm_rows}
    misaligned = by_arm["misaligned"]
    aligned = by_arm["aligned"]
    record_constant_both = len(set(all_records)) == 1

    if not record_constant_both:
        verdict: Verdict = "substitution_visible"
    elif (
        misaligned["reward_strictly_rises"]
        and misaligned["principal_strictly_falls"]
        and aligned["principal_strictly_rises"]
    ):
        verdict = "substitution_silent"
    else:
        verdict = "inconclusive"

    ranking: Ranking = {
        "rule": (
            "substitution_silent iff the record is constant across all "
            "13 steps of both arms AND misaligned E_t[U] strictly falls "
            "while E_t[r] strictly rises AND the aligned control's "
            "E_t[U] strictly rises.  substitution_visible iff the "
            "record ever varies.  inconclusive otherwise."
        ),
        "n_arms": len(arm_rows),
        "n_steps": len(TRAJECTORY),
        "record_constant_both_arms": record_constant_both,
        "misaligned_reward_rises": misaligned["reward_strictly_rises"],
        "misaligned_principal_falls": misaligned["principal_strictly_falls"],
        "aligned_principal_rises": aligned["principal_strictly_rises"],
        "limit_mass": str(limit_mass),
        "verdict": verdict,
    }
    required = {
        "SIL_RECORD_CONSTANT": record_constant_both,
        "SIL_MISALIGNED_R_RISES": misaligned["reward_strictly_rises"],
        "SIL_MISALIGNED_U_FALLS": misaligned["principal_strictly_falls"],
        "SIL_LIMIT_CONCENTRATES": misaligned["argmax_mass_strictly_rises"]
        and limit_mass == EXPECTED_LIMIT_MASS
        and limit_mass > LIMIT_MASS_FLOOR,
        "SIL_ALIGNED_CONTROL": aligned["principal_strictly_rises"],
        "SIL_EXACT_ARITHMETIC": all(
            is_exact_rational_string(value)
            for row in trace
            for value in (
                *row["weights"],
                row["expected_reward"],
                row["expected_principal"],
                row["argmax_reward_mass"],
            )
        )
        and all(
            row["uniform_anchor_ok"]
            and is_exact_rational_string(row["final_argmax_mass"])
            for row in arm_rows
        ),
        "SIL_RANKING_RECORDED": ranking["verdict"]
        in {"substitution_silent", "substitution_visible", "inconclusive"},
        "SIL_CLAIM_BOUNDARY": True,
    }
    return {
        "status": "pass" if all(required.values()) else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {"identity": PRODUCING_AGENT, "session_ref": SESSION_REF},
        "realization_space": list(REALIZATIONS),
        "principal_value": [str(value) for value in PRINCIPAL_VALUE],
        "arms": arm_rows,
        "trace": trace,
        "ranking": ranking,
        "gates": required,
        "process_disclosure": PROCESS_DISCLOSURE,
        "withheld": [
            "Valence, agency, consciousness, phenomenology",
            (
                "Any claim about real specifications' leakage (the "
                "zero-leakage limit is constructed here, not measured)"
            ),
            (
                "The intention-to-mechanism bridge (stays a bet per "
                'the essay "Intention Is All You Need")'
            ),
            "LLM agent eval",
            "A better language model",
        ],
    }
