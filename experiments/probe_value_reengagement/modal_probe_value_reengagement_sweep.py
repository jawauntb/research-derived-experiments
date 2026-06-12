#!/usr/bin/env python3
"""Paper 23A — Probe Value and Re-Engagement.

Tests (i) principled probe-value oracle vs current-error oracle, and
(ii) two-timescale V_probe + non-null prediction-error boost for G7
re-engagement after regime shift.

Carries P22 environment (action-correlated hazard + mid-training regime
shift) with κ bumped to 0.60 to make architectural distinctions decisive.

Conditions (9):
  - p22_learned_current_replay            : P22 baseline (no re-engagement)
  - current_error_oracle                  : P22 broken oracle (proves it's bad)
  - true_probe_value_oracle_single_null   : corrected oracle (MAE reducibility)
  - true_probe_value_oracle_sequence      : corrected oracle + trigger bonus
  - two_timescale_vprobe                  : base + shift signal only
  - two_timescale_plus_prediction_error   : HEADLINE (shift + surprise)
  - matched_random_time_budget            : time-matched random
  - scheduled_null_anchor                 : positive anchor control
  - oracle_source                         : semantic upper bound

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/probe_value_reengagement/modal_probe_value_reengagement_sweep.py
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

app = modal.App(name="research-derived-probe-value-reengagement")

ITEM_TYPES = {
    (0, 0): {"role": "food",     "dE_consume": +1.0, "dD_consume":  0.0},
    (0, 1): {"role": "poison",   "dE_consume": -1.0, "dD_consume": +0.5},
    (1, 0): {"role": "medicine", "dE_consume": -0.3, "dD_consume": -0.4},
    (1, 1): {"role": "neutral",  "dE_consume":  0.0, "dD_consume":  0.0},
}
ITEMS = list(ITEM_TYPES.keys())
ROLES = ["food", "poison", "medicine", "neutral"]
ROLE_IDX = {r: i for i, r in enumerate(ROLES)}

EMBED_DIM = 32
OBS_NOISE = 0.15
T_MAX = 50
ENERGY_DECAY = 0.04
DAMAGE_ACCRUAL = 0.03
ENERGY_INIT = 0.5
DAMAGE_INIT = 0.0
SHOCK_E_MAG = 0.30
SHOCK_D_MAG = 0.20

HAZARD_GAMMA = 0.7
HAZARD_KAPPA = 0.60   # bumped from P22's 0.30 per pre-reg
HAZARD_AMP = 0.5
HISTORY_EMA_ALPHA = 0.30
HISTORY_DIM = 5

BASE_SHOCK_E = {"food": 0.5, "poison": 0.1, "medicine": 0.1, "neutral": 0.1}
BASE_SHOCK_D = {"food": 0.1, "poison": 0.6, "medicine": 0.1, "neutral": 0.1}

N_ACTIONS_WITH_NULL = 3

PRIORITY_WEIGHTS = {
    "balanced": (1.0, 1.0),
    "hungry":   (1.5, 0.5),
    "injured":  (0.5, 1.5),
}

COST_HEADLINE = 0.025
CURRENT_REPLAY_K = 64
VAR_EMA_ALPHA = 0.05
VAR_EPS = 1e-2
WARMUP_PROBE_FLOOR = 0.33
WARMUP_EPISODES = 50
REGIME_SHIFT_EPISODE = 250

# Two-timescale parameters
FAST_EMA_ALPHA = 0.25
SLOW_EMA_ALPHA = 0.05
SHIFT_MARGIN = 0.02
LAMBDA_SHIFT = 2.0
LAMBDA_SURPRISE = 1.0
NON_NULL_SURPRISE_ALPHA = 0.10

ALL_CONDITIONS = [
    "p22_learned_current_replay",
    "current_error_oracle",
    "true_probe_value_oracle_single_null",
    "true_probe_value_oracle_sequence",
    "two_timescale_vprobe",
    "two_timescale_plus_prediction_error",
    "matched_random_time_budget",
    "scheduled_null_anchor",
    "oracle_source",
]

LEARNED_PROBE_CONDS = {
    "p22_learned_current_replay",
    "two_timescale_vprobe",
    "two_timescale_plus_prediction_error",
}

ORACLE_PROBE_CONDS = {
    "current_error_oracle",
    "true_probe_value_oracle_single_null",
    "true_probe_value_oracle_sequence",
}


def role_of(c, l):
    return ITEM_TYPES[(c, l)]["role"]


def consume_self_dE(c, l):
    return ITEM_TYPES[(c, l)]["dE_consume"]


def consume_self_dD(c, l):
    return ITEM_TYPES[(c, l)]["dD_consume"]


@app.function(image=IMAGE, timeout=7200, cpu=4, memory=6144)
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

    is_oracle_source = (condition == "oracle_source")
    use_two_timescale = condition in (
        "two_timescale_vprobe", "two_timescale_plus_prediction_error"
    )
    use_prediction_error_boost = (
        condition == "two_timescale_plus_prediction_error"
    )

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

    def action_self_dE_fn(action, c, l):
        if action == 1:
            return consume_self_dE(c, l) - ENERGY_DECAY
        return -ENERGY_DECAY

    def action_self_dD_fn(action, c, l):
        if action == 1:
            return consume_self_dD(c, l) + DAMAGE_ACCRUAL
        return DAMAGE_ACCRUAL

    def get_regime_trigger(episode):
        return "food" if episode < REGIME_SHIFT_EPISODE else "medicine"

    def update_hazard(h, action, c, l, episode):
        trigger_role = get_regime_trigger(episode)
        triggered = (action == 1 and role_of(c, l) == trigger_role)
        new_h = HAZARD_GAMMA * h + HAZARD_KAPPA * float(triggered)
        return min(1.0, new_h)

    def shock_prob_E(role_name, h):
        return min(1.0, BASE_SHOCK_E[role_name] + HAZARD_AMP * h)

    def sample_shock_E(role_name, h, rng):
        return SHOCK_E_MAG if rng.rand() < shock_prob_E(role_name, h) else 0.0

    def sample_shock_D(role_name, rng):
        return SHOCK_D_MAG if rng.rand() < BASE_SHOCK_D[role_name] else 0.0

    def bucket_key(c, l, E, D):
        e_bin = "E_low" if E < 0.5 else "E_high"
        d_bin = "D_low" if D < 0.5 else "D_high"
        return f"{role_of(c, l)}_{e_bin}_{d_bin}"

    BUCKETS = [f"{r}_{eb}_{db}" for r in ROLES
                for eb in ("E_low", "E_high") for db in ("D_low", "D_high")]
    AFFECTED_BUCKETS = [b for b in BUCKETS if b.startswith(("food_", "medicine_"))]
    UNAFFECTED_BUCKETS = [b for b in BUCKETS if b.startswith(("poison_", "neutral_"))]

    state_ctx_dim = 14
    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)
    direct_self_head = nn.Sequential(
        nn.Linear(EMBED_DIM + state_ctx_dim + n_actions, 32), nn.Tanh(),
        nn.Linear(32, 2),
    ).to(device)
    mediated_world_head = nn.Sequential(
        nn.Linear(EMBED_DIM + state_ctx_dim + HISTORY_DIM, 32), nn.Tanh(),
        nn.Linear(32, 2),
    ).to(device)
    exogenous_world_head = nn.Sequential(
        nn.Linear(EMBED_DIM + state_ctx_dim, 32), nn.Tanh(),
        nn.Linear(32, 2),
    ).to(device)
    v_probe_head = nn.Sequential(
        nn.Linear(EMBED_DIM + state_ctx_dim + HISTORY_DIM, 32), nn.Tanh(),
        nn.Linear(32, 2), nn.Softplus(),
    ).to(device)

    params = (list(encoder.parameters())
              + list(direct_self_head.parameters())
              + list(mediated_world_head.parameters())
              + list(exogenous_world_head.parameters())
              + list(v_probe_head.parameters()))
    opt = torch.optim.Adam(params, lr=2e-3)

    current_replay_buf = {b: deque(maxlen=CURRENT_REPLAY_K) for b in BUCKETS}
    bucket_count = {b: 0 for b in BUCKETS}
    bucket_null_density_train = {b: 0 for b in BUCKETS}
    bucket_null_pre_shift = {b: 0 for b in BUCKETS}
    bucket_null_post_shift_early = {b: 0 for b in BUCKETS}  # eps 250-275
    bucket_null_post_shift_late = {b: 0 for b in BUCKETS}   # eps 276-500

    # Two-timescale state per bucket per dim
    fast_ema = {b: {"E": 0.0, "D": 0.0} for b in BUCKETS}
    slow_ema = {b: {"E": 0.0, "D": 0.0} for b in BUCKETS}
    non_null_surprise = {b: {"E": 0.0, "D": 0.0} for b in BUCKETS}

    var_state = {"mu_E": 0.0, "var_E": 0.05,
                  "mu_D": 0.0, "var_D": 0.05, "n_updates": 0}
    warmup_v_probe_values = {"E": [], "D": []}
    tau_E_perdim = 0.5; tau_D_perdim = 0.5

    def world_predict(z, ff, hist_t):
        m_inp = torch.cat([z, ff, hist_t], dim=-1)
        e_inp = torch.cat([z, ff], dim=-1)
        mw = mediated_world_head(m_inp)
        ew = exogenous_world_head(e_inp)
        return mw, ew

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
            hist_arr = np.stack([t[5] for t in current_replay_buf[b]]).astype(np.float32)
            with torch.no_grad():
                x = torch.from_numpy(obs_arr).to(device)
                z = encoder(x)
                e_t = torch.from_numpy(Es.reshape(-1, 1)).to(device)
                d_t = torch.from_numpy(Ds.reshape(-1, 1)).to(device)
                ff = fourier_ED(e_t, d_t)
                hist_t_t = torch.from_numpy(hist_arr).to(device)
                mw, ew = world_predict(z, ff, hist_t_t)
                pw_E = (mw[:, 0] + ew[:, 0]).cpu().numpy()
                pw_D = (mw[:, 1] + ew[:, 1]).cpu().numpy()
                e_signed = float((pw_E - tEs).mean())
                d_signed = float((pw_D - tDs).mean())
            errs[b] = (abs(e_signed), abs(d_signed))
        return errs

    def normalize_target(raw_E, raw_D):
        scale_E = (var_state["var_E"] + VAR_EPS) ** 0.5
        scale_D = (var_state["var_D"] + VAR_EPS) ** 0.5
        return (raw_E / scale_E, raw_D / scale_D)

    def step_loss(mb):
        actions_arr = np.array([bb["action"] for bb in mb], dtype=np.int64)
        Es_arr = np.array([bb["E"] for bb in mb], dtype=np.float32)
        Ds_arr = np.array([bb["D"] for bb in mb], dtype=np.float32)
        tot_E_arr = np.array([bb["total_E"] for bb in mb], dtype=np.float32)
        tot_D_arr = np.array([bb["total_D"] for bb in mb], dtype=np.float32)
        self_E_arr = np.array([bb["self_E"] for bb in mb], dtype=np.float32)
        self_D_arr = np.array([bb["self_D"] for bb in mb], dtype=np.float32)
        med_E_arr = np.array([bb["mediated_E"] for bb in mb], dtype=np.float32)
        med_D_arr = np.array([bb["mediated_D"] for bb in mb], dtype=np.float32)
        exo_E_arr = np.array([bb["exogenous_E"] for bb in mb], dtype=np.float32)
        exo_D_arr = np.array([bb["exogenous_D"] for bb in mb], dtype=np.float32)
        hist_arr = np.stack([bb["hist"] for bb in mb]).astype(np.float32)
        obss_arr = np.stack([bb["obs"] for bb in mb])

        x_mb = torch.from_numpy(obss_arr).to(device)
        z_mb = encoder(x_mb)
        e_t = torch.from_numpy(Es_arr.reshape(-1, 1)).to(device)
        d_t = torch.from_numpy(Ds_arr.reshape(-1, 1)).to(device)
        ff = fourier_ED(e_t, d_t)
        a_oh = torch.zeros(len(mb), n_actions, device=device)
        a_oh[np.arange(len(mb)), actions_arr] = 1.0
        hist_t = torch.from_numpy(hist_arr).to(device)
        self_input = torch.cat([z_mb, ff, a_oh], dim=-1)
        pred_self_v = direct_self_head(self_input)
        mw, ew = world_predict(z_mb, ff, hist_t)
        pred_world_E = mw[:, 0] + ew[:, 0]
        pred_world_D = mw[:, 1] + ew[:, 1]

        tot_E_t = torch.from_numpy(tot_E_arr).to(device)
        tot_D_t = torch.from_numpy(tot_D_arr).to(device)
        self_E_t = torch.from_numpy(self_E_arr).to(device)
        self_D_t = torch.from_numpy(self_D_arr).to(device)
        med_E_t = torch.from_numpy(med_E_arr).to(device)
        med_D_t = torch.from_numpy(med_D_arr).to(device)
        exo_E_t = torch.from_numpy(exo_E_arr).to(device)
        exo_D_t = torch.from_numpy(exo_D_arr).to(device)
        null_mask = torch.from_numpy(actions_arr == 2)
        non_null_mask = ~null_mask

        if is_oracle_source:
            attr_loss = (
                F.mse_loss(pred_self_v[:, 0], self_E_t)
                + F.mse_loss(pred_self_v[:, 1], self_D_t)
                + F.mse_loss(mw[:, 0], med_E_t)
                + F.mse_loss(mw[:, 1], med_D_t)
                + F.mse_loss(ew[:, 0], exo_E_t)
                + F.mse_loss(ew[:, 1], exo_D_t)
            )
        else:
            null_loss = torch.tensor(0.0, device=device)
            non_null_loss = torch.tensor(0.0, device=device)
            if null_mask.any():
                nw_E = F.mse_loss(pred_world_E[null_mask], tot_E_t[null_mask])
                nw_D = F.mse_loss(pred_world_D[null_mask], tot_D_t[null_mask])
                ns_E = F.mse_loss(pred_self_v[:, 0][null_mask],
                                   torch.full_like(pred_self_v[:, 0][null_mask],
                                                    -ENERGY_DECAY))
                ns_D = F.mse_loss(pred_self_v[:, 1][null_mask],
                                   torch.full_like(pred_self_v[:, 1][null_mask],
                                                    DAMAGE_ACCRUAL))
                null_loss = nw_E + nw_D + 0.5 * (ns_E + ns_D)
            if non_null_mask.any():
                non_null_loss = (
                    F.mse_loss((pred_self_v[:, 0] + pred_world_E)[non_null_mask],
                                tot_E_t[non_null_mask])
                    + F.mse_loss((pred_self_v[:, 1] + pred_world_D)[non_null_mask],
                                  tot_D_t[non_null_mask])
                )
            attr_loss = null_loss + non_null_loss

        v_loss = torch.tensor(0.0, device=device)
        if condition in LEARNED_PROBE_CONDS and null_mask.any():
            vp_inp = torch.cat([z_mb, ff, hist_t], dim=-1)
            v_pred = v_probe_head(vp_inp[null_mask])
            null_buckets = [mb[i]["bucket"] for i in
                             null_mask.nonzero(as_tuple=True)[0].cpu().numpy().tolist()]
            errs = get_current_replay_errors()
            targets_raw = [errs.get(b, (0.0, 0.0)) for b in null_buckets]
            target_E = np.array([normalize_target(t[0], t[1])[0]
                                  for t in targets_raw], dtype=np.float32)
            target_D = np.array([normalize_target(t[0], t[1])[1]
                                  for t in targets_raw], dtype=np.float32)
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

    learning_curve = []
    checkpoint_episodes = list(range(25, n_episodes + 1, 25))

    def per_dim_mae_snapshot():
        rng_diag = np.random.RandomState(seed + 99999)
        food_obs = np.stack([encode_one(0, 0, rng_diag) for _ in range(32)])
        poison_obs = np.stack([encode_one(0, 1, rng_diag) for _ in range(32)])
        with torch.no_grad():
            zf = encoder(torch.from_numpy(food_obs).to(device))
            zp = encoder(torch.from_numpy(poison_obs).to(device))
            e_t = torch.full((32, 1), 0.5, dtype=torch.float32, device=device)
            d_t = torch.full((32, 1), 0.25, dtype=torch.float32, device=device)
            ff = fourier_ED(e_t, d_t)
            a_oh = torch.zeros(32, n_actions, device=device); a_oh[:, 1] = 1.0
            food_self = direct_self_head(torch.cat([zf, ff, a_oh], dim=-1))
            poison_self = direct_self_head(torch.cat([zp, ff, a_oh], dim=-1))
            food_psE = float(food_self[:, 0].mean())
            poison_psD = float(poison_self[:, 1].mean())
        return abs(food_psE - 0.96) + abs(poison_psD - 0.53)

    for episode in range(n_episodes):
        if episode == WARMUP_EPISODES and condition in LEARNED_PROBE_CONDS:
            if warmup_v_probe_values["E"] and warmup_v_probe_values["D"]:
                arr_E = np.array(warmup_v_probe_values["E"])
                arr_D = np.array(warmup_v_probe_values["D"])
                tau_E_perdim = float(np.percentile(arr_E, 85.0))
                tau_D_perdim = float(np.percentile(arr_D, 85.0))

        E = ENERGY_INIT; D = DAMAGE_INIT; h = 0.0; steps = 0
        eps_explore = max(0.10, 0.50 - 0.40 * (episode / max(n_episodes, 1)))
        in_warmup = (episode < WARMUP_EPISODES)
        hist_ema = np.zeros(HISTORY_DIM, dtype=np.float32)
        recent_trigger = False  # for sequence oracle

        while E > 0 and D < 1.0 and steps < T_MAX:
            idx = rng_online.randint(0, len(ITEMS))
            c_, l_ = ITEMS[idx]
            obs_raw = encode_one(c_, l_, rng_online)
            x = torch.from_numpy(obs_raw[None]).float().to(device)
            hist_now = hist_ema.copy()
            hist_t_now = torch.from_numpy(hist_now[None]).to(device)

            with torch.no_grad():
                z_cur = encoder(x)
                e_t = torch.full((1, 1), float(E), dtype=torch.float32, device=device)
                d_t = torch.full((1, 1), float(D), dtype=torch.float32, device=device)
                ff_cur = fourier_ED(e_t, d_t)
                mw, ew = world_predict(z_cur, ff_cur, hist_t_now)
                w_pred_E = float((mw[:, 0] + ew[:, 0]).item())
                w_pred_D = float((mw[:, 1] + ew[:, 1]).item())
                vp_inp = torch.cat([z_cur, ff_cur, hist_t_now], dim=-1)
                v_out = v_probe_head(vp_inp).squeeze(0)
                v_E_base = float(v_out[0].item())
                v_D_base = float(v_out[1].item())
                if in_warmup and condition in LEARNED_PROBE_CONDS:
                    warmup_v_probe_values["E"].append(v_E_base)
                    warmup_v_probe_values["D"].append(v_D_base)
                scores = []
                for a in [0, 1]:
                    a_oh = torch.zeros(1, n_actions, device=device); a_oh[0, a] = 1.0
                    inp = torch.cat([z_cur, ff_cur, a_oh], dim=-1)
                    ps = direct_self_head(inp).squeeze(0)
                    scores.append(float(w_E_train * ps[0].item()
                                          - w_D_train * ps[1].item()))
                greedy_action = 0 if scores[0] >= scores[1] else 1

            # Compute two-timescale probe score
            b_now = bucket_key(c_, l_, E, D)
            shift_E = max(0.0, abs(fast_ema[b_now]["E"]) - abs(slow_ema[b_now]["E"]) - SHIFT_MARGIN)
            shift_D = max(0.0, abs(fast_ema[b_now]["D"]) - abs(slow_ema[b_now]["D"]) - SHIFT_MARGIN)
            surp_E = non_null_surprise[b_now]["E"]
            surp_D = non_null_surprise[b_now]["D"]
            if use_two_timescale:
                v_E = v_E_base + LAMBDA_SHIFT * shift_E
                v_D = v_D_base + LAMBDA_SHIFT * shift_D
                if use_prediction_error_boost:
                    v_E += LAMBDA_SURPRISE * surp_E
                    v_D += LAMBDA_SURPRISE * surp_D
            else:
                v_E = v_E_base; v_D = v_D_base

            take_null = False
            if in_warmup and condition in LEARNED_PROBE_CONDS:
                take_null = (rng_online.rand() < WARMUP_PROBE_FLOOR)
            elif condition == "scheduled_null_anchor":
                take_null = (rng_online.rand() < 0.33)
            elif condition == "matched_random_time_budget":
                take_null = (rng_online.rand() < matched_target_rate)
            elif condition == "oracle_source":
                take_null = (rng_online.rand() < 0.33)
            elif condition == "current_error_oracle":
                # P22's broken oracle
                true_w_E = (BASE_SHOCK_E[role_of(c_, l_)] + HAZARD_AMP * h) * SHOCK_E_MAG
                true_w_D = BASE_SHOCK_D[role_of(c_, l_)] * SHOCK_D_MAG
                err_E = abs(w_pred_E - true_w_E)
                err_D = abs(w_pred_D - true_w_D)
                take_null = (max(err_E, err_D) > cost)
            elif condition == "true_probe_value_oracle_single_null":
                # Probe value ∝ error² / (K + 1)
                true_w_E = (BASE_SHOCK_E[role_of(c_, l_)] + HAZARD_AMP * h) * SHOCK_E_MAG
                true_w_D = BASE_SHOCK_D[role_of(c_, l_)] * SHOCK_D_MAG
                err_E = abs(w_pred_E - true_w_E)
                err_D = abs(w_pred_D - true_w_D)
                K_b = bucket_null_density_train[b_now]
                pv_E = (err_E ** 2) / (K_b + 1)
                pv_D = (err_D ** 2) / (K_b + 1)
                take_null = (max(pv_E, pv_D) > cost * 0.01)  # rescaled
            elif condition == "true_probe_value_oracle_sequence":
                true_w_E = (BASE_SHOCK_E[role_of(c_, l_)] + HAZARD_AMP * h) * SHOCK_E_MAG
                true_w_D = BASE_SHOCK_D[role_of(c_, l_)] * SHOCK_D_MAG
                err_E = abs(w_pred_E - true_w_E)
                err_D = abs(w_pred_D - true_w_D)
                K_b = bucket_null_density_train[b_now]
                pv_E = (err_E ** 2) / (K_b + 1)
                pv_D = (err_D ** 2) / (K_b + 1)
                # Sequence bonus: recent trigger consume increases probe value
                seq_bonus = 0.005 if recent_trigger else 0.0
                take_null = ((max(pv_E, pv_D) + seq_bonus) > cost * 0.01)
            elif condition in LEARNED_PROBE_CONDS:
                take_null = (v_E > tau_E_perdim) or (v_D > tau_D_perdim)

            if take_null:
                action = 2
            else:
                if rng_online.rand() < eps_explore:
                    action = int(rng_online.choice([0, 1]))
                else:
                    action = greedy_action

            self_step_E = action_self_dE_fn(action, c_, l_)
            self_step_D = action_self_dD_fn(action, c_, l_)
            role_name = role_of(c_, l_)
            ws_E = sample_shock_E(role_name, h, rng_online)
            ws_D = sample_shock_D(role_name, rng_online)
            total_E = self_step_E + ws_E
            total_D = self_step_D + ws_D
            E_delta = total_E - (cost if action == 2 else 0.0)

            # Decompose world expectation for oracle_source
            mediated_E = HAZARD_AMP * h * SHOCK_E_MAG
            exogenous_E = BASE_SHOCK_E[role_name] * SHOCK_E_MAG
            mediated_D = 0.0
            exogenous_D = BASE_SHOCK_D[role_name] * SHOCK_D_MAG

            buffer.append(dict(
                obs=obs_raw, E=float(E), D=float(D), action=int(action),
                total_E=float(total_E), total_D=float(total_D),
                self_E=float(self_step_E), self_D=float(self_step_D),
                world_E=float(ws_E), world_D=float(ws_D),
                mediated_E=float(mediated_E), mediated_D=float(mediated_D),
                exogenous_E=float(exogenous_E), exogenous_D=float(exogenous_D),
                c=int(c_), l=int(l_), bucket=b_now,
                hist=hist_now.copy(),
                hazard=float(h), episode=int(episode),
            ))

            # Update two-timescale EMAs and surprise from observation
            signed_E = w_pred_E - total_E
            signed_D = w_pred_D - total_D
            fast_ema[b_now]["E"] = ((1 - FAST_EMA_ALPHA) * fast_ema[b_now]["E"]
                                      + FAST_EMA_ALPHA * signed_E)
            fast_ema[b_now]["D"] = ((1 - FAST_EMA_ALPHA) * fast_ema[b_now]["D"]
                                      + FAST_EMA_ALPHA * signed_D)
            slow_ema[b_now]["E"] = ((1 - SLOW_EMA_ALPHA) * slow_ema[b_now]["E"]
                                      + SLOW_EMA_ALPHA * signed_E)
            slow_ema[b_now]["D"] = ((1 - SLOW_EMA_ALPHA) * slow_ema[b_now]["D"]
                                      + SLOW_EMA_ALPHA * signed_D)
            # Update non-null surprise from non-null actions only
            if action != 2:
                non_null_surprise[b_now]["E"] = (
                    (1 - NON_NULL_SURPRISE_ALPHA) * non_null_surprise[b_now]["E"]
                    + NON_NULL_SURPRISE_ALPHA * abs(signed_E)
                )
                non_null_surprise[b_now]["D"] = (
                    (1 - NON_NULL_SURPRISE_ALPHA) * non_null_surprise[b_now]["D"]
                    + NON_NULL_SURPRISE_ALPHA * abs(signed_D)
                )

            if action == 2:
                alpha = VAR_EMA_ALPHA
                old_mu_E = var_state["mu_E"]; old_mu_D = var_state["mu_D"]
                var_state["mu_E"] = (1 - alpha) * old_mu_E + alpha * signed_E
                var_state["var_E"] = ((1 - alpha) * var_state["var_E"]
                                       + alpha * (signed_E - old_mu_E) ** 2)
                var_state["mu_D"] = (1 - alpha) * old_mu_D + alpha * signed_D
                var_state["var_D"] = ((1 - alpha) * var_state["var_D"]
                                       + alpha * (signed_D - old_mu_D) ** 2)
                var_state["n_updates"] += 1
                current_replay_buf[b_now].append(
                    (obs_raw.copy(), float(E), float(D),
                     float(total_E), float(total_D), hist_now.copy())
                )
                bucket_count[b_now] += 1
                bucket_null_density_train[b_now] += 1
                if episode < REGIME_SHIFT_EPISODE:
                    bucket_null_pre_shift[b_now] += 1
                elif episode < REGIME_SHIFT_EPISODE + 25:
                    bucket_null_post_shift_early[b_now] += 1
                else:
                    bucket_null_post_shift_late[b_now] += 1

            # Update history EMA + trigger memory
            new_hist = (1 - HISTORY_EMA_ALPHA) * hist_ema
            if action == 1:
                new_hist[ROLE_IDX[role_name]] += HISTORY_EMA_ALPHA
                trigger_role = get_regime_trigger(episode)
                recent_trigger = (role_name == trigger_role)
            elif action == 2:
                new_hist[4] += HISTORY_EMA_ALPHA
                recent_trigger = False
            else:
                recent_trigger = False
            hist_ema = new_hist

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
            h = update_hazard(h, action, c_, l_, episode)
            steps += 1

        if (episode + 1) in checkpoint_episodes:
            mae_now = per_dim_mae_snapshot()
            learning_curve.append({
                "episode": int(episode + 1),
                "total_food_E_poison_D_mae": float(mae_now),
                "cum_null_count": int(sum(bucket_null_density_train.values())),
            })

    encoder.eval(); direct_self_head.eval()
    mediated_world_head.eval(); exogenous_world_head.eval()
    v_probe_head.eval()

    # Diagnostics
    rng_diag = np.random.RandomState(seed + 333)
    n_diag = 128
    E_GRID = [0.1, 0.5, 0.9]; D_GRID = [0.1, 0.5, 0.9]
    pred_by_role = {}
    avg_hist = np.full(HISTORY_DIM, 0.2, dtype=np.float32)
    avg_hist_t = torch.from_numpy(avg_hist[None].repeat(n_diag, axis=0)).to(device)
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
                        a_oh = torch.zeros(n_diag, n_actions, device=device); a_oh[:, action_idx] = 1.0
                        inp = torch.cat([z, ff, a_oh], dim=-1)
                        ps = direct_self_head(inp)
                        preds_E.append(float(ps[:, 0].mean()))
                        preds_D.append(float(ps[:, 1].mean()))
                results[f"self_E_action_{action_idx}"] = float(np.mean(preds_E))
                results[f"self_D_action_{action_idx}"] = float(np.mean(preds_D))
            world_E_preds = []; world_D_preds = []; med_E_preds = []; med_D_preds = []
            exo_E_preds = []; exo_D_preds = []
            for Ev in E_GRID:
                for Dv in D_GRID:
                    e_t = torch.full((n_diag, 1), Ev, dtype=torch.float32, device=device)
                    d_t = torch.full((n_diag, 1), Dv, dtype=torch.float32, device=device)
                    ff = fourier_ED(e_t, d_t)
                    mw, ew = world_predict(z, ff, avg_hist_t)
                    world_E_preds.append(float((mw[:, 0] + ew[:, 0]).mean()))
                    world_D_preds.append(float((mw[:, 1] + ew[:, 1]).mean()))
                    med_E_preds.append(float(mw[:, 0].mean()))
                    med_D_preds.append(float(mw[:, 1].mean()))
                    exo_E_preds.append(float(ew[:, 0].mean()))
                    exo_D_preds.append(float(ew[:, 1].mean()))
            results["world_E"] = float(np.mean(world_E_preds))
            results["world_D"] = float(np.mean(world_D_preds))
            results["mediated_E"] = float(np.mean(med_E_preds))
            results["mediated_D"] = float(np.mean(med_D_preds))
            results["exogenous_E"] = float(np.mean(exo_E_preds))
            results["exogenous_D"] = float(np.mean(exo_D_preds))
        results["true_self_consume_E"] = consume_self_dE(c, l) - ENERGY_DECAY
        results["true_self_consume_D"] = consume_self_dD(c, l) + DAMAGE_ACCRUAL
        # True world expectations under final regime
        results["true_world_E_in_dist"] = BASE_SHOCK_E[role_of(c, l)] * SHOCK_E_MAG
        results["true_world_D_in_dist"] = BASE_SHOCK_D[role_of(c, l)] * SHOCK_D_MAG
        results["true_mediated_E"] = 0.0  # at neutral history h≈0
        results["true_exogenous_E"] = BASE_SHOCK_E[role_of(c, l)] * SHOCK_E_MAG
        pred_by_role[role] = results

    def plan_consume_or_skip(z_eval, E_now, D_now, w_E, w_D):
        with torch.no_grad():
            e_t = torch.full((z_eval.shape[0], 1), float(E_now), dtype=torch.float32, device=device)
            d_t = torch.full((z_eval.shape[0], 1), float(D_now), dtype=torch.float32, device=device)
            ff = fourier_ED(e_t, d_t)
            scores = np.zeros(2)
            for a in [0, 1]:
                a_oh = torch.zeros(z_eval.shape[0], n_actions, device=device); a_oh[:, a] = 1.0
                inp = torch.cat([z_eval, ff, a_oh], dim=-1)
                ps = direct_self_head(inp).squeeze(0)
                scores[a] = w_E * ps[0].item() - w_D * ps[1].item()
            return int(np.argmax(scores))

    def oracle_action(c, l, w_E, w_D):
        consume_E = consume_self_dE(c, l) - ENERGY_DECAY
        consume_D = consume_self_dD(c, l) + DAMAGE_ACCRUAL
        skip_E = -ENERGY_DECAY; skip_D = DAMAGE_ACCRUAL
        s_consume = w_E * consume_E - w_D * consume_D
        s_skip = w_E * skip_E - w_D * skip_D
        return 0 if s_skip >= s_consume else 1

    def eval_under(w_E, w_D, name, regime_episode):
        rng_eval = np.random.RandomState(seed + 9999 + hash(name) % 1000)
        returns = []; per_role_acc = defaultdict(list)
        for _ in range(eval_episodes):
            E = ENERGY_INIT; D = DAMAGE_INIT; h = 0.0; steps = 0
            while E > 0 and D < 1.0 and steps < T_MAX:
                idx = rng_eval.randint(0, len(ITEMS))
                c_, l_ = ITEMS[idx]
                obs_ = encode_one(c_, l_, rng_eval)
                x = torch.from_numpy(obs_[None]).float().to(device)
                with torch.no_grad():
                    z = encoder(x)
                action = plan_consume_or_skip(z, E, D, w_E, w_D)
                self_step_E = action_self_dE_fn(action, c_, l_)
                self_step_D = action_self_dD_fn(action, c_, l_)
                role_name = role_of(c_, l_)
                ws_E = sample_shock_E(role_name, h, rng_eval)
                ws_D = sample_shock_D(role_name, rng_eval)
                opt_action = oracle_action(c_, l_, w_E, w_D)
                if action != 2:
                    per_role_acc[role_name].append(int(action == opt_action))
                E = max(0.0, min(1.0, E + self_step_E + ws_E))
                D = max(0.0, min(1.0, D + self_step_D + ws_D))
                h = update_hazard(h, action, c_, l_, regime_episode)
                steps += 1
            returns.append(float(steps))
        return dict(
            mean_return=float(np.mean(returns)),
            per_role_accuracy={k: float(np.mean(v)) if v else 0.0
                                for k, v in per_role_acc.items()},
        )

    eval_results = {}
    for prio, (w_E, w_D) in PRIORITY_WEIGHTS.items():
        eval_results[prio] = eval_under(w_E, w_D, prio, n_episodes - 1)

    # Post-shift recovery metrics
    post_shift_curve = [lc for lc in learning_curve
                         if lc["episode"] >= REGIME_SHIFT_EPISODE]
    post_shift_auc = float(sum(lc["total_food_E_poison_D_mae"]
                                for lc in post_shift_curve))
    time_to_recover = None
    for lc in post_shift_curve:
        if lc["total_food_E_poison_D_mae"] <= 0.10:
            time_to_recover = lc["episode"]
            break

    pre_shift_nulls_in_affected = sum(bucket_null_pre_shift[b]
                                        for b in AFFECTED_BUCKETS)
    early_post_shift_nulls_in_affected = sum(bucket_null_post_shift_early[b]
                                               for b in AFFECTED_BUCKETS)
    late_post_shift_nulls_in_affected = sum(bucket_null_post_shift_late[b]
                                              for b in AFFECTED_BUCKETS)
    post_shift_nulls_unaffected = sum(bucket_null_post_shift_early[b]
                                        + bucket_null_post_shift_late[b]
                                        for b in UNAFFECTED_BUCKETS)
    post_shift_nulls_affected = (early_post_shift_nulls_in_affected
                                   + late_post_shift_nulls_in_affected)

    return dict(
        seed=seed, condition=condition, cost=cost,
        n_actions=n_actions, target_null_rate=target_null_rate,
        eval_by_priority=eval_results,
        prediction_by_role=pred_by_role,
        learning_curve=learning_curve,
        bucket_null_density_train=bucket_null_density_train,
        bucket_null_pre_shift=bucket_null_pre_shift,
        bucket_null_post_shift_early=bucket_null_post_shift_early,
        bucket_null_post_shift_late=bucket_null_post_shift_late,
        var_state=var_state,
        thresholds={"tau_E": tau_E_perdim, "tau_D": tau_D_perdim},
        post_shift_auc=post_shift_auc,
        time_to_recover=time_to_recover,
        pre_shift_nulls_in_affected=pre_shift_nulls_in_affected,
        early_post_shift_nulls_in_affected=early_post_shift_nulls_in_affected,
        late_post_shift_nulls_in_affected=late_post_shift_nulls_in_affected,
        post_shift_nulls_affected=post_shift_nulls_affected,
        post_shift_nulls_unaffected=post_shift_nulls_unaffected,
    )


def _flatten_to_row(r):
    bal = r["eval_by_priority"]["balanced"]
    row = dict(
        seed=r["seed"], condition=r["condition"], cost=r["cost"],
        target_null_rate=r.get("target_null_rate"),
        balanced_return=bal["mean_return"],
        post_shift_auc=r.get("post_shift_auc", 0.0),
        time_to_recover=r.get("time_to_recover"),
        pre_shift_nulls_in_affected=r.get("pre_shift_nulls_in_affected", 0),
        early_post_shift_nulls_in_affected=r.get("early_post_shift_nulls_in_affected", 0),
        late_post_shift_nulls_in_affected=r.get("late_post_shift_nulls_in_affected", 0),
        post_shift_nulls_affected=r.get("post_shift_nulls_affected", 0),
        post_shift_nulls_unaffected=r.get("post_shift_nulls_unaffected", 0),
    )
    for role in ROLES:
        for prio in ["balanced", "hungry", "injured"]:
            row[f"{prio}_acc_{role}"] = r["eval_by_priority"][prio]["per_role_accuracy"].get(role, 0.0)
    for role, info in r["prediction_by_role"].items():
        row[f"pred_self_E_consume_{role}"] = info["self_E_action_1"]
        row[f"pred_self_D_consume_{role}"] = info["self_D_action_1"]
        row[f"pred_world_E_{role}"] = info["world_E"]
        row[f"pred_world_D_{role}"] = info["world_D"]
        row[f"pred_mediated_E_{role}"] = info.get("mediated_E", 0.0)
        row[f"pred_exogenous_E_{role}"] = info.get("exogenous_E", 0.0)
        row[f"true_self_E_consume_{role}"] = info["true_self_consume_E"]
        row[f"true_self_D_consume_{role}"] = info["true_self_consume_D"]
        row[f"true_world_E_{role}"] = info["true_world_E_in_dist"]
        row[f"true_world_D_{role}"] = info["true_world_D_in_dist"]
    if r.get("learning_curve"):
        row["final_lc_mae"] = r["learning_curve"][-1]["total_food_E_poison_D_mae"]
        row["final_cum_nulls"] = r["learning_curve"][-1]["cum_null_count"]
    return row


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    n_episodes: int = 500,
    batch_size: int = 48,
    eval_episodes: int = 50,
    out: str = "artifacts/probe_value_reengagement/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    primary_cost = COST_HEADLINE

    pass1_conds = [c for c in ALL_CONDITIONS if c != "matched_random_time_budget"]
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
        if r["condition"] == "two_timescale_plus_prediction_error":
            total_nulls = sum(r["bucket_null_density_train"].values())
            rates[int(r["seed"])] = total_nulls / max(500 * 25, 1)
    print(f"  estimated headline rates: {rates}")

    pass2_args = []
    for sd in seed_list:
        target_rate = rates.get(sd, 0.20)
        pass2_args.append(dict(
            seed=sd, condition="matched_random_time_budget", cost=primary_cost,
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
            regime_shift_episode=REGIME_SHIFT_EPISODE,
            hazard_gamma=HAZARD_GAMMA, hazard_kappa=HAZARD_KAPPA,
            hazard_amp=HAZARD_AMP,
            history_dim=HISTORY_DIM,
            fast_ema_alpha=FAST_EMA_ALPHA, slow_ema_alpha=SLOW_EMA_ALPHA,
            shift_margin=SHIFT_MARGIN,
            lambda_shift=LAMBDA_SHIFT, lambda_surprise=LAMBDA_SURPRISE,
            non_null_surprise_alpha=NON_NULL_SURPRISE_ALPHA,
            base_shock_E=BASE_SHOCK_E, base_shock_D=BASE_SHOCK_D,
            shock_E_mag=SHOCK_E_MAG, shock_D_mag=SHOCK_D_MAG,
            energy_decay=ENERGY_DECAY, damage_accrual=DAMAGE_ACCRUAL,
            priority_weights=PRIORITY_WEIGHTS,
            item_types={f"{c},{l}": info for (c, l), info in ITEM_TYPES.items()},
            realized_headline_rates={str(k): v for k, v in rates.items()},
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nsummary ({len(summary_rows)} cells):")
    print(f"{'cond':<43} {'seed':>10} | {'psAUC':>6} {'tRec':>5} {'pre_a':>6} {'post_a':>6} {'post_u':>6}")
    for r in summary_rows:
        ttr = r.get('time_to_recover') or 0
        print(f"  {r['condition']:<41} {r['seed']:>10} | "
              f"{r['post_shift_auc']:>6.3f} "
              f"{ttr:>5} "
              f"{r['pre_shift_nulls_in_affected']:>6d} "
              f"{r['post_shift_nulls_affected']:>6d} "
              f"{r['post_shift_nulls_unaffected']:>6d}")
