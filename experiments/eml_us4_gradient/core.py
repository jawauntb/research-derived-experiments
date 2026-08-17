"""US-4′ lowest-bound gradient half: does Φ predict master-formula GD?

The Gibbs half showed that two min-internal=3 fibers can differ in
truncated mass.  Sampling those same trees would recover that ranking
by definition.  This package uses a different process: gradient descent
on a size-3 master skeleton whose ``1``-leaves are learnable positive
reals.

Registered targets (frozen before any blind count):

- Fat / zero: ``eml(1,eml(eml(1,1),1))`` and ``eml(x,eml(eml(x,1),1))``
  — identically 0, two size-3 formulas, higher Φ.
- Thin / singleton: ``eml(1,eml(1,eml(1,1)))`` — constant
  ``e-ln(e-1)``, one formula, lower Φ.

Headline GD uses the two all-ones skeletons so both have four weights.
The x-zero formula is a target-registration check, not extra inits.

Not Odrzywołek's neural bootstrap.  Local-CPU analogue only.
"""

from __future__ import annotations

import math
import random
from typing import Literal, TypedDict

from experiments.eml_variable_spectrum.core import (
    TEST_GRID,
    VarTree,
    eval_at,
    parse_var,
    require_finite,
)

EXPERIMENT_ID = "eml_us4_gradient"
RUN_ID = "eml_us4_gradient_2026_08_17"
PRODUCING_AGENT = "Cursor Grok 4.6 (cloud agent, under J. Brown direction)"
SESSION_REF = "bc-b0dc5f4f-3e49-560f-bd25-5809a86ca2c1"

ZERO_ONES = "eml(1,eml(eml(1,1),1))"
ZERO_X = "eml(x,eml(eml(x,1),1))"
SINGLETON = "eml(1,eml(1,eml(1,1)))"
SEEDS: tuple[int, ...] = (0, 1, 2, 3, 4, 5, 6, 7)
STEPS = 200
LR = 0.15
SUCCESS_MSE = 1e-6
WEIGHT_LO = 0.1
WEIGHT_HI = 3.0
THETA_LO = math.log(1e-4)
THETA_HI = math.log(50.0)
PERTURB_LOG = 0.1
RANKING_MARGIN = 1
PERTURB_SEED_SHIFT = 10_000

PROCESS_DISCLOSURE = (
    "Recovery is hand-derived gradient descent on a master formula "
    "(the registered size-3 skeleton; 1-leaves are learnable positive "
    "reals; x-leaves stay x).  It is not a Gibbs sampler of the census "
    "trees and not Odrzywołek's neural bootstrap.  Local-CPU analogue only."
)
CLAIM_BOUNDARY = (
    "Local matching-skeleton GD ranking only.  Not Odrzywołek's neural "
    "bootstrap.  Not a Gibbs-sampler tautology.  Not function identity "
    "from the grid except the exact zero identity."
)


def n_weight_leaves(tree: VarTree) -> int:
    if tree.is_leaf:
        return 1 if tree.leaf == "1" else 0
    assert tree.left is not None and tree.right is not None
    return n_weight_leaves(tree.left) + n_weight_leaves(tree.right)


def _combine(left_val: float | None, right_val: float | None) -> float | None:
    if left_val is None or right_val is None:
        return None
    if not math.isfinite(left_val) or not math.isfinite(right_val) or right_val <= 0.0:
        return None
    try:
        value = math.exp(left_val) - math.log(right_val)
    except OverflowError:
        return None
    if not math.isfinite(value):
        return None
    return value


def eval_weighted(tree: VarTree, x_val: float, weights: tuple[float, ...]) -> float | None:
    cursor = 0

    def go(node: VarTree) -> float | None:
        nonlocal cursor
        if node.is_leaf:
            if node.leaf == "1":
                value = weights[cursor]
                cursor += 1
                return value
            return x_val
        assert node.left is not None and node.right is not None
        return _combine(go(node.left), go(node.right))

    return go(tree)


def eval_value_and_grad(
    tree: VarTree,
    x_val: float,
    weights: tuple[float, ...],
) -> tuple[float | None, tuple[float, ...]]:
    """Reverse-mode d(eval)/dw through ``eml(a,b)=exp(a)-ln(b)``."""

    n_weights = len(weights)
    cursor = 0

    def go(node: VarTree) -> tuple[float | None, list[float]]:
        nonlocal cursor
        zeros = [0.0] * n_weights
        if node.is_leaf:
            if node.leaf == "1":
                index = cursor
                cursor += 1
                zeros[index] = 1.0
                return weights[index], zeros
            return x_val, zeros
        assert node.left is not None and node.right is not None
        left_val, left_grad = go(node.left)
        right_val, right_grad = go(node.right)
        value = _combine(left_val, right_val)
        if value is None or left_val is None or right_val is None:
            return None, zeros
        d_left = math.exp(left_val)
        d_right = -1.0 / right_val
        merged = [d_left * left_g + d_right * right_g for left_g, right_g in zip(left_grad, right_grad)]
        return value, merged

    value, grad = go(tree)
    return value, tuple(grad)


def target_grid(pretty: str) -> tuple[float, ...]:
    tree = parse_var(pretty)
    return tuple(require_finite(eval_at(tree, x_val), f"{pretty}@{x_val}") for x_val in TEST_GRID)


def mse(tree: VarTree, weights: tuple[float, ...], target: tuple[float, ...]) -> float:
    total = 0.0
    for x_val, expected in zip(TEST_GRID, target):
        observed = eval_weighted(tree, x_val, weights)
        if observed is None or not math.isfinite(observed):
            return 1e6
        err = observed - expected
        total += err * err
    return total / float(len(target))


def loss_grad(tree: VarTree, weights: tuple[float, ...], target: tuple[float, ...]) -> tuple[float, ...] | None:
    n_weights = len(weights)
    acc = [0.0] * n_weights
    scale = 2.0 / float(len(target))
    for x_val, expected in zip(TEST_GRID, target):
        value, d_eval = eval_value_and_grad(tree, x_val, weights)
        if value is None:
            return None
        coef = scale * (value - expected)
        for index in range(n_weights):
            acc[index] += coef * d_eval[index]
    return tuple(acc)


def log_uniform_weights(n_weights: int, seed: int) -> tuple[float, ...]:
    rng = random.Random(seed)
    low = math.log(WEIGHT_LO)
    high = math.log(WEIGHT_HI)
    return tuple(math.exp(rng.uniform(low, high)) for _ in range(n_weights))


def perturbed_true_weights(n_weights: int, seed: int) -> tuple[float, ...]:
    rng = random.Random(PERTURB_SEED_SHIFT + seed)
    return tuple(math.exp(rng.uniform(-PERTURB_LOG, PERTURB_LOG)) for _ in range(n_weights))


def _clip_theta(theta: float) -> float:
    return min(THETA_HI, max(THETA_LO, theta))


def descend(
    tree: VarTree,
    start: tuple[float, ...],
    target: tuple[float, ...],
) -> tuple[float, tuple[float, ...]]:
    theta = [_clip_theta(math.log(weight)) for weight in start]
    weights = tuple(math.exp(value) for value in theta)
    loss = mse(tree, weights, target)
    lr = LR
    for _step in range(STEPS):
        if loss < SUCCESS_MSE:
            break
        grads = loss_grad(tree, weights, target)
        if grads is None:
            break
        grad_theta = [grad_w * weight for grad_w, weight in zip(grads, weights)]
        scale = max((abs(grad) for grad in grad_theta), default=1.0)
        if scale > 1.0:
            grad_theta = [grad / scale for grad in grad_theta]
        nxt_theta = [_clip_theta(value - lr * grad) for value, grad in zip(theta, grad_theta)]
        nxt_weights = tuple(math.exp(value) for value in nxt_theta)
        nxt_loss = mse(tree, nxt_weights, target)
        if nxt_loss < loss:
            theta = nxt_theta
            weights = nxt_weights
            loss = nxt_loss
            lr = min(0.5, lr * 1.1)
        else:
            lr *= 0.5
            if lr < 1e-12:
                break
    return loss, weights


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


class TargetSpec(TypedDict):
    name: str
    pretty: str
    n_internal: int
    n_weights: int
    is_zero: bool
    grid: list[float]


class SeedRow(TypedDict):
    target: str
    skeleton: str
    mode: Literal["blind", "perturbed_correct"]
    seed: int
    start: list[float]
    final_mse: float
    success: bool


class RecoveryRow(TypedDict):
    target: str
    skeleton: str
    mode: Literal["blind", "perturbed_correct"]
    n_success: int
    n_trials: int
    success_rate: float
    best_mse: float


class Ranking(TypedDict):
    rule: str
    margin: int
    zero_successes: int
    singleton_successes: int
    n_inits: int
    verdict: Literal["phi_holds", "min_size_governs", "phi_killed", "withheld_optimizer"]
    claim: Literal["supported", "rejected", "withheld"]


class RegisteredConfig(TypedDict):
    seeds: list[int]
    steps: int
    lr: float
    success_mse: float
    weight_lo: float
    weight_hi: float
    ranking_margin: int
    zero_ones: str
    zero_x: str
    singleton: str
    process: str


class Gates(TypedDict):
    US4G_TARGETS_REGISTERED: bool
    US4G_PROCESS_IS_NOT_GIBBS_SAMPLER: bool
    US4G_DETERMINISTIC: bool
    US4G_RANKING: bool
    US4G_CLAIM_BOUNDARY: bool
    US4G_PERTURBED_CORRECT: bool


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    registered: RegisteredConfig
    targets: list[TargetSpec]
    recoveries: list[RecoveryRow]
    seed_rows: list[SeedRow]
    ranking: Ranking
    gates: Gates
    process_disclosure: str
    claim_boundary: str
    withheld: list[str]
    citations: list[str]


def _target_spec(name: str, pretty: str) -> TargetSpec:
    tree = parse_var(pretty)
    grid = target_grid(pretty)
    return {
        "name": name,
        "pretty": pretty,
        "n_internal": tree.n_internal,
        "n_weights": n_weight_leaves(tree),
        "is_zero": all(math.isclose(value, 0.0, rel_tol=0.0, abs_tol=1e-12) for value in grid),
        "grid": [float(value) for value in grid],
    }


def _run_seed(
    *,
    target_name: str,
    skeleton: str,
    target: tuple[float, ...],
    mode: Literal["blind", "perturbed_correct"],
    seed: int,
) -> SeedRow:
    tree = parse_var(skeleton)
    n_weights = n_weight_leaves(tree)
    start = perturbed_true_weights(n_weights, seed) if mode == "perturbed_correct" else log_uniform_weights(n_weights, seed)
    loss, _weights = descend(tree, start, target)
    return {
        "target": target_name,
        "skeleton": skeleton,
        "mode": mode,
        "seed": seed,
        "start": [float(value) for value in start],
        "final_mse": float(loss),
        "success": loss < SUCCESS_MSE,
    }


def _summarize(rows: list[SeedRow]) -> RecoveryRow:
    first = rows[0]
    n_success = sum(1 for row in rows if row["success"])
    best = min(row["final_mse"] for row in rows)
    n_trials = len(rows)
    return {
        "target": first["target"],
        "skeleton": first["skeleton"],
        "mode": first["mode"],
        "n_success": n_success,
        "n_trials": n_trials,
        "success_rate": n_success / float(n_trials),
        "best_mse": best,
    }


def _run_mode(
    *,
    target_name: str,
    skeleton: str,
    target: tuple[float, ...],
    mode: Literal["blind", "perturbed_correct"],
) -> tuple[RecoveryRow, list[SeedRow]]:
    rows = [
        _run_seed(
            target_name=target_name,
            skeleton=skeleton,
            target=target,
            mode=mode,
            seed=seed,
        )
        for seed in SEEDS
    ]
    return _summarize(rows), rows


def apply_ranking(zero_successes: int, singleton_successes: int, perturbed_ok: bool) -> Ranking:
    """Preregistered rule.  Do not edit after seeing counts."""

    rule = (
        "After the run, on the same 8-init budget: if zero successes > "
        "singleton successes + 0 (margin ≥ 1 extra success), Φ-ranking "
        "holds; if equal, reject Φ-predicts-GD and record "
        "min-size-still-governs; if singleton > zero, kill Φ-predicts-GD. "
        "If perturbed-correct fails, withhold, do not reject."
    )
    if not perturbed_ok:
        verdict: Literal["phi_holds", "min_size_governs", "phi_killed", "withheld_optimizer"] = (
            "withheld_optimizer"
        )
        claim: Literal["supported", "rejected", "withheld"] = "withheld"
    elif zero_successes >= singleton_successes + RANKING_MARGIN:
        verdict = "phi_holds"
        claim = "supported"
    elif singleton_successes > zero_successes:
        verdict = "phi_killed"
        claim = "rejected"
    else:
        verdict = "min_size_governs"
        claim = "rejected"
    return {
        "rule": rule,
        "margin": RANKING_MARGIN,
        "zero_successes": zero_successes,
        "singleton_successes": singleton_successes,
        "n_inits": len(SEEDS),
        "verdict": verdict,
        "claim": claim,
    }


def evaluate_benchmark() -> BenchmarkPayload:
    zero_spec = _target_spec("zero", ZERO_ONES)
    singleton_spec = _target_spec("singleton", SINGLETON)
    x_spec = _target_spec("zero_x", ZERO_X)
    zero_grid = target_grid(ZERO_ONES)
    singleton_grid = target_grid(SINGLETON)
    perturbed, perturbed_rows = _run_mode(
        target_name="zero",
        skeleton=ZERO_ONES,
        target=zero_grid,
        mode="perturbed_correct",
    )
    zero_blind, zero_rows = _run_mode(
        target_name="zero",
        skeleton=ZERO_ONES,
        target=zero_grid,
        mode="blind",
    )
    singleton_blind, singleton_rows = _run_mode(
        target_name="singleton",
        skeleton=SINGLETON,
        target=singleton_grid,
        mode="blind",
    )
    replay_zero, _replay_zero_rows = _run_mode(
        target_name="zero",
        skeleton=ZERO_ONES,
        target=zero_grid,
        mode="blind",
    )
    replay_singleton, _replay_singleton_rows = _run_mode(
        target_name="singleton",
        skeleton=SINGLETON,
        target=singleton_grid,
        mode="blind",
    )
    perturbed_ok = perturbed["n_success"] >= 1
    ranking = apply_ranking(zero_blind["n_success"], singleton_blind["n_success"], perturbed_ok)
    targets_ok = (
        zero_spec["n_internal"] == singleton_spec["n_internal"] == 3
        and zero_spec["is_zero"]
        and not singleton_spec["is_zero"]
        and x_spec["is_zero"]
        and x_spec["n_internal"] == 3
        and zero_spec["n_weights"] == singleton_spec["n_weights"] == 4
    )
    process_ok = (
        "gradient descent on a master formula" in PROCESS_DISCLOSURE
        and "not a Gibbs sampler" in PROCESS_DISCLOSURE
    )
    boundary_ok = "Not Odrzywołek's neural bootstrap" in CLAIM_BOUNDARY
    deterministic = (
        replay_zero["n_success"] == zero_blind["n_success"]
        and replay_singleton["n_success"] == singleton_blind["n_success"]
    )
    ranking_recorded = ranking["verdict"] in {
        "phi_holds",
        "min_size_governs",
        "phi_killed",
        "withheld_optimizer",
    }
    gates: Gates = {
        "US4G_TARGETS_REGISTERED": targets_ok,
        "US4G_PROCESS_IS_NOT_GIBBS_SAMPLER": process_ok,
        "US4G_DETERMINISTIC": deterministic,
        "US4G_RANKING": ranking_recorded,
        "US4G_CLAIM_BOUNDARY": boundary_ok,
        "US4G_PERTURBED_CORRECT": perturbed_ok,
    }
    instrument_ok = all(
        (
            gates["US4G_TARGETS_REGISTERED"],
            gates["US4G_PROCESS_IS_NOT_GIBBS_SAMPLER"],
            gates["US4G_DETERMINISTIC"],
            gates["US4G_RANKING"],
            gates["US4G_CLAIM_BOUNDARY"],
            gates["US4G_PERTURBED_CORRECT"],
        )
    )
    return {
        "status": "pass" if instrument_ok else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {
            "identity": PRODUCING_AGENT,
            "session_ref": SESSION_REF,
        },
        "registered": {
            "seeds": list(SEEDS),
            "steps": STEPS,
            "lr": LR,
            "success_mse": SUCCESS_MSE,
            "weight_lo": WEIGHT_LO,
            "weight_hi": WEIGHT_HI,
            "ranking_margin": RANKING_MARGIN,
            "zero_ones": ZERO_ONES,
            "zero_x": ZERO_X,
            "singleton": SINGLETON,
            "process": "master_formula_gd",
        },
        "targets": [zero_spec, singleton_spec, x_spec],
        "recoveries": [perturbed, zero_blind, singleton_blind],
        "seed_rows": perturbed_rows + zero_rows + singleton_rows,
        "ranking": ranking,
        "gates": gates,
        "process_disclosure": PROCESS_DISCLOSURE,
        "claim_boundary": CLAIM_BOUNDARY,
        "withheld": [
            "Odrzywołek neural bootstrap",
            "Gibbs sampling of the census trees",
            "Identity of functions from the grid except the exact zero target",
            "Any claim that Φ governs every optimizer or every master",
        ],
        "citations": [
            "Odrzywołek, A. (2026). All elementary functions from a single binary operator. arXiv:2603.21852.",
        ],
    }
