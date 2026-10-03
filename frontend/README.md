# Neuro frontend

Thin Vite + React UI for BraTS slice upload and segmentation overlays.

```bash
# API (repo root)
source .venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# UI
cd frontend
pnpm install
pnpm dev
```

Open http://localhost:5173 — Vite proxies `/api` → `http://127.0.0.1:8000`.
