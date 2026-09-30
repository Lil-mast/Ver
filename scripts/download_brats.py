#!/usr/bin/env python3
"""Download BraTS 2020 training HDF5 pack from Kaggle into data/brats2020/.

Preferred: Kaggle MCP (https://www.kaggle.com/mcp) with download_dataset
  owner_slug=awsaf49  dataset_slug=brats2020-training-data

Fallback (this script): Kaggle CLI — requires ~/.kaggle/kaggle.json
  or env KAGGLE_USERNAME + KAGGLE_KEY.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


DATASET = "awsaf49/brats2020-training-data"


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

    if shutil.which("kaggle") is None:
        print(
            "kaggle CLI not found. Install with: uv pip install kaggle\n"
            "Or connect Kaggle MCP in Cursor (~/.cursor/mcp.json) and ask the "
            "agent to download awsaf49/brats2020-training-data.",
            file=sys.stderr,
        )
        return 1

    print(f"Downloading {DATASET} → {out} …")
    subprocess.run(
        [
            "kaggle",
            "datasets",
            "download",
            "-d",
            DATASET,
            "-p",
            str(out),
            "--unzip",
        ],
        check=True,
    )

    # Flatten accidental nested zips if CLI left any
    for zpath in out.glob("*.zip"):
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(out)
        zpath.unlink()

    n_h5 = len(list(out.rglob("volume_*_slice_*.h5")))
    print(f"Done. Found {n_h5} HDF5 slice files under {out}")
    if n_h5 == 0:
        print("Warning: no volume_*_slice_*.h5 files found — check unzip layout.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
