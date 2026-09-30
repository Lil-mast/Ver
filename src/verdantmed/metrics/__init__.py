"""Segmentation metrics."""

from __future__ import annotations

import torch


def dice_per_class(
    pred: torch.Tensor,
    target: torch.Tensor,
    num_classes: int,
    ignore_background: bool = True,
    eps: float = 1e-6,
) -> torch.Tensor:
    """Mean Dice over batch for each class.

    pred/target: (B, H, W) long class indices.
    Returns: (C,) or (C-1,) if ignore_background.
    """
    start = 1 if ignore_background else 0
    scores = []
    for c in range(start, num_classes):
        p = pred == c
        t = target == c
        inter = (p & t).sum().float()
        denom = p.sum().float() + t.sum().float()
        scores.append((2 * inter + eps) / (denom + eps))
    if not scores:
        return torch.zeros(0, device=pred.device)
    return torch.stack(scores)


def dice_mean(
    pred: torch.Tensor,
    target: torch.Tensor,
    num_classes: int,
    ignore_background: bool = True,
) -> torch.Tensor:
    return dice_per_class(pred, target, num_classes, ignore_background).mean()
