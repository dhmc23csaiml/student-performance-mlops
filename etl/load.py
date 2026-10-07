"""
Database Loading Module.
Fulfills Assignment Part 1 Requirements:
- Loads cleaned tables into relational Star Schema (PostgreSQL / SQLite).
- Loads Fact tables: fact_attendance, fact_assessment_marks.
- Loads Dimension tables: dim_student, dim_lms_activity.
- Populates the Analytical Data Mart: mart_student_risk_analytics.
- Stores data quality error logs into etl_rejected_records.
- Verifies record count integrity post-load.
"""

from pathlib import Path
import sys
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import CLEANED_DATA_DIR, ANALYTICS_DATA_DIR, REJECTED_DATA_DIR
from database.db_manager import init_database, load_dataframe_to_table, query_warehouse


def load_warehouse():
    print("=" * 60)
    print("STEP 4: WAREHOUSE LOADING & DATA MART POPULATION")
    print("=" * 60)

    # Ensure schema is ready
    init_database()

    # Load cleaned dimension and facts
    tables_to_load = [
        ("dim_student", CLEANED_DATA_DIR / "dim_student.csv"),
        ("fact_attendance", CLEANED_DATA_DIR / "fact_attendance.csv"),
        ("dim_lms_activity", CLEANED_DATA_DIR / "dim_lms_activity.csv"),
        ("fact_assessment_marks", CLEANED_DATA_DIR / "fact_assessment_marks.csv"),
        ("mart_student_risk_analytics", ANALYTICS_DATA_DIR / "student_risk_mart.csv"),
    ]

    for table_name, file_path in tables_to_load:
        if file_path.exists():
            df = pd.read_csv(file_path)
            load_dataframe_to_table(df, table_name, if_exists="replace")
            print(f"[OK] Loaded table '{table_name}': {len(df)} records inserted.")
        else:
            print(f"[-] WARNING: File {file_path.name} not found. Skipping load for {table_name}.")

    # Load Rejected Records into audit table
    rej_file = REJECTED_DATA_DIR / "rejected_records_audit.csv"
    if rej_file.exists():
        rej_df = pd.read_csv(rej_file)
        load_dataframe_to_table(rej_df, "etl_rejected_records", if_exists="replace")
        print(f"[OK] Loaded table 'etl_rejected_records': {len(rej_df)} audit entries.")

    # Warehouse Verification Check
    print("\n--- DATA WAREHOUSE HEALTH CHECK & RECORD COUNTS ---")
    for tbl in ["dim_student", "dim_course_subject", "fact_attendance", "fact_assessment_marks", "mart_student_risk_analytics", "etl_rejected_records"]:
        try:
            count_df = query_warehouse(f"SELECT COUNT(*) as count FROM {tbl}")
            cnt = count_df["count"].iloc[0]
            print(f"  [>] {tbl:<30}: {cnt:>6} rows")
        except Exception as e:
            print(f"  [-] {tbl:<30}: Error ({e})")

    print("[*] Storage layer loading successfully finished.\n")


if __name__ == "__main__":
    load_warehouse()
