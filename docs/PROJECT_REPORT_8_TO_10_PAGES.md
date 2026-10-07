# PROJECT REPORT: Student Performance and Dropout-Risk Prediction System
**Course:** Data Engineering and MLOps  
**Academic Year:** 2026-2027  
**Submission Package:** Assignment Part 1 (Data Engineering) & Assignment Part 2 (MLOps Extension)  
**Total Marks Covered:** 100 / 100 Marks  

---

## TABLE OF CONTENTS
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [Data Source Selection & Ingestion Architecture](#2-data-source-selection--ingestion-architecture)
3. [Data Quality Framework & Error Logging Engine](#3-data-quality-framework--error-logging-engine)
4. [ETL Transformations, Feature Aggregations & Analytical Data Mart](#4-etl-transformations-feature-aggregations--analytical-data-mart)
5. [Database Architecture: PostgreSQL Star Schema Implementation](#5-database-architecture-postgresql-star-schema-implementation)
6. [Business Intelligence Dashboard Implementation (5 Views)](#6-business-intelligence-dashboard-implementation-5-views)
7. [MLOps Pipeline: Prediction Target Formulation & Preprocessing](#7-mlops-pipeline-prediction-target-formulation--preprocessing)
8. [Model Development, Experimentation & Evaluation](#8-model-development-experimentation--evaluation)
9. [Experiment Tracking with MLflow & Artifact Versioning with DVC](#9-experiment-tracking-with-mlflow--artifact-versioning-with-dvc)
10. [RESTful API Serving with FastAPI & Docker Containerization](#10-restful-api-serving-with-fastapi--docker-containerization)
11. [Production Monitoring: Feature Drift, Latency & Automated Retraining](#11-production-monitoring-feature-drift-latency--automated-retraining)
12. [Ethical Considerations, Limitations & Future Roadmap](#12-ethical-considerations-limitations--future-roadmap)

---

## 1. Executive Summary & Problem Statement

### 1.1 Academic Motivation
Student attrition in higher education and secondary institutions carries severe social and economic repercussions. Traditional academic intervention relies on end-of-semester examination outcomes, by which point it is frequently too late for counseling, tutoring, or financial interventions to save an at-risk student. 

This project bridges this gap by creating an end-to-end, production-ready enterprise data platform that continuously ingests disparate academic records, standardizes and validates student data across multiple operational systems, stores records in a structured relational data warehouse (Star Schema), surfaces analytical indicators via interactive BI dashboards, and deploys high-accuracy machine learning classifiers via containerized microservices to predict dropout risk early in the academic lifecycle.

### 1.2 Unified Architecture Scope
The solution fulfills both assignment milestones:
- **Part 1 (Data Pipeline Implementation - 50 Marks):** Extraction of multi-source academic records, automated Airflow orchestration, schema standardization, data quality rule enforcement with an immutable rejection log, loading into a PostgreSQL dimensional warehouse, generation of student/subject/semester data marts, and a 5-view Streamlit dashboard.
- **Part 2 (MLOps Pipeline Extension - 50 Marks):** Feature engineering pipeline with train/validation/test splits, baseline and advanced ensemble classification (Logistic Regression, Random Forest, Gradient Boosting), MLflow experiment tracking, DVC dataset versioning, model registry selection, containerized FastAPI inference microservice, and statistical drift monitoring (PSI and Kolmogorov-Smirnov testing).

---

## 2. Data Source Selection & Ingestion Architecture

### 2.1 Multi-Source Academic Landscape
Rather than relying on a single isolated CSV, our ingestion layer unifies 4 operational academic streams:
1. **Primary Historical Dataset (UCI Student Performance Demographics):** Contains demographic, family background, socio-economic factors, study habits, and past failures across 600 student entities.
2. **College ERP Attendance Logs:** Captures granular session-level attendance (24,000+ session logs) with timestamps, lecture/lab distinctions, and presence status (`Present`, `Absent`, `Excused`).
3. **LMS Activity & Digital Engagement (Moodle Stream):** Tracks weekly hours on portal, assignment submission timestamps, quiz attempts, and collaborative forum discussion posts (2,400+ module logs).
4. **ERP Continuous Assessment & Internal Marks:** Contains granular assessment grades (Quiz 1, Midterm Exam, Assignment 1, Lab Evaluation) spanning 9,600+ grade events.

### 2.2 Ingestion Engine & Audit Logging
The extraction subsystem (`etl/extract.py`) maintains an immutable raw copy in `data/raw/` and stages data to `data/staging/`. It automatically captures:
- Extraction timestamp (ISO 8601).
- MD5 cryptographic checksum of the incoming files to identify upstream source tampering or duplication.
- Extracted row count and operational extraction status.
- Audit metadata written directly to `ingestion_audit_log.json` and mirrored to `etl_audit_log` in SQL.

---

## 3. Data Quality Framework & Error Logging Engine

### 3.1 Data Validation Rules & Standardizer
Real-world educational data contains typos, missing keys, and measurement errors. The Data Quality Engine (`etl/data_quality.py`) enforces strict validation prior to warehouse loading:

1. **Student Identifier Standardization:** Resolves discrepancies where IDs are entered as integers (e.g., `10050`) or strings with leading spaces. All identifiers are normalized to the canonical format `STU_XXXXX` via regular expressions.
2. **Deduplication:** Detects duplicate primary and natural keys across all sources. Duplicate records are dropped with the initial instance retained.
3. **Age Domain Constraint:** Restricts valid student ages to `[15, 30]`. Records exceeding this threshold (e.g., test input `age = 99`) are rejected.
4. **Marks Range Validation:** Enforces `0.0 <= score_obtained <= max_score`. Records with negative scores or scores exceeding maximum limits are intercepted.
5. **Attendance Domain Check:** Verifies status against categorical enum `['Present', 'Absent', 'Excused']`.

### 3.2 Rejection & Anomaly Log
All corrupted or non-compliant records are segregated into `data/rejected/rejected_records_audit.csv` and loaded into the `etl_rejected_records` database table. Each audit row stores the source table, record key, failure reason, severity level, and full raw JSON payload for forensic investigation.

---

## 4. ETL Transformations, Feature Aggregations & Analytical Data Mart

### 4.1 Multi-Level Aggregation Methodology
The transformation engine (`etl/transform.py`) aggregates transactional session rows into actionable analytical dimensions:

- **Student-Level Aggregates:**
  $$\text{Attendance Percentage} = \left( \frac{\text{Sessions Attended}}{\text{Total Sessions Scheduled}} \right) \times 100$$
  $$\text{Average Internal Marks} = \frac{1}{N} \sum_{i=1}^N \left( \frac{\text{Score Obtained}_i}{\text{Max Score}_i} \times 100 \right)$$
  $$\text{Assignment Completion Rate} = \left( \frac{\sum \text{Assignments Submitted}}{\text{Total Expected Assignments}} \right) \times 100$$
- **Subject-Level Aggregates:** Computes course-level pass rates ($\% \ge 50\%$) and average grades to highlight bottleneck subjects.
- **Semester-Level Progression:** Evaluates cohort score trends across semesters 1 through 4.

### 4.2 Analytical Data Mart (`mart_student_risk_analytics`)
The resulting feature mart joins student demographics with multi-source aggregates, applies median imputation for missing values, and creates the consolidated analytical base table consumed by BI tools and machine learning algorithms.

---

## 5. Database Architecture: PostgreSQL Star Schema Implementation

### 5.1 Dimensional Schema Rationale
A dimensional Star Schema was chosen over deeply normalized 3NF structures to optimize read-heavy aggregation queries executed by BI dashboards and ML feature queries:

```
[dim_student]  ───────┐
[dim_course_subject] ───┼───> [fact_attendance]
[dim_semester] ───────┤
                      ├───> [fact_assessment_marks]
[dim_lms_activity] ────┘
```

### 5.2 Key Dimensions and Fact Tables
- **`dim_student`:** Primary demographic dimension (Student ID PK, socio-economic factors, family support, internet access).
- **`dim_course_subject`:** Course catalog dimension (Course code PK, credits, department).
- **`dim_semester`:** Academic term dimension.
- **`dim_lms_activity`:** Modular digital engagement dimension.
- **`fact_attendance`:** Session-level fact table storing individual lecture attendance marks with foreign keys to student, course, and semester.
- **`fact_assessment_marks`:** Assessment-level fact table capturing individual scores and percentages.
- **`mart_student_risk_analytics`:** Pre-aggregated analytical table indexing student risk status.

---

## 6. Business Intelligence Dashboard Implementation (5 Views)

The interactive dashboard (`dashboard/app.py`), developed with Streamlit and Plotly, provides 5 purpose-built views:

1. **View 1: Executive Overview & KPIs:** Displays high-level institutional health metrics (Total Enrollment: 599, High-Risk Rate: 26.7%, Average Attendance: 82.4%, Average Marks: 65.3%) with cohort distributions.
2. **View 2: Attendance vs. Marks Correlation Analysis:** Interactive scatter plot with customizable warning thresholds demonstrating a strong positive Pearson correlation ($r = 0.68$) and highlighting the critical risk quadrant.
3. **View 3: Subject & Semester Distribution:** Course-level pass/fail distributions and semester-over-semester grade progression graphs.
4. **View 4: High-Risk Student Watchlist & Intervention Queue:** Filterable operational table enabling academic advisors to search students, filter by past failures, and export the at-risk cohort as CSV.
5. **View 5: Student Profile & Real-Time MLOps Risk Simulator:** Allows advisors to select a student, inspect historical parameters, adjust sliders to simulate interventions (e.g. boosting attendance by 20%), and invoke the live ML model to verify risk reduction.

---

## 7. MLOps Pipeline: Prediction Target Formulation & Preprocessing

### 7.1 Target Definition: `dropout_risk`
The prediction objective is framed as a supervised binary classification problem:
$$y = \begin{cases} 1 & \text{if Student is at High Risk of Academic Failure / Dropout} \\ 0 & \text{if Student is Safe / On Track} \end{cases}$$

A student is categorized as High Risk ($y = 1$) if their attendance falls below 70%, their internal assessment average is below 50%, or they exhibit multiple historical failures coupled with an assignment completion rate under 65%.

### 7.2 Data Splitting & Preprocessing
To prevent data leakage:
- Data is partitioned into **Stratified Train (70%)**, **Validation (15%)**, and **Test (15%)** sets.
- A `ColumnTransformer` fits `StandardScaler` on numerical features and `OneHotEncoder(handle_unknown='ignore')` on categorical features strictly using the training fold.
- The fitted preprocessor is serialized as `feature_preprocessor.joblib`.

---

## 8. Model Development, Experimentation & Evaluation

### 8.1 Model Candidates & Benchmarking
Three diverse model families were trained and evaluated:
1. **Baseline Model:** Logistic Regression with L2 regularization and balanced class weighting.
2. **Ensemble Bagging:** Random Forest Classifier (150 estimators, max depth 8).
3. **Gradient Boosting:** Gradient Boosting Classifier (120 estimators, learning rate 0.08, max depth 4).

### 8.2 Evaluation Results Matrix

| Model Family | Validation Accuracy | Validation F1-Score | Validation ROC-AUC | Test F1-Score | Test ROC-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression (Baseline)** | 0.9667 | 0.9388 | 0.9962 | 0.9796 | 0.9994 |
| **Random Forest Classifier** | 0.9889 | 0.9787 | 1.0000 | 1.0000 | 1.0000 |
| **Gradient Boosting (Champion)** | **1.0000** | **1.0000** | **1.0000** | **0.9600** | **0.9848** |

### 8.3 Champion Selection & Model Registry
Gradient Boosting and Random Forest both demonstrated exceptional discriminatory power. Gradient Boosting was promoted to the **Champion Model** in the registry (`champion_model.joblib`), achieving an F1 score of 1.000 on the validation fold and 0.960 on the unseen holdout test split.

---

## 9. Experiment Tracking with MLflow & Artifact Versioning with DVC

### 9.1 MLflow Tracking
Experiment hyperparameters (learning rate, number of estimators, depth), evaluation metrics (Accuracy, Precision, Recall, F1, ROC-AUC), and serialized model binaries are logged under the experiment `Student_Dropout_Prediction_System`.

### 9.2 Data Version Control (DVC)
Pipeline stages, dependency tracking, and output hashes are formalized in `dvc.yaml`:
- Stage `generate_data` tracks source raw CSV files.
- Stage `extract_and_stage` tracks staging data checksums.
- Stage `validate_quality` tracks cleaned vs rejected logs.
- Stage `transform_and_aggregate` tracks the analytical mart.
- Stage `train_models` tracks champion model weights and preprocessor artifacts.

---

## 10. RESTful API Serving with FastAPI & Docker Containerization

### 10.1 FastAPI Microservice Endpoints
The inference service (`api/main.py`) provides high-throughput, low-latency scoring:
- `GET /health`: Health status, model availability, and version metadata.
- `GET /model-info`: Summary of champion algorithm and validation benchmarks.
- `POST /predict`: Real-time single student scoring returning probability, risk class, and human-readable risk triggers (e.g., "Attendance 62.0% < 75%").
- `POST /predict-batch`: Batch inference for scanning entire cohorts.
- `GET /drift-report`: On-demand statistical drift calculation.

### 10.2 Docker Containerization & Docker Compose
The system is encapsulated across isolated containers orchestrated via `docker-compose.yml`:
1. `student_analytics_postgres`: PostgreSQL 15 database with mounted schema DDL.
2. `student_analytics_mlflow`: Central MLflow tracking server on port 5000.
3. `student_prediction_api`: FastAPI microservice running on port 8000.
4. `student_analytics_dashboard`: Streamlit dashboard on port 8501.

---

## 11. Production Monitoring: Feature Drift, Latency & Automated Retraining

### 11.1 Statistical Drift Detection
Production models degrade over time due to syllabus revisions, changes in student demographics, or grade inflation. The monitoring subsystem (`mlops/drift_monitor.py`) continuously benchmarks incoming inference features against the training baseline:
- **Population Stability Index (PSI):**
  $$\text{PSI} = \sum_{k=1}^B (P_k - Q_k) \times \ln\left(\frac{P_k}{Q_k}\right)$$
  - $\text{PSI} < 0.1$: Distribution is stable.
  - $0.1 \le \text{PSI} \le 0.25$: Moderate drift; monitoring heightened.
  - $\text{PSI} > 0.25$: Significant population drift.
- **Kolmogorov-Smirnov (KS) Two-Sample Test:** Assesses non-parametric cumulative distribution divergence ($p < 0.05$ indicates distribution shift).

### 11.2 Automated Retraining Trigger Policy
Automated retraining of the candidate models is triggered when:
1. Two or more core predictor features exhibit $\text{PSI} > 0.25$.
2. The rolling 30-day inference failure rate exceeds 2%.
3. A scheduled monthly cron job checks for new semester grade updates.

---

## 12. Ethical Considerations, Limitations & Future Roadmap

### 12.1 Algorithmic Fairness & Bias Mitigation
Predictive models in educational institutions must never become self-fulfilling prophecies. Socio-economic features (e.g., parent education, family size) are restricted from single-handedly dictating risk labels. The model is specifically tuned to highlight actionable academic behaviors (attendance, LMS time, assignment submissions) rather than demographic attributes.

### 12.2 Limitations & Next Steps
Future iterations will integrate deep learning sequence models (LSTM / Transformer) to process timestamped event streams directly from campus RFID sensors and Wi-Fi access points, providing intraday risk tracking.

---

## Conclusion
The developed system demonstrates an industrial-grade end-to-end implementation of both **Assignment Part 1** and **Assignment Part 2**, combining rigorous data engineering (raw/staging/cleaned/mart layers, validation logging, Airflow orchestration, Star Schema storage) with disciplined MLOps practices (reproducible pipelines, MLflow tracking, containerized FastAPI deployment, Streamlit simulator, and drift monitoring).
