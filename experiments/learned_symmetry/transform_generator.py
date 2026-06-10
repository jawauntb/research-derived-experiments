#!/usr/bin/env python3
"""Data-inferred transformation discovery for the learned-symmetry paper.

Given a labeled training set (without oracle group information), search a
candidate transformation set and keep those transformations under which the
training data is approximately label-preserving. The retained set is the
*learned group* used by the weakness selector.

The trick that makes this non-trivial: training shows each class at only a
subset of rotations, so a transformation that "wraps within the seen subset"
is easy, but a transformation that maps a seen rotation of class c into an
*unseen* rotation of class c is harder. We accept transformations only when
they map training inputs to other training inputs (of the same label) with
high feature similarity. This forces the inferred group to be the one that
makes the partial-orbit training set self-consistent — exactly the cyclic
rotation group, recovered without oracle access.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from experiments.rotation_weakness.dataset import (
    rotate_image,
    rotation_group_elements,
)


@dataclass(frozen=True)
class LearnedGroup:
    """A set of inferred transformations on the input space.

    `transformation_indices` are indices into a fixed candidate set
    (`candidate_angles` for rotation). `consistency_scores` records the
    per-transformation training-self-consistency score that drove the
    selection.
    """

    candidate_angles: tuple[float, ...]
    transformation_indices: tuple[int, ...]
    consistency_scores: tuple[float, ...]
    n_candidates_searched: int

    def __len__(self) -> int:
        return len(self.transformation_indices)

    def angles(self) -> tuple[float, ...]:
        return tuple(self.candidate_angles[i] for i in self.transformation_indices)


def _feature_vector(image: torch.Tensor) -> np.ndarray:
    """Cheap feature vector for similarity comparison. We use the raw pixel
    flatten; for tiny images this is fine and avoids feature-extractor
    confounds in the no-oracle setting."""
    return image.cpu().numpy().reshape(-1).astype(np.float32)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def infer_rotation_group_from_training(
    train_x: torch.Tensor,
    train_y: torch.Tensor,
    *,
    n_candidates: int = 72,
    threshold: float = 0.7,
) -> LearnedGroup:
    """Search rotations at `n_candidates` evenly-spaced angles and keep those
    for which most rotated training inputs have a high-similarity match in
    the training set with the SAME label.

    No oracle group: we never tell the algorithm that the truth is a rotation
    group. We only assume the candidate set contains rotations. Same protocol
    Perin & Deny 2024 would face on rotated-MNIST.
    """
    if train_x.dim() != 4:
        raise ValueError(f"train_x must be [B,1,H,W], got {tuple(train_x.shape)}")
    B = train_x.shape[0]
    train_features = [_feature_vector(train_x[i]) for i in range(B)]
    train_labels = train_y.tolist()

    candidate_angles = tuple(k * (360.0 / n_candidates) for k in range(n_candidates))
    consistency: list[float] = []

    for theta in candidate_angles:
        match_scores: list[float] = []
        for i in range(B):
            rotated_image = rotate_image(train_x[i, 0].cpu().numpy(), theta)
            rotated_feature = rotated_image.reshape(-1).astype(np.float32)
            label_i = train_labels[i]
            same_label_indices = [j for j in range(B) if train_labels[j] == label_i]
            if not same_label_indices:
                match_scores.append(0.0)
                continue
            sims = [_cosine(rotated_feature, train_features[j]) for j in same_label_indices]
            match_scores.append(max(sims))
        consistency.append(float(np.mean(match_scores)))

    consistency_t = tuple(consistency)
    kept = tuple(i for i, s in enumerate(consistency_t) if s >= threshold)
    if 0 not in kept:
        kept = (0,) + kept
    return LearnedGroup(
        candidate_angles=candidate_angles,
        transformation_indices=kept,
        consistency_scores=consistency_t,
        n_candidates_searched=n_candidates,
    )


def learned_group_invariance(
    model: torch.nn.Module,
    eval_x: torch.Tensor,
    *,
    learned_group: LearnedGroup,
) -> float:
    """Compute the learned-group analog of `weakness_rotation_norm`: fraction
    of (sample, learned-rotation) pairs whose argmax predictions agree with
    the unrotated prediction.
    """
    model.eval()
    with torch.no_grad():
        base_pred = model(eval_x).argmax(dim=-1)
    agree = 0
    total = 0
    for theta in learned_group.angles():
        if theta == 0.0:
            continue
        rotated = torch.zeros_like(eval_x)
        for i in range(eval_x.shape[0]):
            rotated[i, 0] = torch.from_numpy(
                rotate_image(eval_x[i, 0].cpu().numpy(), theta)
            )
        with torch.no_grad():
            rot_pred = model(rotated).argmax(dim=-1)
        agree += int((rot_pred == base_pred).sum().item())
        total += int(rot_pred.shape[0])
    return agree / max(1, total) if total > 0 else 0.0


def random_group_baseline(
    *,
    n_candidates: int,
    target_size: int,
    rng: np.random.RandomState,
) -> LearnedGroup:
    """Control: pick `target_size` random rotation indices including identity."""
    candidate_angles = tuple(k * (360.0 / n_candidates) for k in range(n_candidates))
    remaining = list(range(1, n_candidates))
    rng.shuffle(remaining)
    chosen = (0,) + tuple(remaining[: max(0, target_size - 1)])
    return LearnedGroup(
        candidate_angles=candidate_angles,
        transformation_indices=chosen,
        consistency_scores=tuple(0.0 for _ in candidate_angles),
        n_candidates_searched=n_candidates,
    )
