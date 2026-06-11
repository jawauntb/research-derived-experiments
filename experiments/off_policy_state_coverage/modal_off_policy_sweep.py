#!/usr/bin/env python3
"""Paper 13a — Off-Policy ΔE Training for State-Dependent Concern.

Paper 12 found that the online model_plan_delta_e pipeline fails
uniformly on state-dependent reward (return 13 / acc 0.47 across all
six tested conditions), and diagnosed the failure as a *policy-
coupled state-coverage* problem: the agent's own homeostatic
dynamics produce training data biased toward low-E states, so the
ΔE head never sees the high-E counterfactual data it would need
to learn the E=0.5 inversion.

This paper tests the prescribed fix: decouple the training
distribution from episode dynamics by sampling (item, E, action)
tuples uniformly off-policy and training the ΔE head supervised on
the resulting (z, E, action) → observed_ΔE mapping. At eval time,
plan online via greedy argmax over predicted ΔE (Paper 10 rule).

Conditions (4 × 2 envs × 3 seeds = 24 cells):
  - off_policy_state_aware    : ΔE head + encoder trained on
                                uniformly-sampled (item, E ∈ [0,1],
                                action) tuples. Head sees E. HEADLINE.
  - off_policy_state_blind    : same but head does NOT see E.
                                FALSIFICATION CONTROL — must fail on
                                state-dep env even with perfect coverage.
  - online_state_aware (P12)  : Paper 12 baseline for comparison.
  - online_random_E_start     : Paper 12 best attempted fix for
                                comparison.

For diagnostic logging, all online conditions track the empirical
E-bin distribution of training (z, E, action) → ΔE tuples (4 bins:
[0, 0.25), [0.25, 0.5), [0.5, 0.75), [0.75, 1.0]). Off-policy
conditions are uniform by construction.

Pre-registered gates:
  G1 — static_xor replication: off_policy_state_aware acc ≥ 0.95.
  G2 — state-dep competence: off_policy_state_aware achieves
       state_conditional_competence ≥ 0.90, hungry ≥ 0.90, sated ≥ 0.90.
  G3 — state-blind falsification: off_policy_state_blind acc ≤ 0.55
       on state_dep_inv_xor (head cannot represent E-dependence).
  G4 — coverage diagnostic: online conditions' high-E (E ≥ 0.5)
       fraction of training data should be substantially below 0.5.

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/off_policy_state_coverage/modal_off_policy_sweep.py
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

app = modal.App(name="research-derived-off-policy-state-coverage")

N_COLORS = 4
N_LABELS = 2
ITEMS = [(c, l) for c in range(N_COLORS) for l in range(N_LABELS)]
EMBED_DIM = 32
OBS_NOISE = 0.15
T_MAX = 50
ENERGY_DECAY = 0.04
ENERGY_INIT = 0.5

ALL_CONDITIONS = [
    "off_policy_state_aware",
    "off_policy_state_blind",
    "online_state_aware",
    "online_random_E_start",
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
    n_train_steps: int = arg["n_train_steps"]
    batch_size: int = arg["batch_size"]
    eval_episodes: int = arg["eval_episodes"]

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rng_env = np.random.RandomState(seed + 13)
    perm = rng_env.permutation(16)
    state_aware = (condition != "off_policy_state_blind")
    is_off_policy = condition.startswith("off_policy")

    def encode_one(c, l, rng):
        obs = np.zeros(16, dtype=np.float32)
        obs[c] = 1.0
        obs[8 + l] = 1.0
        obs = obs + rng.randn(16).astype(np.float32) * OBS_NOISE
        return obs[perm]

    def sample_off_policy_batch(rng):
        # Sample (item, E, action) uniformly
        idx = rng.randint(0, len(ITEMS), size=batch_size)
        colors = np.array([ITEMS[i][0] for i in idx])
        labels = np.array([ITEMS[i][1] for i in idx])
        energies = rng.uniform(0.0, 1.0, size=batch_size).astype(np.float32)
        actions = rng.randint(0, 2, size=batch_size).astype(np.int64)
        obs = np.stack([encode_one(c, l, rng) for c, l in zip(colors, labels)])
        # Compute observed ΔE
        observed_de = np.zeros(batch_size, dtype=np.float32)
        for i in range(batch_size):
            E_before = energies[i]
            E_after = E_before - ENERGY_DECAY
            if actions[i] == 1:
                r = reward_of(env_name, colors[i], labels[i], E_before)
                E_after = min(1.0, max(0.0, E_before + r - ENERGY_DECAY))
            observed_de[i] = E_after - E_before
        return obs, energies, actions, observed_de

    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)
    aux_input_dim = EMBED_DIM + (1 if state_aware else 0) + 2

    def make_head():
        return nn.Sequential(
            nn.Linear(aux_input_dim, 32), nn.Tanh(),
            nn.Linear(32, 1),
        ).to(device)

    aux_head = make_head()
    params = list(encoder.parameters()) + list(aux_head.parameters())
    opt = torch.optim.Adam(params, lr=2e-3)

    def head_input(z_t, E_val, a_oh):
        if state_aware:
            if isinstance(E_val, (int, float)):
                e_t = torch.full((z_t.shape[0], 1), float(E_val),
                                 dtype=torch.float32, device=device)
            else:
                e_t = torch.tensor(np.asarray(E_val).reshape(-1, 1),
                                   dtype=torch.float32, device=device)
            return torch.cat([z_t, e_t, a_oh], dim=-1)
        else:
            return torch.cat([z_t, a_oh], dim=-1)

    # ============ Training ============
    rng_train = np.random.RandomState(seed + 47)
    E_bin_counts = [0, 0, 0, 0]  # [0, 0.25, 0.5, 0.75, 1.0]
    consume_E_bin_counts = [0, 0, 0, 0]
    skip_E_bin_counts = [0, 0, 0, 0]

    if is_off_policy:
        for step in range(n_train_steps):
            obs, energies, actions, observed_de = sample_off_policy_batch(rng_train)
            # Track diagnostic distribution
            for i in range(batch_size):
                bin_idx = min(3, int(energies[i] * 4))
                E_bin_counts[bin_idx] += 1
                if actions[i] == 1:
                    consume_E_bin_counts[bin_idx] += 1
                else:
                    skip_E_bin_counts[bin_idx] += 1
            x = torch.from_numpy(obs).to(device)
            z = encoder(x)
            a_oh = torch.zeros(batch_size, 2, device=device)
            a_oh[np.arange(batch_size), actions] = 1.0
            pred = aux_head(head_input(z, energies, a_oh)).squeeze(-1)
            targets = torch.from_numpy(observed_de).to(device)
            loss = F.mse_loss(pred, targets)
            opt.zero_grad(); loss.backward(); opt.step()
    else:
        # Online training (Paper 12 style)
        rng_rl = np.random.RandomState(seed + 47)
        # Pre-compute n_train_episodes from n_train_steps (~50 steps/episode)
        n_train_episodes = max(1, n_train_steps * batch_size // T_MAX)
        random_E_start = (condition == "online_random_E_start")
        for ep in range(n_train_episodes):
            if random_E_start:
                E = float(rng_rl.uniform(0.1, 0.9))
            else:
                E = ENERGY_INIT
            zs, energies_l, actions_oh_l, observed_des_l = [], [], [], []
            steps = 0
            while E > 0 and steps < T_MAX:
                action = int(rng_rl.choice([0, 1]))
                idx = rng_rl.randint(0, len(ITEMS))
                c_, l_ = ITEMS[idx]
                obs_ = encode_one(c_, l_, rng_rl)
                x = torch.from_numpy(obs_[None]).float().to(device)
                z = encoder(x).squeeze(0)
                E_before = E
                # Track diagnostic
                bin_idx = min(3, int(E_before * 4))
                E_bin_counts[bin_idx] += 1
                if action == 1:
                    consume_E_bin_counts[bin_idx] += 1
                else:
                    skip_E_bin_counts[bin_idx] += 1
                r = reward_of(env_name, c_, l_, E_before)
                E -= ENERGY_DECAY
                if action == 1:
                    E = min(1.0, max(0.0, E + float(r)))
                observed_de = E - E_before
                a_oh = torch.zeros(2, device=device); a_oh[action] = 1.0
                zs.append(z); energies_l.append(torch.tensor(E_before, device=device))
                actions_oh_l.append(a_oh)
                observed_des_l.append(torch.tensor(observed_de, dtype=torch.float32, device=device))
                steps += 1
            if zs:
                z_stack = torch.stack(zs)
                a_stack = torch.stack(actions_oh_l)
                targets = torch.stack(observed_des_l)
                if state_aware:
                    e_stack = torch.stack(energies_l).unsqueeze(-1)
                    aux_input = torch.cat([z_stack, e_stack, a_stack], dim=-1)
                else:
                    aux_input = torch.cat([z_stack, a_stack], dim=-1)
                pred = aux_head(aux_input).squeeze(-1)
                loss = F.mse_loss(pred, targets)
                opt.zero_grad(); loss.backward(); opt.step()

    # ============ Eval (always online greedy argmax) ============
    encoder.eval(); aux_head.eval()
    rng_eval = np.random.RandomState(seed + 9999)
    episode_returns = []
    action_acc_records = []
    action_acc_hungry = []
    action_acc_sated = []
    for _ in range(eval_episodes):
        E = ENERGY_INIT
        steps = 0
        while E > 0 and steps < T_MAX:
            idx = rng_eval.randint(0, len(ITEMS))
            c_, l_ = ITEMS[idx]
            obs_ = encode_one(c_, l_, rng_eval)
            x = torch.from_numpy(obs_[None]).float().to(device)
            true_r = reward_of(env_name, c_, l_, E)
            optimal_action = 1 if true_r > 0 else 0
            with torch.no_grad():
                z = encoder(x)
                a_oh_c = torch.tensor([[0.0, 1.0]], device=device)
                a_oh_s = torch.tensor([[1.0, 0.0]], device=device)
                pc = aux_head(head_input(z, E, a_oh_c)).item()
                ps = aux_head(head_input(z, E, a_oh_s)).item()
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

    # ============ Calibration per E grid ============
    n_cal = 256
    cal_records = []
    rng_cal = np.random.RandomState(seed + 333)
    import numpy as _np
    for E_grid in [0.2, 0.5, 0.8]:
        obs_l, col_l, lab_l, rew_l = [], [], [], []
        for _ in range(n_cal):
            idx = rng_cal.randint(0, len(ITEMS))
            c_, l_ = ITEMS[idx]
            obs_l.append(encode_one(c_, l_, rng_cal))
            col_l.append(c_); lab_l.append(l_)
            rew_l.append(reward_of(env_name, c_, l_, E_grid))
        obs_arr = _np.array(obs_l)
        rews = _np.array(rew_l)
        with torch.no_grad():
            z_cal = encoder(torch.from_numpy(obs_arr).to(device))
        a_consume = torch.zeros(n_cal, 2, device=device); a_consume[:, 1] = 1.0
        a_skip = torch.zeros(n_cal, 2, device=device); a_skip[:, 0] = 1.0
        with torch.no_grad():
            pred_c = aux_head(head_input(z_cal, E_grid, a_consume)).squeeze(-1).cpu().numpy()
            pred_s = aux_head(head_input(z_cal, E_grid, a_skip)).squeeze(-1).cpu().numpy()
        pred_margin = pred_c - pred_s
        optimal = (rews > 0).astype(_np.int64)
        pred_action = (pred_margin > 0).astype(_np.int64)
        cal_records.append(dict(
            E_grid=E_grid,
            margin_sign_acc=float(_np.mean(pred_action == optimal)),
        ))

    return dict(
        seed=seed,
        env=env_name,
        condition=condition,
        mean_return=float(_np.mean(episode_returns)),
        action_accuracy=float(_np.mean(action_acc_records)),
        action_acc_hungry=float(_np.mean(action_acc_hungry)) if action_acc_hungry else None,
        action_acc_sated=float(_np.mean(action_acc_sated)) if action_acc_sated else None,
        state_conditional_competence=(
            (float(_np.mean(action_acc_hungry)) + float(_np.mean(action_acc_sated))) / 2.0
            if action_acc_hungry and action_acc_sated else None
        ),
        calibration_by_E=cal_records,
        E_bin_counts=E_bin_counts,
        consume_E_bin_counts=consume_E_bin_counts,
        skip_E_bin_counts=skip_E_bin_counts,
        episode_returns=episode_returns,
    )


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    n_train_steps: int = 1500,
    batch_size: int = 64,
    eval_episodes: int = 50,
    out: str = "artifacts/off_policy_state_coverage/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    cell_args = []
    for sd in seed_list:
        for cond in ALL_CONDITIONS:
            for env in ALL_ENVS:
                cell_args.append(dict(
                    seed=sd, condition=cond, env=env,
                    n_train_steps=n_train_steps,
                    batch_size=batch_size,
                    eval_episodes=eval_episodes,
                ))
    print(f"running {len(cell_args)} cells in parallel...")
    results = list(run_cell.map(cell_args))
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for r in results:
        cal_by_E = {f"acc@E={c['E_grid']}": c["margin_sign_acc"]
                    for c in r["calibration_by_E"]}
        total_train = sum(r["E_bin_counts"])
        bin_fracs = ([float(c) / total_train for c in r["E_bin_counts"]]
                     if total_train > 0 else [0, 0, 0, 0])
        consume_total = sum(r["consume_E_bin_counts"])
        consume_high_E_frac = (
            (r["consume_E_bin_counts"][2] + r["consume_E_bin_counts"][3]) / consume_total
            if consume_total > 0 else 0.0
        )
        summary_rows.append(dict(
            seed=r["seed"], condition=r["condition"], env=r["env"],
            mean_return=r["mean_return"],
            action_accuracy=r["action_accuracy"],
            action_acc_hungry=r["action_acc_hungry"],
            action_acc_sated=r["action_acc_sated"],
            state_conditional_competence=r["state_conditional_competence"],
            E_bin_fracs=bin_fracs,
            consume_high_E_frac=float(consume_high_E_frac),
            **cal_by_E,
        ))

    out_path.write_text(json.dumps({
        "manifest": dict(
            seeds=seed_list, conditions=ALL_CONDITIONS, envs=ALL_ENVS,
            n_train_steps=n_train_steps, batch_size=batch_size,
            eval_episodes=eval_episodes,
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nsummary ({len(summary_rows)} cells):")
    print(f"{'cond':<26} {'env':<22} {'seed':>10} | "
          f"{'ret':>5} {'acc':>5} {'sc_c':>5} | "
          f"{'acc@.2':>7} {'acc@.5':>7} {'acc@.8':>7} | "
          f"{'highE_consume':>14}")
    for r in summary_rows:
        sc = "  --  " if r["state_conditional_competence"] is None else f"{r['state_conditional_competence']:.3f}"
        print(f"  {r['condition']:<24} {r['env']:<20} {r['seed']:>10} | "
              f"{r['mean_return']:>4.1f} {r['action_accuracy']:>4.2f} "
              f"{sc:>5} | "
              f"{r['acc@E=0.2']:>6.3f} {r['acc@E=0.5']:>6.3f} {r['acc@E=0.8']:>6.3f} | "
              f"{r['consume_high_E_frac']:>13.3f}")
