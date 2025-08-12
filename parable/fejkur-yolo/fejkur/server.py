from __future__ import annotations

import os
import pathlib
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from ultralytics import YOLO


APP_ROOT = pathlib.Path(__file__).resolve().parent.parent
MODELS_DIR = APP_ROOT / "models"
DEFAULT_MODEL_PATH = MODELS_DIR / "yolo11n.pt"
RUNS_DETECT_DIR = APP_ROOT / "runs" / "detect"


class DetectRequest(BaseModel):
    source_path: str = Field(..., description="Absolute path to an image or video file")
    conf: Optional[float] = Field(0.5, ge=0.0, le=1.0)
    save_txt: bool = True
    save_conf: bool = True


class DetectResponse(BaseModel):
    humansDetected: bool
    humansCount: int
    saveDir: Optional[str]


app = FastAPI(title="Fejkur YOLO Service", version="0.1.0")


_model: Optional[YOLO] = None


def _ensure_model_loaded() -> YOLO:
    global _model
    if _model is None:
        model_path = os.getenv("FEJKUR_YOLO_MODEL", str(DEFAULT_MODEL_PATH))
        _model = YOLO(model_path)
    return _model


@app.post("/detect", response_model=DetectResponse)
def detect(req: DetectRequest) -> DetectResponse:
    model = _ensure_model_loaded()

    source_path = req.source_path
    if not os.path.isabs(source_path):
        # Allow relative to repo root if not absolute
        source_path = str((APP_ROOT.parent / source_path).resolve())

    if not os.path.exists(source_path):
        raise HTTPException(
            status_code=400, detail=f"Source path not found: {source_path}"
        )

    # Run prediction, saving labels for compatibility with existing TS logic if needed
    results = model.predict(
        source=source_path,
        conf=req.conf or 0.5,
        save_txt=req.save_txt,
        save_conf=req.save_conf,
        project=str(RUNS_DETECT_DIR),
        name="predict",
        exist_ok=True,
        verbose=False,
    )

    # Count humans (class id 0 per COCO) directly from results to avoid filesystem reads
    humans_count = 0
    if results:
        first = results[0]
        try:
            classes = first.boxes.cls.tolist() if first.boxes is not None else []
            humans_count = sum(1 for c in classes if int(c) == 0)
        except Exception:
            humans_count = 0

        save_dir = str(first.save_dir) if getattr(first, "save_dir", None) else None
    else:
        save_dir = None

    return DetectResponse(
        humansDetected=humans_count > 0,
        humansCount=humans_count,
        saveDir=save_dir,
    )


def main() -> None:
    import uvicorn

    uvicorn.run(
        "fejkur.server:app",
        host=os.getenv("FEJKUR_HOST", "127.0.0.1"),
        port=int(os.getenv("FEJKUR_PORT", "8001")),
        reload=False,
        workers=1,
    )


if __name__ == "__main__":
    main()
