"""Exact symbolic-causation benchmark on a tiny enumerable world.

A symbolic structure becomes causally effective only through instantiation (the
structural-realism ontology). But "changes behaviour" is not one thing. This
module makes four quantities exact and shows they dissociate:

* **signal** -- ``delta_kl = KL(P(traj | m) || P(traj | baseline))``: does the
  symbol move the trajectory distribution at all?
* **control / navigability** -- ``goal_gain``: does it raise the probability of
  reaching the target region? plus ``viability_gain`` for avoiding failure.
* **knowledge** -- ``predictive_accuracy``: does ``m`` predict outcomes without
  necessarily changing them?
* **agency** -- control **plus** correct causal self-attribution
  (``calibration_error`` small: the agent's claimed effect matches the true
  do-effect) **plus** ``transfer`` (the effect survives an environment
  perturbation the intervention did not choose).

The pre-registered claim is a dissociation: hand-built conditions each realize a
distinct metric signature, so no single scalar (behavioural influence) suffices
to identify agency; in particular a "false-credit" condition improves the
outcome while its true do-effect is zero, and a "brittle controller" controls in
the base environment but fails to transfer.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass

State = str
# A transition model maps each state to a distribution over next states.
Transition = Mapping[State, Mapping[State, float]]

START: State = "s0"
GOAL: State = "g"
FAIL: State = "f"
HORIZON = 3

# Two non-terminal "mid" states a, b are statistically identical for goal/fail
# but carry distinct labels, so rerouting between them is pure signal.
_MID_STATS: dict[State, float] = {GOAL: 0.4, FAIL: 0.3}


def _mid(self_state: State, to_goal: float, to_fail: float) -> dict[State, float]:
    return {GOAL: to_goal, FAIL: to_fail, self_state: 1.0 - to_goal - to_fail}


def base_environment() -> dict[State, dict[State, float]]:
    """Baseline dynamics: the system idles in ``a``/``b`` and may reach goal or fail.

    Both mid states carry support (0.9/0.1) and are statistically identical for
    goal/fail, so rerouting mass between them is pure signal with finite KL.
    """
    return {
        START: {"a": 0.9, "b": 0.1},
        "a": _mid("a", _MID_STATS[GOAL], _MID_STATS[FAIL]),
        "b": _mid("b", _MID_STATS[GOAL], _MID_STATS[FAIL]),
        GOAL: {GOAL: 1.0},
        FAIL: {FAIL: 1.0},
    }


def perturbed_environment() -> dict[State, dict[State, float]]:
    """A structure-preserving perturbation: same roles, shifted idle dynamics."""
    env = base_environment()
    env["a"] = _mid("a", 0.35, 0.35)
    env["b"] = _mid("b", 0.35, 0.35)
    return env


def enrichment_shift(env: Transition) -> dict[State, dict[State, float]]:
    """An exogenous environmental improvement (nothing to do with the agent)."""
    shifted = {s: dict(d) for s, d in env.items()}
    shifted["a"] = _mid("a", 0.7, 0.1)
    return shifted


def trajectory_distribution(
    env: Transition, *, start: State = START, horizon: int = HORIZON
) -> dict[tuple[State, ...], float]:
    """Exact distribution over length-``horizon`` state paths from ``start``."""
    dist: dict[tuple[State, ...], float] = {(start,): 1.0}
    for _ in range(horizon):
        nxt: dict[tuple[State, ...], float] = {}
        for path, prob in dist.items():
            last = path[-1]
            for succ, p in env[last].items():
                if p <= 0:
                    continue
                nxt[path + (succ,)] = nxt.get(path + (succ,), 0.0) + prob * p
        dist = nxt
    return dist


def terminal_distribution(env: Transition) -> dict[State, float]:
    terminal: dict[State, float] = {}
    for path, prob in trajectory_distribution(env).items():
        terminal[path[-1]] = terminal.get(path[-1], 0.0) + prob
    return terminal


def _absorbing_reach(env: Transition, target: State) -> float:
    """Probability the target absorbing state is occupied at the horizon."""
    return terminal_distribution(env).get(target, 0.0)


def kl_divergence(
    p: Mapping[tuple[State, ...], float], q: Mapping[tuple[State, ...], float]
) -> float:
    total = 0.0
    for path, pp in p.items():
        if pp <= 0:
            continue
        qq = q.get(path, 0.0)
        if qq <= 0:
            return math.inf
        total += pp * math.log2(pp / qq)
    return total


def total_variation(p: Mapping[State, float], q: Mapping[State, float]) -> float:
    keys = set(p) | set(q)
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in keys)


@dataclass(frozen=True)
class Intervention:
    """A symbolic model instantiated as an operation on the environment."""

    name: str
    apply: Callable[[Transition], dict[State, dict[State, float]]]
    claimed_goal_effect: float
    predicted_terminal: Mapping[State, float] | None = None
    # ``enriched`` marks conditions whose *deployment* environment is exogenously
    # improved -- used to model observed-but-uncaused outcome gains.
    enriched: bool = False


def _reroute_to_b(env: Transition) -> dict[State, dict[State, float]]:
    # Swap the idle mass onto ``b``; ``a`` and ``b`` are statistically identical
    # for goal/fail, so terminal outcomes are unchanged (pure signal, finite KL).
    out = {s: dict(d) for s, d in env.items()}
    out[START] = {"a": 0.1, "b": 0.9}
    return out


def _bias_to_goal(env: Transition) -> dict[State, dict[State, float]]:
    out = {s: dict(d) for s, d in env.items()}
    out["a"] = _mid("a", 0.7, 0.1)
    out["b"] = _mid("b", 0.7, 0.1)
    return out


def _identity(env: Transition) -> dict[State, dict[State, float]]:
    return {s: dict(d) for s, d in env.items()}


def _brittle_bias(env: Transition) -> dict[State, dict[State, float]]:
    """Controls only when idle dynamics match the base environment exactly."""
    out = {s: dict(d) for s, d in env.items()}
    if abs(env["a"].get(GOAL, 0.0) - _MID_STATS[GOAL]) < 1e-12:
        out["a"] = _mid("a", 0.7, 0.1)
        out["b"] = _mid("b", 0.7, 0.1)
    # Otherwise the intervention silently reduces to baseline (no transfer).
    return out


def default_interventions() -> tuple[Intervention, ...]:
    base_terminal = terminal_distribution(base_environment())
    return (
        Intervention("baseline", _identity, claimed_goal_effect=0.0),
        Intervention("noise_signal", _reroute_to_b, claimed_goal_effect=0.0),
        # Controls the outcome but does not know its own effect (miscalibrated).
        Intervention("control", _bias_to_goal, claimed_goal_effect=0.18),
        Intervention(
            "knowledge_only",
            _identity,
            claimed_goal_effect=0.0,
            predicted_terminal=base_terminal,
        ),
        Intervention(
            "false_credit", _identity, claimed_goal_effect=0.32, enriched=True
        ),
        # Controls, correctly attributes its effect, and transfers: full agency.
        Intervention("agent", _bias_to_goal, claimed_goal_effect=0.32),
        Intervention("brittle_controller", _brittle_bias, claimed_goal_effect=0.32),
    )


def evaluate_intervention(m: Intervention) -> dict:
    base = base_environment()
    base_traj = trajectory_distribution(base)
    base_goal = _absorbing_reach(base, GOAL)
    base_viability = 1.0 - _absorbing_reach(base, FAIL)

    applied = m.apply(base)
    applied_traj = trajectory_distribution(applied)

    delta_kl = kl_divergence(applied_traj, base_traj)
    true_goal_effect = _absorbing_reach(applied, GOAL) - base_goal
    viability_gain = (1.0 - _absorbing_reach(applied, FAIL)) - base_viability

    # Deployment outcome may include an exogenous enrichment (false credit).
    deployment = enrichment_shift(base) if m.enriched else base
    observed_goal_gain = _absorbing_reach(deployment, GOAL) - base_goal

    calibration_error = abs(m.claimed_goal_effect - true_goal_effect)

    if m.predicted_terminal is None:
        predictive_accuracy = 0.0
    else:
        predictive_accuracy = 1.0 - total_variation(
            m.predicted_terminal, terminal_distribution(base)
        )

    # Transfer: does the intervention's do-effect survive a perturbation it did
    # not choose? Measured as the true goal effect in the perturbed environment.
    perturbed = perturbed_environment()
    perturbed_goal = _absorbing_reach(perturbed, GOAL)
    transfer = _absorbing_reach(m.apply(perturbed), GOAL) - perturbed_goal

    return {
        "intervention": m.name,
        "delta_kl": round(delta_kl, 12),
        "true_goal_effect": round(true_goal_effect, 12),
        "observed_goal_gain": round(observed_goal_gain, 12),
        "viability_gain": round(viability_gain, 12),
        "claimed_goal_effect": round(m.claimed_goal_effect, 12),
        "calibration_error": round(calibration_error, 12),
        "predictive_accuracy": round(predictive_accuracy, 12),
        "transfer": round(transfer, 12),
    }


# Thresholds for the qualitative taxonomy (pre-registered).
_SIGNAL = 1e-9
_EFFECT = 1e-3
_CALIB = 1e-3
_PRED = 0.99


def classify(row: Mapping[str, float]) -> str:
    signal = row["delta_kl"] > _SIGNAL
    controls = row["true_goal_effect"] > _EFFECT
    predicts = row["predictive_accuracy"] >= _PRED
    calibrated = row["calibration_error"] <= _CALIB
    transfers = row["transfer"] > _EFFECT
    miscredits = row["observed_goal_gain"] > _EFFECT and row["true_goal_effect"] <= _EFFECT

    if miscredits and not controls:
        return "false_credit"
    if controls and calibrated and transfers:
        return "agency"
    if controls and not transfers:
        return "brittle_control"
    if controls:
        return "control"
    if predicts and not signal:
        return "knowledge"
    if signal and not controls:
        return "signal_only"
    return "inert"


EXPECTED_CLASS: dict[str, str] = {
    "baseline": "inert",
    "noise_signal": "signal_only",
    "control": "control",
    "knowledge_only": "knowledge",
    "false_credit": "false_credit",
    "agent": "agency",
    "brittle_controller": "brittle_control",
}


def evaluate_benchmark() -> dict:
    rows = [evaluate_intervention(m) for m in default_interventions()]
    classifications = {row["intervention"]: classify(row) for row in rows}

    by_name = {row["intervention"]: row for row in rows}
    signal_without_control = (
        by_name["noise_signal"]["delta_kl"] > _SIGNAL
        and by_name["noise_signal"]["true_goal_effect"] <= _EFFECT
    )
    knowledge_without_signal = (
        by_name["knowledge_only"]["predictive_accuracy"] >= _PRED
        and by_name["knowledge_only"]["delta_kl"] <= _SIGNAL
    )
    false_credit_uncaused = (
        by_name["false_credit"]["observed_goal_gain"] > _EFFECT
        and by_name["false_credit"]["true_goal_effect"] <= _EFFECT
        and by_name["false_credit"]["calibration_error"] > _CALIB
    )
    agency_transfers = by_name["agent"]["transfer"] > _EFFECT
    brittle_does_not_transfer = by_name["brittle_controller"]["transfer"] <= _EFFECT
    taxonomy_recovered = all(
        classifications[name] == expected for name, expected in EXPECTED_CLASS.items()
    )

    gates = {
        "signal_dissociates_from_control": signal_without_control,
        "knowledge_dissociates_from_signal": knowledge_without_signal,
        "false_credit_is_uncaused_and_miscalibrated": false_credit_uncaused,
        "agency_transfers": agency_transfers,
        "brittle_control_does_not_transfer": brittle_does_not_transfer,
        "taxonomy_recovered": taxonomy_recovered,
    }
    status = "pass" if all(gates.values()) else "fail"
    return {
        "status": status,
        "gates": gates,
        "classifications": classifications,
        "rows": rows,
    }
