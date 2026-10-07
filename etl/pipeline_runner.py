"""
Master End-to-End ETL Pipeline Runner.
Orchestrates:
1. Extraction & Staging (with checksum & row counts)
2. Data Quality & Anomaly Detection (with Rejection Logging)
3. Transformation & Analytical Aggregation (Attendance, Marks, LMS rates)
4. Relational Storage Loading (PostgreSQL / SQLite Star Schema & Data Mart)
"""

import time
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from etl.generate_datasets import generate_all_datasets
from etl.extract import extract_sources
from etl.data_quality import run_data_quality
from etl.transform import transform_and_aggregate
from etl.load import load_warehouse
from config import RAW_DATA_DIR


def run_full_pipeline():
    start_time = time.time()
    print("\n" + "#" * 65)
    print("  STUDENT PERFORMANCE & DROPOUT ANALYTICS - END-TO-END PIPELINE")
    print("#" * 65 + "\n")

    # Step 0: Ensure raw data exists
    if not (RAW_DATA_DIR / "uci_student_demographics.csv").exists():
        print("[!] Raw datasets missing. Auto-generating multi-source records...")
        generate_all_datasets()

    # Step 1: Extraction
    extract_sources()

    # Step 2: Quality Checks & Rejection Log
    run_data_quality()

    # Step 3: Transformation & Aggregation
    transform_and_aggregate()

    # Step 4: Storage & Data Mart Load
    load_warehouse()

    elapsed = round(time.time() - start_time, 2)
    print("=" * 65)
    print(f"PIPELINE EXECUTION COMPLETED SUCCESSFULLY IN {elapsed}s")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_full_pipeline()
