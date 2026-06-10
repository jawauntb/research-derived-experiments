#!/usr/bin/env python3
"""Paper 10b — Hardening the Loop: Ablations and Robustness for
Planning from Concern.

Per Paper 10 reviewer prescription, five hardening tests on the
model_plan_delta_e pipeline from Paper 10:

  1. REWARD-AXIS ABLATION at eval time. Train as before, then ablate
     specific axes (color, label, reward, random) in z and recompute
     ΔE_head(z, E, a). Per-axis action-accuracy drop tells us which
     geometry is causally load-bearing.
  2. EXPLORATION-REGIME SWEEP. Replace uniform-random data collection
     with: biased_consume (always consume), eps_greedy (50% explore
     + 50% argmax current model), replay_balanced (biased data
     buffered, balanced batch sampling).
  3. HEAD-CAPACITY SWEEP. ΔE head varies in capacity: linear,
     small (8), medium (32 default), large (128), raw_input (no
     encoder, ΔE head reads obs directly).
  4. ΔE CALIBRATION. Save predicted vs observed ΔE per (item, action)
     for diagnostic scatter.
  5. HARDER-ENV variant. Faster decay (0.08) + per-consume action cost
     (0.05). Forces decision quality to matter.

Two studies in one sweep:
  - STUDY = "exploration":  4 regimes × 3 seeds × 2 envs = 24 cells
  - STUDY = "capacity":     5 heads   × 3 seeds × 2 envs = 30 cells
  - STUDY = "harder_env":   2 envs (std/hard) × 3 seeds × 2 reward_fns = 12 cells
  Total: 66 cells. All do axis ablation + calibration at eval.

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/planning_hardening/modal_hardening_sweep.py
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

app = modal.App(name="research-derived-planning-hardening")

N_COLORS = 4
N_LABELS = 2
ITEMS = [(c, l) for c in range(N_COLORS) for l in range(N_LABELS)]
EMBED_DIM = 32
OBS_NOISE = 0.15
T_MAX = 50
ENERGY_INIT = 0.5


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
    study: str = arg["study"]
    exploration: str = arg["exploration"]
    head_capacity: str = arg["head_capacity"]
    env_hardness: str = arg["env_hardness"]
    encoder_train_episodes: int = arg["encoder_train_episodes"]
    eval_episodes: int = arg["eval_episodes"]
    test_samples: int = arg["test_samples"]

    # Env-hardness toggles
    if env_hardness == "hard":
        energy_decay = 0.08
        action_cost = 0.05
    else:
        energy_decay = 0.04
        action_cost = 0.0

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

    # Build encoder (or use identity for raw_input)
    use_raw_input = (head_capacity == "raw_input")
    if not use_raw_input:
        encoder = nn.Sequential(
            nn.Linear(16, 64), nn.ReLU(),
            nn.Linear(64, EMBED_DIM),
        ).to(device)
        emb_dim = EMBED_DIM
    else:
        encoder = nn.Identity().to(device)
        emb_dim = 16

    # Build ΔE head based on capacity
    if head_capacity == "linear":
        aux_head = nn.Linear(emb_dim + 1 + 2, 1).to(device)
    elif head_capacity == "small":
        aux_head = nn.Sequential(
            nn.Linear(emb_dim + 1 + 2, 8), nn.Tanh(),
            nn.Linear(8, 1),
        ).to(device)
    elif head_capacity == "large":
        aux_head = nn.Sequential(
            nn.Linear(emb_dim + 1 + 2, 128), nn.Tanh(),
            nn.Linear(128, 1),
        ).to(device)
    else:  # medium (default) or raw_input
        aux_head = nn.Sequential(
            nn.Linear(emb_dim + 1 + 2, 32), nn.Tanh(),
            nn.Linear(32, 1),
        ).to(device)

    params = (
        (list(encoder.parameters()) if not use_raw_input else [])
        + list(aux_head.parameters())
    )
    opt_aux = torch.optim.Adam(params, lr=2e-3)
    rng_rl = np.random.RandomState(seed + 47)

    # Replay buffer for replay_balanced
    replay_consume = []
    replay_skip = []
    REPLAY_CAP = 1000

    for ep in range(encoder_train_episodes):
        E = ENERGY_INIT
        zs, energies, actions_oh, observed_des = [], [], [], []
        steps = 0
        while E > 0 and steps < T_MAX:
            obs_, _, _, rew_ = sample_items(1, rng_rl)
            x = torch.from_numpy(obs_).float().to(device)
            z = encoder(x).squeeze(0)
            # Action choice depends on exploration regime
            if exploration == "uniform_random":
                action = int(rng_rl.choice([0, 1]))
            elif exploration == "biased_consume":
                action = 1
            elif exploration == "eps_greedy":
                if rng_rl.rand() < 0.5:
                    action = int(rng_rl.choice([0, 1]))
                else:
                    # argmax via current aux_head
                    with torch.no_grad():
                        e_t = torch.tensor([[E]], dtype=torch.float32, device=device)
                        a_oh_consume = torch.tensor([[0.0, 1.0]], device=device)
                        a_oh_skip = torch.tensor([[1.0, 0.0]], device=device)
                        z_unsq = z.unsqueeze(0)
                        pred_c = aux_head(torch.cat([z_unsq, e_t, a_oh_consume], -1)).item()
                        pred_s = aux_head(torch.cat([z_unsq, e_t, a_oh_skip], -1)).item()
                    action = 1 if pred_c > pred_s else 0
            elif exploration == "replay_balanced":
                # Collect with biased policy (consume 80% of time)
                action = 1 if rng_rl.rand() < 0.8 else 0
            else:
                raise ValueError(exploration)

            E_before = E
            E -= energy_decay
            if action == 1:
                E = min(1.0, max(0.0, E + float(rew_[0]) - action_cost))
            observed_de = E - E_before
            a_oh = torch.zeros(2, device=device)
            a_oh[action] = 1.0
            sample = (z.detach(), float(E_before), int(action),
                      float(observed_de))
            zs.append(z); energies.append(torch.tensor(E_before, device=device))
            actions_oh.append(a_oh)
            observed_des.append(torch.tensor(observed_de, dtype=torch.float32, device=device))
            # For replay buffer
            if exploration == "replay_balanced":
                buf = replay_consume if action == 1 else replay_skip
                buf.append(sample)
                if len(buf) > REPLAY_CAP:
                    buf.pop(0)
            steps += 1

        # Compute loss
        if zs:
            if exploration == "replay_balanced" and len(replay_consume) > 8 and len(replay_skip) > 8:
                # Balanced replay batch: 32 each
                rng_perm = rng_rl
                n_each = min(32, len(replay_consume), len(replay_skip))
                idx_c = rng_perm.choice(len(replay_consume), n_each, replace=False)
                idx_s = rng_perm.choice(len(replay_skip), n_each, replace=False)
                samples = [replay_consume[i] for i in idx_c] + [replay_skip[i] for i in idx_s]
                z_stack = torch.stack([s[0] for s in samples])
                e_stack = torch.tensor([[s[1]] for s in samples], device=device)
                a_stack = torch.zeros(len(samples), 2, device=device)
                for i, s in enumerate(samples):
                    a_stack[i, s[2]] = 1.0
                targets = torch.tensor([s[3] for s in samples], dtype=torch.float32, device=device)
            else:
                z_stack = torch.stack(zs)
                e_stack = torch.stack(energies).unsqueeze(-1)
                a_stack = torch.stack(actions_oh)
                targets = torch.stack(observed_des)
            aux_input = torch.cat([z_stack, e_stack, a_stack], dim=-1)
            pred = aux_head(aux_input).squeeze(-1)
            loss = F.mse_loss(pred, targets)
            opt_aux.zero_grad(); loss.backward(); opt_aux.step()

    # Freeze encoder for ablations
    encoder.eval()
    aux_head.eval()

    # ============ Cluster gaps ============
    rng_test = np.random.RandomState(seed + 9998)
    obs_t, col_t, lab_t, rew_t = sample_items(test_samples, rng_test)
    with torch.no_grad():
        zt = encoder(torch.from_numpy(obs_t).to(device)).cpu().numpy()
    cluster_gaps = compute_cluster_gaps(zt, col_t, lab_t, rew_t)

    # ============ ΔE calibration plot data ============
    # For each item, get predicted ΔE for consume and skip, vs observed
    # ground-truth ΔE under each action.
    n_cal = min(256, len(obs_t))
    cal_obs = obs_t[:n_cal]
    cal_col = col_t[:n_cal]
    cal_lab = lab_t[:n_cal]
    cal_rew = rew_t[:n_cal]
    with torch.no_grad():
        z_cal = encoder(torch.from_numpy(cal_obs).to(device))
    # Predicted under each action at fixed E=0.5
    fixed_E = torch.full((n_cal, 1), 0.5, device=device)
    a_consume = torch.zeros(n_cal, 2, device=device); a_consume[:, 1] = 1.0
    a_skip = torch.zeros(n_cal, 2, device=device); a_skip[:, 0] = 1.0
    with torch.no_grad():
        pred_de_consume = aux_head(torch.cat([z_cal, fixed_E, a_consume], -1)).squeeze(-1).cpu().numpy()
        pred_de_skip = aux_head(torch.cat([z_cal, fixed_E, a_skip], -1)).squeeze(-1).cpu().numpy()
    # True ΔE per action at E=0.5
    true_de_skip = np.full(n_cal, -energy_decay)
    true_de_consume = np.clip(0.5 + cal_rew - action_cost, 0, 1) - 0.5 - energy_decay
    cal_consume_mse = float(np.mean((pred_de_consume - true_de_consume) ** 2))
    cal_skip_mse = float(np.mean((pred_de_skip - true_de_skip) ** 2))
    # Predicted action and accuracy
    pred_action = (pred_de_consume > pred_de_skip).astype(np.int64)
    optimal_action = (cal_rew > 0).astype(np.int64)
    calibration_action_acc = float(np.mean(pred_action == optimal_action))

    # ============ Greedy eval ============
    rng_eval = np.random.RandomState(seed + 9999)

    def greedy_eval(ablation_axis=None):
        # ablation_axis: None | "color" | "label" | "reward" | "random"
        episode_returns = []
        action_acc_records = []
        # Precompute centroids for ablation axis directions
        if ablation_axis is not None:
            with torch.no_grad():
                z_all = encoder(torch.from_numpy(obs_t).to(device)).cpu().numpy()
            mean_z = z_all.mean(axis=0, keepdims=True)
            centered = z_all - mean_z
            norms = np.linalg.norm(centered, axis=1, keepdims=True)
            if ablation_axis == "color":
                axis_labels = col_t
            elif ablation_axis == "label":
                axis_labels = lab_t
            elif ablation_axis == "reward":
                axis_labels = rew_t.astype(np.int64)
            elif ablation_axis == "random":
                rng_rand = np.random.RandomState(seed + 4242)
                axis_labels = rng_rand.permutation(col_t)
            # Compute mean direction per class, average across classes weighted
            classes = np.unique(axis_labels)
            dirs = []
            for cls in classes:
                mask = axis_labels == cls
                if mask.any():
                    d = centered[mask].mean(axis=0)
                    n = np.linalg.norm(d)
                    if n > 1e-9:
                        dirs.append(d / n)
            if not dirs:
                axis_unit = None
            else:
                axis_mat = np.stack(dirs)  # K x D
                # Use the principal direction via SVD of axis_mat
                _, _, Vt = np.linalg.svd(axis_mat, full_matrices=False)
                axis_unit = Vt[0]  # top direction in this class-mean subspace
            axis_t = torch.tensor(axis_unit, dtype=torch.float32, device=device) if axis_unit is not None else None
        else:
            axis_t = None

        for _ in range(eval_episodes):
            E = ENERGY_INIT
            steps = 0
            while E > 0 and steps < T_MAX:
                obs_, _, _, rew_ = sample_items(1, rng_eval)
                x = torch.from_numpy(obs_).float().to(device)
                optimal_action = 1 if rew_[0] > 0 else 0
                with torch.no_grad():
                    z = encoder(x)
                    if axis_t is not None:
                        # subtract projection onto axis_t
                        proj = (z * axis_t).sum(dim=-1, keepdim=True) * axis_t
                        z = z - proj
                    e_t = torch.tensor([[E]], dtype=torch.float32, device=device)
                    a_oh_consume = torch.tensor([[0.0, 1.0]], device=device)
                    a_oh_skip = torch.tensor([[1.0, 0.0]], device=device)
                    pred_c = aux_head(torch.cat([z, e_t, a_oh_consume], -1)).item()
                    pred_s = aux_head(torch.cat([z, e_t, a_oh_skip], -1)).item()
                    action = 1 if pred_c > pred_s else 0
                action_acc_records.append(int(action == optimal_action))
                E -= energy_decay
                if action == 1:
                    E = min(1.0, max(0.0, E + float(rew_[0]) - action_cost))
                steps += 1
            episode_returns.append(float(steps))
        return dict(
            mean_return=float(np.mean(episode_returns)),
            action_accuracy=float(np.mean(action_acc_records)),
            episode_returns=episode_returns,
        )

    baseline_eval = greedy_eval(ablation_axis=None)
    ablation_results = {
        ax: greedy_eval(ablation_axis=ax)
        for ax in ["color", "label", "reward", "random"]
    }

    return dict(
        seed=seed,
        env=env_name,
        study=study,
        exploration=exploration,
        head_capacity=head_capacity,
        env_hardness=env_hardness,
        cluster_gaps=cluster_gaps,
        baseline_return=baseline_eval["mean_return"],
        baseline_action_accuracy=baseline_eval["action_accuracy"],
        ablation_return=dict((ax, ablation_results[ax]["mean_return"])
                            for ax in ablation_results),
        ablation_action_accuracy=dict((ax, ablation_results[ax]["action_accuracy"])
                                     for ax in ablation_results),
        calibration_consume_mse=cal_consume_mse,
        calibration_skip_mse=cal_skip_mse,
        calibration_action_acc=calibration_action_acc,
        calibration_pred_consume=pred_de_consume.tolist(),
        calibration_pred_skip=pred_de_skip.tolist(),
        calibration_true_consume=true_de_consume.tolist(),
        calibration_true_skip=true_de_skip.tolist(),
        calibration_rewards=cal_rew.tolist(),
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
    out: str = "artifacts/planning_hardening/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    envs = ["xor", "additive_thresh"]

    cell_args = []

    # Study 1: exploration regime (default head, default env hardness)
    for sd in seed_list:
        for env in envs:
            for expl in ["uniform_random", "biased_consume",
                        "eps_greedy", "replay_balanced"]:
                cell_args.append(dict(
                    seed=sd, env=env, study="exploration",
                    exploration=expl, head_capacity="medium",
                    env_hardness="std",
                    encoder_train_episodes=encoder_train_episodes,
                    eval_episodes=eval_episodes,
                    test_samples=test_samples,
                ))

    # Study 2: head capacity (default exploration, default env hardness)
    for sd in seed_list:
        for env in envs:
            for hc in ["linear", "small", "medium", "large", "raw_input"]:
                if hc == "medium":
                    continue  # already covered by exploration=uniform above
                cell_args.append(dict(
                    seed=sd, env=env, study="capacity",
                    exploration="uniform_random", head_capacity=hc,
                    env_hardness="std",
                    encoder_train_episodes=encoder_train_episodes,
                    eval_episodes=eval_episodes,
                    test_samples=test_samples,
                ))

    # Study 3: harder environment (default exploration, default head)
    for sd in seed_list:
        for env in envs:
            cell_args.append(dict(
                seed=sd, env=env, study="harder_env",
                exploration="uniform_random", head_capacity="medium",
                env_hardness="hard",
                encoder_train_episodes=encoder_train_episodes,
                eval_episodes=eval_episodes,
                test_samples=test_samples,
            ))

    print(f"running {len(cell_args)} cells in parallel...")
    results = list(run_cell.map(cell_args))
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for r in results:
        summary_rows.append(dict(
            seed=r["seed"], env=r["env"], study=r["study"],
            exploration=r["exploration"], head_capacity=r["head_capacity"],
            env_hardness=r["env_hardness"],
            reward_gap=r["cluster_gaps"]["reward"],
            color_gap=r["cluster_gaps"]["color"],
            label_gap=r["cluster_gaps"]["label"],
            baseline_return=r["baseline_return"],
            baseline_acc=r["baseline_action_accuracy"],
            ablate_color_return=r["ablation_return"]["color"],
            ablate_label_return=r["ablation_return"]["label"],
            ablate_reward_return=r["ablation_return"]["reward"],
            ablate_random_return=r["ablation_return"]["random"],
            ablate_color_acc=r["ablation_action_accuracy"]["color"],
            ablate_label_acc=r["ablation_action_accuracy"]["label"],
            ablate_reward_acc=r["ablation_action_accuracy"]["reward"],
            ablate_random_acc=r["ablation_action_accuracy"]["random"],
            calibration_acc=r["calibration_action_acc"],
            calibration_consume_mse=r["calibration_consume_mse"],
            calibration_skip_mse=r["calibration_skip_mse"],
        ))

    out_path.write_text(json.dumps({
        "manifest": dict(
            seeds=seed_list,
            encoder_train_episodes=encoder_train_episodes,
            eval_episodes=eval_episodes,
            test_samples=test_samples,
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nsummary ({len(summary_rows)} cells):")
    print(f"{'study':<12} {'cond':<22} {'env':<18} {'seed':>10} | "
          f"{'rg':>7} {'base_ret':>9} {'abl_rw_ret':>10} {'abl_rw_acc':>10}")
    for r in summary_rows:
        cond = (r["exploration"] if r["study"] == "exploration"
                else r["head_capacity"] if r["study"] == "capacity"
                else r["env_hardness"])
        print(f"  {r['study']:<10} {cond:<22} {r['env']:<16} {r['seed']:>10} | "
              f"{r['reward_gap']:>+.3f} {r['baseline_return']:>8.2f} "
              f"{r['ablate_reward_return']:>9.2f} {r['ablate_reward_acc']:>9.3f}")
