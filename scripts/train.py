""" Train a 2D U-Net on BraTS HDF5 slices."""

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

from neuro.config import load_config
from neuro.data import BraTSHDF5Dataset
from neuro.metrics import dice_mean
from neuro.models import build_model


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "brats2d_unet.yaml",
    )
    p.add_argument("--epochs", type=int, default=None)
    p.add_argument("--max-patients", type=int, default=None)
    p.add_argument("--device", type=str, default=None)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    cfg = load_config(args.config)
    if args.epochs is not None:
        cfg["train"]["epochs"] = args.epochs
    if args.max_patients is not None:
        cfg["data"]["max_patients"] = args.max_patients
    if args.device is not None:
        cfg["device"] = args.device

    device = torch.device(cfg["device"])
    if cfg["device"] == "cuda" and not torch.cuda.is_available():
        print("CUDA requested but unavailable — falling back to CPU")
        device = torch.device("cpu")

    torch.manual_seed(int(cfg.get("seed", 42)))

    data_root = ROOT / cfg["data"]["root"]
    train_ds = BraTSHDF5Dataset(
        data_root,
        split="train",
        val_fraction=float(cfg["data"]["val_fraction"]),
        seed=int(cfg.get("seed", 42)),
        max_patients=cfg["data"].get("max_patients"),
        image_size=int(cfg["data"]["image_size"]),
        metadata_csv=cfg["data"].get("metadata"),
    )
    val_ds = BraTSHDF5Dataset(
        data_root,
        split="val",
        val_fraction=float(cfg["data"]["val_fraction"]),
        seed=int(cfg.get("seed", 42)),
        max_patients=cfg["data"].get("max_patients"),
        image_size=int(cfg["data"]["image_size"]),
        metadata_csv=cfg["data"].get("metadata"),
    )

    train_loader = DataLoader(
        train_ds,
        batch_size=int(cfg["train"]["batch_size"]),
        shuffle=True,
        num_workers=int(cfg["data"].get("num_workers", 0)),
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=int(cfg["eval"]["batch_size"]),
        shuffle=False,
        num_workers=int(cfg["data"].get("num_workers", 0)),
    )

    model = build_model(cfg).to(device)
    opt = torch.optim.AdamW(
        model.parameters(),
        lr=float(cfg["train"]["lr"]),
        weight_decay=float(cfg["train"]["weight_decay"]),
    )
    num_classes = int(cfg["data"]["num_classes"])
    ckpt_dir = ROOT / cfg["train"]["checkpoint_dir"]
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    history: list[dict[str, float]] = []
    best_dice = -1.0

    for epoch in range(1, int(cfg["train"]["epochs"]) + 1):
        model.train()
        running_loss = 0.0
        n_batches = 0
        pbar = tqdm(train_loader, desc=f"epoch {epoch} train")
        for batch in pbar:
            images = batch["image"].to(device)
            masks = batch["mask"].to(device)
            logits = model(images)
            loss = F.cross_entropy(logits, masks)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            running_loss += float(loss.item())
            n_batches += 1
            pbar.set_postfix(loss=running_loss / n_batches)

        model.eval()
        val_loss = 0.0
        val_dice = 0.0
        n_val = 0
        with torch.no_grad():
            for batch in tqdm(val_loader, desc=f"epoch {epoch} val"):
                images = batch["image"].to(device)
                masks = batch["mask"].to(device)
                logits = model(images)
                loss = F.cross_entropy(logits, masks)
                pred = logits.argmax(dim=1)
                val_loss += float(loss.item())
                val_dice += float(dice_mean(pred, masks, num_classes).item())
                n_val += 1

        train_loss = running_loss / max(n_batches, 1)
        val_loss /= max(n_val, 1)
        val_dice /= max(n_val, 1)
        row = {
            "epoch": float(epoch),
            "train_loss": train_loss,
            "val_loss": val_loss,
            "val_dice": val_dice,
        }
        history.append(row)
        print(
            f"epoch {epoch}: train_loss={train_loss:.4f} "
            f"val_loss={val_loss:.4f} val_dice={val_dice:.4f}"
        )

        torch.save(
            {
                "model": model.state_dict(),
                "config": cfg,
                "epoch": epoch,
                "val_dice": val_dice,
            },
            ckpt_dir / "last.pt",
        )
        if val_dice >= best_dice:
            best_dice = val_dice
            torch.save(
                {
                    "model": model.state_dict(),
                    "config": cfg,
                    "epoch": epoch,
                    "val_dice": val_dice,
                },
                ckpt_dir / "best.pt",
            )

    metrics_path = ckpt_dir / "train_history.json"
    metrics_path.write_text(json.dumps(history, indent=2), encoding="utf-8")
    print(f"Best val Dice={best_dice:.4f}. Checkpoints in {ckpt_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
