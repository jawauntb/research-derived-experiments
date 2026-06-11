#!/usr/bin/env python3
"""Paper 16 — First-Order Self / Reafference.

The first self/world attribution test in the program. An agent observes
viability change ΔE that has two sources:
  - self-caused: the agent's action × the item it interacted with
  - world-caused: an exogenous shock that depends on observable cues
                  (here: item identity) but NOT on the agent's action

Training: shock correlates with item 0 (food): P(shock | item 0) = 0.8;
otherwise 0.1.

Shifted eval: shock correlation MOVES to item 2 (medicine):
P(shock | item 2) = 0.8; otherwise 0.1.

The factorized model has two sub-heads with architectural separation:
  - self_head sees (z, E, action) and learns the action-conditional
    component of ΔE.
  - world_head sees (z, E) only, NO action, and learns the action-
    independent component.

This is a minimal computational analogue of Bennett's first-order
self / Levin's "computational boundary of self" / Sperry-Holst
reafference: separating self-caused from world-caused change.

Conditions (4 × 3 seeds = 12 cells):
  - total_dV_head            : single head (z, E, action) → ΔE_total.
                                BASELINE — no factorization.
  - factorized_self_world    : self + world heads, MSE on total ΔE.
                                HEADLINE.
  - oracle_source            : same architecture, each sub-head trained
                                with oracle self/world component labels.
                                UPPER BOUND.
  - shuffled_source          : oracle architecture, but with shuffled
                                source labels. CONTROL.

Each cell is evaluated under TWO contexts: in-distribution and shifted.

Planning: greedy argmax over predicted SELF component only (the agent
treats world component as exogenous). For total_dV_head, the planner
uses predicted total ΔE (it can't separate). For oracle/factorized,
the planner uses self component.

Pre-registered gates:
  G1 (factorization transfer): factorized return under SHIFT ≥
     total return under SHIFT + 5.
  G2 (false credit): factorized self_pred for food consume is more
     stable between in-dist and shift than total model's prediction.
     Specifically: |factorized self_pred(food, consume)_shift −
                     factorized self_pred(food, consume)_in_dist|
                   < |total pred(food, consume)_shift −
                     total pred(food, consume)_in_dist|.
  G3 (oracle sanity): oracle return on shifted ≥ factorized return
     on shifted (within noise).
  G4 (shuffled control): shuffled return on shifted < factorized
     return on shifted.

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/first_order_self/modal_first_order_self_sweep.py
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

app = modal.App(name="research-derived-first-order-self")

# Item types: 4 roles via (color, label)
# 0=food, 1=poison, 2=medicine, 3=neutral
ITEM_TYPES = {
    (0, 0): {"role": "food", "dE_consume": +1.0},
    (0, 1): {"role": "poison", "dE_consume": -1.0},
    (1, 0): {"role": "medicine", "dE_consume": -0.1},
    (1, 1): {"role": "neutral", "dE_consume": 0.0},
}
ITEMS = list(ITEM_TYPES.keys())
ROLE_IDX = {"food": 0, "poison": 1, "medicine": 2, "neutral": 3}
N_COLORS = 2
N_LABELS = 2

EMBED_DIM = 32
OBS_NOISE = 0.15
T_MAX = 50
ENERGY_DECAY = 0.04
ENERGY_INIT = 0.5
SHOCK_MAGNITUDE = 0.30

# Shock distributions
TRAINING_SHOCK = {
    "food": 0.8, "poison": 0.1, "medicine": 0.1, "neutral": 0.1,
}
SHIFTED_SHOCK = {
    "food": 0.1, "poison": 0.1, "medicine": 0.8, "neutral": 0.1,
}

ALL_CONDITIONS = [
    "total_dV_head",
    "factorized_self_world",
    "oracle_source",
    "shuffled_source",
]


def role_of(c, l):
    return ITEM_TYPES[(c, l)]["role"]


def consume_self_dE(c, l):
    return ITEM_TYPES[(c, l)]["dE_consume"]


def sample_world_shock(c, l, shock_dist, rng):
    """Sample world shock for this item under the given distribution."""
    role = role_of(c, l)
    p = shock_dist[role]
    if rng.rand() < p:
        return SHOCK_MAGNITUDE
    return 0.0


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
    perm = rng_env.permutation(16)

    def encode_one(c, l, rng):
        obs = np.zeros(16, dtype=np.float32)
        obs[c] = 1.0
        obs[8 + l] = 1.0
        obs = obs + rng.randn(16).astype(np.float32) * OBS_NOISE
        return obs[perm]

    def fourier_E(E_tensor):
        if E_tensor.dim() == 2:
            E_tensor = E_tensor.squeeze(-1)
        feats = [E_tensor.unsqueeze(-1)]
        for freq in [1.0, 2.0, 4.0]:
            feats.append(torch.sin(torch.pi * freq * E_tensor).unsqueeze(-1))
            feats.append(torch.cos(torch.pi * freq * E_tensor).unsqueeze(-1))
        return torch.cat(feats, dim=-1)

    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)

    # Head architectures depend on condition
    # All conditions use: encoder + Fourier features of E
    # self_head input: (z [32] + ffE [7] + action_oh [2]) = 41
    # world_head input: (z [32] + ffE [7]) = 39 (no action)
    # total_head input: same as self_head = 41
    if condition == "total_dV_head":
        head = nn.Sequential(
            nn.Linear(EMBED_DIM + 7 + 2, 32), nn.Tanh(),
            nn.Linear(32, 1),
        ).to(device)
        self_head = head
        world_head = None
    else:
        # factorized, oracle, shuffled all use 2-head architecture
        self_head = nn.Sequential(
            nn.Linear(EMBED_DIM + 7 + 2, 32), nn.Tanh(),
            nn.Linear(32, 1),
        ).to(device)
        world_head = nn.Sequential(
            nn.Linear(EMBED_DIM + 7, 32), nn.Tanh(),
            nn.Linear(32, 1),
        ).to(device)

    params = list(encoder.parameters()) + list(self_head.parameters())
    if world_head is not None:
        params += list(world_head.parameters())
    opt = torch.optim.Adam(params, lr=2e-3)

    # ============ Training ============
    rng_train = np.random.RandomState(seed + 47)

    for step in range(n_train_steps):
        # Sample off-policy batch
        idxs = rng_train.randint(0, len(ITEMS), size=batch_size)
        colors = np.array([ITEMS[i][0] for i in idxs])
        labels = np.array([ITEMS[i][1] for i in idxs])
        Es = rng_train.uniform(0.0, 1.0, size=batch_size).astype(np.float32)
        actions = rng_train.randint(0, 2, size=batch_size).astype(np.int64)
        # Compute self_dE and world_dE per sample
        self_dE = np.zeros(batch_size, dtype=np.float32)
        world_dE = np.zeros(batch_size, dtype=np.float32)
        for i in range(batch_size):
            # self: action-conditional effect, including decay
            if actions[i] == 1:
                self_dE[i] = consume_self_dE(int(colors[i]), int(labels[i])) - ENERGY_DECAY
            else:
                self_dE[i] = -ENERGY_DECAY
            world_dE[i] = sample_world_shock(int(colors[i]), int(labels[i]),
                                              TRAINING_SHOCK, rng_train)
        total_dE = self_dE + world_dE
        # Clip total to valid energy bounds
        # (don't clip targets — the head should predict raw dE; clipping is for env dynamics)

        obs = np.stack([encode_one(c, l, rng_train) for c, l in zip(colors, labels)])
        x = torch.from_numpy(obs).to(device)
        z = encoder(x)
        e_t = torch.from_numpy(Es.reshape(-1, 1)).to(device)
        ffE = fourier_E(e_t)
        a_oh = torch.zeros(batch_size, 2, device=device)
        a_oh[np.arange(batch_size), actions] = 1.0
        self_input = torch.cat([z, ffE, a_oh], dim=-1)

        if condition == "total_dV_head":
            pred_total = self_head(self_input).squeeze(-1)
            target = torch.from_numpy(total_dE).to(device)
            loss = F.mse_loss(pred_total, target)
        elif condition == "factorized_self_world":
            world_input = torch.cat([z, ffE], dim=-1)
            pred_self = self_head(self_input).squeeze(-1)
            pred_world = world_head(world_input).squeeze(-1)
            pred_total = pred_self + pred_world
            target = torch.from_numpy(total_dE).to(device)
            loss = F.mse_loss(pred_total, target)
        elif condition == "oracle_source":
            world_input = torch.cat([z, ffE], dim=-1)
            pred_self = self_head(self_input).squeeze(-1)
            pred_world = world_head(world_input).squeeze(-1)
            target_self = torch.from_numpy(self_dE).to(device)
            target_world = torch.from_numpy(world_dE).to(device)
            loss = F.mse_loss(pred_self, target_self) + F.mse_loss(pred_world, target_world)
        elif condition == "shuffled_source":
            # Shuffle source labels: each pred head gets a randomly-assigned target
            world_input = torch.cat([z, ffE], dim=-1)
            pred_self = self_head(self_input).squeeze(-1)
            pred_world = world_head(world_input).squeeze(-1)
            # Swap targets randomly per-sample with prob 0.5
            swap_mask = rng_train.rand(batch_size) < 0.5
            target_self_arr = np.where(swap_mask, world_dE, self_dE).astype(np.float32)
            target_world_arr = np.where(swap_mask, self_dE, world_dE).astype(np.float32)
            target_self = torch.from_numpy(target_self_arr).to(device)
            target_world = torch.from_numpy(target_world_arr).to(device)
            loss = F.mse_loss(pred_self, target_self) + F.mse_loss(pred_world, target_world)
        else:
            raise ValueError(condition)

        opt.zero_grad(); loss.backward(); opt.step()

    encoder.eval(); self_head.eval()
    if world_head is not None:
        world_head.eval()

    # ============ Planning ============
    def plan_action(z, E_now, c, l):
        with torch.no_grad():
            e_t = torch.full((z.shape[0], 1), float(E_now),
                             dtype=torch.float32, device=device)
            ffE = fourier_E(e_t)
            scores = np.zeros(2)
            for a in range(2):
                a_oh = torch.zeros(z.shape[0], 2, device=device); a_oh[:, a] = 1.0
                self_input = torch.cat([z, ffE, a_oh], dim=-1)
                if condition == "total_dV_head":
                    # Total model uses its total prediction for action choice
                    scores[a] = self_head(self_input).item()
                else:
                    # Factorized/oracle/shuffled use SELF component only
                    scores[a] = self_head(self_input).item()
            return int(np.argmax(scores))

    # ============ Eval under both distributions ============
    def eval_under_distribution(shock_dist, distribution_name):
        rng_eval = np.random.RandomState(seed + 9999 + hash(distribution_name) % 1000)
        episode_returns = []
        action_acc_records = []
        per_role_acc = {role: {"correct": 0, "total": 0} for role in ROLE_IDX}
        for _ in range(eval_episodes):
            E = ENERGY_INIT
            steps = 0
            while E > 0 and steps < T_MAX:
                idx = rng_eval.randint(0, len(ITEMS))
                c_, l_ = ITEMS[idx]
                obs_ = encode_one(c_, l_, rng_eval)
                x = torch.from_numpy(obs_[None]).float().to(device)
                with torch.no_grad():
                    z = encoder(x)
                action = plan_action(z, E, c_, l_)
                # Compute actual ΔE for this step
                self_dE_step = (consume_self_dE(c_, l_) - ENERGY_DECAY) if action == 1 else -ENERGY_DECAY
                world_dE_step = sample_world_shock(c_, l_, shock_dist, rng_eval)
                # Determine optimal action from SELF component (the agent's controllable part)
                # Skip self = -decay; consume self = consume_dE - decay
                # Optimal: choose consume iff consume_dE > 0
                optimal = 1 if consume_self_dE(c_, l_) > 0 else 0
                role = role_of(c_, l_)
                per_role_acc[role]["total"] += 1
                if action == optimal:
                    per_role_acc[role]["correct"] += 1
                    action_acc_records.append(1)
                else:
                    action_acc_records.append(0)
                # Apply combined ΔE to E
                E = max(0.0, min(1.0, E + self_dE_step + world_dE_step))
                steps += 1
            episode_returns.append(float(steps))
        import numpy as _np
        return dict(
            distribution=distribution_name,
            mean_return=float(_np.mean(episode_returns)),
            action_accuracy=float(_np.mean(action_acc_records)),
            per_role_accuracy={
                role: (
                    float(per_role_acc[role]["correct"] / per_role_acc[role]["total"])
                    if per_role_acc[role]["total"] > 0 else None
                )
                for role in ROLE_IDX
            },
        )

    in_dist_eval = eval_under_distribution(TRAINING_SHOCK, "in_distribution")
    shifted_eval = eval_under_distribution(SHIFTED_SHOCK, "shifted")

    # ============ Diagnostic: prediction stability ============
    # For each item, compute predicted ΔE (or self component) at fixed E=0.5
    # for consume action. Compare predictions to ground truth in-dist and shift.
    rng_diag = np.random.RandomState(seed + 333)
    n_diag = 64
    pred_by_role = {role: {"pred_consume": [], "true_in_dist_consume": [],
                            "true_shift_consume": []}
                    for role in ROLE_IDX}
    for _ in range(n_diag):
        for (c, l), info in ITEM_TYPES.items():
            role = info["role"]
            obs = encode_one(c, l, rng_diag)
            with torch.no_grad():
                z = encoder(torch.from_numpy(obs[None]).to(device))
                e_t = torch.full((1, 1), 0.5, dtype=torch.float32, device=device)
                ffE = fourier_E(e_t)
                a_oh = torch.tensor([[0.0, 1.0]], device=device)  # consume
                self_input = torch.cat([z, ffE, a_oh], dim=-1)
                pred_self = self_head(self_input).item()
            pred_by_role[role]["pred_consume"].append(pred_self)
            # True self ΔE for consume: consume_dE - decay
            true_self = consume_self_dE(c, l) - ENERGY_DECAY
            # Expected total in-dist consume: self + avg world shock
            expected_world_in_dist = TRAINING_SHOCK[role] * SHOCK_MAGNITUDE
            expected_world_shift = SHIFTED_SHOCK[role] * SHOCK_MAGNITUDE
            true_total_in_dist = true_self + expected_world_in_dist
            true_total_shift = true_self + expected_world_shift
            pred_by_role[role]["true_in_dist_consume"].append(true_total_in_dist)
            pred_by_role[role]["true_shift_consume"].append(true_total_shift)

    import numpy as _np
    pred_diagnostics = {}
    for role in ROLE_IDX:
        preds = _np.array(pred_by_role[role]["pred_consume"])
        true_id = _np.array(pred_by_role[role]["true_in_dist_consume"])
        true_sh = _np.array(pred_by_role[role]["true_shift_consume"])
        pred_diagnostics[role] = dict(
            mean_pred_consume=float(_np.mean(preds)),
            true_total_in_dist_consume=float(_np.mean(true_id)),
            true_total_shift_consume=float(_np.mean(true_sh)),
            true_self_consume=float(consume_self_dE(*[
                (c, l) for (c, l), info in ITEM_TYPES.items() if info["role"] == role
            ][0]) - ENERGY_DECAY),
        )

    # False-credit metric: how close is pred to TRUE SELF (action effect alone)
    # vs to TRUE TOTAL IN-DIST (which includes the world shock)?
    # For the factorized model, self_head should track true_self.
    # For the total model, head_pred tracks true_total_in_dist.
    return dict(
        seed=seed,
        condition=condition,
        in_dist_eval=in_dist_eval,
        shifted_eval=shifted_eval,
        prediction_diagnostics=pred_diagnostics,
    )


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    n_train_steps: int = 1500,
    batch_size: int = 64,
    eval_episodes: int = 50,
    out: str = "artifacts/first_order_self/sweep_v1.json",
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
            in_dist_return=r["in_dist_eval"]["mean_return"],
            in_dist_acc=r["in_dist_eval"]["action_accuracy"],
            shifted_return=r["shifted_eval"]["mean_return"],
            shifted_acc=r["shifted_eval"]["action_accuracy"],
        )
        for role in ROLE_IDX:
            row[f"in_dist_{role}_acc"] = r["in_dist_eval"]["per_role_accuracy"][role]
            row[f"shifted_{role}_acc"] = r["shifted_eval"]["per_role_accuracy"][role]
            d = r["prediction_diagnostics"][role]
            row[f"pred_{role}_consume"] = d["mean_pred_consume"]
            row[f"true_self_{role}_consume"] = d["true_self_consume"]
            row[f"true_total_in_dist_{role}_consume"] = d["true_total_in_dist_consume"]
            row[f"true_total_shift_{role}_consume"] = d["true_total_shift_consume"]
        summary_rows.append(row)

    out_path.write_text(json.dumps({
        "manifest": dict(
            seeds=seed_list, conditions=ALL_CONDITIONS,
            n_train_steps=n_train_steps, batch_size=batch_size,
            eval_episodes=eval_episodes,
            training_shock=TRAINING_SHOCK,
            shifted_shock=SHIFTED_SHOCK,
            shock_magnitude=SHOCK_MAGNITUDE,
            item_types={f"{c},{l}": info for (c, l), info in ITEM_TYPES.items()},
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nsummary ({len(summary_rows)} cells):")
    print(f"{'condition':<24} {'seed':>10} | "
          f"{'id_ret':>6} {'sh_ret':>6} {'id_acc':>6} {'sh_acc':>6} | "
          f"{'pred_food':>9} {'pred_med':>9}")
    for r in summary_rows:
        print(f"  {r['condition']:<22} {r['seed']:>10} | "
              f"{r['in_dist_return']:>5.1f} {r['shifted_return']:>5.1f} "
              f"{r['in_dist_acc']:>5.2f} {r['shifted_acc']:>5.2f} | "
              f"{r['pred_food_consume']:>+8.3f} {r['pred_medicine_consume']:>+8.3f}")
