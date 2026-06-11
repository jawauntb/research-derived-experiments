#!/usr/bin/env python3
"""Paper 13b — Regime-Sensitive ΔE Models for State-Dependent Concern.

Paper 13a found that off-policy state-aware training partially recovers
state-dependent valence (state_dep_inv_xor acc 0.96, acc@E=0.8 = 0.99,
acc@E=0.2 = 0.87) but FAILS at the discontinuous boundary E=0.5
(acc 0.46, chance). Diagnosis: smooth Tanh MLP cannot sharply
represent the step function at E=0.5.

This paper tests four architectural fixes — all under off-policy
training — and asks: does the architecture, not the data, contain
the last bottleneck for state-dependent concern?

Conditions (5):

  - monolithic_head           : Paper 13a baseline. Single MLP head:
                                (z, E, action_oh) → ΔE. REPLICATION.

  - oracle_boundary_feature   : Add 1[E<0.5] as input feature. ORACLE
                                DIAGNOSTIC — hands the agent the
                                correct partition. Should resolve the
                                boundary if architecture is the only
                                obstacle.

  - learned_boundary_gate     : Two ΔE sub-heads (hungry-expert and
                                sated-expert), soft-mixed by a learned
                                sigmoid gate over E. MIXTURE-OF-EXPERTS
                                (Jacobs et al. 1991). Autonomous: the
                                gate is learned, not given.

  - fourier_E_features        : Replace scalar E with multi-frequency
                                Fourier features
                                [E, sin(πE), cos(πE), sin(2πE),
                                 cos(2πE), sin(4πE), cos(4πE)]. Helps
                                MLPs represent sharp transitions
                                (Rahaman et al. spectral-bias work).

  - sign_loss                 : Multi-task: standard ΔE MSE + cross-
                                entropy on sign(ΔE_consume - ΔE_skip).
                                The planner only needs the sign; train
                                it directly.

30 cells: 5 × 2 envs (static_xor, state_dep_inv_xor) × 3 seeds.

Pre-registered gates:
  G1 oracle confirms bottleneck: oracle_boundary_feature acc@E=0.5 ≥ 0.90
     on state_dep_inv_xor.
  G2 autonomous fix: ≥1 learned mechanism (gate, fourier, sign) reaches
     acc@E=0.5 ≥ 0.85 on state_dep_inv_xor.
  G3 replication: monolithic_head acc@E=0.5 ≈ 0.46 (within 0.10).

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/regime_sensitive_de/modal_regime_sensitive_sweep.py
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

app = modal.App(name="research-derived-regime-sensitive-de")

N_COLORS = 4
N_LABELS = 2
ITEMS = [(c, l) for c in range(N_COLORS) for l in range(N_LABELS)]
EMBED_DIM = 32
OBS_NOISE = 0.15
T_MAX = 50
ENERGY_DECAY = 0.04
ENERGY_INIT = 0.5

ALL_CONDITIONS = [
    "monolithic_head",
    "oracle_boundary_feature",
    "learned_boundary_gate",
    "fourier_E_features",
    "sign_loss",
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

    def encode_one(c, l, rng):
        obs = np.zeros(16, dtype=np.float32)
        obs[c] = 1.0
        obs[8 + l] = 1.0
        obs = obs + rng.randn(16).astype(np.float32) * OBS_NOISE
        return obs[perm]

    def sample_off_policy_batch(rng):
        idx = rng.randint(0, len(ITEMS), size=batch_size)
        colors = np.array([ITEMS[i][0] for i in idx])
        labels = np.array([ITEMS[i][1] for i in idx])
        energies = rng.uniform(0.0, 1.0, size=batch_size).astype(np.float32)
        actions = rng.randint(0, 2, size=batch_size).astype(np.int64)
        obs = np.stack([encode_one(c, l, rng) for c, l in zip(colors, labels)])
        observed_de = np.zeros(batch_size, dtype=np.float32)
        de_consume = np.zeros(batch_size, dtype=np.float32)
        de_skip = np.full(batch_size, -ENERGY_DECAY, dtype=np.float32)
        for i in range(batch_size):
            E_before = energies[i]
            r = reward_of(env_name, colors[i], labels[i], E_before)
            de_consume[i] = (
                min(1.0, max(0.0, E_before + r - ENERGY_DECAY)) - E_before
            )
            if actions[i] == 1:
                observed_de[i] = de_consume[i]
            else:
                observed_de[i] = de_skip[i]
        return obs, energies, actions, observed_de, de_consume, de_skip

    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)

    # ============ Build head per condition ============
    def fourier_encode(E_tensor):
        # E_tensor: (n, 1) or (n,) — return (n, 7) Fourier features
        E = E_tensor if E_tensor.dim() == 1 else E_tensor.squeeze(-1)
        feats = [E.unsqueeze(-1)]
        for freq in [1.0, 2.0, 4.0]:
            feats.append(torch.sin(torch.pi * freq * E).unsqueeze(-1))
            feats.append(torch.cos(torch.pi * freq * E).unsqueeze(-1))
        return torch.cat(feats, dim=-1)

    if condition == "oracle_boundary_feature":
        head_input_dim = EMBED_DIM + 1 + 1 + 2  # z, E, boundary, action_oh
    elif condition == "fourier_E_features":
        head_input_dim = EMBED_DIM + 7 + 2  # z, fourier(E)=7, action_oh
    else:
        head_input_dim = EMBED_DIM + 1 + 2  # z, E, action_oh

    if condition == "learned_boundary_gate":
        # Two expert sub-heads + a learned gate over E
        expert_h = nn.Sequential(
            nn.Linear(head_input_dim, 32), nn.Tanh(),
            nn.Linear(32, 1),
        ).to(device)
        expert_s = nn.Sequential(
            nn.Linear(head_input_dim, 32), nn.Tanh(),
            nn.Linear(32, 1),
        ).to(device)
        # Gate: sigmoid(w*E + b), parameterized as a tiny linear layer
        gate_net = nn.Linear(1, 1).to(device)
        params = (
            list(encoder.parameters())
            + list(expert_h.parameters())
            + list(expert_s.parameters())
            + list(gate_net.parameters())
        )
    else:
        aux_head = nn.Sequential(
            nn.Linear(head_input_dim, 32), nn.Tanh(),
            nn.Linear(32, 1),
        ).to(device)
        params = list(encoder.parameters()) + list(aux_head.parameters())

    opt = torch.optim.Adam(params, lr=2e-3)

    def build_input(z, E_val, a_oh):
        if isinstance(E_val, (int, float)):
            e_t = torch.full((z.shape[0], 1), float(E_val),
                             dtype=torch.float32, device=device)
        else:
            e_t = torch.tensor(np.asarray(E_val).reshape(-1, 1),
                               dtype=torch.float32, device=device)
        if condition == "oracle_boundary_feature":
            b = (e_t < 0.5).float()
            return torch.cat([z, e_t, b, a_oh], dim=-1)
        elif condition == "fourier_E_features":
            ff = fourier_encode(e_t.squeeze(-1))  # (n, 7)
            return torch.cat([z, ff, a_oh], dim=-1)
        else:
            return torch.cat([z, e_t, a_oh], dim=-1)

    def predict_de(z, E_val, a_oh):
        if condition == "learned_boundary_gate":
            if isinstance(E_val, (int, float)):
                e_t = torch.full((z.shape[0], 1), float(E_val),
                                 dtype=torch.float32, device=device)
            else:
                e_t = torch.tensor(np.asarray(E_val).reshape(-1, 1),
                                   dtype=torch.float32, device=device)
            base_in = torch.cat([z, e_t, a_oh], dim=-1)
            ph = expert_h(base_in).squeeze(-1)
            ps = expert_s(base_in).squeeze(-1)
            # Gate: sigmoid(w*(E - 0.5)). Initialize so the gate centers
            # near E=0.5 — the network is free to learn the actual
            # boundary location.
            gate_logit = gate_net(e_t).squeeze(-1)
            g = torch.sigmoid(gate_logit)
            # g is "p(hungry-expert)"; mix accordingly
            return g * ph + (1 - g) * ps
        else:
            inp = build_input(z, E_val, a_oh)
            return aux_head(inp).squeeze(-1)

    # ============ Train ============
    rng_train = np.random.RandomState(seed + 47)
    for step in range(n_train_steps):
        obs, energies, actions, observed_de, de_consume, de_skip = sample_off_policy_batch(rng_train)
        x = torch.from_numpy(obs).to(device)
        z = encoder(x)
        a_oh = torch.zeros(batch_size, 2, device=device)
        a_oh[np.arange(batch_size), actions] = 1.0
        targets = torch.from_numpy(observed_de).to(device)
        pred = predict_de(z, energies, a_oh)
        loss = F.mse_loss(pred, targets)
        if condition == "sign_loss":
            # Predict ΔE for BOTH actions; compute predicted margin and
            # supervise it directly against the true margin's sign.
            a_oh_c = torch.zeros(batch_size, 2, device=device); a_oh_c[:, 1] = 1.0
            a_oh_s = torch.zeros(batch_size, 2, device=device); a_oh_s[:, 0] = 1.0
            pc_all = predict_de(z, energies, a_oh_c)
            ps_all = predict_de(z, energies, a_oh_s)
            pred_margin = pc_all - ps_all
            true_margin = torch.from_numpy(de_consume - de_skip).to(device)
            # Cross-entropy on sign: treat pred_margin as logit for "consume
            # is better" vs "skip is better"; target is 1 if consume better.
            target_consume_better = (true_margin > 0).long()
            logits = torch.stack([-pred_margin, pred_margin], dim=-1)
            sign_loss_val = F.cross_entropy(logits, target_consume_better)
            loss = loss + 0.5 * sign_loss_val
        opt.zero_grad(); loss.backward(); opt.step()

    # ============ Eval (greedy argmax over predicted ΔE) ============
    encoder.eval()
    if condition == "learned_boundary_gate":
        expert_h.eval(); expert_s.eval(); gate_net.eval()
    else:
        aux_head.eval()

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
                pc = predict_de(z, E, a_oh_c).item()
                ps = predict_de(z, E, a_oh_s).item()
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

    # ============ Per-E calibration ============
    cal_records = []
    rng_cal = np.random.RandomState(seed + 333)
    import numpy as _np
    n_cal = 256
    for E_grid in [0.1, 0.2, 0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 0.8, 0.9]:
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
            pc = predict_de(z_cal, E_grid, a_consume).cpu().numpy()
            ps = predict_de(z_cal, E_grid, a_skip).cpu().numpy()
        pred_margin = pc - ps
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
        episode_returns=episode_returns,
    )


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    n_train_steps: int = 1500,
    batch_size: int = 64,
    eval_episodes: int = 50,
    out: str = "artifacts/regime_sensitive_de/sweep_v1.json",
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
            n_train_steps=n_train_steps, batch_size=batch_size,
            eval_episodes=eval_episodes,
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nsummary ({len(summary_rows)} cells):")
    print(f"{'cond':<26} {'env':<22} {'seed':>10} | "
          f"{'ret':>5} {'acc':>5} {'sc_c':>5} {'@0.2':>5} {'@0.5':>5} {'@0.8':>5}")
    for r in summary_rows:
        sc = "  --  " if r["state_conditional_competence"] is None else f"{r['state_conditional_competence']:.3f}"
        print(f"  {r['condition']:<24} {r['env']:<20} {r['seed']:>10} | "
              f"{r['mean_return']:>4.1f} {r['action_accuracy']:>4.2f} "
              f"{sc:>5} {r['acc@E=0.2']:>4.2f} {r['acc@E=0.5']:>4.2f} "
              f"{r['acc@E=0.8']:>4.2f}")
