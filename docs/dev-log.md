# Development log

Incremental build notes for the Neuro MVP sprint (Wed → Sat morning). Prefer small commits; do not land the whole app in one shot.

## Commit cadence

Aim for **at least five commits** before calling the MVP done. Each commit should leave the tree useful (installable / documented / one working vertical slice).

| # | Milestone | Status |
|---|-----------|--------|
| 1 | Project foundation: `pyproject.toml`, `.gitignore`, package stub, 2D config, README for Python 3.12 + uv | done (`e40a133`) |
| 2 | BraTS HDF5 dataset + download helper | done (`1db0a16`) |
| 3 | 2D U-Net + train / eval smoke scripts | done |
| 4 | FastAPI `/health` + `/model` + `/predict` | done |
| 5 | Thin frontend + docs polish | done |

### Synthetic data (dev fixture)

```bash
source .venv/bin/activate
python scripts/make_synthetic_brats.py
python scripts/train.py --epochs 2 --max-patients 4
python scripts/evaluate.py
```

### API

```bash
source .venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
# GET  /health  /model
# POST /predict  (multipart .h5)
# POST /predict/path?path=data/brats2020/.../volume_1_slice_31.h5
```

### Frontend

```bash
cd frontend && pnpm install && pnpm dev
# http://localhost:5173  (proxies /api → :8000)
```


Extra commits for Kaggle download wiring, bugfixes, and docs are welcome.

## Environment notes

- Recreate `.venv` with **Python 3.12** (`uv venv --python 3.12`). Do not use 3.13+ for PyTorch CUDA/CPU wheels yet.
- Skip `torchaudio` — MRI path does not need it.
- If installs fail with **Disk quota exceeded** under `/tmp`, set `TMPDIR` and `UV_CACHE_DIR` under `$HOME`.
- This workstation has **no NVIDIA GPU** → CPU torch + 2D slice training for the first demo.

## Data

Target Kaggle dataset: `awsaf49/brats2020-training-data` → `data/brats2020/` (gitignored). Prefer Kaggle MCP (`https://www.kaggle.com/mcp`); fallback: Kaggle CLI / API with `KGAT` bearer token.

**Status (2026-09-30):** Real pack downloaded via Kaggle API (~57k `volume_*_slice_*.h5` files + `BraTS20 Training Metadata.csv`). Synthetic fixture kept under `data/brats2020/_synthetic_backup/`.

After using a token in chat or configs, **rotate it** on Kaggle Settings → API.

## Related

- [Blog: Teaching the computer to see](blog/teaching-the-computer-to-see.md)
- [Architecture](architecture.md)
- [Case study](case-study.md)
- [README](../README.md)
