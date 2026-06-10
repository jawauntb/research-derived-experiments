#!/usr/bin/env python3
"""Neural transformation generator for non-enumerable symmetries.

Replaces the enumerative `infer_rotation_group_from_training` procedure with
a small neural module that *generates* candidate transformations from a
continuous latent space, rather than scoring a hand-picked finite set.

Architecture:

  G_φ(x, z) → θ
      An image-conditioned scalar generator. Given anchor image x ∈ R^{1×H×W}
      and latent z ∈ R^d, predicts a rotation angle θ ∈ R (radians).
      The transformed image is rotate(x, θ), via differentiable
      affine_grid + grid_sample so gradients flow through.

Training loss:

  For each (x_i, y_i) in the training batch and a sampled z, the predicted
  rotation x_rot = rotate(x_i, θ) should be close (in pixel-space) to the
  *nearest* training image x_j with the same label. This pulls θ toward
  values that map intra-class. We also regularize so multiple z draws
  produce different θs (diversity term) and so θ=0 is reachable (identity
  preservation).

After training, sampling many z's per anchor traces out the *learned
orbit* of that anchor. The discovered group is the set of distinct θ
values that recur across anchors. If the true symmetry is Z_8, the
learned orbit should cluster at multiples of 45°.

This is a clean test of (iii): can a neural module recover the symmetry
*generator* (not the symmetry score) from training data alone?
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass(frozen=True)
class GeneratorConfig:
    seed: int
    hidden_width: int = 64
    z_dim: int = 4
    encoder_channels: int = 16
    learning_rate: float = 3e-3
    weight_decay: float = 1e-4
    diversity_weight: float = 1.0  # high: encourage spread in z
    identity_weight: float = 0.0  # reserved for identity-preservation variants
    epochs: int = 300
    n_diversity_pairs: int = 4


class RotationGenerator(nn.Module):
    """Image-conditioned rotation-angle generator."""

    def __init__(self, *, grid: int = 16, hidden: int = 64, z_dim: int = 4,
                 channels: int = 16) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(1, channels, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(channels, channels * 2, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Flatten(),
        )
        feat_dim = channels * 2 * (grid // 4) * (grid // 4)
        self.angle_head = nn.Sequential(
            nn.Linear(feat_dim + z_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, 1),
        )

    def forward(self, x: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
        """Returns predicted rotation angles in radians, shape [B]."""
        feat = self.encoder(x)
        combined = torch.cat([feat, z], dim=-1)
        return self.angle_head(combined).squeeze(-1)


def rotate_batch_differentiable(x: torch.Tensor, angle: torch.Tensor) -> torch.Tensor:
    """Batch rotation of [B, 1, H, W] by per-example angles (radians).

    Uses affine_grid + grid_sample so gradients flow through the angle.
    """
    cos_a = torch.cos(angle)
    sin_a = torch.sin(angle)
    zero = torch.zeros_like(angle)
    theta = torch.stack(
        [
            torch.stack([cos_a, -sin_a, zero], dim=-1),
            torch.stack([sin_a, cos_a, zero], dim=-1),
        ],
        dim=1,
    )
    grid = F.affine_grid(theta, x.shape, align_corners=False)
    return F.grid_sample(x, grid, align_corners=False, padding_mode="zeros")


def train_generator(
    *,
    train_x: torch.Tensor,
    train_y: torch.Tensor,
    config: GeneratorConfig,
) -> tuple[RotationGenerator, list[float]]:
    """Train the rotation generator on the labeled training set.

    Loss components:
      - intra-class distance: min ||rotate(x_i, θ) − x_j||² over same-label j
      - diversity: encourage different z's to produce different θ's
      - identity: small penalty on |θ| when z is small (≈0), so the
        generator can produce the identity
    """
    torch.manual_seed(config.seed)
    np.random.seed(config.seed)
    grid = train_x.shape[-1]
    model = RotationGenerator(
        grid=grid,
        hidden=config.hidden_width,
        z_dim=config.z_dim,
        channels=config.encoder_channels,
    )
    opt = torch.optim.Adam(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )

    B = train_x.shape[0]
    train_flat = train_x.view(B, -1)
    same_class = (train_y.unsqueeze(0) == train_y.unsqueeze(1)).float()
    same_class.fill_diagonal_(0)

    losses: list[float] = []
    for _ in range(config.epochs):
        model.train()
        opt.zero_grad()

        # Multiple z draws so the diversity loss can act per-anchor.
        K = config.n_diversity_pairs
        all_thetas = []
        intra_terms = []
        for _ in range(K):
            z = torch.randn(B, config.z_dim)
            theta = model(train_x, z)
            x_rot = rotate_batch_differentiable(train_x, theta)
            x_rot_flat = x_rot.view(B, -1)
            diff = x_rot_flat.unsqueeze(1) - train_flat.unsqueeze(0)
            dist = (diff ** 2).sum(dim=-1)
            masked = dist + (1 - same_class) * 1e6
            intra_terms.append(masked.min(dim=1).values)
            all_thetas.append(theta)

        intra_loss = torch.stack(intra_terms, dim=0).mean()

        # Diversity: for each anchor, encourage the K predicted angles to
        # cover the circle. We use 1 + mean cos(θ_i - θ_j) over distinct
        # pairs — minimizing pushes the pairs apart on the circle.
        thetas = torch.stack(all_thetas, dim=0)  # [K, B]
        diversity_term = 0.0
        n_pairs = 0
        for i in range(K):
            for j in range(i + 1, K):
                diversity_term = diversity_term + (1.0 + torch.cos(thetas[i] - thetas[j])).mean()
                n_pairs += 1
        diversity_loss = diversity_term / max(1, n_pairs)

        loss = intra_loss + config.diversity_weight * diversity_loss
        loss.backward()
        opt.step()
        losses.append(float(loss.item()))
    return model, losses


def sample_learned_orbit(
    *,
    model: RotationGenerator,
    x: torch.Tensor,
    n_samples: int = 256,
    z_dim: int = 4,
    seed: Optional[int] = None,
) -> torch.Tensor:
    """Sample `n_samples` rotation angles from the generator for each anchor.

    Returns a tensor of shape [B, n_samples] in radians, modulo 2π.
    """
    if seed is not None:
        torch.manual_seed(seed)
    model.eval()
    B = x.shape[0]
    angles = []
    with torch.no_grad():
        for _ in range(n_samples):
            z = torch.randn(B, z_dim)
            theta = model(x, z)
            angles.append(theta.cpu())
    angles_t = torch.stack(angles, dim=1)  # [B, n_samples]
    # Wrap to [0, 2π).
    angles_t = torch.remainder(angles_t, 2 * np.pi)
    return angles_t


def discover_generator_modes(
    angles_rad: torch.Tensor, *, n_bins: int = 72, top_k: int = 12,
    nms_window_bins: int = 2,
) -> list[float]:
    """Find peaks in the generator's angle distribution using non-maximum
    suppression so we don't return K bins of one tall cluster.

    Returns up to `top_k` distinct peaks in degrees, sorted.
    """
    flat = angles_rad.flatten().numpy()
    counts, edges = np.histogram(flat, bins=n_bins, range=(0.0, 2 * np.pi))
    centers_rad = (edges[:-1] + edges[1:]) / 2
    centers_deg = np.degrees(centers_rad)

    # NMS: walk bins in descending count order, suppress neighbors.
    suppressed = np.zeros(n_bins, dtype=bool)
    order = np.argsort(counts)[::-1]
    peaks = []
    for idx in order:
        if suppressed[idx] or counts[idx] == 0:
            continue
        peaks.append((idx, counts[idx]))
        if len(peaks) >= top_k:
            break
        lo = max(0, idx - nms_window_bins)
        hi = min(n_bins, idx + nms_window_bins + 1)
        suppressed[lo:hi] = True
        # Also suppress wrap-around neighbors near 0/2π.
        if idx < nms_window_bins:
            suppressed[n_bins - (nms_window_bins - idx):] = True
        if idx >= n_bins - nms_window_bins:
            suppressed[: nms_window_bins - (n_bins - 1 - idx) + 1] = True
    return sorted(float(centers_deg[i]) for i, _ in peaks)


def train_generator_ensemble(
    *,
    train_x: torch.Tensor,
    train_y: torch.Tensor,
    config: GeneratorConfig,
    n_generators: int = 8,
    base_seed: int = 0,
) -> list[RotationGenerator]:
    """Train K generators with different seeds.

    Each model tends to collapse into one rotation angle; the ensemble
    covers the full discovered orbit.
    """
    models = []
    for k in range(n_generators):
        cfg_k = GeneratorConfig(
            seed=base_seed + k * 9999,
            hidden_width=config.hidden_width,
            z_dim=config.z_dim,
            encoder_channels=config.encoder_channels,
            learning_rate=config.learning_rate,
            weight_decay=config.weight_decay,
            diversity_weight=config.diversity_weight,
            identity_weight=config.identity_weight,
            epochs=config.epochs,
        )
        model, _ = train_generator(train_x=train_x, train_y=train_y, config=cfg_k)
        models.append(model)
    return models


def sample_ensemble_orbit(
    *,
    models: list[RotationGenerator],
    x: torch.Tensor,
    n_samples_per_model: int = 32,
    z_dim: int = 4,
    base_seed: int = 0,
) -> torch.Tensor:
    """Aggregate orbit samples across the ensemble."""
    all_angles = []
    for k, m in enumerate(models):
        a = sample_learned_orbit(
            model=m, x=x, n_samples=n_samples_per_model,
            z_dim=z_dim, seed=base_seed + k,
        )
        all_angles.append(a)
    return torch.cat(all_angles, dim=1)  # [B, K * n_samples_per_model]
