"""
ETL Transformation and Analytical Aggregation Module.
Fulfills Assignment Part 1 Requirements:
- Standardizes records and joins student multi-source data.
- Handles missing attendance and assignment records.
- Creates Student-level, Subject-level, and Semester-level aggregates.
- Generates required analytical features:
    * attendance_percentage
    * average_internal_marks
    * assignment_completion_rate
    * previous_semester_performance / score trends
    * academic failure & dropout risk target indicator
- Exports the unified Analytical Data Mart (mart_student_risk_analytics).
"""

from pathlib import Path
import sys
import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import CLEANED_DATA_DIR, ANALYTICS_DATA_DIR


def transform_and_aggregate():
    print("=" * 60)
    print("STEP 3: TRANSFORMATION & ANALYTICS AGGREGATION")
    print("=" * 60)

    ANALYTICS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Cleaned Layers
    students_df = pd.read_csv(CLEANED_DATA_DIR / "dim_student.csv")
    attendance_df = pd.read_csv(CLEANED_DATA_DIR / "fact_attendance.csv")
    lms_df = pd.read_csv(CLEANED_DATA_DIR / "dim_lms_activity.csv")
    marks_df = pd.read_csv(CLEANED_DATA_DIR / "fact_assessment_marks.csv")

    print(f"[*] Loaded cleaned tables: {len(students_df)} students, {len(attendance_df)} attendance rows, {len(marks_df)} marks rows.")

    # 2. Attendance Aggregation (Student-level & Course-level)
    print("[*] Computing attendance metrics...")
    attendance_df["is_attended"] = attendance_df["status"].isin(["Present", "Excused"]).astype(int)
    
    # Student-level attendance
    stu_att = attendance_df.groupby("student_id").agg(
        total_sessions=("is_attended", "count"),
        attended_sessions=("is_attended", "sum"),
    ).reset_index()
    stu_att["attendance_percentage"] = (stu_att["attended_sessions"] / stu_att["total_sessions"]) * 100.0
    stu_att["attendance_percentage"] = stu_att["attendance_percentage"].round(2)

    # 3. Marks & Assessment Aggregation
    print("[*] Computing internal assessment and marks aggregates...")
    marks_df["score_pct"] = (marks_df["score_obtained"] / marks_df["max_score"]) * 100.0
    
    # Student-level marks aggregate
    stu_marks = marks_df.groupby("student_id").agg(
        average_internal_marks=("score_pct", "mean"),
        min_internal_mark=("score_pct", "min"),
        max_internal_mark=("score_pct", "max"),
        total_assessments_taken=("score_obtained", "count"),
    ).reset_index()
    stu_marks["average_internal_marks"] = stu_marks["average_internal_marks"].round(2)

    # Subject-level marks aggregate for subject pass/fail analytics
    subject_marks = marks_df.groupby(["course_code"]).agg(
        course_avg_mark=("score_pct", "mean"),
        course_pass_count=("score_pct", lambda s: (s >= 50.0).sum()),
        course_total_count=("score_pct", "count"),
    ).reset_index()
    subject_marks["course_pass_rate"] = ((subject_marks["course_pass_count"] / subject_marks["course_total_count"]) * 100.0).round(2)
    subject_marks.to_csv(ANALYTICS_DATA_DIR / "subject_performance_summary.csv", index=False)

    # Semester-level marks aggregate
    semester_marks = marks_df.groupby(["semester"]).agg(
        semester_avg_mark=("score_pct", "mean"),
        semester_total_tests=("score_pct", "count"),
    ).reset_index()
    semester_marks.to_csv(ANALYTICS_DATA_DIR / "semester_performance_summary.csv", index=False)

    # 4. LMS Digital Activity Aggregation
    print("[*] Computing LMS engagement and assignment completion rate...")
    # Assume 5 assignments expected per course (4 courses = 20 assignments)
    stu_lms = lms_df.groupby("student_id").agg(
        total_submitted_assignments=("assignment_submissions", "sum"),
        quiz_attempts_avg=("quiz_attempts", "mean"),
        total_forum_posts=("forum_posts", "sum"),
        avg_weekly_learning_hours=("learning_hours_weekly", "mean"),
        total_lms_logins=("lms_login_count", "sum"),
    ).reset_index()
    
    # 4 courses * 5 assignments = 20 max assignments
    stu_lms["assignment_completion_rate"] = (stu_lms["total_submitted_assignments"] / 20.0) * 100.0
    stu_lms["assignment_completion_rate"] = stu_lms["assignment_completion_rate"].clip(upper=100.0).round(2)
    stu_lms["quiz_attempts_avg"] = stu_lms["quiz_attempts_avg"].round(2)
    stu_lms["avg_weekly_learning_hours"] = stu_lms["avg_weekly_learning_hours"].round(2)

    # 5. Join Multi-Source Aggregates to Create Analytical Data Mart
    print("[*] Merging sources into Consolidated Analytical Data Mart...")
    mart_df = students_df.merge(stu_att, on="student_id", how="left")
    mart_df = mart_df.merge(stu_marks, on="student_id", how="left")
    mart_df = mart_df.merge(stu_lms, on="student_id", how="left")

    # Handle Missing Values (Imputation as required by Assignment Part 1)
    mart_df["attendance_percentage"] = mart_df["attendance_percentage"].fillna(mart_df["attendance_percentage"].median())
    mart_df["average_internal_marks"] = mart_df["average_internal_marks"].fillna(mart_df["average_internal_marks"].median())
    mart_df["assignment_completion_rate"] = mart_df["assignment_completion_rate"].fillna(50.0)
    mart_df["avg_weekly_learning_hours"] = mart_df["avg_weekly_learning_hours"].fillna(4.0)

    # 6. Generate Synthetic Previous-Semester Trend Feature
    # Simulates historical academic progression (G1/G2 equivalent from UCI)
    np.random.seed(42)
    mart_df["previous_score_trend"] = (
        mart_df["average_internal_marks"] + np.random.normal(loc=-2.0, scale=4.0, size=len(mart_df))
    ).clip(0, 100).round(2)

    # 7. Formulate Ground Truth Target: 'dropout_risk' (Part 2 Target)
    # A student is high risk (1) if low attendance (<70%), low internal marks (<50), or multiple historical failures
    risk_condition = (
        (mart_df["attendance_percentage"] < 70.0) |
        (mart_df["average_internal_marks"] < 50.0) |
        ((mart_df["failures"] >= 2) & (mart_df["assignment_completion_rate"] < 65.0))
    )
    mart_df["dropout_risk"] = np.where(risk_condition, 1, 0)
    
    # Risk category text for business dashboards
    mart_df["risk_category"] = np.where(
        mart_df["dropout_risk"] == 1,
        "High Risk (Intervention Required)",
        "Low Risk (On Track)"
    )

    # Export Data Mart
    mart_file = ANALYTICS_DATA_DIR / "student_risk_mart.csv"
    mart_df.to_csv(mart_file, index=False)
    
    high_risk_count = (mart_df['dropout_risk'] == 1).sum()
    low_risk_count = (mart_df['dropout_risk'] == 0).sum()
    print(f"[OK] Analytical Data Mart created: {len(mart_df)} student profiles.")
    print(f"     -> High Risk / Dropout Prone: {high_risk_count} ({high_risk_count/len(mart_df)*100:.1f}%)")
    print(f"     -> Low Risk / Safe: {low_risk_count} ({low_risk_count/len(mart_df)*100:.1f}%)")
    print(f"     -> Saved to {mart_file.name}\n")
    return mart_df


if __name__ == "__main__":
    transform_and_aggregate()
