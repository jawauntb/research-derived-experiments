#!/usr/bin/env python3
"""Boundary Priors (Track 3): minimal embodied self/world demarcation.

A minimal embodied agent acts through ``K`` channels, each secretly SELF
(action-controllable) or WORLD (exogenous). Under a limited actuation budget the
agent must infer the self/world boundary to spend its budget on controllable
channels. At a regime shift the boundary moves (tool attach/detach, limb loss).

Thesis under test (There Is No Self-Evidence; Levin TAME; metric-stack
synthesis section 18): the boundary is a prior, not an evidentially fixed fact.
A plastic/removable prior should recover after the shift; a fixed prior (even
the correct one) should not; and generic plasticity with shuffled attribution
should also fail. See preregistration.md for the pre-committed gates.

Pure standard library, deterministic per seed.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pvariance
from typing import Sequence

SELF = 1
WORLD = 0

PRE_SHIFT_SEEDS = (20260610, 1729, 4242)


@dataclass
class Config:
    channels: int = 8
    num_self: int = 3
    budget: int = 3
    p_world: float = 0.5
    drift: float = 0.15  # SELF channels perturb unless maintained -> budget stays scarce
    steps: int = 600
    shift_step: int = 300
    window: int = 120
    settle: int = 40
    lr: float = 0.3
    epsilon: float = 0.25
    belief_decay: float = 0.03  # unmonitored beliefs relax toward 0.5 (removable prior)
    theta: float = 0.7  # self/world decision + classification threshold
    init_belief: float = 0.5


@dataclass
class ConditionResult:
    condition: str
    seed: int
    mean_reward_pre: float
    mean_reward_post: float
    boundary_accuracy_pre: float
    boundary_accuracy_post: float
    criticality_pre: float
    criticality_post: float
    belief_tracking_lag: int
    probe_rate_pre: float
    probe_rate_post: float


def draw_types(rng: random.Random, channels: int, num_self: int) -> list[int]:
    idx = list(range(channels))
    rng.shuffle(idx)
    selfset = set(idx[:num_self])
    return [SELF if k in selfset else WORLD for k in range(channels)]


def reshuffle_types(rng: random.Random, channels: int, num_self: int, old: list[int]) -> list[int]:
    """Re-draw the assignment as a genuine boundary move (a tool swap).

    Prefer a new SELF set disjoint from the old one (full tool detach + new
    attach). Falls back to any differing assignment if disjointness is
    impossible (2 * num_self > channels).
    """
    old_self = {k for k in range(channels) if old[k] == SELF}
    pool = [k for k in range(channels) if k not in old_self]
    if len(pool) >= num_self:
        rng.shuffle(pool)
        new_self = set(pool[:num_self])
        return [SELF if k in new_self else WORLD for k in range(channels)]
    for _ in range(64):
        new = draw_types(rng, channels, num_self)
        if new != old:
            return new
    return new


def belief_for_condition(condition: str, rng: random.Random, cfg: Config, types: list[int]) -> list[float]:
    if condition == "fixed_self_correct":
        return [1.0 if t == SELF else 0.0 for t in types]
    if condition == "fixed_all_self":
        return [1.0] * cfg.channels
    if condition == "fixed_all_world":
        return [0.0] * cfg.channels
    if condition == "random_prior":
        return [rng.random() for _ in range(cfg.channels)]
    # plastic and shuffled_evidence start uninformed
    return [cfg.init_belief] * cfg.channels


def is_plastic(condition: str) -> bool:
    return condition in ("plastic", "shuffled_evidence")


def choose_actuated(
    *,
    rng: random.Random,
    cfg: Config,
    belief: Sequence[float],
    values: Sequence[int],
    targets: Sequence[int],
    probe: bool,
) -> list[int]:
    """Pick up to ``budget`` channels to actuate this step.

    Exploit: channels believed SELF and currently off-target. Probe: channels
    whose self/world status is most uncertain (belief closest to 0.5).
    """
    channels = list(range(cfg.channels))
    if probe:
        # Probe random channels so confidently-wrong beliefs (after a shift) get
        # re-tested, not only the already-uncertain ones.
        rng.shuffle(channels)
        return channels[: cfg.budget]
    # Exploit: prefer believed-self (above threshold), off-target channels.
    rng.shuffle(channels)
    scored = sorted(
        channels,
        key=lambda k: (belief[k] * (1.0 if values[k] != targets[k] else 0.1)),
        reverse=True,
    )
    chosen = [k for k in scored if belief[k] > cfg.theta]
    if len(chosen) >= cfg.budget:
        return chosen[: cfg.budget]
    # Fill remaining budget with the most uncertain channels (cheap exploration).
    remaining = [k for k in scored if k not in set(chosen)]
    remaining.sort(key=lambda k: abs(belief[k] - 0.5))
    return (chosen + remaining)[: cfg.budget]


def run_condition(condition: str, seed: int, cfg: Config) -> ConditionResult:
    rng = random.Random(seed)
    env_rng = random.Random(seed * 7919 + 1)

    types = draw_types(rng, cfg.channels, cfg.num_self)
    targets = [rng.randint(0, 1) for _ in range(cfg.channels)]
    values = [env_rng.randint(0, 1) for _ in range(cfg.channels)]
    belief = belief_for_condition(condition, rng, cfg, types)

    # Shuffled-evidence anti-cheat: a fixed permutation that misroutes attribution.
    perm = list(range(cfg.channels))
    rng.shuffle(perm)

    rewards: list[float] = []
    boundary_acc: list[float] = []
    crit: list[float] = []
    probe_flags: list[int] = []
    shifted_at = None
    lag = -1

    for step in range(cfg.steps):
        if step == cfg.shift_step:
            types = reshuffle_types(rng, cfg.channels, cfg.num_self, types)
            shifted_at = step

        probe = is_plastic(condition) and (rng.random() < cfg.epsilon)
        probe_flags.append(1 if probe else 0)
        actuated = choose_actuated(
            rng=rng, cfg=cfg, belief=belief, values=values, targets=targets, probe=probe
        )
        actuated_set = set(actuated)
        intended = {k: targets[k] for k in actuated}

        # Environment transition.
        new_values = list(values)
        for k in range(cfg.channels):
            if types[k] == WORLD:
                new_values[k] = 1 if env_rng.random() < cfg.p_world else 0
            else:  # SELF
                if k in actuated_set:
                    new_values[k] = intended[k]
                elif env_rng.random() < cfg.drift:
                    new_values[k] = 1 - new_values[k]  # drifts off-target unless maintained

        # Belief update (plastic conditions only): actuated channels get control
        # evidence; unmonitored channels relax toward 0.5 (the removable prior).
        if is_plastic(condition):
            for k in range(cfg.channels):
                if k in actuated_set:
                    signal = 1.0 if new_values[k] == intended[k] else 0.0
                    target_idx = perm[k] if condition == "shuffled_evidence" else k
                    belief[target_idx] += cfg.lr * (signal - belief[target_idx])
                else:
                    belief[k] += cfg.belief_decay * (0.5 - belief[k])

        values = new_values

        reward = mean(1.0 if values[k] == targets[k] else 0.0 for k in range(cfg.channels))
        rewards.append(reward)
        acc = mean(
            1.0 if (belief[k] > cfg.theta) == (types[k] == SELF) else 0.0 for k in range(cfg.channels)
        )
        boundary_acc.append(acc)
        crit.append(pvariance(belief))

        if shifted_at is not None and lag < 0 and step >= shifted_at + 1 and acc >= 0.85:
            lag = step - shifted_at

    pre = slice(cfg.shift_step - cfg.window, cfg.shift_step)
    post = slice(cfg.shift_step + cfg.settle, cfg.shift_step + cfg.settle + cfg.window)

    return ConditionResult(
        condition=condition,
        seed=seed,
        mean_reward_pre=mean(rewards[pre]),
        mean_reward_post=mean(rewards[post]),
        boundary_accuracy_pre=mean(boundary_acc[pre]),
        boundary_accuracy_post=mean(boundary_acc[post]),
        criticality_pre=mean(crit[pre]),
        criticality_post=mean(crit[post]),
        belief_tracking_lag=lag,
        probe_rate_pre=mean(probe_flags[pre]),
        probe_rate_post=mean(probe_flags[post]),
    )


CONDITIONS = (
    "plastic",
    "fixed_self_correct",
    "fixed_all_self",
    "fixed_all_world",
    "random_prior",
    "shuffled_evidence",
)


def summarize(results: list[ConditionResult]) -> dict[str, object]:
    by_cond: dict[str, list[ConditionResult]] = {}
    for r in results:
        by_cond.setdefault(r.condition, []).append(r)
    out: dict[str, object] = {}
    for cond, items in by_cond.items():
        out[cond] = {
            "seeds": [r.seed for r in items],
            "mean_reward_pre": mean(r.mean_reward_pre for r in items),
            "mean_reward_post": mean(r.mean_reward_post for r in items),
            "boundary_accuracy_pre": mean(r.boundary_accuracy_pre for r in items),
            "boundary_accuracy_post": mean(r.boundary_accuracy_post for r in items),
            "criticality_pre": mean(r.criticality_pre for r in items),
            "criticality_post": mean(r.criticality_post for r in items),
            "belief_tracking_lag": mean(r.belief_tracking_lag for r in items if r.belief_tracking_lag >= 0)
            if any(r.belief_tracking_lag >= 0 for r in items)
            else -1,
            "probe_rate_pre": mean(r.probe_rate_pre for r in items),
            "probe_rate_post": mean(r.probe_rate_post for r in items),
        }
    return out


def evaluate_gates(results: list[ConditionResult], cfg: Config) -> dict[str, object]:
    by_cond_seed: dict[tuple[str, int], ConditionResult] = {(r.condition, r.seed): r for r in results}
    seeds = sorted({r.seed for r in results})

    def get(cond: str, seed: int) -> ConditionResult:
        return by_cond_seed[(cond, seed)]

    g1 = all(
        get("plastic", s).mean_reward_post - get("fixed_self_correct", s).mean_reward_post >= 0.05
        for s in seeds
    )
    g2 = all(get("plastic", s).boundary_accuracy_post >= 0.85 for s in seeds)
    g3 = all(
        (get("plastic", s).mean_reward_post - get("shuffled_evidence", s).mean_reward_post >= 0.05)
        and (get("shuffled_evidence", s).boundary_accuracy_post <= 0.65)
        for s in seeds
    )
    g4 = all(
        get("fixed_self_correct", s).boundary_accuracy_pre >= 0.9
        and get("fixed_self_correct", s).boundary_accuracy_post <= 0.65
        for s in seeds
    )
    # Kill criterion: red-team shortcut ties plastic.
    shortcut_ties = all(
        abs(get("plastic", s).mean_reward_post - get("fixed_all_self", s).mean_reward_post) <= 0.03
        for s in seeds
    )
    return {
        "G1_adaptability": g1,
        "G2_re_tracking": g2,
        "G3_attribution_not_generic_plasticity": g3,
        "G4_boundary_really_moved": g4,
        "all_pass": bool(g1 and g2 and g3 and g4),
        "kill_red_team_shortcut_ties_plastic": shortcut_ties,
        "claim_tier": "diagnostic" if (g1 and g2 and g3 and g4) else "not_reached",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, nargs="*", default=list(PRE_SHIFT_SEEDS))
    parser.add_argument("--channels", type=int, default=Config.channels)
    parser.add_argument("--num-self", type=int, default=Config.num_self)
    parser.add_argument("--budget", type=int, default=Config.budget)
    parser.add_argument("--steps", type=int, default=Config.steps)
    parser.add_argument("--shift-step", type=int, default=Config.shift_step)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    cfg = Config(
        channels=args.channels,
        num_self=args.num_self,
        budget=args.budget,
        steps=args.steps,
        shift_step=args.shift_step,
    )

    results: list[ConditionResult] = []
    for seed in args.seeds:
        for cond in CONDITIONS:
            results.append(run_condition(cond, seed, cfg))

    payload = {
        "manifest": {
            "track": "boundary_priors",
            "seeds": args.seeds,
            "config": asdict(cfg),
            "conditions": list(CONDITIONS),
        },
        "summary": summarize(results),
        "gates": evaluate_gates(results, cfg),
        "results": [asdict(r) for r in results],
    }
    output = json.dumps(payload, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
