-- ====================================================================
-- PostgreSQL Database Schema for Student Performance & Dropout-Risk
-- Architecture: Star Schema with Analytical Data Marts & Audit Tables
-- Course: Data Engineering and MLOps
-- ====================================================================

-- 1. DIMENSION: Student Demographics (UCI Historical Foundation)
CREATE TABLE IF NOT EXISTS dim_student (
    student_id VARCHAR(20) PRIMARY KEY,
    gender VARCHAR(10),
    age INT CHECK (age >= 15 AND age <= 30),
    address VARCHAR(5),
    famsize VARCHAR(10),
    pstatus VARCHAR(5),
    medu INT,
    fedu INT,
    traveltime INT,
    studytime INT,
    failures INT,
    schoolsup VARCHAR(10),
    famsup VARCHAR(10),
    paid VARCHAR(10),
    activities VARCHAR(10),
    internet VARCHAR(10),
    health INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. DIMENSION: Course and Subject Information
CREATE TABLE IF NOT EXISTS dim_course_subject (
    course_code VARCHAR(20) PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    credits INT NOT NULL,
    department VARCHAR(50) NOT NULL
);

-- 3. DIMENSION: Academic Semester
CREATE TABLE IF NOT EXISTS dim_semester (
    semester_id INT PRIMARY KEY,
    semester_name VARCHAR(50) NOT NULL,
    academic_year VARCHAR(20) NOT NULL
);

-- 4. DIMENSION: LMS Activity & Digital Footprint
CREATE TABLE IF NOT EXISTS dim_lms_activity (
    activity_id VARCHAR(50) PRIMARY KEY,
    student_id VARCHAR(20) REFERENCES dim_student(student_id),
    course_code VARCHAR(20) REFERENCES dim_course_subject(course_code),
    semester INT,
    assignment_submissions INT,
    quiz_attempts INT,
    forum_posts INT,
    lms_login_count INT,
    learning_hours_weekly NUMERIC(5, 2)
);

-- 5. FACT TABLE: Attendance Log (Session-grain fact table)
CREATE TABLE IF NOT EXISTS fact_attendance (
    attendance_id VARCHAR(50) PRIMARY KEY,
    student_id VARCHAR(20) REFERENCES dim_student(student_id),
    course_code VARCHAR(20) REFERENCES dim_course_subject(course_code),
    semester INT,
    session_date DATE,
    session_type VARCHAR(20),
    status VARCHAR(20) CHECK (status IN ('Present', 'Absent', 'Excused')),
    is_attended INT DEFAULT 0
);

-- 6. FACT TABLE: Assessment and Exam Marks (Assessment-grain fact table)
CREATE TABLE IF NOT EXISTS fact_assessment_marks (
    mark_id VARCHAR(50) PRIMARY KEY,
    student_id VARCHAR(20) REFERENCES dim_student(student_id),
    course_code VARCHAR(20) REFERENCES dim_course_subject(course_code),
    semester INT,
    assessment_name VARCHAR(50),
    score_obtained NUMERIC(5, 2) CHECK (score_obtained >= 0.0),
    max_score NUMERIC(5, 2),
    score_pct NUMERIC(5, 2)
);

-- 7. ANALYTICAL DATA MART: Aggregated Student Risk View / Mart
CREATE TABLE IF NOT EXISTS mart_student_risk_analytics (
    student_id VARCHAR(20) PRIMARY KEY REFERENCES dim_student(student_id),
    gender VARCHAR(10),
    age INT,
    studytime INT,
    failures INT,
    attendance_percentage NUMERIC(5, 2),
    average_internal_marks NUMERIC(5, 2),
    assignment_completion_rate NUMERIC(5, 2),
    avg_weekly_learning_hours NUMERIC(5, 2),
    previous_score_trend NUMERIC(5, 2),
    dropout_risk INT CHECK (dropout_risk IN (0, 1)),
    risk_category VARCHAR(50),
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. AUDIT & DATA QUALITY: Pipeline Ingestion Audit Log
CREATE TABLE IF NOT EXISTS etl_audit_log (
    log_id SERIAL PRIMARY KEY,
    source_name VARCHAR(100),
    file_name VARCHAR(100),
    staged_path TEXT,
    status VARCHAR(20),
    row_count INT,
    file_checksum_md5 VARCHAR(64),
    extracted_at TIMESTAMP
);

-- 9. AUDIT & DATA QUALITY: Rejected Records and Anomaly Log
CREATE TABLE IF NOT EXISTS etl_rejected_records (
    rejection_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    record_identifier VARCHAR(100),
    rejection_reason TEXT,
    severity VARCHAR(20),
    raw_record_payload TEXT,
    rejected_at TIMESTAMP
);

-- Indexes for Fast Analytics Queries
CREATE INDEX IF NOT EXISTS idx_att_student ON fact_attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_marks_student ON fact_assessment_marks(student_id);
CREATE INDEX IF NOT EXISTS idx_risk_status ON mart_student_risk_analytics(dropout_risk);
