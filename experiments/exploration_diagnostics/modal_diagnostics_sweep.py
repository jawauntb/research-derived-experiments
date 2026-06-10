#!/usr/bin/env python3
"""Paper 11b — Exploration Diagnostics.

Diagnostic appendix to Paper 11. Three studies per condition × 3 seeds = 54
cells total (XOR only):

  - clean_default       : matches Paper 11 baseline. Clean init, σ=0.15
                          observation noise.
  - wrong_init          : ΔE head adversarially pretrained on FLIPPED
                          rewards (consume → -reward). Tests whether
                          each exploration mechanism can detect and
                          recover from a confidently-wrong starting
                          model.
  - high_noise          : σ=0.50 observation noise. Tests when novelty
                          mechanisms fail catastrophically and when
                          margin-based sampling becomes overconfident.

Each cell additionally logs (beyond Paper 11):
  - consume_mse + skip_mse + margin_mse + margin_sign_accuracy
  - aux head MSE trajectory across episodes

Conditions (same as Paper 11):
  biased_only / eps_greedy_decay / pred_error_curiosity /
  ensemble_disagree / expected_info_gain / uniform_random.

We rename `expected_info_gain` in the paper text to "margin-based
epistemic sampling" per reviewer guidance (the mechanism is a one-step
proxy for expected information gain, not a full EIG calculation). The
code name is kept for backward-compat with Paper 11.

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/exploration_diagnostics/modal_diagnostics_sweep.py
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

app = modal.App(name="research-derived-exploration-diagnostics")

N_COLORS = 4
N_LABELS = 2
ITEMS = [(c, l) for c in range(N_COLORS) for l in range(N_LABELS)]
EMBED_DIM = 32
T_MAX = 50
ENERGY_DECAY = 0.04
ENERGY_INIT = 0.5

ALL_CONDITIONS = [
    "biased_only",
    "eps_greedy_decay",
    "pred_error_curiosity",
    "ensemble_disagree",
    "expected_info_gain",
    "uniform_random",
]
ALL_VARIANTS = ["clean_default", "wrong_init", "high_noise"]


def reward_fn_xor():
    return lambda c, l: 1.0 if ((c in (0, 1)) ^ (l == 0)) else -1.0


@app.function(image=IMAGE, timeout=1800, cpu=4, memory=4096)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    seed: int = arg["seed"]
    condition: str = arg["condition"]
    variant: str = arg["variant"]
    encoder_train_episodes: int = arg["encoder_train_episodes"]
    eval_episodes: int = arg["eval_episodes"]
    test_samples: int = arg["test_samples"]
    bias_p_consume: float = arg["bias_p_consume"]
    wrong_init_steps: int = arg["wrong_init_steps"]

    # Variant toggles
    obs_noise = 0.50 if variant == "high_noise" else 0.15
    do_wrong_init = (variant == "wrong_init")

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rng_env = np.random.RandomState(seed + 13)
    perm = rng_env.permutation(16)
    reward_fn = reward_fn_xor()

    def encode_obs(colors, labels, rng):
        n = len(colors)
        obs = np.zeros((n, 16), dtype=np.float32)
        obs[np.arange(n), colors] = 1.0
        obs[np.arange(n), 8 + labels] = 1.0
        obs += rng.randn(n, 16).astype(np.float32) * obs_noise
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

    def make_head():
        return nn.Sequential(
            nn.Linear(EMBED_DIM + 1 + 2, 32), nn.Tanh(),
            nn.Linear(32, 1),
        ).to(device)

    if condition == "ensemble_disagree":
        torch.manual_seed(seed + 1001)
        aux_head2 = make_head()
        torch.manual_seed(seed)
        aux_head = make_head()
    else:
        aux_head = make_head()
        aux_head2 = None

    # ============ Optional wrong-init pretrain ============
    # Pretrain ΔE head on FLIPPED rewards: train it to predict -reward
    # instead of +reward for the consume action. Encoder unaffected.
    if do_wrong_init:
        params_pre = list(aux_head.parameters())
        if aux_head2 is not None:
            params_pre += list(aux_head2.parameters())
        opt_pre = torch.optim.Adam(params_pre, lr=2e-3)
        rng_pre = np.random.RandomState(seed + 23)
        for step in range(wrong_init_steps):
            obs, _, _, rewards = sample_items(64, rng_pre)
            x = torch.from_numpy(obs).to(device)
            with torch.no_grad():
                z = encoder(x)
            # FLIPPED targets: predicted ΔE for consume = -reward - decay
            # (the negation flips the optimal action)
            flipped_de_consume = (-rewards) - ENERGY_DECAY
            flipped_de_skip = np.full(len(rewards), -ENERGY_DECAY)
            # Train both branches
            e_t = torch.full((len(obs), 1), 0.5, device=device)
            a_oh_c = torch.zeros(len(obs), 2, device=device); a_oh_c[:, 1] = 1.0
            a_oh_s = torch.zeros(len(obs), 2, device=device); a_oh_s[:, 0] = 1.0
            t_c = torch.from_numpy(flipped_de_consume.astype(np.float32)).to(device)
            t_s = torch.from_numpy(flipped_de_skip.astype(np.float32)).to(device)
            pred_c = aux_head(torch.cat([z, e_t, a_oh_c], -1)).squeeze(-1)
            pred_s = aux_head(torch.cat([z, e_t, a_oh_s], -1)).squeeze(-1)
            loss = F.mse_loss(pred_c, t_c) + F.mse_loss(pred_s, t_s)
            if aux_head2 is not None:
                pred_c2 = aux_head2(torch.cat([z, e_t, a_oh_c], -1)).squeeze(-1)
                pred_s2 = aux_head2(torch.cat([z, e_t, a_oh_s], -1)).squeeze(-1)
                loss = loss + F.mse_loss(pred_c2, t_c) + F.mse_loss(pred_s2, t_s)
            opt_pre.zero_grad(); loss.backward(); opt_pre.step()

    if aux_head2 is not None:
        params = (list(encoder.parameters()) + list(aux_head.parameters())
                  + list(aux_head2.parameters()))
    else:
        params = list(encoder.parameters()) + list(aux_head.parameters())
    opt = torch.optim.Adam(params, lr=2e-3)

    rng_rl = np.random.RandomState(seed + 47)
    pred_err_running = 0.5
    aux_loss_traj = []

    def choose_action(z_unsq, E, episode_idx):
        nonlocal pred_err_running
        if condition == "biased_only":
            return 1 if rng_rl.rand() < bias_p_consume else 0
        elif condition == "uniform_random":
            return int(rng_rl.choice([0, 1]))
        elif condition == "eps_greedy_decay":
            eps = max(0.05, 1.0 - (episode_idx / encoder_train_episodes) * 0.95)
            if rng_rl.rand() < eps:
                return int(rng_rl.choice([0, 1]))
            with torch.no_grad():
                e_t = torch.tensor([[E]], dtype=torch.float32, device=device)
                a_oh_c = torch.tensor([[0.0, 1.0]], device=device)
                a_oh_s = torch.tensor([[1.0, 0.0]], device=device)
                pred_c = aux_head(torch.cat([z_unsq, e_t, a_oh_c], -1)).item()
                pred_s = aux_head(torch.cat([z_unsq, e_t, a_oh_s], -1)).item()
            return 1 if pred_c > pred_s else 0
        elif condition == "pred_error_curiosity":
            curiosity_eps = max(0.05, min(0.95, pred_err_running))
            if rng_rl.rand() < curiosity_eps:
                return int(rng_rl.choice([0, 1]))
            with torch.no_grad():
                e_t = torch.tensor([[E]], dtype=torch.float32, device=device)
                a_oh_c = torch.tensor([[0.0, 1.0]], device=device)
                a_oh_s = torch.tensor([[1.0, 0.0]], device=device)
                pred_c = aux_head(torch.cat([z_unsq, e_t, a_oh_c], -1)).item()
                pred_s = aux_head(torch.cat([z_unsq, e_t, a_oh_s], -1)).item()
            return 1 if pred_c > pred_s else 0
        elif condition == "ensemble_disagree":
            with torch.no_grad():
                e_t = torch.tensor([[E]], dtype=torch.float32, device=device)
                a_oh_c = torch.tensor([[0.0, 1.0]], device=device)
                a_oh_s = torch.tensor([[1.0, 0.0]], device=device)
                p1_c = aux_head(torch.cat([z_unsq, e_t, a_oh_c], -1)).item()
                p2_c = aux_head2(torch.cat([z_unsq, e_t, a_oh_c], -1)).item()
                p1_s = aux_head(torch.cat([z_unsq, e_t, a_oh_s], -1)).item()
                p2_s = aux_head2(torch.cat([z_unsq, e_t, a_oh_s], -1)).item()
                disagree = abs(p1_c - p2_c) + abs(p1_s - p2_s)
            ex_p = max(0.05, min(0.95, disagree / 2.0 + 0.05))
            if rng_rl.rand() < ex_p:
                return int(rng_rl.choice([0, 1]))
            mean_c = 0.5 * (p1_c + p2_c)
            mean_s = 0.5 * (p1_s + p2_s)
            return 1 if mean_c > mean_s else 0
        elif condition == "expected_info_gain":
            with torch.no_grad():
                e_t = torch.tensor([[E]], dtype=torch.float32, device=device)
                a_oh_c = torch.tensor([[0.0, 1.0]], device=device)
                a_oh_s = torch.tensor([[1.0, 0.0]], device=device)
                pred_c = aux_head(torch.cat([z_unsq, e_t, a_oh_c], -1)).item()
                pred_s = aux_head(torch.cat([z_unsq, e_t, a_oh_s], -1)).item()
            margin = abs(pred_c - pred_s)
            ex_p = max(0.05, min(0.95, 1.0 - margin / 2.0))
            if rng_rl.rand() < ex_p:
                return int(rng_rl.choice([0, 1]))
            return 1 if pred_c > pred_s else 0
        else:
            raise ValueError(condition)

    for ep in range(encoder_train_episodes):
        E = ENERGY_INIT
        zs, energies, actions_oh, observed_des = [], [], [], []
        steps = 0
        while E > 0 and steps < T_MAX:
            obs_, _, _, rew_ = sample_items(1, rng_rl)
            x = torch.from_numpy(obs_).float().to(device)
            z = encoder(x).squeeze(0)
            z_unsq = z.unsqueeze(0)
            action = choose_action(z_unsq, E, ep)
            E_before = E
            E -= ENERGY_DECAY
            if action == 1:
                E = min(1.0, max(0.0, E + float(rew_[0])))
            observed_de = E - E_before
            with torch.no_grad():
                a_oh_now = torch.zeros(1, 2, device=device); a_oh_now[0, action] = 1.0
                e_t = torch.tensor([[E_before]], dtype=torch.float32, device=device)
                pred_de = aux_head(torch.cat([z_unsq, e_t, a_oh_now], -1)).item()
            pred_err_running = 0.95 * pred_err_running + 0.05 * abs(observed_de - pred_de)

            a_oh = torch.zeros(2, device=device); a_oh[action] = 1.0
            zs.append(z); energies.append(torch.tensor(E_before, device=device))
            actions_oh.append(a_oh)
            observed_des.append(torch.tensor(observed_de, dtype=torch.float32, device=device))
            steps += 1

        if zs:
            z_stack = torch.stack(zs)
            e_stack = torch.stack(energies).unsqueeze(-1)
            a_stack = torch.stack(actions_oh)
            targets = torch.stack(observed_des)
            aux_input = torch.cat([z_stack, e_stack, a_stack], dim=-1)
            pred = aux_head(aux_input).squeeze(-1)
            loss = F.mse_loss(pred, targets)
            if aux_head2 is not None:
                idx = torch.randperm(len(zs))[:max(1, len(zs) // 2)]
                pred2 = aux_head2(aux_input[idx]).squeeze(-1)
                loss = loss + F.mse_loss(pred2, targets[idx])
            opt.zero_grad(); loss.backward(); opt.step()
            if ep % max(1, encoder_train_episodes // 20) == 0:
                aux_loss_traj.append(dict(episode=ep, loss=float(loss.item())))

    # ============ Cluster gaps ============
    rng_test = np.random.RandomState(seed + 9998)
    obs_t, col_t, lab_t, rew_t = sample_items(test_samples, rng_test)
    with torch.no_grad():
        zt = encoder(torch.from_numpy(obs_t).to(device)).cpu().numpy()
    cluster_gaps = compute_cluster_gaps(zt, col_t, lab_t, rew_t)

    # ============ Extended calibration (consume + skip + margin) ============
    n_cal = min(256, len(obs_t))
    with torch.no_grad():
        z_cal = encoder(torch.from_numpy(obs_t[:n_cal]).to(device))
    fixed_E = torch.full((n_cal, 1), 0.5, device=device)
    a_consume = torch.zeros(n_cal, 2, device=device); a_consume[:, 1] = 1.0
    a_skip = torch.zeros(n_cal, 2, device=device); a_skip[:, 0] = 1.0
    with torch.no_grad():
        pred_de_consume = aux_head(torch.cat([z_cal, fixed_E, a_consume], -1)).squeeze(-1).cpu().numpy()
        pred_de_skip = aux_head(torch.cat([z_cal, fixed_E, a_skip], -1)).squeeze(-1).cpu().numpy()
    true_de_skip = np.full(n_cal, -ENERGY_DECAY)
    true_de_consume = np.clip(0.5 + rew_t[:n_cal], 0, 1) - 0.5 - ENERGY_DECAY
    consume_mse = float(np.mean((pred_de_consume - true_de_consume) ** 2))
    skip_mse = float(np.mean((pred_de_skip - true_de_skip) ** 2))
    pred_margin = pred_de_consume - pred_de_skip
    true_margin = true_de_consume - true_de_skip
    margin_mse = float(np.mean((pred_margin - true_margin) ** 2))
    margin_sign_acc = float(np.mean(np.sign(pred_margin) == np.sign(true_margin)))

    # ============ Greedy eval ============
    encoder.eval(); aux_head.eval()
    rng_eval = np.random.RandomState(seed + 9999)
    episode_returns = []
    action_acc_records = []
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
                a_oh_c = torch.tensor([[0.0, 1.0]], device=device)
                a_oh_s = torch.tensor([[1.0, 0.0]], device=device)
                pred_c = aux_head(torch.cat([z, e_t, a_oh_c], -1)).item()
                pred_s = aux_head(torch.cat([z, e_t, a_oh_s], -1)).item()
                action = 1 if pred_c > pred_s else 0
            action_acc_records.append(int(action == optimal_action))
            E -= ENERGY_DECAY
            if action == 1:
                E = min(1.0, max(0.0, E + float(rew_[0])))
            steps += 1
        episode_returns.append(float(steps))

    return dict(
        seed=seed,
        condition=condition,
        variant=variant,
        obs_noise=obs_noise,
        cluster_gaps=cluster_gaps,
        mean_return=float(np.mean(episode_returns)),
        action_accuracy=float(np.mean(action_acc_records)),
        episode_returns=episode_returns,
        consume_mse=consume_mse,
        skip_mse=skip_mse,
        margin_mse=margin_mse,
        margin_sign_acc=margin_sign_acc,
        aux_loss_traj=aux_loss_traj,
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
    eval_episodes: int = 50,
    test_samples: int = 512,
    bias_p_consume: float = 0.95,
    wrong_init_steps: int = 200,
    out: str = "artifacts/exploration_diagnostics/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    cell_args = []
    for sd in seed_list:
        for cond in ALL_CONDITIONS:
            for variant in ALL_VARIANTS:
                cell_args.append(dict(
                    seed=sd, condition=cond, variant=variant,
                    encoder_train_episodes=encoder_train_episodes,
                    eval_episodes=eval_episodes,
                    test_samples=test_samples,
                    bias_p_consume=bias_p_consume,
                    wrong_init_steps=wrong_init_steps,
                ))
    print(f"running {len(cell_args)} cells in parallel...")
    results = list(run_cell.map(cell_args))
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for r in results:
        summary_rows.append(dict(
            seed=r["seed"], condition=r["condition"], variant=r["variant"],
            obs_noise=r["obs_noise"],
            reward_gap=r["cluster_gaps"]["reward"],
            color_gap=r["cluster_gaps"]["color"],
            label_gap=r["cluster_gaps"]["label"],
            mean_return=r["mean_return"],
            action_accuracy=r["action_accuracy"],
            consume_mse=r["consume_mse"],
            skip_mse=r["skip_mse"],
            margin_mse=r["margin_mse"],
            margin_sign_acc=r["margin_sign_acc"],
        ))

    out_path.write_text(json.dumps({
        "manifest": dict(
            seeds=seed_list, conditions=ALL_CONDITIONS, variants=ALL_VARIANTS,
            encoder_train_episodes=encoder_train_episodes,
            eval_episodes=eval_episodes, bias_p_consume=bias_p_consume,
            wrong_init_steps=wrong_init_steps,
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nsummary ({len(summary_rows)} cells):")
    print(f"{'condition':<24} {'variant':<16} {'seed':>10} | "
          f"{'rg':>7} {'ret':>6} {'acc':>5} {'cMSE':>6} {'sMSE':>6} {'mMSE':>6} {'msACC':>6}")
    for r in summary_rows:
        print(f"  {r['condition']:<22} {r['variant']:<14} {r['seed']:>10} | "
              f"{r['reward_gap']:>+.3f} {r['mean_return']:>5.1f} "
              f"{r['action_accuracy']:>4.2f} {r['consume_mse']:>5.3f} "
              f"{r['skip_mse']:>5.3f} {r['margin_mse']:>5.3f} "
              f"{r['margin_sign_acc']:>5.3f}")
