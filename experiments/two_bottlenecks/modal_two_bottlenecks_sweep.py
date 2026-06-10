#!/usr/bin/env python3
"""Paper 9 — Two Bottlenecks sweep.

Paper 8 found a decoupling cell: `rl_delta_e_aux` × `additive_stable`
achieved reward_gap +1.00 (encoder organized by reward axis) while
return stayed at 13 (policy never learned to exploit). The two
candidate explanations:

  (A) Encoder OK, policy was the bottleneck. With a *good* policy
      signal (supervised optimal-action labels), the same encoder
      should support competence.
  (B) Encoder was misleading. The +1.0 cluster_gap is geometric but
      not causally useful. Supervised policy training will also fail.

This sweep tests (A) vs (B). Six conditions, separating encoder and
policy training cleanly:

  - delta_e_then_freeze_sup_policy   : encoder via ΔE aux (random
                                       policy), freeze, train policy
                                       head with supervised optimal-
                                       action labels. HEADLINE.
  - delta_e_then_freeze_rl_policy    : same encoder, REINFORCE policy.
  - valence_then_freeze_sup_policy   : encoder via supervised valence
                                       (Paper 6), freeze, then train a
                                       NEW supervised policy head.
                                       UPPER BOUND.
  - random_freeze_sup_policy         : random init encoder (frozen),
                                       supervised policy. LOWER BOUND.
  - scratch_joint_sup_policy         : random init encoder + supervised
                                       policy, joint training. (Paper 6
                                       baseline.)
  - sensory_then_freeze_sup_policy   : encoder via color-prediction,
                                       freeze, supervised policy.
                                       PROXY CONTROL.

6 conditions × 2 envs (xor, additive_thresh) × 3 seeds = 36 cells.
~25 min on Modal CPU.

The policy is "supervised" in the sense that the optimal action
(consume iff reward > 0) is given as the cross-entropy target at every
state. There is no policy gradient on rewards; the policy is learning
a classification problem on top of the encoder's features.
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

app = modal.App(name="research-derived-two-bottlenecks")

N_COLORS = 4
N_LABELS = 2
ITEMS = [(c, l) for c in range(N_COLORS) for l in range(N_LABELS)]
EMBED_DIM = 32
OBS_NOISE = 0.15
T_MAX = 50
ENERGY_DECAY = 0.04
ENERGY_INIT = 0.5

ALL_CONDITIONS = [
    "delta_e_then_freeze_sup_policy",
    "delta_e_then_freeze_rl_policy",
    "valence_then_freeze_sup_policy",
    "random_freeze_sup_policy",
    "scratch_joint_sup_policy",
    "sensory_then_freeze_sup_policy",
]
ALL_ENVS = ["xor", "additive_thresh"]


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
    env_name: str = arg["env"]
    encoder_train_episodes: int = arg["encoder_train_episodes"]
    policy_train_steps: int = arg["policy_train_steps"]
    policy_train_batch: int = arg["policy_train_batch"]
    eval_episodes: int = arg["eval_episodes"]
    test_samples: int = arg["test_samples"]

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rng_env = np.random.RandomState(seed + 13)
    perm = rng_env.permutation(16)
    reward_fn = reward_fn_of(env_name)

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
        rewards = np.array([reward_fn(c, l) for c, l in zip(colors, labels)])
        obs = encode_obs(colors, labels, rng)
        return obs, colors, labels, rewards

    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)

    encoder_train_log = []
    policy_train_log = []

    # ============ STAGE 1: train (or set up) encoder ============
    if condition in ("delta_e_then_freeze_sup_policy",
                     "delta_e_then_freeze_rl_policy"):
        # Train encoder via action-conditioned ΔE aux head with random
        # uniform policy (no policy gradient on encoder; the only
        # encoder signal is the ΔE aux loss).
        aux_head = nn.Sequential(
            nn.Linear(EMBED_DIM + 1 + 2, 32), nn.Tanh(),
            nn.Linear(32, 1),
        ).to(device)
        opt_enc = torch.optim.Adam(
            list(encoder.parameters()) + list(aux_head.parameters()),
            lr=2e-3,
        )
        rng_rl = np.random.RandomState(seed + 47)
        for ep in range(encoder_train_episodes):
            E = ENERGY_INIT
            zs, energies, actions_oh, observed_des = [], [], [], []
            steps = 0
            while E > 0 and steps < T_MAX:
                obs_, _, _, rew_ = sample_items(1, rng_rl)
                x = torch.from_numpy(obs_).float().to(device)
                z = encoder(x).squeeze(0)
                # uniform random policy
                action = int(rng_rl.choice([0, 1]))
                E_before = E
                E -= ENERGY_DECAY
                if action == 1:
                    E = min(1.0, max(0.0, E + float(rew_[0])))
                observed_de = E - E_before

                a_oh = torch.zeros(2, device=device)
                a_oh[action] = 1.0
                zs.append(z)
                energies.append(torch.tensor(E_before, device=device))
                actions_oh.append(a_oh)
                observed_des.append(torch.tensor(observed_de,
                                                  dtype=torch.float32,
                                                  device=device))
                steps += 1
            if zs:
                z_stack = torch.stack(zs)
                e_stack = torch.stack(energies).unsqueeze(-1)
                a_stack = torch.stack(actions_oh)
                aux_input = torch.cat([z_stack, e_stack, a_stack], dim=-1)
                pred = aux_head(aux_input).squeeze(-1)
                targets = torch.stack(observed_des)
                loss = F.mse_loss(pred, targets)
                opt_enc.zero_grad(); loss.backward(); opt_enc.step()
                if ep % max(1, encoder_train_episodes // 20) == 0:
                    encoder_train_log.append(
                        dict(episode=ep, loss=float(loss.item()))
                    )

    elif condition == "valence_then_freeze_sup_policy":
        # Pretrain encoder via supervised optimal-action prediction
        head_pre = nn.Linear(EMBED_DIM, 2).to(device)
        opt_pre = torch.optim.Adam(
            list(encoder.parameters()) + list(head_pre.parameters()),
            lr=2e-3,
        )
        rng_pre = np.random.RandomState(seed + 23)
        for step in range(policy_train_steps // 2):
            obs, _, _, rewards = sample_items(policy_train_batch, rng_pre)
            x = torch.from_numpy(obs).to(device)
            z = encoder(x)
            logits = head_pre(z)
            target = torch.from_numpy((rewards > 0).astype(np.int64)).long().to(device)
            loss = F.cross_entropy(logits, target)
            opt_pre.zero_grad(); loss.backward(); opt_pre.step()
            if step % 50 == 0:
                encoder_train_log.append(
                    dict(step=step, loss=float(loss.item()))
                )

    elif condition == "sensory_then_freeze_sup_policy":
        head_pre = nn.Linear(EMBED_DIM, N_COLORS).to(device)
        opt_pre = torch.optim.Adam(
            list(encoder.parameters()) + list(head_pre.parameters()),
            lr=2e-3,
        )
        rng_pre = np.random.RandomState(seed + 23)
        for step in range(policy_train_steps // 2):
            obs, colors, _, _ = sample_items(policy_train_batch, rng_pre)
            x = torch.from_numpy(obs).to(device)
            z = encoder(x)
            logits = head_pre(z)
            target = torch.from_numpy(colors).long().to(device)
            loss = F.cross_entropy(logits, target)
            opt_pre.zero_grad(); loss.backward(); opt_pre.step()
            if step % 50 == 0:
                encoder_train_log.append(
                    dict(step=step, loss=float(loss.item()))
                )

    # random_freeze_sup_policy: encoder stays at random init.
    # scratch_joint_sup_policy: encoder gets trained jointly with the
    #   policy in stage 2.

    # ============ Measure encoder cluster gaps now (pre-policy-training) ============
    rng_pre_test = np.random.RandomState(seed + 333)
    obs_pre_t, col_pre_t, lab_pre_t, rew_pre_t = sample_items(
        test_samples, rng_pre_test
    )
    with torch.no_grad():
        z_pre = encoder(torch.from_numpy(obs_pre_t).to(device)).cpu().numpy()
    pretrained_gaps = compute_cluster_gaps(z_pre, col_pre_t, lab_pre_t, rew_pre_t)

    # ============ STAGE 2: train policy head ============
    # Freeze encoder for all "freeze" conditions
    if condition not in ("scratch_joint_sup_policy",):
        for p in encoder.parameters():
            p.requires_grad = False

    policy_head = nn.Sequential(
        nn.Linear(EMBED_DIM + 1, 32), nn.Tanh(),
        nn.Linear(32, 2),
    ).to(device)

    if condition == "delta_e_then_freeze_rl_policy":
        # REINFORCE
        opt_pol = torch.optim.Adam(policy_head.parameters(), lr=2e-3)
        rng_rl2 = np.random.RandomState(seed + 71)
        episode_returns_rl = []
        n_rl_episodes = policy_train_steps  # treat as episodes for parity
        for ep in range(n_rl_episodes):
            E = ENERGY_INIT
            log_probs = []
            rewards_arr = []
            steps = 0
            while E > 0 and steps < T_MAX:
                obs_, _, _, rew_ = sample_items(1, rng_rl2)
                x = torch.from_numpy(obs_).float().to(device)
                with torch.no_grad():
                    z = encoder(x)
                e_t = torch.tensor([[E]], dtype=torch.float32, device=device)
                logits = policy_head(torch.cat([z, e_t], dim=-1))
                dist = torch.distributions.Categorical(logits=logits)
                action = int(dist.sample().item())
                log_probs.append(dist.log_prob(torch.tensor(action, device=device)))
                E -= ENERGY_DECAY
                if action == 1:
                    E = min(1.0, max(0.0, E + float(rew_[0])))
                    step_reward = float(rew_[0])
                else:
                    step_reward = 0.0
                rewards_arr.append(step_reward)
                steps += 1
            episode_returns_rl.append(float(steps))
            gamma = 0.99
            G = 0.0
            returns_disc = []
            for r in reversed(rewards_arr):
                G = r + gamma * G
                returns_disc.append(G)
            returns_disc.reverse()
            rt = torch.tensor(returns_disc, dtype=torch.float32, device=device)
            if len(rt) > 1:
                rt = (rt - rt.mean()) / (rt.std() + 1e-8)
            loss = -(torch.stack(log_probs) * rt).mean()
            opt_pol.zero_grad(); loss.backward(); opt_pol.step()
            if ep % max(1, n_rl_episodes // 20) == 0:
                policy_train_log.append(
                    dict(episode=ep, return_mean=float(np.mean(episode_returns_rl[-20:])))
                )
    else:
        # Supervised policy training
        params = list(policy_head.parameters())
        if condition == "scratch_joint_sup_policy":
            params += list(encoder.parameters())
        opt_pol = torch.optim.Adam(params, lr=2e-3)
        rng_pol = np.random.RandomState(seed + 71)
        for step in range(policy_train_steps):
            obs, _, _, rewards = sample_items(policy_train_batch, rng_pol)
            x = torch.from_numpy(obs).to(device)
            if condition == "scratch_joint_sup_policy":
                z = encoder(x)
            else:
                with torch.no_grad():
                    z = encoder(x)
            # Sample a random energy state per item for the policy head
            energies = (rng_pol.rand(len(obs))).astype(np.float32)
            e_t = torch.from_numpy(energies).unsqueeze(-1).to(device)
            logits = policy_head(torch.cat([z, e_t], dim=-1))
            target = torch.from_numpy((rewards > 0).astype(np.int64)).long().to(device)
            loss = F.cross_entropy(logits, target)
            opt_pol.zero_grad(); loss.backward(); opt_pol.step()
            if step % max(1, policy_train_steps // 20) == 0:
                with torch.no_grad():
                    acc = (logits.argmax(-1) == target).float().mean().item()
                policy_train_log.append(
                    dict(step=step, loss=float(loss.item()), acc=float(acc))
                )

    # ============ STAGE 3: evaluate ============
    encoder.eval(); policy_head.eval()
    rng_eval = np.random.RandomState(seed + 9999)
    episode_returns = []
    for _ in range(eval_episodes):
        E = ENERGY_INIT
        steps = 0
        while E > 0 and steps < T_MAX:
            obs_, _, _, rew_ = sample_items(1, rng_eval)
            x = torch.from_numpy(obs_).float().to(device)
            with torch.no_grad():
                z = encoder(x)
                e_t = torch.tensor([[E]], dtype=torch.float32, device=device)
                logits = policy_head(torch.cat([z, e_t], dim=-1))
                action = int(logits.argmax(-1).item())
            E -= ENERGY_DECAY
            if action == 1:
                E = min(1.0, max(0.0, E + float(rew_[0])))
            steps += 1
        episode_returns.append(float(steps))

    # Final cluster gaps
    rng_test = np.random.RandomState(seed + 9998)
    obs_t, col_t, lab_t, rew_t = sample_items(test_samples, rng_test)
    with torch.no_grad():
        zt = encoder(torch.from_numpy(obs_t).to(device)).cpu().numpy()
    final_gaps = compute_cluster_gaps(zt, col_t, lab_t, rew_t)

    return dict(
        seed=seed,
        condition=condition,
        env=env_name,
        encoder_train_log=encoder_train_log,
        policy_train_log=policy_train_log,
        pretrained_cluster_gaps=pretrained_gaps,
        final_cluster_gaps=final_gaps,
        eval_mean_return=float(np.mean(episode_returns)),
        eval_max_return=float(np.max(episode_returns)),
        eval_min_return=float(np.min(episode_returns)),
        eval_episode_returns=episode_returns,
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
    encoder_train_episodes: int = 1500,
    policy_train_steps: int = 1500,
    policy_train_batch: int = 64,
    eval_episodes: int = 50,
    test_samples: int = 512,
    out: str = "artifacts/two_bottlenecks/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    cell_args = []
    for sd in seed_list:
        for cond in ALL_CONDITIONS:
            for env in ALL_ENVS:
                cell_args.append(dict(
                    seed=sd, condition=cond, env=env,
                    encoder_train_episodes=encoder_train_episodes,
                    policy_train_steps=policy_train_steps,
                    policy_train_batch=policy_train_batch,
                    eval_episodes=eval_episodes,
                    test_samples=test_samples,
                ))
    print(f"running {len(cell_args)} cells in parallel...")
    results = list(run_cell.map(cell_args))
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for r in results:
        pre = r["pretrained_cluster_gaps"]
        fin = r["final_cluster_gaps"]
        summary_rows.append(dict(
            seed=r["seed"], condition=r["condition"], env=r["env"],
            pre_reward_gap=pre["reward"],
            pre_color_gap=pre["color"],
            pre_label_gap=pre["label"],
            final_reward_gap=fin["reward"],
            final_color_gap=fin["color"],
            final_label_gap=fin["label"],
            eval_mean_return=r["eval_mean_return"],
        ))

    out_path.write_text(json.dumps({
        "manifest": dict(
            seeds=seed_list,
            conditions=ALL_CONDITIONS,
            envs=ALL_ENVS,
            encoder_train_episodes=encoder_train_episodes,
            policy_train_steps=policy_train_steps,
            policy_train_batch=policy_train_batch,
            eval_episodes=eval_episodes,
            t_max=T_MAX, energy_decay=ENERGY_DECAY, energy_init=ENERGY_INIT,
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nfinal summary ({len(summary_rows)} cells):")
    print(f"{'condition':<35} {'env':<18} {'seed':>10} | "
          f"{'pre_rg':>8} {'fin_rg':>8} {'return':>8}")
    for r in summary_rows:
        print(f"  {r['condition']:<33} {r['env']:<16} {r['seed']:>10} | "
              f"{r['pre_reward_gap']:>+.4f} {r['final_reward_gap']:>+.4f} "
              f"{r['eval_mean_return']:>7.2f}")
