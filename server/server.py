# server/server.py
import os
import logging
from concurrent import futures
import grpc
import joblib
import numpy as np

from protos import model_pb2, model_pb2_grpc

from grpc_reflection.v1alpha import reflection

MODEL_PATH = os.environ.get("MODEL_PATH", "/app/models/model.pkl")
MODEL_VERSION = os.environ.get("MODEL_VERSION", "v1.0.0")
SERVER_PORT = os.environ.get("PORT", "50051")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("grpc-ml-server")

class PredictionServiceServicer(model_pb2_grpc.PredictionServiceServicer):
    def __init__(self, model):
        self.model = model

    def Health(self, request, context):
        # Простой ответ
        return model_pb2.HealthResponse(status="ok", modelVersion=MODEL_VERSION)

    def Predict(self, request, context):
        try:
            features = list(request.features)
            if len(features) == 0:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Request.features is empty")
                return model_pb2.PredictResponse()

            # модель ожидает 2D-матрицу: (1, n_features)
            arr = np.array(features, dtype=float).reshape(1, -1)
            
            # # попытка получить предсказание
            # if hasattr(self.model, "predict_proba"):
            #     probs = self.model.predict_proba(arr)
            #     # !!!!!!!! бинарнуя или многоклассовую классификацию
            #     pred_idx = int(np.argmax(probs, axis=1)[0])
            #     confidence = float(np.max(probs, axis=1)[0])
            #     prediction = str(pred_idx)
            # else:
            pred = self.model.predict(arr)
            prediction = str(int(pred[0]) if hasattr(pred[0], "__int__") else str(pred[0]))
            confidence = 1.0

            return model_pb2.PredictResponse(
                prediction=prediction,
                confidence=confidence,
                modelVersion=MODEL_VERSION
            )
        except Exception as e:
            logger.exception("Prediction error")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Prediction failed: {e}")
            return model_pb2.PredictResponse()

def serve():
    if not os.path.exists(MODEL_PATH):
        logger.error("Model not found at %s", MODEL_PATH)
        raise SystemExit(1)
    logger.info("Loading model from %s", MODEL_PATH)
    model = joblib.load(MODEL_PATH)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    model_pb2_grpc.add_PredictionServiceServicer_to_server(
        PredictionServiceServicer(model), server
    )

    # Чтобы клинет без proto работал
    service_names = (
        model_pb2_grpc.PredictionServiceServicer.__name__,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, server)

    addr = f"[::]:{SERVER_PORT}"
    server.add_insecure_port(addr)
    logger.info("Starting gRPC server on %s", addr)
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
