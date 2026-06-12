#!/usr/bin/env python3
"""Paper 17A — Learning When Not to Act.

Costly null probes for self/world identifiability in minimal homeostatic agents.

Paper 16b proved that null-anchor intervention breaks the self/world gauge
symmetry. But null actions were experimenter-scheduled. This paper asks
whether a minimal agent can LEARN when to spend a viability-cost null action
to improve attribution, and whether that learned selection actually fires in
states the model is uncertain about (as opposed to "more null data anywhere").

Seven conditions × cost ∈ {0.01, 0.025, 0.04} × 3 seeds, with
matched_random_null_anchor's null rate set to the realized rate of
learned_costly_null_probe at each (cost, seed).

Conditions:
  - factorized_no_null            : Paper 16 failure baseline (n_actions=2)
  - factorized_null_passive       : Null in action space, no anchor loss
  - scheduled_null_anchor         : Experimenter-scheduled null + anchor loss
  - matched_random_null_anchor    : Same null budget as learned, random placement
  - learned_costly_null_probe     : MAIN. Probe-value head decides null fires
  - oracle_uncertainty_probe      : Oracle access to per-state attribution error
  - oracle_source                 : Per-sample self/world labels (16b upper bound)

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/costly_null_probes/modal_costly_null_probes_sweep.py
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

app = modal.App(name="research-derived-costly-null-probes")

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
N_ACTIONS_WITH_NULL = 3
N_ACTIONS_NO_NULL = 2

TRAINING_SHOCK = {"food": 0.8, "poison": 0.1, "medicine": 0.1, "neutral": 0.1}
SHIFTED_SHOCK = {"food": 0.1, "poison": 0.1, "medicine": 0.8, "neutral": 0.1}

COST_HEADLINE = 0.025
COSTS = [0.01, 0.025, 0.04]

ALL_CONDITIONS = [
    "factorized_no_null",
    "factorized_null_passive",
    "scheduled_null_anchor",
    "matched_random_null_anchor",
    "learned_costly_null_probe",
    "oracle_uncertainty_probe",
    "oracle_source",
]

COST_RELEVANT = {"learned_costly_null_probe", "oracle_uncertainty_probe",
                 "matched_random_null_anchor"}
COST_IRRELEVANT = set(ALL_CONDITIONS) - COST_RELEVANT


def role_of(c, l):
    return ITEM_TYPES[(c, l)]["role"]


def consume_self_dE(c, l):
    return ITEM_TYPES[(c, l)]["dE_consume"]


def true_world_expectation(c, l, shock_dist):
    return shock_dist[role_of(c, l)] * SHOCK_MAGNITUDE


@app.function(image=IMAGE, timeout=2400, cpu=4, memory=4096)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    seed: int = arg["seed"]
    condition: str = arg["condition"]
    cost: float = arg["cost"]
    target_null_rate = arg.get("target_null_rate", None)
    n_train_steps: int = arg["n_train_steps"]
    batch_size: int = arg["batch_size"]
    eval_episodes: int = arg["eval_episodes"]

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cpu")
    rng_env = np.random.RandomState(seed + 13)
    perm = rng_env.permutation(16)

    has_null = condition != "factorized_no_null"
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
        if action == 1:
            return consume_self_dE(c, l) - ENERGY_DECAY
        else:
            return -ENERGY_DECAY

    def sample_world_shock_local(c, l, shock_dist, rng):
        role = role_of(c, l)
        if rng.rand() < shock_dist[role]:
            return SHOCK_MAGNITUDE
        return 0.0

    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)
    self_head = nn.Sequential(
        nn.Linear(EMBED_DIM + 7 + n_actions, 32), nn.Tanh(),
        nn.Linear(32, 1),
    ).to(device)
    world_head = nn.Sequential(
        nn.Linear(EMBED_DIM + 7, 32), nn.Tanh(),
        nn.Linear(32, 1),
    ).to(device)

    # Probe-value head (only meaningfully trained for learned_costly_null_probe,
    # but we instantiate it in all factorized conditions for cleanliness).
    v_probe_head = nn.Sequential(
        nn.Linear(EMBED_DIM + 7, 32), nn.Tanh(),
        nn.Linear(32, 1), nn.Softplus(),
    ).to(device)

    params = (list(encoder.parameters()) + list(self_head.parameters())
              + list(world_head.parameters())
              + list(v_probe_head.parameters()))
    opt = torch.optim.Adam(params, lr=2e-3)

    rng_train = np.random.RandomState(seed + 47)

    # ============ Training ============
    for step in range(n_train_steps):
        idxs = rng_train.randint(0, len(ITEMS), size=batch_size)
        colors = np.array([ITEMS[i][0] for i in idxs])
        labels = np.array([ITEMS[i][1] for i in idxs])
        Es = rng_train.uniform(0.0, 1.0, size=batch_size).astype(np.float32)

        # Action sampling depends on condition
        if condition == "factorized_no_null":
            actions = rng_train.randint(0, 2, size=batch_size).astype(np.int64)
        elif condition == "matched_random_null_anchor":
            rate = float(target_null_rate) if target_null_rate is not None else 0.20
            null_choice = (rng_train.rand(batch_size) < rate).astype(np.int64)
            non_null = rng_train.randint(0, 2, size=batch_size).astype(np.int64)
            actions = np.where(null_choice == 1, 2, non_null)
        else:
            # All other null-bearing conditions: uniform over (skip, consume, null)
            actions = rng_train.randint(0, n_actions, size=batch_size).astype(np.int64)

        self_dE = np.zeros(batch_size, dtype=np.float32)
        world_dE = np.zeros(batch_size, dtype=np.float32)
        for i in range(batch_size):
            self_dE[i] = action_self_dE(int(actions[i]),
                                         int(colors[i]), int(labels[i]))
            world_dE[i] = sample_world_shock_local(int(colors[i]),
                                                    int(labels[i]),
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
        world_input = torch.cat([z, ffE], dim=-1)

        pred_self = self_head(self_input).squeeze(-1)
        pred_world = world_head(world_input).squeeze(-1)
        target_total = torch.from_numpy(total_dE).to(device)

        # ----- Main attribution loss -----
        if condition == "factorized_no_null":
            loss = F.mse_loss(pred_self + pred_world, target_total)
        elif condition == "factorized_null_passive":
            loss = F.mse_loss(pred_self + pred_world, target_total)
        elif condition == "oracle_source":
            target_self = torch.from_numpy(self_dE).to(device)
            target_world = torch.from_numpy(world_dE).to(device)
            loss = (F.mse_loss(pred_self, target_self)
                    + F.mse_loss(pred_world, target_world))
        else:
            # All anchor-loss conditions: scheduled, matched_random, learned,
            # oracle_uncertainty share the same training loss form.
            null_mask = torch.from_numpy(actions == 2)
            non_null_mask = ~null_mask
            null_loss = torch.tensor(0.0, device=device)
            non_null_loss = torch.tensor(0.0, device=device)
            if null_mask.any():
                null_world_loss = F.mse_loss(
                    pred_world[null_mask], target_total[null_mask]
                )
                null_self_anchor = F.mse_loss(
                    pred_self[null_mask],
                    torch.full_like(pred_self[null_mask], -ENERGY_DECAY),
                )
                null_loss = null_world_loss + 0.5 * null_self_anchor
            if non_null_mask.any():
                non_null_loss = F.mse_loss(
                    pred_self[non_null_mask] + pred_world[non_null_mask],
                    target_total[non_null_mask],
                )
            loss = null_loss + non_null_loss

        # ----- V_probe auxiliary loss (only meaningful when there are nulls) -----
        if condition not in ("factorized_no_null",):
            null_mask = torch.from_numpy(actions == 2)
            if null_mask.any():
                # Target: |pred_world - observed_total| at null observations.
                # Detach pred_world so gradient flows only into v_probe via its loss.
                with torch.no_grad():
                    residual_target = (pred_world[null_mask].detach()
                                       - target_total[null_mask]).abs()
                v_pred = v_probe_head(world_input[null_mask]).squeeze(-1)
                v_loss = F.mse_loss(v_pred, residual_target)
                loss = loss + 0.5 * v_loss

        opt.zero_grad()
        loss.backward()
        opt.step()

    encoder.eval(); self_head.eval(); world_head.eval(); v_probe_head.eval()

    # ============ Component-recovery diagnostics ============
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
            world_input = torch.cat([z, ffE], dim=-1)
            pred_w = world_head(world_input).squeeze(-1).cpu().numpy()
            results["world"] = float(pred_w.mean())
            v_pred = v_probe_head(world_input).squeeze(-1).cpu().numpy()
            results["v_probe"] = float(v_pred.mean())
        results["true_self_consume"] = consume_self_dE(c, l) - ENERGY_DECAY
        results["true_self_skip_or_null"] = -ENERGY_DECAY
        results["true_world_in_dist"] = true_world_expectation(c, l, TRAINING_SHOCK)
        results["true_world_shift"] = true_world_expectation(c, l, SHIFTED_SHOCK)
        pred_by_role[role] = results

    # ============ Per-state-bucket diagnostics for G6/G7 ============
    # Buckets: role (4) × E_bin (low E<0.5, high E≥0.5) = 8 buckets.
    bucket_diag = {}
    for (c, l), info in ITEM_TYPES.items():
        role = info["role"]
        true_world = true_world_expectation(c, l, TRAINING_SHOCK)
        for E_bin_name, E_val in [("E_low", 0.25), ("E_high", 0.75)]:
            key = f"{role}_{E_bin_name}"
            obs_list = [encode_one(c, l, rng_diag) for _ in range(64)]
            obs_arr = np.stack(obs_list)
            with torch.no_grad():
                z = encoder(torch.from_numpy(obs_arr).to(device))
                e_t = torch.full((64, 1), E_val, dtype=torch.float32, device=device)
                ffE = fourier_E(e_t)
                world_input = torch.cat([z, ffE], dim=-1)
                v_vals = v_probe_head(world_input).squeeze(-1).cpu().numpy()
                w_vals = world_head(world_input).squeeze(-1).cpu().numpy()
            v_probe_mean = float(v_vals.mean())
            world_pred_mean = float(w_vals.mean())
            oracle_uncertainty = abs(world_pred_mean - true_world)
            bucket_diag[key] = dict(
                v_probe=v_probe_mean,
                world_pred=world_pred_mean,
                true_world=true_world,
                oracle_uncertainty=oracle_uncertainty,
            )

    # ============ Eval (with probe rule per condition) ============
    def probe_decision(z_eval, E_now, c_now, l_now):
        """Returns (should_null, v_value_at_state)."""
        with torch.no_grad():
            e_t = torch.full((1, 1), float(E_now),
                             dtype=torch.float32, device=device)
            ffE = fourier_E(e_t)
            world_input = torch.cat([z_eval, ffE], dim=-1)
            v_val = float(v_probe_head(world_input).item())
            w_val = float(world_head(world_input).item())
        if condition == "learned_costly_null_probe":
            return (v_val > cost), v_val, w_val
        elif condition == "oracle_uncertainty_probe":
            shock_dist = TRAINING_SHOCK
            true_world = shock_dist[role_of(c_now, l_now)] * SHOCK_MAGNITUDE
            err = abs(w_val - true_world)
            return (err > cost), err, w_val
        elif condition == "scheduled_null_anchor":
            return False, v_val, w_val  # no eval probing
        elif condition == "matched_random_null_anchor":
            return False, v_val, w_val  # no eval probing (training-only)
        else:
            return False, v_val, w_val

    def plan_consume_or_skip(z_eval, E_now):
        with torch.no_grad():
            e_t = torch.full((z_eval.shape[0], 1), float(E_now),
                             dtype=torch.float32, device=device)
            ffE = fourier_E(e_t)
            scores = np.zeros(2)
            for a in [0, 1]:
                a_oh = torch.zeros(z_eval.shape[0], n_actions, device=device)
                a_oh[:, a] = 1.0
                inp = torch.cat([z_eval, ffE, a_oh], dim=-1)
                scores[a] = self_head(inp).item()
            return int(np.argmax(scores))

    def eval_under(shock_dist, dist_name):
        rng_eval = np.random.RandomState(seed + 9999 + hash(dist_name) % 1000)
        returns = []
        acc_records = []
        null_actions = 0
        total_actions = 0
        probe_fires_by_bucket = {f"{r}_{eb}": 0 for r in ROLE_IDX
                                  for eb in ("E_low", "E_high")}
        state_visits_by_bucket = {f"{r}_{eb}": 0 for r in ROLE_IDX
                                    for eb in ("E_low", "E_high")}
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
                role = role_of(c_, l_)
                E_bin = "E_low" if E < 0.5 else "E_high"
                bucket_key = f"{role}_{E_bin}"
                state_visits_by_bucket[bucket_key] += 1
                # Decide whether to probe
                if has_null and condition in (
                    "learned_costly_null_probe", "oracle_uncertainty_probe"
                ):
                    should_null, _, _ = probe_decision(z, E, c_, l_)
                else:
                    should_null = False
                if should_null:
                    action = 2  # null
                    null_actions += 1
                    probe_fires_by_bucket[bucket_key] += 1
                else:
                    action = plan_consume_or_skip(z, E)
                total_actions += 1
                self_step = action_self_dE(action, c_, l_)
                world_step = sample_world_shock_local(c_, l_,
                                                       shock_dist, rng_eval)
                # Apply cost if null
                if action == 2:
                    self_step = self_step - cost
                optimal = 1 if consume_self_dE(c_, l_) > 0 else 0
                # Track accuracy only on non-null decisions
                if action != 2:
                    acc_records.append(int(action == optimal))
                E = max(0.0, min(1.0, E + self_step + world_step))
                steps += 1
            returns.append(float(steps))
        import numpy as _np
        return dict(
            distribution=dist_name,
            mean_return=float(_np.mean(returns)),
            action_accuracy=(float(_np.mean(acc_records))
                              if acc_records else 0.0),
            null_rate=(null_actions / max(total_actions, 1)),
            probe_fires_by_bucket=probe_fires_by_bucket,
            state_visits_by_bucket=state_visits_by_bucket,
        )

    in_dist = eval_under(TRAINING_SHOCK, "in_dist")
    shifted = eval_under(SHIFTED_SHOCK, "shifted")

    return dict(
        seed=seed,
        condition=condition,
        cost=cost,
        has_null=has_null,
        n_actions=n_actions,
        target_null_rate=target_null_rate,
        in_dist_eval=in_dist,
        shifted_eval=shifted,
        prediction_by_role=pred_by_role,
        bucket_diag=bucket_diag,
    )


def _flatten_to_row(r):
    row = dict(
        seed=r["seed"], condition=r["condition"], cost=r["cost"],
        has_null=r["has_null"],
        target_null_rate=r.get("target_null_rate"),
        in_dist_return=r["in_dist_eval"]["mean_return"],
        in_dist_acc=r["in_dist_eval"]["action_accuracy"],
        in_dist_null_rate=r["in_dist_eval"]["null_rate"],
        shifted_return=r["shifted_eval"]["mean_return"],
        shifted_acc=r["shifted_eval"]["action_accuracy"],
        shifted_null_rate=r["shifted_eval"]["null_rate"],
    )
    for role, info in r["prediction_by_role"].items():
        row[f"pred_self_consume_{role}"] = info["self_action_1"]
        row[f"pred_self_skip_{role}"] = info["self_action_0"]
        if "self_action_2" in info:
            row[f"pred_self_null_{role}"] = info["self_action_2"]
        row[f"pred_world_{role}"] = info["world"]
        row[f"pred_v_probe_{role}"] = info["v_probe"]
        row[f"true_self_consume_{role}"] = info["true_self_consume"]
        row[f"true_self_skip_or_null_{role}"] = info["true_self_skip_or_null"]
        row[f"true_world_in_dist_{role}"] = info["true_world_in_dist"]
        row[f"true_world_shift_{role}"] = info["true_world_shift"]
    return row


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    n_train_steps: int = 1500,
    batch_size: int = 64,
    eval_episodes: int = 50,
    out: str = "artifacts/costly_null_probes/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    cost_relevant_no_matched = ["learned_costly_null_probe",
                                "oracle_uncertainty_probe"]
    cost_irrelevant = ["factorized_no_null", "factorized_null_passive",
                       "scheduled_null_anchor", "oracle_source"]

    # ============ PASS 1 ============
    pass1_args = []
    for sd in seed_list:
        for cond in cost_irrelevant:
            pass1_args.append(dict(
                seed=sd, condition=cond, cost=COST_HEADLINE,
                n_train_steps=n_train_steps, batch_size=batch_size,
                eval_episodes=eval_episodes,
            ))
        for cond in cost_relevant_no_matched:
            for c in COSTS:
                pass1_args.append(dict(
                    seed=sd, condition=cond, cost=c,
                    n_train_steps=n_train_steps, batch_size=batch_size,
                    eval_episodes=eval_episodes,
                ))
    print(f"PASS 1: running {len(pass1_args)} cells in parallel...")
    pass1_results = list(run_cell.map(pass1_args))

    # Look up learned-probe null rates per (cost, seed)
    rates = {}
    for r in pass1_results:
        if r["condition"] == "learned_costly_null_probe":
            rates[(float(r["cost"]), int(r["seed"]))] = (
                r["in_dist_eval"]["null_rate"]
            )
    print(f"  learned probe rates by (cost, seed): {rates}")

    # ============ PASS 2 ============
    pass2_args = []
    for sd in seed_list:
        for c in COSTS:
            target_rate = rates.get((c, sd), 0.20)
            target_rate = max(0.02, min(0.6, target_rate))
            pass2_args.append(dict(
                seed=sd, condition="matched_random_null_anchor", cost=c,
                target_null_rate=target_rate,
                n_train_steps=n_train_steps, batch_size=batch_size,
                eval_episodes=eval_episodes,
            ))
    print(f"PASS 2: running {len(pass2_args)} cells in parallel...")
    pass2_results = list(run_cell.map(pass2_args))

    results = pass1_results + pass2_results
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = [_flatten_to_row(r) for r in results]

    out_path.write_text(json.dumps({
        "manifest": dict(
            seeds=seed_list, conditions=ALL_CONDITIONS, costs=COSTS,
            cost_headline=COST_HEADLINE,
            n_train_steps=n_train_steps, batch_size=batch_size,
            eval_episodes=eval_episodes,
            training_shock=TRAINING_SHOCK,
            shifted_shock=SHIFTED_SHOCK,
            shock_magnitude=SHOCK_MAGNITUDE,
            item_types={f"{c},{l}": info for (c, l), info in ITEM_TYPES.items()},
            realized_learned_probe_rates={f"{k[0]},{k[1]}": v
                                            for k, v in rates.items()},
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nsummary ({len(summary_rows)} cells):")
    print(f"{'cond':<28} {'seed':>10} {'cost':>5} | "
          f"{'ps_food':>7} {'pw_food':>7} {'ret_id':>6} "
          f"{'null%':>6}")
    print(f"  TRUE FOOD: self_consume=+0.96, world_in_dist=+0.24")
    for r in summary_rows:
        psw = r.get('pred_world_food')
        psw_str = f"{psw:+.3f}" if psw is not None else "  --  "
        nrate = r.get('in_dist_null_rate', 0.0) * 100
        print(f"  {r['condition']:<28} {r['seed']:>10} {r['cost']:>5.3f} | "
              f"{r['pred_self_consume_food']:>+.3f} {psw_str:>7} "
              f"{r['in_dist_return']:>5.1f} {nrate:>5.1f}")
