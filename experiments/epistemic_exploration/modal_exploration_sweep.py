#!/usr/bin/env python3
"""Paper 11 — Epistemic Exploration for Biased-Policy Recovery.

Paper 10b found that the model_plan_delta_e pipeline succeeds under
uniform random and ε-greedy exploration but collapses under fully-
biased exploration (always consume → XOR acc 0.491). The encoder
still organizes by reward (rg +1.80), but the ΔE head never observes
the skip action, so its argmax becomes ill-defined.

This paper asks: can a homeostatic agent recover full competence
under a biased *initial* policy by using intrinsic epistemic
exploration mechanisms, without requiring experimenter-supplied
uniform action probabilities?

Six conditions, all starting from a "biased consume" prior
(initial p(consume)=0.95). They differ in how the action is
chosen during ΔE-aux training:

  - biased_only         : always consume, no exploration. FAILURE
                          BASELINE.
  - eps_greedy_decay    : ε starts at 1.0, decays linearly to 0.05
                          over training. Simple stochastic coverage.
  - pred_error_curiosity: ICM-style. The agent maintains a ΔE
                          prediction model and computes |observed - predicted|
                          after each step. With probability proportional
                          to a moving average of recent prediction error,
                          take a uniform-random action. Otherwise take
                          the action with higher predicted ΔE.
  - ensemble_disagree   : Bootstrap-DQN style. Maintain two ΔE heads
                          with different random init / bootstrap samples.
                          Each step, sample uniformly at random with
                          probability proportional to the heads'
                          disagreement on the predicted ΔE for the
                          current item × current energy. Otherwise greedy.
  - expected_info_gain  : Active-inference flavored. Sample action
                          with probability proportional to entropy of
                          the model's predicted-best-action distribution
                          across recent items. Otherwise greedy.
  - uniform_random      : POSITIVE CONTROL (matches Paper 10).

6 conditions × 2 envs (xor, additive_thresh) × 3 seeds = 36 cells.

Pre-registered gates:
  G1 — biased_only XOR acc ≤ 0.55 (recall of Paper 10b failure)
  G2 — uniform_random XOR acc ≥ 0.95 (Paper 10 positive control)
  G3 — AT LEAST ONE intrinsic mechanism (pred_error_curiosity /
       ensemble_disagree / expected_info_gain) reaches XOR acc ≥ 0.90
       starting from the biased prior.

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/epistemic_exploration/modal_exploration_sweep.py
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

app = modal.App(name="research-derived-epistemic-exploration")

N_COLORS = 4
N_LABELS = 2
ITEMS = [(c, l) for c in range(N_COLORS) for l in range(N_LABELS)]
EMBED_DIM = 32
OBS_NOISE = 0.15
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
    env_name: str = arg["env"]
    condition: str = arg["condition"]
    encoder_train_episodes: int = arg["encoder_train_episodes"]
    eval_episodes: int = arg["eval_episodes"]
    test_samples: int = arg["test_samples"]
    bias_p_consume: float = arg["bias_p_consume"]

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

    def make_head():
        return nn.Sequential(
            nn.Linear(EMBED_DIM + 1 + 2, 32), nn.Tanh(),
            nn.Linear(32, 1),
        ).to(device)

    # For ensemble_disagree we maintain TWO heads
    if condition == "ensemble_disagree":
        aux_head = make_head()
        aux_head2 = make_head()
        # different init seeds
        torch.manual_seed(seed + 1001)
        aux_head2 = make_head()
        torch.manual_seed(seed)
        params = (list(encoder.parameters())
                  + list(aux_head.parameters())
                  + list(aux_head2.parameters()))
    else:
        aux_head = make_head()
        aux_head2 = None
        params = list(encoder.parameters()) + list(aux_head.parameters())

    opt = torch.optim.Adam(params, lr=2e-3)
    rng_rl = np.random.RandomState(seed + 47)

    # Tracking for intrinsic mechanisms
    pred_err_running = 0.5  # exponential moving average

    def choose_action(z_unsq, E, episode_idx):
        if condition == "biased_only":
            return 1 if rng_rl.rand() < bias_p_consume else 0
        elif condition == "uniform_random":
            return int(rng_rl.choice([0, 1]))
        elif condition == "eps_greedy_decay":
            # epsilon = 1.0 → 0.05 linearly over training
            eps = max(0.05, 1.0 - (episode_idx / encoder_train_episodes) * 0.95)
            if rng_rl.rand() < eps:
                return int(rng_rl.choice([0, 1]))
            # Otherwise greedy
            with torch.no_grad():
                e_t = torch.tensor([[E]], dtype=torch.float32, device=device)
                a_oh_c = torch.tensor([[0.0, 1.0]], device=device)
                a_oh_s = torch.tensor([[1.0, 0.0]], device=device)
                pred_c = aux_head(torch.cat([z_unsq, e_t, a_oh_c], -1)).item()
                pred_s = aux_head(torch.cat([z_unsq, e_t, a_oh_s], -1)).item()
            return 1 if pred_c > pred_s else 0
        elif condition == "pred_error_curiosity":
            # Probability of random action scales with recent prediction error
            # err in [0, ~2]; map to [0.05, 0.95] via sigmoid-ish
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
            # Sample uniformly with prob proportional to head disagreement
            with torch.no_grad():
                e_t = torch.tensor([[E]], dtype=torch.float32, device=device)
                a_oh_c = torch.tensor([[0.0, 1.0]], device=device)
                a_oh_s = torch.tensor([[1.0, 0.0]], device=device)
                p1_c = aux_head(torch.cat([z_unsq, e_t, a_oh_c], -1)).item()
                p2_c = aux_head2(torch.cat([z_unsq, e_t, a_oh_c], -1)).item()
                p1_s = aux_head(torch.cat([z_unsq, e_t, a_oh_s], -1)).item()
                p2_s = aux_head2(torch.cat([z_unsq, e_t, a_oh_s], -1)).item()
                disagree = abs(p1_c - p2_c) + abs(p1_s - p2_s)
            # map disagreement [0, 2] to explore-probability [0.05, 0.95]
            ex_p = max(0.05, min(0.95, disagree / 2.0 + 0.05))
            if rng_rl.rand() < ex_p:
                return int(rng_rl.choice([0, 1]))
            mean_c = 0.5 * (p1_c + p2_c)
            mean_s = 0.5 * (p1_s + p2_s)
            return 1 if mean_c > mean_s else 0
        elif condition == "expected_info_gain":
            # Approximate info gain by the margin |pred_c - pred_s|.
            # Small margin = high uncertainty = sample randomly.
            with torch.no_grad():
                e_t = torch.tensor([[E]], dtype=torch.float32, device=device)
                a_oh_c = torch.tensor([[0.0, 1.0]], device=device)
                a_oh_s = torch.tensor([[1.0, 0.0]], device=device)
                pred_c = aux_head(torch.cat([z_unsq, e_t, a_oh_c], -1)).item()
                pred_s = aux_head(torch.cat([z_unsq, e_t, a_oh_s], -1)).item()
            margin = abs(pred_c - pred_s)
            # large margin → low explore prob; small margin → high
            ex_p = max(0.05, min(0.95, 1.0 - margin / 2.0))
            if rng_rl.rand() < ex_p:
                return int(rng_rl.choice([0, 1]))
            return 1 if pred_c > pred_s else 0
        else:
            raise ValueError(condition)

    explore_rates = []
    for ep in range(encoder_train_episodes):
        E = ENERGY_INIT
        zs, energies, actions_oh, observed_des = [], [], [], []
        steps = 0
        randomized_count = 0
        while E > 0 and steps < T_MAX:
            obs_, _, _, rew_ = sample_items(1, rng_rl)
            x = torch.from_numpy(obs_).float().to(device)
            z = encoder(x).squeeze(0)
            z_unsq = z.unsqueeze(0)
            action_before_random_count = randomized_count
            # We can't directly observe whether choose_action took the random
            # branch, so we re-do it inline for tracking. Simpler: take action.
            action = choose_action(z_unsq, E, ep)
            E_before = E
            E -= ENERGY_DECAY
            if action == 1:
                E = min(1.0, max(0.0, E + float(rew_[0])))
            observed_de = E - E_before

            # Update curiosity running pred error
            with torch.no_grad():
                a_oh = torch.zeros(1, 2, device=device)
                a_oh[0, action] = 1.0
                e_t = torch.tensor([[E_before]], dtype=torch.float32, device=device)
                pred_de = aux_head(torch.cat([z_unsq, e_t, a_oh], -1)).item()
            pred_err = abs(observed_de - pred_de)
            pred_err_running = 0.95 * pred_err_running + 0.05 * pred_err

            a_oh = torch.zeros(2, device=device); a_oh[action] = 1.0
            zs.append(z); energies.append(torch.tensor(E_before, device=device))
            actions_oh.append(a_oh)
            observed_des.append(torch.tensor(observed_de, dtype=torch.float32, device=device))
            steps += 1

        # Compute MSE loss + optional second-head loss
        if zs:
            z_stack = torch.stack(zs)
            e_stack = torch.stack(energies).unsqueeze(-1)
            a_stack = torch.stack(actions_oh)
            targets = torch.stack(observed_des)
            aux_input = torch.cat([z_stack, e_stack, a_stack], dim=-1)
            pred = aux_head(aux_input).squeeze(-1)
            loss = F.mse_loss(pred, targets)
            if aux_head2 is not None:
                # Bootstrap second head on a different random subset of samples
                idx = torch.randperm(len(zs))[:max(1, len(zs) // 2)]
                pred2 = aux_head2(aux_input[idx]).squeeze(-1)
                loss = loss + F.mse_loss(pred2, targets[idx])
            opt.zero_grad(); loss.backward(); opt.step()

    # ============ Cluster gaps ============
    rng_test = np.random.RandomState(seed + 9998)
    obs_t, col_t, lab_t, rew_t = sample_items(test_samples, rng_test)
    with torch.no_grad():
        zt = encoder(torch.from_numpy(obs_t).to(device)).cpu().numpy()
    cluster_gaps = compute_cluster_gaps(zt, col_t, lab_t, rew_t)

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

    # Calibration on both actions across items
    n_cal = min(256, len(obs_t))
    with torch.no_grad():
        z_cal = encoder(torch.from_numpy(obs_t[:n_cal]).to(device))
    fixed_E = torch.full((n_cal, 1), 0.5, device=device)
    a_consume = torch.zeros(n_cal, 2, device=device); a_consume[:, 1] = 1.0
    a_skip = torch.zeros(n_cal, 2, device=device); a_skip[:, 0] = 1.0
    with torch.no_grad():
        pred_de_consume = aux_head(torch.cat([z_cal, fixed_E, a_consume], -1)).squeeze(-1).cpu().numpy()
        pred_de_skip = aux_head(torch.cat([z_cal, fixed_E, a_skip], -1)).squeeze(-1).cpu().numpy()
    import numpy as np
    true_de_skip = np.full(n_cal, -ENERGY_DECAY)
    true_de_consume = np.clip(0.5 + rew_t[:n_cal], 0, 1) - 0.5 - ENERGY_DECAY
    calibration_consume_mse = float(np.mean((pred_de_consume - true_de_consume) ** 2))
    calibration_skip_mse = float(np.mean((pred_de_skip - true_de_skip) ** 2))

    return dict(
        seed=seed,
        env=env_name,
        condition=condition,
        cluster_gaps=cluster_gaps,
        mean_return=float(np.mean(episode_returns)),
        action_accuracy=float(np.mean(action_acc_records)),
        episode_returns=episode_returns,
        calibration_consume_mse=calibration_consume_mse,
        calibration_skip_mse=calibration_skip_mse,
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
    out: str = "artifacts/epistemic_exploration/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    cell_args = []
    for sd in seed_list:
        for cond in ALL_CONDITIONS:
            for env in ALL_ENVS:
                cell_args.append(dict(
                    seed=sd, env=env, condition=cond,
                    encoder_train_episodes=encoder_train_episodes,
                    eval_episodes=eval_episodes,
                    test_samples=test_samples,
                    bias_p_consume=bias_p_consume,
                ))
    print(f"running {len(cell_args)} cells in parallel...")
    results = list(run_cell.map(cell_args))
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for r in results:
        summary_rows.append(dict(
            seed=r["seed"], env=r["env"], condition=r["condition"],
            reward_gap=r["cluster_gaps"]["reward"],
            color_gap=r["cluster_gaps"]["color"],
            label_gap=r["cluster_gaps"]["label"],
            mean_return=r["mean_return"],
            action_accuracy=r["action_accuracy"],
            calibration_consume_mse=r["calibration_consume_mse"],
            calibration_skip_mse=r["calibration_skip_mse"],
        ))

    out_path.write_text(json.dumps({
        "manifest": dict(
            seeds=seed_list,
            conditions=ALL_CONDITIONS,
            envs=ALL_ENVS,
            encoder_train_episodes=encoder_train_episodes,
            eval_episodes=eval_episodes,
            bias_p_consume=bias_p_consume,
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nsummary ({len(summary_rows)} cells):")
    print(f"{'condition':<26} {'env':<18} {'seed':>10} | "
          f"{'rg':>7} {'return':>7} {'acc':>6} {'cal_c_mse':>10}")
    for r in summary_rows:
        print(f"  {r['condition']:<24} {r['env']:<16} {r['seed']:>10} | "
              f"{r['reward_gap']:>+.3f} {r['mean_return']:>6.2f} "
              f"{r['action_accuracy']:>5.3f} {r['calibration_consume_mse']:>9.4f}")
