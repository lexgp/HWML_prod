# server/main.py
import os
import logging
import pickle
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time
from prometheus_client import Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

MODEL_PATH = os.getenv("MODEL_PATH", "models/model.pkl")
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0.0")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ml-rest-server")

app = FastAPI(title="ML REST API")

REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "Request latency",
    ["endpoint"]
)

class PredictRequest(BaseModel):
    features: list[float]

class PredictResponse(BaseModel):
    prediction: str
    confidence: float
    modelVersion: str

class HealthResponse(BaseModel):
    status: str
    modelVersion: str

if not os.path.exists(MODEL_PATH):
    logger.error("Model not found at %s", MODEL_PATH)
    raise SystemExit(1)

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)
logger.info("Model loaded from %s", MODEL_PATH)

@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "modelVersion": MODEL_VERSION}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    start = time.time()
    try:
        arr = np.array(req.features, dtype=float).reshape(1, -1)
        pred = model.predict(arr)

        # искусственно замедляем для проверки алерта
        time.sleep(1.5)

        prediction = str(int(pred[0]) if hasattr(pred[0], "__int__") else str(pred[0]))
        confidence = 1.0
        return {"prediction": prediction, "confidence": confidence, "modelVersion": MODEL_VERSION}
    except Exception as e:
        logger.exception("Prediction error")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")
    finally:
        REQUEST_LATENCY.labels(endpoint="/predict").observe(time.time() - start)

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
