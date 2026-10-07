"""
Apache Airflow DAG: Student Academic Analytics & Dropout Risk Pipeline.
Fulfills Assignment Part 1 Requirements:
- Schedules and orchestrates ingestion, validation, transformation, and warehouse loading.
- Defines task-level error handling, retry policies, and execution dependencies.
- Can be placed directly in AIRFLOW_HOME/dags.
"""

from datetime import datetime, timedelta
import os
import sys

# Ensure DAG can import pipeline modules
DAGS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DAGS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.operators.bash import BashOperator
    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False


def task_extract_sources(**kwargs):
    from etl.extract import extract_sources
    print("[Airflow Task] Running source extraction...")
    summary = extract_sources()
    return f"Extracted {len(summary)} sources"


def task_data_quality_checks(**kwargs):
    from etl.data_quality import run_data_quality
    print("[Airflow Task] Running data quality validation...")
    run_data_quality()
    return "Data quality validation complete"


def task_transform_and_aggregate(**kwargs):
    from etl.transform import transform_and_aggregate
    print("[Airflow Task] Running feature transformations and analytical aggregation...")
    transform_and_aggregate()
    return "Aggregation complete"


def task_load_warehouse(**kwargs):
    from etl.load import load_warehouse
    print("[Airflow Task] Loading cleaned data and data mart into warehouse...")
    load_warehouse()
    return "Warehouse loading complete"


# Default arguments for Airflow DAG
default_args = {
    "owner": "data_engineering_team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2026, 9, 1),
}

if AIRFLOW_AVAILABLE:
    with DAG(
        dag_id="student_academic_analytics_etl",
        default_args=default_args,
        description="End-to-end Academic Analytics & Dropout Risk Data Pipeline",
        schedule_interval="@daily",
        catchup=False,
        tags=["academic_analytics", "etl", "data_warehouse", "mlops"],
    ) as dag:

        extract_task = PythonOperator(
            task_id="extract_academic_sources",
            python_callable=task_extract_sources,
        )

        quality_task = PythonOperator(
            task_id="validate_data_quality",
            python_callable=task_data_quality_checks,
        )

        transform_task = PythonOperator(
            task_id="transform_and_aggregate_metrics",
            python_callable=task_transform_and_aggregate,
        )

        load_task = PythonOperator(
            task_id="load_postgres_warehouse",
            python_callable=task_load_warehouse,
        )

        # Define DAG Execution Flow
        extract_task >> quality_task >> transform_task >> load_task
else:
    print("[INFO] Apache Airflow library not loaded in active environment. DAG file defined for Airflow server.")
