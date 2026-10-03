"""Model factory."""

from __future__ import annotations

from typing import Any

import torch.nn as nn
from monai.networks.nets import UNet


def build_model(cfg: dict[str, Any]) -> nn.Module:
    model_cfg = cfg["model"]
    name = model_cfg.get("name", "unet2d")
    if name != "unet2d":
        raise ValueError(f"Unsupported model: {name}")

    return UNet(
        spatial_dims=2,
        in_channels=int(model_cfg["in_channels"]),
        out_channels=int(model_cfg["out_channels"]),
        channels=tuple(model_cfg["channels"]),
        strides=tuple(model_cfg["strides"]),
        num_res_units=2,
    )
