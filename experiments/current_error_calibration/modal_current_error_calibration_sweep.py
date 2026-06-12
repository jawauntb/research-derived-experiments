#!/usr/bin/env python3
"""Paper 19 — Current-Error Calibration for Identifying Interventions.

Tests three hypotheses for Paper 18's V_probe anti-calibration failure:
  H1 — lag: recent residuals (α=0.20 or sliding window) restore calibration
  H2 — staleness: residuals must be recomputed against current world_head
  H3 — structural: local same-class signals are non-epistemic

Conditions:
  - factorized_no_null_online            : gauge failure baseline
  - scheduled_null_anchor_online         : positive anchor control
  - matched_random_online                : same null count, random placement (Pass 2)
  - learned_historical_ema_online        : P18 baseline (α=0.05, lagged absolute)
  - learned_recent_ema_online            : H1 (α=0.20, lagged absolute)
  - learned_sliding_window_online        : H1 nonparametric (last K=50 signed residuals)
  - learned_current_replay_online        : H2 (per-bucket buffer; current-model residuals)
  - learned_current_replay_audit_online  : HEADLINE (current_replay + 5% audit floor)
  - oracle_uncertainty_probe_online      : upper bound on probe placement
  - oracle_source_online                 : upper bound on semantic decomposition

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/current_error_calibration/modal_current_error_calibration_sweep.py
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "numpy>=1.26,<2.0",
)

app = modal.App(name="research-derived-current-error-calibration")

ITEM_TYPES = {
    (0, 0): {"role": "food", "dE_consume": +1.0},
    (0, 1): {"role": "poison", "dE_consume": -1.0},
    (1, 0): {"role": "medicine", "dE_consume": -0.1},
    (1, 1): {"role": "neutral", "dE_consume": 0.0},
}
ITEMS = list(ITEM_TYPES.keys())
ROLES = ["food", "poison", "medicine", "neutral"]

EMBED_DIM = 32
OBS_NOISE = 0.15
T_MAX = 50
ENERGY_DECAY = 0.04
ENERGY_INIT = 0.5
SHOCK_MAGNITUDE = 0.30

N_ACTIONS_WITH_NULL = 3
N_ACTIONS_NO_NULL = 2

TRAINING_SHOCK = {"food": 0.8, "poison": 0.1, "medicine": 0.1, "neutral": 0.1}
SHIFTED_SHOCK = {"food": 0.1, "poison": 0.1, "medicine": 0.8, "neutral": 0.1}

COST_HEADLINE = 0.025

EMA_ALPHA_HISTORICAL = 0.05
EMA_ALPHA_RECENT = 0.20
SLIDING_WINDOW_K = 50
CURRENT_REPLAY_K = 64
AUDIT_FLOOR = 0.05

ALL_CONDITIONS = [
    "factorized_no_null_online",
    "scheduled_null_anchor_online",
    "matched_random_online",
    "learned_historical_ema_online",
    "learned_recent_ema_online",
    "learned_sliding_window_online",
    "learned_current_replay_online",
    "learned_current_replay_audit_online",
    "oracle_uncertainty_probe_online",
    "oracle_source_online",
]

LEARNED_PROBE_CONDS = {
    "learned_historical_ema_online",
    "learned_recent_ema_online",
    "learned_sliding_window_online",
    "learned_current_replay_online",
    "learned_current_replay_audit_online",
}


def role_of(c, l):
    return ITEM_TYPES[(c, l)]["role"]


def consume_self_dE(c, l):
    return ITEM_TYPES[(c, l)]["dE_consume"]


def true_world_expectation(c, l, shock_dist):
    return shock_dist[role_of(c, l)] * SHOCK_MAGNITUDE


@app.function(image=IMAGE, timeout=3600, cpu=4, memory=4096)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from collections import defaultdict, deque

    seed: int = arg["seed"]
    condition: str = arg["condition"]
    cost: float = arg["cost"]
    target_null_rate = arg.get("target_null_rate", None)
    n_episodes: int = arg["n_episodes"]
    batch_size: int = arg["batch_size"]
    eval_episodes: int = arg["eval_episodes"]

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cpu")
    rng_env = np.random.RandomState(seed + 13)
    perm = rng_env.permutation(16)

    has_null = condition != "factorized_no_null_online"
    n_actions = N_ACTIONS_WITH_NULL if has_null else N_ACTIONS_NO_NULL

    use_target = "none"
    use_audit = False
    if condition == "learned_historical_ema_online":
        use_target = "historical_ema"
    elif condition == "learned_recent_ema_online":
        use_target = "recent_ema"
    elif condition == "learned_sliding_window_online":
        use_target = "sliding_window"
    elif condition == "learned_current_replay_online":
        use_target = "current_replay"
    elif condition == "learned_current_replay_audit_online":
        use_target = "current_replay"
        use_audit = True

    is_learned_probe_eval = condition in LEARNED_PROBE_CONDS
    is_oracle_probe_eval = condition == "oracle_uncertainty_probe_online"

    def encode_one(c, l, rng):
        obs = np.zeros(16, dtype=np.float32)
        obs[c] = 1.0
        obs[8 + l] = 1.0
        obs = obs + rng.randn(16).astype(np.float32) * OBS_NOISE
        return obs[perm]

    def fourier_E(E_tensor):
        if E_tensor.dim() == 2:
            E_tensor = E_tensor.squeeze(-1)
        feats = [E_tensor.unsqueeze(-1)]
        for freq in [1.0, 2.0, 4.0]:
            feats.append(torch.sin(torch.pi * freq * E_tensor).unsqueeze(-1))
            feats.append(torch.cos(torch.pi * freq * E_tensor).unsqueeze(-1))
        return torch.cat(feats, dim=-1)

    def action_self_dE(action, c, l):
        if action == 1:
            return consume_self_dE(c, l) - ENERGY_DECAY
        else:
            return -ENERGY_DECAY

    def sample_world_shock(c, l, shock_dist, rng):
        if rng.rand() < shock_dist[role_of(c, l)]:
            return SHOCK_MAGNITUDE
        return 0.0

    def bucket_key(c, l, E):
        e_bin = "E_low" if E < 0.5 else "E_high"
        return f"{role_of(c, l)}_{e_bin}"

    BUCKETS = [f"{r}_{e}" for r in ROLES for e in ("E_low", "E_high")]

    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)
    self_head = nn.Sequential(
        nn.Linear(EMBED_DIM + 7 + n_actions, 32), nn.Tanh(),
        nn.Linear(32, 1),
    ).to(device)
    world_head = nn.Sequential(
        nn.Linear(EMBED_DIM + 7, 32), nn.Tanh(),
        nn.Linear(32, 1),
    ).to(device)
    v_probe_head = nn.Sequential(
        nn.Linear(EMBED_DIM + 7, 32), nn.Tanh(),
        nn.Linear(32, 1), nn.Softplus(),
    ).to(device)

    params = (list(encoder.parameters()) + list(self_head.parameters())
              + list(world_head.parameters())
              + list(v_probe_head.parameters()))
    opt = torch.optim.Adam(params, lr=2e-3)

    # Target-variant state
    historical_ema = {b: 0.0 for b in BUCKETS}
    recent_ema = {b: 0.0 for b in BUCKETS}
    sliding_window = {b: deque(maxlen=SLIDING_WINDOW_K) for b in BUCKETS}
    current_replay_buf = {b: deque(maxlen=CURRENT_REPLAY_K) for b in BUCKETS}
    bucket_count = {b: 0 for b in BUCKETS}
    # Track world_head error per bucket at start vs end of training (for G15)
    bucket_initial_world_error = {b: None for b in BUCKETS}
    bucket_null_density = {b: 0 for b in BUCKETS}

    def step_loss(z, ffE, a_oh, actions_np, total_dE_t, self_dE_t,
                  world_dE_t, lagged_v_targets_t):
        self_input = torch.cat([z, ffE, a_oh], dim=-1)
        world_input = torch.cat([z, ffE], dim=-1)
        pred_self = self_head(self_input).squeeze(-1)
        pred_world = world_head(world_input).squeeze(-1)
        target_total = total_dE_t

        if condition == "factorized_no_null_online":
            attr_loss = F.mse_loss(pred_self + pred_world, target_total)
        elif condition == "oracle_source_online":
            attr_loss = (F.mse_loss(pred_self, self_dE_t)
                         + F.mse_loss(pred_world, world_dE_t))
        else:
            null_mask = torch.from_numpy(actions_np == 2)
            non_null_mask = ~null_mask
            null_loss = torch.tensor(0.0, device=device)
            non_null_loss = torch.tensor(0.0, device=device)
            if null_mask.any():
                null_world_loss = F.mse_loss(
                    pred_world[null_mask], target_total[null_mask]
                )
                null_self_anchor = F.mse_loss(
                    pred_self[null_mask],
                    torch.full_like(pred_self[null_mask], -ENERGY_DECAY),
                )
                null_loss = null_world_loss + 0.5 * null_self_anchor
            if non_null_mask.any():
                non_null_loss = F.mse_loss(
                    pred_self[non_null_mask] + pred_world[non_null_mask],
                    target_total[non_null_mask],
                )
            attr_loss = null_loss + non_null_loss

        # V_probe loss (only meaningful for learned-probe conditions)
        v_loss = torch.tensor(0.0, device=device)
        if has_null and condition in LEARNED_PROBE_CONDS:
            null_mask_t = torch.from_numpy(actions_np == 2)
            if null_mask_t.any():
                v_target = lagged_v_targets_t[null_mask_t]
                v_pred = v_probe_head(world_input[null_mask_t]).squeeze(-1)
                v_loss = F.mse_loss(v_pred, v_target)

        return attr_loss + 0.5 * v_loss

    def get_current_replay_error_per_bucket():
        """Recompute current world_head error per bucket from replay buffer."""
        errs = {b: 0.0 for b in BUCKETS}
        for b in BUCKETS:
            if len(current_replay_buf[b]) == 0:
                continue
            obs_arr = np.stack([t[0] for t in current_replay_buf[b]])
            Es_arr = np.array([t[1] for t in current_replay_buf[b]],
                                dtype=np.float32)
            totals_arr = np.array([t[2] for t in current_replay_buf[b]],
                                    dtype=np.float32)
            with torch.no_grad():
                x = torch.from_numpy(obs_arr).to(device)
                z = encoder(x)
                e_t = torch.from_numpy(Es_arr.reshape(-1, 1)).to(device)
                ffE = fourier_E(e_t)
                pw = world_head(torch.cat([z, ffE], dim=-1)).squeeze(-1)
                signed = (pw.cpu().numpy() - totals_arr).mean()
            errs[b] = float(abs(signed))
        return errs

    def get_v_target_for_bucket(b):
        if use_target == "historical_ema":
            return abs(historical_ema[b])
        elif use_target == "recent_ema":
            return abs(recent_ema[b])
        elif use_target == "sliding_window":
            if len(sliding_window[b]) == 0:
                return 0.0
            return abs(float(np.mean(sliding_window[b])))
        elif use_target == "current_replay":
            errs = get_current_replay_error_per_bucket()
            return errs.get(b, 0.0)
        return 0.0

    buffer = []
    SGD_EVERY = 30
    SGD_K = 4
    rng_online = np.random.RandomState(seed + 47)
    global_step = 0

    matched_target_rate = (float(target_null_rate)
                            if target_null_rate is not None else 0.20)
    matched_target_rate = max(0.02, min(0.6, matched_target_rate))

    # Capture initial world error per bucket for G15
    def capture_world_error_per_bucket(rng):
        out = {}
        for (c, l), _ in ITEM_TYPES.items():
            true_world = true_world_expectation(c, l, TRAINING_SHOCK)
            for E_bin_name, E_val in [("E_low", 0.25), ("E_high", 0.75)]:
                key = f"{role_of(c, l)}_{E_bin_name}"
                obs_list = [encode_one(c, l, rng) for _ in range(32)]
                obs_arr = np.stack(obs_list)
                with torch.no_grad():
                    z = encoder(torch.from_numpy(obs_arr).to(device))
                    e_t = torch.full((32, 1), E_val,
                                      dtype=torch.float32, device=device)
                    ffE = fourier_E(e_t)
                    pw = world_head(torch.cat([z, ffE], dim=-1)).squeeze(-1)
                    w_mean = float(pw.cpu().numpy().mean())
                out[key] = abs(w_mean - true_world)
        return out

    bucket_initial_world_error = capture_world_error_per_bucket(
        np.random.RandomState(seed + 1234)
    )

    # ============ ONLINE TRAINING (all conds are online here) ============
    for episode in range(n_episodes):
        E = ENERGY_INIT
        steps = 0
        eps_explore = max(0.05, 0.30 - 0.25 * (episode / max(n_episodes, 1)))
        while E > 0 and steps < T_MAX:
            idx = rng_online.randint(0, len(ITEMS))
            c_, l_ = ITEMS[idx]
            obs_raw = encode_one(c_, l_, rng_online)
            x = torch.from_numpy(obs_raw[None]).float().to(device)

            with torch.no_grad():
                z_cur = encoder(x)
                e_cur_t = torch.full((1, 1), float(E),
                                      dtype=torch.float32, device=device)
                ffE_cur = fourier_E(e_cur_t)
                w_inp_cur = torch.cat([z_cur, ffE_cur], dim=-1)
                v_val = float(v_probe_head(w_inp_cur).item())
                w_pred_cur = float(world_head(w_inp_cur).item())
                scores = []
                for a in [0, 1]:
                    a_oh = torch.zeros(1, n_actions, device=device)
                    a_oh[0, a] = 1.0
                    s_inp = torch.cat([z_cur, ffE_cur, a_oh], dim=-1)
                    scores.append(float(self_head(s_inp).item()))
                greedy_action = 0 if scores[0] >= scores[1] else 1

            take_null = False
            if condition == "factorized_no_null_online":
                take_null = False
            elif condition == "scheduled_null_anchor_online":
                take_null = (rng_online.rand() < 0.33)
            elif condition == "matched_random_online":
                take_null = (rng_online.rand() < matched_target_rate)
            elif condition in LEARNED_PROBE_CONDS:
                learned_fire = (v_val > cost)
                audit_fire = (use_audit and rng_online.rand() < AUDIT_FLOOR)
                take_null = learned_fire or audit_fire
            elif condition == "oracle_uncertainty_probe_online":
                true_world = (TRAINING_SHOCK[role_of(c_, l_)]
                               * SHOCK_MAGNITUDE)
                take_null = (abs(w_pred_cur - true_world) > cost)
            elif condition == "oracle_source_online":
                take_null = (rng_online.rand() < 0.33)

            if take_null:
                action = 2
            else:
                if rng_online.rand() < eps_explore:
                    action = int(rng_online.choice([0, 1]))
                else:
                    action = greedy_action

            self_step_base = action_self_dE(action, c_, l_)
            world_step = sample_world_shock(c_, l_, TRAINING_SHOCK, rng_online)
            total_cost_free = self_step_base + world_step
            E_delta = total_cost_free - (cost if action == 2 else 0.0)

            # V_probe target lookup BEFORE updating bucket state
            b_now = bucket_key(c_, l_, E)
            lagged_v_target = 0.0
            if action == 2 and condition in LEARNED_PROBE_CONDS:
                lagged_v_target = get_v_target_for_bucket(b_now)

            buffer.append(dict(
                obs=obs_raw, E=float(E), action=int(action),
                total=float(total_cost_free),
                self_dE=float(self_step_base),
                world_dE=float(world_step), c=int(c_), l=int(l_),
                lagged_v=float(lagged_v_target),
                bucket=b_now,
            ))

            if action == 2:
                # Update bucket-state based on observation (post-record)
                signed = w_pred_cur - total_cost_free
                if condition in LEARNED_PROBE_CONDS:
                    if use_target == "historical_ema":
                        if bucket_count[b_now] == 0:
                            historical_ema[b_now] = signed
                        else:
                            historical_ema[b_now] = (
                                (1 - EMA_ALPHA_HISTORICAL) * historical_ema[b_now]
                                + EMA_ALPHA_HISTORICAL * signed
                            )
                    elif use_target == "recent_ema":
                        if bucket_count[b_now] == 0:
                            recent_ema[b_now] = signed
                        else:
                            recent_ema[b_now] = (
                                (1 - EMA_ALPHA_RECENT) * recent_ema[b_now]
                                + EMA_ALPHA_RECENT * signed
                            )
                    elif use_target == "sliding_window":
                        sliding_window[b_now].append(signed)
                    elif use_target == "current_replay":
                        current_replay_buf[b_now].append(
                            (obs_raw.copy(), float(E), float(total_cost_free))
                        )
                bucket_count[b_now] += 1
                bucket_null_density[b_now] += 1

            global_step += 1

            if (len(buffer) >= 64
                    and global_step % SGD_EVERY == 0):
                for _ in range(SGD_K):
                    per_stratum = batch_size // 3
                    idx_by_action = defaultdict(list)
                    for k, bb in enumerate(buffer):
                        idx_by_action[bb["action"]].append(k)
                    sampled_idxs = []
                    for a in range(n_actions):
                        pool = idx_by_action.get(a, [])
                        if not pool:
                            continue
                        take = min(per_stratum, len(pool))
                        sampled_idxs.extend(rng_online.choice(
                            pool, size=take, replace=(take > len(pool))
                        ).tolist())
                    if not sampled_idxs:
                        continue
                    rng_online.shuffle(sampled_idxs)
                    mb = [buffer[k] for k in sampled_idxs]

                    actions_arr = np.array([bb["action"] for bb in mb],
                                            dtype=np.int64)
                    Es_arr = np.array([bb["E"] for bb in mb], dtype=np.float32)
                    totals_arr = np.array([bb["total"] for bb in mb],
                                           dtype=np.float32)
                    selfs_arr = np.array([bb["self_dE"] for bb in mb],
                                          dtype=np.float32)
                    worlds_arr = np.array([bb["world_dE"] for bb in mb],
                                           dtype=np.float32)
                    obss_arr = np.stack([bb["obs"] for bb in mb])

                    # Compute V_probe targets for this minibatch
                    # For current_replay: recompute fresh per-bucket errors
                    if use_target == "current_replay":
                        fresh_errs = get_current_replay_error_per_bucket()
                        lvts_arr = np.array(
                            [fresh_errs.get(bb["bucket"], 0.0)
                             if bb["action"] == 2 else 0.0 for bb in mb],
                            dtype=np.float32,
                        )
                    else:
                        lvts_arr = np.array(
                            [bb["lagged_v"] for bb in mb],
                            dtype=np.float32,
                        )

                    x_mb = torch.from_numpy(obss_arr).to(device)
                    z_mb = encoder(x_mb)
                    e_mb = torch.from_numpy(
                        Es_arr.reshape(-1, 1)
                    ).to(device)
                    ffE_mb = fourier_E(e_mb)
                    a_oh = torch.zeros(len(mb), n_actions, device=device)
                    a_oh[np.arange(len(mb)), actions_arr] = 1.0

                    total_t = torch.from_numpy(totals_arr).to(device)
                    self_t = torch.from_numpy(selfs_arr).to(device)
                    world_t = torch.from_numpy(worlds_arr).to(device)
                    lvt_t = torch.from_numpy(lvts_arr).to(device)
                    loss = step_loss(
                        z_mb, ffE_mb, a_oh, actions_arr,
                        total_t, self_t, world_t, lvt_t,
                    )
                    opt.zero_grad(); loss.backward(); opt.step()

            E = max(0.0, min(1.0, E + E_delta))
            steps += 1

    encoder.eval(); self_head.eval(); world_head.eval(); v_probe_head.eval()

    bucket_final_world_error = capture_world_error_per_bucket(
        np.random.RandomState(seed + 5678)
    )

    # ============ Component-recovery diagnostics across E grid ============
    rng_diag = np.random.RandomState(seed + 333)
    n_diag = 128
    E_GRID = [0.1, 0.25, 0.5, 0.75, 0.9]
    pred_by_role = {}
    for (c, l), info in ITEM_TYPES.items():
        role = info["role"]
        obs_list = [encode_one(c, l, rng_diag) for _ in range(n_diag)]
        obs_arr = np.stack(obs_list)
        with torch.no_grad():
            z = encoder(torch.from_numpy(obs_arr).to(device))
            results = {}
            for action_idx in range(n_actions):
                preds_across_E = []
                for E_val in E_GRID:
                    e_t = torch.full((n_diag, 1), E_val,
                                      dtype=torch.float32, device=device)
                    ffE = fourier_E(e_t)
                    a_oh = torch.zeros(n_diag, n_actions, device=device)
                    a_oh[:, action_idx] = 1.0
                    inp = torch.cat([z, ffE, a_oh], dim=-1)
                    pred_s = self_head(inp).squeeze(-1).cpu().numpy()
                    preds_across_E.append(float(pred_s.mean()))
                results[f"self_action_{action_idx}"] = float(np.mean(preds_across_E))
                results[f"self_action_{action_idx}_by_E"] = preds_across_E
            world_preds = []
            v_preds = []
            for E_val in E_GRID:
                e_t = torch.full((n_diag, 1), E_val,
                                  dtype=torch.float32, device=device)
                ffE = fourier_E(e_t)
                world_input = torch.cat([z, ffE], dim=-1)
                world_preds.append(
                    float(world_head(world_input).squeeze(-1).cpu().numpy().mean())
                )
                v_preds.append(
                    float(v_probe_head(world_input).squeeze(-1).cpu().numpy().mean())
                )
            results["world"] = float(np.mean(world_preds))
            results["world_by_E"] = world_preds
            results["v_probe"] = float(np.mean(v_preds))
        results["true_self_consume"] = consume_self_dE(c, l) - ENERGY_DECAY
        results["true_self_skip_or_null"] = -ENERGY_DECAY
        results["true_world_in_dist"] = true_world_expectation(c, l, TRAINING_SHOCK)
        results["true_world_shift"] = true_world_expectation(c, l, SHIFTED_SHOCK)
        pred_by_role[role] = results

    # Per-bucket diagnostics
    bucket_diag = {}
    for (c, l), _ in ITEM_TYPES.items():
        true_world = true_world_expectation(c, l, TRAINING_SHOCK)
        for E_bin_name, E_val in [("E_low", 0.25), ("E_high", 0.75)]:
            key = f"{role_of(c, l)}_{E_bin_name}"
            obs_list = [encode_one(c, l, rng_diag) for _ in range(64)]
            obs_arr = np.stack(obs_list)
            with torch.no_grad():
                z = encoder(torch.from_numpy(obs_arr).to(device))
                e_t = torch.full((64, 1), E_val, dtype=torch.float32, device=device)
                ffE = fourier_E(e_t)
                world_input = torch.cat([z, ffE], dim=-1)
                v_vals = v_probe_head(world_input).squeeze(-1).cpu().numpy()
                w_vals = world_head(world_input).squeeze(-1).cpu().numpy()
            v_probe_mean = float(v_vals.mean())
            world_pred_mean = float(w_vals.mean())
            bucket_diag[key] = dict(
                v_probe=v_probe_mean,
                world_pred=world_pred_mean,
                true_world=true_world,
                oracle_uncertainty=abs(world_pred_mean - true_world),
                initial_world_error=float(
                    bucket_initial_world_error.get(key, 0.0)
                ),
                final_world_error=float(
                    bucket_final_world_error.get(key, 0.0)
                ),
                world_error_reduction=float(
                    bucket_initial_world_error.get(key, 0.0)
                    - bucket_final_world_error.get(key, 0.0)
                ),
                null_density=int(bucket_null_density.get(key, 0)),
            )

    # ============ Eval ============
    def plan_consume_or_skip(z_eval, E_now):
        with torch.no_grad():
            e_t = torch.full((z_eval.shape[0], 1), float(E_now),
                             dtype=torch.float32, device=device)
            ffE = fourier_E(e_t)
            scores = np.zeros(2)
            for a in [0, 1]:
                a_oh = torch.zeros(z_eval.shape[0], n_actions, device=device)
                a_oh[:, a] = 1.0
                inp = torch.cat([z_eval, ffE, a_oh], dim=-1)
                scores[a] = self_head(inp).item()
            return int(np.argmax(scores))

    def eval_under(shock_dist, dist_name):
        rng_eval = np.random.RandomState(seed + 9999 + hash(dist_name) % 1000)
        returns = []
        acc_records = []
        null_actions = 0
        total_actions = 0
        probe_fires_by_bucket = {b: 0 for b in BUCKETS}
        state_visits_by_bucket = {b: 0 for b in BUCKETS}
        for _ in range(eval_episodes):
            E = ENERGY_INIT
            steps = 0
            while E > 0 and steps < T_MAX:
                idx = rng_eval.randint(0, len(ITEMS))
                c_, l_ = ITEMS[idx]
                obs_ = encode_one(c_, l_, rng_eval)
                x = torch.from_numpy(obs_[None]).float().to(device)
                with torch.no_grad():
                    z = encoder(x)
                    e_cur_t = torch.full((1, 1), float(E),
                                          dtype=torch.float32, device=device)
                    ffE_cur = fourier_E(e_cur_t)
                    w_inp = torch.cat([z, ffE_cur], dim=-1)
                    v_val = float(v_probe_head(w_inp).item())
                    w_pred = float(world_head(w_inp).item())
                bk = bucket_key(c_, l_, E)
                state_visits_by_bucket[bk] += 1
                should_null = False
                if is_learned_probe_eval and has_null:
                    learned_fire = (v_val > cost)
                    audit_fire = (use_audit and rng_eval.rand() < AUDIT_FLOOR)
                    should_null = learned_fire or audit_fire
                elif is_oracle_probe_eval and has_null:
                    true_world = (TRAINING_SHOCK[role_of(c_, l_)]
                                   * SHOCK_MAGNITUDE)
                    should_null = (abs(w_pred - true_world) > cost)
                if should_null:
                    action = 2
                    null_actions += 1
                    probe_fires_by_bucket[bk] += 1
                else:
                    action = plan_consume_or_skip(z, E)
                total_actions += 1
                self_step = action_self_dE(action, c_, l_)
                world_step = sample_world_shock(c_, l_, shock_dist, rng_eval)
                if action == 2:
                    self_step = self_step - cost
                optimal = 1 if consume_self_dE(c_, l_) > 0 else 0
                if action != 2:
                    acc_records.append(int(action == optimal))
                E = max(0.0, min(1.0, E + self_step + world_step))
                steps += 1
            returns.append(float(steps))
        return dict(
            distribution=dist_name,
            mean_return=float(np.mean(returns)),
            action_accuracy=(float(np.mean(acc_records))
                              if acc_records else 0.0),
            null_rate=(null_actions / max(total_actions, 1)),
            probe_fires_by_bucket=probe_fires_by_bucket,
            state_visits_by_bucket=state_visits_by_bucket,
        )

    in_dist = eval_under(TRAINING_SHOCK, "in_dist")
    shifted = eval_under(SHIFTED_SHOCK, "shifted")

    return dict(
        seed=seed, condition=condition, cost=cost,
        has_null=has_null, n_actions=n_actions,
        target_null_rate=target_null_rate,
        use_target=use_target, use_audit=use_audit,
        in_dist_eval=in_dist, shifted_eval=shifted,
        prediction_by_role=pred_by_role,
        bucket_diag=bucket_diag,
    )


def _flatten_to_row(r):
    row = dict(
        seed=r["seed"], condition=r["condition"], cost=r["cost"],
        has_null=r["has_null"],
        target_null_rate=r.get("target_null_rate"),
        in_dist_return=r["in_dist_eval"]["mean_return"],
        in_dist_acc=r["in_dist_eval"]["action_accuracy"],
        in_dist_null_rate=r["in_dist_eval"]["null_rate"],
        shifted_return=r["shifted_eval"]["mean_return"],
        shifted_acc=r["shifted_eval"]["action_accuracy"],
        shifted_null_rate=r["shifted_eval"]["null_rate"],
    )
    for role, info in r["prediction_by_role"].items():
        row[f"pred_self_consume_{role}"] = info["self_action_1"]
        row[f"pred_self_skip_{role}"] = info["self_action_0"]
        if "self_action_2" in info:
            row[f"pred_self_null_{role}"] = info["self_action_2"]
        row[f"pred_world_{role}"] = info["world"]
        row[f"pred_v_probe_{role}"] = info["v_probe"]
        row[f"true_self_consume_{role}"] = info["true_self_consume"]
        row[f"true_self_skip_or_null_{role}"] = info["true_self_skip_or_null"]
        row[f"true_world_in_dist_{role}"] = info["true_world_in_dist"]
        row[f"true_world_shift_{role}"] = info["true_world_shift"]
    return row


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    n_episodes: int = 200,
    batch_size: int = 48,
    eval_episodes: int = 50,
    out: str = "artifacts/current_error_calibration/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    # Headline cost only for primary sweep
    primary_cost = COST_HEADLINE

    # All conditions except matched_random in Pass 1
    pass1_args = []
    pass1_conds = [c for c in ALL_CONDITIONS if c != "matched_random_online"]
    for sd in seed_list:
        for cond in pass1_conds:
            pass1_args.append(dict(
                seed=sd, condition=cond, cost=primary_cost,
                n_episodes=n_episodes,
                batch_size=batch_size, eval_episodes=eval_episodes,
            ))
    print(f"PASS 1: running {len(pass1_args)} cells in parallel...")
    pass1_results = list(run_cell.map(pass1_args))

    # Match matched_random to headline learned_current_replay_audit's null rate
    rates = {}
    for r in pass1_results:
        if r["condition"] == "learned_current_replay_audit_online":
            rates[int(r["seed"])] = r["in_dist_eval"]["null_rate"]
    print(f"  headline (current_replay_audit) rates: {rates}")

    pass2_args = []
    for sd in seed_list:
        target_rate = rates.get(sd, 0.20)
        pass2_args.append(dict(
            seed=sd, condition="matched_random_online", cost=primary_cost,
            target_null_rate=target_rate,
            n_episodes=n_episodes,
            batch_size=batch_size, eval_episodes=eval_episodes,
        ))
    print(f"PASS 2: running {len(pass2_args)} matched_random cells...")
    pass2_results = list(run_cell.map(pass2_args))

    results = pass1_results + pass2_results
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = [_flatten_to_row(r) for r in results]

    out_path.write_text(json.dumps({
        "manifest": dict(
            seeds=seed_list, conditions=ALL_CONDITIONS,
            cost_headline=COST_HEADLINE,
            n_episodes=n_episodes,
            batch_size=batch_size, eval_episodes=eval_episodes,
            training_shock=TRAINING_SHOCK, shifted_shock=SHIFTED_SHOCK,
            shock_magnitude=SHOCK_MAGNITUDE,
            ema_alpha_historical=EMA_ALPHA_HISTORICAL,
            ema_alpha_recent=EMA_ALPHA_RECENT,
            sliding_window_K=SLIDING_WINDOW_K,
            current_replay_K=CURRENT_REPLAY_K,
            audit_floor=AUDIT_FLOOR,
            item_types={f"{c},{l}": info for (c, l), info in ITEM_TYPES.items()},
            realized_headline_rates={str(k): v for k, v in rates.items()},
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nsummary ({len(summary_rows)} cells):")
    print(f"{'cond':<42} {'seed':>10} {'cost':>5} | "
          f"{'ps_food':>7} {'pw_food':>7} {'ret':>5} {'null%':>6}")
    print(f"  TRUE FOOD: self_consume=+0.96, world_in_dist=+0.24")
    for r in summary_rows:
        psw = r.get('pred_world_food')
        psw_str = f"{psw:+.3f}" if psw is not None else "  --  "
        nrate = r.get('in_dist_null_rate', 0.0) * 100
        print(f"  {r['condition']:<42} {r['seed']:>10} {r['cost']:>5.3f} | "
              f"{r['pred_self_consume_food']:>+.3f} {psw_str:>7} "
              f"{r['in_dist_return']:>5.1f} {nrate:>5.1f}")
