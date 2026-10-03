"""Neuro FastAPI service — health, model info, and slice prediction."""

from __future__ import annotations

import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from neuro.config import project_root
from neuro.inference import SegmentationService

ROOT = project_root()
service = SegmentationService()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        service.load()
    except FileNotFoundError as exc:
        # Allow boot without weights; /predict will error clearly
        print(f"Warning: {exc}")
    yield


app = FastAPI(
    title="Neuro",
    description="2D BraTS slice segmentation API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str


class ModelResponse(BaseModel):
    name: str
    checkpoint: str
    loaded: bool
    device: str
    image_size: int
    num_classes: int
    in_channels: int
    out_channels: int
    epoch: int | None = None
    val_dice: float | None = None


class PredictResponse(BaseModel):
    source: str
    image_size: list[int]
    class_pixel_counts: dict[str, int]
    has_ground_truth: bool
    gt_class_pixel_counts: dict[str, int] | None = None
    image_png_base64: str = Field(description="Grayscale MRI slice as PNG base64")
    mask_png_base64: str = Field(description="Colorized predicted mask PNG base64")
    overlay_png_base64: str = Field(description="MRI + mask overlay PNG base64")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=bool(service.meta.get("loaded")),
        device=str(service.meta.get("device", service.device)),
    )


@app.get("/model", response_model=ModelResponse)
def model_info() -> ModelResponse:
    m = service.meta
    model_cfg: dict[str, Any] = m.get("model") or {}
    return ModelResponse(
        name=str(model_cfg.get("name", "unet2d")),
        checkpoint=str(m.get("checkpoint", "")),
        loaded=bool(m.get("loaded")),
        device=str(m.get("device", "")),
        image_size=int(m.get("image_size", 0)),
        num_classes=int(m.get("num_classes", 0)),
        in_channels=int(model_cfg.get("in_channels", 4)),
        out_channels=int(model_cfg.get("out_channels", 4)),
        epoch=m.get("epoch"),
        val_dice=m.get("val_dice"),
    )


@app.post("/predict", response_model=PredictResponse)
async def predict(
    file: UploadFile = File(..., description="BraTS HDF5 slice (volume_*_slice_*.h5)"),
) -> PredictResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".h5", ".hdf5"}:
        raise HTTPException(
            status_code=400,
            detail="Upload a .h5 / .hdf5 BraTS slice file",
        )

    try:
        service.load()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty upload")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        tmp.write(raw)
        tmp.flush()
        try:
            result = service.predict_h5(Path(tmp.name))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"Inference failed: {exc}") from exc

    result["source"] = file.filename
    return PredictResponse(**result)


@app.post("/predict/path", response_model=PredictResponse)
def predict_path(
    path: str = Query(..., description="Server-local path to a .h5 slice"),
) -> PredictResponse:
    """Predict from a server-local HDF5 path (dev convenience)."""
    p = Path(path)
    if not p.is_file():
        alt = ROOT / path
        if alt.is_file():
            p = alt
        else:
            raise HTTPException(status_code=404, detail=f"File not found: {path}")
    try:
        service.load()
        result = service.predict_h5(p)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Inference failed: {exc}") from exc
    return PredictResponse(**result)
