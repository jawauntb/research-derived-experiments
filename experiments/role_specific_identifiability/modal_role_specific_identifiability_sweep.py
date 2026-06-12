#!/usr/bin/env python3
"""Paper 25 — Role-Specific Mediated + Two-Sided Gauge + Fully-Learned Buckets.

Final identifiability stress test. Freeze P23B/P24 probing stack
(no new mechanism). Vary only three things:
  1. Role-specific mediated environment (per-role hazard amps)
  2. Two-sided gauge anchoring (mediated_low_zero + exogenous_low_anchor)
  3. Fully-learned buckets (K=16 k-means over (z, E, D, hist))

Conditions (9):
  - p24_default_role_invariant_no_contrast      : old env baseline
  - role_specific_no_contrast                   : NEW env baseline
  - role_specific_contrast_one_sided            : P24-style one-sided
  - role_specific_contrast_twosided_lambda1     : two-sided λ_exo=1
  - role_specific_contrast_twosided_lambda3     : HEADLINE
  - wrong_history_contrast_role_specific        : MUST fail now
  - shuffled_contrast_role_specific             : MUST fail
  - fully_learned_buckets_with_contrast         : learned abstractions
  - oracle_source_role_specific                 : semantic upper bound

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/role_specific_identifiability/modal_role_specific_identifiability_sweep.py
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

app = modal.App(name="research-derived-role-specific-identifiability")

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
HAZARD_KAPPA = 0.60

# NEW for Paper 25: role-specific hazard amplifiers
ROLE_HAZARD_AMP_E_ROLE_SPECIFIC = {
    "food": 0.50, "medicine": 0.20, "poison": 0.00, "neutral": 0.00,
}
ROLE_HAZARD_AMP_D_ROLE_SPECIFIC = {
    "food": 0.00, "medicine": 0.00, "poison": 0.33, "neutral": 0.00,
}
# Old role-invariant (for p24_default_role_invariant_no_contrast)
HAZARD_AMP_INVARIANT = 0.5

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
REGIME_SHIFT_1 = 250
REGIME_SHIFT_2 = 400

FAST_EMA_ALPHA = 0.25
SLOW_EMA_ALPHA = 0.05
SHIFT_MARGIN = 0.02
LAMBDA_SHIFT = 2.0
LAMBDA_SURPRISE = 1.0
NON_NULL_SURPRISE_ALPHA = 0.10

LEAKY_EFFORT_RHO = 0.93
REFRACTORY_LAMBDA = 1.5

# Contrast loss parameters
HIGH_H_THRESHOLD = 0.30
LOW_H_THRESHOLD = 0.10
HIGH_LOW_BUFFER_K = 16
MIN_PAIR_COUNT = 4
LAMBDA_CONTRAST = 1.0
PAIR_BONUS = 0.3

# Fully-learned buckets
N_FULLY_LEARNED_CLUSTERS = 16
KMEANS_ALPHA = 0.05

ALL_CONDITIONS = [
    "p24_default_role_invariant_no_contrast",
    "role_specific_no_contrast",
    "role_specific_contrast_one_sided",
    "role_specific_contrast_twosided_lambda1",
    "role_specific_contrast_twosided_lambda3",
    "wrong_history_contrast_role_specific",
    "shuffled_contrast_role_specific",
    "fully_learned_buckets_with_contrast",
    "oracle_source_role_specific",
]


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
    n_episodes: int = arg["n_episodes"]
    batch_size: int = arg["batch_size"]
    eval_episodes: int = arg["eval_episodes"]

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cpu")
    rng_env = np.random.RandomState(seed + 13)
    perm = rng_env.permutation(16)

    n_actions = N_ACTIONS_WITH_NULL

    is_oracle_source = (condition == "oracle_source_role_specific")
    is_role_invariant_env = (condition == "p24_default_role_invariant_no_contrast")
    apply_contrast = condition in {
        "role_specific_contrast_one_sided",
        "role_specific_contrast_twosided_lambda1",
        "role_specific_contrast_twosided_lambda3",
        "wrong_history_contrast_role_specific",
        "shuffled_contrast_role_specific",
        "fully_learned_buckets_with_contrast",
    }
    use_twosided_anchor = condition in {
        "role_specific_contrast_twosided_lambda1",
        "role_specific_contrast_twosided_lambda3",
        "wrong_history_contrast_role_specific",
        "shuffled_contrast_role_specific",
        "fully_learned_buckets_with_contrast",
    }
    lambda_exo = (
        1.0 if condition == "role_specific_contrast_twosided_lambda1"
        else 3.0
    )
    use_fully_learned = condition == "fully_learned_buckets_with_contrast"
    is_shuffled = condition == "shuffled_contrast_role_specific"
    is_wrong_history = condition == "wrong_history_contrast_role_specific"

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
        if episode < REGIME_SHIFT_1:
            return "food"
        elif episode < REGIME_SHIFT_2:
            return "medicine"
        return "food"

    def update_hazard(h, action, c, l, episode):
        trigger_role = get_regime_trigger(episode)
        triggered = (action == 1 and role_of(c, l) == trigger_role)
        new_h = HAZARD_GAMMA * h + HAZARD_KAPPA * float(triggered)
        return min(1.0, new_h)

    def shock_prob_E(role_name, h):
        if is_role_invariant_env:
            return min(1.0, BASE_SHOCK_E[role_name] + HAZARD_AMP_INVARIANT * h)
        return min(1.0,
                    BASE_SHOCK_E[role_name]
                    + ROLE_HAZARD_AMP_E_ROLE_SPECIFIC[role_name] * h)

    def shock_prob_D(role_name, h):
        if is_role_invariant_env:
            return BASE_SHOCK_D[role_name]
        return min(1.0,
                    BASE_SHOCK_D[role_name]
                    + ROLE_HAZARD_AMP_D_ROLE_SPECIFIC[role_name] * h)

    def sample_shock_E(role_name, h, rng):
        return SHOCK_E_MAG if rng.rand() < shock_prob_E(role_name, h) else 0.0

    def sample_shock_D(role_name, h, rng):
        return SHOCK_D_MAG if rng.rand() < shock_prob_D(role_name, h) else 0.0

    def oracle_bucket_key(c, l, E, D):
        e_bin = "E_low" if E < 0.5 else "E_high"
        d_bin = "D_low" if D < 0.5 else "D_high"
        return f"{role_of(c, l)}_{e_bin}_{d_bin}"

    # Fully-learned buckets: k-means over (z, E, D, hist)
    fully_learned_dim = EMBED_DIM + 1 + 1 + HISTORY_DIM  # 32+1+1+5=39
    cluster_centers = (
        np.random.RandomState(seed + 77).randn(
            N_FULLY_LEARNED_CLUSTERS, fully_learned_dim
        ).astype(np.float32) * 0.1
    )
    cluster_counts = np.zeros(N_FULLY_LEARNED_CLUSTERS, dtype=np.int64)

    def fully_learned_cluster_id(z_np, E, D, hist):
        feat = np.concatenate([z_np, [E], [D], hist], axis=-1).astype(np.float32)
        dists = np.sum((cluster_centers - feat[None]) ** 2, axis=-1)
        return int(np.argmin(dists))

    def fully_learned_bucket_key(z_np, E, D, hist):
        cid = fully_learned_cluster_id(z_np, E, D, hist)
        return f"L{cid}"

    def bucket_key(c, l, E, D, z_np=None, hist=None):
        if use_fully_learned and z_np is not None and hist is not None:
            return fully_learned_bucket_key(z_np, E, D, hist)
        return oracle_bucket_key(c, l, E, D)

    if use_fully_learned:
        BUCKETS = [f"L{i}" for i in range(N_FULLY_LEARNED_CLUSTERS)]
    else:
        BUCKETS = [f"{r}_{eb}_{db}" for r in ROLES
                    for eb in ("E_low", "E_high") for db in ("D_low", "D_high")]

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
    high_h_buf = {b: deque(maxlen=HIGH_LOW_BUFFER_K) for b in BUCKETS}
    low_h_buf = {b: deque(maxlen=HIGH_LOW_BUFFER_K) for b in BUCKETS}
    bucket_count = {b: 0 for b in BUCKETS}
    bucket_null_density = {b: 0 for b in BUCKETS}

    fast_ema = {b: {"E": 0.0, "D": 0.0} for b in BUCKETS}
    slow_ema = {b: {"E": 0.0, "D": 0.0} for b in BUCKETS}
    non_null_surprise = {b: {"E": 0.0, "D": 0.0} for b in BUCKETS}
    probe_effort = {b: {"E": 0.0, "D": 0.0} for b in BUCKETS}

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

    def compute_contrast_loss():
        if not apply_contrast:
            return (torch.tensor(0.0, device=device),
                    torch.tensor(0.0, device=device),
                    torch.tensor(0.0, device=device), 0)
        n_pairs = 0
        contrast_terms = []
        exo_anchor_terms = []
        med_low_zero_terms = []
        bucket_keys = list(BUCKETS)
        shuffled_keys = bucket_keys.copy()
        rng_shuffle = np.random.RandomState(seed + 88888)
        rng_shuffle.shuffle(shuffled_keys)
        for i, b in enumerate(bucket_keys):
            if len(high_h_buf[b]) < MIN_PAIR_COUNT:
                continue
            if is_shuffled:
                b_low = shuffled_keys[i]
            else:
                b_low = b
            if len(low_h_buf[b_low]) < MIN_PAIR_COUNT:
                continue
            # Wrong-history: use a different role's pairs in the role-specific env
            if is_wrong_history and not use_fully_learned:
                wrong_role_map = {"food": "medicine", "poison": "neutral",
                                    "medicine": "food", "neutral": "poison"}
                if "_" in b and not b.startswith("L"):
                    role_part = b.split("_")[0]
                    rest_parts = "_".join(b.split("_")[1:])
                    wrong_role = wrong_role_map.get(role_part, role_part)
                    b_target = f"{wrong_role}_{rest_parts}"
                    if (b_target not in high_h_buf
                            or len(high_h_buf[b_target]) < MIN_PAIR_COUNT
                            or len(low_h_buf[b_target]) < MIN_PAIR_COUNT):
                        continue
                    high_targets = high_h_buf[b_target]
                    low_targets = low_h_buf[b_target]
                else:
                    continue
            else:
                high_targets = high_h_buf[b]
                low_targets = low_h_buf[b_low]
            # Contrast target — use E component
            high_target_E = float(np.mean([t[3] for t in high_targets]))
            low_target_E = float(np.mean([t[3] for t in low_targets]))
            contrast_target_E_val = high_target_E - low_target_E
            high_target_D = float(np.mean([t[4] for t in high_targets]))
            low_target_D = float(np.mean([t[4] for t in low_targets]))
            contrast_target_D_val = high_target_D - low_target_D

            obs_high = np.stack([t[0] for t in high_h_buf[b]])
            E_high = np.array([t[1] for t in high_h_buf[b]], dtype=np.float32)
            D_high = np.array([t[2] for t in high_h_buf[b]], dtype=np.float32)
            hist_high = np.stack([t[5] for t in high_h_buf[b]]).astype(np.float32)
            obs_low = np.stack([t[0] for t in low_h_buf[b_low]])
            E_low_arr = np.array([t[1] for t in low_h_buf[b_low]], dtype=np.float32)
            D_low_arr = np.array([t[2] for t in low_h_buf[b_low]], dtype=np.float32)
            hist_low = np.stack([t[5] for t in low_h_buf[b_low]]).astype(np.float32)

            x_h_g = torch.from_numpy(obs_high).to(device)
            x_l_g = torch.from_numpy(obs_low).to(device)
            z_h_g = encoder(x_h_g); z_l_g = encoder(x_l_g)
            Eh_t = torch.from_numpy(E_high.reshape(-1, 1)).to(device)
            Dh_t = torch.from_numpy(D_high.reshape(-1, 1)).to(device)
            El_t = torch.from_numpy(E_low_arr.reshape(-1, 1)).to(device)
            Dl_t = torch.from_numpy(D_low_arr.reshape(-1, 1)).to(device)
            ff_h = fourier_ED(Eh_t, Dh_t)
            ff_l = fourier_ED(El_t, Dl_t)
            hist_h_t = torch.from_numpy(hist_high).to(device)
            hist_l_t = torch.from_numpy(hist_low).to(device)

            mw_high = mediated_world_head(
                torch.cat([z_h_g, ff_h, hist_h_t], dim=-1)
            )
            mw_low = mediated_world_head(
                torch.cat([z_l_g, ff_l, hist_l_t], dim=-1)
            )
            ew_low = exogenous_world_head(
                torch.cat([z_l_g, ff_l], dim=-1)
            )

            # E-dim contrast loss
            pred_contrast_E = mw_high[:, 0].mean() - mw_low[:, 0].mean()
            target_E_t = torch.tensor(contrast_target_E_val,
                                       dtype=torch.float32, device=device)
            contrast_terms.append((pred_contrast_E - target_E_t) ** 2)
            # D-dim contrast loss (new for P25 — role-specific D structure)
            pred_contrast_D = mw_high[:, 1].mean() - mw_low[:, 1].mean()
            target_D_t = torch.tensor(contrast_target_D_val,
                                       dtype=torch.float32, device=device)
            contrast_terms.append((pred_contrast_D - target_D_t) ** 2)

            # Exogenous anchor at low-h
            exo_E_target_t = torch.tensor(low_target_E,
                                           dtype=torch.float32, device=device)
            exo_anchor_terms.append((ew_low[:, 0].mean() - exo_E_target_t) ** 2)
            exo_D_target_t = torch.tensor(low_target_D,
                                           dtype=torch.float32, device=device)
            exo_anchor_terms.append((ew_low[:, 1].mean() - exo_D_target_t) ** 2)

            # Two-sided: mediated at low-h should be zero
            if use_twosided_anchor:
                med_low_zero_terms.append((mw_low[:, 0].mean()) ** 2)
                med_low_zero_terms.append((mw_low[:, 1].mean()) ** 2)
            n_pairs += 1
        if n_pairs == 0:
            return (torch.tensor(0.0, device=device),
                    torch.tensor(0.0, device=device),
                    torch.tensor(0.0, device=device), 0)
        contrast_loss = torch.stack(contrast_terms).mean()
        exo_loss = torch.stack(exo_anchor_terms).mean()
        med_low_zero_loss = (torch.stack(med_low_zero_terms).mean()
                             if med_low_zero_terms
                             else torch.tensor(0.0, device=device))
        return contrast_loss, exo_loss, med_low_zero_loss, n_pairs

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
                                   torch.full_like(pred_self_v[:, 0][null_mask], -ENERGY_DECAY))
                ns_D = F.mse_loss(pred_self_v[:, 1][null_mask],
                                   torch.full_like(pred_self_v[:, 1][null_mask], DAMAGE_ACCRUAL))
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
        if null_mask.any():
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

        total_loss = attr_loss + 0.5 * v_loss

        n_pairs_used = 0
        if apply_contrast:
            cl, el, ml, n_pairs_used = compute_contrast_loss()
            total_loss = (total_loss
                           + LAMBDA_CONTRAST * cl
                           + lambda_exo * el
                           + lambda_exo * ml)

        return total_loss, n_pairs_used

    buffer = []
    SGD_EVERY = 30
    SGD_K = 4
    rng_online = np.random.RandomState(seed + 47)
    global_step = 0

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
        if episode == WARMUP_EPISODES:
            if warmup_v_probe_values["E"] and warmup_v_probe_values["D"]:
                arr_E = np.array(warmup_v_probe_values["E"])
                arr_D = np.array(warmup_v_probe_values["D"])
                tau_E_perdim = float(np.percentile(arr_E, 85.0))
                tau_D_perdim = float(np.percentile(arr_D, 85.0))

        E = ENERGY_INIT; D = DAMAGE_INIT; h = 0.0; steps = 0
        eps_explore = max(0.10, 0.50 - 0.40 * (episode / max(n_episodes, 1)))
        in_warmup = (episode < WARMUP_EPISODES)
        hist_ema = np.zeros(HISTORY_DIM, dtype=np.float32)

        while E > 0 and D < 1.0 and steps < T_MAX:
            idx = rng_online.randint(0, len(ITEMS))
            c_, l_ = ITEMS[idx]
            obs_raw = encode_one(c_, l_, rng_online)
            x = torch.from_numpy(obs_raw[None]).float().to(device)
            hist_now = hist_ema.copy()
            hist_t_now = torch.from_numpy(hist_now[None]).to(device)

            with torch.no_grad():
                z_cur = encoder(x)
                z_np = z_cur.squeeze(0).cpu().numpy()
                e_t = torch.full((1, 1), float(E), dtype=torch.float32, device=device)
                d_t = torch.full((1, 1), float(D), dtype=torch.float32, device=device)
                ff_cur = fourier_ED(e_t, d_t)
                vp_inp = torch.cat([z_cur, ff_cur, hist_t_now], dim=-1)
                v_out = v_probe_head(vp_inp).squeeze(0)
                v_E_base = float(v_out[0].item())
                v_D_base = float(v_out[1].item())
                if in_warmup:
                    warmup_v_probe_values["E"].append(v_E_base)
                    warmup_v_probe_values["D"].append(v_D_base)
                mw, ew = world_predict(z_cur, ff_cur, hist_t_now)
                w_pred_E = float((mw[:, 0] + ew[:, 0]).item())
                w_pred_D = float((mw[:, 1] + ew[:, 1]).item())
                scores = []
                for a in [0, 1]:
                    a_oh = torch.zeros(1, n_actions, device=device); a_oh[0, a] = 1.0
                    inp = torch.cat([z_cur, ff_cur, a_oh], dim=-1)
                    ps = direct_self_head(inp).squeeze(0)
                    scores.append(float(w_E_train * ps[0].item()
                                          - w_D_train * ps[1].item()))
                greedy_action = 0 if scores[0] >= scores[1] else 1

            # k-means update
            if use_fully_learned and not in_warmup:
                feat = np.concatenate([z_np, [E], [D], hist_now], axis=-1).astype(np.float32)
                cid = fully_learned_cluster_id(z_np, E, D, hist_now)
                cluster_centers[cid] = (
                    (1 - KMEANS_ALPHA) * cluster_centers[cid]
                    + KMEANS_ALPHA * feat
                )
                cluster_counts[cid] += 1

            b_now = bucket_key(c_, l_, E, D, z_np=z_np, hist=hist_now)
            if b_now not in fast_ema:
                # safety: initialize missing buckets (shouldn't happen for oracle)
                fast_ema[b_now] = {"E": 0.0, "D": 0.0}
                slow_ema[b_now] = {"E": 0.0, "D": 0.0}
                non_null_surprise[b_now] = {"E": 0.0, "D": 0.0}
                probe_effort[b_now] = {"E": 0.0, "D": 0.0}
                current_replay_buf[b_now] = deque(maxlen=CURRENT_REPLAY_K)
                high_h_buf[b_now] = deque(maxlen=HIGH_LOW_BUFFER_K)
                low_h_buf[b_now] = deque(maxlen=HIGH_LOW_BUFFER_K)
                bucket_count[b_now] = 0
                bucket_null_density[b_now] = 0

            shift_E = max(0.0, abs(fast_ema[b_now]["E"]) - abs(slow_ema[b_now]["E"]) - SHIFT_MARGIN)
            shift_D = max(0.0, abs(fast_ema[b_now]["D"]) - abs(slow_ema[b_now]["D"]) - SHIFT_MARGIN)
            surp_E = non_null_surprise[b_now]["E"]
            surp_D = non_null_surprise[b_now]["D"]
            v_E_score = v_E_base + LAMBDA_SHIFT * shift_E + LAMBDA_SURPRISE * surp_E
            v_D_score = v_D_base + LAMBDA_SHIFT * shift_D + LAMBDA_SURPRISE * surp_D
            if not in_warmup and apply_contrast:
                missing_high = max(0, MIN_PAIR_COUNT - len(high_h_buf[b_now]))
                missing_low = max(0, MIN_PAIR_COUNT - len(low_h_buf[b_now]))
                v_E_score += PAIR_BONUS * (missing_high + missing_low) / (2 * MIN_PAIR_COUNT)
                v_D_score += PAIR_BONUS * (missing_high + missing_low) / (2 * MIN_PAIR_COUNT)
            thr_E = tau_E_perdim * (1.0 + REFRACTORY_LAMBDA * probe_effort[b_now]["E"])
            thr_D = tau_D_perdim * (1.0 + REFRACTORY_LAMBDA * probe_effort[b_now]["D"])

            take_null = False
            if in_warmup:
                take_null = (rng_online.rand() < WARMUP_PROBE_FLOOR)
            elif is_oracle_source:
                take_null = (rng_online.rand() < 0.33)
            elif apply_contrast:
                base_fire = (v_E_score > thr_E) or (v_D_score > thr_D)
                buffer_short = (
                    len(high_h_buf[b_now]) < MIN_PAIR_COUNT
                    or len(low_h_buf[b_now]) < MIN_PAIR_COUNT
                )
                take_null = base_fire or (buffer_short and rng_online.rand() < 0.10)
            else:
                take_null = (v_E_score > thr_E) or (v_D_score > thr_D)

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
            ws_D = sample_shock_D(role_name, h, rng_online)
            total_E = self_step_E + ws_E
            total_D = self_step_D + ws_D
            E_delta = total_E - (cost if action == 2 else 0.0)

            # Compute mediated/exogenous truth for oracle_source training
            if is_role_invariant_env:
                mediated_E = HAZARD_AMP_INVARIANT * h * SHOCK_E_MAG
                mediated_D = 0.0
            else:
                mediated_E = ROLE_HAZARD_AMP_E_ROLE_SPECIFIC[role_name] * h * SHOCK_E_MAG
                mediated_D = ROLE_HAZARD_AMP_D_ROLE_SPECIFIC[role_name] * h * SHOCK_D_MAG
            exogenous_E = BASE_SHOCK_E[role_name] * SHOCK_E_MAG
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
            if action != 2:
                non_null_surprise[b_now]["E"] = (
                    (1 - NON_NULL_SURPRISE_ALPHA) * non_null_surprise[b_now]["E"]
                    + NON_NULL_SURPRISE_ALPHA * abs(signed_E)
                )
                non_null_surprise[b_now]["D"] = (
                    (1 - NON_NULL_SURPRISE_ALPHA) * non_null_surprise[b_now]["D"]
                    + NON_NULL_SURPRISE_ALPHA * abs(signed_D)
                )

            for b in BUCKETS:
                probe_effort[b]["E"] *= LEAKY_EFFORT_RHO
                probe_effort[b]["D"] *= LEAKY_EFFORT_RHO

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
                if h > HIGH_H_THRESHOLD:
                    high_h_buf[b_now].append(
                        (obs_raw.copy(), float(E), float(D),
                         float(total_E), float(total_D), hist_now.copy())
                    )
                elif h < LOW_H_THRESHOLD:
                    low_h_buf[b_now].append(
                        (obs_raw.copy(), float(E), float(D),
                         float(total_E), float(total_D), hist_now.copy())
                    )
                bucket_count[b_now] += 1
                bucket_null_density[b_now] += 1
                probe_effort[b_now]["E"] += 1.0
                probe_effort[b_now]["D"] += 1.0

            new_hist = (1 - HISTORY_EMA_ALPHA) * hist_ema
            if action == 1:
                new_hist[ROLE_IDX[role_name]] += HISTORY_EMA_ALPHA
            elif action == 2:
                new_hist[4] += HISTORY_EMA_ALPHA
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
                    loss, _ = step_loss(mb)
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
                "cum_null_count": int(sum(bucket_null_density.values())),
            })

    encoder.eval(); direct_self_head.eval()
    mediated_world_head.eval(); exogenous_world_head.eval()
    v_probe_head.eval()

    # Diagnostics — per-role mediated/exogenous via causal contrast
    rng_diag = np.random.RandomState(seed + 333)
    n_diag = 128
    E_GRID = [0.1, 0.5, 0.9]; D_GRID = [0.1, 0.5, 0.9]
    pred_by_role = {}
    high_hist = np.array([1.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
    high_hist_t = torch.from_numpy(high_hist[None].repeat(n_diag, axis=0)).to(device)
    low_hist = np.zeros(HISTORY_DIM, dtype=np.float32)
    low_hist_t = torch.from_numpy(low_hist[None].repeat(n_diag, axis=0)).to(device)

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
            world_E_high = []; world_E_low = []
            world_D_high = []; world_D_low = []
            for Ev in E_GRID:
                for Dv in D_GRID:
                    e_t = torch.full((n_diag, 1), Ev, dtype=torch.float32, device=device)
                    d_t = torch.full((n_diag, 1), Dv, dtype=torch.float32, device=device)
                    ff = fourier_ED(e_t, d_t)
                    mw_h, ew_h = world_predict(z, ff, high_hist_t)
                    mw_l, ew_l = world_predict(z, ff, low_hist_t)
                    world_E_high.append(float((mw_h[:, 0] + ew_h[:, 0]).mean()))
                    world_E_low.append(float((mw_l[:, 0] + ew_l[:, 0]).mean()))
                    world_D_high.append(float((mw_h[:, 1] + ew_h[:, 1]).mean()))
                    world_D_low.append(float((mw_l[:, 1] + ew_l[:, 1]).mean()))
            results["world_E_high"] = float(np.mean(world_E_high))
            results["world_E_low"] = float(np.mean(world_E_low))
            results["world_D_high"] = float(np.mean(world_D_high))
            results["world_D_low"] = float(np.mean(world_D_low))
            results["pred_mediated_E_contrast"] = (
                results["world_E_high"] - results["world_E_low"]
            )
            results["pred_mediated_D_contrast"] = (
                results["world_D_high"] - results["world_D_low"]
            )
            results["pred_exogenous_E_contrast"] = results["world_E_low"]
            results["pred_exogenous_D_contrast"] = results["world_D_low"]
        # True role-specific values at h=1
        if is_role_invariant_env:
            true_med_E_max = HAZARD_AMP_INVARIANT * 1.0 * SHOCK_E_MAG
            true_med_D_max = 0.0
        else:
            true_med_E_max = ROLE_HAZARD_AMP_E_ROLE_SPECIFIC[role] * 1.0 * SHOCK_E_MAG
            true_med_D_max = ROLE_HAZARD_AMP_D_ROLE_SPECIFIC[role] * 1.0 * SHOCK_D_MAG
        results["true_mediated_E_max"] = true_med_E_max
        results["true_mediated_D_max"] = true_med_D_max
        results["true_exogenous_E"] = BASE_SHOCK_E[role] * SHOCK_E_MAG
        results["true_exogenous_D"] = BASE_SHOCK_D[role] * SHOCK_D_MAG
        results["true_self_consume_E"] = consume_self_dE(c, l) - ENERGY_DECAY
        results["true_self_consume_D"] = consume_self_dD(c, l) + DAMAGE_ACCRUAL
        pred_by_role[role] = results

    # Eval (simplified, carried from P24)
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

    def eval_under(w_E, w_D, regime_episode):
        rng_eval = np.random.RandomState(seed + 9999)
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
                ws_D = sample_shock_D(role_name, h, rng_eval)
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
        eval_results[prio] = eval_under(w_E, w_D, n_episodes - 1)

    # Bucket density log for G8 non-collapse
    bucket_density_distribution = {b: int(bucket_null_density.get(b, 0))
                                     for b in BUCKETS}

    return dict(
        seed=seed, condition=condition, cost=cost,
        n_actions=n_actions,
        eval_by_priority=eval_results,
        prediction_by_role=pred_by_role,
        learning_curve=learning_curve,
        bucket_null_density=bucket_density_distribution,
        var_state=var_state,
        thresholds={"tau_E": tau_E_perdim, "tau_D": tau_D_perdim},
        cluster_counts=cluster_counts.tolist() if use_fully_learned else None,
        is_role_invariant_env=is_role_invariant_env,
        lambda_exo=lambda_exo,
    )


def _flatten_to_row(r):
    bal = r["eval_by_priority"]["balanced"]
    row = dict(
        seed=r["seed"], condition=r["condition"], cost=r["cost"],
        balanced_return=bal["mean_return"],
        lambda_exo=r.get("lambda_exo"),
    )
    for role in ROLES:
        for prio in ["balanced", "hungry", "injured"]:
            row[f"{prio}_acc_{role}"] = r["eval_by_priority"][prio]["per_role_accuracy"].get(role, 0.0)
    for role, info in r["prediction_by_role"].items():
        row[f"pred_self_E_consume_{role}"] = info["self_E_action_1"]
        row[f"pred_self_D_consume_{role}"] = info["self_D_action_1"]
        row[f"pred_mediated_E_contrast_{role}"] = info.get("pred_mediated_E_contrast", 0.0)
        row[f"pred_mediated_D_contrast_{role}"] = info.get("pred_mediated_D_contrast", 0.0)
        row[f"pred_exogenous_E_contrast_{role}"] = info.get("pred_exogenous_E_contrast", 0.0)
        row[f"pred_exogenous_D_contrast_{role}"] = info.get("pred_exogenous_D_contrast", 0.0)
        row[f"true_mediated_E_max_{role}"] = info.get("true_mediated_E_max", 0.0)
        row[f"true_mediated_D_max_{role}"] = info.get("true_mediated_D_max", 0.0)
        row[f"true_exogenous_E_{role}"] = info.get("true_exogenous_E", 0.0)
        row[f"true_exogenous_D_{role}"] = info.get("true_exogenous_D", 0.0)
    if r.get("learning_curve"):
        row["final_lc_mae"] = r["learning_curve"][-1]["total_food_E_poison_D_mae"]
    return row


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    n_episodes: int = 500,
    batch_size: int = 48,
    eval_episodes: int = 50,
    out: str = "artifacts/role_specific_identifiability/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    primary_cost = COST_HEADLINE

    pass1_args = []
    for sd in seed_list:
        for cond in ALL_CONDITIONS:
            pass1_args.append(dict(
                seed=sd, condition=cond, cost=primary_cost,
                n_episodes=n_episodes,
                batch_size=batch_size, eval_episodes=eval_episodes,
            ))
    print(f"PASS 1: running {len(pass1_args)} cells in parallel...")
    results = list(run_cell.map(pass1_args))

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
            regime_shift_1=REGIME_SHIFT_1, regime_shift_2=REGIME_SHIFT_2,
            role_hazard_amp_E_role_specific=ROLE_HAZARD_AMP_E_ROLE_SPECIFIC,
            role_hazard_amp_D_role_specific=ROLE_HAZARD_AMP_D_ROLE_SPECIFIC,
            hazard_amp_invariant=HAZARD_AMP_INVARIANT,
            lambda_contrast=LAMBDA_CONTRAST,
            n_fully_learned_clusters=N_FULLY_LEARNED_CLUSTERS,
            item_types={f"{c},{l}": info for (c, l), info in ITEM_TYPES.items()},
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nsummary ({len(summary_rows)} cells):")
    print(f"{'cond':<46} {'seed':>10} | "
          f"{'medE_f':>6} {'medE_m':>6} {'medD_p':>6} {'exoE_f':>6} {'lc':>6}")
    print(f"  TRUE role-specific medE: food=+0.150, medicine=+0.060")
    print(f"  TRUE role-specific medD: poison=+0.066")
    for r in summary_rows:
        medE_f = r.get('pred_mediated_E_contrast_food', 0.0)
        medE_m = r.get('pred_mediated_E_contrast_medicine', 0.0)
        medD_p = r.get('pred_mediated_D_contrast_poison', 0.0)
        exoE_f = r.get('pred_exogenous_E_contrast_food', 0.0)
        lc = r.get('final_lc_mae', 0.0)
        print(f"  {r['condition']:<44} {r['seed']:>10} | "
              f"{medE_f:>+6.3f} {medE_m:>+6.3f} {medD_p:>+6.3f} {exoE_f:>+6.3f} {lc:>6.3f}")
