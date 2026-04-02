import base64
import io
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image, UnidentifiedImageError

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)
MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_BYTES", "10485760"))
BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from gradcam import GradCAM
from model import SkinLesionModel


def parse_origins() -> List[str]:
    origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    return [origin.strip() for origin in origins_env.split(",") if origin.strip()]


def pil_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


class PredictResponse(BaseModel):
    probability: float = Field(..., ge=0.0, le=1.0)
    label: str
    gradcam: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = os.getenv("MODEL_PATH", str(BASE_DIR / "best_model.pth"))
    logger.info("Loading model from %s", model_path)

    model_service = SkinLesionModel(model_path)
    gradcam_service = GradCAM(model_service.model)

    app.state.model_service = model_service
    app.state.gradcam_service = gradcam_service
    logger.info("Model and Grad-CAM initialized")

    try:
        yield
    finally:
        gradcam_service.close()
        logger.info("Grad-CAM hooks cleaned up")


app = FastAPI(
    title="Skin Lesion Inference API",
    description="FastAPI backend for EfficientNet-B4 skin lesion classification",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_origins(),
    allow_origin_regex=os.getenv("CORS_ORIGIN_REGEX", r"https://.*\.vercel\.app"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict:
    model_loaded = hasattr(app.state, "model_service") and hasattr(app.state, "gradcam_service")
    return {"status": "ok", "model_loaded": model_loaded}


@app.get("/ping")
def ping() -> dict:
    return {"message": "pong"}


@app.post("/predict", response_model=PredictResponse)
async def predict(image: UploadFile = File(...)) -> PredictResponse:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are supported.")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large.")

    try:
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="Invalid image file.") from exc

    try:
        model_service: SkinLesionModel = app.state.model_service
        gradcam_service: GradCAM = app.state.gradcam_service

        input_tensor = model_service.preprocess(pil_image)
        probability = model_service.predict_proba(input_tensor)
        label = "malignant" if probability > 0.5 else "benign"

        overlay_image = gradcam_service.generate(input_tensor, pil_image)
        gradcam_base64 = pil_to_base64(overlay_image)
    except Exception as exc:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail="Prediction failed.") from exc

    return PredictResponse(probability=probability, label=label, gradcam=gradcam_base64)
