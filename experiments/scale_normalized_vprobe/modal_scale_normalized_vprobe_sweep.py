#!/usr/bin/env python3
"""Paper 21A — Scale-Normalized Probe Calibration.

Tests whether Paper 20B's scale-asymmetric V_probe calibration closes
when the target is variance-normalized and/or the decision threshold is
per-dimension. 2x2 factorial (raw/normalized target × global/per-dim
threshold) plus controls and oracle upper bounds.

Conditions:
  - raw_global_cost                   : P20B reproduction
  - norm_target_global_cost           : H1 (target normalization alone)
  - raw_target_perdim_cost            : H2 (threshold scaling alone)
  - norm_target_perdim_cost           : HEADLINE (both fixes)
  - norm_target_dim_balanced_floor    : sensitivity (audit floor)
  - matched_random_total              : matched volume, uniform random
  - matched_random_bucket_balanced    : matched, balanced across buckets
  - vector_scheduled_null_anchor      : positive control
  - vector_oracle_uncertainty_probe   : upper bound on placement
  - vector_oracle_source              : upper bound (semantic labels)

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/scale_normalized_vprobe/modal_scale_normalized_vprobe_sweep.py
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

app = modal.App(name="research-derived-scale-normalized-vprobe")

ITEM_TYPES = {
    (0, 0): {"role": "food",     "dE_consume": +1.0, "dD_consume":  0.0},
    (0, 1): {"role": "poison",   "dE_consume": -1.0, "dD_consume": +0.5},
    (1, 0): {"role": "medicine", "dE_consume": -0.3, "dD_consume": -0.4},
    (1, 1): {"role": "neutral",  "dE_consume":  0.0, "dD_consume":  0.0},
}
ITEMS = list(ITEM_TYPES.keys())
ROLES = ["food", "poison", "medicine", "neutral"]

EMBED_DIM = 32
OBS_NOISE = 0.15
T_MAX = 50
ENERGY_DECAY = 0.04
DAMAGE_ACCRUAL = 0.03
ENERGY_INIT = 0.5
DAMAGE_INIT = 0.0
SHOCK_E_MAG = 0.30
SHOCK_D_MAG = 0.20

N_ACTIONS_WITH_NULL = 3

TRAINING_SHOCK_E = {"food": 0.8, "poison": 0.1, "medicine": 0.1, "neutral": 0.1}
TRAINING_SHOCK_D = {"food": 0.1, "poison": 0.6, "medicine": 0.1, "neutral": 0.1}
SHIFTED_SHOCK_E = {"food": 0.1, "poison": 0.1, "medicine": 0.8, "neutral": 0.1}
SHIFTED_SHOCK_D = {"food": 0.1, "poison": 0.1, "medicine": 0.6, "neutral": 0.1}

PRIORITY_WEIGHTS = {
    "balanced": (1.0, 1.0),
    "hungry":   (1.5, 0.5),
    "injured":  (0.5, 1.5),
}

COST_HEADLINE = 0.025
CURRENT_REPLAY_K = 64
VAR_EMA_ALPHA = 0.05
VAR_EPS = 1e-2
AUDIT_FLOOR = 0.05

# Target ~12% null rate during warmup
WARMUP_PROBE_FLOOR = 0.33
WARMUP_EPISODES = 50

ALL_CONDITIONS = [
    "raw_global_cost",
    "norm_target_global_cost",
    "raw_target_perdim_cost",
    "norm_target_perdim_cost",
    "norm_target_dim_balanced_floor",
    "matched_random_total",
    "matched_random_bucket_balanced",
    "vector_scheduled_null_anchor",
    "vector_oracle_uncertainty_probe",
    "vector_oracle_source",
]

LEARNED_PROBE_CONDS = {
    "raw_global_cost",
    "norm_target_global_cost",
    "raw_target_perdim_cost",
    "norm_target_perdim_cost",
    "norm_target_dim_balanced_floor",
}

ANCHOR_CONDS = {
    "vector_scheduled_null_anchor",
    "matched_random_total",
    "matched_random_bucket_balanced",
    "raw_global_cost",
    "norm_target_global_cost",
    "raw_target_perdim_cost",
    "norm_target_perdim_cost",
    "norm_target_dim_balanced_floor",
    "vector_oracle_uncertainty_probe",
}


def role_of(c, l):
    return ITEM_TYPES[(c, l)]["role"]


def consume_self_dE(c, l):
    return ITEM_TYPES[(c, l)]["dE_consume"]


def consume_self_dD(c, l):
    return ITEM_TYPES[(c, l)]["dD_consume"]


def true_world_expectation_E(c, l, shock_dist_E):
    return shock_dist_E[role_of(c, l)] * SHOCK_E_MAG


def true_world_expectation_D(c, l, shock_dist_D):
    return shock_dist_D[role_of(c, l)] * SHOCK_D_MAG


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

    n_actions = N_ACTIONS_WITH_NULL

    use_normalized = condition in (
        "norm_target_global_cost",
        "norm_target_perdim_cost",
        "norm_target_dim_balanced_floor",
    )
    use_perdim_threshold = condition in (
        "raw_target_perdim_cost",
        "norm_target_perdim_cost",
        "norm_target_dim_balanced_floor",
    )
    use_audit_floor = condition == "norm_target_dim_balanced_floor"
    bucket_balanced_random = condition == "matched_random_bucket_balanced"

    def encode_one(c, l, rng):
        obs = np.zeros(16, dtype=np.float32)
        obs[c] = 1.0
        obs[8 + l] = 1.0
        obs = obs + rng.randn(16).astype(np.float32) * OBS_NOISE
        return obs[perm]

    def fourier_one(x_t):
        if x_t.dim() == 2:
            x_t = x_t.squeeze(-1)
        feats = [x_t.unsqueeze(-1)]
        for freq in [1.0, 2.0, 4.0]:
            feats.append(torch.sin(torch.pi * freq * x_t).unsqueeze(-1))
            feats.append(torch.cos(torch.pi * freq * x_t).unsqueeze(-1))
        return torch.cat(feats, dim=-1)

    def fourier_ED(E_t, D_t):
        return torch.cat([fourier_one(E_t), fourier_one(D_t)], dim=-1)

    def action_self_dE(action, c, l):
        if action == 1:
            return consume_self_dE(c, l) - ENERGY_DECAY
        return -ENERGY_DECAY

    def action_self_dD(action, c, l):
        if action == 1:
            return consume_self_dD(c, l) + DAMAGE_ACCRUAL
        return DAMAGE_ACCRUAL

    def sample_shock_E(c, l, dist, rng):
        return SHOCK_E_MAG if rng.rand() < dist[role_of(c, l)] else 0.0

    def sample_shock_D(c, l, dist, rng):
        return SHOCK_D_MAG if rng.rand() < dist[role_of(c, l)] else 0.0

    def bucket_key(c, l, E, D):
        e_bin = "E_low" if E < 0.5 else "E_high"
        d_bin = "D_low" if D < 0.5 else "D_high"
        return f"{role_of(c, l)}_{e_bin}_{d_bin}"

    BUCKETS = [f"{r}_{eb}_{db}" for r in ROLES
                for eb in ("E_low", "E_high")
                for db in ("D_low", "D_high")]

    state_ctx_dim = 14
    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)
    is_oracle_source = (condition == "vector_oracle_source")
    self_head = nn.Sequential(
        nn.Linear(EMBED_DIM + state_ctx_dim + n_actions, 32), nn.Tanh(),
        nn.Linear(32, 2),
    ).to(device)
    world_head = nn.Sequential(
        nn.Linear(EMBED_DIM + state_ctx_dim, 32), nn.Tanh(),
        nn.Linear(32, 2),
    ).to(device)
    v_probe_head = nn.Sequential(
        nn.Linear(EMBED_DIM + state_ctx_dim, 32), nn.Tanh(),
        nn.Linear(32, 2), nn.Softplus(),
    ).to(device)

    params = (list(encoder.parameters()) + list(self_head.parameters())
              + list(world_head.parameters())
              + list(v_probe_head.parameters()))
    opt = torch.optim.Adam(params, lr=2e-3)

    current_replay_buf = {b: deque(maxlen=CURRENT_REPLAY_K) for b in BUCKETS}
    bucket_count = {b: 0 for b in BUCKETS}
    bucket_null_density = {b: 0 for b in BUCKETS}

    # Per-dimension running variance (NOT per-bucket)
    var_state = {
        "mu_E": 0.0, "var_E": 0.05,
        "mu_D": 0.0, "var_D": 0.05,
        "n_updates": 0,
    }

    # Threshold calibration: collected during warmup
    warmup_v_probe_values = {"E": [], "D": []}
    cost_E_perdim = cost
    cost_D_perdim = cost
    tau_norm_global = 0.5
    tau_E_perdim = 0.5
    tau_D_perdim = 0.5
    thresholds_calibrated = False

    def get_current_replay_errors():
        errs = {b: (0.0, 0.0) for b in BUCKETS}
        for b in BUCKETS:
            if len(current_replay_buf[b]) == 0:
                continue
            obs_arr = np.stack([t[0] for t in current_replay_buf[b]])
            Es = np.array([t[1] for t in current_replay_buf[b]], dtype=np.float32)
            Ds = np.array([t[2] for t in current_replay_buf[b]], dtype=np.float32)
            tEs = np.array([t[3] for t in current_replay_buf[b]], dtype=np.float32)
            tDs = np.array([t[4] for t in current_replay_buf[b]], dtype=np.float32)
            with torch.no_grad():
                x = torch.from_numpy(obs_arr).to(device)
                z = encoder(x)
                e_t = torch.from_numpy(Es.reshape(-1, 1)).to(device)
                d_t = torch.from_numpy(Ds.reshape(-1, 1)).to(device)
                ff = fourier_ED(e_t, d_t)
                pw = world_head(torch.cat([z, ff], dim=-1))
                pw_E = pw[:, 0].cpu().numpy()
                pw_D = pw[:, 1].cpu().numpy()
                e_signed = float((pw_E - tEs).mean())
                d_signed = float((pw_D - tDs).mean())
            errs[b] = (abs(e_signed), abs(d_signed))
        return errs

    def target_for_bucket(b):
        raw_E, raw_D = get_current_replay_errors().get(b, (0.0, 0.0))
        if use_normalized:
            scale_E = (var_state["var_E"] + VAR_EPS) ** 0.5
            scale_D = (var_state["var_D"] + VAR_EPS) ** 0.5
            return (raw_E / scale_E, raw_D / scale_D)
        return (raw_E, raw_D)

    def step_loss(mb):
        actions_arr = np.array([bb["action"] for bb in mb], dtype=np.int64)
        Es_arr = np.array([bb["E"] for bb in mb], dtype=np.float32)
        Ds_arr = np.array([bb["D"] for bb in mb], dtype=np.float32)
        tot_E_arr = np.array([bb["total_E"] for bb in mb], dtype=np.float32)
        tot_D_arr = np.array([bb["total_D"] for bb in mb], dtype=np.float32)
        self_E_arr = np.array([bb["self_E"] for bb in mb], dtype=np.float32)
        self_D_arr = np.array([bb["self_D"] for bb in mb], dtype=np.float32)
        world_E_arr = np.array([bb["world_E"] for bb in mb], dtype=np.float32)
        world_D_arr = np.array([bb["world_D"] for bb in mb], dtype=np.float32)
        obss_arr = np.stack([bb["obs"] for bb in mb])

        x_mb = torch.from_numpy(obss_arr).to(device)
        z_mb = encoder(x_mb)
        e_t = torch.from_numpy(Es_arr.reshape(-1, 1)).to(device)
        d_t = torch.from_numpy(Ds_arr.reshape(-1, 1)).to(device)
        ff = fourier_ED(e_t, d_t)
        a_oh = torch.zeros(len(mb), n_actions, device=device)
        a_oh[np.arange(len(mb)), actions_arr] = 1.0
        self_input = torch.cat([z_mb, ff, a_oh], dim=-1)
        world_input = torch.cat([z_mb, ff], dim=-1)
        pred_self_v = self_head(self_input)
        pred_world_v = world_head(world_input)

        tot_E_t = torch.from_numpy(tot_E_arr).to(device)
        tot_D_t = torch.from_numpy(tot_D_arr).to(device)
        self_E_t = torch.from_numpy(self_E_arr).to(device)
        self_D_t = torch.from_numpy(self_D_arr).to(device)
        world_E_t = torch.from_numpy(world_E_arr).to(device)
        world_D_t = torch.from_numpy(world_D_arr).to(device)
        null_mask = torch.from_numpy(actions_arr == 2)
        non_null_mask = ~null_mask

        if is_oracle_source:
            attr_loss = (
                F.mse_loss(pred_self_v[:, 0], self_E_t)
                + F.mse_loss(pred_self_v[:, 1], self_D_t)
                + F.mse_loss(pred_world_v[:, 0], world_E_t)
                + F.mse_loss(pred_world_v[:, 1], world_D_t)
            )
        elif condition in ANCHOR_CONDS:
            null_loss = torch.tensor(0.0, device=device)
            non_null_loss = torch.tensor(0.0, device=device)
            if null_mask.any():
                null_world_E = F.mse_loss(pred_world_v[:, 0][null_mask], tot_E_t[null_mask])
                null_world_D = F.mse_loss(pred_world_v[:, 1][null_mask], tot_D_t[null_mask])
                null_self_E_anchor = F.mse_loss(
                    pred_self_v[:, 0][null_mask],
                    torch.full_like(pred_self_v[:, 0][null_mask], -ENERGY_DECAY),
                )
                null_self_D_anchor = F.mse_loss(
                    pred_self_v[:, 1][null_mask],
                    torch.full_like(pred_self_v[:, 1][null_mask], DAMAGE_ACCRUAL),
                )
                null_loss = (null_world_E + null_world_D
                              + 0.5 * (null_self_E_anchor + null_self_D_anchor))
            if non_null_mask.any():
                non_null_loss = (
                    F.mse_loss((pred_self_v[:, 0] + pred_world_v[:, 0])[non_null_mask],
                                tot_E_t[non_null_mask])
                    + F.mse_loss((pred_self_v[:, 1] + pred_world_v[:, 1])[non_null_mask],
                                  tot_D_t[non_null_mask])
                )
            attr_loss = null_loss + non_null_loss
        else:
            attr_loss = (
                F.mse_loss(pred_self_v[:, 0] + pred_world_v[:, 0], tot_E_t)
                + F.mse_loss(pred_self_v[:, 1] + pred_world_v[:, 1], tot_D_t)
            )

        v_loss = torch.tensor(0.0, device=device)
        if condition in LEARNED_PROBE_CONDS and null_mask.any():
            v_pred = v_probe_head(world_input[null_mask])
            null_buckets = [mb[i]["bucket"] for i in
                             null_mask.nonzero(as_tuple=True)[0].cpu().numpy().tolist()]
            targets = [target_for_bucket(b) for b in null_buckets]
            target_E = np.array([t[0] for t in targets], dtype=np.float32)
            target_D = np.array([t[1] for t in targets], dtype=np.float32)
            v_target = torch.stack([
                torch.from_numpy(target_E).to(device),
                torch.from_numpy(target_D).to(device),
            ], dim=-1)
            v_loss = F.mse_loss(v_pred, v_target)

        return attr_loss + 0.5 * v_loss

    buffer = []
    SGD_EVERY = 30
    SGD_K = 4
    rng_online = np.random.RandomState(seed + 47)
    global_step = 0

    matched_target_rate = (float(target_null_rate)
                            if target_null_rate is not None else 0.20)
    matched_target_rate = max(0.02, min(0.6, matched_target_rate))

    w_E_train, w_D_train = PRIORITY_WEIGHTS["balanced"]

    for episode in range(n_episodes):
        # Calibrate thresholds at end of warmup
        if episode == WARMUP_EPISODES and condition in LEARNED_PROBE_CONDS:
            if warmup_v_probe_values["E"] and warmup_v_probe_values["D"]:
                arr_E = np.array(warmup_v_probe_values["E"])
                arr_D = np.array(warmup_v_probe_values["D"])
                # Target ~15% above threshold
                if use_normalized:
                    tau_norm_global = float(np.percentile(
                        np.concatenate([arr_E, arr_D]), 85.0
                    ))
                    if use_perdim_threshold:
                        tau_E_perdim = float(np.percentile(arr_E, 85.0))
                        tau_D_perdim = float(np.percentile(arr_D, 85.0))
                else:
                    if use_perdim_threshold:
                        cost_E_perdim = float(np.percentile(arr_E, 85.0))
                        cost_D_perdim = float(np.percentile(arr_D, 85.0))
                thresholds_calibrated = True

        E = ENERGY_INIT
        D = DAMAGE_INIT
        steps = 0
        eps_explore = max(0.10, 0.50 - 0.40 * (episode / max(n_episodes, 1)))
        in_warmup = (episode < WARMUP_EPISODES)
        while E > 0 and D < 1.0 and steps < T_MAX:
            idx = rng_online.randint(0, len(ITEMS))
            c_, l_ = ITEMS[idx]
            obs_raw = encode_one(c_, l_, rng_online)
            x = torch.from_numpy(obs_raw[None]).float().to(device)

            with torch.no_grad():
                z_cur = encoder(x)
                e_t = torch.full((1, 1), float(E), dtype=torch.float32, device=device)
                d_t = torch.full((1, 1), float(D), dtype=torch.float32, device=device)
                ff_cur = fourier_ED(e_t, d_t)
                w_inp_cur = torch.cat([z_cur, ff_cur], dim=-1)
                if condition in LEARNED_PROBE_CONDS:
                    v_out = v_probe_head(w_inp_cur).squeeze(0)
                    v_E = float(v_out[0].item())
                    v_D = float(v_out[1].item())
                    if in_warmup:
                        warmup_v_probe_values["E"].append(v_E)
                        warmup_v_probe_values["D"].append(v_D)
                else:
                    v_E = 0.0; v_D = 0.0
                if not is_oracle_source:
                    pw_t = world_head(w_inp_cur).squeeze(0)
                    w_pred_E = float(pw_t[0].item())
                    w_pred_D = float(pw_t[1].item())
                else:
                    w_pred_E = 0.0; w_pred_D = 0.0
                scores = []
                for a in [0, 1]:
                    a_oh = torch.zeros(1, n_actions, device=device)
                    a_oh[0, a] = 1.0
                    inp = torch.cat([z_cur, ff_cur, a_oh], dim=-1)
                    ps = self_head(inp).squeeze(0)
                    scores.append(
                        float(w_E_train * ps[0].item()
                              - w_D_train * ps[1].item())
                    )
                greedy_action = 0 if scores[0] >= scores[1] else 1

            take_null = False
            if in_warmup and condition in LEARNED_PROBE_CONDS:
                take_null = (rng_online.rand() < WARMUP_PROBE_FLOOR)
            elif condition == "vector_scheduled_null_anchor":
                take_null = (rng_online.rand() < 0.33)
            elif condition == "matched_random_total":
                take_null = (rng_online.rand() < matched_target_rate)
            elif condition == "matched_random_bucket_balanced":
                # Bias toward under-sampled buckets
                b_now = bucket_key(c_, l_, E, D)
                cur_density = bucket_null_density[b_now]
                avg_density = sum(bucket_null_density.values()) / max(len(BUCKETS), 1)
                if cur_density < avg_density:
                    take_null = (rng_online.rand() < matched_target_rate * 1.5)
                else:
                    take_null = (rng_online.rand() < matched_target_rate * 0.5)
            elif condition == "vector_oracle_uncertainty_probe":
                true_w_E = TRAINING_SHOCK_E[role_of(c_, l_)] * SHOCK_E_MAG
                true_w_D = TRAINING_SHOCK_D[role_of(c_, l_)] * SHOCK_D_MAG
                err_E = abs(w_pred_E - true_w_E)
                err_D = abs(w_pred_D - true_w_D)
                take_null = (max(err_E, err_D) > cost)
            elif condition == "vector_oracle_source":
                take_null = (rng_online.rand() < 0.33)
            elif condition in LEARNED_PROBE_CONDS:
                # Apply factorial threshold rule based on condition
                if condition == "raw_global_cost":
                    take_null = (max(v_E, v_D) > cost)
                elif condition == "norm_target_global_cost":
                    take_null = (max(v_E, v_D) > tau_norm_global)
                elif condition == "raw_target_perdim_cost":
                    take_null = (v_E > cost_E_perdim) or (v_D > cost_D_perdim)
                elif condition == "norm_target_perdim_cost":
                    take_null = (v_E > tau_E_perdim) or (v_D > tau_D_perdim)
                elif condition == "norm_target_dim_balanced_floor":
                    learned = (v_E > tau_E_perdim) or (v_D > tau_D_perdim)
                    audit = (rng_online.rand() < AUDIT_FLOOR) if use_audit_floor else False
                    take_null = learned or audit

            if take_null:
                action = 2
            else:
                if rng_online.rand() < eps_explore:
                    action = int(rng_online.choice([0, 1]))
                else:
                    action = greedy_action

            self_step_E = action_self_dE(action, c_, l_)
            self_step_D = action_self_dD(action, c_, l_)
            ws_E = sample_shock_E(c_, l_, TRAINING_SHOCK_E, rng_online)
            ws_D = sample_shock_D(c_, l_, TRAINING_SHOCK_D, rng_online)
            total_E = self_step_E + ws_E
            total_D = self_step_D + ws_D
            E_delta = total_E - (cost if action == 2 else 0.0)

            b_now = bucket_key(c_, l_, E, D)
            buffer.append(dict(
                obs=obs_raw, E=float(E), D=float(D), action=int(action),
                total_E=float(total_E), total_D=float(total_D),
                self_E=float(self_step_E), self_D=float(self_step_D),
                world_E=float(ws_E), world_D=float(ws_D),
                c=int(c_), l=int(l_), bucket=b_now,
            ))

            if action == 2:
                # Update per-dim running variance from this null observation
                # Use the current model's residual
                signed_E = w_pred_E - total_E
                signed_D = w_pred_D - total_D
                alpha = VAR_EMA_ALPHA
                old_mu_E = var_state["mu_E"]
                old_mu_D = var_state["mu_D"]
                var_state["mu_E"] = (1 - alpha) * old_mu_E + alpha * signed_E
                var_state["var_E"] = ((1 - alpha) * var_state["var_E"]
                                        + alpha * (signed_E - old_mu_E) ** 2)
                var_state["mu_D"] = (1 - alpha) * old_mu_D + alpha * signed_D
                var_state["var_D"] = ((1 - alpha) * var_state["var_D"]
                                        + alpha * (signed_D - old_mu_D) ** 2)
                var_state["n_updates"] += 1
                if condition in LEARNED_PROBE_CONDS or condition == "vector_oracle_uncertainty_probe":
                    current_replay_buf[b_now].append(
                        (obs_raw.copy(), float(E), float(D),
                         float(total_E), float(total_D))
                    )
                bucket_count[b_now] += 1
                bucket_null_density[b_now] += 1

            global_step += 1

            if (len(buffer) >= 64 and global_step % SGD_EVERY == 0):
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
                    loss = step_loss(mb)
                    opt.zero_grad(); loss.backward(); opt.step()

            E = max(0.0, min(1.0, E + E_delta))
            D = max(0.0, min(1.0, D + total_D))
            steps += 1

    encoder.eval(); self_head.eval(); world_head.eval(); v_probe_head.eval()

    # ============ Diagnostics ============
    rng_diag = np.random.RandomState(seed + 333)
    n_diag = 128
    E_GRID = [0.1, 0.5, 0.9]
    D_GRID = [0.1, 0.5, 0.9]
    pred_by_role = {}
    for (c, l), info in ITEM_TYPES.items():
        role = info["role"]
        obs_arr = np.stack([encode_one(c, l, rng_diag) for _ in range(n_diag)])
        with torch.no_grad():
            z = encoder(torch.from_numpy(obs_arr).to(device))
            results = {}
            for action_idx in range(n_actions):
                preds_E = []; preds_D = []
                for Ev in E_GRID:
                    for Dv in D_GRID:
                        e_t = torch.full((n_diag, 1), Ev, dtype=torch.float32, device=device)
                        d_t = torch.full((n_diag, 1), Dv, dtype=torch.float32, device=device)
                        ff = fourier_ED(e_t, d_t)
                        a_oh = torch.zeros(n_diag, n_actions, device=device)
                        a_oh[:, action_idx] = 1.0
                        inp = torch.cat([z, ff, a_oh], dim=-1)
                        ps = self_head(inp)
                        preds_E.append(float(ps[:, 0].mean()))
                        preds_D.append(float(ps[:, 1].mean()))
                results[f"self_E_action_{action_idx}"] = float(np.mean(preds_E))
                results[f"self_D_action_{action_idx}"] = float(np.mean(preds_D))
            world_E_preds = []; world_D_preds = []
            v_E_preds = []; v_D_preds = []
            for Ev in E_GRID:
                for Dv in D_GRID:
                    e_t = torch.full((n_diag, 1), Ev, dtype=torch.float32, device=device)
                    d_t = torch.full((n_diag, 1), Dv, dtype=torch.float32, device=device)
                    ff = fourier_ED(e_t, d_t)
                    inp = torch.cat([z, ff], dim=-1)
                    pw = world_head(inp)
                    world_E_preds.append(float(pw[:, 0].mean()))
                    world_D_preds.append(float(pw[:, 1].mean()))
                    vp = v_probe_head(inp)
                    v_E_preds.append(float(vp[:, 0].mean()))
                    v_D_preds.append(float(vp[:, 1].mean()))
            results["world_E"] = float(np.mean(world_E_preds))
            results["world_D"] = float(np.mean(world_D_preds))
            results["v_probe_E"] = float(np.mean(v_E_preds))
            results["v_probe_D"] = float(np.mean(v_D_preds))
        results["true_self_consume_E"] = consume_self_dE(c, l) - ENERGY_DECAY
        results["true_self_consume_D"] = consume_self_dD(c, l) + DAMAGE_ACCRUAL
        results["true_world_E_in_dist"] = true_world_expectation_E(c, l, TRAINING_SHOCK_E)
        results["true_world_D_in_dist"] = true_world_expectation_D(c, l, TRAINING_SHOCK_D)
        pred_by_role[role] = results

    bucket_diag = {}
    for (c, l), _ in ITEM_TYPES.items():
        true_w_E = true_world_expectation_E(c, l, TRAINING_SHOCK_E)
        true_w_D = true_world_expectation_D(c, l, TRAINING_SHOCK_D)
        for E_bin_name, E_val in [("E_low", 0.25), ("E_high", 0.75)]:
            for D_bin_name, D_val in [("D_low", 0.25), ("D_high", 0.75)]:
                key = f"{role_of(c, l)}_{E_bin_name}_{D_bin_name}"
                obs_arr = np.stack([encode_one(c, l, rng_diag) for _ in range(32)])
                with torch.no_grad():
                    z = encoder(torch.from_numpy(obs_arr).to(device))
                    e_t = torch.full((32, 1), E_val, dtype=torch.float32, device=device)
                    d_t = torch.full((32, 1), D_val, dtype=torch.float32, device=device)
                    ff = fourier_ED(e_t, d_t)
                    inp = torch.cat([z, ff], dim=-1)
                    vp = v_probe_head(inp)
                    v_E_mean = float(vp[:, 0].mean())
                    v_D_mean = float(vp[:, 1].mean())
                    pw = world_head(inp)
                    w_E_mean = float(pw[:, 0].mean())
                    w_D_mean = float(pw[:, 1].mean())
                bucket_diag[key] = dict(
                    v_probe_E=v_E_mean, v_probe_D=v_D_mean,
                    world_pred_E=w_E_mean, world_pred_D=w_D_mean,
                    true_world_E=true_w_E, true_world_D=true_w_D,
                    oracle_unc_E=abs(w_E_mean - true_w_E),
                    oracle_unc_D=abs(w_D_mean - true_w_D),
                    null_density=int(bucket_null_density.get(key, 0)),
                )

    # ============ Eval under priorities ============
    def plan_consume_or_skip(z_eval, E_now, D_now, w_E, w_D):
        with torch.no_grad():
            e_t = torch.full((z_eval.shape[0], 1), float(E_now), dtype=torch.float32, device=device)
            d_t = torch.full((z_eval.shape[0], 1), float(D_now), dtype=torch.float32, device=device)
            ff = fourier_ED(e_t, d_t)
            scores = np.zeros(2)
            for a in [0, 1]:
                a_oh = torch.zeros(z_eval.shape[0], n_actions, device=device)
                a_oh[:, a] = 1.0
                inp = torch.cat([z_eval, ff, a_oh], dim=-1)
                ps = self_head(inp).squeeze(0)
                scores[a] = w_E * ps[0].item() - w_D * ps[1].item()
            return int(np.argmax(scores))

    def oracle_action(c, l, w_E, w_D):
        consume_E = consume_self_dE(c, l) - ENERGY_DECAY
        consume_D = consume_self_dD(c, l) + DAMAGE_ACCRUAL
        skip_E = -ENERGY_DECAY; skip_D = DAMAGE_ACCRUAL
        s_consume = w_E * consume_E - w_D * consume_D
        s_skip = w_E * skip_E - w_D * skip_D
        return 0 if s_skip >= s_consume else 1

    def eval_under(shock_E_dist, shock_D_dist, w_E, w_D, name):
        rng_eval = np.random.RandomState(seed + 9999 + hash(name) % 1000)
        returns = []
        per_role_acc = defaultdict(list)
        null_actions = 0
        total_actions = 0
        probe_fires_by_bucket = {b: 0 for b in BUCKETS}
        state_visits_by_bucket = {b: 0 for b in BUCKETS}
        for _ in range(eval_episodes):
            E = ENERGY_INIT; D = DAMAGE_INIT; steps = 0
            while E > 0 and D < 1.0 and steps < T_MAX:
                idx = rng_eval.randint(0, len(ITEMS))
                c_, l_ = ITEMS[idx]
                obs_ = encode_one(c_, l_, rng_eval)
                x = torch.from_numpy(obs_[None]).float().to(device)
                with torch.no_grad():
                    z = encoder(x)
                    e_t = torch.full((1, 1), float(E), dtype=torch.float32, device=device)
                    d_t = torch.full((1, 1), float(D), dtype=torch.float32, device=device)
                    ff = fourier_ED(e_t, d_t)
                    w_inp = torch.cat([z, ff], dim=-1)
                    vp = v_probe_head(w_inp).squeeze(0)
                    v_E = float(vp[0].item()); v_D = float(vp[1].item())
                    pw = world_head(w_inp).squeeze(0)
                    w_pred_E = float(pw[0].item()); w_pred_D = float(pw[1].item())
                bk = bucket_key(c_, l_, E, D)
                state_visits_by_bucket[bk] += 1
                should_null = False
                if condition == "raw_global_cost":
                    should_null = (max(v_E, v_D) > cost)
                elif condition == "norm_target_global_cost":
                    should_null = (max(v_E, v_D) > tau_norm_global)
                elif condition == "raw_target_perdim_cost":
                    should_null = (v_E > cost_E_perdim) or (v_D > cost_D_perdim)
                elif condition == "norm_target_perdim_cost":
                    should_null = (v_E > tau_E_perdim) or (v_D > tau_D_perdim)
                elif condition == "norm_target_dim_balanced_floor":
                    learned = (v_E > tau_E_perdim) or (v_D > tau_D_perdim)
                    audit = (rng_eval.rand() < AUDIT_FLOOR)
                    should_null = learned or audit
                elif condition == "vector_oracle_uncertainty_probe":
                    true_w_E = TRAINING_SHOCK_E[role_of(c_, l_)] * SHOCK_E_MAG
                    true_w_D = TRAINING_SHOCK_D[role_of(c_, l_)] * SHOCK_D_MAG
                    err_E = abs(w_pred_E - true_w_E)
                    err_D = abs(w_pred_D - true_w_D)
                    should_null = (max(err_E, err_D) > cost)
                if should_null:
                    action = 2
                    null_actions += 1
                    probe_fires_by_bucket[bk] += 1
                else:
                    action = plan_consume_or_skip(z, E, D, w_E, w_D)
                total_actions += 1
                self_step_E = action_self_dE(action, c_, l_)
                self_step_D = action_self_dD(action, c_, l_)
                ws_E = sample_shock_E(c_, l_, shock_E_dist, rng_eval)
                ws_D = sample_shock_D(c_, l_, shock_D_dist, rng_eval)
                if action == 2:
                    self_step_E = self_step_E - cost
                opt_action = oracle_action(c_, l_, w_E, w_D)
                if action != 2:
                    per_role_acc[role_of(c_, l_)].append(int(action == opt_action))
                E = max(0.0, min(1.0, E + self_step_E + ws_E))
                D = max(0.0, min(1.0, D + self_step_D + ws_D))
                steps += 1
            returns.append(float(steps))
        return dict(
            distribution=name,
            mean_return=float(np.mean(returns)),
            per_role_accuracy={k: float(np.mean(v)) if v else 0.0
                                for k, v in per_role_acc.items()},
            null_rate=(null_actions / max(total_actions, 1)),
            probe_fires_by_bucket=probe_fires_by_bucket,
            state_visits_by_bucket=state_visits_by_bucket,
        )

    eval_results = {}
    for priority_name, (w_E_eval, w_D_eval) in PRIORITY_WEIGHTS.items():
        eval_results[priority_name] = eval_under(
            TRAINING_SHOCK_E, TRAINING_SHOCK_D,
            w_E_eval, w_D_eval, f"{priority_name}_in_dist",
        )

    return dict(
        seed=seed, condition=condition, cost=cost,
        n_actions=n_actions,
        target_null_rate=target_null_rate,
        use_normalized=use_normalized, use_perdim_threshold=use_perdim_threshold,
        use_audit_floor=use_audit_floor,
        bucket_balanced_random=bucket_balanced_random,
        thresholds={
            "tau_norm_global": tau_norm_global,
            "tau_E_perdim": tau_E_perdim,
            "tau_D_perdim": tau_D_perdim,
            "cost_E_perdim": cost_E_perdim,
            "cost_D_perdim": cost_D_perdim,
        },
        var_state=var_state,
        eval_by_priority=eval_results,
        prediction_by_role=pred_by_role,
        bucket_diag=bucket_diag,
    )


def _flatten_to_row(r):
    bal = r["eval_by_priority"]["balanced"]
    hung = r["eval_by_priority"]["hungry"]
    inj = r["eval_by_priority"]["injured"]
    row = dict(
        seed=r["seed"], condition=r["condition"], cost=r["cost"],
        target_null_rate=r.get("target_null_rate"),
        balanced_return=bal["mean_return"],
        balanced_null_rate=bal["null_rate"],
        hungry_return=hung["mean_return"],
        hungry_null_rate=hung["null_rate"],
        injured_return=inj["mean_return"],
        injured_null_rate=inj["null_rate"],
    )
    for role in ROLES:
        for pname, eres in r["eval_by_priority"].items():
            row[f"{pname}_acc_{role}"] = eres["per_role_accuracy"].get(role, 0.0)
    for role, info in r["prediction_by_role"].items():
        row[f"pred_self_E_consume_{role}"] = info["self_E_action_1"]
        row[f"pred_self_D_consume_{role}"] = info["self_D_action_1"]
        row[f"pred_world_E_{role}"] = info["world_E"]
        row[f"pred_world_D_{role}"] = info["world_D"]
        row[f"v_probe_E_{role}"] = info["v_probe_E"]
        row[f"v_probe_D_{role}"] = info["v_probe_D"]
        row[f"true_self_E_consume_{role}"] = info["true_self_consume_E"]
        row[f"true_self_D_consume_{role}"] = info["true_self_consume_D"]
        row[f"true_world_E_{role}"] = info["true_world_E_in_dist"]
        row[f"true_world_D_{role}"] = info["true_world_D_in_dist"]
    return row


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    n_episodes: int = 500,
    batch_size: int = 48,
    eval_episodes: int = 50,
    out: str = "artifacts/scale_normalized_vprobe/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    primary_cost = COST_HEADLINE

    pass1_conds = [c for c in ALL_CONDITIONS
                    if c not in ("matched_random_total", "matched_random_bucket_balanced")]
    pass1_args = []
    for sd in seed_list:
        for cond in pass1_conds:
            pass1_args.append(dict(
                seed=sd, condition=cond, cost=primary_cost,
                n_episodes=n_episodes,
                batch_size=batch_size, eval_episodes=eval_episodes,
            ))
    print(f"PASS 1: running {len(pass1_args)} cells in parallel...")
    pass1_results = list(run_cell.map(pass1_args))

    rates = {}
    for r in pass1_results:
        if r["condition"] == "norm_target_perdim_cost":
            rates[int(r["seed"])] = r["eval_by_priority"]["balanced"]["null_rate"]
    print(f"  headline (norm_target_perdim_cost) rates: {rates}")

    pass2_args = []
    for sd in seed_list:
        target_rate = rates.get(sd, 0.20)
        for cond_name in ("matched_random_total", "matched_random_bucket_balanced"):
            pass2_args.append(dict(
                seed=sd, condition=cond_name, cost=primary_cost,
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
            n_episodes=n_episodes, batch_size=batch_size,
            eval_episodes=eval_episodes,
            warmup_episodes=WARMUP_EPISODES,
            warmup_probe_floor=WARMUP_PROBE_FLOOR,
            training_shock_E=TRAINING_SHOCK_E,
            training_shock_D=TRAINING_SHOCK_D,
            shock_E_mag=SHOCK_E_MAG, shock_D_mag=SHOCK_D_MAG,
            energy_decay=ENERGY_DECAY, damage_accrual=DAMAGE_ACCRUAL,
            priority_weights=PRIORITY_WEIGHTS,
            current_replay_K=CURRENT_REPLAY_K,
            var_ema_alpha=VAR_EMA_ALPHA,
            audit_floor=AUDIT_FLOOR,
            item_types={f"{c},{l}": info for (c, l), info in ITEM_TYPES.items()},
            realized_headline_rates={str(k): v for k, v in rates.items()},
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nsummary ({len(summary_rows)} cells):")
    print(f"{'cond':<42} {'seed':>10} | {'psE_f':>6} {'psD_p':>6} {'pwE_f':>6} {'pwD_p':>6} {'medH':>5} {'null%':>5}")
    print(f"  TRUE FOOD self_E=+0.96, POISON self_D=+0.53")
    for r in summary_rows:
        medH = r.get('hungry_acc_medicine', 0.0)
        print(f"  {r['condition']:<40} {r['seed']:>10} | "
              f"{r['pred_self_E_consume_food']:>+5.2f} "
              f"{r['pred_self_D_consume_poison']:>+5.2f} "
              f"{r['pred_world_E_food']:>+5.2f} "
              f"{r['pred_world_D_poison']:>+5.2f} "
              f"{medH:>5.2f} "
              f"{r['balanced_null_rate']*100:>4.1f}%")
