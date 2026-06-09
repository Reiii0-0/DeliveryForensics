"""Plugin for calculating haversine distance between sellers and customers.
Note: Logic migrated to native ClickHouse in delivery_transformer.py for performance.
"""

from extractors.csv_extractor import get_ch_client

def transform_dim_geo():
    """No-op: distance is now calculated during fact table transformation."""
    print("Skipping transform_dim_geo (migrated to native SQL in transform_fact_deliveries).")

def create_materialized_views():
    """Initializes/Refreshes Materialized Views by running the DDL."""
    client = get_ch_client()
    import os
    sql_path = '/opt/airflow/sql/ddl/materialized_views.sql'
    if not os.path.exists(sql_path):
        print(f"Warning: DDL file not found at {sql_path}")
        return
    with open(sql_path, 'r') as f:
        queries = f.read().split(';')
    for query in queries:
        if query.strip():
            client.command(query)
    print("Materialized Views created/refreshed.")
