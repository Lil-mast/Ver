# Teaching a computer to see tumors (so far)

*VerdantMed AI build journal — mid-sprint notes from a research-to-API MVP on BraTS MRI.*

**Precision that heals — faded green, focused care.**

---

This is not a finished product post. It is a snapshot of what we have actually shipped in the VerdantMed repo: environment, data, a 2D segmentation loop, and a FastAPI surface — before the thin UI lands.

If you want the dry checklist, see the [development log](dev-log.md). This piece is the story.

## The bet

Radiology already “sees.” The bottleneck is scale and consistency: drawing tumor subregions on multi-sequence MRI is slow and operator-dependent. VerdantMed’s first slice of product is narrower than “AI for healthcare”:

> Given one axial BraTS-style MRI slice (four channels), predict a pixel mask for tumor-related classes, and expose that result over HTTP.

We deliberately started with **2D slices** and **CPU-friendly** training. This workstation has no NVIDIA GPU. The architecture docs still dream about 3D SwinUNETR and TensorRT; the code that runs today does not.

## Day zero: the install that refused to install

The first real bug was prosaic. `uv pip install torch … torchaudio` failed because the venv was on **Python 3.13**, and the CUDA/CPU wheels we wanted only advertised ABIs through **cp312**.

Two lessons stuck:

1. Pin `requires-python = ">=3.10,<3.13"` and create the venv with **`uv venv --python 3.12`**.
2. Drop **torchaudio**. It is an audio stack. MRI does not need it, and it was the package yelling loudest about ABI tags.

Bonus landmine: extracting a large torch wheel into `/tmp` on a small tmpfs hit **disk quota**. Point `TMPDIR` and `UV_CACHE_DIR` at `$HOME` and the install sails through.

That became commit-shaped scaffolding: `pyproject.toml`, package layout under `src/verdantmed/`, a YAML config for a 2D U-Net, and a README that no longer pretends 3.13 is fine.

## How we feed the model

Public BraTS volumes are often NIfTI. The Kaggle pack we targeted — `awsaf49/brats2020-training-data` — ships **per-slice HDF5** files named like `volume_41_slice_12.h5`, plus a metadata CSV.

Each file holds:

- `image` — typically `(240, 240, 4)` float modalities  
- `mask` — on this pack, `(240, 240, 3)` **one-hot** channels (no explicit background channel)

Our `BraTSHDF5Dataset`:

- finds the live `BraTS2020_training_data/content/data` tree (and skips a `_synthetic_backup` folder we kept for smoke tests),
- splits by **patient/volume id** so slices from the same brain do not leak across train and val,
- normalizes non-zero intensities per channel,
- resizes to a small square (64² in the CPU config),
- maps one-hot masks to class ids `0..3`.

Getting the data meant authenticating to Kaggle with a **KGAT** bearer token, downloading ~7GB, unzipping ~57k slices, then deleting the zip. Auth lives outside the git repo (`~/.cursor/mcp.json` / env). Tokens pasted into chat should be rotated.

Until that download finished, we trained on a **synthetic** HDF5 fixture so the training script could be proven end-to-end. That checkpoint is still what the API loads unless you retrain — more on that honesty below.

## What “teaching it to see” means here

We are not building general computer vision. We are doing **supervised semantic segmentation**:

1. **Eyes** — a MONAI **2D U-Net**: four input channels in, four class logits per pixel out.  
2. **Teacher** — human (challenge) masks in the HDF5 files.  
3. **Lesson** — `cross_entropy(logits, mask)` with AdamW.  
4. **Report card** — mean **Dice** on validation (overlap with truth, usually ignoring background).

Training lives in `scripts/train.py`; evaluation writes a small JSON summary. Best weights go to `checkpoints/best.pt` (gitignored).

On a CPU laptop this is intentionally tiny: few patients, few epochs, small spatial size. The pipeline is real; the clinical-grade score is not — not yet.

## Serving the mask

Once a checkpoint exists, FastAPI wraps it:

| Route | Role |
|-------|------|
| `GET /health` | Process up; whether weights loaded |
| `GET /model` | Name, device, image size, val Dice from the ckpt |
| `POST /predict` | Multipart `.h5` upload → base64 PNG image / mask / overlay + class counts |
| `POST /predict/path` | Same for a server-local path (dev convenience) |

CORS is open for a local frontend. Inference reuses the same preprocess path as training so train/serve do not silently diverge.

We hit the classic ops footgun after leaving a smoke-test uvicorn running overnight: the next `uvicorn … --port 8000` failed with **Address already in use**. Kill the old PID; move on.

## What is true vs what is aspirational

**True today**

- Reproducible uv + Python 3.12 project  
- Real BraTS HDF5 on disk  
- Dataset + U-Net train/eval scripts  
- FastAPI that returns overlays from a checkpoint  

**Aspirational / next**

- Thin web UI (upload a slice, show the verdant overlay)  
- Retrain `best.pt` on a real-patient subset (still CPU) or move to CUDA  
- 3D models, DICOM ingest, experiment tracking, hardened auth — later  

The [case study](case-study.md) still frames the clinical audience; the [architecture](architecture.md) doc tracks the longer imaging roadmap. This blog is the bridge between those docs and the commits.

## Why ship in small commits

We forced a cadence: foundation → dataset → train smoke → Kaggle fixes → API, each leaving the tree runnable. That kept “finish the app” from becoming one unreviewable blob, and it left a trail you can narrate — which is this post.

## Try the path we have

```bash
uv venv --python 3.12 && source .venv/bin/activate
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
uv pip install -e .

# data already under data/brats2020/ (or scripts/download_brats.py with KAGGLE_API_TOKEN)

python scripts/train.py --epochs 2 --max-patients 4   # prefer real data root
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Then `POST /predict` with a `volume_*_slice_*.h5` file and decode the overlay PNG.

---

*Shipped next: a thin **pnpm** + Vite React frontend that makes that overlay human-visible without curl. Still ahead: a real-data retrain so the mask starts to mean something on BraTS itself.*

Related: [Architecture](architecture.md) · [Case study](case-study.md) · [Dev log](dev-log.md) · [README](../README.md)
