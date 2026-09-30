#!/usr/bin/env python3
"""Download BraTS 2020 training HDF5 pack from Kaggle into data/brats2020/.

Preferred: Kaggle MCP (https://www.kaggle.com/mcp) with download_dataset
  owner_slug=awsaf49  dataset_slug=brats2020-training-data

Fallback (this script):
  export KAGGLE_API_TOKEN=KGAT_...   # bearer token from Kaggle Settings → API
  python scripts/download_brats.py

Or classic ~/.kaggle/kaggle.json + `kaggle` CLI.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen


DATASET = "awsaf49/brats2020-training-data"
DOWNLOAD_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/awsaf49/brats2020-training-data"
)


def download_with_token(out: Path, token: str) -> None:
    zip_path = out / "brats2020-training-data.zip"
    print(f"Downloading {DATASET} with KGAT token → {zip_path} …")
    req = Request(DOWNLOAD_URL, headers={"Authorization": f"Bearer {token}"})
    with urlopen(req) as resp:
        # urlopen follows redirects by default for http.client in recent Python
        total = 0
        with zip_path.open("wb") as f:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                total += len(chunk)
                if total % (64 * 1024 * 1024) < 1024 * 1024:
                    print(f"  … {total / 1e9:.2f} GB", flush=True)
    print("Extracting …")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(out)
    zip_path.unlink(missing_ok=True)


def download_with_cli(out: Path) -> None:
    if shutil.which("kaggle") is None:
        raise RuntimeError(
            "kaggle CLI not found. Install with: uv pip install kaggle\n"
            "Or set KAGGLE_API_TOKEN=KGAT_... and re-run."
        )
    print(f"Downloading {DATASET} via kaggle CLI → {out} …")
    subprocess.run(
        ["kaggle", "datasets", "download", "-d", DATASET, "-p", str(out), "--unzip"],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/brats2020"),
        help="Output directory (default: data/brats2020)",
    )
    args = parser.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    token = os.environ.get("KAGGLE_API_TOKEN") or os.environ.get("KAGGLE_KEY")
    try:
        if token and str(token).startswith("KGAT"):
            download_with_token(out, str(token))
        else:
            download_with_cli(out)
    except Exception as exc:  # noqa: BLE001
        print(f"Download failed: {exc}", file=sys.stderr)
        return 1

    for zpath in out.glob("*.zip"):
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(out)
        zpath.unlink()

    n_real = len(
        [
            p
            for p in out.rglob("volume_*_slice_*.h5")
            if "_synthetic_backup" not in p.parts
        ]
    )
    print(f"Done. Found {n_real} real HDF5 slices under {out}")
    if n_real == 0:
        print("Warning: no volume_*_slice_*.h5 files found.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
