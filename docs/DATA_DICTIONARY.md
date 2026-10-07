# Data Dictionary & Validation Rules Catalog
**System:** Student Performance and Dropout-Risk Prediction System  
**Course:** Data Engineering and MLOps  

---

## 1. Table Overview

| Table / Layer | Name | Type | Description |
| :--- | :--- | :--- | :--- |
| Raw / Cleaned | `dim_student` | Dimension | Demographic, socio-economic, and historical background data. |
| Raw / Cleaned | `dim_course_subject` | Dimension | Academic course catalog, credits, and departmental mappings. |
| Raw / Cleaned | `dim_semester` | Dimension | Academic terms and calendar years. |
| Raw / Cleaned | `dim_lms_activity` | Dimension | Learning Management System (Moodle) behavioral tracking. |
| Raw / Cleaned | `fact_attendance` | Fact Table | Individual class session attendance events. |
| Raw / Cleaned | `fact_assessment_marks` | Fact Table | Continuous assessment, midterm, and examination scores. |
| Analytics | `mart_student_risk_analytics` | Data Mart | Denormalized student-level analytical and ML feature table. |
| Audit | `etl_audit_log` | Governance | Extraction batch logs, MD5 hashes, and status. |
| Audit | `etl_rejected_records` | Governance | Data quality failure log with root cause error reasons. |

---

## 2. Comprehensive Attribute Specifications

### Table: `dim_student`
| Field Name | Data Type | Nullable | Primary Key | Description & Domain |
| :--- | :--- | :--- | :--- | :--- |
| `student_id` | VARCHAR(20) | NO | YES | Standardized unique student key (`STU_XXXXX`). |
| `gender` | VARCHAR(10) | NO | NO | Student sex (`'M'` = Male, `'F'` = Female). |
| `age` | INT | NO | NO | Student age (Validated domain: 15 to 30 years). |
| `address` | VARCHAR(5) | NO | NO | Home address type (`'U'` = Urban, `'R'` = Rural). |
| `famsize` | VARCHAR(10) | NO | NO | Family size (`'LE3'` <= 3 members, `'GT3'` > 3 members). |
| `pstatus` | VARCHAR(5) | NO | NO | Parent cohabitation status (`'T'` = Together, `'A'` = Apart). |
| `medu` | INT | NO | NO | Mother education level (`0` = None, `4` = Higher Education). |
| `fedu` | INT | NO | NO | Father education level (`0` = None, `4` = Higher Education). |
| `traveltime` | INT | NO | NO | Home to school travel time (`1` = <15 min to `4` = >1 hour). |
| `studytime` | INT | NO | NO | Weekly study time (`1` = <2h, `2` = 2-5h, `3` = 5-10h, `4` = >10h). |
| `failures` | INT | NO | NO | Count of past class failures (`0` to `4`). |
| `schoolsup` | VARCHAR(10) | NO | NO | Institutional extra educational support (`'yes'`, `'no'`). |
| `famsup` | VARCHAR(10) | NO | NO | Family educational support (`'yes'`, `'no'`). |
| `paid` | VARCHAR(10) | NO | NO | Extra paid classes taken (`'yes'`, `'no'`). |
| `activities` | VARCHAR(10) | NO | NO | Extracurricular activities participation (`'yes'`, `'no'`). |
| `internet` | VARCHAR(10) | NO | NO | Internet access at home (`'yes'`, `'no'`). |
| `health` | INT | NO | NO | Current health status (`1` = Very bad to `5` = Very good). |

### Table: `fact_attendance`
| Field Name | Data Type | Nullable | Primary Key | Description & Domain |
| :--- | :--- | :--- | :--- | :--- |
| `attendance_id` | VARCHAR(50) | NO | YES | Unique attendance event identifier (`ATT_XXXXX`). |
| `student_id` | VARCHAR(20) | NO | NO (FK) | Reference to `dim_student(student_id)`. |
| `course_code` | VARCHAR(20) | NO | NO (FK) | Course code (e.g., `'CS101'`, `'DS201'`). |
| `semester` | INT | NO | NO | Academic semester (`1` through `8`). |
| `session_date` | DATE | NO | NO | Date of lecture or practical session (`YYYY-MM-DD`). |
| `session_type` | VARCHAR(20) | NO | NO | Session type (`'Lecture'`, `'Lab'`). |
| `status` | VARCHAR(20) | NO | NO | Attendance mark (`'Present'`, `'Absent'`, `'Excused'`). |
| `is_attended` | INT | NO | NO | Binary flag (`1` if Present or Excused, `0` if Absent). |

### Table: `fact_assessment_marks`
| Field Name | Data Type | Nullable | Primary Key | Description & Domain |
| :--- | :--- | :--- | :--- | :--- |
| `mark_id` | VARCHAR(50) | NO | YES | Unique mark record identifier (`MRK_XXXXX`). |
| `student_id` | VARCHAR(20) | NO | NO (FK) | Reference to `dim_student(student_id)`. |
| `course_code` | VARCHAR(20) | NO | NO (FK) | Course evaluated. |
| `semester` | INT | NO | NO | Academic semester. |
| `assessment_name` | VARCHAR(50) | NO | NO | Assessment label (e.g., `'Quiz_1'`, `'Midterm_Exam'`). |
| `score_obtained` | NUMERIC(5, 2) | NO | NO | Actual student score (`>= 0.0` and `<= max_score`). |
| `max_score` | NUMERIC(5, 2) | NO | NO | Maximum achievable points for assessment. |
| `score_pct` | NUMERIC(5, 2) | NO | NO | Scaled percentage: `(score_obtained / max_score) * 100`. |

### Table: `dim_lms_activity`
| Field Name | Data Type | Nullable | Primary Key | Description & Domain |
| :--- | :--- | :--- | :--- | :--- |
| `activity_id` | VARCHAR(50) | NO | YES | Unique LMS record key (`LMS_XXXXX`). |
| `student_id` | VARCHAR(20) | NO | NO (FK) | Reference to `dim_student(student_id)`. |
| `course_code` | VARCHAR(20) | NO | NO (FK) | Course LMS environment. |
| `semester` | INT | NO | NO | Semester identifier. |
| `assignment_submissions` | INT | NO | NO | Total assignments submitted on time. |
| `quiz_attempts` | INT | NO | NO | Digital quiz attempts count. |
| `forum_posts` | INT | NO | NO | Collaborative forum discussion posts. |
| `lms_login_count` | INT | NO | NO | Cumulative portal logins. |
| `learning_hours_weekly`| NUMERIC(5, 2) | NO | NO | Average weekly active screen time in hours. |

### Table: `mart_student_risk_analytics` (Analytical Data Mart)
| Field Name | Data Type | Nullable | Primary Key | Description & Analytical Role |
| :--- | :--- | :--- | :--- | :--- |
| `student_id` | VARCHAR(20) | NO | YES | Unique student identifier. |
| `attendance_percentage` | NUMERIC(5, 2) | NO | NO | Aggregate attendance across all courses (`0.0%` to `100.0%`). |
| `average_internal_marks` | NUMERIC(5, 2) | NO | NO | Aggregate grade percentage across all exams (`0.0` to `100.0`). |
| `assignment_completion_rate` | NUMERIC(5, 2) | NO | NO | Ratio of completed assignments (`0.0%` to `100.0%`). |
| `avg_weekly_learning_hours` | NUMERIC(5, 2) | NO | NO | Weekly hours logged in LMS. |
| `previous_score_trend` | NUMERIC(5, 2) | NO | NO | Prior term performance momentum. |
| `dropout_risk` | INT | NO | NO | **Prediction Target (Part 2)**: `1` = High Risk, `0` = Low Risk. |
| `risk_category` | VARCHAR(50) | NO | NO | Human-readable advisor label for dashboards. |

---

## 3. Data Quality & Rejection Validation Rules

| Rule ID | Table Target | Attribute | Validation Condition | Remediation / Rejection Action |
| :--- | :--- | :--- | :--- | :--- |
| `VR-01` | All | `student_id` | Match regex `^STU_\d+$` | Strip spaces; prefix missing `'STU_'` if numeric; reject if corrupted. |
| `VR-02` | All | Primary Keys | Must be globally unique | Drop duplicates keeping first; log duplicate rows in `etl_rejected_records`. |
| `VR-03` | `dim_student` | `age` | `15 <= age <= 30` | Reject record if age < 15 or > 30 (log anomaly in audit). |
| `VR-04` | `fact_attendance` | `status` | In `['Present', 'Absent', 'Excused']` | Reject record if unrecognized attendance status string. |
| `VR-05` | `fact_assessment_marks`| `score_obtained` | `0.0 <= score_obtained <= max_score` | Reject record if negative or exceeding maximum possible marks. |
| `VR-06` | `dim_lms_activity` | `learning_hours_weekly` | `0.0 <= hours <= 100.0` | Reject if extreme anomaly > 100 hours/week. |
| `VR-07` | Mart Aggregation | Feature Nulls | No NaNs in critical predictors | Impute median for missing attendance/marks; assign 50% baseline for assignments. |
