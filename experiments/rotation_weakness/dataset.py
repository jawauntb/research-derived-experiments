#!/usr/bin/env python3
"""Synthetic rotation-equivariant image classification dataset.

Each class is defined by a fixed stroke pattern on a 16×16 grid. The
underlying group is Z_n cyclic rotation of the image plane (we use n=8
by default, i.e. 45-degree increments).

Training shows each class at only a *subset* of rotations. The held-out
rotations are the OOD set. This recreates the partially-observed cyclic
symmetry setup of Perin and Deny (2024) with weakness as the additional
measurement.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import numpy as np
import torch
from scipy.ndimage import rotate as scipy_rotate


GRID_SIZE = 16
N_CLASSES = 8


# Each class is a list of stroke segments (x1, y1, x2, y2) in [0, 1]
# normalized coordinates. Strokes are drawn as filled lines onto the grid.
# These are chosen to be distinguishable and have non-trivial rotational
# variation (so rotating one class image does NOT trivially match another).
STROKE_PATTERNS: list[list[tuple[float, float, float, float]]] = [
    [(0.1, 0.5, 0.9, 0.5)],                                # horizontal line
    [(0.5, 0.1, 0.5, 0.9)],                                # vertical line
    [(0.1, 0.1, 0.9, 0.9)],                                # main diagonal
    [(0.1, 0.9, 0.9, 0.1)],                                # anti-diagonal
    [(0.2, 0.5, 0.5, 0.2), (0.5, 0.2, 0.8, 0.5)],          # caret pointing up
    [(0.2, 0.5, 0.5, 0.8), (0.5, 0.8, 0.8, 0.5)],          # caret pointing down
    [(0.2, 0.2, 0.8, 0.2), (0.2, 0.2, 0.2, 0.8)],          # L-shape
    [(0.5, 0.2, 0.8, 0.5), (0.8, 0.5, 0.5, 0.8), (0.5, 0.8, 0.2, 0.5), (0.2, 0.5, 0.5, 0.2)],  # diamond
]


@dataclass(frozen=True)
class RotatedSample:
    image: torch.Tensor          # [1, H, W]
    label: int
    rotation_index: int          # 0..n_rot-1
    rotation_degrees: float


def _render_pattern(pattern: list[tuple[float, float, float, float]], size: int = GRID_SIZE) -> np.ndarray:
    img = np.zeros((size, size), dtype=np.float32)
    for x1, y1, x2, y2 in pattern:
        px1, py1 = int(round(x1 * (size - 1))), int(round(y1 * (size - 1)))
        px2, py2 = int(round(x2 * (size - 1))), int(round(y2 * (size - 1)))
        steps = max(abs(px2 - px1), abs(py2 - py1)) + 1
        for s in range(steps + 1):
            t = s / max(1, steps)
            x = int(round(px1 + t * (px2 - px1)))
            y = int(round(py1 + t * (py2 - py1)))
            if 0 <= x < size and 0 <= y < size:
                img[y, x] = 1.0
    return img


def render_class_base(label: int) -> np.ndarray:
    if not 0 <= label < N_CLASSES:
        raise ValueError(f"label must be in [0, {N_CLASSES})")
    return _render_pattern(STROKE_PATTERNS[label])


def rotate_image(img: np.ndarray, degrees: float) -> np.ndarray:
    rotated = scipy_rotate(
        img, angle=degrees, reshape=False, order=1, mode="constant", cval=0.0
    )
    return np.clip(rotated, 0.0, 1.0).astype(np.float32)


def make_sample(label: int, rotation_index: int, n_rotations: int) -> RotatedSample:
    base = render_class_base(label)
    degrees = rotation_index * (360.0 / n_rotations)
    rotated = rotate_image(base, degrees)
    return RotatedSample(
        image=torch.from_numpy(rotated).unsqueeze(0),
        label=label,
        rotation_index=rotation_index,
        rotation_degrees=degrees,
    )


@dataclass(frozen=True)
class RotationSplit:
    n_rotations: int
    train_rotations_per_class: dict[int, tuple[int, ...]]
    ood_rotations_per_class: dict[int, tuple[int, ...]]
    rng_seed: int


def make_partial_rotation_split(
    *,
    n_rotations: int = 8,
    train_per_class: int = 3,
    seed: int = 0,
) -> RotationSplit:
    if not 1 <= train_per_class < n_rotations:
        raise ValueError("train_per_class must be in [1, n_rotations)")
    rng = random.Random(seed)
    train: dict[int, tuple[int, ...]] = {}
    ood: dict[int, tuple[int, ...]] = {}
    for label in range(N_CLASSES):
        rots = list(range(n_rotations))
        rng.shuffle(rots)
        train_rots = tuple(sorted(rots[:train_per_class]))
        ood_rots = tuple(sorted(rots[train_per_class:]))
        train[label] = train_rots
        ood[label] = ood_rots
    return RotationSplit(
        n_rotations=n_rotations,
        train_rotations_per_class=train,
        ood_rotations_per_class=ood,
        rng_seed=seed,
    )


def materialize_split(
    split: RotationSplit,
    *,
    samples_per_class_rotation: int = 4,
    noise_std: float = 0.05,
    seed: int = 0,
) -> tuple[list[RotatedSample], list[RotatedSample]]:
    rng = np.random.RandomState(seed)
    train_samples: list[RotatedSample] = []
    ood_samples: list[RotatedSample] = []

    for label, rots in split.train_rotations_per_class.items():
        for r in rots:
            for _ in range(samples_per_class_rotation):
                s = make_sample(label, r, split.n_rotations)
                noisy = s.image + torch.from_numpy(
                    rng.normal(0.0, noise_std, size=s.image.shape).astype(np.float32)
                )
                train_samples.append(
                    RotatedSample(
                        image=noisy.clamp(0.0, 1.0),
                        label=label,
                        rotation_index=r,
                        rotation_degrees=s.rotation_degrees,
                    )
                )
    for label, rots in split.ood_rotations_per_class.items():
        for r in rots:
            for _ in range(samples_per_class_rotation):
                s = make_sample(label, r, split.n_rotations)
                noisy = s.image + torch.from_numpy(
                    rng.normal(0.0, noise_std, size=s.image.shape).astype(np.float32)
                )
                ood_samples.append(
                    RotatedSample(
                        image=noisy.clamp(0.0, 1.0),
                        label=label,
                        rotation_index=r,
                        rotation_degrees=s.rotation_degrees,
                    )
                )
    return train_samples, ood_samples


def to_tensors(samples: list[RotatedSample]) -> tuple[torch.Tensor, torch.Tensor]:
    images = torch.stack([s.image for s in samples], dim=0)
    labels = torch.tensor([s.label for s in samples], dtype=torch.long)
    return images, labels


def rotation_group_elements(n_rotations: int) -> list[float]:
    """Return the angle in degrees of each cyclic rotation index."""
    return [k * (360.0 / n_rotations) for k in range(n_rotations)]
