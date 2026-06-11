#!/usr/bin/env python3
"""Paper 14 — Allostatic State Control.

Paper 13b showed that under sharp state-dependent valence, smooth
function approximators reach sc_competence 0.99 but trajectory-
weighted returns lag (24.5/50 for Fourier features) because the
agent's policy-induced state distribution concentrates on the
singular boundary point E=0.5 where the model fails.

Paper 13b's proposed Paper 14: instead of resolving the boundary
ARCHITECTURALLY, give the agent a third action — `regulate` — that
moves its own internal state away from the boundary where its model
is unreliable. The agent learns to *behaviorally avoid* the region
of model failure rather than learning to perfectly represent it.

Four conditions × 3 boundary locations × 3 seeds = 36 cells.

Conditions:
  - baseline_2action      : Fourier features (Paper 13b head), 2 actions
                            (consume/skip), greedy planner. Replicates
                            Paper 13b Fourier baseline.
  - 4action_greedy        : Fourier head, 4 actions (consume/skip/
                            regulate_up/regulate_down), greedy argmax
                            over predicted ΔE. ABLATION: tests whether
                            adding the action alone is enough.
  - 4action_two_step      : same actions, two-step lookahead planner.
                            score(a) = pred_ΔE(a) + γ · max_{a'}
                                       pred_ΔE_at_E_after(a, a')
  - 4action_uncertainty   : HEADLINE. Same actions, uncertainty-aware
                            planner: score(a) = pred_ΔE(a) + λ ·
                            |predicted_margin(z, E_after_a)|. The
                            agent gets a bonus for actions that lead
                            to high-confidence states.

Boundary locations: {0.3, 0.5, 0.7}.

Action dynamics:
  - consume        : ΔE = reward(item, E) − decay
  - skip           : ΔE = −decay (=−0.04)
  - regulate_up    : E moves +0.10; net ΔE = +0.10 − decay − 0.04 = +0.02
                     (small positive — net better than skip)
  - regulate_down  : E moves −0.10; net ΔE = −0.10 − decay − 0.04 = −0.18

Pre-registered gates:
  G1 — allostatic competence: `4action_uncertainty` mean return ≥ 45/50
       across the 3 boundary locations.
  G2 — boundary avoidance: `4action_uncertainty` boundary_occupancy
       (fraction of trajectory steps with |E − boundary| < 0.06)
       reduced by ≥ 70% vs `baseline_2action`.
  G3 — regulate specificity: `4action_uncertainty` regulate actions
       used preferentially near boundary. specificity = fraction of
       regulate uses where |current margin| was below median.
       Target: ≥ 0.65.
  G4 — ablation: `4action_greedy` ≈ `baseline_2action` return
       (within 5 points). Demonstrates the action alone is not the
       mechanism; the planner is.

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/allostatic_control/modal_allostatic_sweep.py
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

app = modal.App(name="research-derived-allostatic-control")

N_COLORS = 4
N_LABELS = 2
ITEMS = [(c, l) for c in range(N_COLORS) for l in range(N_LABELS)]
EMBED_DIM = 32
OBS_NOISE = 0.15
T_MAX = 50
ENERGY_DECAY = 0.04
ENERGY_INIT = 0.5
REGULATE_STEP = 0.10
REGULATE_EXTRA_COST = 0.04  # makes regulate slightly worse than skip alone

ALL_CONDITIONS = [
    "baseline_2action",
    "4action_greedy",
    "4action_two_step",
    "4action_uncertainty",
]
BOUNDARY_LOCATIONS = [0.3, 0.5, 0.7]


def base_xor(c, l):
    return 1.0 if ((c in (0, 1)) ^ (l == 0)) else -1.0


def reward_of_with_boundary(c, l, energy, boundary):
    # State-dep inverted XOR with the inversion at `boundary`.
    return base_xor(c, l) if energy < boundary else -base_xor(c, l)


@app.function(image=IMAGE, timeout=1800, cpu=4, memory=4096)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    seed: int = arg["seed"]
    condition: str = arg["condition"]
    boundary: float = arg["boundary"]
    n_train_steps: int = arg["n_train_steps"]
    batch_size: int = arg["batch_size"]
    eval_episodes: int = arg["eval_episodes"]
    uncertainty_lambda: float = arg["uncertainty_lambda"]
    two_step_gamma: float = arg["two_step_gamma"]

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rng_env = np.random.RandomState(seed + 13)
    perm = rng_env.permutation(16)

    has_4_actions = condition.startswith("4action")
    n_actions = 4 if has_4_actions else 2

    def encode_one(c, l, rng):
        obs = np.zeros(16, dtype=np.float32)
        obs[c] = 1.0
        obs[8 + l] = 1.0
        obs = obs + rng.randn(16).astype(np.float32) * OBS_NOISE
        return obs[perm]

    def apply_action(action: int, E: float, c: int, l: int):
        """Apply action, return (new_E, observed_ΔE)."""
        E_after = E - ENERGY_DECAY
        if action == 1:  # consume
            r = reward_of_with_boundary(c, l, E, boundary)
            E_after = min(1.0, max(0.0, E + r - ENERGY_DECAY))
        elif action == 0:  # skip
            E_after = E - ENERGY_DECAY
        elif action == 2:  # regulate_up
            E_after = min(1.0, max(0.0, E + REGULATE_STEP - ENERGY_DECAY - REGULATE_EXTRA_COST))
        elif action == 3:  # regulate_down
            E_after = min(1.0, max(0.0, E - REGULATE_STEP - ENERGY_DECAY - REGULATE_EXTRA_COST))
        return float(E_after), float(E_after - E)

    def sample_off_policy_batch(rng):
        idx = rng.randint(0, len(ITEMS), size=batch_size)
        colors = np.array([ITEMS[i][0] for i in idx])
        labels = np.array([ITEMS[i][1] for i in idx])
        energies = rng.uniform(0.0, 1.0, size=batch_size).astype(np.float32)
        actions = rng.randint(0, n_actions, size=batch_size).astype(np.int64)
        obs = np.stack([encode_one(c, l, rng) for c, l in zip(colors, labels)])
        observed_de = np.zeros(batch_size, dtype=np.float32)
        for i in range(batch_size):
            _, de = apply_action(int(actions[i]), float(energies[i]),
                                  int(colors[i]), int(labels[i]))
            observed_de[i] = de
        return obs, energies, actions, observed_de

    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)

    # Fourier-feature input
    def fourier_E(E_tensor):
        # E_tensor: (n,) or (n, 1) → (n, 7)
        if E_tensor.dim() == 2:
            E_tensor = E_tensor.squeeze(-1)
        feats = [E_tensor.unsqueeze(-1)]
        for freq in [1.0, 2.0, 4.0]:
            feats.append(torch.sin(torch.pi * freq * E_tensor).unsqueeze(-1))
            feats.append(torch.cos(torch.pi * freq * E_tensor).unsqueeze(-1))
        return torch.cat(feats, dim=-1)

    aux_input_dim = EMBED_DIM + 7 + n_actions
    aux_head = nn.Sequential(
        nn.Linear(aux_input_dim, 32), nn.Tanh(),
        nn.Linear(32, 1),
    ).to(device)

    opt = torch.optim.Adam(
        list(encoder.parameters()) + list(aux_head.parameters()), lr=2e-3,
    )

    def predict_de_batch(z, E_vals, action_indices):
        """Predict ΔE for a batch of (z, E, action)."""
        if isinstance(E_vals, (int, float)):
            e_t = torch.full((z.shape[0], 1), float(E_vals),
                             dtype=torch.float32, device=device)
        else:
            e_t = torch.tensor(np.asarray(E_vals).reshape(-1, 1),
                               dtype=torch.float32, device=device)
        ff = fourier_E(e_t)
        a_oh = torch.zeros(z.shape[0], n_actions, device=device)
        if isinstance(action_indices, int):
            a_oh[:, action_indices] = 1.0
        else:
            a_oh[torch.arange(z.shape[0]), torch.tensor(action_indices, device=device)] = 1.0
        return aux_head(torch.cat([z, ff, a_oh], dim=-1)).squeeze(-1)

    def predict_de_all_actions(z, E_val):
        """Return (n, n_actions) of predicted ΔE per action."""
        outs = []
        for a in range(n_actions):
            outs.append(predict_de_batch(z, E_val, a))
        return torch.stack(outs, dim=-1)  # (n, n_actions)

    # ============ Train ============
    rng_train = np.random.RandomState(seed + 47)
    for step in range(n_train_steps):
        obs, energies, actions, observed_de = sample_off_policy_batch(rng_train)
        x = torch.from_numpy(obs).to(device)
        z = encoder(x)
        a_oh = torch.zeros(batch_size, n_actions, device=device)
        a_oh[np.arange(batch_size), actions] = 1.0
        e_t = torch.from_numpy(energies.reshape(-1, 1)).to(device)
        ff = fourier_E(e_t)
        pred = aux_head(torch.cat([z, ff, a_oh], dim=-1)).squeeze(-1)
        targets = torch.from_numpy(observed_de).to(device)
        loss = F.mse_loss(pred, targets)
        opt.zero_grad(); loss.backward(); opt.step()

    # ============ Helper: predict E_after for each action ============
    def predict_E_after(z_single, E_now, c, l):
        """Return (n_actions,) list of E_after for each action.
        Action effect on E is deterministic (we know dynamics) — we
        use the env model directly for E_after. The ΔE head is
        used only for evaluating the bonus."""
        E_afters = []
        # Compute E_after analytically per action. For consume action,
        # we need to know the reward — but reward depends on the actual
        # (c, l), which the env knows. We use the deterministic env.
        for a in range(n_actions):
            E_after, _ = apply_action(a, float(E_now), c, l)
            E_afters.append(E_after)
        return E_afters

    def predict_margin_at(z, E_val):
        """Predicted |ΔE(consume) − ΔE(skip)| at given (z, E)."""
        pc = predict_de_batch(z, E_val, 1).item()
        ps = predict_de_batch(z, E_val, 0).item()
        return abs(pc - ps)

    def plan_action(z_single, E_now, c, l):
        with torch.no_grad():
            pred_des = predict_de_all_actions(z_single, E_now).squeeze(0).cpu().numpy()
        # pred_des: (n_actions,)
        if condition == "baseline_2action":
            # Pick from 2 actions only
            return int(np.argmax(pred_des[:2]))
        elif condition == "4action_greedy":
            return int(np.argmax(pred_des))
        elif condition == "4action_two_step":
            # score(a) = pred_ΔE(a) + γ · max_{a'} pred_ΔE_at_E_after(a, a')
            E_afters = predict_E_after(z_single, E_now, c, l)
            scores = np.zeros(n_actions)
            with torch.no_grad():
                for a in range(n_actions):
                    pred_at_next = predict_de_all_actions(z_single, E_afters[a]).squeeze(0).cpu().numpy()
                    scores[a] = pred_des[a] + two_step_gamma * float(np.max(pred_at_next))
            return int(np.argmax(scores))
        elif condition == "4action_uncertainty":
            # score(a) = pred_ΔE(a) + λ · |predicted_margin(z, E_after_a)|
            E_afters = predict_E_after(z_single, E_now, c, l)
            scores = np.zeros(n_actions)
            with torch.no_grad():
                for a in range(n_actions):
                    margin = predict_margin_at(z_single, E_afters[a])
                    scores[a] = pred_des[a] + uncertainty_lambda * margin
            return int(np.argmax(scores))
        else:
            raise ValueError(condition)

    # ============ Eval ============
    encoder.eval(); aux_head.eval()
    rng_eval = np.random.RandomState(seed + 9999)
    episode_returns = []
    action_acc_records = []
    E_trajectory = []  # all E_before values across all eval steps
    regulate_uses = []  # (E_before, |margin|) for each regulate action
    all_margins = []  # |margin| at each step (for specificity computation)
    consume_skip_choices_correct = []  # only consume/skip actions, was it the right one?

    for _ in range(eval_episodes):
        E = ENERGY_INIT
        steps = 0
        while E > 0 and steps < T_MAX:
            idx = rng_eval.randint(0, len(ITEMS))
            c_, l_ = ITEMS[idx]
            obs_ = encode_one(c_, l_, rng_eval)
            x = torch.from_numpy(obs_[None]).float().to(device)
            true_r = reward_of_with_boundary(c_, l_, E, boundary)
            optimal_consume = 1 if true_r > 0 else 0
            with torch.no_grad():
                z = encoder(x)
                # current margin
                pc = predict_de_batch(z, E, 1).item()
                ps = predict_de_batch(z, E, 0).item()
                margin_here = abs(pc - ps)
                action = plan_action(z, E, c_, l_)
            all_margins.append(margin_here)
            E_trajectory.append(float(E))
            if action in (0, 1):  # skip or consume
                # judge consume/skip correctness
                correct = int(action == optimal_consume)
                action_acc_records.append(correct)
                consume_skip_choices_correct.append(correct)
            else:
                regulate_uses.append((float(E), margin_here))
            E_after, _ = apply_action(action, E, c_, l_)
            E = E_after
            steps += 1
        episode_returns.append(float(steps))

    # ============ Compute summary metrics ============
    import numpy as _np
    mean_return = float(_np.mean(episode_returns))
    action_accuracy = float(_np.mean(action_acc_records)) if action_acc_records else None
    # Boundary occupancy: fraction of trajectory steps where |E - boundary| < 0.06
    boundary_occupancy = float(_np.mean([abs(e - boundary) < 0.06 for e in E_trajectory]))
    # Regulate action rate
    n_regulates = len(regulate_uses)
    regulate_rate = float(n_regulates / max(1, len(E_trajectory)))
    # Regulate specificity: fraction of regulate uses where margin was below median
    if all_margins and regulate_uses:
        median_margin = float(_np.median(all_margins))
        below_median = sum(1 for _, m in regulate_uses if m <= median_margin)
        regulate_specificity = float(below_median / max(1, len(regulate_uses)))
    else:
        regulate_specificity = None

    # ============ Per-E calibration (informational) ============
    cal_records = []
    rng_cal = _np.random.RandomState(seed + 333)
    n_cal = 256
    for E_grid in [0.1, 0.2, 0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 0.8, 0.9]:
        obs_l, col_l, lab_l, rew_l = [], [], [], []
        for _ in range(n_cal):
            idx = rng_cal.randint(0, len(ITEMS))
            c_, l_ = ITEMS[idx]
            obs_l.append(encode_one(c_, l_, rng_cal))
            col_l.append(c_); lab_l.append(l_)
            rew_l.append(reward_of_with_boundary(c_, l_, E_grid, boundary))
        obs_arr = _np.array(obs_l)
        rews = _np.array(rew_l)
        with torch.no_grad():
            z_cal = encoder(torch.from_numpy(obs_arr).to(device))
        with torch.no_grad():
            pc = predict_de_batch(z_cal, E_grid, 1).cpu().numpy()
            ps = predict_de_batch(z_cal, E_grid, 0).cpu().numpy()
        pred_margin = pc - ps
        optimal = (rews > 0).astype(_np.int64)
        pred_action = (pred_margin > 0).astype(_np.int64)
        cal_records.append(dict(
            E_grid=E_grid,
            margin_sign_acc=float(_np.mean(pred_action == optimal)),
        ))

    return dict(
        seed=seed,
        condition=condition,
        boundary=boundary,
        n_actions=n_actions,
        mean_return=mean_return,
        action_accuracy=action_accuracy,
        boundary_occupancy=boundary_occupancy,
        regulate_rate=regulate_rate,
        regulate_specificity=regulate_specificity,
        consume_skip_accuracy=(float(_np.mean(consume_skip_choices_correct))
                               if consume_skip_choices_correct else None),
        calibration_by_E=cal_records,
        n_regulate_uses=n_regulates,
        episode_returns=episode_returns,
        E_trajectory_sample=E_trajectory[:100],
    )


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    n_train_steps: int = 1500,
    batch_size: int = 64,
    eval_episodes: int = 50,
    uncertainty_lambda: float = 0.5,
    two_step_gamma: float = 0.5,
    out: str = "artifacts/allostatic_control/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    cell_args = []
    for sd in seed_list:
        for cond in ALL_CONDITIONS:
            for boundary in BOUNDARY_LOCATIONS:
                cell_args.append(dict(
                    seed=sd, condition=cond, boundary=boundary,
                    n_train_steps=n_train_steps,
                    batch_size=batch_size,
                    eval_episodes=eval_episodes,
                    uncertainty_lambda=uncertainty_lambda,
                    two_step_gamma=two_step_gamma,
                ))
    print(f"running {len(cell_args)} cells in parallel...")
    results = list(run_cell.map(cell_args))
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for r in results:
        cal_by_E = {f"acc@E={c['E_grid']}": c["margin_sign_acc"]
                    for c in r["calibration_by_E"]}
        rs = r["regulate_specificity"]
        summary_rows.append(dict(
            seed=r["seed"], condition=r["condition"], boundary=r["boundary"],
            mean_return=r["mean_return"],
            action_accuracy=r["action_accuracy"],
            boundary_occupancy=r["boundary_occupancy"],
            regulate_rate=r["regulate_rate"],
            regulate_specificity=rs if rs is not None else 0.0,
            consume_skip_accuracy=r["consume_skip_accuracy"],
            n_regulate_uses=r["n_regulate_uses"],
            **cal_by_E,
        ))

    out_path.write_text(json.dumps({
        "manifest": dict(
            seeds=seed_list, conditions=ALL_CONDITIONS,
            boundary_locations=BOUNDARY_LOCATIONS,
            n_train_steps=n_train_steps, batch_size=batch_size,
            eval_episodes=eval_episodes,
            uncertainty_lambda=uncertainty_lambda,
            two_step_gamma=two_step_gamma,
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nsummary ({len(summary_rows)} cells):")
    print(f"{'cond':<24} {'b':>3} {'seed':>10} | "
          f"{'ret':>5} {'acc':>5} {'b_occ':>5} {'reg_r':>5} {'reg_sp':>6} "
          f"{'cs_acc':>6} {'@b':>5}")
    for r in summary_rows:
        ca = "  --  " if r["action_accuracy"] is None else f"{r['action_accuracy']:.2f}"
        cs = "  --  " if r["consume_skip_accuracy"] is None else f"{r['consume_skip_accuracy']:.2f}"
        rs = "  --  " if r["regulate_specificity"] is None else f"{r['regulate_specificity']:.2f}"
        # Look up acc at the boundary
        bkey = f"acc@E={r['boundary']}"
        acc_at_b = r.get(bkey, 0.0)
        print(f"  {r['condition']:<22} {r['boundary']:>3.1f} {r['seed']:>10} | "
              f"{r['mean_return']:>4.1f} {ca:>5} {r['boundary_occupancy']:>4.2f} "
              f"{r['regulate_rate']:>4.2f} {rs:>6} {cs:>6} {acc_at_b:>4.2f}")
