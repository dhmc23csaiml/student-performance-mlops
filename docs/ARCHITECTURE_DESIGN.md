# Architecture Design: Student Performance & Dropout-Risk Prediction System
**Course:** Data Engineering and MLOps  
**System:** Multi-Source Academic Analytics & Real-Time Intervention Platform  

---

## 1. End-to-End System Architecture

The system is engineered as a decoupled, multi-tiered data engineering and MLOps ecosystem.

```mermaid
flowchart TD
    subgraph SOURCELAYER ["1. Source Layer (Multi-Source Academic Data)"]
        S1["UCI Historical Demographics (CSV)"]
        S2["College ERP Attendance Logs (CSV/DB)"]
        S3["LMS Moodle Activity & Submissions (CSV/API)"]
        S4["ERP Continuous Assessment Marks (CSV/DB)"]
    end

    subgraph INGESTION ["2. Ingestion & Orchestration Layer"]
        A1["Apache Airflow DAG / Scheduled Ingestion Engine"]
        A2["Extract Script (MD5 Checksum, Row Auditing)"]
        A3[("Raw & Staging Storage")]
    end

    subgraph DQ_CLEAN ["3. Data Quality & Cleaning Layer"]
        DQ1["Validation Rules Engine"]
        DQ2["Student ID Standardizer (STU_XXXXX)"]
        DQ3["Range Checks (Scores: 0-100, Attendance: 0-100%, Age: 15-30)"]
        REJ[("Rejected Records Audit Log (CSV/DB)")]
    end

    subgraph TRANSFORM ["4. Transformation & Analytical Aggregation"]
        T1["Student-Level Aggregates (Att %, Avg Marks, LMS Hours)"]
        T2["Subject-Level Pass/Fail Aggregates"]
        T3["Semester-Level Progressions"]
        MART[("Analytical Data Mart: mart_student_risk_analytics")]
    end

    subgraph WAREHOUSE ["5. Storage Layer (PostgreSQL Star Schema)"]
        D1[("dim_student")]
        D2[("dim_course_subject")]
        D3[("dim_semester")]
        D4[("dim_lms_activity")]
        F1[("fact_attendance")]
        F2[("fact_assessment_marks")]
    end

    subgraph VISUALIZATION ["6. Visualization & Application Layer"]
        DASH["Streamlit Interactive Analytics Dashboard (5 Views)"]
        V1["KPIs & Cohort Overview"]
        V2["Attendance vs Marks Matrix"]
        V3["Subject/Semester Distribution"]
        V4["At-Risk Early Intervention Watchlist"]
        V5["Student Profile & Simulation Sandbox"]
    end

    subgraph MLOPS ["7. MLOps Lifecycle & Deployment Layer"]
        M1["Data & Feature Versioning (DVC)"]
        M2["Model Training (LogReg, RandomForest, GradientBoosting)"]
        M3["MLflow Experiment Tracking & Model Registry"]
        M4["FastAPI Prediction Microservice (Port 8000)"]
        M5["Docker Containerization & Orchestration"]
        M6["Data & Prediction Drift Monitor (PSI & KS-Test)"]
    end

    SOURCELAYER --> INGESTION
    A1 --> A2 --> A3
    A3 --> DQ_CLEAN
    DQ1 --> REJ
    DQ_CLEAN --> TRANSFORM
    TRANSFORM --> WAREHOUSE
    TRANSFORM --> MART
    WAREHOUSE --> DASH
    MART --> DASH
    MART --> MLOPS
    M4 --> DASH
    M6 -.-> |Retraining Trigger| M2
```

---

## 2. Storage Layer: Star Schema Design

The relational warehouse follows a dimensional **Star Schema** pattern optimized for fast analytical aggregations across student demographics, attendance sessions, and continuous assessment marks:

```mermaid
erDiagram
    dim_student ||--o{ fact_attendance : "tracks"
    dim_student ||--o{ fact_assessment_marks : "earns"
    dim_student ||--o{ dim_lms_activity : "logs"
    dim_course_subject ||--o{ fact_attendance : "held_for"
    dim_course_subject ||--o{ fact_assessment_marks : "tested_in"
    dim_course_subject ||--o{ dim_lms_activity : "enrolled_in"

    dim_student {
        string student_id PK
        string gender
        int age
        string address
        string famsize
        string pstatus
        int medu
        int fedu
        int traveltime
        int studytime
        int failures
        string schoolsup
        string famsup
        string paid
        string activities
        string internet
        int health
    }

    dim_course_subject {
        string course_code PK
        string course_name
        int credits
        string department
    }

    dim_lms_activity {
        string activity_id PK
        string student_id FK
        string course_code FK
        int semester
        int assignment_submissions
        int quiz_attempts
        int forum_posts
        int lms_login_count
        float learning_hours_weekly
    }

    fact_attendance {
        string attendance_id PK
        string student_id FK
        string course_code FK
        int semester
        date session_date
        string session_type
        string status
        int is_attended
    }

    fact_assessment_marks {
        string mark_id PK
        string student_id FK
        string course_code FK
        int semester
        string assessment_name
        float score_obtained
        float max_score
        float score_pct
    }
```

---

## 3. Data Layers Explanation

1. **Raw Layer (`data/raw/`)**: Holds immutable extracts from upstream operational systems with raw filenames and source timestamps.
2. **Staging Layer (`data/staging/`)**: Transient zone where incoming files are registered with row counts and MD5 hashes for pipeline auditability.
3. **Cleaned Layer (`data/cleaned/`)**: Standardized datasets that have passed schema, type, and range validation rules. Malformed or duplicate records are diverted to `data/rejected/`.
4. **Analytical Data Mart (`data/analytics/`)**: Feature-engineered, denormalized analytical views (`mart_student_risk_analytics.csv`) consumed directly by BI dashboards and machine learning pipelines.
5. **Warehouse Storage Layer**: PostgreSQL tables structured as dimensions and facts ensuring referential integrity and query speed.

---

## 4. MLOps CI/CD & Retraining Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Advisor as Academic Advisor / User
    participant Streamlit as Streamlit Dashboard
    participant API as FastAPI Microservice
    participant Registry as Model Registry (Champion)
    participant Monitor as Drift Monitor (PSI/KS)
    participant Pipeline as ML Retraining Engine

    Advisor->>Streamlit: Opens Student Intervention Simulator
    Streamlit->>API: POST /predict (student metrics payload)
    API->>Registry: Fetch champion model & preprocessor
    Registry-->>API: Active weights (Gradient Boosting)
    API-->>Streamlit: Prediction (Risk: 88%, Triggers: Low Attendance)
    Streamlit-->>Advisor: Displays Early Alert & Tutoring Recommendation
    
    Note over API,Monitor: Asynchronous Batch Monitoring
    Monitor->>Monitor: Compute PSI on last 30 days incoming traffic
    alt Feature Drift PSI > 0.25 detected
        Monitor->>Pipeline: Trigger automated retraining pipeline
        Pipeline->>Pipeline: Fit candidate models (LogReg, RF, GradientBoosting)
        Pipeline->>Registry: Promote new champion if validation F1 > current
    end
```
