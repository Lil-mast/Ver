"""Create a tiny synthetic BraTS-like HDF5 pack for CPU smoke tests."""

from __future__ import annotations

import argparse
from pathlib import Path

import h5py
import numpy as np


def write_slice(path: Path, volume: int, slice_idx: int, size: int = 64) -> None:
    rng = np.random.default_rng(volume * 1000 + slice_idx)
    image = rng.normal(0.0, 0.3, size=(size, size, 4)).astype(np.float32)
    # Soft “brain” disk
    yy, xx = np.ogrid[:size, :size]
    cy, cx = size // 2, size // 2
    brain = (yy - cy) ** 2 + (xx - cx) ** 2 < (size * 0.35) ** 2
    image[brain] += 1.0

    mask = np.zeros((size, size), dtype=np.uint8)
    # Tumor blob with BraTS-style labels 1,2,4
    ty, tx = cy - size // 8, cx + size // 10
    core = (yy - ty) ** 2 + (xx - tx) ** 2 < (size * 0.08) ** 2
    edema = (yy - ty) ** 2 + (xx - tx) ** 2 < (size * 0.14) ** 2
    enh = (yy - ty) ** 2 + (xx - tx) ** 2 < (size * 0.05) ** 2
    mask[edema] = 2
    mask[core] = 1
    mask[enh] = 4

    path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(path, "w") as f:
        f.create_dataset("image", data=image, compression="gzip")
        f.create_dataset("mask", data=mask, compression="gzip")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/brats2020/BraTS2020_training_data/content/data"),
    )
    parser.add_argument("--patients", type=int, default=4)
    parser.add_argument("--slices", type=int, default=8)
    parser.add_argument("--size", type=int, default=64)
    args = parser.parse_args()

    n = 0
    for vol in range(1, args.patients + 1):
        for s in range(args.slices):
            path = args.out / f"volume_{vol}_slice_{s}.h5"
            write_slice(path, vol, s, size=args.size)
            n += 1

    # Default layout mirrors Kaggle: .../brats2020/BraTS2020_training_data/content/data
    brats_root = args.out
    for _ in range(3):
        brats_root = brats_root.parent
    meta = brats_root / "BraTS20 Training Metadata.csv"
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text("volume_no,slice_no,target\n", encoding="utf-8")
    print(f"Wrote {n} synthetic HDF5 slices under {args.out}")
    print(f"Metadata stub: {meta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
