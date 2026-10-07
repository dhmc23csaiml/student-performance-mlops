# Student Performance and Dropout-Risk Prediction System
### Complete End-to-End Implementation for Data Engineering & MLOps

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B.svg)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📌 Project Overview
This repository delivers an end-to-end academic analytics and MLOps ecosystem that ingests, cleans, validates, and stores multi-source student records into a relational **Star Schema**, visualizes insights across **5 interactive dashboard views**, and serves real-time **dropout-risk predictions** via a containerized **FastAPI** microservice with **drift monitoring**.

It fully satisfies all requirements of both **Assignment Part 1 (Data Pipeline)** and **Assignment Part 2 (MLOps Extension)**.

---

## 📁 Project Structure

```
student-performance-mlops/
├── README.md                           # Master setup & execution guide
├── requirements.txt                    # Pinned Python dependencies
├── docker-compose.yml                  # Multi-container orchestration (Postgres, MLflow, API, Dashboard)
├── Dockerfile.api                      # Container image for FastAPI microservice
├── Dockerfile.dashboard                # Container image for Streamlit dashboard
├── .env.example                        # Template for environment variables
├── dvc.yaml                            # DVC data & model artifact pipeline definition
├── config.py                           # Central configuration & directory paths
├── data/
│   ├── raw/                            # Immutable raw extracts (UCI, ERP, LMS)
│   ├── staging/                        # Staging area with row-count and MD5 audit
│   ├── cleaned/                        # Standardized, validated dimension & fact tables
│   ├── analytics/                      # Analytical Data Mart (student_risk_mart.csv)
│   └── rejected/                       # Rejected-record error log (rejected_records_audit.csv)
├── database/
│   ├── schema.sql                      # PostgreSQL Star Schema DDL & analytical views
│   └── db_manager.py                   # Relational database manager (PostgreSQL / SQLite)
├── etl/
│   ├── generate_datasets.py            # Multi-source dataset simulator (with intentional anomalies)
│   ├── extract.py                      # Extraction script with checksum & metadata logging
│   ├── data_quality.py                 # Validation engine & rejected-record logger
│   ├── transform.py                    # Aggregation engine (attendance %, avg marks, risk target)
│   ├── load.py                         # Warehouse table & data mart loader
│   └── pipeline_runner.py              # End-to-end master ETL execution script
├── dags/
│   └── student_analytics_dag.py        # Production Apache Airflow DAG
├── mlops/
│   ├── features.py                     # Stratified splitting & ColumnTransformer pipeline
│   ├── train.py                        # Model trainer (LogReg, RandomForest, GradientBoosting)
│   ├── drift_monitor.py                # Statistical feature drift detector (PSI & KS-test)
│   └── models/                         # Serialized models, preprocessors & registry metadata
├── api/
│   ├── schemas.py                      # Pydantic validation request/response schemas
│   └── main.py                         # FastAPI RESTful prediction microservice
├── dashboard/
│   └── app.py                          # Streamlit application with 5 comprehensive views
└── docs/
    ├── ARCHITECTURE_DESIGN.md          # System architecture, Star Schema & Mermaid diagrams
    ├── DATA_DICTIONARY.md              # Complete catalog of fields, types & validation rules
    └── PROJECT_REPORT_8_TO_10_PAGES.md # 8-10 page academic project submission report
```

---

## 🚀 Quickstart: Run Every Step From Scratch

### Option A: Standalone Local Execution (Fastest - No Docker Required)

#### 1. Setup Virtual Environment & Install Dependencies
```bash
# Clone or open the project folder
cd student-performance-mlops

# Create & activate a virtual environment (optional but recommended)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

#### 2. Execute Part 1: End-to-End Data Engineering Pipeline
Runs data generation, extraction, data quality validation, transformations, and warehouse loading:
```bash
python etl/pipeline_runner.py
```
> **Output:** Populates `data/raw/`, `data/staging/`, `data/cleaned/`, `data/analytics/student_risk_mart.csv`, `data/rejected/rejected_records_audit.csv`, and initializes the local warehouse database!

#### 3. Execute Part 2: Train & Register MLOps Models
Fits candidate models, evaluates metrics, and registers the Champion Model:
```bash
python mlops/train.py
```
> **Output:** Trains Baseline Logistic Regression, Random Forest, and Gradient Boosting. Registers `champion_model.joblib` and `feature_preprocessor.joblib`.

#### 4. Launch the FastAPI Prediction Microservice
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive Swagger API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

#### 5. Launch the Streamlit Interactive Dashboard
In a new terminal window:
```bash
streamlit run dashboard/app.py
```
- Open your browser at: [http://localhost:8501](http://localhost:8501)

---

### Option B: Production Containerized Run (Docker Compose)

Run the entire stack (PostgreSQL Warehouse, MLflow, FastAPI API, and Streamlit Dashboard) with a single command:
```bash
docker compose up --build
```

Access services:
- **Streamlit Dashboard:** [http://localhost:8501](http://localhost:8501)
- **FastAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **MLflow Experiment Server:** [http://localhost:5000](http://localhost:5000)
- **PostgreSQL Warehouse:** `localhost:5432` (`postgres` / `postgres`)

---

## 📊 Assignment Part 1 Deliverables Mapping (50 Marks)

| Item # | Submission Requirement | Implemented File / Location |
| :---: | :--- | :--- |
| **1** | Source code and ETL scripts | [etl/extract.py](file:///C:/Users/dhanu/.gemini/antigravity/scratch/student-performance-mlops/etl/extract.py), [etl/data_quality.py](file:///C:/Users/dhanu/.gemini/antigravity/scratch/student-performance-mlops/etl/data_quality.py), [etl/transform.py](file:///C:/Users/dhanu/.gemini/antigravity/scratch/student-performance-mlops/etl/transform.py), [etl/load.py](file:///C:/Users/dhanu/.gemini/antigravity/scratch/student-performance-mlops/etl/load.py) |
| **2** | Airflow DAG workflow | [dags/student_analytics_dag.py](file:///C:/Users/dhanu/.gemini/antigravity/scratch/student-performance-mlops/dags/student_analytics_dag.py) |
| **3** | Database schema & sample populated tables | [database/schema.sql](file:///C:/Users/dhanu/.gemini/antigravity/scratch/student-performance-mlops/database/schema.sql), [database/db_manager.py](file:///C:/Users/dhanu/.gemini/antigravity/scratch/student-performance-mlops/database/db_manager.py) |
| **4** | Dataset source information & access | [docs/DATA_DICTIONARY.md](file:///C:/Users/dhanu/.gemini/antigravity/scratch/student-performance-mlops/docs/DATA_DICTIONARY.md) (Section 1) |
| **5** | Architecture diagram & pipeline flow | [docs/ARCHITECTURE_DESIGN.md](file:///C:/Users/dhanu/.gemini/antigravity/scratch/student-performance-mlops/docs/ARCHITECTURE_DESIGN.md) |
| **6** | Data dictionary & validation rules | [docs/DATA_DICTIONARY.md](file:///C:/Users/dhanu/.gemini/antigravity/scratch/student-performance-mlops/docs/DATA_DICTIONARY.md) (Section 3) |
| **7** | Streamlit application (5 Views) | [dashboard/app.py](file:///C:/Users/dhanu/.gemini/antigravity/scratch/student-performance-mlops/dashboard/app.py) |
| **8** | Project report (8-10 pages) | [docs/PROJECT_REPORT_8_TO_10_PAGES.md](file:///C:/Users/dhanu/.gemini/antigravity/scratch/student-performance-mlops/docs/PROJECT_REPORT_8_TO_10_PAGES.md) |
| **9** | Execution evidence | Auto-verified via pipeline logs & audit JSON |
| **10**| README with setup & run instructions | [README.md](file:///C:/Users/dhanu/.gemini/antigravity/scratch/student-performance-mlops/README.md) |

---

## 🤖 Assignment Part 2 Deliverables Mapping (50 Marks)

- **Prediction Target:** Defined as `dropout_risk` (1 = At Risk / Dropout, 0 = Safe / On Track).
- **Candidate Models:** Logistic Regression (Baseline), Random Forest, and Gradient Boosting.
- **Experiment Tracking:** MLflow parameter, metric, and artifact logging with automated Champion model registration.
- **Data & Model Versioning:** Tracked via [dvc.yaml](file:///C:/Users/dhanu/.gemini/antigravity/scratch/student-performance-mlops/dvc.yaml).
- **FastAPI Serving:** Pydantic validation, health checks, single prediction (`POST /predict`), batch prediction (`POST /predict-batch`), latency telemetry.
- **Containerization:** Production Dockerfiles (`Dockerfile.api`, `Dockerfile.dashboard`) and `docker-compose.yml`.
- **Drift Monitoring:** Statistical PSI and Kolmogorov-Smirnov test engine in [mlops/drift_monitor.py](file:///C:/Users/dhanu/.gemini/antigravity/scratch/student-performance-mlops/mlops/drift_monitor.py).
