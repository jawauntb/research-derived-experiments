#!/usr/bin/env python3
"""Paper 22 — When the World Responds.

Action-correlated world shocks with mid-training regime shift. First test of
self/world identifiability when world dynamics depend on agent's prior actions.

Conditions:
  - p21a_independent_baseline           : Replicate P21A under independent shocks
  - two_head_actionblind_world          : Expected failure under action-correlated
  - two_head_history_world              : Test if history-conditioning fixes it
  - three_head_direct_mediated_exogenous : Headline semantic decomposition
  - scheduled_null_anchor               : Positive anchor control
  - learned_scale_norm_current_replay   : HEADLINE autonomous probe
  - matched_random_time_budget          : Time-matched random null
  - matched_random_bucket_dim           : Bucket-balanced random
  - oracle_probe_value                  : Upper bound (probe-value oracle)
  - oracle_source                       : Upper bound (semantic labels)

Hazard: h(t+1) = γ·h(t) + κ·I[consume_trigger]
Regime A (eps 0-249): trigger = consume food
Regime B (eps 250-499): trigger = consume medicine

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/world_responds/modal_world_responds_sweep.py
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

app = modal.App(name="research-derived-world-responds")

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
HAZARD_KAPPA = 0.30
HAZARD_AMP = 0.5
HISTORY_EMA_ALPHA = 0.30
HISTORY_DIM = 5  # food, poison, medicine, neutral consume rates + null rate

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
AUDIT_FLOOR = 0.05
WARMUP_PROBE_FLOOR = 0.33
WARMUP_EPISODES = 50
REGIME_SHIFT_EPISODE = 250

ALL_CONDITIONS = [
    "p21a_independent_baseline",
    "two_head_actionblind_world",
    "two_head_history_world",
    "three_head_direct_mediated_exogenous",
    "scheduled_null_anchor",
    "learned_scale_norm_current_replay",
    "matched_random_time_budget",
    "matched_random_bucket_dim",
    "oracle_probe_value",
    "oracle_source",
]

LEARNED_PROBE_CONDS = {
    "learned_scale_norm_current_replay",
}

THREE_HEAD_CONDS = {
    "three_head_direct_mediated_exogenous",
    "oracle_source",
}

ACTION_BLIND_WORLD_CONDS = {
    "p21a_independent_baseline",
    "two_head_actionblind_world",
}


def role_of(c, l):
    return ITEM_TYPES[(c, l)]["role"]


def consume_self_dE(c, l):
    return ITEM_TYPES[(c, l)]["dE_consume"]


def consume_self_dD(c, l):
    return ITEM_TYPES[(c, l)]["dD_consume"]


@app.function(image=IMAGE, timeout=5400, cpu=4, memory=6144)
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

    # Architecture
    use_action_blind_world = condition in ACTION_BLIND_WORLD_CONDS
    use_three_head = condition in THREE_HEAD_CONDS
    use_independent_shocks = (condition == "p21a_independent_baseline")
    is_oracle_source = (condition == "oracle_source")
    use_history_in_world = (not use_action_blind_world) and (not use_three_head)
    use_history_in_three_head = use_three_head

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
        triggers = (action == 1 and role_of(c, l) == trigger_role)
        new_h = HAZARD_GAMMA * h + HAZARD_KAPPA * float(triggers)
        return min(1.0, new_h)

    def shock_prob_E(role_name, h):
        if use_independent_shocks:
            base = {"food": 0.8, "poison": 0.1, "medicine": 0.1, "neutral": 0.1}
            return min(1.0, base[role_name])
        return min(1.0, BASE_SHOCK_E[role_name] + HAZARD_AMP * h)

    def shock_prob_D(role_name):
        return BASE_SHOCK_D[role_name]

    def sample_shock_E(role_name, h, rng):
        return SHOCK_E_MAG if rng.rand() < shock_prob_E(role_name, h) else 0.0

    def sample_shock_D(role_name, rng):
        return SHOCK_D_MAG if rng.rand() < shock_prob_D(role_name) else 0.0

    def bucket_key(c, l, E, D):
        e_bin = "E_low" if E < 0.5 else "E_high"
        d_bin = "D_low" if D < 0.5 else "D_high"
        return f"{role_of(c, l)}_{e_bin}_{d_bin}"

    BUCKETS = [f"{r}_{eb}_{db}" for r in ROLES
                for eb in ("E_low", "E_high")
                for db in ("D_low", "D_high")]

    state_ctx_dim = 14
    hist_input_dim = HISTORY_DIM if (use_history_in_world or use_history_in_three_head) else 0

    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)
    self_head = nn.Sequential(
        nn.Linear(EMBED_DIM + state_ctx_dim + n_actions, 32), nn.Tanh(),
        nn.Linear(32, 2),
    ).to(device)

    if use_three_head:
        # direct_self handled by self_head above
        mediated_world_head = nn.Sequential(
            nn.Linear(EMBED_DIM + state_ctx_dim + HISTORY_DIM, 32), nn.Tanh(),
            nn.Linear(32, 2),
        ).to(device)
        exogenous_world_head = nn.Sequential(
            nn.Linear(EMBED_DIM + state_ctx_dim, 32), nn.Tanh(),
            nn.Linear(32, 2),
        ).to(device)
        world_head = None
    else:
        world_input_dim = EMBED_DIM + state_ctx_dim + hist_input_dim
        world_head = nn.Sequential(
            nn.Linear(world_input_dim, 32), nn.Tanh(),
            nn.Linear(32, 2),
        ).to(device)
        mediated_world_head = None
        exogenous_world_head = None

    v_probe_head = nn.Sequential(
        nn.Linear(EMBED_DIM + state_ctx_dim + hist_input_dim, 32), nn.Tanh(),
        nn.Linear(32, 2), nn.Softplus(),
    ).to(device)

    params = list(encoder.parameters()) + list(self_head.parameters())
    if world_head is not None:
        params += list(world_head.parameters())
    if mediated_world_head is not None:
        params += list(mediated_world_head.parameters())
    if exogenous_world_head is not None:
        params += list(exogenous_world_head.parameters())
    params += list(v_probe_head.parameters())
    opt = torch.optim.Adam(params, lr=2e-3)

    current_replay_buf = {b: deque(maxlen=CURRENT_REPLAY_K) for b in BUCKETS}
    bucket_count = {b: 0 for b in BUCKETS}
    bucket_null_density_train = {b: 0 for b in BUCKETS}
    bucket_null_density_pre_shift = {b: 0 for b in BUCKETS}
    bucket_null_density_post_shift = {b: 0 for b in BUCKETS}

    var_state = {"mu_E": 0.0, "var_E": 0.05,
                  "mu_D": 0.0, "var_D": 0.05, "n_updates": 0}
    warmup_v_probe_values = {"E": [], "D": []}
    tau_E_perdim = 0.5
    tau_D_perdim = 0.5

    def make_world_input(z, ff, hist_t=None):
        if hist_t is None or hist_input_dim == 0:
            return torch.cat([z, ff], dim=-1)
        return torch.cat([z, ff, hist_t], dim=-1)

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
            if hist_input_dim > 0 and len(current_replay_buf[b][0]) > 5:
                hist_arr = np.stack([t[5] for t in current_replay_buf[b]])
            else:
                hist_arr = None
            with torch.no_grad():
                x = torch.from_numpy(obs_arr).to(device)
                z = encoder(x)
                e_t = torch.from_numpy(Es.reshape(-1, 1)).to(device)
                d_t = torch.from_numpy(Ds.reshape(-1, 1)).to(device)
                ff = fourier_ED(e_t, d_t)
                hist_t_t = (torch.from_numpy(hist_arr.astype(np.float32)).to(device)
                            if hist_arr is not None else None)
                if use_three_head:
                    h_inp = make_world_input(z, ff, hist_t_t)
                    e_inp = make_world_input(z, ff, None)
                    mw = mediated_world_head(h_inp)
                    ew = exogenous_world_head(e_inp)
                    pw_E = (mw[:, 0] + ew[:, 0]).cpu().numpy()
                    pw_D = (mw[:, 1] + ew[:, 1]).cpu().numpy()
                else:
                    w_inp = make_world_input(z, ff, hist_t_t if use_history_in_world else None)
                    pw = world_head(w_inp)
                    pw_E = pw[:, 0].cpu().numpy()
                    pw_D = pw[:, 1].cpu().numpy()
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
        world_E_arr = np.array([bb["world_E"] for bb in mb], dtype=np.float32)
        world_D_arr = np.array([bb["world_D"] for bb in mb], dtype=np.float32)
        hist_arr = np.stack([bb["hist"] for bb in mb]).astype(np.float32)
        med_E_arr = np.array([bb.get("mediated_E", 0.0) for bb in mb], dtype=np.float32)
        med_D_arr = np.array([bb.get("mediated_D", 0.0) for bb in mb], dtype=np.float32)
        exo_E_arr = np.array([bb.get("exogenous_E", 0.0) for bb in mb], dtype=np.float32)
        exo_D_arr = np.array([bb.get("exogenous_D", 0.0) for bb in mb], dtype=np.float32)
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
        pred_self_v = self_head(self_input)

        tot_E_t = torch.from_numpy(tot_E_arr).to(device)
        tot_D_t = torch.from_numpy(tot_D_arr).to(device)
        self_E_t = torch.from_numpy(self_E_arr).to(device)
        self_D_t = torch.from_numpy(self_D_arr).to(device)
        world_E_t = torch.from_numpy(world_E_arr).to(device)
        world_D_t = torch.from_numpy(world_D_arr).to(device)
        med_E_t = torch.from_numpy(med_E_arr).to(device)
        med_D_t = torch.from_numpy(med_D_arr).to(device)
        exo_E_t = torch.from_numpy(exo_E_arr).to(device)
        exo_D_t = torch.from_numpy(exo_D_arr).to(device)
        null_mask = torch.from_numpy(actions_arr == 2)
        non_null_mask = ~null_mask

        # Three-head loss
        if use_three_head:
            h_inp = make_world_input(z_mb, ff, hist_t)
            e_inp = make_world_input(z_mb, ff, None)
            mw = mediated_world_head(h_inp)
            ew = exogenous_world_head(e_inp)
            pred_world_E = mw[:, 0] + ew[:, 0]
            pred_world_D = mw[:, 1] + ew[:, 1]
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
        else:
            w_inp = make_world_input(z_mb, ff,
                                      hist_t if use_history_in_world else None)
            pred_world_v = world_head(w_inp)
            null_loss = torch.tensor(0.0, device=device)
            non_null_loss = torch.tensor(0.0, device=device)
            if null_mask.any():
                nw_E = F.mse_loss(pred_world_v[:, 0][null_mask], tot_E_t[null_mask])
                nw_D = F.mse_loss(pred_world_v[:, 1][null_mask], tot_D_t[null_mask])
                ns_E = F.mse_loss(pred_self_v[:, 0][null_mask],
                                   torch.full_like(pred_self_v[:, 0][null_mask],
                                                    -ENERGY_DECAY))
                ns_D = F.mse_loss(pred_self_v[:, 1][null_mask],
                                   torch.full_like(pred_self_v[:, 1][null_mask],
                                                    DAMAGE_ACCRUAL))
                null_loss = nw_E + nw_D + 0.5 * (ns_E + ns_D)
            if non_null_mask.any():
                non_null_loss = (
                    F.mse_loss((pred_self_v[:, 0] + pred_world_v[:, 0])[non_null_mask],
                                tot_E_t[non_null_mask])
                    + F.mse_loss((pred_self_v[:, 1] + pred_world_v[:, 1])[non_null_mask],
                                  tot_D_t[non_null_mask])
                )
            attr_loss = null_loss + non_null_loss

        v_loss = torch.tensor(0.0, device=device)
        if condition in LEARNED_PROBE_CONDS and null_mask.any():
            vp_inp = make_world_input(z_mb, ff,
                                       hist_t if hist_input_dim > 0 else None)
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

    learning_curve = []  # per-checkpoint per-dim MAE
    checkpoint_episodes = list(range(50, n_episodes + 1, 50))

    def per_dim_mae_snapshot():
        """Quick MAE estimate using the predict-by-role diagnostic."""
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
            food_self = self_head(torch.cat([zf, ff, a_oh], dim=-1))
            poison_self = self_head(torch.cat([zp, ff, a_oh], dim=-1))
            food_psE = float(food_self[:, 0].mean())
            poison_psD = float(poison_self[:, 1].mean())
        food_E_mae = abs(food_psE - 0.96)
        poison_D_mae = abs(poison_psD - 0.53)
        return food_E_mae + poison_D_mae

    for episode in range(n_episodes):
        if episode == WARMUP_EPISODES and condition in LEARNED_PROBE_CONDS:
            if warmup_v_probe_values["E"] and warmup_v_probe_values["D"]:
                arr_E = np.array(warmup_v_probe_values["E"])
                arr_D = np.array(warmup_v_probe_values["D"])
                tau_E_perdim = float(np.percentile(arr_E, 85.0))
                tau_D_perdim = float(np.percentile(arr_D, 85.0))

        E = ENERGY_INIT
        D = DAMAGE_INIT
        h = 0.0
        steps = 0
        eps_explore = max(0.10, 0.50 - 0.40 * (episode / max(n_episodes, 1)))
        in_warmup = (episode < WARMUP_EPISODES)
        hist_ema = np.zeros(HISTORY_DIM, dtype=np.float32)

        post_shift_window = episode >= REGIME_SHIFT_EPISODE

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
                vp_inp = make_world_input(z_cur, ff_cur, hist_t_now if hist_input_dim > 0 else None)
                if condition in LEARNED_PROBE_CONDS:
                    v_out = v_probe_head(vp_inp).squeeze(0)
                    v_E = float(v_out[0].item()); v_D = float(v_out[1].item())
                    if in_warmup:
                        warmup_v_probe_values["E"].append(v_E)
                        warmup_v_probe_values["D"].append(v_D)
                else:
                    v_E = 0.0; v_D = 0.0
                if not is_oracle_source:
                    if use_three_head:
                        h_inp = make_world_input(z_cur, ff_cur, hist_t_now)
                        e_inp = make_world_input(z_cur, ff_cur, None)
                        mw = mediated_world_head(h_inp).squeeze(0)
                        ew = exogenous_world_head(e_inp).squeeze(0)
                        w_pred_E = float(mw[0].item() + ew[0].item())
                        w_pred_D = float(mw[1].item() + ew[1].item())
                    else:
                        w_inp = make_world_input(z_cur, ff_cur,
                                                  hist_t_now if use_history_in_world else None)
                        pw_t = world_head(w_inp).squeeze(0)
                        w_pred_E = float(pw_t[0].item())
                        w_pred_D = float(pw_t[1].item())
                else:
                    w_pred_E = 0.0; w_pred_D = 0.0
                scores = []
                for a in [0, 1]:
                    a_oh = torch.zeros(1, n_actions, device=device); a_oh[0, a] = 1.0
                    inp = torch.cat([z_cur, ff_cur, a_oh], dim=-1)
                    ps = self_head(inp).squeeze(0)
                    scores.append(float(w_E_train * ps[0].item()
                                          - w_D_train * ps[1].item()))
                greedy_action = 0 if scores[0] >= scores[1] else 1

            take_null = False
            if in_warmup and condition in LEARNED_PROBE_CONDS:
                take_null = (rng_online.rand() < WARMUP_PROBE_FLOOR)
            elif condition == "scheduled_null_anchor":
                take_null = (rng_online.rand() < 0.33)
            elif condition in ("two_head_actionblind_world", "two_head_history_world",
                                "three_head_direct_mediated_exogenous"):
                take_null = (rng_online.rand() < 0.33)
            elif condition == "p21a_independent_baseline":
                # P21A's learned scale-norm probe
                if not in_warmup:
                    take_null = (v_E > tau_E_perdim) or (v_D > tau_D_perdim)
                else:
                    take_null = (rng_online.rand() < WARMUP_PROBE_FLOOR)
            elif condition == "matched_random_time_budget":
                take_null = (rng_online.rand() < matched_target_rate)
            elif condition == "matched_random_bucket_dim":
                b_now = bucket_key(c_, l_, E, D)
                cur_density = bucket_null_density_train[b_now]
                avg_density = (sum(bucket_null_density_train.values())
                                / max(len(BUCKETS), 1))
                if cur_density < avg_density:
                    take_null = (rng_online.rand() < matched_target_rate * 1.5)
                else:
                    take_null = (rng_online.rand() < matched_target_rate * 0.5)
            elif condition == "oracle_probe_value":
                # Approximate value-of-info: use oracle attribution error for now
                # (full VoI requires intervention rollout per step; expensive)
                trigger_role = get_regime_trigger(episode)
                base_E = BASE_SHOCK_E[role_of(c_, l_)] if not use_independent_shocks else \
                          {"food": 0.8, "poison": 0.1, "medicine": 0.1, "neutral": 0.1}[role_of(c_, l_)]
                true_w_E = (base_E + HAZARD_AMP * h) * SHOCK_E_MAG \
                              if not use_independent_shocks else base_E * SHOCK_E_MAG
                true_w_D = BASE_SHOCK_D[role_of(c_, l_)] * SHOCK_D_MAG
                err_E = abs(w_pred_E - true_w_E)
                err_D = abs(w_pred_D - true_w_D)
                take_null = (max(err_E, err_D) > cost)
            elif condition == "oracle_source":
                take_null = (rng_online.rand() < 0.33)
            elif condition == "learned_scale_norm_current_replay":
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

            # Compute mediated and exogenous components (oracle truth for oracle_source)
            base_E_role = BASE_SHOCK_E[role_name] if not use_independent_shocks else \
                          {"food": 0.8, "poison": 0.1, "medicine": 0.1, "neutral": 0.1}[role_name]
            mediated_E = HAZARD_AMP * h * SHOCK_E_MAG if not use_independent_shocks else 0.0
            exogenous_E = base_E_role * SHOCK_E_MAG
            mediated_D = 0.0
            exogenous_D = BASE_SHOCK_D[role_name] * SHOCK_D_MAG

            b_now = bucket_key(c_, l_, E, D)
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

            if action == 2:
                signed_E = w_pred_E - total_E
                signed_D = w_pred_D - total_D
                alpha = VAR_EMA_ALPHA
                old_mu_E = var_state["mu_E"]; old_mu_D = var_state["mu_D"]
                var_state["mu_E"] = (1 - alpha) * old_mu_E + alpha * signed_E
                var_state["var_E"] = ((1 - alpha) * var_state["var_E"]
                                       + alpha * (signed_E - old_mu_E) ** 2)
                var_state["mu_D"] = (1 - alpha) * old_mu_D + alpha * signed_D
                var_state["var_D"] = ((1 - alpha) * var_state["var_D"]
                                       + alpha * (signed_D - old_mu_D) ** 2)
                var_state["n_updates"] += 1
                if hist_input_dim > 0:
                    current_replay_buf[b_now].append(
                        (obs_raw.copy(), float(E), float(D),
                         float(total_E), float(total_D), hist_now.copy())
                    )
                else:
                    current_replay_buf[b_now].append(
                        (obs_raw.copy(), float(E), float(D),
                         float(total_E), float(total_D))
                    )
                bucket_count[b_now] += 1
                bucket_null_density_train[b_now] += 1
                if post_shift_window:
                    bucket_null_density_post_shift[b_now] += 1
                else:
                    bucket_null_density_pre_shift[b_now] += 1

            # Update history EMA
            consume_role_idx = ROLE_IDX[role_name] if action == 1 else -1
            new_hist = (1 - HISTORY_EMA_ALPHA) * hist_ema
            if action == 1:
                new_hist[consume_role_idx] += HISTORY_EMA_ALPHA
            elif action == 2:
                new_hist[4] += HISTORY_EMA_ALPHA  # null rate channel
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

            # Update env state
            E = max(0.0, min(1.0, E + E_delta))
            D = max(0.0, min(1.0, D + total_D))
            h = update_hazard(h, action, c_, l_, episode)
            steps += 1

        # Checkpoint per dim MAE
        if (episode + 1) in checkpoint_episodes:
            mae_now = per_dim_mae_snapshot()
            learning_curve.append({
                "episode": int(episode + 1),
                "total_food_E_poison_D_mae": float(mae_now),
                "cum_null_count": int(sum(bucket_null_density_train.values())),
            })

    encoder.eval(); self_head.eval(); v_probe_head.eval()
    if world_head is not None: world_head.eval()
    if mediated_world_head is not None: mediated_world_head.eval()
    if exogenous_world_head is not None: exogenous_world_head.eval()

    # ============ Diagnostics ============
    rng_diag = np.random.RandomState(seed + 333)
    n_diag = 128
    E_GRID = [0.1, 0.5, 0.9]; D_GRID = [0.1, 0.5, 0.9]
    pred_by_role = {}
    avg_hist = np.full(HISTORY_DIM, 0.2, dtype=np.float32)  # neutral history for diagnostic
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
                    if use_three_head:
                        h_inp = make_world_input(z, ff, avg_hist_t)
                        e_inp = make_world_input(z, ff, None)
                        mw = mediated_world_head(h_inp)
                        ew = exogenous_world_head(e_inp)
                        world_E_preds.append(float((mw[:, 0] + ew[:, 0]).mean()))
                        world_D_preds.append(float((mw[:, 1] + ew[:, 1]).mean()))
                    else:
                        w_inp = make_world_input(z, ff,
                                                  avg_hist_t if use_history_in_world else None)
                        pw = world_head(w_inp)
                        world_E_preds.append(float(pw[:, 0].mean()))
                        world_D_preds.append(float(pw[:, 1].mean()))
                    vp_inp = make_world_input(z, ff,
                                               avg_hist_t if hist_input_dim > 0 else None)
                    vp = v_probe_head(vp_inp)
                    v_E_preds.append(float(vp[:, 0].mean()))
                    v_D_preds.append(float(vp[:, 1].mean()))
            results["world_E"] = float(np.mean(world_E_preds))
            results["world_D"] = float(np.mean(world_D_preds))
            results["v_probe_E"] = float(np.mean(v_E_preds))
            results["v_probe_D"] = float(np.mean(v_D_preds))
        results["true_self_consume_E"] = consume_self_dE(c, l) - ENERGY_DECAY
        results["true_self_consume_D"] = consume_self_dD(c, l) + DAMAGE_ACCRUAL
        # True world in mid-regime average (h=~0.15)
        base_E_role = BASE_SHOCK_E[role_of(c, l)] if not use_independent_shocks else \
                      {"food": 0.8, "poison": 0.1, "medicine": 0.1, "neutral": 0.1}[role_of(c, l)]
        results["true_world_E_in_dist"] = base_E_role * SHOCK_E_MAG
        results["true_world_D_in_dist"] = BASE_SHOCK_D[role_of(c, l)] * SHOCK_D_MAG
        pred_by_role[role] = results

    # Eval under priorities (carrying over P21A approach but with hazard state)
    def plan_consume_or_skip(z_eval, E_now, D_now, w_E, w_D):
        with torch.no_grad():
            e_t = torch.full((z_eval.shape[0], 1), float(E_now), dtype=torch.float32, device=device)
            d_t = torch.full((z_eval.shape[0], 1), float(D_now), dtype=torch.float32, device=device)
            ff = fourier_ED(e_t, d_t)
            scores = np.zeros(2)
            for a in [0, 1]:
                a_oh = torch.zeros(z_eval.shape[0], n_actions, device=device); a_oh[:, a] = 1.0
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

    # Eval under final regime (episode 499 = regime B)
    eval_results = {}
    for prio, (w_E, w_D) in PRIORITY_WEIGHTS.items():
        eval_results[prio] = eval_under(w_E, w_D, prio, n_episodes - 1)

    return dict(
        seed=seed, condition=condition, cost=cost,
        n_actions=n_actions, target_null_rate=target_null_rate,
        eval_by_priority=eval_results,
        prediction_by_role=pred_by_role,
        learning_curve=learning_curve,
        bucket_null_density_train=bucket_null_density_train,
        bucket_null_density_pre_shift=bucket_null_density_pre_shift,
        bucket_null_density_post_shift=bucket_null_density_post_shift,
        var_state=var_state,
        thresholds={"tau_E": tau_E_perdim, "tau_D": tau_D_perdim},
    )


def _flatten_to_row(r):
    bal = r["eval_by_priority"]["balanced"]
    row = dict(
        seed=r["seed"], condition=r["condition"], cost=r["cost"],
        target_null_rate=r.get("target_null_rate"),
        balanced_return=bal["mean_return"],
    )
    for role in ROLES:
        for prio in ["balanced", "hungry", "injured"]:
            row[f"{prio}_acc_{role}"] = r["eval_by_priority"][prio]["per_role_accuracy"].get(role, 0.0)
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
    out: str = "artifacts/world_responds/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    primary_cost = COST_HEADLINE

    pass1_conds = [c for c in ALL_CONDITIONS
                    if c not in ("matched_random_time_budget",
                                  "matched_random_bucket_dim")]
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
        if r["condition"] == "learned_scale_norm_current_replay":
            total_nulls = sum(r["bucket_null_density_train"].values())
            # rough rate estimate
            rates[int(r["seed"])] = total_nulls / (r.get("n_actions", 500) * 25)
    print(f"  estimated headline rates: {rates}")

    pass2_args = []
    for sd in seed_list:
        target_rate = rates.get(sd, 0.20)
        for cond_name in ("matched_random_time_budget", "matched_random_bucket_dim"):
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
            regime_shift_episode=REGIME_SHIFT_EPISODE,
            hazard_gamma=HAZARD_GAMMA, hazard_kappa=HAZARD_KAPPA,
            hazard_amp=HAZARD_AMP,
            history_dim=HISTORY_DIM,
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
    print(f"{'cond':<46} {'seed':>10} | {'psE_f':>6} {'psD_p':>6} {'pwE_f':>6} {'medH':>5} {'ret':>5} {'lc_mae':>7}")
    print(f"  TRUE FOOD self_E=+0.96, POISON self_D=+0.53")
    for r in summary_rows:
        medH = r.get('hungry_acc_medicine', 0.0)
        lc = r.get('final_lc_mae', 0.0)
        print(f"  {r['condition']:<44} {r['seed']:>10} | "
              f"{r['pred_self_E_consume_food']:>+5.2f} "
              f"{r['pred_self_D_consume_poison']:>+5.2f} "
              f"{r['pred_world_E_food']:>+5.2f} "
              f"{medH:>5.2f} "
              f"{r['balanced_return']:>5.1f} "
              f"{lc:>7.3f}")
