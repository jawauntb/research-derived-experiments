#!/usr/bin/env python3
"""Paper 20B — Vector First-Order Self.

Composition stress test: Paper 15 vector ΔV + Paper 16b null anchoring +
Paper 19 current-replay autonomous probing.

Per-dimension self/world attribution under autonomous current-replay
null probing in a two-variable (E, D) homeostatic bandit.

Conditions:
  - vector_total_dV                            : no factorization baseline
  - vector_factorized_no_null                  : P16 gauge-symmetric failure
  - vector_passive_null                        : null inclusion w/o anchor
  - vector_scheduled_null_anchor               : positive anchor control
  - vector_matched_random_anchor               : same null count, random (Pass 2)
  - vector_learned_current_replay_probe        : HEADLINE (vector V_probe + dim_complete)
  - vector_learned_current_replay_probe_audit  : sensitivity
  - vector_oracle_uncertainty_probe            : upper bound on placement
  - vector_oracle_source                       : upper bound (semantic labels)
  - scalar_drive_selfworld                     : P15 scalar-collapse control
  - scalar_probe_vector_heads                  : vector heads w/ scalar probe
  - priority_weighted_probe                    : vector V_probe + weighted rule

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/vector_first_order_self/modal_vector_first_order_self_sweep.py
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

app = modal.App(name="research-derived-vector-first-order-self")

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
N_ACTIONS_NO_NULL = 2

# Per-dimension shock probabilities by role.
# E shock concentrated on food; D shock concentrated on poison.
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

EMA_ALPHA = 0.05
CURRENT_REPLAY_K = 64
AUDIT_FLOOR = 0.05

ALL_CONDITIONS = [
    "vector_total_dV",
    "vector_factorized_no_null",
    "vector_passive_null",
    "vector_scheduled_null_anchor",
    "vector_matched_random_anchor",
    "vector_learned_current_replay_probe",
    "vector_learned_current_replay_probe_audit",
    "vector_oracle_uncertainty_probe",
    "vector_oracle_source",
    "scalar_drive_selfworld",
    "scalar_probe_vector_heads",
    "priority_weighted_probe",
]

LEARNED_PROBE_CONDS = {
    "vector_learned_current_replay_probe",
    "vector_learned_current_replay_probe_audit",
    "scalar_probe_vector_heads",
    "priority_weighted_probe",
}

ANCHOR_CONDS = {
    "vector_scheduled_null_anchor",
    "vector_matched_random_anchor",
    "vector_learned_current_replay_probe",
    "vector_learned_current_replay_probe_audit",
    "vector_oracle_uncertainty_probe",
    "scalar_probe_vector_heads",
    "priority_weighted_probe",
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

    has_null = condition != "vector_factorized_no_null"
    n_actions = N_ACTIONS_WITH_NULL if has_null else N_ACTIONS_NO_NULL

    is_total_dV = (condition == "vector_total_dV")
    is_oracle_source = (condition == "vector_oracle_source")
    is_oracle_uncertainty = (condition == "vector_oracle_uncertainty_probe")
    is_scalar_drive = (condition == "scalar_drive_selfworld")
    is_scalar_probe = (condition == "scalar_probe_vector_heads")
    is_priority_weighted = (condition == "priority_weighted_probe")
    is_audit = (condition == "vector_learned_current_replay_probe_audit")

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
        return torch.cat(feats, dim=-1)  # 7

    def fourier_ED(E_t, D_t):
        return torch.cat([fourier_one(E_t), fourier_one(D_t)], dim=-1)  # 14

    def action_self_dE(action, c, l):
        if action == 1:
            return consume_self_dE(c, l) - ENERGY_DECAY
        else:
            return -ENERGY_DECAY

    def action_self_dD(action, c, l):
        if action == 1:
            return consume_self_dD(c, l) + DAMAGE_ACCRUAL
        else:
            return DAMAGE_ACCRUAL

    def sample_world_shock_E(c, l, dist_E, rng):
        if rng.rand() < dist_E[role_of(c, l)]:
            return SHOCK_E_MAG
        return 0.0

    def sample_world_shock_D(c, l, dist_D, rng):
        if rng.rand() < dist_D[role_of(c, l)]:
            return SHOCK_D_MAG
        return 0.0

    def bucket_key(c, l, E, D):
        e_bin = "E_low" if E < 0.5 else "E_high"
        d_bin = "D_low" if D < 0.5 else "D_high"
        return f"{role_of(c, l)}_{e_bin}_{d_bin}"

    BUCKETS = [f"{r}_{eb}_{db}"
                for r in ROLES
                for eb in ("E_low", "E_high")
                for db in ("D_low", "D_high")]

    # ===== model components =====
    state_ctx_dim = 14  # ffE + ffD
    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)

    if is_total_dV:
        # single total head, no factorization
        total_head = nn.Sequential(
            nn.Linear(EMBED_DIM + state_ctx_dim + n_actions, 32), nn.Tanh(),
            nn.Linear(32, 2),  # (dE_total, dD_total)
        ).to(device)
        self_head = None
        world_head = None
    elif is_scalar_drive:
        # scalar self/world drives
        self_head = nn.Sequential(
            nn.Linear(EMBED_DIM + state_ctx_dim + n_actions, 32), nn.Tanh(),
            nn.Linear(32, 1),
        ).to(device)
        world_head = nn.Sequential(
            nn.Linear(EMBED_DIM + state_ctx_dim, 32), nn.Tanh(),
            nn.Linear(32, 1),
        ).to(device)
        total_head = None
    else:
        # vector self/world
        self_head = nn.Sequential(
            nn.Linear(EMBED_DIM + state_ctx_dim + n_actions, 32), nn.Tanh(),
            nn.Linear(32, 2),
        ).to(device)
        world_head = nn.Sequential(
            nn.Linear(EMBED_DIM + state_ctx_dim, 32), nn.Tanh(),
            nn.Linear(32, 2),
        ).to(device)
        total_head = None

    # V_probe head
    if is_scalar_probe:
        v_probe_head = nn.Sequential(
            nn.Linear(EMBED_DIM + state_ctx_dim, 32), nn.Tanh(),
            nn.Linear(32, 1), nn.Softplus(),
        ).to(device)
        v_probe_dim = 1
    else:
        v_probe_head = nn.Sequential(
            nn.Linear(EMBED_DIM + state_ctx_dim, 32), nn.Tanh(),
            nn.Linear(32, 2), nn.Softplus(),
        ).to(device)
        v_probe_dim = 2

    params = list(encoder.parameters())
    if total_head is not None:
        params += list(total_head.parameters())
    if self_head is not None:
        params += list(self_head.parameters())
    if world_head is not None:
        params += list(world_head.parameters())
    params += list(v_probe_head.parameters())
    opt = torch.optim.Adam(params, lr=2e-3)

    # ===== current-replay state =====
    current_replay_buf = {b: deque(maxlen=CURRENT_REPLAY_K) for b in BUCKETS}
    bucket_count = {b: 0 for b in BUCKETS}
    bucket_null_density = {b: 0 for b in BUCKETS}

    def get_current_replay_errors():
        """Recompute current world_head errors per bucket and dimension."""
        errs = {b: (0.0, 0.0) for b in BUCKETS}
        for b in BUCKETS:
            if len(current_replay_buf[b]) == 0:
                continue
            obs_arr = np.stack([t[0] for t in current_replay_buf[b]])
            Es_arr = np.array([t[1] for t in current_replay_buf[b]],
                                dtype=np.float32)
            Ds_arr = np.array([t[2] for t in current_replay_buf[b]],
                                dtype=np.float32)
            tot_E_arr = np.array([t[3] for t in current_replay_buf[b]],
                                   dtype=np.float32)
            tot_D_arr = np.array([t[4] for t in current_replay_buf[b]],
                                   dtype=np.float32)
            with torch.no_grad():
                x = torch.from_numpy(obs_arr).to(device)
                z = encoder(x)
                e_t = torch.from_numpy(Es_arr.reshape(-1, 1)).to(device)
                d_t = torch.from_numpy(Ds_arr.reshape(-1, 1)).to(device)
                ff = fourier_ED(e_t, d_t)
                if world_head is None:
                    continue
                pred_w = world_head(torch.cat([z, ff], dim=-1))
                if pred_w.shape[-1] == 2:
                    pred_w_E = pred_w[:, 0].cpu().numpy()
                    pred_w_D = pred_w[:, 1].cpu().numpy()
                else:
                    # scalar world_head (scalar_drive condition)
                    pred_w_E = pred_w.squeeze(-1).cpu().numpy()
                    pred_w_D = np.zeros_like(pred_w_E)
                e_signed = (pred_w_E - tot_E_arr).mean()
                d_signed = (pred_w_D - tot_D_arr).mean()
            errs[b] = (float(abs(e_signed)), float(abs(d_signed)))
        return errs

    # ===== rollout state =====
    buffer = []
    SGD_EVERY = 30
    SGD_K = 4
    rng_online = np.random.RandomState(seed + 47)
    global_step = 0

    matched_target_rate = (float(target_null_rate)
                            if target_null_rate is not None else 0.20)
    matched_target_rate = max(0.02, min(0.6, matched_target_rate))

    w_E_train, w_D_train = PRIORITY_WEIGHTS["balanced"]

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

        tot_E_t = torch.from_numpy(tot_E_arr).to(device)
        tot_D_t = torch.from_numpy(tot_D_arr).to(device)
        self_E_t = torch.from_numpy(self_E_arr).to(device)
        self_D_t = torch.from_numpy(self_D_arr).to(device)
        world_E_t = torch.from_numpy(world_E_arr).to(device)
        world_D_t = torch.from_numpy(world_D_arr).to(device)

        null_mask = torch.from_numpy(actions_arr == 2)
        non_null_mask = ~null_mask

        if is_total_dV:
            pred_total = total_head(self_input)  # (B, 2)
            attr_loss = (F.mse_loss(pred_total[:, 0], tot_E_t)
                         + F.mse_loss(pred_total[:, 1], tot_D_t))
        elif is_scalar_drive:
            # Scalar drive baseline: scalar target = w_E*true_self_E - w_D*true_self_D
            # (under training weights, i.e., balanced)
            target_scalar_self = w_E_train * self_E_t - w_D_train * self_D_t
            target_scalar_world = w_E_train * world_E_t - w_D_train * world_D_t
            pred_self_s = self_head(self_input).squeeze(-1)
            pred_world_s = world_head(world_input).squeeze(-1)
            target_total_s = target_scalar_self + target_scalar_world
            if condition == "vector_factorized_no_null":
                attr_loss = F.mse_loss(pred_self_s + pred_world_s, target_total_s)
            else:
                null_loss = torch.tensor(0.0, device=device)
                non_null_loss = torch.tensor(0.0, device=device)
                if null_mask.any():
                    null_world_loss = F.mse_loss(
                        pred_world_s[null_mask], target_total_s[null_mask]
                    )
                    # For null, true scalar self = -decay*w_E - DAMAGE_ACCRUAL*w_D
                    null_self_target = (
                        -ENERGY_DECAY * w_E_train - DAMAGE_ACCRUAL * w_D_train
                    )
                    null_self_anchor = F.mse_loss(
                        pred_self_s[null_mask],
                        torch.full_like(pred_self_s[null_mask], null_self_target),
                    )
                    null_loss = null_world_loss + 0.5 * null_self_anchor
                if non_null_mask.any():
                    non_null_loss = F.mse_loss(
                        pred_self_s[non_null_mask] + pred_world_s[non_null_mask],
                        target_total_s[non_null_mask],
                    )
                attr_loss = null_loss + non_null_loss
        elif is_oracle_source:
            pred_self_v = self_head(self_input)  # (B, 2)
            pred_world_v = world_head(world_input)  # (B, 2)
            attr_loss = (
                F.mse_loss(pred_self_v[:, 0], self_E_t)
                + F.mse_loss(pred_self_v[:, 1], self_D_t)
                + F.mse_loss(pred_world_v[:, 0], world_E_t)
                + F.mse_loss(pred_world_v[:, 1], world_D_t)
            )
        else:
            # Vector factorized: pred_self + pred_world = total (per dim)
            pred_self_v = self_head(self_input)  # (B, 2)
            pred_world_v = world_head(world_input)  # (B, 2)
            if condition in ("vector_factorized_no_null", "vector_passive_null"):
                attr_loss = (
                    F.mse_loss(pred_self_v[:, 0] + pred_world_v[:, 0], tot_E_t)
                    + F.mse_loss(pred_self_v[:, 1] + pred_world_v[:, 1], tot_D_t)
                )
            elif condition in ANCHOR_CONDS:
                null_loss = torch.tensor(0.0, device=device)
                non_null_loss = torch.tensor(0.0, device=device)
                if null_mask.any():
                    null_world_E = F.mse_loss(
                        pred_world_v[:, 0][null_mask], tot_E_t[null_mask]
                    )
                    null_world_D = F.mse_loss(
                        pred_world_v[:, 1][null_mask], tot_D_t[null_mask]
                    )
                    null_self_E_anchor = F.mse_loss(
                        pred_self_v[:, 0][null_mask],
                        torch.full_like(pred_self_v[:, 0][null_mask],
                                          -ENERGY_DECAY),
                    )
                    null_self_D_anchor = F.mse_loss(
                        pred_self_v[:, 1][null_mask],
                        torch.full_like(pred_self_v[:, 1][null_mask],
                                          DAMAGE_ACCRUAL),
                    )
                    null_loss = (null_world_E + null_world_D
                                  + 0.5 * (null_self_E_anchor + null_self_D_anchor))
                if non_null_mask.any():
                    non_null_loss = (
                        F.mse_loss(
                            (pred_self_v[:, 0] + pred_world_v[:, 0])[non_null_mask],
                            tot_E_t[non_null_mask],
                        )
                        + F.mse_loss(
                            (pred_self_v[:, 1] + pred_world_v[:, 1])[non_null_mask],
                            tot_D_t[non_null_mask],
                        )
                    )
                attr_loss = null_loss + non_null_loss
            else:
                attr_loss = (
                    F.mse_loss(pred_self_v[:, 0] + pred_world_v[:, 0], tot_E_t)
                    + F.mse_loss(pred_self_v[:, 1] + pred_world_v[:, 1], tot_D_t)
                )

        # V_probe loss
        v_loss = torch.tensor(0.0, device=device)
        if condition in LEARNED_PROBE_CONDS and null_mask.any():
            fresh_errs = get_current_replay_errors()
            v_pred = v_probe_head(world_input[null_mask])  # (B_null, v_probe_dim)
            null_buckets = [mb[i]["bucket"] for i in
                             null_mask.nonzero(as_tuple=True)[0].cpu().numpy().tolist()]
            target_E = np.array([fresh_errs.get(b, (0.0, 0.0))[0]
                                  for b in null_buckets], dtype=np.float32)
            target_D = np.array([fresh_errs.get(b, (0.0, 0.0))[1]
                                  for b in null_buckets], dtype=np.float32)
            if v_probe_dim == 2:
                v_target = torch.stack([
                    torch.from_numpy(target_E).to(device),
                    torch.from_numpy(target_D).to(device),
                ], dim=-1)
                v_loss = F.mse_loss(v_pred, v_target)
            else:
                # scalar probe target = (err_E + err_D) / 2
                v_target = torch.from_numpy(
                    (target_E + target_D) / 2.0
                ).to(device)
                v_loss = F.mse_loss(v_pred.squeeze(-1), v_target)

        return attr_loss + 0.5 * v_loss

    # ===== rollout =====
    for episode in range(n_episodes):
        E = ENERGY_INIT
        D = DAMAGE_INIT
        steps = 0
        eps_explore = max(0.05, 0.30 - 0.25 * (episode / max(n_episodes, 1)))
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
                    if v_probe_dim == 2:
                        v_E = float(v_out[0].item()); v_D = float(v_out[1].item())
                    else:
                        v_E = float(v_out.item()); v_D = float(v_out.item())
                else:
                    v_E = 0.0; v_D = 0.0
                # World forward for oracle uncertainty rule
                if world_head is not None:
                    pred_w = world_head(w_inp_cur).squeeze(0)
                    if pred_w.dim() == 0:
                        w_pred_E = float(pred_w.item()); w_pred_D = 0.0
                    elif pred_w.numel() == 2:
                        w_pred_E = float(pred_w[0].item())
                        w_pred_D = float(pred_w[1].item())
                    else:
                        w_pred_E = float(pred_w.item()); w_pred_D = 0.0
                else:
                    w_pred_E = 0.0; w_pred_D = 0.0
                # Greedy planning over (skip, consume)
                if is_total_dV:
                    scores = []
                    for a in [0, 1]:
                        a_oh = torch.zeros(1, n_actions, device=device)
                        a_oh[0, a] = 1.0
                        inp = torch.cat([z_cur, ff_cur, a_oh], dim=-1)
                        pt = total_head(inp).squeeze(0)
                        scores.append(
                            float(w_E_train * pt[0].item()
                                  - w_D_train * pt[1].item())
                        )
                elif is_scalar_drive:
                    scores = []
                    for a in [0, 1]:
                        a_oh = torch.zeros(1, n_actions, device=device)
                        a_oh[0, a] = 1.0
                        inp = torch.cat([z_cur, ff_cur, a_oh], dim=-1)
                        scores.append(float(self_head(inp).item()))
                else:
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
            if condition == "vector_factorized_no_null":
                take_null = False
            elif condition in ("vector_passive_null", "vector_scheduled_null_anchor"):
                take_null = (rng_online.rand() < 0.33)
            elif condition == "vector_matched_random_anchor":
                take_null = (rng_online.rand() < matched_target_rate)
            elif condition == "vector_learned_current_replay_probe":
                take_null = (max(v_E, v_D) > cost)
            elif condition == "vector_learned_current_replay_probe_audit":
                learned_fire = (max(v_E, v_D) > cost)
                audit_fire = (rng_online.rand() < AUDIT_FLOOR)
                take_null = learned_fire or audit_fire
            elif condition == "vector_oracle_uncertainty_probe":
                true_w_E = (TRAINING_SHOCK_E[role_of(c_, l_)] * SHOCK_E_MAG)
                true_w_D = (TRAINING_SHOCK_D[role_of(c_, l_)] * SHOCK_D_MAG)
                err_E = abs(w_pred_E - true_w_E)
                err_D = abs(w_pred_D - true_w_D)
                take_null = (max(err_E, err_D) > cost)
            elif condition == "vector_oracle_source":
                take_null = (rng_online.rand() < 0.33)
            elif condition == "scalar_drive_selfworld":
                take_null = (rng_online.rand() < 0.33)
            elif condition == "scalar_probe_vector_heads":
                take_null = (v_E > cost)  # v_E is the scalar probe output here
            elif condition == "priority_weighted_probe":
                take_null = (w_E_train * v_E + w_D_train * v_D > cost)
            elif condition == "vector_total_dV":
                take_null = False  # no null actions in total baseline

            if take_null and has_null:
                action = 2
            else:
                if rng_online.rand() < eps_explore:
                    action = int(rng_online.choice([0, 1]))
                else:
                    action = greedy_action
                if not has_null and action == 2:
                    action = 0

            self_step_E = action_self_dE(action, c_, l_)
            self_step_D = action_self_dD(action, c_, l_)
            world_step_E = sample_world_shock_E(c_, l_, TRAINING_SHOCK_E,
                                                  rng_online)
            world_step_D = sample_world_shock_D(c_, l_, TRAINING_SHOCK_D,
                                                  rng_online)
            total_E = self_step_E + world_step_E
            total_D = self_step_D + world_step_D
            E_delta = total_E - (cost if action == 2 else 0.0)
            D_delta = total_D

            b_now = bucket_key(c_, l_, E, D)
            buffer.append(dict(
                obs=obs_raw, E=float(E), D=float(D), action=int(action),
                total_E=float(total_E), total_D=float(total_D),
                self_E=float(self_step_E), self_D=float(self_step_D),
                world_E=float(world_step_E), world_D=float(world_step_D),
                c=int(c_), l=int(l_), bucket=b_now,
            ))

            if action == 2:
                if condition in LEARNED_PROBE_CONDS or condition == "vector_oracle_uncertainty_probe":
                    current_replay_buf[b_now].append(
                        (obs_raw.copy(), float(E), float(D),
                         float(total_E), float(total_D))
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
                    loss = step_loss(mb)
                    opt.zero_grad(); loss.backward(); opt.step()

            E = max(0.0, min(1.0, E + E_delta))
            D = max(0.0, min(1.0, D + D_delta))
            steps += 1

    encoder.eval()
    if total_head is not None: total_head.eval()
    if self_head is not None: self_head.eval()
    if world_head is not None: world_head.eval()
    v_probe_head.eval()

    # ===== Component diagnostics =====
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
                self_E_preds = []
                self_D_preds = []
                for Ev in E_GRID:
                    for Dv in D_GRID:
                        e_t = torch.full((n_diag, 1), Ev,
                                          dtype=torch.float32, device=device)
                        d_t = torch.full((n_diag, 1), Dv,
                                          dtype=torch.float32, device=device)
                        ff = fourier_ED(e_t, d_t)
                        a_oh = torch.zeros(n_diag, n_actions, device=device)
                        a_oh[:, action_idx] = 1.0
                        inp = torch.cat([z, ff, a_oh], dim=-1)
                        if is_total_dV:
                            ps = total_head(inp)
                            self_E_preds.append(float(ps[:, 0].mean()))
                            self_D_preds.append(float(ps[:, 1].mean()))
                        elif is_scalar_drive:
                            ss = self_head(inp).squeeze(-1).cpu().numpy()
                            # decompose scalar back into E/D is impossible;
                            # report scalar drive value
                            self_E_preds.append(float(ss.mean()))
                            self_D_preds.append(0.0)
                        else:
                            ps = self_head(inp)
                            self_E_preds.append(float(ps[:, 0].mean()))
                            self_D_preds.append(float(ps[:, 1].mean()))
                results[f"self_E_action_{action_idx}"] = float(np.mean(self_E_preds))
                results[f"self_D_action_{action_idx}"] = float(np.mean(self_D_preds))
            world_E_preds = []
            world_D_preds = []
            v_E_preds = []
            v_D_preds = []
            for Ev in E_GRID:
                for Dv in D_GRID:
                    e_t = torch.full((n_diag, 1), Ev,
                                      dtype=torch.float32, device=device)
                    d_t = torch.full((n_diag, 1), Dv,
                                      dtype=torch.float32, device=device)
                    ff = fourier_ED(e_t, d_t)
                    inp = torch.cat([z, ff], dim=-1)
                    if world_head is not None:
                        pw = world_head(inp)
                        if pw.shape[-1] == 2:
                            world_E_preds.append(float(pw[:, 0].mean()))
                            world_D_preds.append(float(pw[:, 1].mean()))
                        else:
                            world_E_preds.append(float(pw.mean()))
                            world_D_preds.append(0.0)
                    vp = v_probe_head(inp)
                    if vp.shape[-1] == 2:
                        v_E_preds.append(float(vp[:, 0].mean()))
                        v_D_preds.append(float(vp[:, 1].mean()))
                    else:
                        v_E_preds.append(float(vp.squeeze(-1).mean()))
                        v_D_preds.append(0.0)
            results["world_E"] = float(np.mean(world_E_preds)) if world_E_preds else 0.0
            results["world_D"] = float(np.mean(world_D_preds)) if world_D_preds else 0.0
            results["v_probe_E"] = float(np.mean(v_E_preds))
            results["v_probe_D"] = float(np.mean(v_D_preds))
        results["true_self_consume_E"] = consume_self_dE(c, l) - ENERGY_DECAY
        results["true_self_consume_D"] = consume_self_dD(c, l) + DAMAGE_ACCRUAL
        results["true_self_skip_E"] = -ENERGY_DECAY
        results["true_self_skip_D"] = DAMAGE_ACCRUAL
        results["true_world_E_in_dist"] = true_world_expectation_E(c, l, TRAINING_SHOCK_E)
        results["true_world_D_in_dist"] = true_world_expectation_D(c, l, TRAINING_SHOCK_D)
        pred_by_role[role] = results

    # Per-bucket diagnostics
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
                    e_t = torch.full((32, 1), E_val,
                                      dtype=torch.float32, device=device)
                    d_t = torch.full((32, 1), D_val,
                                      dtype=torch.float32, device=device)
                    ff = fourier_ED(e_t, d_t)
                    inp = torch.cat([z, ff], dim=-1)
                    if v_probe_dim == 2:
                        vp = v_probe_head(inp)
                        v_E_mean = float(vp[:, 0].mean())
                        v_D_mean = float(vp[:, 1].mean())
                    else:
                        v_E_mean = float(v_probe_head(inp).squeeze(-1).mean())
                        v_D_mean = v_E_mean
                    if world_head is not None:
                        pw = world_head(inp)
                        if pw.shape[-1] == 2:
                            w_E_mean = float(pw[:, 0].mean())
                            w_D_mean = float(pw[:, 1].mean())
                        else:
                            w_E_mean = float(pw.squeeze(-1).mean()); w_D_mean = 0.0
                    else:
                        w_E_mean = 0.0; w_D_mean = 0.0
                bucket_diag[key] = dict(
                    v_probe_E=v_E_mean, v_probe_D=v_D_mean,
                    world_pred_E=w_E_mean, world_pred_D=w_D_mean,
                    true_world_E=true_w_E, true_world_D=true_w_D,
                    oracle_unc_E=abs(w_E_mean - true_w_E),
                    oracle_unc_D=abs(w_D_mean - true_w_D),
                    null_density=int(bucket_null_density.get(key, 0)),
                )

    # ===== Eval under three priority weights =====
    def plan_consume_or_skip(z_eval, E_now, D_now, w_E, w_D):
        with torch.no_grad():
            e_t = torch.full((z_eval.shape[0], 1), float(E_now),
                             dtype=torch.float32, device=device)
            d_t = torch.full((z_eval.shape[0], 1), float(D_now),
                             dtype=torch.float32, device=device)
            ff = fourier_ED(e_t, d_t)
            scores = np.zeros(2)
            for a in [0, 1]:
                a_oh = torch.zeros(z_eval.shape[0], n_actions, device=device)
                a_oh[:, a] = 1.0
                inp = torch.cat([z_eval, ff, a_oh], dim=-1)
                if is_total_dV:
                    pt = total_head(inp).squeeze(0)
                    scores[a] = w_E * pt[0].item() - w_D * pt[1].item()
                elif is_scalar_drive:
                    # Scalar drive can't reweight; uses trained scalar directly
                    scores[a] = self_head(inp).item()
                else:
                    ps = self_head(inp).squeeze(0)
                    scores[a] = w_E * ps[0].item() - w_D * ps[1].item()
            return int(np.argmax(scores))

    def oracle_action(c, l, w_E, w_D):
        consume_E = consume_self_dE(c, l) - ENERGY_DECAY
        consume_D = consume_self_dD(c, l) + DAMAGE_ACCRUAL
        skip_E = -ENERGY_DECAY
        skip_D = DAMAGE_ACCRUAL
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
            E = ENERGY_INIT
            D = DAMAGE_INIT
            steps = 0
            while E > 0 and D < 1.0 and steps < T_MAX:
                idx = rng_eval.randint(0, len(ITEMS))
                c_, l_ = ITEMS[idx]
                obs_ = encode_one(c_, l_, rng_eval)
                x = torch.from_numpy(obs_[None]).float().to(device)
                with torch.no_grad():
                    z = encoder(x)
                    e_t = torch.full((1, 1), float(E),
                                      dtype=torch.float32, device=device)
                    d_t = torch.full((1, 1), float(D),
                                      dtype=torch.float32, device=device)
                    ff = fourier_ED(e_t, d_t)
                    w_inp = torch.cat([z, ff], dim=-1)
                    if condition in LEARNED_PROBE_CONDS:
                        vp = v_probe_head(w_inp).squeeze(0)
                        if v_probe_dim == 2:
                            v_E = float(vp[0].item()); v_D = float(vp[1].item())
                        else:
                            v_E = float(vp.item()); v_D = v_E
                    else:
                        v_E = 0.0; v_D = 0.0
                    if world_head is not None:
                        pw_t = world_head(w_inp).squeeze(0)
                        if pw_t.numel() == 2:
                            w_pred_E = float(pw_t[0].item())
                            w_pred_D = float(pw_t[1].item())
                        else:
                            w_pred_E = float(pw_t.item()); w_pred_D = 0.0
                bk = bucket_key(c_, l_, E, D)
                state_visits_by_bucket[bk] += 1
                should_null = False
                if has_null:
                    if condition == "vector_learned_current_replay_probe":
                        should_null = (max(v_E, v_D) > cost)
                    elif condition == "vector_learned_current_replay_probe_audit":
                        learned = (max(v_E, v_D) > cost)
                        audit = (rng_eval.rand() < AUDIT_FLOOR)
                        should_null = learned or audit
                    elif condition == "vector_oracle_uncertainty_probe":
                        true_w_E_o = TRAINING_SHOCK_E[role_of(c_, l_)] * SHOCK_E_MAG
                        true_w_D_o = TRAINING_SHOCK_D[role_of(c_, l_)] * SHOCK_D_MAG
                        e_err = abs(w_pred_E - true_w_E_o)
                        d_err = abs(w_pred_D - true_w_D_o)
                        should_null = (max(e_err, d_err) > cost)
                    elif condition == "scalar_probe_vector_heads":
                        should_null = (v_E > cost)
                    elif condition == "priority_weighted_probe":
                        should_null = (w_E_train * v_E + w_D_train * v_D > cost)
                if should_null:
                    action = 2
                    null_actions += 1
                    probe_fires_by_bucket[bk] += 1
                else:
                    action = plan_consume_or_skip(z, E, D, w_E, w_D)
                total_actions += 1
                self_step_E = action_self_dE(action, c_, l_)
                self_step_D = action_self_dD(action, c_, l_)
                ws_E = sample_world_shock_E(c_, l_, shock_E_dist, rng_eval)
                ws_D = sample_world_shock_D(c_, l_, shock_D_dist, rng_eval)
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
        has_null=has_null, n_actions=n_actions,
        target_null_rate=target_null_rate,
        v_probe_dim=v_probe_dim,
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
        has_null=r["has_null"],
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
    n_episodes: int = 250,
    batch_size: int = 48,
    eval_episodes: int = 50,
    out: str = "artifacts/vector_first_order_self/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    primary_cost = COST_HEADLINE

    pass1_args = []
    pass1_conds = [c for c in ALL_CONDITIONS if c != "vector_matched_random_anchor"]
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
        if r["condition"] == "vector_learned_current_replay_probe":
            rates[int(r["seed"])] = (
                r["eval_by_priority"]["balanced"]["null_rate"]
            )
    print(f"  headline rates: {rates}")

    pass2_args = []
    for sd in seed_list:
        target_rate = rates.get(sd, 0.20)
        pass2_args.append(dict(
            seed=sd, condition="vector_matched_random_anchor", cost=primary_cost,
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
            training_shock_E=TRAINING_SHOCK_E,
            training_shock_D=TRAINING_SHOCK_D,
            shifted_shock_E=SHIFTED_SHOCK_E,
            shifted_shock_D=SHIFTED_SHOCK_D,
            shock_E_mag=SHOCK_E_MAG, shock_D_mag=SHOCK_D_MAG,
            energy_decay=ENERGY_DECAY, damage_accrual=DAMAGE_ACCRUAL,
            priority_weights=PRIORITY_WEIGHTS,
            current_replay_K=CURRENT_REPLAY_K,
            audit_floor=AUDIT_FLOOR,
            item_types={f"{c},{l}": info for (c, l), info in ITEM_TYPES.items()},
            realized_headline_rates={str(k): v for k, v in rates.items()},
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nsummary ({len(summary_rows)} cells):")
    print(f"{'cond':<45} {'seed':>10} | {'psE_f':>6} {'psD_p':>6} {'pwE_f':>6} {'pwD_p':>6} {'medB':>5} {'medH':>5} {'medI':>5} {'null%':>5}")
    print(f"  TRUE FOOD self_E=+0.96, world_E=+0.24")
    print(f"  TRUE POISON self_D=+0.53, world_D=+0.12")
    for r in summary_rows:
        medB = r.get('balanced_acc_medicine', 0.0)
        medH = r.get('hungry_acc_medicine', 0.0)
        medI = r.get('injured_acc_medicine', 0.0)
        print(f"  {r['condition']:<43} {r['seed']:>10} | "
              f"{r['pred_self_E_consume_food']:>+5.2f} "
              f"{r['pred_self_D_consume_poison']:>+5.2f} "
              f"{r['pred_world_E_food']:>+5.2f} "
              f"{r['pred_world_D_poison']:>+5.2f} "
              f"{medB:>5.2f} {medH:>5.2f} {medI:>5.2f} "
              f"{r['balanced_null_rate']*100:>4.1f}%")
