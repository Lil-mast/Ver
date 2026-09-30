"""BraTS 2020 HDF5 slice dataset (awsaf49/brats2020-training-data)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

# Official BraTS labels contiguous class indices for CrossEntropy
BRATS_LABEL_MAP = {0: 0, 1: 1, 2: 2, 4: 3}


def remap_brats_labels(mask: np.ndarray) -> np.ndarray:
    """Map BraTS labels {0,1,2,4} to {0,1,2,3}. Unknown labels become background."""
    out = np.zeros_like(mask, dtype=np.int64)
    for src, dst in BRATS_LABEL_MAP.items():
        out[mask == src] = dst
    return out


def find_data_dir(root: Path) -> Path:
    """Locate the directory that contains volume_*_slice_*.h5 files."""
    root = root.resolve()
    if any(root.glob("volume_*_slice_*.h5")):
        return root
    candidates = sorted(root.rglob("volume_*_slice_*.h5"))
    if not candidates:
        raise FileNotFoundError(
            f"No volume_*_slice_*.h5 files under {root}. "
            "Download awsaf49/brats2020-training-data into data/brats2020/."
        )
    return candidates[0].parent


def find_metadata_csv(root: Path) -> Path | None:
    for name in (
        "BraTS20 Training Metadata.csv",
        "BraTS20_Training_Metadata.csv",
        "metadata.csv",
    ):
        direct = root / name
        if direct.is_file():
            return direct
        matches = list(root.rglob(name))
        if matches:
            return matches[0]
    return None


def _load_h5_pair(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Return image (C,H,W) float32 and mask (H,W) int64."""
    with h5py.File(path, "r") as f:
        keys = set(f.keys())
        if "image" in keys:
            image = np.asarray(f["image"])
        elif "images" in keys:
            image = np.asarray(f["images"])
        else:
            raise KeyError(f"{path}: expected 'image' key, found {sorted(keys)}")

        if "mask" in keys:
            mask = np.asarray(f["mask"])
        elif "masks" in keys:
            mask = np.asarray(f["masks"])
        else:
            raise KeyError(f"{path}: expected 'mask' key, found {sorted(keys)}")

    # image: (H,W,C) or (C,H,W)
    if image.ndim != 3:
        raise ValueError(f"{path}: image shape {image.shape}, expected 3D")
    if image.shape[0] in (1, 3, 4) and image.shape[-1] not in (1, 3, 4):
        pass  # already CHW-ish
    elif image.shape[-1] in (1, 3, 4):
        image = np.transpose(image, (2, 0, 1))
    else:
        # Prefer channels-last if last dim is smallest
        if image.shape[-1] < image.shape[0]:
            image = np.transpose(image, (2, 0, 1))

    # mask: (H,W), (H,W,C) one-hot, or (C,H,W)
    if mask.ndim == 3:
        if mask.shape[-1] <= 4 and mask.shape[0] > 4:
            # one-hot HWC → class map; if multi-label one-hot of WT/TC/ET, take argmax+1
            if mask.max() <= 1:
                # background where all zero
                cls = mask.argmax(axis=-1).astype(np.int64)
                empty = mask.sum(axis=-1) == 0
                cls[empty] = 0
                # shift if classes were 0..K-1 without explicit bg channel
                mask = cls
            else:
                mask = mask[..., 0]
        elif mask.shape[0] <= 4:
            if mask.max() <= 1:
                cls = mask.argmax(axis=0).astype(np.int64)
                empty = mask.sum(axis=0) == 0
                cls[empty] = 0
                mask = cls
            else:
                mask = mask[0]
        else:
            mask = mask[..., 0] if mask.shape[-1] < mask.shape[0] else mask[0]

    image = image.astype(np.float32)
    mask = remap_brats_labels(mask.astype(np.int64))
    return image, mask


def _normalize_per_channel(image: np.ndarray) -> np.ndarray:
    out = image.copy()
    for c in range(out.shape[0]):
        ch = out[c]
        nonzero = ch[ch > 0]
        if nonzero.size == 0:
            continue
        mean = nonzero.mean()
        std = nonzero.std()
        if std < 1e-6:
            std = 1.0
        out[c] = (ch - mean) / std
    return out


def _resize_hw(
    image: np.ndarray, mask: np.ndarray, size: int
) -> tuple[np.ndarray, np.ndarray]:
    """Nearest resize to (size, size) without adding heavy deps beyond torch."""
    img_t = torch.from_numpy(image).unsqueeze(0)  # 1,C,H,W
    msk_t = torch.from_numpy(mask).unsqueeze(0).unsqueeze(0).float()  # 1,1,H,W
    img_t = torch.nn.functional.interpolate(
        img_t, size=(size, size), mode="bilinear", align_corners=False
    )
    msk_t = torch.nn.functional.interpolate(msk_t, size=(size, size), mode="nearest")
    return img_t.squeeze(0).numpy(), msk_t.squeeze(0).squeeze(0).long().numpy()


class BraTSHDF5Dataset(Dataset):
    """2D BraTS slices from per-slice HDF5 files."""

    def __init__(
        self,
        root: str | Path,
        *,
        split: str = "train",
        val_fraction: float = 0.2,
        seed: int = 42,
        max_patients: int | None = None,
        image_size: int = 128,
        transform: Any | None = None,
        metadata_csv: str | Path | None = None,
    ) -> None:
        self.root = Path(root)
        self.data_dir = find_data_dir(self.root)
        self.image_size = image_size
        self.transform = transform
        self.split = split

        files = sorted(self.data_dir.glob("volume_*_slice_*.h5"))
        if not files:
            raise FileNotFoundError(f"No HDF5 slices in {self.data_dir}")

        # Group by volume / patient id
        by_volume: dict[int, list[Path]] = {}
        for path in files:
            # volume_{id}_slice_{n}.h5
            stem = path.stem  # volume_41_slice_0
            parts = stem.split("_")
            try:
                vol_idx = parts.index("volume")
                volume_id = int(parts[vol_idx + 1])
            except (ValueError, IndexError) as exc:
                raise ValueError(f"Unexpected filename: {path.name}") from exc
            by_volume.setdefault(volume_id, []).append(path)

        volume_ids = sorted(by_volume.keys())
        rng = np.random.default_rng(seed)
        rng.shuffle(volume_ids)

        if max_patients is not None:
            volume_ids = volume_ids[: max(1, int(max_patients))]

        n_val = max(1, int(round(len(volume_ids) * val_fraction))) if len(volume_ids) > 1 else 0
        val_ids = set(volume_ids[:n_val])
        train_ids = set(volume_ids[n_val:]) if n_val < len(volume_ids) else set(volume_ids)

        chosen = train_ids if split == "train" else val_ids
        if not chosen and split == "val":
            # tiny subset: reuse last patient for val
            chosen = {volume_ids[-1]}

        self.paths: list[Path] = []
        for vid in sorted(chosen):
            self.paths.extend(sorted(by_volume[vid]))

        # Optional metadata presence check (not required for indexing)
        meta_path = Path(metadata_csv) if metadata_csv else find_metadata_csv(self.root)
        self.metadata: pd.DataFrame | None = None
        if meta_path and meta_path.is_file():
            self.metadata = pd.read_csv(meta_path)

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor | str]:
        path = self.paths[index]
        image, mask = _load_h5_pair(path)
        image = _normalize_per_channel(image)

        # Ensure 4 channels (pad or crop)
        c = image.shape[0]
        if c < 4:
            pad = np.zeros((4 - c, image.shape[1], image.shape[2]), dtype=np.float32)
            image = np.concatenate([image, pad], axis=0)
        elif c > 4:
            image = image[:4]

        if self.image_size:
            image, mask = _resize_hw(image, mask, self.image_size)

        sample = {
            "image": torch.from_numpy(image.copy()),
            "mask": torch.from_numpy(mask.copy()).long(),
            "path": str(path),
        }
        if self.transform is not None:
            sample = self.transform(sample)
        return sample
