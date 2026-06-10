#!/usr/bin/env python3
"""Paper 7 — Homeostatic Object Formation sweep.

Extends Paper 6 (Valence-Induced Object Formation) from a one-shot
supervised stand-in to an episodic homeostatic RL setting.

Environment.
  Each step the agent sees one item and decides consume / skip.
  Item observation is 16-dim with crossed (color × label) → reward
  structure as in Paper 6.
  Agent has internal energy E ∈ [0, 1], starting at 0.5.
  On every step: E -= delta (constant decay).
  On consume: E += reward(color, label), clipped to [0, 1].
  Episode ends when E ≤ 0 (failure) or step count reaches T_max.
  Episodic return = number of steps survived.

Agent.
  Encoder MLP 16 → 64 → 32 on the item observation only.
  Policy head: (embedding [32], energy [1]) → action logits [2].
  REINFORCE with whitened-return baseline.

Conditions (Law-of-the-Stack on prior representation):
  - rl_from_scratch        : random encoder init, joint encoder+head RL
  - rl_after_reconstruct   : pretrain encoder via reconstruction MSE
                             for KP steps, then joint encoder+head RL
  - rl_after_sensory       : pretrain encoder on color classification
                             for KP steps, then joint encoder+head RL
  - rl_frozen_reconstruct  : pretrain encoder via reconstruction,
                             then RL with encoder FROZEN (LoS: no
                             encoder slack remaining)
  - rl_frozen_sensory      : same, frozen after color pretraining

Measurements per cell.
  - Episode-return curve over RL training
  - Cluster gaps (color / label / reward axes) on a held-out test set
    using the final encoder
  - Final mean episodic return over last 20 episodes
  - For pretrained variants: the cluster gaps of the *pretrained*
    encoder, before RL begins.

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/homeostatic_objects/modal_homeostatic_sweep.py
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

app = modal.App(name="research-derived-homeostatic-objects")

N_COLORS = 4
N_LABELS = 2
ITEMS = [(c, l) for c in range(N_COLORS) for l in range(N_LABELS)]
EMBED_DIM = 32
OBS_NOISE = 0.15
T_MAX = 50
ENERGY_DECAY = 0.04
ENERGY_INIT = 0.5

ALL_CONDITIONS = [
    "rl_from_scratch",
    "rl_after_reconstruct",
    "rl_after_sensory",
    "rl_after_valence",
    "rl_frozen_reconstruct",
    "rl_frozen_sensory",
    "rl_frozen_valence",
]


@app.function(image=IMAGE, timeout=1200, cpu=4, memory=4096)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    seed: int = arg["seed"]
    condition: str = arg["condition"]
    reward_structure: str = arg["reward_structure"]
    pretrain_steps: int = arg["pretrain_steps"]
    pretrain_batch: int = arg["pretrain_batch"]
    n_episodes: int = arg["n_episodes"]
    test_samples: int = arg["test_samples"]

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rng_env = np.random.RandomState(seed + 13)

    def reward_of(color: int, label: int) -> float:
        if reward_structure == "xor":
            return 1.0 if ((color in (0, 1)) ^ (label == 0)) else -1.0
        elif reward_structure == "additive_thresh":
            return 1.0 if (color + (1 if label == 1 else -2)) > 0 else -1.0
        raise ValueError(reward_structure)

    # Stable obs permutation
    perm = rng_env.permutation(16)

    def encode_obs(colors, labels, rng):
        n = len(colors)
        obs = np.zeros((n, 16), dtype=np.float32)
        obs[np.arange(n), colors] = 1.0
        obs[np.arange(n), 8 + labels] = 1.0
        obs += rng.randn(n, 16).astype(np.float32) * OBS_NOISE
        return obs[:, perm]

    def sample_items(n, rng):
        idx = rng.randint(0, len(ITEMS), size=n)
        colors = np.array([ITEMS[i][0] for i in idx])
        labels = np.array([ITEMS[i][1] for i in idx])
        rewards = np.array([reward_of(c, l) for c, l in zip(colors, labels)])
        obs = encode_obs(colors, labels, rng)
        return obs, colors, labels, rewards

    # Build encoder
    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)

    # Optional pretraining
    pretrain_log = []
    pretrained_cluster_gaps = None
    if "after" in condition or "frozen" in condition:
        if "reconstruct" in condition:
            decoder = nn.Sequential(
                nn.Linear(EMBED_DIM, 64), nn.ReLU(),
                nn.Linear(64, 16),
            ).to(device)
            opt_pre = torch.optim.Adam(
                list(encoder.parameters()) + list(decoder.parameters()),
                lr=2e-3,
            )
            rng_pre = np.random.RandomState(seed + 23)
            for step in range(pretrain_steps):
                obs, _, _, _ = sample_items(pretrain_batch, rng_pre)
                x = torch.from_numpy(obs).to(device)
                z = encoder(x)
                recon = decoder(z)
                loss = F.mse_loss(recon, x)
                opt_pre.zero_grad()
                loss.backward()
                opt_pre.step()
                if step % 100 == 0 or step == pretrain_steps - 1:
                    pretrain_log.append(dict(step=step, loss=float(loss.item())))
        elif "sensory" in condition:
            head_pre = nn.Linear(EMBED_DIM, N_COLORS).to(device)
            opt_pre = torch.optim.Adam(
                list(encoder.parameters()) + list(head_pre.parameters()),
                lr=2e-3,
            )
            rng_pre = np.random.RandomState(seed + 23)
            for step in range(pretrain_steps):
                obs, colors, _, _ = sample_items(pretrain_batch, rng_pre)
                x = torch.from_numpy(obs).to(device)
                z = encoder(x)
                logits = head_pre(z)
                target = torch.from_numpy(colors).long().to(device)
                loss = F.cross_entropy(logits, target)
                opt_pre.zero_grad()
                loss.backward()
                opt_pre.step()
                if step % 100 == 0 or step == pretrain_steps - 1:
                    pretrain_log.append(dict(step=step, loss=float(loss.item())))
        elif "valence" in condition:
            # Pretrain on optimal-action prediction (Paper 6 objective).
            # This gives the encoder a reward-axis representation BEFORE RL.
            head_pre = nn.Linear(EMBED_DIM, 2).to(device)
            opt_pre = torch.optim.Adam(
                list(encoder.parameters()) + list(head_pre.parameters()),
                lr=2e-3,
            )
            rng_pre = np.random.RandomState(seed + 23)
            for step in range(pretrain_steps):
                obs, _, _, rewards = sample_items(pretrain_batch, rng_pre)
                x = torch.from_numpy(obs).to(device)
                z = encoder(x)
                logits = head_pre(z)
                # optimal action = consume (1) iff reward > 0
                optimal_action = (rewards > 0).astype(np.int64)
                target = torch.from_numpy(optimal_action).long().to(device)
                loss = F.cross_entropy(logits, target)
                opt_pre.zero_grad()
                loss.backward()
                opt_pre.step()
                if step % 100 == 0 or step == pretrain_steps - 1:
                    pretrain_log.append(dict(step=step, loss=float(loss.item())))
        # Measure pretrained cluster gaps on a held-out set
        rng_pre_test = np.random.RandomState(seed + 333)
        obs_t, col_t, lab_t, rew_t = sample_items(test_samples, rng_pre_test)
        with torch.no_grad():
            zt = encoder(torch.from_numpy(obs_t).to(device)).cpu().numpy()
        pretrained_cluster_gaps = compute_cluster_gaps(zt, col_t, lab_t, rew_t)

    # Freeze if needed
    if condition.startswith("rl_frozen"):
        for p in encoder.parameters():
            p.requires_grad = False

    # Policy head: (embedding [32], energy [1]) -> 2 logits
    policy_head = nn.Sequential(
        nn.Linear(EMBED_DIM + 1, 32), nn.Tanh(),
        nn.Linear(32, 2),
    ).to(device)

    trainable = (
        [p for p in encoder.parameters() if p.requires_grad]
        + list(policy_head.parameters())
    )
    opt_rl = torch.optim.Adam(trainable, lr=2e-3)

    def step_policy(obs_np, energy):
        x = torch.from_numpy(obs_np[None]).float().to(device)
        z = encoder(x)
        e_t = torch.tensor([[energy]], dtype=torch.float32, device=device)
        logits = policy_head(torch.cat([z, e_t], dim=-1))
        return torch.distributions.Categorical(logits=logits)

    # ====== RL loop ======
    episode_returns = []
    episode_log = []
    rng_rl = np.random.RandomState(seed + 47)
    for ep in range(n_episodes):
        E = ENERGY_INIT
        log_probs = []
        rewards = []
        steps = 0
        while E > 0 and steps < T_MAX:
            obs_, col_, lab_, rew_ = sample_items(1, rng_rl)
            dist = step_policy(obs_[0], E)
            action = int(dist.sample().item())
            log_probs.append(dist.log_prob(torch.tensor(action, device=device)))
            E -= ENERGY_DECAY
            if action == 1:  # consume
                E = min(1.0, max(0.0, E + float(rew_[0])))
                step_reward = float(rew_[0])
            else:
                step_reward = 0.0
            rewards.append(step_reward)
            steps += 1
        episode_returns.append(float(steps))
        # Compute discounted returns (gamma = 0.99) — but a simple sum works
        gamma = 0.99
        G = 0.0
        returns_arr = []
        for r in reversed(rewards):
            G = r + gamma * G
            returns_arr.append(G)
        returns_arr.reverse()
        returns_t = torch.tensor(returns_arr, dtype=torch.float32, device=device)
        if len(returns_t) > 1:
            returns_t = (returns_t - returns_t.mean()) / (returns_t.std() + 1e-8)
        loss = -(torch.stack(log_probs) * returns_t).mean()
        opt_rl.zero_grad()
        loss.backward()
        opt_rl.step()
        if ep % max(1, n_episodes // 20) == 0 or ep == n_episodes - 1:
            episode_log.append(dict(
                episode=ep,
                steps=float(steps),
                reward_sum=float(sum(rewards)),
                rolling_mean_steps=float(np.mean(episode_returns[-20:])),
            ))

    # ====== Final cluster gaps ======
    rng_test = np.random.RandomState(seed + 9999)
    obs_t, col_t, lab_t, rew_t = sample_items(test_samples, rng_test)
    with torch.no_grad():
        zt = encoder(torch.from_numpy(obs_t).to(device)).cpu().numpy()
    final_gaps = compute_cluster_gaps(zt, col_t, lab_t, rew_t)

    return dict(
        seed=seed,
        condition=condition,
        reward_structure=reward_structure,
        pretrain_log=pretrain_log,
        pretrained_cluster_gaps=pretrained_cluster_gaps,
        episode_log=episode_log,
        episode_returns=episode_returns,
        final_cluster_gaps=final_gaps,
        final_mean_return=float(np.mean(episode_returns[-20:])),
        final_max_return=float(np.max(episode_returns[-20:])),
        # For PCA in figures
        test_embeddings=zt.tolist(),
        test_colors=col_t.tolist(),
        test_labels=lab_t.tolist(),
        test_rewards=rew_t.tolist(),
    )


def compute_cluster_gaps(z, colors, labels, rewards):
    """Compute centered-cosine cluster gaps for color, label, reward axes."""
    import numpy as np
    mean = z.mean(axis=0, keepdims=True)
    centered = z - mean
    norms = np.linalg.norm(centered, axis=1, keepdims=True)
    unit = centered / np.clip(norms, 1e-9, None)
    sim = unit @ unit.T

    def gap(labels_arr):
        same = labels_arr[:, None] == labels_arr[None, :]
        diff = ~same
        np.fill_diagonal(same, False)
        return float(sim[same].mean() - sim[diff].mean())

    return dict(
        color=gap(colors),
        label=gap(labels),
        reward=gap(rewards),
    )


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    pretrain_steps: int = 800,
    pretrain_batch: int = 64,
    n_episodes: int = 800,
    test_samples: int = 512,
    out: str = "artifacts/homeostatic_objects/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    reward_structures = ["xor", "additive_thresh"]

    cell_args = []
    for sd in seed_list:
        for cond in ALL_CONDITIONS:
            for rs in reward_structures:
                cell_args.append(dict(
                    seed=sd, condition=cond, reward_structure=rs,
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
        summary_rows.append(dict(
            seed=r["seed"], condition=r["condition"],
            reward_structure=r["reward_structure"],
            final_color_gap=gaps["color"],
            final_label_gap=gaps["label"],
            final_reward_gap=gaps["reward"],
            pretrained_color_gap=pre["color"] if pre else None,
            pretrained_label_gap=pre["label"] if pre else None,
            pretrained_reward_gap=pre["reward"] if pre else None,
            final_mean_return=r["final_mean_return"],
        ))

    out_path.write_text(json.dumps({
        "manifest": dict(
            seeds=seed_list,
            conditions=ALL_CONDITIONS,
            reward_structures=reward_structures,
            pretrain_steps=pretrain_steps,
            pretrain_batch=pretrain_batch,
            n_episodes=n_episodes,
            test_samples=test_samples,
            t_max=T_MAX,
            energy_decay=ENERGY_DECAY,
            energy_init=ENERGY_INIT,
            obs_noise=OBS_NOISE,
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nfinal-snapshot summary ({len(summary_rows)} cells):")
    print(f"{'cond':<25} {'rs':<18} {'seed':>10} | "
          f"{'color':>8} {'label':>8} {'reward':>8} {'return':>8}")
    for r in summary_rows:
        print(f"  {r['condition']:<23} {r['reward_structure']:<16} {r['seed']:>10} | "
              f"{r['final_color_gap']:>+.4f} {r['final_label_gap']:>+.4f} "
              f"{r['final_reward_gap']:>+.4f} {r['final_mean_return']:>7.2f}")
