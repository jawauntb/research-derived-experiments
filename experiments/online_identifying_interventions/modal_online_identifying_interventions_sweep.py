#!/usr/bin/env python3
"""Paper 18 — Online Identifying Interventions.

Factorial isolation of (data regime: off-policy fixed | online buffer-shaped)
× (probe target: raw per-sample residual | lagged signed-residual EMA).

Conditions:
  - factorized_no_null_online             : 16/17A gauge-symmetric failure baseline
  - factorized_null_passive_online        : Null inclusion w/o anchor loss
  - scheduled_null_anchor_online          : 16b positive control under online training
  - matched_random_global_online          : Same null count as headline, random
  - learned_raw_vprobe_offpolicy          : 17A replication / 2×2 cell
  - learned_raw_vprobe_online             : 2×2 cell: online data + raw target
  - debiased_vprobe_offpolicy             : 2×2 cell: off-policy + debiased target
  - learned_debiased_vprobe_online        : HEADLINE: online + debiased
  - oracle_uncertainty_probe_online       : Upper bound on probe placement
  - oracle_source_online                  : 16b upper bound (semantic labels)

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/online_identifying_interventions/modal_online_identifying_interventions_sweep.py
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

app = modal.App(name="research-derived-online-identifying-interventions")

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
COSTS = [0.01, 0.025, 0.04]

EMA_ALPHA = 0.05

ALL_CONDITIONS = [
    "factorized_no_null_online",
    "factorized_null_passive_online",
    "scheduled_null_anchor_online",
    "matched_random_global_online",
    "learned_raw_vprobe_offpolicy",
    "learned_raw_vprobe_online",
    "debiased_vprobe_offpolicy",
    "learned_debiased_vprobe_online",
    "oracle_uncertainty_probe_online",
    "oracle_source_online",
]

COST_RELEVANT = {
    "learned_raw_vprobe_offpolicy",
    "learned_raw_vprobe_online",
    "debiased_vprobe_offpolicy",
    "learned_debiased_vprobe_online",
    "oracle_uncertainty_probe_online",
    "matched_random_global_online",
}

ONLINE_CONDITIONS = {
    "factorized_no_null_online",
    "factorized_null_passive_online",
    "scheduled_null_anchor_online",
    "matched_random_global_online",
    "learned_raw_vprobe_online",
    "learned_debiased_vprobe_online",
    "oracle_uncertainty_probe_online",
    "oracle_source_online",
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
    from collections import defaultdict

    seed: int = arg["seed"]
    condition: str = arg["condition"]
    cost: float = arg["cost"]
    target_null_rate = arg.get("target_null_rate", None)
    n_episodes: int = arg["n_episodes"]
    n_offpolicy_steps: int = arg["n_offpolicy_steps"]
    batch_size: int = arg["batch_size"]
    eval_episodes: int = arg["eval_episodes"]

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cpu")
    rng_env = np.random.RandomState(seed + 13)
    perm = rng_env.permutation(16)

    is_online = condition in ONLINE_CONDITIONS
    has_null = condition != "factorized_no_null_online"
    n_actions = N_ACTIONS_WITH_NULL if has_null else N_ACTIONS_NO_NULL

    use_debiased = condition in (
        "debiased_vprobe_offpolicy", "learned_debiased_vprobe_online"
    )
    is_learned_probe_eval = condition in (
        "learned_raw_vprobe_offpolicy", "learned_raw_vprobe_online",
        "debiased_vprobe_offpolicy", "learned_debiased_vprobe_online",
    )
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

    bucket_ema = {b: 0.0 for b in BUCKETS}
    bucket_count = {b: 0 for b in BUCKETS}

    def step_loss(z, ffE, a_oh, actions_np, total_dE_t, self_dE_t,
                  world_dE_t, lagged_v_targets_t=None):
        self_input = torch.cat([z, ffE, a_oh], dim=-1)
        world_input = torch.cat([z, ffE], dim=-1)
        pred_self = self_head(self_input).squeeze(-1)
        pred_world = world_head(world_input).squeeze(-1)
        target_total = total_dE_t

        if condition == "factorized_no_null_online":
            attr_loss = F.mse_loss(pred_self + pred_world, target_total)
        elif condition == "factorized_null_passive_online":
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
        if has_null and condition != "factorized_null_passive_online":
            null_mask_t = torch.from_numpy(actions_np == 2)
            if null_mask_t.any():
                if use_debiased and lagged_v_targets_t is not None:
                    # Debiased: use stored lagged EMA absolute residual targets
                    null_idx = null_mask_t.nonzero(as_tuple=True)[0]
                    v_target = lagged_v_targets_t[null_idx]
                else:
                    # Raw: per-sample |pred_world - observed_total|
                    with torch.no_grad():
                        v_target = (
                            pred_world[null_mask_t].detach()
                            - target_total[null_mask_t]
                        ).abs()
                v_pred = v_probe_head(world_input[null_mask_t]).squeeze(-1)
                v_loss = F.mse_loss(v_pred, v_target)

        return attr_loss + 0.5 * v_loss, pred_self, pred_world

    # ============ OFF-POLICY TRAINING ============
    if not is_online:
        rng_train = np.random.RandomState(seed + 47)
        for step in range(n_offpolicy_steps):
            idxs = rng_train.randint(0, len(ITEMS), size=batch_size)
            colors = np.array([ITEMS[i][0] for i in idxs])
            labels = np.array([ITEMS[i][1] for i in idxs])
            Es = rng_train.uniform(0.0, 1.0, size=batch_size).astype(np.float32)
            if condition == "factorized_no_null_online":
                actions = rng_train.randint(0, 2, size=batch_size).astype(np.int64)
            else:
                actions = rng_train.randint(0, n_actions, size=batch_size).astype(np.int64)

            self_dE_arr = np.zeros(batch_size, dtype=np.float32)
            world_dE_arr = np.zeros(batch_size, dtype=np.float32)
            for i in range(batch_size):
                self_dE_arr[i] = action_self_dE(int(actions[i]),
                                                  int(colors[i]), int(labels[i]))
                world_dE_arr[i] = sample_world_shock(int(colors[i]),
                                                      int(labels[i]),
                                                      TRAINING_SHOCK, rng_train)
            total_dE_arr = self_dE_arr + world_dE_arr

            obs = np.stack([encode_one(c, l, rng_train)
                            for c, l in zip(colors, labels)])
            x = torch.from_numpy(obs).to(device)
            z = encoder(x)
            e_t = torch.from_numpy(Es.reshape(-1, 1)).to(device)
            ffE = fourier_E(e_t)
            a_oh = torch.zeros(batch_size, n_actions, device=device)
            a_oh[np.arange(batch_size), actions] = 1.0

            # For debiased off-policy: compute lagged_v_targets for null entries
            lagged_v_targets = None
            if use_debiased:
                lvt = np.zeros(batch_size, dtype=np.float32)
                for i in range(batch_size):
                    if actions[i] == 2:
                        b = bucket_key(int(colors[i]), int(labels[i]), float(Es[i]))
                        lvt[i] = abs(bucket_ema[b])
                lagged_v_targets = torch.from_numpy(lvt).to(device)

            total_dE_t = torch.from_numpy(total_dE_arr).to(device)
            self_dE_t = torch.from_numpy(self_dE_arr).to(device)
            world_dE_t = torch.from_numpy(world_dE_arr).to(device)
            loss, pred_self_t, pred_world_t = step_loss(
                z, ffE, a_oh, actions, total_dE_t, self_dE_t, world_dE_t,
                lagged_v_targets,
            )
            opt.zero_grad(); loss.backward(); opt.step()

            # Update bucket EMA from null observations (post-step)
            if use_debiased:
                with torch.no_grad():
                    z_post = encoder(x)
                    pw_post = world_head(
                        torch.cat([z_post, ffE], dim=-1)
                    ).squeeze(-1).cpu().numpy()
                for i in range(batch_size):
                    if actions[i] == 2:
                        b = bucket_key(int(colors[i]), int(labels[i]), float(Es[i]))
                        signed = float(pw_post[i] - total_dE_arr[i])
                        if bucket_count[b] == 0:
                            bucket_ema[b] = signed
                        else:
                            bucket_ema[b] = ((1 - EMA_ALPHA) * bucket_ema[b]
                                              + EMA_ALPHA * signed)
                        bucket_count[b] += 1

    # ============ ONLINE TRAINING ============
    else:
        # Replay buffer of (raw obs, E, action, total, self, world, c, l, lagged_v_target)
        buffer = []
        SGD_EVERY = 30
        SGD_K = 4
        rng_online = np.random.RandomState(seed + 47)
        global_step = 0

        # For matched_random_global: track scheduled null indices
        # (we'll inject random nulls at the matched rate during rollout)
        matched_target_rate = (float(target_null_rate)
                                if target_null_rate is not None else 0.20)
        matched_target_rate = max(0.02, min(0.6, matched_target_rate))

        for episode in range(n_episodes):
            E = ENERGY_INIT
            steps = 0
            while E > 0 and steps < T_MAX:
                idx = rng_online.randint(0, len(ITEMS))
                c_, l_ = ITEMS[idx]
                obs_raw = encode_one(c_, l_, rng_online)
                x = torch.from_numpy(obs_raw[None]).float().to(device)

                # Decide action
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

                action = greedy_action
                if condition == "factorized_no_null_online":
                    pass  # only consume/skip
                elif condition == "factorized_null_passive_online":
                    # Random null injection at 33% to populate null buffer
                    # without anchor loss (matches off-policy passive)
                    if rng_online.rand() < 0.33:
                        action = 2
                elif condition == "scheduled_null_anchor_online":
                    # Experimenter-scheduled at 33%
                    if rng_online.rand() < 0.33:
                        action = 2
                elif condition == "matched_random_global_online":
                    if rng_online.rand() < matched_target_rate:
                        action = 2
                elif condition in ("learned_raw_vprobe_online",
                                    "learned_debiased_vprobe_online"):
                    if v_val > cost:
                        action = 2
                elif condition == "oracle_uncertainty_probe_online":
                    true_world = (TRAINING_SHOCK[role_of(c_, l_)]
                                   * SHOCK_MAGNITUDE)
                    err = abs(w_pred_cur - true_world)
                    if err > cost:
                        action = 2
                elif condition == "oracle_source_online":
                    # Random null at 33% to populate buffer (oracle gets explicit
                    # source labels for training, so null is just data variety)
                    if rng_online.rand() < 0.33:
                        action = 2

                # Step env
                self_step = action_self_dE(action, c_, l_)
                world_step = sample_world_shock(c_, l_, TRAINING_SHOCK, rng_online)
                if action == 2:
                    self_step = self_step - cost
                total = self_step + world_step

                # Record lagged v_target BEFORE EMA update
                lagged_v_target = 0.0
                if use_debiased and action == 2:
                    b = bucket_key(c_, l_, E)
                    lagged_v_target = abs(bucket_ema[b])

                # Add to buffer
                buffer.append(dict(
                    obs=obs_raw, E=float(E), action=int(action),
                    total=float(total), self_dE=float(self_step + (cost if action==2 else 0)),
                    world_dE=float(world_step), c=int(c_), l=int(l_),
                    lagged_v=float(lagged_v_target),
                ))

                # Update bucket EMA AFTER recording lagged target
                if use_debiased and action == 2:
                    b = bucket_key(c_, l_, E)
                    signed = w_pred_cur - total
                    if bucket_count[b] == 0:
                        bucket_ema[b] = signed
                    else:
                        bucket_ema[b] = ((1 - EMA_ALPHA) * bucket_ema[b]
                                          + EMA_ALPHA * signed)
                    bucket_count[b] += 1

                global_step += 1

                # SGD update from stratified buffer
                if (len(buffer) >= 64
                        and global_step % SGD_EVERY == 0):
                    for _ in range(SGD_K):
                        # Stratify by action
                        per_stratum = batch_size // 3
                        idx_by_action = defaultdict(list)
                        for k, b in enumerate(buffer):
                            idx_by_action[b["action"]].append(k)
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

                        actions_arr = np.array([b["action"] for b in mb],
                                                dtype=np.int64)
                        Es_arr = np.array([b["E"] for b in mb], dtype=np.float32)
                        totals_arr = np.array([b["total"] for b in mb],
                                               dtype=np.float32)
                        selfs_arr = np.array([b["self_dE"] for b in mb],
                                              dtype=np.float32)
                        worlds_arr = np.array([b["world_dE"] for b in mb],
                                               dtype=np.float32)
                        obss_arr = np.stack([b["obs"] for b in mb])
                        lvts_arr = np.array([b["lagged_v"] for b in mb],
                                             dtype=np.float32)

                        x_mb = torch.from_numpy(obss_arr).to(device)
                        z_mb = encoder(x_mb)
                        e_mb = torch.from_numpy(
                            Es_arr.reshape(-1, 1)
                        ).to(device)
                        ffE_mb = fourier_E(e_mb)
                        a_oh = torch.zeros(len(mb), n_actions, device=device)
                        a_oh[np.arange(len(mb)), actions_arr] = 1.0

                        lvt_t = (torch.from_numpy(lvts_arr).to(device)
                                  if use_debiased else None)
                        total_t = torch.from_numpy(totals_arr).to(device)
                        self_t = torch.from_numpy(selfs_arr).to(device)
                        world_t = torch.from_numpy(worlds_arr).to(device)
                        loss, _, _ = step_loss(
                            z_mb, ffE_mb, a_oh, actions_arr,
                            total_t, self_t, world_t, lvt_t,
                        )
                        opt.zero_grad(); loss.backward(); opt.step()

                E = max(0.0, min(1.0, E + total))
                steps += 1

    encoder.eval(); self_head.eval(); world_head.eval(); v_probe_head.eval()

    # ============ Component-recovery diagnostics ============
    rng_diag = np.random.RandomState(seed + 333)
    n_diag = 128
    pred_by_role = {}
    for (c, l), info in ITEM_TYPES.items():
        role = info["role"]
        obs_list = [encode_one(c, l, rng_diag) for _ in range(n_diag)]
        obs_arr = np.stack(obs_list)
        with torch.no_grad():
            z = encoder(torch.from_numpy(obs_arr).to(device))
            e_t = torch.full((n_diag, 1), 0.5, dtype=torch.float32, device=device)
            ffE = fourier_E(e_t)
            results = {}
            for action_idx in range(n_actions):
                a_oh = torch.zeros(n_diag, n_actions, device=device)
                a_oh[:, action_idx] = 1.0
                inp = torch.cat([z, ffE, a_oh], dim=-1)
                pred_s = self_head(inp).squeeze(-1).cpu().numpy()
                results[f"self_action_{action_idx}"] = float(pred_s.mean())
            world_input = torch.cat([z, ffE], dim=-1)
            pred_w = world_head(world_input).squeeze(-1).cpu().numpy()
            results["world"] = float(pred_w.mean())
            v_pred = v_probe_head(world_input).squeeze(-1).cpu().numpy()
            results["v_probe"] = float(v_pred.mean())
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
                ema_signed_residual=float(bucket_ema.get(key, 0.0)),
                ema_count=int(bucket_count.get(key, 0)),
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
                    should_null = (v_val > cost)
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
        import numpy as _np
        return dict(
            distribution=dist_name,
            mean_return=float(_np.mean(returns)),
            action_accuracy=(float(_np.mean(acc_records))
                              if acc_records else 0.0),
            null_rate=(null_actions / max(total_actions, 1)),
            probe_fires_by_bucket=probe_fires_by_bucket,
            state_visits_by_bucket=state_visits_by_bucket,
        )

    in_dist = eval_under(TRAINING_SHOCK, "in_dist")
    shifted = eval_under(SHIFTED_SHOCK, "shifted")

    # Buffer composition (for G10) — only in online conditions
    buffer_composition = None
    if is_online:
        # During online training we kept a buffer; rebuild key stats here
        pass  # buffer composition stats are not directly exported; we re-derive
              # from eval probe fires + offline diagnostics

    return dict(
        seed=seed, condition=condition, cost=cost, is_online=is_online,
        has_null=has_null, n_actions=n_actions,
        target_null_rate=target_null_rate,
        use_debiased=use_debiased,
        in_dist_eval=in_dist, shifted_eval=shifted,
        prediction_by_role=pred_by_role,
        bucket_diag=bucket_diag,
    )


def _flatten_to_row(r):
    row = dict(
        seed=r["seed"], condition=r["condition"], cost=r["cost"],
        is_online=r["is_online"],
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
    n_offpolicy_steps: int = 1500,
    batch_size: int = 48,
    eval_episodes: int = 50,
    out: str = "artifacts/online_identifying_interventions/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    cost_irrelevant_conds = [c for c in ALL_CONDITIONS
                              if c not in COST_RELEVANT]
    cost_relevant_no_matched = [c for c in ALL_CONDITIONS
                                  if c in COST_RELEVANT
                                  and c != "matched_random_global_online"]

    # PASS 1
    pass1_args = []
    for sd in seed_list:
        for cond in cost_irrelevant_conds:
            pass1_args.append(dict(
                seed=sd, condition=cond, cost=COST_HEADLINE,
                n_episodes=n_episodes,
                n_offpolicy_steps=n_offpolicy_steps,
                batch_size=batch_size, eval_episodes=eval_episodes,
            ))
        for cond in cost_relevant_no_matched:
            for c in COSTS:
                pass1_args.append(dict(
                    seed=sd, condition=cond, cost=c,
                    n_episodes=n_episodes,
                    n_offpolicy_steps=n_offpolicy_steps,
                    batch_size=batch_size, eval_episodes=eval_episodes,
                ))
    print(f"PASS 1: running {len(pass1_args)} cells in parallel...")
    pass1_results = list(run_cell.map(pass1_args))

    rates = {}
    for r in pass1_results:
        if r["condition"] == "learned_debiased_vprobe_online":
            rates[(float(r["cost"]), int(r["seed"]))] = (
                r["in_dist_eval"]["null_rate"]
            )
    print(f"  headline learned probe rates by (cost, seed): {rates}")

    # PASS 2
    pass2_args = []
    for sd in seed_list:
        for c in COSTS:
            target_rate = rates.get((c, sd), 0.20)
            pass2_args.append(dict(
                seed=sd, condition="matched_random_global_online", cost=c,
                target_null_rate=target_rate,
                n_episodes=n_episodes,
                n_offpolicy_steps=n_offpolicy_steps,
                batch_size=batch_size, eval_episodes=eval_episodes,
            ))
    print(f"PASS 2: running {len(pass2_args)} cells in parallel...")
    pass2_results = list(run_cell.map(pass2_args))

    results = pass1_results + pass2_results
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = [_flatten_to_row(r) for r in results]

    out_path.write_text(json.dumps({
        "manifest": dict(
            seeds=seed_list, conditions=ALL_CONDITIONS, costs=COSTS,
            cost_headline=COST_HEADLINE,
            n_episodes=n_episodes, n_offpolicy_steps=n_offpolicy_steps,
            batch_size=batch_size, eval_episodes=eval_episodes,
            training_shock=TRAINING_SHOCK, shifted_shock=SHIFTED_SHOCK,
            shock_magnitude=SHOCK_MAGNITUDE,
            ema_alpha=EMA_ALPHA,
            item_types={f"{c},{l}": info for (c, l), info in ITEM_TYPES.items()},
            realized_headline_rates={f"{k[0]},{k[1]}": v
                                       for k, v in rates.items()},
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nsummary ({len(summary_rows)} cells):")
    print(f"{'cond':<38} {'seed':>10} {'cost':>5} | "
          f"{'ps_food':>7} {'pw_food':>7} {'ret':>5} {'null%':>6}")
    print(f"  TRUE FOOD: self_consume=+0.96, world_in_dist=+0.24")
    for r in summary_rows:
        psw = r.get('pred_world_food')
        psw_str = f"{psw:+.3f}" if psw is not None else "  --  "
        nrate = r.get('in_dist_null_rate', 0.0) * 100
        print(f"  {r['condition']:<38} {r['seed']:>10} {r['cost']:>5.3f} | "
              f"{r['pred_self_consume_food']:>+.3f} {psw_str:>7} "
              f"{r['in_dist_return']:>5.1f} {nrate:>5.1f}")
