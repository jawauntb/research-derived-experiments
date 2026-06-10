#!/usr/bin/env python3
"""Paper 8 — Concern Bootstrap sweep.

Tests whether a self-organizing training pressure can induce valence-
aligned representation without supervised optimal-action labels (as in
Paper 6/7). Headline mechanism: an action-conditioned ΔE auxiliary
prediction head trained jointly with REINFORCE.

Conditions (5):
  - rl_scratch          : baseline (no aux, no pretrain)
  - rl_delta_e_aux      : REINFORCE + action-conditioned ΔE prediction
                          (headline). Encoder gets gradients from BOTH
                          the policy loss and the aux loss.
  - rl_curriculum       : train in additive_thresh for the first half,
                          then ecological shift to XOR. From scratch.
  - rl_after_valence    : supervised optimal-action pretrain (upper
                          bound, from Paper 7).
  - rl_frozen_sensory   : supervised color pretrain, freeze encoder,
                          RL only on policy head (proxy-trap control).

Environment configs (3):
  - xor_stable          : XOR throughout
  - additive_stable     : additive_thresh throughout
  - add_to_xor_shift    : additive_thresh for first half, XOR for
                          second half (ecological shift)

5 × 3 envs × 3 seeds = 45 cells. ~30 min on Modal CPU.

Aux head signature:
  aux_head(z, energy_scalar, action_one_hot) -> predicted ΔE
  loss = MSE(predicted_ΔE, observed_ΔE)

The encoder gets gradients from this MSE, which depends on (item,
action) — so the encoder learns to represent the item's *causal*
contribution to ΔE, i.e., the reward axis under this environment.
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

app = modal.App(name="research-derived-concern-bootstrap")

N_COLORS = 4
N_LABELS = 2
ITEMS = [(c, l) for c in range(N_COLORS) for l in range(N_LABELS)]
EMBED_DIM = 32
OBS_NOISE = 0.15
T_MAX = 50
ENERGY_DECAY = 0.04
ENERGY_INIT = 0.5

ALL_CONDITIONS = [
    "rl_scratch",
    "rl_delta_e_aux",
    "rl_curriculum",
    "rl_after_valence",
    "rl_frozen_sensory",
]
ALL_ENVS = ["xor_stable", "additive_stable", "add_to_xor_shift"]


def reward_fn_of(name: str):
    if name == "xor":
        return lambda c, l: 1.0 if ((c in (0, 1)) ^ (l == 0)) else -1.0
    elif name == "additive_thresh":
        return lambda c, l: 1.0 if (c + (1 if l == 1 else -2)) > 0 else -1.0
    raise ValueError(name)


@app.function(image=IMAGE, timeout=1800, cpu=4, memory=4096)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    seed: int = arg["seed"]
    condition: str = arg["condition"]
    env_config: str = arg["env_config"]
    pretrain_steps: int = arg["pretrain_steps"]
    pretrain_batch: int = arg["pretrain_batch"]
    n_episodes: int = arg["n_episodes"]
    test_samples: int = arg["test_samples"]

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rng_env = np.random.RandomState(seed + 13)
    perm = rng_env.permutation(16)

    # Determine env_phase1 and env_phase2 from env_config
    if env_config == "xor_stable":
        env_phase1 = env_phase2 = "xor"
    elif env_config == "additive_stable":
        env_phase1 = env_phase2 = "additive_thresh"
    elif env_config == "add_to_xor_shift":
        env_phase1 = "additive_thresh"
        env_phase2 = "xor"
    elif condition == "rl_curriculum":
        # Curriculum hardcodes additive→xor regardless of env_config; treat
        # as add_to_xor_shift for env_config == add_to_xor_shift only.
        # In other env_configs, the curriculum starts and ends in env_config.
        env_phase1 = env_phase2 = env_config.replace("_stable", "")
    else:
        raise ValueError(env_config)

    # Curriculum always runs additive→xor for its dedicated env (we'll only
    # report rl_curriculum on the add_to_xor_shift env to keep it clean)
    if condition == "rl_curriculum":
        env_phase1 = "additive_thresh"
        env_phase2 = "xor"

    rwd_phase1 = reward_fn_of(env_phase1)
    rwd_phase2 = reward_fn_of(env_phase2)
    shift_at = n_episodes // 2

    def encode_obs(colors, labels, rng):
        n = len(colors)
        obs = np.zeros((n, 16), dtype=np.float32)
        obs[np.arange(n), colors] = 1.0
        obs[np.arange(n), 8 + labels] = 1.0
        obs += rng.randn(n, 16).astype(np.float32) * OBS_NOISE
        return obs[:, perm]

    def sample_items(n, rng, reward_fn):
        idx = rng.randint(0, len(ITEMS), size=n)
        colors = np.array([ITEMS[i][0] for i in idx])
        labels = np.array([ITEMS[i][1] for i in idx])
        rewards = np.array([reward_fn(c, l) for c, l in zip(colors, labels)])
        obs = encode_obs(colors, labels, rng)
        return obs, colors, labels, rewards

    # ============ Encoder ============
    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)

    # ============ Optional pretraining ============
    pretrain_log = []
    pretrained_cluster_gaps = None
    if condition == "rl_after_valence":
        head_pre = nn.Linear(EMBED_DIM, 2).to(device)
        opt_pre = torch.optim.Adam(
            list(encoder.parameters()) + list(head_pre.parameters()), lr=2e-3,
        )
        rng_pre = np.random.RandomState(seed + 23)
        for step in range(pretrain_steps):
            obs, _, _, rewards = sample_items(pretrain_batch, rng_pre, rwd_phase1)
            x = torch.from_numpy(obs).to(device)
            z = encoder(x)
            logits = head_pre(z)
            optimal_action = (rewards > 0).astype(np.int64)
            target = torch.from_numpy(optimal_action).long().to(device)
            loss = F.cross_entropy(logits, target)
            opt_pre.zero_grad(); loss.backward(); opt_pre.step()
            if step % 100 == 0:
                pretrain_log.append(dict(step=step, loss=float(loss.item())))
    elif condition == "rl_frozen_sensory":
        head_pre = nn.Linear(EMBED_DIM, N_COLORS).to(device)
        opt_pre = torch.optim.Adam(
            list(encoder.parameters()) + list(head_pre.parameters()), lr=2e-3,
        )
        rng_pre = np.random.RandomState(seed + 23)
        for step in range(pretrain_steps):
            obs, colors, _, _ = sample_items(pretrain_batch, rng_pre, rwd_phase1)
            x = torch.from_numpy(obs).to(device)
            z = encoder(x)
            logits = head_pre(z)
            target = torch.from_numpy(colors).long().to(device)
            loss = F.cross_entropy(logits, target)
            opt_pre.zero_grad(); loss.backward(); opt_pre.step()
            if step % 100 == 0:
                pretrain_log.append(dict(step=step, loss=float(loss.item())))

    # Measure pretrained cluster gaps
    if condition in ("rl_after_valence", "rl_frozen_sensory"):
        rng_pre_test = np.random.RandomState(seed + 333)
        # Measure against the phase-1 reward function
        obs_t, col_t, lab_t, rew_t = sample_items(
            test_samples, rng_pre_test, rwd_phase1,
        )
        with torch.no_grad():
            zt = encoder(torch.from_numpy(obs_t).to(device)).cpu().numpy()
        pretrained_cluster_gaps = compute_cluster_gaps(zt, col_t, lab_t, rew_t)

    # Freeze encoder for the frozen condition
    if condition == "rl_frozen_sensory":
        for p in encoder.parameters():
            p.requires_grad = False

    # ============ Policy head ============
    policy_head = nn.Sequential(
        nn.Linear(EMBED_DIM + 1, 32), nn.Tanh(),
        nn.Linear(32, 2),
    ).to(device)

    # ============ ΔE auxiliary head (only for rl_delta_e_aux) ============
    aux_head = None
    if condition == "rl_delta_e_aux":
        aux_head = nn.Sequential(
            nn.Linear(EMBED_DIM + 1 + 2, 32), nn.Tanh(),
            nn.Linear(32, 1),
        ).to(device)

    # Set up optimizer
    trainable = (
        [p for p in encoder.parameters() if p.requires_grad]
        + list(policy_head.parameters())
    )
    if aux_head is not None:
        trainable += list(aux_head.parameters())
    opt_rl = torch.optim.Adam(trainable, lr=2e-3)

    # ============ RL loop ============
    episode_returns = []
    episode_log = []
    rng_rl = np.random.RandomState(seed + 47)
    end_phase1_gaps = None
    end_phase1_return = None
    end_phase1_episode = None
    aux_loss_log = []

    for ep in range(n_episodes):
        reward_fn = rwd_phase1 if ep < shift_at else rwd_phase2
        E = ENERGY_INIT
        log_probs = []
        rewards_arr = []
        aux_records = []  # (z, E_before, action_onehot, observed_delta_e)
        steps = 0

        while E > 0 and steps < T_MAX:
            obs_, col_, lab_, rew_ = sample_items(1, rng_rl, reward_fn)
            x = torch.from_numpy(obs_).float().to(device)
            z = encoder(x)
            e_t = torch.tensor([[E]], dtype=torch.float32, device=device)
            logits = policy_head(torch.cat([z, e_t], dim=-1))
            dist = torch.distributions.Categorical(logits=logits)
            action = int(dist.sample().item())
            log_probs.append(dist.log_prob(torch.tensor(action, device=device)))

            E_before = E
            E -= ENERGY_DECAY
            if action == 1:
                E = min(1.0, max(0.0, E + float(rew_[0])))
                step_reward = float(rew_[0])
            else:
                step_reward = 0.0
            observed_delta_e = E - E_before
            rewards_arr.append(step_reward)

            if aux_head is not None:
                a_onehot = torch.zeros(2, device=device)
                a_onehot[action] = 1.0
                aux_records.append((z.squeeze(0), torch.tensor(E_before, device=device),
                                    a_onehot, torch.tensor(observed_delta_e,
                                                          dtype=torch.float32, device=device)))
            steps += 1

        episode_returns.append(float(steps))
        # Compute discounted returns
        gamma = 0.99
        G = 0.0
        returns_disc = []
        for r in reversed(rewards_arr):
            G = r + gamma * G
            returns_disc.append(G)
        returns_disc.reverse()
        returns_t = torch.tensor(returns_disc, dtype=torch.float32, device=device)
        if len(returns_t) > 1:
            returns_t = (returns_t - returns_t.mean()) / (returns_t.std() + 1e-8)
        policy_loss = -(torch.stack(log_probs) * returns_t).mean()

        # Auxiliary ΔE loss
        if aux_head is not None and aux_records:
            zs = torch.stack([r[0] for r in aux_records])
            Es = torch.stack([r[1].unsqueeze(0) for r in aux_records])
            actions_oh = torch.stack([r[2] for r in aux_records])
            targets = torch.stack([r[3].unsqueeze(0) for r in aux_records]).squeeze(-1)
            aux_input = torch.cat([zs, Es, actions_oh], dim=-1)
            predicted_de = aux_head(aux_input).squeeze(-1)
            aux_loss = F.mse_loss(predicted_de, targets)
            total_loss = policy_loss + 0.5 * aux_loss
        else:
            aux_loss = None
            total_loss = policy_loss

        opt_rl.zero_grad()
        total_loss.backward()
        opt_rl.step()

        # snapshot end-of-phase-1 measurements (for shift envs)
        if ep == shift_at - 1 and env_phase1 != env_phase2:
            rng_snap = np.random.RandomState(seed + 100)
            obs_s, col_s, lab_s, rew_s = sample_items(
                test_samples, rng_snap, rwd_phase1,
            )
            with torch.no_grad():
                zs = encoder(torch.from_numpy(obs_s).to(device)).cpu().numpy()
            end_phase1_gaps = compute_cluster_gaps(zs, col_s, lab_s, rew_s)
            end_phase1_return = float(np.mean(episode_returns[-20:]))
            end_phase1_episode = ep

        if ep % max(1, n_episodes // 20) == 0 or ep == n_episodes - 1:
            episode_log.append(dict(
                episode=ep,
                steps=float(steps),
                reward_sum=float(sum(rewards_arr)),
                rolling_mean_steps=float(np.mean(episode_returns[-20:])),
                aux_loss=float(aux_loss.item()) if aux_loss is not None else None,
                phase=1 if ep < shift_at else 2,
            ))
        if aux_loss is not None and (ep % 100 == 0):
            aux_loss_log.append(dict(episode=ep, aux_loss=float(aux_loss.item())))

    # ============ Final cluster gaps (vs phase-2 reward fn) ============
    rng_test = np.random.RandomState(seed + 9999)
    obs_t, col_t, lab_t, rew_t = sample_items(
        test_samples, rng_test, rwd_phase2,
    )
    with torch.no_grad():
        zt = encoder(torch.from_numpy(obs_t).to(device)).cpu().numpy()
    final_gaps_phase2 = compute_cluster_gaps(zt, col_t, lab_t, rew_t)

    return dict(
        seed=seed,
        condition=condition,
        env_config=env_config,
        env_phase1=env_phase1,
        env_phase2=env_phase2,
        shift_at=shift_at,
        pretrain_log=pretrain_log,
        pretrained_cluster_gaps=pretrained_cluster_gaps,
        episode_log=episode_log,
        episode_returns=episode_returns,
        aux_loss_log=aux_loss_log,
        end_phase1_cluster_gaps=end_phase1_gaps,
        end_phase1_return=end_phase1_return,
        end_phase1_episode=end_phase1_episode,
        final_cluster_gaps=final_gaps_phase2,
        final_mean_return=float(np.mean(episode_returns[-20:])),
        # Save embeddings for PCA
        test_embeddings=zt.tolist(),
        test_colors=col_t.tolist(),
        test_labels=lab_t.tolist(),
        test_rewards=rew_t.tolist(),
    )


def compute_cluster_gaps(z, colors, labels, rewards):
    import numpy as np
    mean = z.mean(axis=0, keepdims=True)
    centered = z - mean
    norms = np.linalg.norm(centered, axis=1, keepdims=True)
    unit = centered / np.clip(norms, 1e-9, None)
    sim = unit @ unit.T

    def gap(arr):
        same = arr[:, None] == arr[None, :]
        diff = ~same
        np.fill_diagonal(same, False)
        return float(sim[same].mean() - sim[diff].mean())

    return dict(color=gap(colors), label=gap(labels), reward=gap(rewards))


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    pretrain_steps: int = 800,
    pretrain_batch: int = 64,
    n_episodes: int = 3000,
    test_samples: int = 512,
    out: str = "artifacts/concern_bootstrap/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]

    # Generate cell args. We want every (condition, env) cross EXCEPT
    # the rl_curriculum condition, which only makes sense in
    # add_to_xor_shift. For uniformity we still run rl_curriculum in
    # the stable envs (it just trains without a shift) so we have a
    # baseline curve.
    cell_args = []
    for sd in seed_list:
        for cond in ALL_CONDITIONS:
            for env in ALL_ENVS:
                cell_args.append(dict(
                    seed=sd, condition=cond, env_config=env,
                    pretrain_steps=pretrain_steps,
                    pretrain_batch=pretrain_batch,
                    n_episodes=n_episodes,
                    test_samples=test_samples,
                ))

    print(f"running {len(cell_args)} cells in parallel...")
    results = list(run_cell.map(cell_args))

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for r in results:
        gaps = r["final_cluster_gaps"]
        pre = r.get("pretrained_cluster_gaps")
        ph1 = r.get("end_phase1_cluster_gaps")
        summary_rows.append(dict(
            seed=r["seed"], condition=r["condition"],
            env_config=r["env_config"],
            final_color_gap=gaps["color"],
            final_label_gap=gaps["label"],
            final_reward_gap=gaps["reward"],
            final_mean_return=r["final_mean_return"],
            phase1_reward_gap=ph1["reward"] if ph1 else None,
            phase1_return=r.get("end_phase1_return"),
            pretrained_color_gap=pre["color"] if pre else None,
            pretrained_reward_gap=pre["reward"] if pre else None,
        ))

    out_path.write_text(json.dumps({
        "manifest": dict(
            seeds=seed_list,
            conditions=ALL_CONDITIONS,
            envs=ALL_ENVS,
            n_episodes=n_episodes,
            pretrain_steps=pretrain_steps,
            pretrain_batch=pretrain_batch,
            test_samples=test_samples,
            t_max=T_MAX, energy_decay=ENERGY_DECAY, energy_init=ENERGY_INIT,
            obs_noise=OBS_NOISE,
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nfinal summary ({len(summary_rows)} cells):")
    print(f"{'cond':<22} {'env':<22} {'seed':>10} | "
          f"{'reward_gap':>10} {'return':>8}")
    for r in summary_rows:
        print(f"  {r['condition']:<20} {r['env_config']:<20} {r['seed']:>10} | "
              f"{r['final_reward_gap']:>+10.4f} {r['final_mean_return']:>7.2f}")
