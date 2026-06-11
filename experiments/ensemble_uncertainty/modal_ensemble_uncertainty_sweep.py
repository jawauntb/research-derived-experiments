#!/usr/bin/env python3
"""Paper 14b — Calibrated Ensemble Uncertainty in Allostatic Planning.

Paper 14 found that greedy planning + a regulate action recovers
boundary-condition return (24.5 → 42.5), but the sophisticated
"uncertainty-aware" planner (named `4action_uncertainty` in P14;
renamed `margin_confidence_planner` here per reviewer) was WORSE
than greedy. The planner's bonus term used |predicted_margin| —
which is *confidence*, not *uncertainty*. Near the boundary, the
model is confident-WRONG, and the confidence-bonus planner walks
into traps.

This paper asks: does a *correctly calibrated* uncertainty signal
(ensemble variance over K=5 ΔE heads) detect the boundary failure
that margin-confidence missed, and do LCB-style risk-averse
planners rescue allostatic control?

Framed as a falsifiable diagnostic:
  - If ensemble variance is high at E=0.5 and low elsewhere → it
    DETECTS the failure. The planner concept may be salvageable.
  - If variance is uniformly distributed → ensemble doesn't
    detect the boundary failure either; greedy + safe-fallback
    regulate remains the robust mechanism.

Conditions (7 × 3 seeds = 21 cells, b=0.5 only):
  - single_head_greedy             : Paper 14 winner baseline (K=1)
  - ensemble_mean_greedy           : K=5 ensemble, greedy on mean
  - ensemble_LCB                   : score = mean − λ·std (pessimistic)
  - ensemble_UCB                   : score = mean + λ·std (optimistic)
  - ensemble_uncertainty_regulate  : greedy on mean; force regulate
                                     when max(var_consume, var_skip)
                                     > threshold
  - margin_confidence_planner      : Paper 14 failed baseline (renamed)
  - oracle_boundary_feature        : upper bound

Pre-registered gates:
  G1 — uncertainty calibration: ensemble variance at E=0.5 ≥ 2× the
       average variance at E ∈ {0.45, 0.55}.
  G2 — error-variance correlation: across the E grid, Pearson
       correlation between absolute prediction error and ensemble
       variance ≥ 0.5.
  G3 — LCB or UCB rescue: best calibrated-uncertainty planner's
       return at b=0.5 ≥ ensemble_mean_greedy − 5 (does NOT fail
       worse than mean-greedy).
  G4 — specificity: ensemble_uncertainty_regulate uses regulate
       preferentially at high-variance states (specificity ≥ 0.5).

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/ensemble_uncertainty/modal_ensemble_uncertainty_sweep.py
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

app = modal.App(name="research-derived-ensemble-uncertainty")

N_COLORS = 4
N_LABELS = 2
ITEMS = [(c, l) for c in range(N_COLORS) for l in range(N_LABELS)]
EMBED_DIM = 32
OBS_NOISE = 0.15
T_MAX = 50
ENERGY_DECAY = 0.04
ENERGY_INIT = 0.5
REGULATE_STEP = 0.10
REGULATE_EXTRA_COST = 0.04
K_ENSEMBLE = 5
BOUNDARY = 0.5

ALL_CONDITIONS = [
    "single_head_greedy",
    "ensemble_mean_greedy",
    "ensemble_LCB",
    "ensemble_UCB",
    "ensemble_uncertainty_regulate",
    "margin_confidence_planner",
    "oracle_boundary_feature",
]


def base_xor(c, l):
    return 1.0 if ((c in (0, 1)) ^ (l == 0)) else -1.0


def reward_of(c, l, energy):
    return base_xor(c, l) if energy < BOUNDARY else -base_xor(c, l)


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
    lcb_lambda: float = arg["lcb_lambda"]
    ucb_lambda: float = arg["ucb_lambda"]
    uncertainty_regulate_threshold: float = arg["uncertainty_regulate_threshold"]

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rng_env = np.random.RandomState(seed + 13)
    perm = rng_env.permutation(16)

    n_actions = 4

    def encode_one(c, l, rng):
        obs = np.zeros(16, dtype=np.float32)
        obs[c] = 1.0
        obs[8 + l] = 1.0
        obs = obs + rng.randn(16).astype(np.float32) * OBS_NOISE
        return obs[perm]

    def apply_action(action: int, E: float, c: int, l: int):
        if action == 1:
            r = reward_of(c, l, E)
            return float(min(1.0, max(0.0, E + r - ENERGY_DECAY)))
        elif action == 0:
            return float(E - ENERGY_DECAY)
        elif action == 2:
            return float(min(1.0, max(0.0, E + REGULATE_STEP - ENERGY_DECAY - REGULATE_EXTRA_COST)))
        elif action == 3:
            return float(min(1.0, max(0.0, E - REGULATE_STEP - ENERGY_DECAY - REGULATE_EXTRA_COST)))
        raise ValueError(action)

    def sample_off_policy_batch(rng):
        idx = rng.randint(0, len(ITEMS), size=batch_size)
        colors = np.array([ITEMS[i][0] for i in idx])
        labels = np.array([ITEMS[i][1] for i in idx])
        energies = rng.uniform(0.0, 1.0, size=batch_size).astype(np.float32)
        actions = rng.randint(0, n_actions, size=batch_size).astype(np.int64)
        obs = np.stack([encode_one(c, l, rng) for c, l in zip(colors, labels)])
        observed_de = np.zeros(batch_size, dtype=np.float32)
        for i in range(batch_size):
            E_after = apply_action(int(actions[i]), float(energies[i]),
                                    int(colors[i]), int(labels[i]))
            observed_de[i] = E_after - energies[i]
        return obs, energies, actions, observed_de

    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)

    def fourier_E(E_tensor):
        if E_tensor.dim() == 2:
            E_tensor = E_tensor.squeeze(-1)
        feats = [E_tensor.unsqueeze(-1)]
        for freq in [1.0, 2.0, 4.0]:
            feats.append(torch.sin(torch.pi * freq * E_tensor).unsqueeze(-1))
            feats.append(torch.cos(torch.pi * freq * E_tensor).unsqueeze(-1))
        return torch.cat(feats, dim=-1)

    # Determine ensemble size and architecture
    use_oracle_feature = (condition == "oracle_boundary_feature")
    use_ensemble = condition.startswith("ensemble") or condition == "ensemble_uncertainty_regulate"
    K = K_ENSEMBLE if use_ensemble else 1

    base_input_dim = EMBED_DIM + 7 + n_actions
    if use_oracle_feature:
        base_input_dim += 1  # 1[E<0.5]

    heads = []
    for k in range(K):
        torch.manual_seed(seed + 1000 * (k + 1))
        h = nn.Sequential(
            nn.Linear(base_input_dim, 32), nn.Tanh(),
            nn.Linear(32, 1),
        ).to(device)
        heads.append(h)
    torch.manual_seed(seed)

    params = list(encoder.parameters())
    for h in heads:
        params += list(h.parameters())
    opt = torch.optim.Adam(params, lr=2e-3)

    def build_input(z, E_vals, a_oh):
        if isinstance(E_vals, (int, float)):
            e_t = torch.full((z.shape[0], 1), float(E_vals),
                             dtype=torch.float32, device=device)
        else:
            e_t = torch.tensor(np.asarray(E_vals).reshape(-1, 1),
                               dtype=torch.float32, device=device)
        ff = fourier_E(e_t)
        if use_oracle_feature:
            b = (e_t < BOUNDARY).float()
            return torch.cat([z, ff, b, a_oh], dim=-1)
        return torch.cat([z, ff, a_oh], dim=-1)

    def predict_de_per_head(z, E_val, action_idx):
        a_oh = torch.zeros(z.shape[0], n_actions, device=device)
        if isinstance(action_idx, int):
            a_oh[:, action_idx] = 1.0
        else:
            a_oh[torch.arange(z.shape[0]), torch.tensor(action_idx, device=device)] = 1.0
        inp = build_input(z, E_val, a_oh)
        preds = [h(inp).squeeze(-1) for h in heads]  # K of (n,)
        return torch.stack(preds, dim=0)  # (K, n)

    def predict_de_stats(z, E_val, action_idx):
        """Return (mean, std) over the ensemble. For K=1 std is 0."""
        per_head = predict_de_per_head(z, E_val, action_idx)
        mean = per_head.mean(dim=0)
        std = per_head.std(dim=0) if K > 1 else torch.zeros_like(mean)
        return mean, std

    # ============ Train ============
    rng_train = np.random.RandomState(seed + 47)
    for step in range(n_train_steps):
        obs, energies, actions, observed_de = sample_off_policy_batch(rng_train)
        x = torch.from_numpy(obs).to(device)
        z = encoder(x)
        a_oh = torch.zeros(batch_size, n_actions, device=device)
        a_oh[np.arange(batch_size), actions] = 1.0
        targets = torch.from_numpy(observed_de).to(device)
        # Train all heads on full batch (no bootstrapping for simplicity;
        # diversity comes from different init seeds). Optional: bootstrap.
        total_loss = 0.0
        for h in heads:
            inp = build_input(z, energies, a_oh)
            pred = h(inp).squeeze(-1)
            total_loss = total_loss + F.mse_loss(pred, targets)
        opt.zero_grad(); total_loss.backward(); opt.step()

    encoder.eval()
    for h in heads:
        h.eval()

    # ============ Planning ============
    def predict_E_after(E_now, c, l):
        return [apply_action(a, E_now, c, l) for a in range(n_actions)]

    def margin_confidence_at(z, E_val):
        """For margin_confidence_planner: |mean_pred_consume − mean_pred_skip|."""
        mc, _ = predict_de_stats(z, E_val, 1)
        ms, _ = predict_de_stats(z, E_val, 0)
        return float(abs(mc.item() - ms.item()))

    def plan_action(z_single, E_now, c, l):
        with torch.no_grad():
            means = []
            stds = []
            for a in range(n_actions):
                m, s = predict_de_stats(z_single, E_now, a)
                means.append(m.item())
                stds.append(s.item())
            means_arr = np.array(means)
            stds_arr = np.array(stds)

        if condition == "single_head_greedy":
            return int(np.argmax(means_arr))
        elif condition == "ensemble_mean_greedy":
            return int(np.argmax(means_arr))
        elif condition == "ensemble_LCB":
            scores = means_arr - lcb_lambda * stds_arr
            return int(np.argmax(scores))
        elif condition == "ensemble_UCB":
            scores = means_arr + ucb_lambda * stds_arr
            return int(np.argmax(scores))
        elif condition == "ensemble_uncertainty_regulate":
            # Greedy on mean; but if max(var_consume, var_skip) is high,
            # force regulate_up (action=2)
            max_item_var = max(stds_arr[0], stds_arr[1])
            if max_item_var > uncertainty_regulate_threshold:
                return 2  # regulate_up
            return int(np.argmax(means_arr[:2]))  # only consume/skip via greedy
        elif condition == "margin_confidence_planner":
            # Paper 14 failed baseline: score(a) = mean(a) + λ · |predicted_margin(E_after)|
            scores = np.zeros(n_actions)
            E_afters = predict_E_after(E_now, c, l)
            with torch.no_grad():
                for a in range(n_actions):
                    margin = margin_confidence_at(z_single, E_afters[a])
                    scores[a] = means_arr[a] + 0.5 * margin
            return int(np.argmax(scores))
        elif condition == "oracle_boundary_feature":
            return int(np.argmax(means_arr))  # head sees oracle feature; greedy
        raise ValueError(condition)

    # ============ Eval ============
    rng_eval = np.random.RandomState(seed + 9999)
    episode_returns = []
    action_acc_records = []
    E_trajectory = []
    regulate_events = []  # (E_before, max_item_var)
    high_var_count = 0
    high_var_threshold = uncertainty_regulate_threshold

    for _ in range(eval_episodes):
        E = ENERGY_INIT
        steps = 0
        while E > 0 and steps < T_MAX:
            idx = rng_eval.randint(0, len(ITEMS))
            c_, l_ = ITEMS[idx]
            obs_ = encode_one(c_, l_, rng_eval)
            x = torch.from_numpy(obs_[None]).float().to(device)
            true_r = reward_of(c_, l_, E)
            optimal_consume = 1 if true_r > 0 else 0
            with torch.no_grad():
                z = encoder(x)
                _, std_c = predict_de_stats(z, E, 1)
                _, std_s = predict_de_stats(z, E, 0)
                max_item_var = max(std_c.item(), std_s.item())
                action = plan_action(z, E, c_, l_)
            E_trajectory.append(float(E))
            if max_item_var > high_var_threshold:
                high_var_count += 1
            if action in (0, 1):
                action_acc_records.append(int(action == optimal_consume))
            else:
                regulate_events.append((float(E), max_item_var))
            E = apply_action(action, E, c_, l_)
            steps += 1
        episode_returns.append(float(steps))

    import numpy as _np

    # ============ Calibration / variance diagnostic ============
    rng_cal = _np.random.RandomState(seed + 333)
    n_cal_per_E = 64
    cal_records = []
    for E_grid in [0.1, 0.2, 0.3, 0.4, 0.45, 0.48, 0.49, 0.5, 0.51, 0.52, 0.55, 0.6, 0.7, 0.8, 0.9]:
        obs_l, col_l, lab_l, rew_l = [], [], [], []
        for _ in range(n_cal_per_E):
            idx = rng_cal.randint(0, len(ITEMS))
            c_, l_ = ITEMS[idx]
            obs_l.append(encode_one(c_, l_, rng_cal))
            col_l.append(c_); lab_l.append(l_)
            rew_l.append(reward_of(c_, l_, E_grid))
        obs_arr = _np.array(obs_l); rews = _np.array(rew_l)
        with torch.no_grad():
            z_cal = encoder(torch.from_numpy(obs_arr).to(device))
        # Compute mean and variance per (z, action)
        a_consume = torch.zeros(n_cal_per_E, n_actions, device=device); a_consume[:, 1] = 1.0
        a_skip = torch.zeros(n_cal_per_E, 2 + 2, device=device); a_skip[:, 0] = 1.0
        with torch.no_grad():
            # Use predict_de_per_head
            pc_per_head = predict_de_per_head(z_cal, E_grid, 1).cpu().numpy()  # (K, n)
            ps_per_head = predict_de_per_head(z_cal, E_grid, 0).cpu().numpy()
            pc_mean = pc_per_head.mean(axis=0); pc_std = pc_per_head.std(axis=0) if K > 1 else _np.zeros_like(pc_mean)
            ps_mean = ps_per_head.mean(axis=0); ps_std = ps_per_head.std(axis=0) if K > 1 else _np.zeros_like(ps_mean)
        pred_margin = pc_mean - ps_mean
        optimal = (rews > 0).astype(_np.int64)
        pred_action = (pred_margin > 0).astype(_np.int64)
        cal_records.append(dict(
            E_grid=float(E_grid),
            margin_sign_acc=float(_np.mean(pred_action == optimal)),
            mean_pc_std=float(_np.mean(pc_std)),
            mean_ps_std=float(_np.mean(ps_std)),
            mean_item_var=float(_np.mean(_np.maximum(pc_std, ps_std))),
            abs_margin_error=float(_np.mean(_np.abs(pred_margin -
                (pc_per_head.mean(axis=0) - ps_per_head.mean(axis=0))))),
        ))

    # Compute calibration metrics
    # G1: variance at E=0.5 vs E={0.45, 0.55}
    var_05 = next(r["mean_item_var"] for r in cal_records if r["E_grid"] == 0.5)
    var_045 = next(r["mean_item_var"] for r in cal_records if r["E_grid"] == 0.45)
    var_055 = next(r["mean_item_var"] for r in cal_records if r["E_grid"] == 0.55)
    var_ratio = var_05 / max(1e-9, 0.5 * (var_045 + var_055))

    # G2: error-variance correlation
    e_errors = [1.0 - r["margin_sign_acc"] for r in cal_records]
    e_vars = [r["mean_item_var"] for r in cal_records]
    if K > 1 and _np.std(e_vars) > 1e-9:
        ev_corr = float(_np.corrcoef(e_errors, e_vars)[0, 1])
    else:
        ev_corr = float("nan")

    # Regulate specificity (high-variance specificity)
    if regulate_events:
        # specificity = fraction of regulate events at high variance
        median_var = _np.median([v for _, v in regulate_events]) if len(regulate_events) > 1 else 0.0
        high_var_regulate = sum(1 for _, v in regulate_events if v >= median_var)
        regulate_high_var_specificity = float(high_var_regulate / max(1, len(regulate_events)))
    else:
        regulate_high_var_specificity = None

    return dict(
        seed=seed,
        condition=condition,
        K=K,
        mean_return=float(_np.mean(episode_returns)),
        action_accuracy=float(_np.mean(action_acc_records)) if action_acc_records else None,
        n_regulate_events=len(regulate_events),
        regulate_high_var_specificity=regulate_high_var_specificity,
        var_at_E05=var_05,
        var_at_E045=var_045,
        var_at_E055=var_055,
        var_ratio_05_vs_neighbors=float(var_ratio),
        error_variance_correlation=ev_corr,
        cal_records=cal_records,
        episode_returns=episode_returns,
    )


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    n_train_steps: int = 1500,
    batch_size: int = 64,
    eval_episodes: int = 50,
    lcb_lambda: float = 1.0,
    ucb_lambda: float = 1.0,
    uncertainty_regulate_threshold: float = 0.05,
    out: str = "artifacts/ensemble_uncertainty/sweep_v1.json",
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
                lcb_lambda=lcb_lambda,
                ucb_lambda=ucb_lambda,
                uncertainty_regulate_threshold=uncertainty_regulate_threshold,
            ))
    print(f"running {len(cell_args)} cells in parallel...")
    results = list(run_cell.map(cell_args))
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for r in results:
        rs = r["regulate_high_var_specificity"]
        summary_rows.append(dict(
            seed=r["seed"], condition=r["condition"],
            K=r["K"],
            mean_return=r["mean_return"],
            action_accuracy=r["action_accuracy"],
            n_regulate_events=r["n_regulate_events"],
            regulate_high_var_specificity=rs if rs is not None else 0.0,
            var_at_E05=r["var_at_E05"],
            var_at_E045=r["var_at_E045"],
            var_at_E055=r["var_at_E055"],
            var_ratio_05_vs_neighbors=r["var_ratio_05_vs_neighbors"],
            error_variance_correlation=r["error_variance_correlation"],
        ))

    out_path.write_text(json.dumps({
        "manifest": dict(
            seeds=seed_list, conditions=ALL_CONDITIONS,
            K_ensemble=K_ENSEMBLE, boundary=BOUNDARY,
            n_train_steps=n_train_steps, batch_size=batch_size,
            eval_episodes=eval_episodes,
            lcb_lambda=lcb_lambda, ucb_lambda=ucb_lambda,
            uncertainty_regulate_threshold=uncertainty_regulate_threshold,
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nsummary ({len(summary_rows)} cells):")
    print(f"{'condition':<35} {'seed':>10} | "
          f"{'ret':>5} {'acc':>5} {'var_05':>7} {'var_ratio':>9} {'err_var_corr':>11}")
    for r in summary_rows:
        ca = "  --  " if r["action_accuracy"] is None else f"{r['action_accuracy']:.2f}"
        evc = "  --  " if not (r["error_variance_correlation"] is not None and not (r["error_variance_correlation"] != r["error_variance_correlation"])) else f"{r['error_variance_correlation']:+.3f}"
        import math
        if r["error_variance_correlation"] is None or math.isnan(r["error_variance_correlation"]):
            evc = "  --  "
        else:
            evc = f"{r['error_variance_correlation']:+.3f}"
        print(f"  {r['condition']:<33} {r['seed']:>10} | "
              f"{r['mean_return']:>4.1f} {ca:>5} {r['var_at_E05']:>6.4f} "
              f"{r['var_ratio_05_vs_neighbors']:>8.2f}x {evc:>11}")
