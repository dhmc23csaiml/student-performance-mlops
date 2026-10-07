"""
Extraction Module for Multi-Source Academic Data.
Fulfills Assignment Part 1 Requirements:
- Ingests CSV sources (UCI Demographics, ERP Attendance, LMS logs, ERP Marks).
- Maintains raw copy and stages data.
- Records extraction date, source name, status, and row count.
- Logs extraction metadata into pipeline audit records.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
import sys
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import RAW_DATA_DIR, STAGING_DATA_DIR, DATA_DIR

AUDIT_LOG_FILE = DATA_DIR / "ingestion_audit_log.json"


def calculate_md5(file_path: Path) -> str:
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()


def extract_sources():
    print("=" * 60)
    print("STEP 1: INGESTION & EXTRACTION PIPELINE")
    print("=" * 60)

    STAGING_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    sources = [
        {"name": "UCI_Student_Demographics", "file": RAW_DATA_DIR / "uci_student_demographics.csv"},
        {"name": "ERP_Attendance_Logs", "file": RAW_DATA_DIR / "erp_attendance_logs.csv"},
        {"name": "LMS_Activity_Submissions", "file": RAW_DATA_DIR / "lms_activity_submissions.csv"},
        {"name": "ERP_Internal_Marks", "file": RAW_DATA_DIR / "erp_internal_marks.csv"},
    ]

    audit_records = []
    staged_summary = {}

    for src in sources:
        file_path = src["file"]
        if not file_path.exists():
            error_msg = f"Source file {file_path.name} not found!"
            print(f"[-] ERROR: {error_msg}")
            audit_records.append({
                "source_name": src["name"],
                "file_name": file_path.name,
                "status": "FAILED",
                "error": error_msg,
                "extracted_at": datetime.now().isoformat(),
                "row_count": 0,
            })
            continue

        try:
            df = pd.read_csv(file_path)
            row_count = len(df)
            file_hash = calculate_md5(file_path)
            
            # Copy to staging area
            staged_path = STAGING_DATA_DIR / file_path.name
            df.to_csv(staged_path, index=False)

            log_entry = {
                "source_name": src["name"],
                "file_name": file_path.name,
                "staged_path": str(staged_path),
                "status": "SUCCESS",
                "row_count": row_count,
                "file_checksum_md5": file_hash,
                "extracted_at": datetime.now().isoformat(),
            }
            audit_records.append(log_entry)
            staged_summary[src["name"]] = df
            print(f"[OK] Ingested {src['name']} ({file_path.name}) -> {row_count} rows staged.")
        except Exception as e:
            print(f"[-] Ingestion failed for {src['name']}: {e}")
            audit_records.append({
                "source_name": src["name"],
                "file_name": file_path.name,
                "status": "ERROR",
                "error": str(e),
                "extracted_at": datetime.now().isoformat(),
                "row_count": 0,
            })

    # Persist Ingestion Audit Log
    existing_logs = []
    if AUDIT_LOG_FILE.exists():
        try:
            with open(AUDIT_LOG_FILE, "r") as f:
                existing_logs = json.load(f)
        except Exception:
            existing_logs = []

    existing_logs.extend(audit_records)
    with open(AUDIT_LOG_FILE, "w") as f:
        json.dump(existing_logs, f, indent=2)

    print(f"[*] Ingestion audit metadata saved to {AUDIT_LOG_FILE.name}")
    print("[*] Extraction stage successfully executed.\n")
    return staged_summary


if __name__ == "__main__":
    extract_sources()
