"""
Central Configuration for Student Performance and Dropout-Risk Prediction System.
Handles database connections, directory paths, data quality rules, and ML parameters.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
STAGING_DATA_DIR = DATA_DIR / "staging"
CLEANED_DATA_DIR = DATA_DIR / "cleaned"
ANALYTICS_DATA_DIR = DATA_DIR / "analytics"
REJECTED_DATA_DIR = DATA_DIR / "rejected"
MODELS_DIR = BASE_DIR / "mlops" / "models"

# Ensure directories exist
for directory in [
    RAW_DATA_DIR,
    STAGING_DATA_DIR,
    CLEANED_DATA_DIR,
    ANALYTICS_DATA_DIR,
    REJECTED_DATA_DIR,
    MODELS_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)

# Database Configuration (PostgreSQL with SQLite fallback for portability)
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "student_analytics_db")

POSTGRES_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SQLITE_URI = f"sqlite:///{DATA_DIR / 'academic_warehouse.db'}"

# Use SQLite by default for seamless standalone execution, switch to Postgres if configured
DATABASE_URL = os.getenv("DATABASE_URL", SQLITE_URI)

# Data Quality Thresholds
VALIDATION_RULES = {
    "min_age": 15,
    "max_age": 25,
    "min_score": 0.0,
    "max_score": 100.0,
    "min_attendance_pct": 0.0,
    "max_attendance_pct": 100.0,
    "valid_semesters": [1, 2, 3, 4, 5, 6, 7, 8],
    "valid_status": ["Present", "Absent", "Excused"],
}

# MLOps Configuration
RANDOM_STATE = 42
TEST_SIZE = 0.20
VAL_SIZE = 0.15
TARGET_COLUMN = "dropout_risk"  # 1 = At Risk / Dropout, 0 = Safe / On Track
DRIFT_PSI_THRESHOLD = 0.25  # PSI > 0.25 indicates significant shift
API_HOST = "0.0.0.0"
API_PORT = 8000
DASHBOARD_PORT = 8501
