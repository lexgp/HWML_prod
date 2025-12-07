# Запуск:
# python -m client.client

import os
import grpc
from protos import model_pb2, model_pb2_grpc

SERVER = os.environ.get("SERVER", "localhost:50051")
TIMEOUT = 5  # seconds

def do_health(stub):
    req = model_pb2.HealthRequest()
    return stub.Health(req, timeout=TIMEOUT)

def do_predict(stub, features):
    req = model_pb2.PredictRequest(features=features)
    return stub.Predict(req, timeout=TIMEOUT)

def main():
    with grpc.insecure_channel(SERVER) as channel:
        stub = model_pb2_grpc.PredictionServiceStub(channel)
        try:
            health = do_health(stub)
            print("Health:", {"status": health.status, "modelVersion": health.modelVersion})
        except Exception as e:
            print("Health call failed:", e)
            return

        sample_features = [ -0.5, -0.09, -1.52, 0.40, -0.62 ]
        try:
            resp = do_predict(stub, sample_features)
            print("Predict:", {
                "prediction": resp.prediction,
                "confidence": resp.confidence,
                "modelVersion": resp.modelVersion
            })
        except Exception as e:
            print("Predict call failed:", e)

if __name__ == "__main__":
    main()
