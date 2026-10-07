"""
Data Quality Validation and Rejection Engine.
Fulfills Assignment Part 1 Requirements:
- Standardizes student identifiers across sources.
- Detects and removes duplicates and invalid marks.
- Applies strict schema and range validations.
- Produces a persistent rejected-record and error log with actionable failure diagnostics.
"""

import re
from datetime import datetime
from pathlib import Path
import sys
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import STAGING_DATA_DIR, CLEANED_DATA_DIR, REJECTED_DATA_DIR, VALIDATION_RULES

REJECTED_LOG_FILE = REJECTED_DATA_DIR / "rejected_records_audit.csv"


def standardize_student_id(val) -> str:
    """Standardizes student identifiers across all ingested sources."""
    if pd.isna(val):
        return None
    val_str = str(val).strip().upper()
    # If student ID is purely numbers, e.g. 10050 -> STU_10050
    if re.match(r"^\d{4,6}$", val_str):
        return f"STU_{val_str}"
    if re.match(r"^STU_\d+$", val_str):
        return val_str
    return val_str  # Will be flagged if not matching expected pattern


class DataQualityEngine:
    def __init__(self):
        self.rejected_records = []

    def log_rejection(self, table_name: str, record_id: str, reason: str, payload: dict, severity: str = "ERROR"):
        self.rejected_records.append({
            "table_name": table_name,
            "record_identifier": record_id,
            "rejection_reason": reason,
            "severity": severity,
            "raw_record_payload": str(payload),
            "rejected_at": datetime.now().isoformat(),
        })

    def validate_demographics(self, df: pd.DataFrame) -> pd.DataFrame:
        print("[*] Validating Demographics data...")
        initial_len = len(df)
        valid_rows = []

        # Remove duplicate records
        duplicates = df[df.duplicated(subset=["student_id"], keep=False)]
        if not duplicates.empty:
            for _, row in duplicates.iterrows():
                self.log_rejection("uci_student_demographics", str(row.get("student_id")), "Duplicate student_id", row.to_dict())
            df = df.drop_duplicates(subset=["student_id"], keep="first")

        for _, row in df.iterrows():
            record_id = str(row.get("student_id", "UNKNOWN"))
            std_id = standardize_student_id(record_id)
            
            # ID Pattern Check
            if not std_id or not re.match(r"^STU_\d{5}$", std_id):
                self.log_rejection("uci_student_demographics", record_id, f"Invalid student ID format '{record_id}'", row.to_dict())
                continue

            # Age Range Check
            age = row.get("age")
            if pd.isna(age) or age < VALIDATION_RULES["min_age"] or age > VALIDATION_RULES["max_age"]:
                self.log_rejection("uci_student_demographics", std_id, f"Age {age} out of range [{VALIDATION_RULES['min_age']}, {VALIDATION_RULES['max_age']}]", row.to_dict())
                continue

            row_dict = row.to_dict()
            row_dict["student_id"] = std_id
            valid_rows.append(row_dict)

        cleaned_df = pd.DataFrame(valid_rows)
        print(f"  -> Demographics: {initial_len} initial -> {len(cleaned_df)} valid ({initial_len - len(cleaned_df)} rejected)")
        return cleaned_df

    def validate_attendance(self, df: pd.DataFrame) -> pd.DataFrame:
        print("[*] Validating Attendance logs...")
        initial_len = len(df)
        valid_rows = []

        # Deduplicate on attendance_id
        df = df.drop_duplicates(subset=["attendance_id"], keep="first")

        for _, row in df.iterrows():
            att_id = str(row.get("attendance_id"))
            std_id = standardize_student_id(row.get("student_id"))
            status = str(row.get("status"))

            if not std_id:
                self.log_rejection("erp_attendance_logs", att_id, "Missing student_id", row.to_dict())
                continue

            if status not in VALIDATION_RULES["valid_status"]:
                self.log_rejection("erp_attendance_logs", att_id, f"Invalid attendance status '{status}'", row.to_dict())
                continue

            row_dict = row.to_dict()
            row_dict["student_id"] = std_id
            valid_rows.append(row_dict)

        cleaned_df = pd.DataFrame(valid_rows)
        print(f"  -> Attendance: {initial_len} initial -> {len(cleaned_df)} valid ({initial_len - len(cleaned_df)} rejected)")
        return cleaned_df

    def validate_lms(self, df: pd.DataFrame) -> pd.DataFrame:
        print("[*] Validating LMS digital activity...")
        initial_len = len(df)
        valid_rows = []

        df = df.drop_duplicates(subset=["activity_id"], keep="first")

        for _, row in df.iterrows():
            act_id = str(row.get("activity_id"))
            std_id = standardize_student_id(row.get("student_id"))

            if not std_id:
                self.log_rejection("lms_activity_submissions", act_id, "Missing student_id", row.to_dict())
                continue

            # Learning hours check
            hours = row.get("learning_hours_weekly")
            if pd.isna(hours) or hours < 0 or hours > 100:
                self.log_rejection("lms_activity_submissions", act_id, f"Invalid weekly learning hours: {hours}", row.to_dict())
                continue

            row_dict = row.to_dict()
            row_dict["student_id"] = std_id
            valid_rows.append(row_dict)

        cleaned_df = pd.DataFrame(valid_rows)
        print(f"  -> LMS Activity: {initial_len} initial -> {len(cleaned_df)} valid ({initial_len - len(cleaned_df)} rejected)")
        return cleaned_df

    def validate_internal_marks(self, df: pd.DataFrame) -> pd.DataFrame:
        print("[*] Validating Internal Marks & Assessments...")
        initial_len = len(df)
        valid_rows = []

        df = df.drop_duplicates(subset=["mark_id"], keep="first")

        for _, row in df.iterrows():
            mark_id = str(row.get("mark_id"))
            std_id = standardize_student_id(row.get("student_id"))
            score = row.get("score_obtained")
            max_score = row.get("max_score")

            if not std_id:
                self.log_rejection("erp_internal_marks", mark_id, "Missing student_id", row.to_dict())
                continue

            # Invalid Marks: score < 0 or score > max_score
            if pd.isna(score) or score < 0.0 or score > max_score:
                self.log_rejection("erp_internal_marks", mark_id, f"Invalid score {score} (Max allowed: {max_score})", row.to_dict())
                continue

            row_dict = row.to_dict()
            row_dict["student_id"] = std_id
            valid_rows.append(row_dict)

        cleaned_df = pd.DataFrame(valid_rows)
        print(f"  -> Marks: {initial_len} initial -> {len(cleaned_df)} valid ({initial_len - len(cleaned_df)} rejected)")
        return cleaned_df

    def save_rejected_log(self):
        if self.rejected_records:
            rej_df = pd.DataFrame(self.rejected_records)
            rej_df.to_csv(REJECTED_LOG_FILE, index=False)
            print(f"[!] Logged {len(rej_df)} rejected records to {REJECTED_LOG_FILE}")
        else:
            print("[OK] No records rejected during quality checks.")


def run_data_quality():
    print("=" * 60)
    print("STEP 2: DATA QUALITY & VALIDATION PIPELINE")
    print("=" * 60)

    CLEANED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    dq = DataQualityEngine()

    # Load staged files
    demo_df = pd.read_csv(STAGING_DATA_DIR / "uci_student_demographics.csv")
    att_df = pd.read_csv(STAGING_DATA_DIR / "erp_attendance_logs.csv")
    lms_df = pd.read_csv(STAGING_DATA_DIR / "lms_activity_submissions.csv")
    marks_df = pd.read_csv(STAGING_DATA_DIR / "erp_internal_marks.csv")

    clean_demo = dq.validate_demographics(demo_df)
    clean_att = dq.validate_attendance(att_df)
    clean_lms = dq.validate_lms(lms_df)
    clean_marks = dq.validate_internal_marks(marks_df)

    # Save cleaned tables
    clean_demo.to_csv(CLEANED_DATA_DIR / "dim_student.csv", index=False)
    clean_att.to_csv(CLEANED_DATA_DIR / "fact_attendance.csv", index=False)
    clean_lms.to_csv(CLEANED_DATA_DIR / "dim_lms_activity.csv", index=False)
    clean_marks.to_csv(CLEANED_DATA_DIR / "fact_assessment_marks.csv", index=False)

    dq.save_rejected_log()
    print("[*] Data quality validation complete. Cleaned layers stored.\n")
    return clean_demo, clean_att, clean_lms, clean_marks


if __name__ == "__main__":
    run_data_quality()
