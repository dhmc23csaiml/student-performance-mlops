"""
Database Management Layer.
Supports PostgreSQL (Production/Docker) and SQLite (Standalone local run).
Executes schema creation, loads dimension and fact tables, and provides analytical query access.
"""

import sqlite3
from pathlib import Path
import sys
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import DATA_DIR

SQLITE_DB_PATH = DATA_DIR / "academic_warehouse.db"


def get_connection():
    """Returns a SQLite connection for standalone portability."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_database():
    """Initializes tables adhering to the Star Schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # DDL compatible with SQLite & PostgreSQL
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS dim_student (
        student_id TEXT PRIMARY KEY,
        gender TEXT,
        age INTEGER,
        address TEXT,
        famsize TEXT,
        pstatus TEXT,
        medu INTEGER,
        fedu INTEGER,
        traveltime INTEGER,
        studytime INTEGER,
        failures INTEGER,
        schoolsup TEXT,
        famsup TEXT,
        paid TEXT,
        activities TEXT,
        internet TEXT,
        health INTEGER
    );

    CREATE TABLE IF NOT EXISTS dim_course_subject (
        course_code TEXT PRIMARY KEY,
        course_name TEXT,
        credits INTEGER,
        department TEXT
    );

    CREATE TABLE IF NOT EXISTS dim_semester (
        semester_id INTEGER PRIMARY KEY,
        semester_name TEXT,
        academic_year TEXT
    );

    CREATE TABLE IF NOT EXISTS dim_lms_activity (
        activity_id TEXT PRIMARY KEY,
        student_id TEXT,
        course_code TEXT,
        semester INTEGER,
        assignment_submissions INTEGER,
        quiz_attempts INTEGER,
        forum_posts INTEGER,
        lms_login_count INTEGER,
        learning_hours_weekly REAL
    );

    CREATE TABLE IF NOT EXISTS fact_attendance (
        attendance_id TEXT PRIMARY KEY,
        student_id TEXT,
        course_code TEXT,
        semester INTEGER,
        session_date TEXT,
        session_type TEXT,
        status TEXT,
        is_attended INTEGER
    );

    CREATE TABLE IF NOT EXISTS fact_assessment_marks (
        mark_id TEXT PRIMARY KEY,
        student_id TEXT,
        course_code TEXT,
        semester INTEGER,
        assessment_name TEXT,
        score_obtained REAL,
        max_score REAL,
        score_pct REAL
    );

    CREATE TABLE IF NOT EXISTS mart_student_risk_analytics (
        student_id TEXT PRIMARY KEY,
        gender TEXT,
        age INTEGER,
        studytime INTEGER,
        failures INTEGER,
        attendance_percentage REAL,
        average_internal_marks REAL,
        assignment_completion_rate REAL,
        avg_weekly_learning_hours REAL,
        previous_score_trend REAL,
        dropout_risk INTEGER,
        risk_category TEXT
    );

    CREATE TABLE IF NOT EXISTS etl_rejected_records (
        rejection_id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_name TEXT,
        record_identifier TEXT,
        rejection_reason TEXT,
        severity TEXT,
        raw_record_payload TEXT,
        rejected_at TEXT
    );
    """)

    # Populate course dimension
    cursor.executemany("""
    INSERT OR IGNORE INTO dim_course_subject (course_code, course_name, credits, department)
    VALUES (?, ?, ?, ?)
    """, [
        ("CS101", "Intro to Computer Science", 4, "Computer Science"),
        ("DS201", "Data Engineering Principles", 4, "Data Science"),
        ("MA102", "Linear Algebra & Calculus", 3, "Mathematics"),
        ("SE301", "Software Engineering & DevOps", 4, "Computer Science"),
    ])

    # Populate semester dimension
    cursor.executemany("""
    INSERT OR IGNORE INTO dim_semester (semester_id, semester_name, academic_year)
    VALUES (?, ?, ?)
    """, [
        (1, "Fall Semester 2025", "2025-2026"),
        (2, "Spring Semester 2026", "2025-2026"),
        (3, "Fall Semester 2026", "2026-2027"),
        (4, "Spring Semester 2027", "2026-2027"),
    ])

    conn.commit()
    conn.close()
    print("[OK] Warehouse tables and dimensions initialized.")


def load_dataframe_to_table(df: pd.DataFrame, table_name: str, if_exists: str = "replace"):
    """Loads a pandas DataFrame into SQLite warehouse table."""
    conn = get_connection()
    df.to_sql(table_name, conn, if_exists=if_exists, index=False)
    conn.close()


def query_warehouse(query: str) -> pd.DataFrame:
    """Executes a SQL query and returns result as DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


if __name__ == "__main__":
    init_database()
