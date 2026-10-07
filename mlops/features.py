"""
Feature Engineering and Dataset Splitting Pipeline.
Fulfills Assignment Part 2 Requirements:
- Reproducible feature pipeline with ColumnTransformer, StandardScaler, and OneHotEncoder.
- Problem-appropriate Stratified Train / Validation / Test split (70% / 15% / 15%).
- Artifact serialization for production inference consistency.
"""

from pathlib import Path
import sys
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import ANALYTICS_DATA_DIR, MODELS_DIR, RANDOM_STATE, TARGET_COLUMN

NUMERICAL_FEATURES = [
    "age",
    "studytime",
    "failures",
    "attendance_percentage",
    "average_internal_marks",
    "assignment_completion_rate",
    "avg_weekly_learning_hours",
    "previous_score_trend",
]

CATEGORICAL_FEATURES = [
    "gender",
    "address",
    "famsize",
    "Pstatus",
    "schoolsup",
    "famsup",
    "paid",
    "activities",
    "internet",
]


def build_preprocessor():
    """Constructs sklearn preprocessing ColumnTransformer."""
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERICAL_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
        ]
    )
    return preprocessor


def prepare_datasets():
    mart_file = ANALYTICS_DATA_DIR / "student_risk_mart.csv"
    if not mart_file.exists():
        raise FileNotFoundError(f"Analytical Mart {mart_file} not found! Run ETL pipeline first.")

    df = pd.read_csv(mart_file)

    # Select feature columns + target
    all_cols = NUMERICAL_FEATURES + CATEGORICAL_FEATURES + [TARGET_COLUMN]
    df_subset = df[all_cols].dropna()

    X = df_subset.drop(columns=[TARGET_COLUMN])
    y = df_subset[TARGET_COLUMN].astype(int)

    # Stratified Split: 70% Train, 15% Validation, 15% Test
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=RANDOM_STATE, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=RANDOM_STATE, stratify=y_temp
    )

    # Fit preprocessor on training data ONLY to prevent data leakage
    preprocessor = build_preprocessor()
    X_train_trans = preprocessor.fit_transform(X_train)
    X_val_trans = preprocessor.transform(X_val)
    X_test_trans = preprocessor.transform(X_test)

    # Save fitted preprocessor
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    preprocessor_path = MODELS_DIR / "feature_preprocessor.joblib"
    joblib.dump(preprocessor, preprocessor_path)
    print(f"[OK] Preprocessor saved to {preprocessor_path.name}")

    print(f"[OK] Dataset Split Summary:")
    print(f"     -> Train set:      {X_train.shape[0]} samples ({y_train.mean()*100:.1f}% risk rate)")
    print(f"     -> Validation set: {X_val.shape[0]} samples ({y_val.mean()*100:.1f}% risk rate)")
    print(f"     -> Test set:       {X_test.shape[0]} samples ({y_test.mean()*100:.1f}% risk rate)")

    return {
        "X_train": X_train_trans,
        "y_train": y_train,
        "X_val": X_val_trans,
        "y_val": y_val,
        "X_test": X_test_trans,
        "y_test": y_test,
        "raw_train_df": X_train,
        "preprocessor": preprocessor,
    }


if __name__ == "__main__":
    prepare_datasets()
