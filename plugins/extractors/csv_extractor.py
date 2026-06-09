"""Plugin for extracting and loading CSV data into ClickHouse.

Standard: PEP-8, CDD (@data_schema.md)
"""

import os
import pandas as pd
import clickhouse_connect
from airflow.exceptions import AirflowException
from typing import Dict, List


REQUIRED_FILES = {
    'orders.csv': 99000,
    'order_items.csv': 111000,
    'customers.csv': 99000,
    'sellers.csv': 3000,
    'products.csv': 32000,
    'geolocation.csv': 1000000,
    'order_reviews.csv': 100000
}


def get_ch_client():
    """Returns a ClickHouse client using environment variables."""
    return clickhouse_connect.get_client(
        host=os.getenv('CLICKHOUSE_HOST', 'clickhouse'),
        port=int(os.getenv('CLICKHOUSE_PORT', 8123)),
        username=os.getenv('CLICKHOUSE_USER', 'default'),
        password=os.getenv('CLICKHOUSE_PASSWORD', 'dustiniapassword'),
        database=os.getenv('CLICKHOUSE_DB', 'dustinia')
    )


def init_clickhouse_schema():
    """Reads and executes all DDL files to initialize the database."""
    client = get_ch_client()
    sql_path = '/opt/airflow/sql/ddl'
    
    ddl_files = [
        'staging_tables.sql',
        'fact_dim_tables.sql',
        'materialized_views.sql'
    ]
    
    for ddl in ddl_files:
        path = os.path.join(sql_path, ddl)
        print(f"Executing DDL: {ddl}...")
        if not os.path.exists(path):
            print(f"Warning: DDL file not found at {path}")
            continue
            
        with open(path, 'r') as f:
            # ClickHouse-connect's command can handle multiple statements 
            # if they are separated properly or run individually.
            # For simplicity, we split by semicolon (naive but usually works for DDLs).
            sql_commands = f.read().split(';')
            for command in sql_commands:
                clean_command = command.strip()
                if clean_command:
                    client.command(clean_command)
    
    print("Database initialization complete.")


def extract_validate_csvs() -> Dict:
    """Validates presence and minimum row count of source CSV files.

    Returns:
        A dictionary containing validation status and metrics.
    
    Raises:
        AirflowException: If mandatory files are missing or empty.
    """
    raw_path = os.getenv('RAW_DATA_PATH', '/opt/airflow/data/raw')
    
    results = {"status": "ok", "files": {}}
    
    for filename, min_rows in REQUIRED_FILES.items():
        file_path = os.path.join(raw_path, filename)
        
        if not os.path.exists(file_path):
            raise AirflowException(f"Missing mandatory file: {filename}")
            
        if os.path.getsize(file_path) == 0:
            raise AirflowException(f"File is empty: {filename}")
            
        # Count rows without loading full file into memory
        with open(file_path, 'rb') as f:
            row_count = sum(1 for _ in f) - 1 # Subtract header
            
        if row_count < min_rows:
            raise AirflowException(
                f"Data Integrity Error: {filename} has {row_count} rows, "
                f"expected at least {min_rows}."
            )
            
        results["files"][filename] = f"validated ({row_count} rows)"
        
    print(f"Validation summary: {results}")
    return results


def load_staging_clickhouse(chunk_size: int = 100000):
    """Loads CSV files into ClickHouse staging tables.

    Args:
        chunk_size: Number of rows per batch insert.
    """
    client = get_ch_client()
    raw_path = os.getenv('RAW_DATA_PATH', '/opt/airflow/data/raw')
    
    mapping = {
        'orders.csv': ('stg_orders', [
            'order_purchase_timestamp', 'order_approved_at', 
            'order_delivered_carrier_date', 'order_delivered_customer_date', 
            'order_estimated_delivery_date'
        ]),
        'order_items.csv': ('stg_order_items', ['shipping_limit_date']),
        'customers.csv': ('stg_customers', []),
        'sellers.csv': ('stg_sellers', []),
        'products.csv': ('stg_products', []),
        'geolocation.csv': ('stg_geolocation', []),
        'order_reviews.csv': ('stg_order_reviews', [
            'review_creation_date', 'review_answer_timestamp'
        ])
    }
    
    for filename, (table_name, date_cols) in mapping.items():
        file_path = os.path.join(raw_path, filename)
        print(f"Loading {filename} into {table_name}...")
        
        # 0. Get target table schema to filter columns
        # This prevents errors when CSV has more columns than the table
        table_info = client.query(f"DESCRIBE TABLE {table_name}")
        target_cols = [row[0] for row in table_info.result_rows]
        print(f"Target columns for {table_name}: {target_cols}")

        # Truncate before load (Full Load strategy for statics)
        client.command(f"TRUNCATE TABLE {table_name}")
        
        # Zip code columns that must be strings
        zip_cols = [
            'customer_zip_code_prefix', 
            'seller_zip_code_prefix', 
            'geolocation_zip_code_prefix'
        ]
        
        # Read in chunks to manage memory
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            # 1. Filter columns to match ClickHouse table
            chunk = chunk[[c for c in chunk.columns if c in target_cols]]

            # 2. Explicitly convert date columns to datetime objects
            for col in date_cols:
                if col in chunk.columns:
                    chunk[col] = pd.to_datetime(chunk[col], errors='coerce')
            
            # 3. Force Zip Code columns to String
            for col in zip_cols:
                if col in chunk.columns:
                    chunk[col] = chunk[col].astype(str)

            # 4. Handle Nulls and Final Type Alignment
            for col in chunk.columns:
                if col in date_cols:
                    chunk[col] = chunk[col].apply(lambda x: x.to_pydatetime() if pd.notnull(x) else None)
                elif chunk[col].dtype == 'object':
                    chunk[col] = chunk[col].where(pd.notnull(chunk[col]), None)
                else:
                    # For numeric columns, ensure No NaNs
                    chunk[col] = chunk[col].where(pd.notnull(chunk[col]), 0 if 'int' in str(chunk[col].dtype) else 0.0)
            
            client.insert_df(table_name, chunk)
            
        count = client.command(f"SELECT count() FROM {table_name}")
        print(f"Finished loading {table_name}. Row count: {count}")

        # Post-load enrichment for geolocation
        if table_name == 'stg_geolocation':
            print("Populating geo_centroids from stg_geolocation...")
            client.command("TRUNCATE TABLE dustinia.geo_centroids")
            client.command("""
            INSERT INTO dustinia.geo_centroids
            SELECT 
                geolocation_zip_code_prefix AS zip,
                avg(geolocation_lat) AS lat,
                avg(geolocation_lng) AS lng
            FROM dustinia.stg_geolocation
            GROUP BY zip
            """)
            print("geo_centroids populated.")
