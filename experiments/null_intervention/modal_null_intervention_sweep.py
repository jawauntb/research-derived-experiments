#!/usr/bin/env python3
"""Paper 16b — Identifiability Through Intervention.

Paper 16 found that architectural factorization (self_head sees action,
world_head doesn't) is gauge-symmetric: the two sub-heads can split
the joint prediction arbitrarily, and architecture alone is
insufficient to recover the true self/world decomposition.

This paper adds a NULL action — a no-op that has zero item self-effect
but is still subject to the world's exogenous shocks. Observed ΔE
under null is a direct measurement of the world component.

When the training loss treats null observations as world-only
supervision (self_head's contribution is masked to 0 for null
actions), the world_head is pinned to its true value. The gauge
symmetry breaks: self_head must take up the residual.

This is the active-inference / reafference operationalization: the
agent learns the self/world boundary through the act of NOT acting.

Five conditions × 3 seeds = 15 cells:
  - total_dV_head             : Paper 16 baseline (no factorization)
  - factorized_no_null        : Paper 16 failure baseline (2 actions)
  - factorized_null_passive   : 3 actions including null; loss is
                                just total MSE (gauge symmetry persists?)
  - factorized_null_anchor    : HEADLINE. For null actions, train ONLY
                                world_head on observed ΔE (self_head
                                contribution masked to 0). For
                                consume/skip, train sum on total target.
  - oracle_source             : explicit per-sample self/world labels
                                (upper bound)

Training shock distribution: P(shock | food) = 0.8, otherwise 0.1.
Shock magnitude = +0.30.

Evaluation under both shock distributions (in-distribution and
shifted: shock correlation moves to medicine).

Pre-registered gates (focus on component recovery):
  G1 active identifiability: factorized_null_anchor self_pred for
     food consume within ±0.15 of true (+0.96).
  G2 gauge breaking: factorized_null_anchor world_pred for food
     within ±0.10 of true world expectation
     (P(shock|food) × shock_magnitude = 0.24).
  G3 false-credit reduction: factorized_null_anchor's food self_pred
     bias reduces by ≥ 70% vs factorized_no_null (Paper 16: +0.51
     overshoot → target ≤ +0.15).
  G4 transfer stability: under shifted shock, factorized_null_anchor's
     self component changes by < 0.10 vs in-dist; factorized_no_null
     changes by ≥ 0.20.

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/null_intervention/modal_null_intervention_sweep.py
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

app = modal.App(name="research-derived-null-intervention")

ITEM_TYPES = {
    (0, 0): {"role": "food", "dE_consume": +1.0},
    (0, 1): {"role": "poison", "dE_consume": -1.0},
    (1, 0): {"role": "medicine", "dE_consume": -0.1},
    (1, 1): {"role": "neutral", "dE_consume": 0.0},
}
ITEMS = list(ITEM_TYPES.keys())
ROLE_IDX = {"food": 0, "poison": 1, "medicine": 2, "neutral": 3}

EMBED_DIM = 32
OBS_NOISE = 0.15
T_MAX = 50
ENERGY_DECAY = 0.04
ENERGY_INIT = 0.5
SHOCK_MAGNITUDE = 0.30

# Actions: 0=skip, 1=consume, 2=null
# skip and null are dynamically identical (both ΔE = -decay + world shock)
# but the agent's data-collection labels them differently.
N_ACTIONS_WITH_NULL = 3
N_ACTIONS_NO_NULL = 2

TRAINING_SHOCK = {"food": 0.8, "poison": 0.1, "medicine": 0.1, "neutral": 0.1}
SHIFTED_SHOCK = {"food": 0.1, "poison": 0.1, "medicine": 0.8, "neutral": 0.1}

ALL_CONDITIONS = [
    "total_dV_head",
    "factorized_no_null",
    "factorized_null_passive",
    "factorized_null_anchor",
    "oracle_source",
]


def role_of(c, l):
    return ITEM_TYPES[(c, l)]["role"]


def consume_self_dE(c, l):
    return ITEM_TYPES[(c, l)]["dE_consume"]


def sample_world_shock(c, l, shock_dist, rng):
    role = role_of(c, l)
    p = shock_dist[role]
    if rng.rand() < p:
        return SHOCK_MAGNITUDE
    return 0.0


def true_world_expectation(c, l, shock_dist):
    role = role_of(c, l)
    return shock_dist[role] * SHOCK_MAGNITUDE


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

    has_null = condition not in ("total_dV_head", "factorized_no_null")
    n_actions = N_ACTIONS_WITH_NULL if has_null else N_ACTIONS_NO_NULL

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

    def action_self_dE(action, c, l):
        """Self component (action-conditional, including decay)."""
        if action == 1:
            return consume_self_dE(c, l) - ENERGY_DECAY
        else:
            # skip or null: no item self effect, just decay
            return -ENERGY_DECAY

    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)

    if condition == "total_dV_head":
        head = nn.Sequential(
            nn.Linear(EMBED_DIM + 7 + n_actions, 32), nn.Tanh(),
            nn.Linear(32, 1),
        ).to(device)
        self_head = head
        world_head = None
    else:
        # All factorized/oracle conditions
        self_head = nn.Sequential(
            nn.Linear(EMBED_DIM + 7 + n_actions, 32), nn.Tanh(),
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
        # Sample batch
        idxs = rng_train.randint(0, len(ITEMS), size=batch_size)
        colors = np.array([ITEMS[i][0] for i in idxs])
        labels = np.array([ITEMS[i][1] for i in idxs])
        Es = rng_train.uniform(0.0, 1.0, size=batch_size).astype(np.float32)
        actions = rng_train.randint(0, n_actions, size=batch_size).astype(np.int64)
        # Compute self/world/total ΔE
        self_dE = np.zeros(batch_size, dtype=np.float32)
        world_dE = np.zeros(batch_size, dtype=np.float32)
        for i in range(batch_size):
            self_dE[i] = action_self_dE(int(actions[i]), int(colors[i]), int(labels[i]))
            world_dE[i] = sample_world_shock(int(colors[i]), int(labels[i]),
                                              TRAINING_SHOCK, rng_train)
        total_dE = self_dE + world_dE

        obs = np.stack([encode_one(c, l, rng_train) for c, l in zip(colors, labels)])
        x = torch.from_numpy(obs).to(device)
        z = encoder(x)
        e_t = torch.from_numpy(Es.reshape(-1, 1)).to(device)
        ffE = fourier_E(e_t)
        a_oh = torch.zeros(batch_size, n_actions, device=device)
        a_oh[np.arange(batch_size), actions] = 1.0
        self_input = torch.cat([z, ffE, a_oh], dim=-1)

        if condition == "total_dV_head":
            pred = self_head(self_input).squeeze(-1)
            target = torch.from_numpy(total_dE).to(device)
            loss = F.mse_loss(pred, target)
        elif condition == "factorized_no_null":
            world_input = torch.cat([z, ffE], dim=-1)
            pred_self = self_head(self_input).squeeze(-1)
            pred_world = world_head(world_input).squeeze(-1)
            loss = F.mse_loss(pred_self + pred_world,
                              torch.from_numpy(total_dE).to(device))
        elif condition == "factorized_null_passive":
            world_input = torch.cat([z, ffE], dim=-1)
            pred_self = self_head(self_input).squeeze(-1)
            pred_world = world_head(world_input).squeeze(-1)
            loss = F.mse_loss(pred_self + pred_world,
                              torch.from_numpy(total_dE).to(device))
        elif condition == "factorized_null_anchor":
            # HEADLINE: for null actions (action=2), train ONLY world_head
            # on observed ΔE. For other actions, train sum on total target.
            world_input = torch.cat([z, ffE], dim=-1)
            pred_self = self_head(self_input).squeeze(-1)
            pred_world = world_head(world_input).squeeze(-1)
            null_mask = (actions == 2)
            non_null_mask = ~null_mask
            target_total = torch.from_numpy(total_dE).to(device)
            # For null: world_pred should predict observed ΔE; self is "free"
            # but we want it to NOT contribute. So include a loss that drives
            # self_pred(null) to 0 explicitly:
            null_loss = torch.tensor(0.0, device=device)
            if null_mask.any():
                # World-only supervision: world_pred(z) should match
                # observed_total_ΔE under null
                null_world_loss = F.mse_loss(
                    pred_world[null_mask], target_total[null_mask]
                )
                # Anchor self_pred(null) toward 0 (so it doesn't compete)
                null_self_anchor = F.mse_loss(
                    pred_self[null_mask],
                    torch.full_like(pred_self[null_mask], -ENERGY_DECAY)
                )
                null_loss = null_world_loss + 0.5 * null_self_anchor
            non_null_loss = torch.tensor(0.0, device=device)
            if non_null_mask.any():
                # Joint sum target on consume/skip
                non_null_loss = F.mse_loss(
                    pred_self[non_null_mask] + pred_world[non_null_mask],
                    target_total[non_null_mask]
                )
            loss = null_loss + non_null_loss
        elif condition == "oracle_source":
            world_input = torch.cat([z, ffE], dim=-1)
            pred_self = self_head(self_input).squeeze(-1)
            pred_world = world_head(world_input).squeeze(-1)
            target_self = torch.from_numpy(self_dE).to(device)
            target_world = torch.from_numpy(world_dE).to(device)
            loss = F.mse_loss(pred_self, target_self) + F.mse_loss(pred_world, target_world)
        else:
            raise ValueError(condition)

        opt.zero_grad(); loss.backward(); opt.step()

    encoder.eval(); self_head.eval()
    if world_head is not None:
        world_head.eval()

    # ============ Component recovery diagnostics ============
    # For each item, predict self_consume, self_skip, self_null (if has_null), and world.
    # Compare to ground truth.
    rng_diag = np.random.RandomState(seed + 333)
    n_diag = 128
    pred_by_role = {}
    for (c, l), info in ITEM_TYPES.items():
        role = info["role"]
        obs_list = [encode_one(c, l, rng_diag) for _ in range(n_diag)]
        obs_arr = np.stack(obs_list)
        with torch.no_grad():
            z = encoder(torch.from_numpy(obs_arr).to(device))
            e_t = torch.full((n_diag, 1), 0.5, dtype=torch.float32, device=device)
            ffE = fourier_E(e_t)
            results = {}
            for action_idx in range(n_actions):
                a_oh = torch.zeros(n_diag, n_actions, device=device)
                a_oh[:, action_idx] = 1.0
                inp = torch.cat([z, ffE, a_oh], dim=-1)
                pred_s = self_head(inp).squeeze(-1).cpu().numpy()
                results[f"self_action_{action_idx}"] = float(pred_s.mean())
            if world_head is not None:
                world_input = torch.cat([z, ffE], dim=-1)
                pred_w = world_head(world_input).squeeze(-1).cpu().numpy()
                results["world"] = float(pred_w.mean())
        # True values
        results["true_self_consume"] = consume_self_dE(c, l) - ENERGY_DECAY
        results["true_self_skip_or_null"] = -ENERGY_DECAY
        results["true_world_in_dist"] = true_world_expectation(c, l, TRAINING_SHOCK)
        results["true_world_shift"] = true_world_expectation(c, l, SHIFTED_SHOCK)
        pred_by_role[role] = results

    # ============ Eval under both distributions ============
    def plan_action(z, E_now):
        with torch.no_grad():
            e_t = torch.full((z.shape[0], 1), float(E_now),
                             dtype=torch.float32, device=device)
            ffE = fourier_E(e_t)
            scores = np.zeros(2)  # planner picks consume/skip only (not null)
            for a in [0, 1]:  # skip, consume
                a_oh = torch.zeros(z.shape[0], n_actions, device=device)
                a_oh[:, a] = 1.0
                inp = torch.cat([z, ffE, a_oh], dim=-1)
                scores[a] = self_head(inp).item()
            return int(np.argmax(scores))

    def eval_under(shock_dist, dist_name):
        rng_eval = np.random.RandomState(seed + 9999 + hash(dist_name) % 1000)
        returns = []
        acc_records = []
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
                action = plan_action(z, E)
                self_step = action_self_dE(action, c_, l_)
                world_step = sample_world_shock(c_, l_, shock_dist, rng_eval)
                optimal = 1 if consume_self_dE(c_, l_) > 0 else 0
                acc_records.append(int(action == optimal))
                E = max(0.0, min(1.0, E + self_step + world_step))
                steps += 1
            returns.append(float(steps))
        import numpy as _np
        return dict(
            distribution=dist_name,
            mean_return=float(_np.mean(returns)),
            action_accuracy=float(_np.mean(acc_records)),
        )

    in_dist = eval_under(TRAINING_SHOCK, "in_dist")
    shifted = eval_under(SHIFTED_SHOCK, "shifted")

    return dict(
        seed=seed,
        condition=condition,
        has_null=has_null,
        n_actions=n_actions,
        in_dist_eval=in_dist,
        shifted_eval=shifted,
        prediction_by_role=pred_by_role,
    )


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    n_train_steps: int = 1500,
    batch_size: int = 64,
    eval_episodes: int = 50,
    out: str = "artifacts/null_intervention/sweep_v1.json",
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
            has_null=r["has_null"],
            in_dist_return=r["in_dist_eval"]["mean_return"],
            in_dist_acc=r["in_dist_eval"]["action_accuracy"],
            shifted_return=r["shifted_eval"]["mean_return"],
            shifted_acc=r["shifted_eval"]["action_accuracy"],
        )
        for role, info in r["prediction_by_role"].items():
            row[f"pred_self_consume_{role}"] = info["self_action_1"]
            row[f"pred_self_skip_{role}"] = info["self_action_0"]
            if "self_action_2" in info:
                row[f"pred_self_null_{role}"] = info["self_action_2"]
            if "world" in info:
                row[f"pred_world_{role}"] = info["world"]
            row[f"true_self_consume_{role}"] = info["true_self_consume"]
            row[f"true_self_skip_or_null_{role}"] = info["true_self_skip_or_null"]
            row[f"true_world_in_dist_{role}"] = info["true_world_in_dist"]
            row[f"true_world_shift_{role}"] = info["true_world_shift"]
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
    print(f"{'condition':<26} {'seed':>10} | "
          f"{'ps_food':>7} {'pw_food':>7} {'ps_med':>7} {'ret_id':>6} {'ret_sh':>6}")
    print(f"  TRUE FOOD: self_consume=+0.96, world_in_dist=+0.24, world_shift=+0.03")
    for r in summary_rows:
        psw = r.get('pred_world_food', None)
        psw_str = f"{psw:+.3f}" if psw is not None else "  --  "
        print(f"  {r['condition']:<24} {r['seed']:>10} | "
              f"{r['pred_self_consume_food']:>+.3f} {psw_str:>7} "
              f"{r['pred_self_consume_medicine']:>+.3f} "
              f"{r['in_dist_return']:>5.1f} {r['shifted_return']:>5.1f}")
