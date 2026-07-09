#!/usr/bin/env python3
"""E2 + E3 -- Compatibility Augmentation vs Readout, with Patch-CE.

The core in-lab discriminator for M3 ("weakness is diagnostic, not causal").
Four arms train small MLPs on modular addition with strict-subset splits:

- **A** readout: no train-time augmentation, select best-of-K by post-hoc
  compatibility (weakness) score.
- **B** compatibility augmentation: train with true-group orbit augmentation
  (cyclic shifts).
- **C** wrong-group augmentation: train with random non-cyclic permutations
  of pairs (control).
- **D** loss selector: no augmentation, select best-of-K by lowest train
  loss.

Per cell we record:
- OOD accuracy on held-out pairs (E2).
- Patch-CE: cross-entropy of the model on OOD pairs after zero-ablating
  the top-k "compatibility-aligned" hidden units, minus baseline CE. Big
  patch-CE gap indicates the compatibility mode is causally used (E3).
- Wrong-group patch-CE control (anti-cheat).
- Weakness / compatibility scores (readout).

Prediction (commitment-first):
- Arm B mean OOD >> Arm A mean OOD.
- Arm B patch-CE >> Arm A patch-CE.
- Arm C patch-CE ~ 0 even though it also uses augmentation.

Run locally on CPU: small (n up to 17). Configurable via CLI.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import json
import math
from pathlib import Path
import random
from typing import Any

# We deliberately avoid the heavier structure_compatible_generalization
# infrastructure: the commitment-surface sweep needs deterministic per-cell
# control over arms and patch operations. Reuses only the low-level Table
# and pair helpers from ``commitment_surface.core``.
from experiments.commitment_surface.core import (
    all_pairs,
    mean_ci95,
    spearman,
)

Pair = tuple[int, int]


@dataclass(frozen=True)
class Config:
    modulus: int
    seed: int
    train_frac: float
    arm: str  # A / B / C / D
    hidden_width: int
    depth: int
    epochs: int
    learning_rate: float
    weight_decay: float
    aug_orbit_size: int  # for B/C: how many group elements to sample per epoch
    top_k_patch: int  # patch ablation width


@dataclass
class CellResult:
    arm: str
    modulus: int
    seed: int
    train_frac: float
    train_pairs: int
    ood_pairs: int
    train_accuracy: float
    ood_accuracy: float
    baseline_ce_ood: float
    patched_ce_ood: float
    patched_ce_ood_wrong: float
    patch_ce_delta: float
    patch_ce_delta_wrong: float
    weakness_true: float
    weakness_wrong: float
    final_train_loss: float
    hidden_width: int
    depth: int
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Torch model + training
# ---------------------------------------------------------------------------


def _load_torch() -> tuple[Any, Any, Any]:  # noqa: D401
    import torch
    import torch.nn as nn
    import torch.nn.functional as F  # type: ignore[reportUnusedImport]

    return torch, nn, F


def make_model(cfg: Config) -> Any:
    torch, nn, _ = _load_torch()

    class _ModularMLP(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            layers: list[Any] = []
            input_dim = 2 * cfg.modulus
            for _ in range(cfg.depth):
                layers.append(nn.Linear(input_dim, cfg.hidden_width))
                layers.append(nn.ReLU())
                input_dim = cfg.hidden_width
            layers.append(nn.Linear(input_dim, cfg.modulus))
            self.net = nn.Sequential(*layers)
            self.hidden_dim = cfg.hidden_width
            self.depth = cfg.depth

        def features(self, x: Any) -> Any:
            # Return activations from the last hidden layer (pre-head).
            h = x
            for layer in list(self.net)[:-1]:
                h = layer(h)
            return h

        def logits_from_features(self, feats: Any) -> Any:
            head = list(self.net)[-1]
            return head(feats)

        def forward(self, x: Any) -> Any:
            return self.net(x)

    return _ModularMLP()


def one_hot_pairs(pairs: list[Pair], modulus: int, device: Any) -> Any:
    torch, _nn, _F = _load_torch()
    out = torch.zeros(len(pairs), 2 * modulus, device=device)
    for row, (a, b) in enumerate(pairs):
        out[row, a] = 1.0
        out[row, modulus + b] = 1.0
    return out


def function_table(model: Any, modulus: int, device: Any) -> tuple[int, ...]:
    torch, _nn, _F = _load_torch()
    pairs = all_pairs(modulus)
    model.eval()
    with torch.no_grad():
        preds = model(one_hot_pairs(pairs, modulus, device)).argmax(dim=-1)
    return tuple(int(x) for x in preds.detach().cpu().tolist())


def _sample_cyclic_shift(rng: random.Random, modulus: int) -> int:
    return rng.randrange(1, modulus)


def _sample_wrong_perm(rng: random.Random, modulus: int) -> list[int]:
    while True:
        perm = list(range(modulus))
        rng.shuffle(perm)
        if any(perm[i] != (i + perm[0]) % modulus for i in range(modulus)):
            return perm


def train_arm(
    cfg: Config,
    train_pairs: list[Pair],
    device: Any,
) -> tuple[Any, float]:
    torch, _nn, F = _load_torch()
    rng = random.Random(cfg.seed)
    torch.manual_seed(cfg.seed)

    model = make_model(cfg).to(device)
    opt = torch.optim.Adam(
        model.parameters(),
        lr=cfg.learning_rate,
        weight_decay=cfg.weight_decay,
    )

    modulus = cfg.modulus
    base_inputs = one_hot_pairs(train_pairs, modulus, device)
    base_targets = torch.tensor(
        [(a + b) % modulus for a, b in train_pairs],
        dtype=torch.long,
        device=device,
    )

    final_loss = math.inf
    for _ in range(cfg.epochs):
        model.train()
        pairs_used: list[Pair] = list(train_pairs)
        labels_used: list[int] = [(a + b) % modulus for a, b in train_pairs]

        if cfg.arm == "B" and cfg.aug_orbit_size > 0:
            for _shift_i in range(cfg.aug_orbit_size):
                k = _sample_cyclic_shift(rng, modulus)
                for a, b in train_pairs:
                    pairs_used.append(((a + k) % modulus, b))
                    labels_used.append((a + b + k) % modulus)
        elif cfg.arm == "C" and cfg.aug_orbit_size > 0:
            # Wrong-group augmentation: same volume as Arm B, but the
            # augmented labels follow a permutation π that is NOT a
            # cyclic shift, so the augmented data teaches the model
            # f(π(a), b) = π(a+b) instead of f(a+k, b) = (a+b)+k. This
            # is inconsistent with the true rule on shared pairs
            # whenever π disagrees with the cyclic action, giving the
            # model a genuinely wrong equivariance to fit -- volume
            # matched to B, group specificity broken.
            for _perm_i in range(cfg.aug_orbit_size):
                perm = _sample_wrong_perm(rng, modulus)
                for a, b in train_pairs:
                    ap = perm[a]
                    pairs_used.append((ap, b))
                    labels_used.append(perm[(a + b) % modulus])

        if len(pairs_used) == len(train_pairs):
            inputs = base_inputs
            targets = base_targets
        else:
            inputs = one_hot_pairs(pairs_used, modulus, device)
            targets = torch.tensor(labels_used, dtype=torch.long, device=device)

        opt.zero_grad()
        loss = F.cross_entropy(model(inputs), targets)
        loss.backward()
        opt.step()
        final_loss = float(loss.detach().cpu().item())

    return model, final_loss


# ---------------------------------------------------------------------------
# Weakness + patch-CE analysis
# ---------------------------------------------------------------------------


def true_translation_compatibility(table: tuple[int, ...], modulus: int) -> float:
    compatible = 0
    pairs = all_pairs(modulus)
    for shift in range(modulus):
        ok = True
        for a, b in pairs:
            lhs = table[((a + shift) % modulus) * modulus + b]
            rhs = (table[a * modulus + b] + shift) % modulus
            if lhs != rhs:
                ok = False
                break
        compatible += int(ok)
    return compatible / modulus


def wrong_permutation_compatibility(
    table: tuple[int, ...],
    modulus: int,
    *,
    rng: random.Random,
    n_perms: int | None = None,
) -> float:
    target = n_perms or modulus
    perms: list[tuple[int, ...]] = []
    attempts = 0
    while len(perms) < target and attempts < 400:
        p = list(range(modulus))
        rng.shuffle(p)
        cand = tuple(p)
        if cand[0] == 0 and all(cand[i] == i for i in range(modulus)):
            attempts += 1
            continue
        if any(cand[i] != (i + cand[0]) % modulus for i in range(modulus)):
            perms.append(cand)
        attempts += 1
    if not perms:
        return 0.0

    pairs = all_pairs(modulus)
    compatible = 0
    for perm in perms:
        ok = True
        for a, b in pairs:
            lhs = table[perm[a] * modulus + b]
            rhs = perm[table[a * modulus + b]]
            if lhs != rhs:
                ok = False
                break
        compatible += int(ok)
    return compatible / len(perms)


def _unit_shift_scores(model: Any, modulus: int, device: Any) -> list[float]:
    """For each last-hidden-layer unit, score its shift-equivariance.

    We measure how well the unit's activation transports under a random
    input shift ``(a, b) -> (a + k mod n, b)``. Units whose activation
    changes coherently under this action are the "compatibility mode"
    candidates -- causal-use plumbing for translation-equivariance.
    """
    torch, _nn, _F = _load_torch()
    model.eval()
    pairs = all_pairs(modulus)
    with torch.no_grad():
        feats = model.features(one_hot_pairs(pairs, modulus, device)).cpu().numpy()
    scores: list[float] = []
    hidden_dim = feats.shape[1]
    for j in range(hidden_dim):
        col = feats[:, j]
        # Total variance of unit vs variance across cyclic shifts (a-mode)
        # A pure shift-equivariant unit has activation determined by a+b
        # (or by a alone up to shift), so grouping by (a+b) mod n should
        # give low within-group variance.
        pred_sum = [(a + b) % modulus for a, b in pairs]
        groups: dict[int, list[float]] = {}
        for idx, s in enumerate(pred_sum):
            groups.setdefault(s, []).append(float(col[idx]))
        overall_mean = float(col.mean())
        overall_var = float(((col - overall_mean) ** 2).mean() + 1e-9)
        within = 0.0
        for _key, vals in groups.items():
            if not vals:
                continue
            m = sum(vals) / len(vals)
            within += sum((v - m) ** 2 for v in vals)
        within /= max(1, len(pairs))
        # High ratio -> most variance is explained by (a+b) mod n
        # (the group-orbit index). That is the compatibility mode.
        ratio = max(0.0, 1.0 - within / overall_var)
        scores.append(ratio)
    return scores


def _a_only_scores(model: Any, modulus: int, device: Any) -> list[float]:
    """Anti-cheat control: score each unit's variance-explained by ``a``
    alone (i.e. group by first coordinate).

    Compatibility (shift-equivariant) units are functions of ``a + b``, so
    grouping by ``a`` alone should NOT explain their variance -- they vary
    across ``b``. A memorizer unit that just looks at ``a`` value, in
    contrast, scores high here. We pick the top-k under this grouping and
    patch them, and expect a *much smaller* CE delta than the top-k of
    the true compatibility scoring: this is our anti-cheat.
    """
    torch, _nn, _F = _load_torch()
    model.eval()
    pairs = all_pairs(modulus)
    with torch.no_grad():
        feats = model.features(one_hot_pairs(pairs, modulus, device)).cpu().numpy()
    scores: list[float] = []
    hidden_dim = feats.shape[1]
    for j in range(hidden_dim):
        col = feats[:, j]
        groups: dict[int, list[float]] = {}
        for idx, (a, _b) in enumerate(pairs):
            groups.setdefault(a, []).append(float(col[idx]))
        overall_mean = float(col.mean())
        overall_var = float(((col - overall_mean) ** 2).mean() + 1e-9)
        within = 0.0
        for _key, vals in groups.items():
            if not vals:
                continue
            m = sum(vals) / len(vals)
            within += sum((v - m) ** 2 for v in vals)
        within /= max(1, len(pairs))
        scores.append(max(0.0, 1.0 - within / overall_var))
    return scores


def ce_with_ablation(
    model: Any,
    modulus: int,
    pairs: list[Pair],
    device: Any,
    ablate_units: list[int],
) -> float:
    """Cross-entropy on ``pairs`` after zero-ablating the given last-hidden
    units. Empty ``ablate_units`` gives the baseline CE.
    """
    torch, _nn, F = _load_torch()
    model.eval()
    with torch.no_grad():
        feats = model.features(one_hot_pairs(pairs, modulus, device))
        if ablate_units:
            for u in ablate_units:
                feats[:, u] = 0.0
        logits = model.logits_from_features(feats)
        targets = torch.tensor(
            [(a + b) % modulus for a, b in pairs],
            dtype=torch.long,
            device=device,
        )
        return float(F.cross_entropy(logits, targets).cpu().item())


# ---------------------------------------------------------------------------
# Cell runner
# ---------------------------------------------------------------------------


def _split_pairs(
    modulus: int,
    train_frac: float,
    rng: random.Random,
) -> tuple[list[Pair], list[Pair]]:
    pool = all_pairs(modulus)
    rng.shuffle(pool)
    n_train = max(1, int(round(len(pool) * train_frac)))
    return pool[:n_train], pool[n_train:]


def run_cell(cfg: Config, device_str: str = "cpu") -> CellResult:
    torch, _nn, F = _load_torch()
    device = torch.device(device_str)

    split_rng = random.Random(cfg.seed + 1009)
    train_pairs, ood_pairs = _split_pairs(cfg.modulus, cfg.train_frac, split_rng)
    model, final_loss = train_arm(cfg, train_pairs, device)

    train_accuracy = plain_accuracy_from_model(model, cfg.modulus, train_pairs, device)
    ood_accuracy = plain_accuracy_from_model(model, cfg.modulus, ood_pairs, device)

    table = function_table(model, cfg.modulus, device)
    weakness_true = true_translation_compatibility(table, cfg.modulus)
    weakness_wrong = wrong_permutation_compatibility(
        table, cfg.modulus, rng=random.Random(cfg.seed + 991)
    )

    baseline_ce = ce_with_ablation(model, cfg.modulus, ood_pairs, device, [])
    unit_scores = _unit_shift_scores(model, cfg.modulus, device)
    wrong_scores = _a_only_scores(model, cfg.modulus, device)
    top_k = min(cfg.top_k_patch, len(unit_scores))
    top_units = sorted(
        range(len(unit_scores)), key=lambda i: unit_scores[i], reverse=True
    )[:top_k]
    wrong_units = sorted(
        range(len(wrong_scores)), key=lambda i: wrong_scores[i], reverse=True
    )[:top_k]

    patched_ce = ce_with_ablation(model, cfg.modulus, ood_pairs, device, top_units)
    patched_ce_wrong = ce_with_ablation(model, cfg.modulus, ood_pairs, device, wrong_units)

    return CellResult(
        arm=cfg.arm,
        modulus=cfg.modulus,
        seed=cfg.seed,
        train_frac=cfg.train_frac,
        train_pairs=len(train_pairs),
        ood_pairs=len(ood_pairs),
        train_accuracy=train_accuracy,
        ood_accuracy=ood_accuracy,
        baseline_ce_ood=baseline_ce,
        patched_ce_ood=patched_ce,
        patched_ce_ood_wrong=patched_ce_wrong,
        patch_ce_delta=patched_ce - baseline_ce,
        patch_ce_delta_wrong=patched_ce_wrong - baseline_ce,
        weakness_true=weakness_true,
        weakness_wrong=weakness_wrong,
        final_train_loss=final_loss,
        hidden_width=cfg.hidden_width,
        depth=cfg.depth,
        metadata={
            "top_units": top_units,
            "wrong_units": wrong_units,
            "unit_score_max": max(unit_scores) if unit_scores else 0.0,
            "unit_score_mean": (
                sum(unit_scores) / len(unit_scores) if unit_scores else 0.0
            ),
        },
    )


def plain_accuracy_from_model(
    model: Any, modulus: int, pairs: list[Pair], device: Any
) -> float:
    torch, _nn, _F = _load_torch()
    model.eval()
    if not pairs:
        return 0.0
    with torch.no_grad():
        preds = model(one_hot_pairs(pairs, modulus, device)).argmax(dim=-1)
        targets = torch.tensor(
            [(a + b) % modulus for a, b in pairs],
            dtype=torch.long,
            device=device,
        )
        return float((preds == targets).float().mean().cpu().item())


# ---------------------------------------------------------------------------
# Sweep + selectors
# ---------------------------------------------------------------------------


def readout_select(cells_per_seed: list[CellResult]) -> CellResult:
    """Arm A selector: pick the cell with the highest post-hoc weakness."""
    return max(cells_per_seed, key=lambda c: c.weakness_true)


def loss_select(cells_per_seed: list[CellResult]) -> CellResult:
    """Arm D selector: pick the cell with the lowest final train loss (ties
    broken by higher train accuracy)."""
    return min(cells_per_seed, key=lambda c: (c.final_train_loss, -c.train_accuracy))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--moduli", type=str, default="7,11")
    p.add_argument("--train-fracs", type=str, default="0.5,0.7")
    p.add_argument("--seeds", type=int, default=6)
    p.add_argument("--selector-pool", type=int, default=6,
                   help="For A/D, train this many seeds and pick the best.")
    p.add_argument("--hidden-width", type=int, default=64)
    p.add_argument("--depth", type=int, default=2)
    p.add_argument("--epochs", type=int, default=1500)
    p.add_argument("--learning-rate", type=float, default=3e-3)
    p.add_argument("--weight-decay", type=float, default=1e-4)
    p.add_argument("--aug-orbit-size", type=int, default=4)
    p.add_argument("--top-k-patch", type=int, default=8)
    p.add_argument(
        "--out", type=Path,
        default=Path("experiments/commitment_surface/results/e2_e3_neural.json"),
    )
    p.add_argument(
        "--summary", type=Path,
        default=Path("experiments/commitment_surface/results/e2_e3_neural.md"),
    )
    p.add_argument("--device", type=str, default="cpu")
    return p.parse_args()


def summarize(rows: list[CellResult], selected: dict[str, list[CellResult]]) -> dict:
    def _stat(rs: list[CellResult], field: str) -> dict:
        vals = [getattr(r, field) for r in rs]
        m, lo, hi = mean_ci95(vals)
        return {"mean": m, "ci95_low": lo, "ci95_high": hi, "n": len(vals)}

    per_arm: dict[str, dict] = {}
    for arm, arm_rows in selected.items():
        if not arm_rows:
            continue
        per_arm[arm] = {
            "ood_accuracy": _stat(arm_rows, "ood_accuracy"),
            "patch_ce_delta": _stat(arm_rows, "patch_ce_delta"),
            "patch_ce_delta_wrong": _stat(arm_rows, "patch_ce_delta_wrong"),
            "weakness_true": _stat(arm_rows, "weakness_true"),
        }

    b = per_arm.get("B", {}).get("ood_accuracy", {}).get("mean", 0.0)
    a = per_arm.get("A", {}).get("ood_accuracy", {}).get("mean", 0.0)
    b_ce = per_arm.get("B", {}).get("patch_ce_delta", {}).get("mean", 0.0)
    a_ce = per_arm.get("A", {}).get("patch_ce_delta", {}).get("mean", 0.0)
    c_ce = per_arm.get("C", {}).get("patch_ce_delta", {}).get("mean", 0.0)

    # E3: readout AUC vs patch-CE regression on OOD lift.
    # Compare correlations of (weakness_true) and (patch_ce_delta) with OOD
    # accuracy across ALL cells regardless of arm.
    weak = [r.weakness_true for r in rows]
    patch = [r.patch_ce_delta for r in rows]
    ood = [r.ood_accuracy for r in rows]
    rho_weakness = spearman(weak, ood)
    rho_patch_ce = spearman(patch, ood)

    return {
        "per_arm": per_arm,
        "gap_B_minus_A_ood": b - a,
        "gap_B_minus_A_patch_ce": b_ce - a_ce,
        "gap_B_minus_C_patch_ce": b_ce - c_ce,
        "rho_weakness_ood": rho_weakness,
        "rho_patch_ce_ood": rho_patch_ce,
        # Gates from PLAN.md:
        "e2_pass_B_beats_A_ood_0p3": (b - a) >= 0.3,
        "e2_pass_B_beats_A_patch_ce_0p5": (b_ce - a_ce) >= 0.5,
        "e3_pass_patch_ce_beats_readout": rho_patch_ce > rho_weakness,
        "n_total_cells": len(rows),
    }


def write_markdown(
    summary: dict,
    all_rows: list[CellResult],
    selected: dict[str, list[CellResult]],
    path: Path,
) -> None:
    lines = [
        "# E2 + E3 — Compatibility Augmentation vs Readout, with Patch-CE",
        "",
        f"Total cells trained: {summary['n_total_cells']}",
        "",
        "## Per-arm summary (selected cell per (n, train_frac))",
        "",
        "| Arm | Description | # sel | OOD acc (mean, 95%CI) | Patch-CE Δ | Wrong Patch-CE Δ | Weakness |",
        "|---|---|---:|---|---|---|---|",
    ]
    labels = {
        "A": "Readout selector (no aug)",
        "B": "Compat aug (true cyclic group)",
        "C": "Wrong-group aug",
        "D": "Loss selector (no aug)",
    }
    for arm in ["A", "B", "C", "D"]:
        stats = summary["per_arm"].get(arm)
        if stats is None:
            continue
        ood = stats["ood_accuracy"]
        pce = stats["patch_ce_delta"]
        wce = stats["patch_ce_delta_wrong"]
        w = stats["weakness_true"]
        n_sel = ood["n"]
        lines.append(
            f"| {arm} | {labels[arm]} | {n_sel} | "
            f"{ood['mean']:.3f} [{ood['ci95_low']:.3f}, {ood['ci95_high']:.3f}] | "
            f"{pce['mean']:.3f} [{pce['ci95_low']:.3f}, {pce['ci95_high']:.3f}] | "
            f"{wce['mean']:.3f} [{wce['ci95_low']:.3f}, {wce['ci95_high']:.3f}] | "
            f"{w['mean']:.3f} |"
        )
    lines.extend([
        "",
        "## Discriminator gates",
        "",
        f"- **E2 pass — B beats A on OOD by ≥ 0.30:** "
        f"**{summary['e2_pass_B_beats_A_ood_0p3']}** "
        f"(gap = {summary['gap_B_minus_A_ood']:.3f})",
        f"- **E2 pass — B beats A on Patch-CE Δ by ≥ 0.50:** "
        f"**{summary['e2_pass_B_beats_A_patch_ce_0p5']}** "
        f"(gap = {summary['gap_B_minus_A_patch_ce']:.3f})",
        f"- **E3 pass — ρ(patch-CE, OOD) > ρ(weakness, OOD):** "
        f"**{summary['e3_pass_patch_ce_beats_readout']}** "
        f"(ρ_patch = {summary['rho_patch_ce_ood']:.3f} vs ρ_weakness = "
        f"{summary['rho_weakness_ood']:.3f})",
        "",
        "## Per-(modulus, train_frac, arm) breakdown",
        "",
        "| Arm | n | train_frac | # seeds | Mean OOD | Mean Patch-CE Δ | Mean Weakness |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    from itertools import groupby
    key = lambda r: (r.arm, r.modulus, r.train_frac)  # noqa: E731
    for (arm, mod, frac), group in groupby(sorted(all_rows, key=key), key=key):
        gs = list(group)
        lines.append(
            f"| {arm} | {mod} | {frac} | {len(gs)} | "
            f"{sum(g.ood_accuracy for g in gs) / len(gs):.3f} | "
            f"{sum(g.patch_ce_delta for g in gs) / len(gs):.3f} | "
            f"{sum(g.weakness_true for g in gs) / len(gs):.3f} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    moduli = [int(x) for x in args.moduli.split(",") if x.strip()]
    train_fracs = [float(x) for x in args.train_fracs.split(",") if x.strip()]

    all_rows: list[CellResult] = []
    selected: dict[str, list[CellResult]] = {"A": [], "B": [], "C": [], "D": []}

    for mod in moduli:
        for frac in train_fracs:
            per_arm_seed_rows: dict[str, list[CellResult]] = {
                "A": [], "B": [], "C": [], "D": []
            }
            # A and D need a selector pool. B and C are direct.
            for arm in ["A", "B", "C", "D"]:
                n_seeds = args.selector_pool if arm in ("A", "D") else args.seeds
                for i in range(n_seeds):
                    cfg = Config(
                        modulus=mod,
                        seed=20260709 + 101 * i + 13 * mod + 7 * int(frac * 100),
                        train_frac=frac,
                        arm=arm,
                        hidden_width=args.hidden_width,
                        depth=args.depth,
                        epochs=args.epochs,
                        learning_rate=args.learning_rate,
                        weight_decay=args.weight_decay,
                        aug_orbit_size=args.aug_orbit_size,
                        top_k_patch=args.top_k_patch,
                    )
                    row = run_cell(cfg, device_str=args.device)
                    all_rows.append(row)
                    per_arm_seed_rows[arm].append(row)
                    print(
                        f"[cell] arm={arm} n={mod} frac={frac} seed={cfg.seed} "
                        f"ood={row.ood_accuracy:.3f} patch_ce_delta={row.patch_ce_delta:.3f} "
                        f"weakness={row.weakness_true:.3f}",
                        flush=True,
                    )
            # Arm A selects the best-of-pool by weakness readout.
            if per_arm_seed_rows["A"]:
                selected["A"].append(readout_select(per_arm_seed_rows["A"]))
            if per_arm_seed_rows["D"]:
                selected["D"].append(loss_select(per_arm_seed_rows["D"]))
            selected["B"].extend(per_arm_seed_rows["B"])
            selected["C"].extend(per_arm_seed_rows["C"])

    summary = summarize(all_rows, selected)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        json.dump(
            {
                "summary": summary,
                "selected": {k: [asdict(r) for r in rs] for k, rs in selected.items()},
                "all_rows": [asdict(r) for r in all_rows],
                "config": vars(args) | {"out": str(args.out), "summary": str(args.summary)},
            },
            fh,
            indent=2,
            default=str,
        )
    write_markdown(summary, all_rows, selected, args.summary)
    print("---SUMMARY---")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
