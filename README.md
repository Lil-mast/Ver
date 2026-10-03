# VerdantMed AI

**Precision that heals — faded green, focused care.**

[![Python 3.10–3.12](https://img.shields.io/badge/python-3.10%E2%80%933.12-#A8D5BA)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-#7FB69A)](https://pytorch.org/)
[![MONAI](https://img.shields.io/badge/MONAI-1.3+-#A8D5BA)](https://monai.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-#A8D5BA)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-Apache%202.0-#7FB69A)](LICENSE)

> Medical image analysis platform for accurate detection and segmentation of pathologies (e.g. brain tumors on MRI) using state-of-the-art deep learning.

VerdantMed AI is a research-to-production pipeline for training, validating, and serving models on medical imaging data. The current MVP targets **2D BraTS slice segmentation** (HDF5) with FastAPI serving and a thin frontend next.

---

## Why VerdantMed AI?

- Addresses a real clinical need: early and precise detection of tumours and other lesions.
- Built on MONAI + PyTorch (CPU today; CUDA when a GPU is available).
- Supports pixel-level segmentation; classification and more modalities later.
- Designed for extensibility to CT, X-ray, ultrasound, and multi-modal data.

---

## Docs

| Document | What it covers |
|----------|----------------|
| [Technical Architecture](docs/architecture.md) | Pipeline, models, imaging stack, FastAPI serving, metrics |
| [Case Study](docs/case-study.md) | Problem, audience, and product framing |
| [OR comparison](docs/or-comparison.md) | Manual vs AI outline in a normal OR (simple Mermaid) |
| [Development log](docs/dev-log.md) | Sprint notes and incremental milestones |
| [Blog: Teaching the computer to see](docs/blog/teaching-the-computer-to-see.md) | Narrative of what we have built so far |
| [Demo guide](docs/demo-guide.md) | Which `.h5` scans show tumor vs clear |

---

## Tech Stack

| Component     | Technology |
|---------------|------------|
| Deep Learning | PyTorch 2.x + MONAI |
| Data (MVP)    | BraTS 2020 HDF5 slices (`awsaf49/brats2020-training-data`) |
| Training      | 2D U-Net, CPU-friendly subset configs |
| API           | FastAPI |
| Packaging     | [uv](https://docs.astral.sh/uv/) |
| Frontend      | Vite + React (**pnpm**), upload / overlay UI |

**Python:** `>=3.10,<3.13`. PyTorch wheels do not support 3.13+ yet — use **3.12**.

---

## Quick Start

### Prerequisites

- Python **3.12** (recommended) via [uv](https://docs.astral.sh/uv/)
- BraTS 2020 training data under `data/brats2020/` (see [dev log](docs/dev-log.md))

### Environment Setup

```bash
# Create venv on 3.12 (not 3.13+)
uv venv --python 3.12
source .venv/bin/activate

# If /tmp is small, point temp/cache at home before large installs:
# export TMPDIR=$HOME/.cache/uv-tmp UV_CACHE_DIR=$HOME/.cache/uv

# CPU torch (default on this machine). Omit torchaudio — not needed for MRI.
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Project + medical stack
uv pip install -e .

# On a CUDA machine instead:
# uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

Training / API entrypoints land in later commits this sprint.

### Smoke train (synthetic until Kaggle data is present)

```bash
source .venv/bin/activate
python scripts/make_synthetic_brats.py   # tiny HDF5 fixture
python scripts/train.py --epochs 2 --max-patients 4
python scripts/evaluate.py               # writes checkpoints/eval_summary.json
```

Real data: download `awsaf49/brats2020-training-data` into `data/brats2020/` (Kaggle MCP or `python scripts/download_brats.py`).

### API

```bash
source .venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

- `GET /health` — liveness + whether weights loaded  
- `GET /model` — architecture / checkpoint metadata  
- `POST /predict` — multipart upload of a `.h5` slice → PNG overlays (base64) + class counts  
- `POST /predict/path?path=...` — same for a server-local path (dev)

### Frontend

```bash
# Terminal A — API
source .venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal B — UI (pnpm)
cd frontend
pnpm install
pnpm dev
```

Open http://localhost:5173 — drop a `volume_*_slice_*.h5` file and run segmentation.

## License

Apache 2.0 — see [LICENSE](LICENSE).
