"""
FastAPI Microservice for Student Dropout-Risk Prediction.
Fulfills Assignment Part 2 Requirements:
- Serves predictions through RESTful API endpoints.
- Validates inputs using Pydantic schemas.
- Incorporates latency tracking and audit telemetry.
- Provides real-time explanation triggers and drift detection endpoints.
"""

import json
import time
from pathlib import Path
import sys
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(str(Path(__file__).resolve().parent.parent))
from api.schemas import BatchPredictionRequest, BatchPredictionResponse, PredictionResponse, StudentFeatures
from config import MODELS_DIR
from mlops.drift_monitor import run_drift_analysis

app = FastAPI(
    title="Student Dropout-Risk Prediction Microservice",
    description="Production-grade inference service for early academic risk identification and intervention.",
    version="1.0.0",
)

# Enable CORS for Streamlit / Frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model state
MODEL = None
PREPROCESSOR = None
MODEL_METADATA = {}


@app.on_event("startup")
def load_artifacts():
    global MODEL, PREPROCESSOR, MODEL_METADATA
    champion_path = MODELS_DIR / "champion_model.joblib"
    preprocessor_path = MODELS_DIR / "feature_preprocessor.joblib"
    registry_path = MODELS_DIR / "model_registry.json"

    if not champion_path.exists() or not preprocessor_path.exists():
        raise RuntimeError(f"Model artifacts not found in {MODELS_DIR}. Run ML training pipeline first.")

    MODEL = joblib.load(champion_path)
    PREPROCESSOR = joblib.load(preprocessor_path)

    if registry_path.exists():
        with open(registry_path, "r") as f:
            MODEL_METADATA = json.load(f)

    print(f"[OK] Loaded Champion Model: {MODEL_METADATA.get('champion_model_name', 'Unknown')}")


def evaluate_risk_triggers(student: StudentFeatures) -> list:
    """Generates human-interpretable risk flags for academic advisors."""
    triggers = []
    if student.attendance_percentage < 75.0:
        triggers.append(f"Low Attendance ({student.attendance_percentage:.1f}% < 75%)")
    if student.average_internal_marks < 50.0:
        triggers.append(f"Failing Internal Marks ({student.average_internal_marks:.1f}/100)")
    if student.assignment_completion_rate < 70.0:
        triggers.append(f"Low Assignment Completion ({student.assignment_completion_rate:.1f}%)")
    if student.failures > 0:
        triggers.append(f"Past Academic Failures ({student.failures} recorded)")
    if student.avg_weekly_learning_hours < 4.0:
        triggers.append(f"Low Digital LMS Engagement ({student.avg_weekly_learning_hours:.1f} hrs/wk)")
    if not triggers:
        triggers.append("No critical risk factors detected (Metrics on track)")
    return triggers


@app.get("/", tags=["General"])
def root():
    return {
        "service": "Student Performance & Dropout Risk Prediction API",
        "status": "Online",
        "docs_url": "/docs",
        "champion_model": MODEL_METADATA.get("champion_model_name", "Registered Champion"),
    }


@app.get("/health", tags=["Monitoring"])
def health_check():
    return {
        "status": "HEALTHY",
        "model_loaded": MODEL is not None,
        "preprocessor_loaded": PREPROCESSOR is not None,
        "champion_model": MODEL_METADATA.get("champion_model_name"),
        "timestamp": time.time(),
    }


@app.get("/model-info", tags=["Monitoring"])
def model_info():
    if not MODEL_METADATA:
        raise HTTPException(status_code=404, detail="Model metadata unavailable.")
    return MODEL_METADATA


@app.post("/predict", response_model=PredictionResponse, tags=["Inference"])
def predict_single(student: StudentFeatures):
    start_time = time.perf_counter()

    try:
        # Prepare single row DataFrame
        input_data = pd.DataFrame([student.model_dump()])
        # Transform using preprocessor
        features_trans = PREPROCESSOR.transform(input_data)

        # Predict
        pred_label = int(MODEL.predict(features_trans)[0])
        pred_prob = float(MODEL.predict_proba(features_trans)[0][1]) if hasattr(MODEL, "predict_proba") else float(pred_label)

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        triggers = evaluate_risk_triggers(student)
        risk_category = "High Risk (Intervention Required)" if pred_label == 1 else "Low Risk (On Track)"

        return PredictionResponse(
            student_id=student.student_id or "STU_ANON",
            dropout_risk_prediction=pred_label,
            risk_probability=round(pred_prob, 4),
            risk_category=risk_category,
            primary_risk_triggers=triggers,
            model_version=MODEL_METADATA.get("champion_model_name", "v1.0.0"),
            inference_latency_ms=latency_ms,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Inference error: {str(e)}")


@app.post("/predict-batch", response_model=BatchPredictionResponse, tags=["Inference"])
def predict_batch(payload: BatchPredictionRequest):
    predictions = []
    for item in payload.students:
        preds = predict_single(item)
        predictions.append(preds)

    return BatchPredictionResponse(
        total_processed=len(predictions),
        predictions=predictions,
    )


@app.get("/drift-report", tags=["Monitoring"])
def get_drift_report():
    try:
        report = run_drift_analysis()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate drift report: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
