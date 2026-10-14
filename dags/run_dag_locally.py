"""
Airflow Local DAG Runner / Emulator.
Enables running the Airflow DAG directly on Windows or without starting full Docker services.
Executes the tasks in the exact sequence and dependency order defined in student_analytics_dag:
    extract_task >> quality_task >> transform_task >> load_task
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from etl.extract import extract_sources
from etl.data_quality import run_data_quality
from etl.transform import transform_and_aggregate
from etl.load import load_warehouse


def run_airflow_dag_locally():
    print("=" * 70)
    print("  APACHE AIRFLOW: DAG EXECUTION EMULATOR")
    print(f"  DAG ID: student_academic_analytics_etl")
    print(f"  Schedule: @daily | Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    tasks = [
        {"id": "extract_academic_sources", "fn": extract_sources, "state": "PENDING"},
        {"id": "validate_data_quality", "fn": run_data_quality, "state": "PENDING"},
        {"id": "transform_and_aggregate_metrics", "fn": transform_and_aggregate, "state": "PENDING"},
        {"id": "load_postgres_warehouse", "fn": load_warehouse, "state": "PENDING"},
    ]

    total_start = time.time()

    for idx, task in enumerate(tasks, 1):
        print(f"\n[AIRFLOW SCHEDULER] >>> Queuing Task ({idx}/4): <TaskInstance: {task['id']}>")
        print(f"[AIRFLOW TASK RUNNER] Status: RUNNING...")
        t_start = time.time()
        
        try:
            task["fn"]()
            elapsed = round(time.time() - t_start, 2)
            task["state"] = "SUCCESS"
            print(f"[AIRFLOW TASK RUNNER] Status: SUCCESS | Duration: {elapsed}s")
        except Exception as e:
            task["state"] = "FAILED"
            print(f"[AIRFLOW TASK RUNNER] Status: FAILED | Error: {e}")
            print(f"[AIRFLOW SCHEDULER] Downstream tasks aborted due to upstream task failure.")
            return

    total_elapsed = round(time.time() - total_start, 2)
    print("\n" + "=" * 70)
    print(f"  DAG RUN COMPLETED SUCCESSFULLY: student_academic_analytics_etl")
    print(f"  All 4 tasks executed in dependency order. Total Time: {total_elapsed}s")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_airflow_dag_locally()
