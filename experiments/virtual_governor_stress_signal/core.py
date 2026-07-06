"""Closed-loop stress-signal diagnostic for virtual-governor architecture.

The suite asks whether a live global-stress signal, translated into local policy
features, improves action selection after constraint shifts. It is intentionally
small: the point is an auditable architecture ablation, not a large benchmark.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean
from typing import Any, cast

import numpy as np


CONDITIONS = (
    "reward_only",
    "local_state",
    "stale_governor",
    "wrong_governor",
    "virtual_governor",
)

CONDITION_LABELS = {
    "reward_only": "reward only",
    "local_state": "local state proxy",
    "stale_governor": "stale governor memory",
    "wrong_governor": "wrong stress signal",
    "virtual_governor": "live virtual governor",
}

DEFAULT_TARGET = np.array([0.62, 0.54, 0.58], dtype=np.float32)
DECOY_TARGET = np.array([0.28, 0.72, 0.28], dtype=np.float32)
TARGETS = np.array(
    [
        [0.82, 0.34, 0.64],
        [0.38, 0.80, 0.42],
        [0.56, 0.44, 0.86],
        [0.76, 0.72, 0.32],
    ],
    dtype=np.float32,
)

ACTION_EFFECTS = np.array(
    [
        [0.12, -0.02, -0.03],
        [-0.09, 0.01, 0.03],
        [-0.02, 0.12, -0.02],
        [0.03, -0.09, 0.00],
        [-0.02, 0.02, 0.12],
        [0.01, 0.00, -0.09],
    ],
    dtype=np.float32,
)
ACTION_COSTS = np.array([0.020, 0.030, 0.020, 0.030, 0.025, 0.025], dtype=np.float32)

OBS_DIM = 9
N_ACTIONS = int(ACTION_EFFECTS.shape[0])


@dataclass(frozen=True)
class TrialResult:
    """One trained condition/seed evaluation row."""

    condition: str
    seed: int
    train_loss: float
    action_accuracy: float
    mean_stress: float
    post_shift_stress_auc: float
    recovery_rate: float
    mean_recovery_steps: float
    final_stress: float
    global_recovery_score: float
    post_shift_curve: list[float]

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def _clip_state(state: np.ndarray) -> np.ndarray:
    return np.clip(state, 0.02, 0.98).astype(np.float32)


def _stress(state: np.ndarray, target: np.ndarray) -> np.ndarray:
    return (target - state).astype(np.float32)


def _next_target(current: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    candidates = [target for target in TARGETS if not np.allclose(target, current)]
    return np.array(candidates[int(rng.integers(0, len(candidates)))], dtype=np.float32)


def stress_norm(state: np.ndarray, target: np.ndarray) -> float:
    return float(np.linalg.norm(_stress(state, target), ord=2))


def oracle_action(state: np.ndarray, target: np.ndarray) -> int:
    """Action minimizing next global stress, with a tiny action-cost tie-breaker."""

    next_states = _clip_state(state[None, :] + ACTION_EFFECTS)
    residual = target[None, :] - next_states
    scores = np.linalg.norm(residual, axis=1) + ACTION_COSTS
    return int(np.argmin(scores))


def apply_action(
    state: np.ndarray,
    action: int,
    rng: np.random.Generator,
    *,
    noise_scale: float = 0.004,
) -> np.ndarray:
    noise = rng.normal(0.0, noise_scale, size=state.shape).astype(np.float32)
    return _clip_state(state + ACTION_EFFECTS[int(action)] + noise)


def condition_observation(
    *,
    condition: str,
    state: np.ndarray,
    target: np.ndarray,
    stress_history: list[np.ndarray],
    lag: int = 8,
) -> np.ndarray:
    """Return fixed-width observation for one architecture condition."""

    live = _stress(state, target)
    proxy = _stress(state, DEFAULT_TARGET)
    zero = np.zeros(3, dtype=np.float32)

    if condition == "reward_only":
        state_part = zero
        signal = zero
        proxy_part = zero
    elif condition == "local_state":
        state_part = state
        signal = zero
        proxy_part = proxy
    elif condition == "stale_governor":
        state_part = state
        index = max(0, len(stress_history) - lag)
        signal = stress_history[index] if stress_history else zero
        proxy_part = proxy
    elif condition == "wrong_governor":
        state_part = state
        signal = _stress(state, DECOY_TARGET)
        proxy_part = proxy
    elif condition == "virtual_governor":
        state_part = state
        signal = live
        proxy_part = proxy
    else:
        raise ValueError(f"unknown condition: {condition}")

    obs = np.concatenate([state_part, signal, proxy_part]).astype(np.float32)
    if obs.shape != (OBS_DIM,):
        raise AssertionError(f"bad observation shape: {obs.shape}")
    return obs


def generate_supervised_rollouts(
    *,
    condition: str,
    seed: int,
    episodes: int,
    steps: int,
    shift_period: int,
) -> tuple[np.ndarray, np.ndarray]:
    rng = _rng(seed)
    observations: list[np.ndarray] = []
    labels: list[int] = []

    for _ in range(episodes):
        state = rng.uniform(0.25, 0.75, size=3).astype(np.float32)
        target = np.array(TARGETS[int(rng.integers(0, len(TARGETS)))], dtype=np.float32)
        stress_history: list[np.ndarray] = []
        for step in range(steps):
            if step > 0 and step % shift_period == 0:
                target = _next_target(target, rng)
            stress_history.append(_stress(state, target))
            observations.append(
                condition_observation(
                    condition=condition,
                    state=state,
                    target=target,
                    stress_history=stress_history,
                )
            )
            action = oracle_action(state, target)
            labels.append(action)
            if rng.random() < 0.78:
                chosen = action
            else:
                chosen = int(rng.integers(0, N_ACTIONS))
            state = apply_action(state, chosen, rng)

    return np.stack(observations).astype(np.float32), np.array(labels, dtype=np.int64)


def _build_model(seed: int):
    import torch

    torch.manual_seed(seed)
    return torch.nn.Sequential(
        torch.nn.Linear(OBS_DIM, 64),
        torch.nn.ReLU(),
        torch.nn.Linear(64, 64),
        torch.nn.ReLU(),
        torch.nn.Linear(64, N_ACTIONS),
    )


def train_policy(
    *,
    condition: str,
    seed: int,
    device: str,
    train_episodes: int,
    train_steps: int,
    shift_period: int,
    epochs: int,
) -> tuple[Any, float]:
    import torch

    x_np, y_np = generate_supervised_rollouts(
        condition=condition,
        seed=seed,
        episodes=train_episodes,
        steps=train_steps,
        shift_period=shift_period,
    )
    model = _build_model(seed).to(device)
    x = torch.tensor(x_np, dtype=torch.float32, device=device)
    y = torch.tensor(y_np, dtype=torch.long, device=device)
    opt = torch.optim.AdamW(model.parameters(), lr=2.5e-3, weight_decay=1e-4)
    loss_fn = torch.nn.CrossEntropyLoss()
    batch_size = 512
    final_loss = 0.0
    for _ in range(epochs):
        order = torch.randperm(x.shape[0], device=device)
        for start in range(0, x.shape[0], batch_size):
            idx = order[start : start + batch_size]
            logits = model(x[idx])
            loss = loss_fn(logits, y[idx])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            final_loss = float(loss.detach().cpu())
    return model, final_loss


def evaluate_policy(
    model: Any,
    *,
    condition: str,
    seed: int,
    device: str,
    eval_episodes: int,
    eval_steps: int,
    shift_period: int,
    post_shift_window: int,
) -> dict[str, float | list[float]]:
    import torch

    rng = _rng(seed + 9_999)
    correct = 0
    total = 0
    stress_values: list[float] = []
    final_stresses: list[float] = []
    recovery_hits: list[float] = []
    recovery_steps: list[float] = []
    post_shift_values: list[list[float]] = [[] for _ in range(post_shift_window)]

    model.eval()
    with torch.no_grad():
        for _ in range(eval_episodes):
            state = rng.uniform(0.25, 0.75, size=3).astype(np.float32)
            target = np.array(TARGETS[int(rng.integers(0, len(TARGETS)))], dtype=np.float32)
            stress_history: list[np.ndarray] = []
            episode_stress: list[float] = []
            shift_points: list[int] = []
            for step in range(eval_steps):
                if step > 0 and step % shift_period == 0:
                    target = _next_target(target, rng)
                    shift_points.append(step)
                stress_history.append(_stress(state, target))
                oracle = oracle_action(state, target)
                obs = condition_observation(
                    condition=condition,
                    state=state,
                    target=target,
                    stress_history=stress_history,
                )
                logits = model(torch.tensor(obs[None, :], dtype=torch.float32, device=device))
                action = int(torch.argmax(logits, dim=1).detach().cpu().item())
                correct += int(action == oracle)
                total += 1
                state = apply_action(state, action, rng)
                value = stress_norm(state, target)
                stress_values.append(value)
                episode_stress.append(value)

            final_stresses.append(episode_stress[-1])
            for shift in shift_points:
                window = episode_stress[shift : shift + post_shift_window]
                if not window:
                    continue
                for offset, value in enumerate(window):
                    post_shift_values[offset].append(value)
                below = [i for i, value in enumerate(window) if value <= 0.18]
                recovery_hits.append(float(bool(below)))
                recovery_steps.append(float(below[0] if below else post_shift_window))

    curve = [mean(values) if values else 0.0 for values in post_shift_values]
    return {
        "action_accuracy": correct / max(1, total),
        "mean_stress": mean(stress_values),
        "post_shift_stress_auc": mean(curve),
        "recovery_rate": mean(recovery_hits) if recovery_hits else 0.0,
        "mean_recovery_steps": mean(recovery_steps) if recovery_steps else float(post_shift_window),
        "final_stress": mean(final_stresses),
        "post_shift_curve": curve,
    }


def run_trial(
    *,
    condition: str,
    seed: int,
    device: str = "cuda",
    train_episodes: int = 96,
    train_steps: int = 56,
    eval_episodes: int = 96,
    eval_steps: int = 72,
    shift_period: int = 18,
    post_shift_window: int = 16,
    epochs: int = 180,
) -> TrialResult:
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition: {condition}")
    model, loss = train_policy(
        condition=condition,
        seed=seed,
        device=device,
        train_episodes=train_episodes,
        train_steps=train_steps,
        shift_period=shift_period,
        epochs=epochs,
    )
    metrics = evaluate_policy(
        model,
        condition=condition,
        seed=seed,
        device=device,
        eval_episodes=eval_episodes,
        eval_steps=eval_steps,
        shift_period=shift_period,
        post_shift_window=post_shift_window,
    )
    mean_stress = float(cast(float, metrics["mean_stress"]))
    post_shift_curve = cast(list[float], metrics["post_shift_curve"])
    return TrialResult(
        condition=condition,
        seed=seed,
        train_loss=loss,
        action_accuracy=float(cast(float, metrics["action_accuracy"])),
        mean_stress=mean_stress,
        post_shift_stress_auc=float(cast(float, metrics["post_shift_stress_auc"])),
        recovery_rate=float(cast(float, metrics["recovery_rate"])),
        mean_recovery_steps=float(cast(float, metrics["mean_recovery_steps"])),
        final_stress=float(cast(float, metrics["final_stress"])),
        global_recovery_score=max(0.0, 1.0 - mean_stress / 0.85),
        post_shift_curve=[float(value) for value in post_shift_curve],
    )


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_condition: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_condition.setdefault(str(record["condition"]), []).append(record)

    rows: list[dict[str, Any]] = []
    for condition in CONDITIONS:
        group = by_condition.get(condition, [])
        if not group:
            continue
        curve_len = len(group[0]["post_shift_curve"])
        mean_curve = [
            mean(float(row["post_shift_curve"][i]) for row in group)
            for i in range(curve_len)
        ]
        rows.append(
            {
                "condition": condition,
                "label": CONDITION_LABELS[condition],
                "n": len(group),
                "action_accuracy": mean(float(row["action_accuracy"]) for row in group),
                "mean_stress": mean(float(row["mean_stress"]) for row in group),
                "post_shift_stress_auc": mean(
                    float(row["post_shift_stress_auc"]) for row in group
                ),
                "recovery_rate": mean(float(row["recovery_rate"]) for row in group),
                "mean_recovery_steps": mean(
                    float(row["mean_recovery_steps"]) for row in group
                ),
                "final_stress": mean(float(row["final_stress"]) for row in group),
                "global_recovery_score": mean(
                    float(row["global_recovery_score"]) for row in group
                ),
                "post_shift_curve": mean_curve,
            }
        )

    ranked = sorted(rows, key=lambda row: row["global_recovery_score"], reverse=True)
    baseline = next(
        (row for row in rows if row["condition"] == "reward_only"),
        None,
    )
    governor = next(
        (row for row in rows if row["condition"] == "virtual_governor"),
        None,
    )
    delta = None
    if baseline and governor:
        delta = governor["global_recovery_score"] - baseline["global_recovery_score"]
    return {
        "by_condition": rows,
        "ranking": ranked,
        "headline_delta_recovery_score": delta,
    }
