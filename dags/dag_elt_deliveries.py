"""Main ELT pipeline for DeliveryForensics.

This DAG orchestrates the extraction of Olist dataset CSVs, 
loading them into ClickHouse staging tables, and performing 
transformations for Persona 3 (Operational Analyst).

Standard: PEP-8, Airflow 2.8.x
"""

import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

# Import custom plugins
from extractors.csv_extractor import extract_validate_csvs, load_staging_clickhouse, init_clickhouse_schema
from transformers.delivery_transformer import transform_fact_deliveries, transform_dimensions
from transformers.geo_transformer import transform_dim_geo, create_materialized_views
from ml.late_predictor import run_ml_late_predictor
from ml.geo_cluster import run_ml_geo_cluster
from extractors.quality_checker import validate_data_quality

# Default arguments for all tasks
default_args = {
    'owner': 'tech_lead',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='dag_elt_deliveries',
    default_args=default_args,
    description='End-to-end ELT for DustiniaDelixia Operational Analysis',
    schedule=None,
    start_date=datetime(2026, 6, 1),
    catchup=False,
    tags=['elt', 'deliveries', 'persona3', 'mci2026'],
    max_active_runs=1,
) as dag:

    start_node = EmptyOperator(task_id='start_pipeline')

    setup_db = PythonOperator(
        task_id='init_clickhouse_schema',
        python_callable=init_clickhouse_schema,
    )

    # Ingestion Phase
    validate_csvs = PythonOperator(
        task_id='extract_validate_csvs',
        python_callable=extract_validate_csvs,
    )

    load_to_staging = PythonOperator(
        task_id='load_staging_clickhouse',
        python_callable=load_staging_clickhouse,
        op_kwargs={'chunk_size': 100000},
    )

    # Transformation Phase
    transform_fact = PythonOperator(
        task_id='transform_fact_deliveries',
        python_callable=transform_fact_deliveries,
    )

    transform_dims = PythonOperator(
        task_id='transform_dimensions',
        python_callable=transform_dimensions,
    )

    transform_geo = PythonOperator(
        task_id='transform_dim_geo',
        python_callable=transform_dim_geo,
    )

    # Serving Phase
    refresh_mv = PythonOperator(
        task_id='create_materialized_views',
        python_callable=create_materialized_views,
    )

    # ML Phase (Value-Add)
    predict_late = PythonOperator(
        task_id='run_ml_late_predictor',
        python_callable=run_ml_late_predictor,
    )

    cluster_geo = PythonOperator(
        task_id='run_ml_geo_cluster',
        python_callable=run_ml_geo_cluster,
        op_kwargs={'n_clusters': 4},
    )

    # Quality Control
    validate_dq = PythonOperator(
        task_id='validate_data_quality',
        python_callable=validate_data_quality,
    )

    end_node = EmptyOperator(task_id='end_pipeline')

    # Define Dependencies
    start_node >> setup_db >> validate_csvs >> load_to_staging
    load_to_staging >> transform_fact
    transform_fact >> [transform_dims, transform_geo]
    [transform_dims, transform_geo] >> refresh_mv
    refresh_mv >> [predict_late, cluster_geo]
    [predict_late, cluster_geo] >> validate_dq >> end_node
