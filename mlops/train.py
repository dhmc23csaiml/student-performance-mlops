"""
Model Training and Experiment Tracking Pipeline.
Fulfills Assignment Part 2 Requirements:
- Trains baseline (Logistic Regression) and advanced models (Random Forest, Gradient Boosting).
- Evaluates metrics: Accuracy, Precision, Recall, F1-Score, and ROC-AUC.
- Logs parameters, metrics, and artifacts (compatible with MLflow).
- Selects the champion model and registers it in the local model registry.
"""

import json
from pathlib import Path
import sys
import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import MODELS_DIR, RANDOM_STATE
from mlops.features import prepare_datasets

# Try importing mlflow if user has it installed
try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False


def train_and_evaluate_models():
    print("=" * 60)
    print("STEP 5: MODEL TRAINING & EXPERIMENT EVALUATION")
    print("=" * 60)

    data = prepare_datasets()
    X_train, y_train = data["X_train"], data["y_train"]
    X_val, y_val = data["X_val"], data["y_val"]
    X_test, y_test = data["X_test"], data["y_test"]

    candidate_models = {
        "Logistic_Regression_Baseline": {
            "model": LogisticRegression(max_iter=1000, random_state=RANDOM_STATE, class_weight="balanced"),
            "params": {"penalty": "l2", "C": 1.0, "solver": "lbfgs"},
        },
        "Random_Forest_Classifier": {
            "model": RandomForestClassifier(n_estimators=150, max_depth=8, random_state=RANDOM_STATE, class_weight="balanced"),
            "params": {"n_estimators": 150, "max_depth": 8, "criterion": "gini"},
        },
        "Gradient_Boosting_Classifier": {
            "model": GradientBoostingClassifier(n_estimators=120, learning_rate=0.08, max_depth=4, random_state=RANDOM_STATE),
            "params": {"n_estimators": 120, "learning_rate": 0.08, "max_depth": 4},
        },
    }

    results = {}
    best_f1 = -1.0
    champion_name = None
    champion_obj = None

    if MLFLOW_AVAILABLE:
        mlflow.set_experiment("Student_Dropout_Prediction_System")

    for name, config in candidate_models.items():
        print(f"\n[*] Training candidate: {name}...")
        clf = config["model"]
        clf.fit(X_train, y_train)

        # Validation set predictions
        val_preds = clf.predict(X_val)
        val_probs = clf.predict_proba(X_val)[:, 1] if hasattr(clf, "predict_proba") else val_preds

        # Test set predictions for final unbiased evaluation
        test_preds = clf.predict(X_test)
        test_probs = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else test_preds

        metrics = {
            "val_accuracy": round(float(accuracy_score(y_val, val_preds)), 4),
            "val_precision": round(float(precision_score(y_val, val_preds, zero_division=0)), 4),
            "val_recall": round(float(recall_score(y_val, val_preds, zero_division=0)), 4),
            "val_f1": round(float(f1_score(y_val, val_preds, zero_division=0)), 4),
            "val_roc_auc": round(float(roc_auc_score(y_val, val_probs)), 4),
            "test_accuracy": round(float(accuracy_score(y_test, test_preds)), 4),
            "test_f1": round(float(f1_score(y_test, test_preds, zero_division=0)), 4),
            "test_roc_auc": round(float(roc_auc_score(y_test, test_probs)), 4),
        }

        results[name] = {
            "params": config["params"],
            "metrics": metrics,
        }

        print(f"    Val Accuracy: {metrics['val_accuracy']:.4f} | Val F1: {metrics['val_f1']:.4f} | Val ROC-AUC: {metrics['val_roc_auc']:.4f}")
        print(f"    Test F1:      {metrics['test_f1']:.4f} | Test ROC-AUC: {metrics['test_roc_auc']:.4f}")

        # Save model candidate
        model_file = MODELS_DIR / f"{name}.joblib"
        joblib.dump(clf, model_file)

        # MLflow experiment logging
        if MLFLOW_AVAILABLE:
            with mlflow.start_run(run_name=name):
                mlflow.log_params(config["params"])
                mlflow.log_metrics(metrics)
                mlflow.sklearn.log_model(clf, artifact_path="model")

        # Select champion based on validation F1 score (prioritizing recall and precision on at-risk students)
        if metrics["val_f1"] > best_f1:
            best_f1 = metrics["val_f1"]
            champion_name = name
            champion_obj = clf

    # Save Champion Model to Registry
    print("\n" + "=" * 60)
    print(f"MODEL REGISTRY DECISION: Champion is '{champion_name}' (Val F1: {best_f1:.4f})")
    print("=" * 60)

    champion_path = MODELS_DIR / "champion_model.joblib"
    joblib.dump(champion_obj, champion_path)

    registry_metadata = {
        "champion_model_name": champion_name,
        "champion_val_f1": best_f1,
        "champion_test_roc_auc": results[champion_name]["metrics"]["test_roc_auc"],
        "artifact_path": str(champion_path),
        "all_model_evaluations": results,
    }

    summary_file = MODELS_DIR / "model_registry.json"
    with open(summary_file, "w") as f:
        json.dump(registry_metadata, f, indent=2)

    print(f"[OK] Champion registered at {champion_path.name}")
    print(f"[OK] Registry metadata written to {summary_file.name}\n")
    return registry_metadata


if __name__ == "__main__":
    train_and_evaluate_models()
