#!/usr/bin/env python3
"""Paper 10 — Planning from Concern sweep.

Tests whether a ΔE-aux-organized encoder + ΔE prediction head supports
COMPETENT homeostatic action via model-based planning — argmax_a
ΔE_head(z, E, a) — without any supervised optimal-action labels and
without policy gradient training.

This directly tests the "two-bottleneck" hypothesis from Paper 9: if
both bottlenecks (encoder organization, policy training signal) can be
solved by interaction-grounded prediction, then concern-shaped agency
can be fully self-organized.

Conditions (6):

  - model_plan_delta_e         : Stage 1 trains encoder + ΔE head via
                                 action-conditioned MSE on observed ΔE,
                                 actions sampled uniformly at random.
                                 Stage 2 acts greedily as
                                 a* = argmax_a ΔE_head(z, E, a).
                                 HEADLINE: full self-organization, no
                                 policy gradient, no supervised labels.
  - model_plan_random_encoder  : Random init encoder (frozen). Train
                                 only ΔE head on observed ΔE. Plan via
                                 argmax. LOWER BOUND.
  - model_plan_sensory_encoder : Sensory-pretrained encoder (frozen).
                                 Train ΔE head, then plan.
  - model_plan_valence_encoder : Supervised-valence-pretrained encoder
                                 (frozen). Train ΔE head, then plan.
                                 UPPER-BOUND-LIKE.
  - distilled_policy_from_model : Train ΔE encoder + head; use model
                                 argmax as supervised labels for a
                                 *new* policy head. Eval with policy.
                                 Tests the planning→policy distillation
                                 pipeline.
  - delta_e_then_supervised_policy : Paper 9 baseline (frozen ΔE
                                 encoder + supervised policy from oracle
                                 optimal-action labels).

6 × 2 envs (xor, additive_thresh) × 3 seeds = 36 cells.

Pre-registered gates:
  G1 No-label competence: model_plan_delta_e reaches return ≥ 45/50 on
     XOR without supervised optimal-action labels.
  G2 Encoder necessity: model_plan_delta_e > model_plan_random_encoder
     by ≥ 15 return points on XOR.
  G3 Planning↔distillation parity: distilled_policy_from_model
     ≈ model_plan_delta_e (within 5 return points).
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

app = modal.App(name="research-derived-planning-concern")

N_COLORS = 4
N_LABELS = 2
ITEMS = [(c, l) for c in range(N_COLORS) for l in range(N_LABELS)]
EMBED_DIM = 32
OBS_NOISE = 0.15
T_MAX = 50
ENERGY_DECAY = 0.04
ENERGY_INIT = 0.5

ALL_CONDITIONS = [
    "model_plan_delta_e",
    "model_plan_random_encoder",
    "model_plan_sensory_encoder",
    "model_plan_valence_encoder",
    "distilled_policy_from_model",
    "delta_e_then_supervised_policy",
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
    pretrain_steps: int = arg["pretrain_steps"]
    pretrain_batch: int = arg["pretrain_batch"]

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

    # ============ STAGE 1a: optional encoder pretrain ============
    encoder_train_log = []
    if condition == "model_plan_sensory_encoder":
        head_pre = nn.Linear(EMBED_DIM, N_COLORS).to(device)
        opt_pre = torch.optim.Adam(
            list(encoder.parameters()) + list(head_pre.parameters()), lr=2e-3,
        )
        rng_pre = np.random.RandomState(seed + 23)
        for step in range(pretrain_steps):
            obs, colors, _, _ = sample_items(pretrain_batch, rng_pre)
            x = torch.from_numpy(obs).to(device)
            z = encoder(x)
            logits = head_pre(z)
            target = torch.from_numpy(colors).long().to(device)
            loss = F.cross_entropy(logits, target)
            opt_pre.zero_grad(); loss.backward(); opt_pre.step()
            if step % 100 == 0:
                encoder_train_log.append(dict(step=step, loss=float(loss.item())))
    elif condition == "model_plan_valence_encoder":
        head_pre = nn.Linear(EMBED_DIM, 2).to(device)
        opt_pre = torch.optim.Adam(
            list(encoder.parameters()) + list(head_pre.parameters()), lr=2e-3,
        )
        rng_pre = np.random.RandomState(seed + 23)
        for step in range(pretrain_steps):
            obs, _, _, rewards = sample_items(pretrain_batch, rng_pre)
            x = torch.from_numpy(obs).to(device)
            z = encoder(x)
            logits = head_pre(z)
            target = torch.from_numpy((rewards > 0).astype(np.int64)).long().to(device)
            loss = F.cross_entropy(logits, target)
            opt_pre.zero_grad(); loss.backward(); opt_pre.step()
            if step % 100 == 0:
                encoder_train_log.append(dict(step=step, loss=float(loss.item())))
    # model_plan_random_encoder: no pretrain
    # model_plan_delta_e / distilled / delta_e_then_supervised: encoder
    # trained via ΔE aux in stage 1b below

    # For random encoder, freeze immediately
    if condition == "model_plan_random_encoder":
        for p in encoder.parameters():
            p.requires_grad = False
    # For sensory/valence pretrain encoders, freeze after pretrain
    elif condition in ("model_plan_sensory_encoder", "model_plan_valence_encoder"):
        for p in encoder.parameters():
            p.requires_grad = False

    # ============ STAGE 1b: ΔE auxiliary head ============
    aux_head = nn.Sequential(
        nn.Linear(EMBED_DIM + 1 + 2, 32), nn.Tanh(),
        nn.Linear(32, 1),
    ).to(device)

    if condition in ("model_plan_delta_e", "distilled_policy_from_model",
                     "delta_e_then_supervised_policy"):
        # Encoder + ΔE head joint training under uniform random policy
        params = list(encoder.parameters()) + list(aux_head.parameters())
    else:
        # Encoder frozen; train only ΔE head
        params = list(aux_head.parameters())

    opt_aux = torch.optim.Adam(params, lr=2e-3)
    rng_rl = np.random.RandomState(seed + 47)
    aux_train_log = []
    for ep in range(encoder_train_episodes):
        E = ENERGY_INIT
        zs, energies, actions_oh, observed_des = [], [], [], []
        steps = 0
        while E > 0 and steps < T_MAX:
            obs_, _, _, rew_ = sample_items(1, rng_rl)
            x = torch.from_numpy(obs_).float().to(device)
            z = encoder(x).squeeze(0)
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
            observed_des.append(torch.tensor(observed_de, dtype=torch.float32, device=device))
            steps += 1
        if zs:
            z_stack = torch.stack(zs)
            e_stack = torch.stack(energies).unsqueeze(-1)
            a_stack = torch.stack(actions_oh)
            aux_input = torch.cat([z_stack, e_stack, a_stack], dim=-1)
            pred = aux_head(aux_input).squeeze(-1)
            targets = torch.stack(observed_des)
            loss = F.mse_loss(pred, targets)
            opt_aux.zero_grad(); loss.backward(); opt_aux.step()
            if ep % max(1, encoder_train_episodes // 20) == 0:
                aux_train_log.append(dict(episode=ep, loss=float(loss.item())))

    # Freeze encoder for the planning conditions (after ΔE aux)
    if condition == "model_plan_delta_e":
        for p in encoder.parameters():
            p.requires_grad = False

    # Measure encoder cluster gaps
    rng_pre_test = np.random.RandomState(seed + 333)
    obs_t, col_t, lab_t, rew_t = sample_items(test_samples, rng_pre_test)
    with torch.no_grad():
        zt = encoder(torch.from_numpy(obs_t).to(device)).cpu().numpy()
    cluster_gaps = compute_cluster_gaps(zt, col_t, lab_t, rew_t)

    # ============ STAGE 2: action policy ============
    policy_head = None  # only used for non-planning conditions

    if condition.startswith("model_plan_"):
        # No policy head. Action = argmax_a ΔE_head(z, E, a)
        pass

    elif condition == "distilled_policy_from_model":
        # Train policy head via supervised distillation from the model's
        # argmax. The labels come from the model itself, not the oracle.
        for p in encoder.parameters():
            p.requires_grad = False
        for p in aux_head.parameters():
            p.requires_grad = False
        policy_head = nn.Sequential(
            nn.Linear(EMBED_DIM + 1, 32), nn.Tanh(),
            nn.Linear(32, 2),
        ).to(device)
        opt_pol = torch.optim.Adam(policy_head.parameters(), lr=2e-3)
        rng_pol = np.random.RandomState(seed + 71)
        for step in range(policy_train_steps):
            obs, _, _, _ = sample_items(policy_train_batch, rng_pol)
            energies_arr = rng_pol.rand(len(obs)).astype(np.float32)
            x = torch.from_numpy(obs).to(device)
            with torch.no_grad():
                z = encoder(x)
                e_t = torch.from_numpy(energies_arr).unsqueeze(-1).to(device)
                # Compute predicted ΔE for both actions; argmax is the
                # "model label."
                a_oh_consume = torch.zeros(len(obs), 2, device=device)
                a_oh_consume[:, 1] = 1.0
                a_oh_skip = torch.zeros(len(obs), 2, device=device)
                a_oh_skip[:, 0] = 1.0
                pred_de_consume = aux_head(torch.cat([z, e_t, a_oh_consume], -1)).squeeze(-1)
                pred_de_skip = aux_head(torch.cat([z, e_t, a_oh_skip], -1)).squeeze(-1)
                model_label = (pred_de_consume > pred_de_skip).long()
            logits = policy_head(torch.cat([z, e_t], -1))
            loss = F.cross_entropy(logits, model_label)
            opt_pol.zero_grad(); loss.backward(); opt_pol.step()

    elif condition == "delta_e_then_supervised_policy":
        # Paper 9 baseline: supervised optimal-action labels
        for p in encoder.parameters():
            p.requires_grad = False
        policy_head = nn.Sequential(
            nn.Linear(EMBED_DIM + 1, 32), nn.Tanh(),
            nn.Linear(32, 2),
        ).to(device)
        opt_pol = torch.optim.Adam(policy_head.parameters(), lr=2e-3)
        rng_pol = np.random.RandomState(seed + 71)
        for step in range(policy_train_steps):
            obs, _, _, rewards = sample_items(policy_train_batch, rng_pol)
            energies_arr = rng_pol.rand(len(obs)).astype(np.float32)
            x = torch.from_numpy(obs).to(device)
            with torch.no_grad():
                z = encoder(x)
            e_t = torch.from_numpy(energies_arr).unsqueeze(-1).to(device)
            logits = policy_head(torch.cat([z, e_t], -1))
            target = torch.from_numpy((rewards > 0).astype(np.int64)).long().to(device)
            loss = F.cross_entropy(logits, target)
            opt_pol.zero_grad(); loss.backward(); opt_pol.step()

    # ============ STAGE 3: greedy eval ============
    encoder.eval()
    aux_head.eval()
    if policy_head is not None:
        policy_head.eval()
    rng_eval = np.random.RandomState(seed + 9999)
    episode_returns = []
    action_acc_records = []  # whether agent took the optimal action
    for _ in range(eval_episodes):
        E = ENERGY_INIT
        steps = 0
        while E > 0 and steps < T_MAX:
            obs_, _, _, rew_ = sample_items(1, rng_eval)
            x = torch.from_numpy(obs_).float().to(device)
            optimal_action = 1 if rew_[0] > 0 else 0
            with torch.no_grad():
                z = encoder(x)
                e_t = torch.tensor([[E]], dtype=torch.float32, device=device)
                if condition.startswith("model_plan_"):
                    # argmax_a ΔE_head
                    a_oh_consume = torch.tensor([[0.0, 1.0]], device=device)
                    a_oh_skip = torch.tensor([[1.0, 0.0]], device=device)
                    pred_consume = aux_head(torch.cat([z, e_t, a_oh_consume], -1)).item()
                    pred_skip = aux_head(torch.cat([z, e_t, a_oh_skip], -1)).item()
                    action = 1 if pred_consume > pred_skip else 0
                else:
                    logits = policy_head(torch.cat([z, e_t], -1))
                    action = int(logits.argmax(-1).item())
            action_acc_records.append(int(action == optimal_action))
            E -= ENERGY_DECAY
            if action == 1:
                E = min(1.0, max(0.0, E + float(rew_[0])))
            steps += 1
        episode_returns.append(float(steps))

    # Final encoder geometry (post all training)
    rng_test = np.random.RandomState(seed + 9998)
    obs_t2, col_t2, lab_t2, rew_t2 = sample_items(test_samples, rng_test)
    with torch.no_grad():
        zt2 = encoder(torch.from_numpy(obs_t2).to(device)).cpu().numpy()
    final_cluster_gaps = compute_cluster_gaps(zt2, col_t2, lab_t2, rew_t2)

    return dict(
        seed=seed,
        condition=condition,
        env=env_name,
        encoder_train_log=encoder_train_log,
        aux_train_log=aux_train_log,
        pretrained_cluster_gaps=cluster_gaps,
        final_cluster_gaps=final_cluster_gaps,
        eval_mean_return=float(np.mean(episode_returns)),
        eval_max_return=float(np.max(episode_returns)),
        eval_min_return=float(np.min(episode_returns)),
        eval_episode_returns=episode_returns,
        eval_action_accuracy=float(np.mean(action_acc_records)),
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
    pretrain_steps: int = 800,
    pretrain_batch: int = 64,
    out: str = "artifacts/planning_from_concern/sweep_v1.json",
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
                    pretrain_steps=pretrain_steps,
                    pretrain_batch=pretrain_batch,
                ))
    print(f"running {len(cell_args)} cells in parallel...")
    results = list(run_cell.map(cell_args))
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for r in results:
        gaps = r["final_cluster_gaps"]
        summary_rows.append(dict(
            seed=r["seed"], condition=r["condition"], env=r["env"],
            final_reward_gap=gaps["reward"],
            final_color_gap=gaps["color"],
            final_label_gap=gaps["label"],
            eval_mean_return=r["eval_mean_return"],
            eval_action_accuracy=r["eval_action_accuracy"],
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
    print(f"{'condition':<40} {'env':<18} {'seed':>10} | "
          f"{'rg':>8} {'return':>7} {'acc':>6}")
    for r in summary_rows:
        print(f"  {r['condition']:<38} {r['env']:<16} {r['seed']:>10} | "
              f"{r['final_reward_gap']:>+.4f} {r['eval_mean_return']:>6.2f} "
              f"{r['eval_action_accuracy']:>5.3f}")
