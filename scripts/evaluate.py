"""Evaluate a checkpoint on the BraTS HDF5 val split."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from verdantmed.config import load_config
from verdantmed.data import BraTSHDF5Dataset
from verdantmed.metrics import dice_mean, dice_per_class
from verdantmed.models import build_model


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=ROOT / "configs" / "brats2d_unet.yaml")
    p.add_argument("--checkpoint", type=Path, default=ROOT / "checkpoints" / "best.pt")
    p.add_argument("--device", type=str, default=None)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    cfg = load_config(args.config)
    if args.device:
        cfg["device"] = args.device

    device = torch.device(cfg["device"])
    if cfg["device"] == "cuda" and not torch.cuda.is_available():
        device = torch.device("cpu")

    ckpt = torch.load(args.checkpoint, map_location=device, weights_only=False)
    if "config" in ckpt:
        # Keep data paths from CLI config; prefer checkpoint model hyperparams
        saved = ckpt["config"]
        cfg["model"] = saved.get("model", cfg["model"])
        cfg["data"]["num_classes"] = saved.get("data", {}).get(
            "num_classes", cfg["data"]["num_classes"]
        )

    model = build_model(cfg).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()

    data_root = ROOT / cfg["data"]["root"]
    val_ds = BraTSHDF5Dataset(
        data_root,
        split="val",
        val_fraction=float(cfg["data"]["val_fraction"]),
        seed=int(cfg.get("seed", 42)),
        max_patients=cfg["data"].get("max_patients"),
        image_size=int(cfg["data"]["image_size"]),
    )
    loader = DataLoader(
        val_ds,
        batch_size=int(cfg["eval"]["batch_size"]),
        shuffle=False,
        num_workers=0,
    )
    num_classes = int(cfg["data"]["num_classes"])

    total_loss = 0.0
    total_dice = 0.0
    class_dice_sum = None
    n = 0
    with torch.no_grad():
        for batch in tqdm(loader, desc="evaluate"):
            images = batch["image"].to(device)
            masks = batch["mask"].to(device)
            logits = model(images)
            loss = F.cross_entropy(logits, masks)
            pred = logits.argmax(dim=1)
            dpc = dice_per_class(pred, masks, num_classes)
            total_loss += float(loss.item())
            total_dice += float(dice_mean(pred, masks, num_classes).item())
            class_dice_sum = dpc if class_dice_sum is None else class_dice_sum + dpc
            n += 1

    summary = {
        "checkpoint": str(args.checkpoint),
        "num_batches": n,
        "val_loss": total_loss / max(n, 1),
        "val_dice_mean": total_dice / max(n, 1),
        "val_dice_per_class_excl_bg": (
            (class_dice_sum / max(n, 1)).tolist() if class_dice_sum is not None else []
        ),
    }
    out = ROOT / "checkpoints" / "eval_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
