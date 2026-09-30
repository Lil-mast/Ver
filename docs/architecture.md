# Technical Architecture & Implementation

How VerdantMed AI trains, evaluates, and serves medical imaging models — with a focus on computer vision, volumetric data, and clinical metrics.

---

## Goals

- End-to-end path from raw scans to deployable inference
- Reproducible experiments on multi-modal MRI (and later CT / X-ray / ultrasound)
- GPU-efficient training (AMP, multi-GPU) and production-oriented serving via FastAPI
- Clinical-grade metrics, not just generic CV scores

---

## Imaging & Data

### Modalities (initial → planned)

| Stage   | Modalities |
|---------|------------|
| Initial | Multi-modal MRI (BraTS-style: T1, T1ce, T2, FLAIR) |
| Next    | CT, X-ray, ultrasound |
| Longer  | Multi-modal fusion (imaging + clinical metadata) |

### Formats (MVP vs later)

- **MVP:** per-slice **HDF5** from Kaggle `awsaf49/brats2020-training-data` (`volume_{id}_slice_{n}.h5`, keys `image` / `mask`)
- **Later:** **NIfTI** volumes (BraTS / MSD), **DICOM** clinical ingest
- MVP trains a **2D** U-Net on axial slices (CPU-friendly). 3D volumes remain on the roadmap.

### Datasets

- BraTS 2020 training (HDF5 slices) — primary for this sprint
- Medical Segmentation Decathlon / custom NIfTI — later

### Preprocessing & Augmentation

Typical MONAI-first pipeline:

1. Load and orient volumes (canonical RAS / LPS as configured)
2. Intensity normalisation (e.g. channel-wise z-score or percentile clipping)
3. Spatial resampling / cropping to a consistent spacing and ROI
4. Train-time augmentation: flips, affine, intensity noise, contrast — via MONAI transforms (+ Albumentations where 2D-only ops help)

Inference uses deterministic transforms and sliding-window inference for large volumes that do not fit in GPU memory.

---

## Computer Vision Models

### Segmentation (pixel / voxel level)

| Architecture | Role |
|--------------|------|
| U-Net | Strong baseline for 2D/3D medical segmentation |
| SegResNet | Residual encoder–decoder; good accuracy / speed tradeoff on MRI |
| SwinUNETR | Transformer backbone for long-range context in volumes |

Outputs are typically multi-class tumor subregions (e.g. enhancing tumor, edema, necrotic core) or binary lesion masks, depending on the task config.

### Classification

- EfficientNet-family (and similar) classifiers for study- or patch-level labels (presence of pathology, triage priority, etc.)
- Can sit alongside segmentation (e.g. classify study → segment ROI)

### Training characteristics

- Mixed precision (AMP) for Tensor Core utilisation
- Multi-GPU via `DistributedDataParallel` when available
- Loss mixtures common in medical CV: Dice + Cross-Entropy / Focal, optionally boundary-aware terms
- Experiment tracking ready for Weights & Biases / MLflow

### Export & acceleration

- ONNX export for portable inference
- TensorRT (or similar) as an optional optimisation path on NVIDIA GPUs
- Serving layer remains FastAPI regardless of runtime backend

---

## Pipeline Stages

```
Data loading → Preprocessing → Training → Evaluation → Inference → API
```

| Stage | Responsibility |
|-------|------------------|
| Data loading | Dataset adapters, caching, multi-modal channel stacking |
| Preprocessing | Spatial + intensity transforms; train vs val/test splits |
| Training | Config-driven loops, checkpoints, logging |
| Evaluation | Hold-out / cross-val metrics; failure-case review |
| Inference | Sliding window, post-processing (connected components, thresholding) |
| API | FastAPI endpoints for predict / health / model metadata |

Configs (Hydra / YAML) will drive datasets, model choice, and hyperparameters so experiments stay reproducible.

---

## Evaluation Metrics

Medical segmentation needs overlap **and** boundary quality:

| Metric | Why it matters clinically |
|--------|---------------------------|
| Dice coefficient | Overlap between prediction and ground truth |
| Hausdorff Distance (e.g. HD95) | Boundary outliers; sensitive to distant false positives |
| Sensitivity / Specificity | Detection vs over-call tradeoff |
| Volume error | Absolute / relative lesion volume agreement |

Classification tasks add standard AUROC / F1 / calibration where relevant. Custom clinical KPIs can be layered on top of MONAI metrics.

---

## Serving (FastAPI)

The application API is **FastAPI** (+ Uvicorn):

- Accept scan uploads or paths (NIfTI / DICOM-derived volumes)
- Run preprocessing + model inference on GPU when available
- Return masks, overlays metadata, and scalar metrics / confidence
- Health and model-info routes for ops

A web frontend will consume this API later; it is intentionally out of scope for the first backend slice.

Optional later: TorchServe / Triton behind the same FastAPI façade for high-throughput batch serving.

---

## Tooling

| Concern | Choice |
|---------|--------|
| Environment & installs | [uv](https://docs.astral.sh/uv/) |
| DL framework | PyTorch 2.x |
| Medical CV | MONAI |
| API | FastAPI |
| Tracking | W&B / MLflow (pluggable) |

---

## Design Principles

1. **Reproducibility** — pinned envs via uv, config-first experiments, seeded runs
2. **GPU efficiency** — AMP, sensible batch / window sizes, avoid unnecessary host–device copies
3. **Clinical metrics first** — Dice/HD95 and related KPIs as first-class evaluation, not afterthoughts
4. **Extensible modalities** — shared transforms and model registry so CT/X-ray paths reuse the same skeleton
5. **API before UI** — solid FastAPI contract first; frontend follows

---

## Related

- [Case Study](case-study.md) — problem framing and audience
- [README](../README.md) — overview and quick start
