#!/usr/bin/env python3
"""Discover the symmetry group implicit in a contrastive-trained encoder.

Pivot from the direct rotation-angle generator (which mode-collapses on
this data) to a more tractable formulation:

  1. Train an encoder e_φ via SimCLR-style contrastive loss on same-class
     pairs from the training set.
  2. The encoder's *implicit invariance group* is the set of input-space
     transformations T such that e_φ(T(x)) ≈ e_φ(x) for held-out x.
  3. We discover this group by scoring a fine grid of candidate
     transformations (rotations at 5° resolution = 72 candidates) against
     the encoder's invariance.

This replaces pixel-space cosine in the v1 enumerative procedure with a
*learned-feature* cosine. The encoder is the "neural component"; the
candidate enumeration becomes fine-grained.

Compared to the rotation-angle generator above, this gives up on
generating continuous transformations directly but reliably recovers the
finite-group structure that the data actually admits, and supports
non-enumerable extensions (drop in any feature space for any modality).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from experiments.rotation_weakness.dataset import rotate_image


@dataclass(frozen=True)
class EncoderConfig:
    seed: int
    embed_dim: int = 32
    hidden_width: int = 64
    encoder_channels: int = 16
    learning_rate: float = 3e-3
    weight_decay: float = 1e-4
    epochs: int = 400
    temperature: float = 0.5


class SmallEncoder(nn.Module):
    def __init__(self, *, grid: int = 16, channels: int = 16, hidden: int = 64,
                 embed_dim: int = 32) -> None:
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Conv2d(1, channels, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(channels, channels * 2, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Flatten(),
        )
        feat_dim = channels * 2 * (grid // 4) * (grid // 4)
        self.head = nn.Sequential(
            nn.Linear(feat_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, embed_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.backbone(x)
        z = self.head(h)
        return F.normalize(z, dim=-1)


def supervised_contrastive_loss(
    z: torch.Tensor, labels: torch.Tensor, *, temperature: float = 0.5
) -> torch.Tensor:
    """SupCon (Khosla et al. 2020) style supervised contrastive loss.

    Pulls same-label embeddings together, pushes different-label apart.
    """
    B = z.shape[0]
    sim = (z @ z.t()) / temperature  # [B, B]
    mask_same = (labels.unsqueeze(0) == labels.unsqueeze(1)).float()
    mask_same.fill_diagonal_(0)
    mask_diff = 1.0 - mask_same
    mask_diff.fill_diagonal_(0)
    # log-sum-exp over negatives + 1 self-mask trick:
    logits = sim - sim.max(dim=1, keepdim=True).values.detach()
    exp_logits = torch.exp(logits)
    exp_logits = exp_logits * (1 - torch.eye(B))
    log_prob = logits - torch.log(exp_logits.sum(dim=1, keepdim=True).clamp(min=1e-9))
    mean_log_prob_pos = (mask_same * log_prob).sum(dim=1) / mask_same.sum(dim=1).clamp(min=1)
    return -mean_log_prob_pos.mean()


def train_encoder(
    *,
    train_x: torch.Tensor,
    train_y: torch.Tensor,
    config: EncoderConfig,
) -> tuple[SmallEncoder, list[float]]:
    torch.manual_seed(config.seed)
    np.random.seed(config.seed)
    grid = train_x.shape[-1]
    model = SmallEncoder(
        grid=grid,
        channels=config.encoder_channels,
        hidden=config.hidden_width,
        embed_dim=config.embed_dim,
    )
    opt = torch.optim.Adam(model.parameters(), lr=config.learning_rate,
                           weight_decay=config.weight_decay)
    losses: list[float] = []
    for _ in range(config.epochs):
        model.train()
        opt.zero_grad()
        z = model(train_x)
        loss = supervised_contrastive_loss(z, train_y, temperature=config.temperature)
        loss.backward()
        opt.step()
        losses.append(float(loss.item()))
    return model, losses


def score_invariance_under_rotation(
    *,
    encoder: SmallEncoder,
    eval_x: torch.Tensor,
    angles_deg: list[float],
) -> dict[float, float]:
    """For each candidate angle θ, compute mean cosine similarity between
    encoder(x) and encoder(rotate(x, θ)) over the eval set.

    A rotation that lies in the encoder's implicit invariance group will
    give cosine ≈ 1. Random rotations will give lower cosine.
    """
    encoder.eval()
    with torch.no_grad():
        base = encoder(eval_x)  # [B, D]

    scores: dict[float, float] = {}
    for theta in angles_deg:
        rot = torch.zeros_like(eval_x)
        for i in range(eval_x.shape[0]):
            rot[i, 0] = torch.from_numpy(rotate_image(eval_x[i, 0].cpu().numpy(), theta))
        with torch.no_grad():
            rot_z = encoder(rot)
        cosines = (base * rot_z).sum(dim=-1)
        scores[theta] = float(cosines.mean().item())
    return scores


def infer_group_from_encoder(
    *,
    scores: dict[float, float],
    threshold: float,
    keep_identity: bool = True,
) -> list[float]:
    """Pick angles whose encoder-invariance cosine exceeds the threshold."""
    kept = [theta for theta, s in scores.items() if s >= threshold]
    if keep_identity and 0.0 not in kept:
        kept = [0.0] + kept
    return sorted(kept)
