"""Export a few anonymized BraTS slices as small, static website demos."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import h5py
import numpy as np
from PIL import Image


CASES = (
    {
        "id": "clear",
        "source": "volume_1_slice_10.h5",
        "title": "Clear reference",
        "summary": "No tumor pixels are marked in this slice’s reference label. Demo verdict: clear for this cut, so you can go grab some KFC. It still says nothing about the rest of a scan.",
        "where": "Nowhere on this slice: the reference label contains no marked tumor pixels. A clear single cut does not mean the full scan is clear.",
        "nerdy": "240 × 240 pixels · 4 MRI channels (T1, T1ce, T2, FLAIR) · 0 / 57,600 tumor-labeled pixels.",
        "has_tumor": False,
    },
    {
        "id": "tumor-a",
        "source": "volume_1_slice_68.h5",
        "title": "Tumor example A",
        "summary": "The expert reference label marks tumor tissue on this slice.",
        "where": "On the displayed slice, the labeled region sits around the center and extends toward the right side of the image. Image-orientation metadata is not included, so this view cannot reliably identify anatomical left or right.",
        "nerdy": "240 × 240 pixels · 5,040 labeled pixels (8.8%) · label centroid at x=52%, y=39% of the displayed image · 3 non-background label classes.",
        "has_tumor": True,
    },
    {
        "id": "tumor-b",
        "source": "volume_40_slice_56.h5",
        "title": "Tumor example B",
        "summary": "The expert reference label marks tumor tissue on this slice.",
        "where": "On the displayed slice, the labeled region is left of center and extends across the middle. Image-orientation metadata is not included, so this view cannot reliably identify anatomical left or right.",
        "nerdy": "240 × 240 pixels · 4,881 labeled pixels (8.5%) · label centroid at x=29%, y=53% of the displayed image · 3 non-background label classes.",
        "has_tumor": True,
    },
)

CLASS_COLORS = np.array(
    [[0, 0, 0], [180, 60, 60], [60, 140, 100], [220, 180, 60]],
    dtype=np.uint8,
)


def to_display(image: np.ndarray) -> np.ndarray:
    if image.shape[-1] < 3:
        channels = np.repeat(image[..., :1], 3, axis=-1)
    else:
        channels = image[..., :3]
    gray = channels.mean(axis=-1)
    nonzero = gray[gray > 0]
    low, high = np.percentile(nonzero, (1, 99)) if nonzero.size else (0, 1)
    if high <= low:
        high = low + 1
    gray = np.clip((gray - low) / (high - low), 0, 1)
    gray = (gray * 255).astype(np.uint8)
    return np.repeat(gray[..., None], 3, axis=-1)


def read_pair(path: Path) -> tuple[np.ndarray, np.ndarray]:
    with h5py.File(path, "r") as handle:
        image = np.asarray(handle["image"])
        raw_mask = np.asarray(handle["mask"])
    if raw_mask.ndim == 3 and raw_mask.shape[-1] <= 4:
        if raw_mask.max() <= 1:
            empty = raw_mask.sum(axis=-1) == 0
            mask = raw_mask.argmax(axis=-1).astype(np.uint8) + 1
            mask[empty] = 0
        else:
            mask = raw_mask[..., 0].astype(np.uint8)
    elif raw_mask.ndim == 2:
        # BraTS scalar labels use 4 for enhancing tumor.
        mask = raw_mask.astype(np.uint8)
        mask[mask == 4] = 3
    else:
        raise ValueError(f"Unsupported mask shape {raw_mask.shape} in {path}")
    return to_display(image), mask


def export(data_dir: Path, output_dir: Path) -> None:
    manifest = []
    for case in CASES:
        scan_path = data_dir / case["source"]
        if not scan_path.is_file():
            raise FileNotFoundError(f"Demo source not found: {scan_path}")
        folder = output_dir / case["id"]
        folder.mkdir(parents=True, exist_ok=True)
        image, labels = read_pair(scan_path)
        label_rgb = CLASS_COLORS[np.clip(labels, 0, 3)]
        overlay = image.copy()
        tumor = labels > 0
        overlay[tumor] = (
            image[tumor].astype(np.float32) * 0.55
            + label_rgb[tumor].astype(np.float32) * 0.45
        ).astype(np.uint8)

        Image.fromarray(image).save(folder / "scan.png", optimize=True)
        Image.fromarray(label_rgb).save(folder / "label.png", optimize=True)
        Image.fromarray(overlay).save(folder / "overlay.png", optimize=True)
        record = {
            **case,
            "source_dataset": "BraTS 2020",
            "label_semantics": "Expert dataset reference mask; not an AI prediction.",
            "technical": {
                "image_shape": list(labels.shape),
                "labeled_pixel_count": int(tumor.sum()),
                "labeled_pixel_percent": round(float(tumor.mean() * 100), 2),
                "labeled_region_centroid_xy_percent": (
                    [
                        round(float(np.where(tumor)[1].mean() / labels.shape[1] * 100), 1),
                        round(float(np.where(tumor)[0].mean() / labels.shape[0] * 100), 1),
                    ]
                    if tumor.any()
                    else None
                ),
                "non_background_classes": sorted(int(v) for v in np.unique(labels) if v > 0),
            },
            "images": {
                "scan": "scan.png",
                "label": "label.png",
                "overlay": "overlay.png",
            },
            "class_pixel_counts": {
                str(int(label)): int((labels == label).sum())
                for label in np.unique(labels)
            },
        }
        (folder / "case.json").write_text(
            json.dumps(record, indent=2) + "\n", encoding="utf-8"
        )
        manifest.append(record)
        print(f"Exported {case['id']}: {scan_path.name}")
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/brats2020/BraTS2020_training_data/content/data"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("frontend/public/demos"))
    args = parser.parse_args()
    export(args.data_dir, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
