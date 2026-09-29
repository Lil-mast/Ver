# VerdantMed AI

**Precision that heals — faded green, focused care.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-#A8D5BA)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-#7FB69A)](https://pytorch.org/)
[![MONAI](https://img.shields.io/badge/MONAI-1.3+-#A8D5BA)](https://monai.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-#A8D5BA)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-Apache%202.0-#7FB69A)](LICENSE)

> Medical image analysis platform for accurate detection and segmentation of pathologies (e.g. brain tumors on MRI) using state-of-the-art deep learning.

VerdantMed AI is a research-to-production pipeline for training, validating, and serving convolutional and transformer-based models on medical imaging data. It prioritises reproducibility, GPU efficiency (NVIDIA CUDA / Tensor Cores), and clinical-grade evaluation metrics.

---

## Why VerdantMed AI?

- Addresses a real clinical need: early and precise detection of tumours and other lesions.
- Built on an NVIDIA-accelerated stack (MONAI + PyTorch + CUDA).
- Supports both classification and pixel-level segmentation.
- Designed for extensibility to CT, X-ray, ultrasound, and multi-modal data.

---

## Docs

| Document | What it covers |
|----------|----------------|
| [Technical Architecture](docs/architecture.md) | Pipeline, models, imaging stack, FastAPI serving, metrics |
| [Case Study](docs/case-study.md) | Problem, audience, and product framing |

A frontend is planned; it is not part of the current scope.

---

## Tech Stack

| Component     | Technology |
|---------------|------------|
| Deep Learning | PyTorch 2.x + MONAI |
| Accelerators  | NVIDIA CUDA, cuDNN, Tensor Cores |
| Data          | BraTS, Medical Segmentation Decathlon, custom NIfTI/DICOM |
| Augmentation  | MONAI transforms + Albumentations |
| Training      | DistributedDataParallel, AMP |
| Evaluation    | MONAI metrics + clinical KPIs |
| API           | FastAPI |
| Packaging     | [uv](https://docs.astral.sh/uv/) |
| Frontend      | Coming soon |

---

## Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- NVIDIA GPU + CUDA (recommended for training)

### Environment Setup

```bash
# Install uv if needed: https://docs.astral.sh/uv/getting-started/installation/

# Create a virtual environment and install dependencies
uv venv --python 3.10
source .venv/bin/activate

# PyTorch with CUDA (adjust CUDA version as needed)
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# MONAI and medical imaging stack
uv pip install "monai[all]" nibabel pydicom scikit-image matplotlib seaborn wandb fastapi uvicorn
```

Training, evaluation, and API entrypoints will land as the project takes shape. See [Technical Architecture](docs/architecture.md) for the intended pipeline.

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
