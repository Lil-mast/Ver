"""Inference helpers: load checkpoint, run 2D segmentation, encode overlays."""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image

from neuro.config import load_config, project_root
from neuro.data.dataset import (
    _load_h5_pair,
    _normalize_per_channel,
    _resize_hw,
)
from neuro.models import build_model

# Distinct colors for classes 1..3 (RGB) — faded green clinical palette accents
CLASS_COLORS = {
    1: (180, 60, 60),    # necrotic / non-enhancing
    2: (60, 140, 100),   # edema — verdant
    3: (220, 180, 60),   # enhancing
}


class SegmentationService:
    """Lazy-loaded model used by the FastAPI app."""

    def __init__(
        self,
        checkpoint: Path | None = None,
        config_path: Path | None = None,
        device: str | None = None,
    ) -> None:
        root = project_root()
        self.config_path = config_path or (root / "configs" / "brats2d_unet.yaml")
        self.checkpoint_path = checkpoint or (root / "checkpoints" / "best.pt")
        self.cfg = load_config(self.config_path)
        if device:
            self.cfg["device"] = device

        requested = self.cfg.get("device", "cpu")
        if requested == "cuda" and not torch.cuda.is_available():
            requested = "cpu"
        self.device = torch.device(requested)

        self.model: torch.nn.Module | None = None
        self.meta: dict[str, Any] = {
            "checkpoint": str(self.checkpoint_path),
            "loaded": False,
            "device": str(self.device),
            "model": self.cfg.get("model", {}),
            "image_size": int(self.cfg["data"]["image_size"]),
            "num_classes": int(self.cfg["data"]["num_classes"]),
        }

    def load(self) -> None:
        if self.model is not None:
            return
        if not self.checkpoint_path.is_file():
            raise FileNotFoundError(
                f"Checkpoint not found: {self.checkpoint_path}. "
                "Run scripts/train.py first."
            )
        ckpt = torch.load(self.checkpoint_path, map_location=self.device, weights_only=False)
        if "config" in ckpt and isinstance(ckpt["config"], dict):
            saved = ckpt["config"]
            self.cfg["model"] = saved.get("model", self.cfg["model"])
            if "data" in saved and "num_classes" in saved["data"]:
                self.cfg["data"]["num_classes"] = saved["data"]["num_classes"]
            if "data" in saved and "image_size" in saved["data"]:
                self.cfg["data"]["image_size"] = saved["data"]["image_size"]

        model = build_model(self.cfg).to(self.device)
        model.load_state_dict(ckpt["model"])
        model.eval()
        self.model = model
        self.meta.update(
            {
                "loaded": True,
                "epoch": ckpt.get("epoch"),
                "val_dice": ckpt.get("val_dice"),
                "image_size": int(self.cfg["data"]["image_size"]),
                "num_classes": int(self.cfg["data"]["num_classes"]),
                "model": self.cfg.get("model", {}),
                "device": str(self.device),
            }
        )

    def preprocess_h5(self, path: Path) -> tuple[torch.Tensor, np.ndarray | None, np.ndarray]:
        """Return (image CHW float tensor, mask HW or None, display RGB uint8)."""
        image, mask = _load_h5_pair(path)
        image = _normalize_per_channel(image)
        c = image.shape[0]
        if c < 4:
            pad = np.zeros((4 - c, image.shape[1], image.shape[2]), dtype=np.float32)
            image = np.concatenate([image, pad], axis=0)
        elif c > 4:
            image = image[:4]

        size = int(self.cfg["data"]["image_size"])
        image, mask = _resize_hw(image, mask, size)

        # Display: average first 3 modalities → grayscale RGB
        vis = image[:3].mean(axis=0)
        vis = vis - vis.min()
        denom = vis.max() - vis.min()
        if denom < 1e-6:
            denom = 1.0
        vis = (vis / denom * 255.0).astype(np.uint8)
        rgb = np.stack([vis, vis, vis], axis=-1)

        tensor = torch.from_numpy(image.copy()).float()
        return tensor, mask, rgb

    @torch.inference_mode()
    def predict_array(self, image: torch.Tensor) -> np.ndarray:
        self.load()
        assert self.model is not None
        logits = self.model(image.unsqueeze(0).to(self.device))
        pred = logits.argmax(dim=1).squeeze(0).cpu().numpy().astype(np.int64)
        return pred

    def predict_h5(self, path: Path) -> dict[str, Any]:
        image, gt_mask, rgb = self.preprocess_h5(path)
        pred = self.predict_array(image)
        return self._pack_result(rgb, pred, gt_mask, source=str(path))

    def _pack_result(
        self,
        rgb: np.ndarray,
        pred: np.ndarray,
        gt_mask: np.ndarray | None,
        source: str,
    ) -> dict[str, Any]:
        overlay = render_overlay(rgb, pred)
        class_counts = {
            str(c): int((pred == c).sum())
            for c in range(int(self.cfg["data"]["num_classes"]))
        }
        result: dict[str, Any] = {
            "source": source,
            "image_size": list(pred.shape),
            "class_pixel_counts": class_counts,
            "image_png_base64": png_b64(rgb),
            "mask_png_base64": png_b64(colorize_mask(pred)),
            "overlay_png_base64": png_b64(overlay),
        }
        if gt_mask is not None:
            result["has_ground_truth"] = True
            result["gt_class_pixel_counts"] = {
                str(c): int((gt_mask == c).sum())
                for c in range(int(self.cfg["data"]["num_classes"]))
            }
        else:
            result["has_ground_truth"] = False
        return result


def colorize_mask(mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape
    out = np.zeros((h, w, 3), dtype=np.uint8)
    for cls, color in CLASS_COLORS.items():
        out[mask == cls] = color
    return out


def render_overlay(rgb: np.ndarray, mask: np.ndarray, alpha: float = 0.45) -> np.ndarray:
    base = rgb.astype(np.float32)
    color = colorize_mask(mask).astype(np.float32)
    tumor = mask > 0
    out = base.copy()
    out[tumor] = (1 - alpha) * base[tumor] + alpha * color[tumor]
    return out.astype(np.uint8)


def png_b64(arr: np.ndarray) -> str:
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")
