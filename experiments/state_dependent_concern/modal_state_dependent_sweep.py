#!/usr/bin/env python3
"""Paper 12 — State-Dependent Concern.

Tests whether the model_plan_delta_e pipeline (Papers 10/10b/11/11b)
extends to *state-dependent* reward functions, where the same sensory
item has different valence depending on the agent's internal energy
level. This is the cleanest empirical test of "meaning is geometry
under concern": concern itself varies with internal state.

Environment:
  - Static XOR (Paper 11 baseline): reward = XOR(color, label) for all E.
  - State-dependent XOR ("inverted-above-half"):
      E < 0.5  →  reward = +XOR(color, label)    (hungry: normal food/poison)
      E ≥ 0.5  →  reward = −XOR(color, label)    (sated: poison/food)
  In the state-dep env, the OPTIMAL ACTION flips with internal state.

Conditions (4):
  - state_aware_head_uniform   : ΔE head sees (z, E, action_oh).
                                 Uniform-random data collection. Baseline.
  - state_aware_head_mbes      : same head, MBES exploration.
  - state_aware_head_ensemble  : same head, K=2 ensemble-margin
                                 exploration (NEW from Paper 11b §4.2).
                                 Sample randomly when ensemble
                                 disagreement is high OR margin is small.
  - state_blind_head_uniform   : ΔE head does NOT see E. Uniform random.
                                 FALSIFICATION CONTROL — should fail
                                 on state-dep env because head cannot
                                 produce E-dependent argmax.

24 cells: 4 × 2 envs × 3 seeds.

New metrics per cell:
  - margin_sign_acc_hungry   : accuracy at E ∈ [0.0, 0.5]
  - margin_sign_acc_sated    : accuracy at E ∈ [0.5, 1.0]
  - state_conditional_competence : mean of the two
  - reward_gap (static role on z) — comparison only

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/state_dependent_concern/modal_state_dependent_sweep.py
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

app = modal.App(name="research-derived-state-dependent-concern")

N_COLORS = 4
N_LABELS = 2
ITEMS = [(c, l) for c in range(N_COLORS) for l in range(N_LABELS)]
EMBED_DIM = 32
OBS_NOISE = 0.15
T_MAX = 50
ENERGY_DECAY = 0.04
ENERGY_INIT = 0.5

ALL_CONDITIONS = [
    "state_aware_head_uniform",
    "state_aware_head_mbes",
    "state_aware_head_ensemble",
    "state_blind_head_uniform",
    "state_aware_head_random_E_start",
    "state_aware_head_random_E_start_mbes",
]
ALL_ENVS = ["static_xor", "state_dep_inv_xor"]


def base_xor(c, l):
    return 1.0 if ((c in (0, 1)) ^ (l == 0)) else -1.0


def reward_of(env, c, l, energy):
    if env == "static_xor":
        return base_xor(c, l)
    elif env == "state_dep_inv_xor":
        return base_xor(c, l) if energy < 0.5 else -base_xor(c, l)
    raise ValueError(env)


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
    eval_episodes: int = arg["eval_episodes"]
    test_samples: int = arg["test_samples"]

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rng_env = np.random.RandomState(seed + 13)
    perm = rng_env.permutation(16)

    def encode_obs(colors, labels, rng):
        n = len(colors)
        obs = np.zeros((n, 16), dtype=np.float32)
        obs[np.arange(n), colors] = 1.0
        obs[np.arange(n), 8 + labels] = 1.0
        obs += rng.randn(n, 16).astype(np.float32) * OBS_NOISE
        return obs[:, perm]

    def sample_items(n, rng, energy_for_reward=0.5):
        idx = rng.randint(0, len(ITEMS), size=n)
        colors = np.array([ITEMS[i][0] for i in idx])
        labels = np.array([ITEMS[i][1] for i in idx])
        rewards = np.array([reward_of(env_name, c, l, energy_for_reward)
                            for c, l in zip(colors, labels)])
        obs = encode_obs(colors, labels, rng)
        return obs, colors, labels, rewards

    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)

    state_aware = condition.startswith("state_aware_head")
    random_E_start = "random_E_start" in condition
    aux_input_dim = EMBED_DIM + (1 if state_aware else 0) + 2

    def make_head():
        return nn.Sequential(
            nn.Linear(aux_input_dim, 32), nn.Tanh(),
            nn.Linear(32, 1),
        ).to(device)

    if condition == "state_aware_head_ensemble":
        torch.manual_seed(seed + 1001)
        aux_head2 = make_head()
        torch.manual_seed(seed)
        aux_head = make_head()
    else:
        aux_head = make_head()
        aux_head2 = None

    params = list(encoder.parameters()) + list(aux_head.parameters())
    if aux_head2 is not None:
        params += list(aux_head2.parameters())
    opt = torch.optim.Adam(params, lr=2e-3)
    rng_rl = np.random.RandomState(seed + 47)

    def head_input(z_t, E_val, a_oh):
        # z_t: (n, EMBED_DIM); a_oh: (n, 2); E_val: float OR (n,) array
        if state_aware:
            if isinstance(E_val, float):
                e_t = torch.full((z_t.shape[0], 1), E_val,
                                 dtype=torch.float32, device=device)
            else:
                e_t = torch.tensor(np.asarray(E_val).reshape(-1, 1),
                                   dtype=torch.float32, device=device)
            return torch.cat([z_t, e_t, a_oh], dim=-1)
        else:
            return torch.cat([z_t, a_oh], dim=-1)

    def predict_de(head, z, E_val, action_idx_or_oh):
        if isinstance(action_idx_or_oh, int):
            a_oh = torch.zeros(z.shape[0], 2, device=device)
            a_oh[:, action_idx_or_oh] = 1.0
        else:
            a_oh = action_idx_or_oh
        return head(head_input(z, E_val, a_oh)).squeeze(-1)

    def choose_action_train(z_unsq, E, ep):
        # Uniform-random for all variants except the MBES/ensemble ones.
        # The MBES variants use the model's margin; the random_E_start
        # variants without "_mbes" use uniform random + random E start.
        is_mbes = "_mbes" in condition
        is_ensemble = condition == "state_aware_head_ensemble"
        if not is_mbes and not is_ensemble:
            return int(rng_rl.choice([0, 1]))
        if condition == "state_aware_head_uniform" or condition == "state_blind_head_uniform":
            return int(rng_rl.choice([0, 1]))
        elif condition.endswith("_mbes") or condition == "state_aware_head_mbes":
            with torch.no_grad():
                pc = predict_de(aux_head, z_unsq, E, 1).item()
                ps = predict_de(aux_head, z_unsq, E, 0).item()
            margin = abs(pc - ps)
            ex_p = max(0.05, min(0.95, 1.0 - margin / 2.0))
            if rng_rl.rand() < ex_p:
                return int(rng_rl.choice([0, 1]))
            return 1 if pc > ps else 0
        elif condition == "state_aware_head_ensemble":
            with torch.no_grad():
                pc1 = predict_de(aux_head, z_unsq, E, 1).item()
                ps1 = predict_de(aux_head, z_unsq, E, 0).item()
                pc2 = predict_de(aux_head2, z_unsq, E, 1).item()
                ps2 = predict_de(aux_head2, z_unsq, E, 0).item()
            margin = abs(0.5 * (pc1 + pc2) - 0.5 * (ps1 + ps2))
            disagree = abs(pc1 - pc2) + abs(ps1 - ps2)
            # explore if small margin OR high disagreement
            ex_p = max(0.05, min(0.95, max(1.0 - margin / 2.0, disagree / 2.0)))
            if rng_rl.rand() < ex_p:
                return int(rng_rl.choice([0, 1]))
            mc = 0.5 * (pc1 + pc2); ms = 0.5 * (ps1 + ps2)
            return 1 if mc > ms else 0
        else:
            raise ValueError(condition)

    def sample_one(rng):
        idx = rng.randint(0, len(ITEMS))
        c, l = ITEMS[idx]
        obs = np.zeros(16, dtype=np.float32)
        obs[c] = 1.0
        obs[8 + l] = 1.0
        obs = obs + rng.randn(16).astype(np.float32) * OBS_NOISE
        return obs[perm], c, l

    aux_loss_traj = []
    for ep in range(encoder_train_episodes):
        if random_E_start:
            # Sample initial E uniformly in [0.1, 0.9] to ensure broad
            # coverage of internal-state space during training.
            E = float(rng_rl.uniform(0.1, 0.9))
        else:
            E = ENERGY_INIT
        zs, energies_list, actions_oh, observed_des = [], [], [], []
        steps = 0
        while E > 0 and steps < T_MAX:
            obs_, c_, l_ = sample_one(rng_rl)
            x = torch.from_numpy(obs_[None]).float().to(device)
            z = encoder(x).squeeze(0)
            z_unsq = z.unsqueeze(0)
            action = choose_action_train(z_unsq, E, ep)
            r = reward_of(env_name, c_, l_, E)  # reward at CURRENT E
            E_before = E
            E -= ENERGY_DECAY
            if action == 1:
                E = min(1.0, max(0.0, E + float(r)))
            observed_de = E - E_before
            a_oh = torch.zeros(2, device=device); a_oh[action] = 1.0
            zs.append(z); energies_list.append(torch.tensor(E_before, device=device))
            actions_oh.append(a_oh)
            observed_des.append(torch.tensor(observed_de, dtype=torch.float32, device=device))
            steps += 1

        if zs:
            z_stack = torch.stack(zs)
            a_stack = torch.stack(actions_oh)
            targets = torch.stack(observed_des)
            if state_aware:
                e_stack = torch.stack(energies_list).unsqueeze(-1)
                aux_input = torch.cat([z_stack, e_stack, a_stack], dim=-1)
            else:
                aux_input = torch.cat([z_stack, a_stack], dim=-1)
            pred = aux_head(aux_input).squeeze(-1)
            loss = F.mse_loss(pred, targets)
            if aux_head2 is not None:
                idx = torch.randperm(len(zs))[:max(1, len(zs) // 2)]
                pred2 = aux_head2(aux_input[idx]).squeeze(-1)
                loss = loss + F.mse_loss(pred2, targets[idx])
            opt.zero_grad(); loss.backward(); opt.step()
            if ep % max(1, encoder_train_episodes // 20) == 0:
                aux_loss_traj.append(dict(episode=ep, loss=float(loss.item())))

    # ============ Eval ============
    encoder.eval(); aux_head.eval()
    if aux_head2 is not None:
        aux_head2.eval()

    rng_eval = np.random.RandomState(seed + 9999)
    episode_returns = []
    action_acc_records = []
    action_acc_hungry = []
    action_acc_sated = []
    for _ in range(eval_episodes):
        E = ENERGY_INIT
        steps = 0
        while E > 0 and steps < T_MAX:
            obs_, c_, l_ = sample_one(rng_eval)
            x = torch.from_numpy(obs_[None]).float().to(device)
            true_r = reward_of(env_name, c_, l_, E)
            optimal_action = 1 if true_r > 0 else 0
            with torch.no_grad():
                z = encoder(x)
                pc = predict_de(aux_head, z, E, 1).item()
                ps = predict_de(aux_head, z, E, 0).item()
                if aux_head2 is not None:
                    pc2 = predict_de(aux_head2, z, E, 1).item()
                    ps2 = predict_de(aux_head2, z, E, 0).item()
                    pc = 0.5 * (pc + pc2); ps = 0.5 * (ps + ps2)
                action = 1 if pc > ps else 0
            correct = int(action == optimal_action)
            action_acc_records.append(correct)
            if E < 0.5:
                action_acc_hungry.append(correct)
            else:
                action_acc_sated.append(correct)
            E -= ENERGY_DECAY
            if action == 1:
                E = min(1.0, max(0.0, E + float(true_r)))
            steps += 1
        episode_returns.append(float(steps))

    # ============ Calibration across E grid ============
    n_cal = 256
    cal_records = []
    rng_cal = np.random.RandomState(seed + 333)
    for E_grid in [0.2, 0.5, 0.8]:
        obs_l, col_l, lab_l, rew_l = [], [], [], []
        for _ in range(n_cal):
            obs_, c_, l_ = sample_one(rng_cal)
            obs_l.append(obs_); col_l.append(c_); lab_l.append(l_)
            rew_l.append(reward_of(env_name, c_, l_, E_grid))
        obs_arr = np.array(obs_l)
        cols = np.array(col_l); labs = np.array(lab_l); rews = np.array(rew_l)
        with torch.no_grad():
            z_cal = encoder(torch.from_numpy(obs_arr).to(device))
        a_consume = torch.zeros(n_cal, 2, device=device); a_consume[:, 1] = 1.0
        a_skip = torch.zeros(n_cal, 2, device=device); a_skip[:, 0] = 1.0
        with torch.no_grad():
            pred_c = aux_head(head_input(z_cal, E_grid, a_consume)).squeeze(-1).cpu().numpy()
            pred_s = aux_head(head_input(z_cal, E_grid, a_skip)).squeeze(-1).cpu().numpy()
            if aux_head2 is not None:
                pred_c2 = aux_head2(head_input(z_cal, E_grid, a_consume)).squeeze(-1).cpu().numpy()
                pred_s2 = aux_head2(head_input(z_cal, E_grid, a_skip)).squeeze(-1).cpu().numpy()
                pred_c = 0.5 * (pred_c + pred_c2); pred_s = 0.5 * (pred_s + pred_s2)
        pred_margin = pred_c - pred_s
        optimal = (rews > 0).astype(np.int64)
        pred_action = (pred_margin > 0).astype(np.int64)
        sign_acc = float(np.mean(pred_action == optimal))
        cal_records.append(dict(
            E_grid=E_grid,
            margin_sign_acc=sign_acc,
            mean_pred_margin=float(np.mean(pred_margin)),
        ))

    return dict(
        seed=seed,
        env=env_name,
        condition=condition,
        mean_return=float(np.mean(episode_returns)),
        action_accuracy=float(np.mean(action_acc_records)),
        action_acc_hungry=float(np.mean(action_acc_hungry)) if action_acc_hungry else None,
        action_acc_sated=float(np.mean(action_acc_sated)) if action_acc_sated else None,
        state_conditional_competence=(
            (float(np.mean(action_acc_hungry)) + float(np.mean(action_acc_sated))) / 2.0
            if action_acc_hungry and action_acc_sated else None
        ),
        calibration_by_E=cal_records,
        episode_returns=episode_returns,
    )


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    encoder_train_episodes: int = 1500,
    eval_episodes: int = 50,
    test_samples: int = 512,
    out: str = "artifacts/state_dependent_concern/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    cell_args = []
    for sd in seed_list:
        for cond in ALL_CONDITIONS:
            for env in ALL_ENVS:
                cell_args.append(dict(
                    seed=sd, condition=cond, env=env,
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
        cal_by_E = {f"acc@E={c['E_grid']}": c["margin_sign_acc"]
                    for c in r["calibration_by_E"]}
        summary_rows.append(dict(
            seed=r["seed"], condition=r["condition"], env=r["env"],
            mean_return=r["mean_return"],
            action_accuracy=r["action_accuracy"],
            action_acc_hungry=r["action_acc_hungry"],
            action_acc_sated=r["action_acc_sated"],
            state_conditional_competence=r["state_conditional_competence"],
            **cal_by_E,
        ))

    out_path.write_text(json.dumps({
        "manifest": dict(
            seeds=seed_list, conditions=ALL_CONDITIONS, envs=ALL_ENVS,
            encoder_train_episodes=encoder_train_episodes,
            eval_episodes=eval_episodes,
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nsummary ({len(summary_rows)} cells):")
    print(f"{'condition':<32} {'env':<22} {'seed':>10} | "
          f"{'ret':>5} {'acc':>5} {'hung':>5} {'sat':>5}")
    for r in summary_rows:
        h = "  --  " if r["action_acc_hungry"] is None else f"{r['action_acc_hungry']:.3f}"
        s = "  --  " if r["action_acc_sated"] is None else f"{r['action_acc_sated']:.3f}"
        print(f"  {r['condition']:<30} {r['env']:<20} {r['seed']:>10} | "
              f"{r['mean_return']:>4.1f} {r['action_accuracy']:>4.2f} "
              f"{h:>5} {s:>5}")
