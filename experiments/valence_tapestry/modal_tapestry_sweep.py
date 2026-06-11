#!/usr/bin/env python3
"""Paper 15 — Tapestry of Valence.

The first multi-valence agent in the program. Previous papers used a
scalar internal variable E (energy). Bennett's "tapestry of valence"
framework argues that mattering is multi-dimensional: hunger and thirst
may both be 'bad' but differ qualitatively because they correspond
to different lower-level patterns of viability consequence.

This paper tests whether a vector-valence head (predicts ΔE and ΔD
jointly) supports more flexible concern than a scalar drive head,
especially under zero-shot reweighting of internal priorities.

Internal state vector: (E, D)
  E ∈ [0, 1]: energy (depletes; episode ends at E≤0)
  D ∈ [0, 1]: damage (accumulates; episode ends at D≥1)

Item types (color × label):
  (0, 0) food      : ΔE=+1.0, ΔD=+0.0
  (0, 1) poison    : ΔE=−1.0, ΔD=+0.3
  (1, 0) medicine  : ΔE=−0.1, ΔD=−0.3
  (1, 1) neutral   : ΔE=0.0,  ΔD=0.0

Actions: consume (1), skip (0). Skip: ΔE = −decay_E, ΔD = +decay_D.
Consume: ΔE/ΔD per the item's effect, plus the decay/accrual.

Drive function: drive(E, D) = w_E · (1 − E) + w_D · D
Agent maximizes drive reduction: score(a) = drive(s) − drive(s_after).

Five conditions:
  - vector_dV_head           : head predicts (ΔE, ΔD) jointly. HEADLINE.
  - scalar_drive_head        : head predicts Δdrive(E, D) directly
                               (collapses both dims into one scalar).
  - energy_only_head         : head predicts only ΔE; assumes ΔD=0.
  - damage_only_head         : head predicts only ΔD; assumes ΔE=0.
  - oracle_role_labels       : head input includes the true item role
                               one-hot. UPPER BOUND.

5 conditions × 3 seeds = 15 cells. Each cell evaluated under 3
weight contexts (balanced, hungry-priority, injured-priority) for
zero-shot reweighting test.

Pre-registered gates:
  G1 vector competence: vector_dV_head return ≥ 45/50 in balanced eval.
  G2 scalar limitation: scalar_drive_head underperforms vector_dV_head
     by ≥ 5 return under weight-shifted evaluations.
  G3 dimension necessity: energy_only_head fails on injured-priority
     (≤ 35); damage_only_head fails on hungry-priority (≤ 35).
  G4 tapestry geometry: effect-vector RSA correlation ≥ 0.5 for
     vector_dV_head (latent-distance correlates with effect-vector-
     distance across the 4 item types).

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/valence_tapestry/modal_tapestry_sweep.py
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

app = modal.App(name="research-derived-valence-tapestry")

# Item types: (color, label) → role
# 0=food, 1=poison, 2=medicine, 3=neutral
ITEM_TYPES = {
    (0, 0): {"role": "food", "dE": +1.0, "dD": 0.0},
    (0, 1): {"role": "poison", "dE": -1.0, "dD": +0.5},
    (1, 0): {"role": "medicine", "dE": -0.1, "dD": -0.5},
    (1, 1): {"role": "neutral", "dE": 0.0, "dD": 0.0},
}
N_COLORS = 2
N_LABELS = 2
ITEMS = list(ITEM_TYPES.keys())
ROLE_IDX = {"food": 0, "poison": 1, "medicine": 2, "neutral": 3}

EMBED_DIM = 32
OBS_NOISE = 0.15
T_MAX = 50
ENERGY_DECAY = 0.04
DAMAGE_ACCRUAL = 0.03  # per step, even on skip; 33-step floor from damage alone
ENERGY_INIT = 0.5
DAMAGE_INIT = 0.0

ALL_CONDITIONS = [
    "vector_dV_head",
    "scalar_drive_head",
    "energy_only_head",
    "damage_only_head",
    "oracle_role_labels",
]

EVAL_WEIGHTS = [
    ("balanced", 1.0, 1.0),
    ("hungry_priority", 2.0, 1.0),
    ("injured_priority", 1.0, 2.0),
]


def role_of(c, l):
    return ITEM_TYPES[(c, l)]["role"]


def consume_effect(c, l):
    info = ITEM_TYPES[(c, l)]
    return info["dE"], info["dD"]


@app.function(image=IMAGE, timeout=1800, cpu=4, memory=4096)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    seed: int = arg["seed"]
    condition: str = arg["condition"]
    n_train_steps: int = arg["n_train_steps"]
    batch_size: int = arg["batch_size"]
    eval_episodes: int = arg["eval_episodes"]

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rng_env = np.random.RandomState(seed + 13)
    # Wider observation since fewer items: still pad to 16 dims for parity
    # with prior papers.
    perm = rng_env.permutation(16)

    def encode_one(c, l, rng):
        obs = np.zeros(16, dtype=np.float32)
        obs[c] = 1.0
        obs[8 + l] = 1.0
        obs = obs + rng.randn(16).astype(np.float32) * OBS_NOISE
        return obs[perm]

    def apply_action(action: int, E: float, D: float, c: int, l: int):
        """Apply action, return (new_E, new_D, dE, dD)."""
        if action == 1:  # consume
            dE_item, dD_item = consume_effect(c, l)
            new_E = float(min(1.0, max(0.0, E + dE_item - ENERGY_DECAY)))
            new_D = float(min(1.0, max(0.0, D + dD_item + DAMAGE_ACCRUAL)))
        else:  # skip
            new_E = float(max(0.0, E - ENERGY_DECAY))
            new_D = float(min(1.0, D + DAMAGE_ACCRUAL))
        return new_E, new_D, new_E - E, new_D - D

    def sample_off_policy_batch(rng):
        idx = rng.randint(0, len(ITEMS), size=batch_size)
        colors = np.array([ITEMS[i][0] for i in idx])
        labels = np.array([ITEMS[i][1] for i in idx])
        Es = rng.uniform(0.0, 1.0, size=batch_size).astype(np.float32)
        Ds = rng.uniform(0.0, 1.0, size=batch_size).astype(np.float32)
        actions = rng.randint(0, 2, size=batch_size).astype(np.int64)
        obs = np.stack([encode_one(c, l, rng) for c, l in zip(colors, labels)])
        observed_dE = np.zeros(batch_size, dtype=np.float32)
        observed_dD = np.zeros(batch_size, dtype=np.float32)
        for i in range(batch_size):
            _, _, dE, dD = apply_action(int(actions[i]), float(Es[i]),
                                         float(Ds[i]), int(colors[i]), int(labels[i]))
            observed_dE[i] = dE
            observed_dD[i] = dD
        return obs, Es, Ds, actions, observed_dE, observed_dD, colors, labels

    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)

    # Determine head architecture
    # Common Fourier features on E and D
    def fourier_encode(scalar_tensor):
        """scalar_tensor: (n,) or (n, 1) → (n, 7) Fourier features."""
        if scalar_tensor.dim() == 2:
            scalar_tensor = scalar_tensor.squeeze(-1)
        feats = [scalar_tensor.unsqueeze(-1)]
        for freq in [1.0, 2.0, 4.0]:
            feats.append(torch.sin(torch.pi * freq * scalar_tensor).unsqueeze(-1))
            feats.append(torch.cos(torch.pi * freq * scalar_tensor).unsqueeze(-1))
        return torch.cat(feats, dim=-1)  # (n, 7)

    # Head input: z (32) + fourier_E (7) + fourier_D (7) + action_oh (2)
    base_input_dim = EMBED_DIM + 7 + 7 + 2
    use_oracle = (condition == "oracle_role_labels")
    if use_oracle:
        head_input_dim = base_input_dim + 4  # role one-hot
    else:
        head_input_dim = base_input_dim

    # Determine output dim
    if condition == "vector_dV_head":
        out_dim = 2  # (ΔE, ΔD)
    elif condition == "scalar_drive_head":
        out_dim = 1  # Δdrive (under training weights)
    elif condition == "energy_only_head":
        out_dim = 1  # ΔE only
    elif condition == "damage_only_head":
        out_dim = 1  # ΔD only
    else:  # oracle_role_labels
        out_dim = 2  # (ΔE, ΔD) — head sees role

    head = nn.Sequential(
        nn.Linear(head_input_dim, 32), nn.Tanh(),
        nn.Linear(32, out_dim),
    ).to(device)

    opt = torch.optim.Adam(
        list(encoder.parameters()) + list(head.parameters()), lr=2e-3,
    )

    def build_input(z, Es, Ds, a_oh, colors=None, labels=None):
        if isinstance(Es, (int, float)):
            E_t = torch.full((z.shape[0], 1), float(Es),
                             dtype=torch.float32, device=device)
        else:
            E_t = torch.tensor(np.asarray(Es).reshape(-1, 1),
                               dtype=torch.float32, device=device)
        if isinstance(Ds, (int, float)):
            D_t = torch.full((z.shape[0], 1), float(Ds),
                             dtype=torch.float32, device=device)
        else:
            D_t = torch.tensor(np.asarray(Ds).reshape(-1, 1),
                               dtype=torch.float32, device=device)
        ffE = fourier_encode(E_t)
        ffD = fourier_encode(D_t)
        parts = [z, ffE, ffD, a_oh]
        if use_oracle and colors is not None and labels is not None:
            role_idx = np.array([
                ROLE_IDX[role_of(int(c), int(l))]
                for c, l in zip(colors, labels)
            ])
            role_oh = torch.zeros(z.shape[0], 4, device=device)
            role_oh[np.arange(z.shape[0]), role_idx] = 1.0
            parts.append(role_oh)
        return torch.cat(parts, dim=-1)

    # ============ Training (with training weights w=1, 1) ============
    # For scalar_drive_head, we need training-time drive deltas.
    train_w_E = 1.0
    train_w_D = 1.0
    rng_train = np.random.RandomState(seed + 47)

    for step in range(n_train_steps):
        obs, Es, Ds, actions, observed_dE, observed_dD, colors, labels = sample_off_policy_batch(rng_train)
        x = torch.from_numpy(obs).to(device)
        z = encoder(x)
        a_oh = torch.zeros(batch_size, 2, device=device)
        a_oh[np.arange(batch_size), actions] = 1.0
        inp = build_input(z, Es, Ds, a_oh, colors, labels)
        pred = head(inp)  # (batch, out_dim)

        if condition in ("vector_dV_head", "oracle_role_labels"):
            target = torch.from_numpy(np.stack([observed_dE, observed_dD], axis=-1)).to(device)
            loss = F.mse_loss(pred, target)
        elif condition == "scalar_drive_head":
            # Δdrive = drive(after) - drive(before) = w_E * (-ΔE) + w_D * ΔD
            target = torch.from_numpy(
                (train_w_E * (-observed_dE) + train_w_D * observed_dD).astype(np.float32)
            ).unsqueeze(-1).to(device)
            loss = F.mse_loss(pred, target)
        elif condition == "energy_only_head":
            target = torch.from_numpy(observed_dE.astype(np.float32)).unsqueeze(-1).to(device)
            loss = F.mse_loss(pred, target)
        elif condition == "damage_only_head":
            target = torch.from_numpy(observed_dD.astype(np.float32)).unsqueeze(-1).to(device)
            loss = F.mse_loss(pred, target)
        else:
            raise ValueError(condition)

        opt.zero_grad(); loss.backward(); opt.step()

    encoder.eval(); head.eval()

    # ============ Eval under each weight context ============
    def predict_action(z, E, D, c, l, w_E, w_D):
        """Plan: pick action that maximizes drive reduction."""
        with torch.no_grad():
            scores = np.zeros(2)
            for a in range(2):
                a_oh = torch.zeros(1, 2, device=device); a_oh[0, a] = 1.0
                inp = build_input(z, E, D, a_oh,
                                  colors=np.array([c]),
                                  labels=np.array([l]))
                pred = head(inp).cpu().numpy().flatten()
                if condition in ("vector_dV_head", "oracle_role_labels"):
                    pdE, pdD = float(pred[0]), float(pred[1])
                elif condition == "scalar_drive_head":
                    # The head predicts Δdrive at TRAINING weights, which
                    # is the score we want to MINIMIZE (low Δdrive = drive
                    # went down = good). But we can't re-weight for new
                    # contexts. So scalar head essentially uses training
                    # weights regardless. Score = -predicted_Δdrive.
                    scores[a] = -float(pred[0])
                    continue
                elif condition == "energy_only_head":
                    pdE = float(pred[0]); pdD = 0.0  # assume no damage effect
                elif condition == "damage_only_head":
                    pdE = 0.0; pdD = float(pred[0])  # assume no energy effect
                # Drive reduction = -Δdrive = w_E * ΔE - w_D * ΔD
                scores[a] = w_E * pdE - w_D * pdD
            return int(np.argmax(scores))

    eval_results_by_context = {}
    for ctx_name, w_E, w_D in EVAL_WEIGHTS:
        rng_eval = np.random.RandomState(seed + 9999 + hash(ctx_name) % 1000)
        episode_returns = []
        action_acc_records = []
        per_role_actions = {role: {"correct": 0, "total": 0} for role in ROLE_IDX}
        for _ in range(eval_episodes):
            E = ENERGY_INIT; D = DAMAGE_INIT
            steps = 0
            while E > 0 and D < 1.0 and steps < T_MAX:
                idx = rng_eval.randint(0, len(ITEMS))
                c_, l_ = ITEMS[idx]
                obs_ = encode_one(c_, l_, rng_eval)
                x = torch.from_numpy(obs_[None]).float().to(device)
                with torch.no_grad():
                    z = encoder(x)
                action = predict_action(z, E, D, c_, l_, w_E, w_D)
                # compute true drive reduction for each action to judge optimality
                _, _, dE_consume, dD_consume = apply_action(1, E, D, c_, l_)
                _, _, dE_skip, dD_skip = apply_action(0, E, D, c_, l_)
                score_consume = w_E * dE_consume - w_D * dD_consume
                score_skip = w_E * dE_skip - w_D * dD_skip
                optimal_action = 1 if score_consume > score_skip else 0
                role = role_of(c_, l_)
                per_role_actions[role]["total"] += 1
                if action == optimal_action:
                    per_role_actions[role]["correct"] += 1
                action_acc_records.append(int(action == optimal_action))
                # take action
                new_E, new_D, _, _ = apply_action(action, E, D, c_, l_)
                E = new_E; D = new_D
                steps += 1
            episode_returns.append(float(steps))
        import numpy as _np
        eval_results_by_context[ctx_name] = dict(
            w_E=w_E, w_D=w_D,
            mean_return=float(_np.mean(episode_returns)),
            action_accuracy=float(_np.mean(action_acc_records)),
            per_role_accuracy={
                role: (
                    float(per_role_actions[role]["correct"] / per_role_actions[role]["total"])
                    if per_role_actions[role]["total"] > 0 else None
                )
                for role in ROLE_IDX
            },
        )

    # ============ Tapestry geometry — effect-vector RSA ============
    # Compute encoder embeddings for each item type (averaging over noise).
    # Then compute pairwise distances and correlate with effect-vector distances.
    import numpy as _np
    role_embeddings = {}
    role_effects = {}
    n_samples_per_role = 64
    rng_geom = _np.random.RandomState(seed + 1234)
    for (c, l), info in ITEM_TYPES.items():
        role = info["role"]
        obs_l = [encode_one(c, l, rng_geom) for _ in range(n_samples_per_role)]
        obs_arr = _np.stack(obs_l)
        with torch.no_grad():
            z = encoder(torch.from_numpy(obs_arr).to(device)).cpu().numpy()
        role_embeddings[role] = z.mean(axis=0)
        role_effects[role] = _np.array([info["dE"], info["dD"]])

    # Pairwise distances
    roles = list(role_embeddings.keys())
    n_roles = len(roles)
    pairs = []
    for i in range(n_roles):
        for j in range(i + 1, n_roles):
            lat_dist = float(_np.linalg.norm(role_embeddings[roles[i]] - role_embeddings[roles[j]]))
            eff_dist = float(_np.linalg.norm(role_effects[roles[i]] - role_effects[roles[j]]))
            pairs.append(dict(role_i=roles[i], role_j=roles[j],
                              latent_distance=lat_dist, effect_distance=eff_dist))
    lat_d = _np.array([p["latent_distance"] for p in pairs])
    eff_d = _np.array([p["effect_distance"] for p in pairs])
    if _np.std(lat_d) > 1e-9 and _np.std(eff_d) > 1e-9:
        rsa_corr = float(_np.corrcoef(lat_d, eff_d)[0, 1])
    else:
        rsa_corr = float("nan")

    return dict(
        seed=seed,
        condition=condition,
        eval_results=eval_results_by_context,
        rsa_correlation=rsa_corr,
        role_pairs=pairs,
    )


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    n_train_steps: int = 1500,
    batch_size: int = 64,
    eval_episodes: int = 50,
    out: str = "artifacts/valence_tapestry/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    cell_args = []
    for sd in seed_list:
        for cond in ALL_CONDITIONS:
            cell_args.append(dict(
                seed=sd, condition=cond,
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
        row = dict(
            seed=r["seed"], condition=r["condition"],
            rsa_correlation=r["rsa_correlation"],
        )
        for ctx_name, _, _ in EVAL_WEIGHTS:
            ev = r["eval_results"][ctx_name]
            row[f"{ctx_name}_return"] = ev["mean_return"]
            row[f"{ctx_name}_accuracy"] = ev["action_accuracy"]
            for role in ROLE_IDX:
                acc = ev["per_role_accuracy"].get(role)
                row[f"{ctx_name}_role_{role}_acc"] = acc
        summary_rows.append(row)

    out_path.write_text(json.dumps({
        "manifest": dict(
            seeds=seed_list, conditions=ALL_CONDITIONS,
            eval_weights=EVAL_WEIGHTS,
            n_train_steps=n_train_steps, batch_size=batch_size,
            eval_episodes=eval_episodes,
            item_types={f"{c},{l}": info for (c, l), info in ITEM_TYPES.items()},
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nsummary ({len(summary_rows)} cells):")
    print(f"{'condition':<24} {'seed':>10} | "
          f"{'bal_ret':>7} {'hng_ret':>7} {'inj_ret':>7} | {'rsa':>5}")
    for r in summary_rows:
        rsa = "  --  " if (r["rsa_correlation"] is None or
                          (isinstance(r["rsa_correlation"], float) and r["rsa_correlation"] != r["rsa_correlation"])) else f"{r['rsa_correlation']:+.2f}"
        print(f"  {r['condition']:<22} {r['seed']:>10} | "
              f"{r['balanced_return']:>6.1f} {r['hungry_priority_return']:>6.1f} "
              f"{r['injured_priority_return']:>6.1f} | {rsa:>5}")
