#!/usr/bin/env python3
"""Boundary Priors (Track 3) — costly probing & selective re-engagement.

Mechanism-tier follow-up to the diagnostic pilot. Probing now costs viability,
and the positive agent gates probing on *control-surprise* with decision-layer
cooling -- the maintained-boundary signature from the metric-stack's Paper 23B:
detect -> allocate -> satiate -> re-engage. A good agent goes quiet once the
self/world boundary is learned, re-engages after the boundary moves, then cools
back down once it has re-identified the controllable set.

This reuses the pilot environment primitives (``draw_types``, ``reshuffle_types``)
from ``experiment.py``. The agent loop differs (surprise-gated probing), so it is
written out here to keep the diagnostic pilot untouched.

Pre-registered mechanism gates M1-M4 are evaluated in ``evaluate_gates``; see
preregistration.md (Next item: "make probing costly and test selective
re-engagement"). Pure standard library, deterministic per seed.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean

from experiments.boundary_priors.experiment import (
    SELF,
    WORLD,
    draw_types,
    reshuffle_types,
)

PRE_SHIFT_SEEDS = (20260610, 1729, 4242)


@dataclass
class REConfig:
    channels: int = 8
    num_self: int = 3
    budget: int = 3
    p_world: float = 0.5
    drift: float = 0.15
    steps: int = 600
    shift_step: int = 300
    window: int = 120  # pre-shift + late-post steady window length
    early_post: int = 40  # window immediately after the shift (re-engagement spike)
    late_start_offset: int = 160  # late steady window starts shift + this
    lr: float = 0.3
    belief_decay: float = 0.03
    theta: float = 0.7
    init_belief: float = 0.5
    probe_cost: float = 0.06  # viability cost charged for each probe step (epistemic action is costly)
    warmup: int = 60  # forced probing so every condition learns the initial boundary
    # surprise/uncertainty-gated probing (positive condition)
    base_probe: float = 0.02
    k_unc: float = 0.6  # probe when the boundary model is uncertain
    k_surprise: float = 4.0  # probe when believed-self control is failing
    k_cool: float = 0.5
    rho: float = 0.9  # probe-effort decay (cooling)
    surprise_alpha: float = 0.4


# Probe policies: map condition -> callable(surprise, effort, uncertainty, cfg) -> p_probe.
def p_probe_reengaging(surprise: float, effort: float, uncertainty: float, cfg: REConfig) -> float:
    raw = cfg.base_probe + cfg.k_unc * uncertainty + cfg.k_surprise * surprise - cfg.k_cool * effort
    return min(0.95, max(0.0, raw))


def p_probe_fixed(_s: float, _e: float, _u: float, _cfg: REConfig) -> float:
    return 0.25


def p_probe_restless(_s: float, _e: float, _u: float, _cfg: REConfig) -> float:
    return 0.60


def p_probe_none(_s: float, _e: float, _u: float, _cfg: REConfig) -> float:
    return 0.0


POLICIES = {
    "reengaging": p_probe_reengaging,
    "fixed_probe": p_probe_fixed,
    "restless": p_probe_restless,
    "no_probe": p_probe_none,
}


@dataclass
class ConditionResult:
    condition: str
    seed: int
    probe_rate_pre: float
    probe_rate_early_post: float
    probe_rate_late_post: float
    reengagement_ratio: float
    net_reward_pre: float
    net_reward_late_post: float
    raw_reward_late_post: float
    boundary_accuracy_late_post: float


def choose_actuated(
    rng: random.Random, cfg: REConfig, belief: list[float], values: list[int], targets: list[int], probe: bool
) -> list[int]:
    channels = list(range(cfg.channels))
    if probe:
        rng.shuffle(channels)
        return channels[: cfg.budget]
    # Exploit ONLY: actuate believed-self channels (off-target first). No filling
    # with uncertain channels -- discovery of newly-controllable channels must go
    # through an explicit probe, so probing is genuinely necessary after a shift.
    rng.shuffle(channels)
    chosen = [k for k in channels if belief[k] > cfg.theta]
    chosen.sort(key=lambda k: 1.0 if values[k] != targets[k] else 0.0, reverse=True)
    return chosen[: cfg.budget]


def run_condition(condition: str, seed: int, cfg: REConfig) -> ConditionResult:
    rng = random.Random(seed)
    env_rng = random.Random(seed * 7919 + 1)
    policy = POLICIES[condition]

    types = draw_types(rng, cfg.channels, cfg.num_self)
    targets = [rng.randint(0, 1) for _ in range(cfg.channels)]
    values = [env_rng.randint(0, 1) for _ in range(cfg.channels)]
    belief = [cfg.init_belief] * cfg.channels

    surprise = 0.0
    effort = 0.0

    probe_flags: list[int] = []
    raw_rewards: list[float] = []
    net_rewards: list[float] = []
    boundary_acc: list[float] = []

    for step in range(cfg.steps):
        if step == cfg.shift_step:
            types = reshuffle_types(rng, cfg.channels, cfg.num_self, types)

        uncertainty = mean(1.0 - abs(2.0 * belief[k] - 1.0) for k in range(cfg.channels))
        if step < cfg.warmup:
            probe = True  # forced warmup: every condition learns the initial boundary
        else:
            probe = rng.random() < policy(surprise, effort, uncertainty, cfg)
        probe_flags.append(1 if probe else 0)

        actuated = choose_actuated(rng, cfg, belief, values, targets, probe)
        actuated_set = set(actuated)
        intended = {k: targets[k] for k in actuated}
        # Channels the agent *expected* to control (believed-self & actuated):
        expected_self = [k for k in actuated if belief[k] > cfg.theta]

        new_values = list(values)
        for k in range(cfg.channels):
            if types[k] == WORLD:
                new_values[k] = 1 if env_rng.random() < cfg.p_world else 0
            elif k in actuated_set:
                new_values[k] = intended[k]
            elif env_rng.random() < cfg.drift:
                new_values[k] = 1 - new_values[k]

        # Belief update (genuine attribution) + decay for unmonitored channels.
        for k in range(cfg.channels):
            if k in actuated_set:
                signal = 1.0 if new_values[k] == intended[k] else 0.0
                belief[k] += cfg.lr * (signal - belief[k])
            else:
                belief[k] += cfg.belief_decay * (0.5 - belief[k])

        # Control-surprise: how often a believed-self actuation failed to control.
        if expected_self:
            event = mean(0.0 if new_values[k] == intended[k] else 1.0 for k in expected_self)
            surprise += cfg.surprise_alpha * (event - surprise)

        # Decision-layer cooling: probe effort integrates probes and decays.
        effort *= cfg.rho
        if probe:
            effort += 1.0

        values = new_values

        raw_reward = mean(1.0 if values[k] == targets[k] else 0.0 for k in range(cfg.channels))
        raw_rewards.append(raw_reward)
        net_rewards.append(raw_reward - (cfg.probe_cost if probe else 0.0))
        boundary_acc.append(
            mean(1.0 if (belief[k] > cfg.theta) == (types[k] == SELF) else 0.0 for k in range(cfg.channels))
        )

    pre = slice(cfg.shift_step - cfg.window, cfg.shift_step)
    early = slice(cfg.shift_step, cfg.shift_step + cfg.early_post)
    late = slice(cfg.shift_step + cfg.late_start_offset, cfg.shift_step + cfg.late_start_offset + cfg.window)

    pr_pre = mean(probe_flags[pre])
    pr_early = mean(probe_flags[early])
    pr_late = mean(probe_flags[late])

    return ConditionResult(
        condition=condition,
        seed=seed,
        probe_rate_pre=pr_pre,
        probe_rate_early_post=pr_early,
        probe_rate_late_post=pr_late,
        reengagement_ratio=(pr_early / pr_pre) if pr_pre > 1e-6 else float("inf"),
        net_reward_pre=mean(net_rewards[pre]),
        net_reward_late_post=mean(net_rewards[late]),
        raw_reward_late_post=mean(raw_rewards[late]),
        boundary_accuracy_late_post=mean(boundary_acc[late]),
    )


CONDITIONS = ("reengaging", "fixed_probe", "restless", "no_probe")


def summarize(results: list[ConditionResult]) -> dict[str, object]:
    by_cond: dict[str, list[ConditionResult]] = {}
    for r in results:
        by_cond.setdefault(r.condition, []).append(r)
    out: dict[str, object] = {}
    for cond, items in by_cond.items():
        finite_ratios = [r.reengagement_ratio for r in items if r.reengagement_ratio != float("inf")]
        out[cond] = {
            "probe_rate_pre": mean(r.probe_rate_pre for r in items),
            "probe_rate_early_post": mean(r.probe_rate_early_post for r in items),
            "probe_rate_late_post": mean(r.probe_rate_late_post for r in items),
            "reengagement_ratio": mean(finite_ratios) if finite_ratios else float("inf"),
            "net_reward_pre": mean(r.net_reward_pre for r in items),
            "net_reward_late_post": mean(r.net_reward_late_post for r in items),
            "raw_reward_late_post": mean(r.raw_reward_late_post for r in items),
            "boundary_accuracy_late_post": mean(r.boundary_accuracy_late_post for r in items),
        }
    return out


def evaluate_gates(results: list[ConditionResult]) -> dict[str, object]:
    by: dict[tuple[str, int], ConditionResult] = {(r.condition, r.seed): r for r in results}
    seeds = sorted({r.seed for r in results})

    def g(cond: str, seed: int) -> ConditionResult:
        return by[(cond, seed)]

    # M1: selective re-engagement -- quiet pre-shift, spike right after the shift.
    m1 = all(
        g("reengaging", s).probe_rate_pre < 0.10
        and g("reengaging", s).probe_rate_early_post >= 0.15
        and g("reengaging", s).probe_rate_early_post >= 1.5 * max(g("reengaging", s).probe_rate_pre, 1e-6)
        for s in seeds
    )
    # M2: satiation -- cools back down after re-identifying.
    m2 = all(
        g("reengaging", s).probe_rate_late_post < g("reengaging", s).probe_rate_early_post for s in seeds
    )
    # M3: net-reward dominance under probe cost vs constant-rate probers.
    m3 = all(
        g("reengaging", s).net_reward_late_post >= g("fixed_probe", s).net_reward_late_post
        and g("reengaging", s).net_reward_late_post >= g("restless", s).net_reward_late_post
        for s in seeds
    )
    # M4: no-false-calm -- low late probing is because attribution resolved, not abandoned.
    m4 = all(g("reengaging", s).boundary_accuracy_late_post >= 0.85 for s in seeds)
    # Context: no_probe should fail to recover the boundary.
    no_probe_fails = all(g("no_probe", s).boundary_accuracy_late_post < 0.85 for s in seeds)

    return {
        "M1_selective_re_engagement": m1,
        "M2_satiation": m2,
        "M3_net_reward_dominance_under_cost": m3,
        "M4_no_false_calm": m4,
        "all_pass": bool(m1 and m2 and m3 and m4),
        "context_no_probe_fails_to_recover": no_probe_fails,
        "claim_tier": "mechanism" if (m1 and m2 and m3 and m4) else "not_reached",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, nargs="*", default=list(PRE_SHIFT_SEEDS))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    cfg = REConfig()
    results: list[ConditionResult] = []
    for seed in args.seeds:
        for cond in CONDITIONS:
            results.append(run_condition(cond, seed, cfg))

    payload = {
        "manifest": {"track": "boundary_priors", "mode": "reengagement", "seeds": args.seeds, "config": asdict(cfg)},
        "summary": summarize(results),
        "gates": evaluate_gates(results),
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
